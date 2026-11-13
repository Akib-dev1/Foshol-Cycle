"""Shared calendar-eligibility evaluator (v1.md §6.1).

One implementation serves every crop profile. Window bounds and metadata come
from the profile; this module never invents an agronomic window or waiting
limit.

Window resolution attaches month/day bounds to real years. A containing
instance wins; otherwise the nearest start among the current/next season and
any window whose support ended in the proposed calendar year is used.
Resolution never skips multiple seasons. The New Year boundary is a deliberate
product policy: on Jan 1 a season that ended in the previous calendar year is
not revived as the context, so the next season is exposed as a future option.
That discontinuity never creates a pass for a past date.

The late bound is optional. It is attached to the preferred end year and is
validated only as an extension of that window. A late bound that cannot be
attached in a given year does not invalidate preferred or future results; it
makes a post-preferred result unknown until a year where it can be resolved.
"""

from __future__ import annotations

import datetime as dt
import re

_MMDD_RE = re.compile(r"^(\d{2})-(\d{2})$")
_SOURCE_FIELDS = ("source_planting_window", "source_local_calendar")


def evaluate_calendar_fit(
    profile: dict,
    start_date: dt.date | str,
    max_waiting_days: int | None = None,
) -> dict:
    """Evaluate one crop profile against one proposed planting date.

    ``start_date`` is a ``datetime.date`` or an ISO ``YYYY-MM-DD`` string.
    ``max_waiting_days`` is an explicit caller-supplied policy; ``None`` means
    no policy is configured and a future window is reported as unknown.

    Returns a JSON-serializable dict with ``status``, ``code``, ``reason``,
    ``source_ids``, and ``details``.
    """
    proposed = _coerce_date(start_date)
    limit = _validate_limit(max_waiting_days)
    source_ids = [field for field in _SOURCE_FIELDS if _text(profile, field)]
    details = _base_details(profile, proposed, limit)

    if not source_ids:
        reason = (
            "The crop profile has neither source_planting_window nor "
            "source_local_calendar; calendar fit is unknown rather than an "
            "automatic pass."
        )
        return _unknown("WINDOW_SOURCE_MISSING", reason, details, source_ids)

    # The normalized MM-DD fields are authoritative. Raw text is only used for
    # descriptive metadata, not to resurrect a value the loader cleared.
    start_text = _normalized_text(profile, "preferred_start_mmdd")
    end_text = _normalized_text(profile, "preferred_end_mmdd")
    late_text = _normalized_text(profile, "supported_late_end_mmdd")

    start_mmdd, error = _parse_window_field(
        start_text, "WINDOW_START_MISSING", "WINDOW_START_INVALID"
    )
    if error:
        return _unknown(
            error, _missing_reason("preferred_start_mmdd"), details, source_ids
        )
    end_mmdd, error = _parse_window_field(
        end_text, "WINDOW_END_MISSING", "WINDOW_END_INVALID"
    )
    if error:
        return _unknown(
            error, _missing_reason("preferred_end_mmdd"), details, source_ids
        )

    late_mmdd = None
    late_invalid = False
    if late_text is not None:
        late_mmdd = _parse_mmdd(late_text)
        late_invalid = late_mmdd is None

    if details["window_basis"] is None:
        return _unknown(
            "WINDOW_BASIS_MISSING",
            _missing_reason("window_basis"),
            details,
            source_ids,
        )
    if details["window_type"] is None:
        return _unknown(
            "WINDOW_TYPE_MISSING",
            _missing_reason("planting_window_type"),
            details,
            source_ids,
        )

    crosses = _parse_optional_bool(profile.get("window_crosses_year"))
    if crosses is None:
        return _unknown(
            "WINDOW_CROSS_YEAR_MISSING",
            _missing_reason("window_crosses_year"),
            details,
            source_ids,
        )
    if crosses != (start_mmdd > end_mmdd):
        reason = (
            "window_crosses_year conflicts with the preferred start/end order "
            f"({start_text} to {end_text}); the window cannot be attached to years "
            "safely."
        )
        return _unknown("WINDOW_DATA_INCONSISTENT", reason, details, source_ids)

    candidates = [
        _build_candidate(year, start_mmdd, end_mmdd, late_mmdd, crosses)
        for year in (proposed.year - 1, proposed.year, proposed.year + 1)
    ]
    if any(candidate["late_status"] == "inconsistent" for candidate in candidates):
        reason = (
            f"supported_late_end_mmdd={late_text} is not a valid extension of the "
            f"preferred window ({start_text} to {end_text}); it must fall after "
            "the preferred end and before the next season's preferred start. The "
            "window data is inconsistent."
        )
        return _unknown("WINDOW_DATA_INCONSISTENT", reason, details, source_ids)

    selected = _select_candidate(candidates, proposed)
    if selected is not None:
        details["window_start_year"] = selected["start_year"]
        if selected["start"] is not None:
            details["preferred_start"] = selected["start"].isoformat()
        if selected["end"] is not None:
            details["preferred_end"] = selected["end"].isoformat()
        if selected["late_status"] == "resolved":
            details["supported_late_end"] = selected["late_end"].isoformat()

    window_type = details["window_type"]
    precision = details["date_precision"]
    geographic_unknown = "NOT_RAJSHI_EXACT" in window_type.upper() or (
        precision is not None
        and "LOCATION_TRANSFERABILITY" in precision.upper()
    )
    if geographic_unknown:
        reason = (
            "The window is not Rajshahi-exact "
            f"(planting_window_type={window_type}, date_precision={precision}); "
            "it cannot support a calendar pass for this district even when the date "
            "falls inside the encoded dates."
        )
        return _unknown("WINDOW_GEOGRAPHY_UNKNOWN", reason, details, source_ids)

    if selected is None:
        return _unknown(
            "WINDOW_DATE_MISSING",
            "No calendar-window instance could be attached to the proposed date.",
            details,
            source_ids,
        )

    start = selected["start"]
    end = selected["end"]
    missing_fields = ", ".join(selected["missing_preferred"])
    if start is None:
        return _unknown(
            "WINDOW_DATE_MISSING",
            _date_missing_reason(missing_fields, proposed),
            details,
            source_ids,
        )

    if proposed < start:
        waiting_days = (start - proposed).days
        details["next_window_start"] = start.isoformat()
        details["waiting_days"] = waiting_days
        if limit is None:
            details["waiting_limit_status"] = "unknown"
            reason = (
                f"The next documented preferred window starts {start.isoformat()} "
                f"({waiting_days} days after the proposed date). No maximum waiting "
                "policy is configured, so this future option is unknown; it is not "
                "a plant-now option."
            )
            return _unknown(
                "FUTURE_WINDOW_WAIT_POLICY_UNKNOWN", reason, details, source_ids
            )
        if waiting_days <= limit:
            details["waiting_limit_status"] = "within_limit"
            reason = (
                f"The next documented preferred window starts {start.isoformat()} "
                f"({waiting_days} days after the proposed date), within the configured "
                f"maximum waiting limit of {limit} days. This is a future option, "
                "not a plant-now option."
            )
            return _caution("FUTURE_WINDOW_WITHIN_LIMIT", reason, details, source_ids)
        details["waiting_limit_status"] = "exceeds_limit"
        reason = (
            f"The next documented preferred window starts {start.isoformat()} "
            f"({waiting_days} days after the proposed date), which exceeds this "
            f"explorer's maximum waiting gap of {limit} days. The limit is a product "
            "relevance cutoff, not a biological impossibility."
        )
        return _unsupported(
            "FUTURE_WINDOW_EXCEEDS_LIMIT", reason, details, source_ids
        )

    if end is None:
        return _unknown(
            "WINDOW_DATE_MISSING",
            _date_missing_reason(missing_fields, proposed),
            details,
            source_ids,
        )

    if proposed <= end:
        if precision is None:
            return _unknown(
                "WINDOW_PRECISION_MISSING",
                _missing_reason("date_precision"),
                details,
                source_ids,
            )
        details["plant_now"] = True
        if precision.strip().upper() == "DAY":
            reason = (
                f"The proposed date is inside the documented preferred window "
                f"({start.isoformat()} to {end.isoformat()}). The window end is a "
                "sourced calendar boundary, not a proven biological deadline."
            )
            return _pass("PREFERRED_WINDOW", reason, details, source_ids)
        reason = (
            f"The proposed date is inside the documented preferred window "
            f"({start.isoformat()} to {end.isoformat()}), but the boundary is "
            f"approximate ({precision}), not exact. The window end is not a proven "
            "biological deadline."
        )
        return _caution(
            "PREFERRED_WINDOW_APPROXIMATE", reason, details, source_ids
        )

    if precision is None:
        return _unknown(
            "WINDOW_PRECISION_MISSING",
            _missing_reason("date_precision"),
            details,
            source_ids,
        )
    if late_invalid:
        reason = (
            "The proposed date is after the preferred window, but "
            f"supported_late_end_mmdd={late_text} is not a valid MM-DD date. The "
            "optional late extension cannot be interpreted; calendar fit after the "
            "preferred end is unknown."
        )
        return _unknown("WINDOW_LATE_END_INVALID", reason, details, source_ids)
    if late_mmdd is None:
        details["plant_now"] = False
        reason = (
            f"The proposed date is outside the documented window "
            f"({start.isoformat()} to {end.isoformat()}). No documented late window "
            "exists for this profile. This is outside documented planting support; "
            "it is not a biological impossibility and the preferred end is not a "
            "proven deadline."
        )
        return _unsupported("OUTSIDE_SUPPORTED_WINDOW", reason, details, source_ids)
    if selected["late_status"] == "unresolved":
        reason = (
            "The proposed date is after the preferred window, but "
            f"supported_late_end_mmdd={late_text} does not exist in the attached "
            f"end year for {proposed.isoformat()} (for example 02-29 outside a leap "
            "year). The late extension is unresolved; calendar fit after the "
            "preferred end is unknown."
        )
        return _unknown(
            "WINDOW_LATE_END_UNRESOLVED", reason, details, source_ids
        )

    late_end = selected["late_end"]
    if proposed <= late_end:
        details["plant_now"] = True
        reason = (
            f"The proposed date is after the preferred window but inside the "
            f"documented supported-late window (to {late_end.isoformat()}). The "
            "preferred end is not a proven biological deadline; late planting "
            "carries documented risk."
        )
        return _caution("LATE_WINDOW", reason, details, source_ids)

    details["plant_now"] = False
    reason = (
        f"The proposed date is outside the documented window "
        f"({start.isoformat()} to {end.isoformat()}) and beyond the supported-late "
        f"end ({late_end.isoformat()}). This is outside documented planting "
        "support; it is not a biological impossibility and the preferred end is "
        "not a proven deadline."
    )
    return _unsupported("OUTSIDE_SUPPORTED_WINDOW", reason, details, source_ids)


def _build_candidate(
    start_year: int,
    start_mmdd: tuple[int, int],
    end_mmdd: tuple[int, int],
    late_mmdd: tuple[int, int] | None,
    crosses: bool,
) -> dict:
    end_year = start_year + 1 if crosses else start_year
    start = _attach_date(start_year, start_mmdd)
    end = _attach_date(end_year, end_mmdd)
    missing_preferred = []
    if start is None:
        missing_preferred.append("preferred_start_mmdd")
    if end is None:
        missing_preferred.append("preferred_end_mmdd")

    late_end = None
    late_status = "absent"
    if late_mmdd is not None:
        late_end = _attach_date(end_year, late_mmdd)
        if late_end is None:
            late_status = "unresolved"
        else:
            late_status = "resolved"
            if end is not None:
                next_start = _attach_date(start_year + 1, start_mmdd)
                if late_end <= end:
                    late_status = "inconsistent"
                elif next_start is not None and late_end >= next_start:
                    late_status = "inconsistent"

    return {
        "start_year": start_year,
        "start": start,
        "end": end,
        "late_end": late_end,
        "late_status": late_status,
        "missing_preferred": missing_preferred,
        "nominal_start": _nominal_ordinal(start_year, start_mmdd),
    }


def _select_candidate(candidates: list[dict], proposed: dt.date) -> dict | None:
    containing = [
        candidate
        for candidate in candidates
        if candidate["start"] is not None
        and candidate["end"] is not None
        and candidate["start"] <= proposed <= _support_end(candidate)
    ]
    if containing:
        return max(containing, key=lambda candidate: candidate["start"])

    # Keep the current/next season and any window whose support ended in the
    # proposed calendar year. A season that ended in an earlier year is not
    # revived as the context for an after-support result; the upcoming window
    # is the future option instead. Nearest start breaks ties within the set.
    #
    # Product policy (pinned by test): on Jan 1 a December-ending season that
    # ended in the previous calendar year is not revived; the next season
    # becomes the future option. This is a deliberate one-day discontinuity at
    # New Year, never a pass for a past date.
    considered = []
    for candidate in candidates:
        if candidate["start_year"] in (proposed.year, proposed.year + 1):
            considered.append(candidate)
        elif (
            candidate["end"] is not None
            and candidate["end"].year == proposed.year
        ):
            considered.append(candidate)
        elif (
            candidate["late_end"] is not None
            and candidate["late_end"].year == proposed.year
        ):
            considered.append(candidate)
    if not considered:
        considered = candidates
    return min(
        considered,
        key=lambda candidate: (
            abs(candidate["nominal_start"] - proposed.toordinal()),
            candidate["nominal_start"] > proposed.toordinal(),
        ),
    )


def _support_end(candidate: dict) -> dt.date:
    end = candidate["end"]
    if candidate["late_status"] != "resolved":
        return end
    late_end = candidate["late_end"]
    return late_end if late_end > end else end


def _attach_date(year: int, mmdd: tuple[int, int]) -> dt.date | None:
    try:
        return dt.date(year, mmdd[0], mmdd[1])
    except ValueError:
        return None


def _nominal_ordinal(year: int, mmdd: tuple[int, int]) -> int:
    try:
        return dt.date(year, mmdd[0], mmdd[1]).toordinal()
    except ValueError:
        # Only 02-29 in a non-leap year reaches here; rank it as March 1.
        return dt.date(year, 3, 1).toordinal()


def _base_details(profile: dict, proposed: dt.date, limit: int | None) -> dict:
    return {
        "planting_date": proposed.isoformat(),
        "plant_now": False,
        "preferred_start": None,
        "preferred_end": None,
        "supported_late_end": None,
        "next_window_start": None,
        "waiting_days": None,
        "waiting_limit_days": limit,
        "waiting_limit_status": "not_applicable",
        "window_start_year": None,
        "date_precision": _text(profile, "date_precision"),
        "hard_deadline_validated": _parse_optional_bool(
            _text(profile, "hard_deadline_validated")
        ),
        "window_basis": _text(profile, "window_basis"),
        "window_type": _text(profile, "planting_window_type"),
        "window_guard_readiness": _text(profile, "window_guard_readiness"),
        "algorithm_use_note": _text(profile, "algorithm_use_note"),
    }


def _result(
    status: str, code: str, reason: str, details: dict, source_ids: list[str]
) -> dict:
    return {
        "status": status,
        "code": code,
        "reason": reason,
        "source_ids": source_ids,
        "details": details,
    }


def _pass(code: str, reason: str, details: dict, source_ids: list[str]) -> dict:
    return _result("pass", code, reason, details, source_ids)


def _caution(code: str, reason: str, details: dict, source_ids: list[str]) -> dict:
    return _result("caution", code, reason, details, source_ids)


def _unsupported(
    code: str, reason: str, details: dict, source_ids: list[str]
) -> dict:
    return _result("unsupported", code, reason, details, source_ids)


def _unknown(code: str, reason: str, details: dict, source_ids: list[str]) -> dict:
    return _result("unknown", code, reason, details, source_ids)


def _coerce_date(value: dt.date | str) -> dt.date:
    if isinstance(value, dt.datetime):
        return value.date()
    if isinstance(value, dt.date):
        return value
    if isinstance(value, str):
        try:
            return dt.date.fromisoformat(value.strip())
        except ValueError as exc:
            raise ValueError(
                f"start_date must be an ISO date (YYYY-MM-DD): {value!r}"
            ) from exc
    raise TypeError("start_date must be a date or an ISO date string")


def _validate_limit(value: int | None) -> int | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError("max_waiting_days must be an integer or None")
    if value < 0:
        raise ValueError("max_waiting_days cannot be negative")
    return value


def _parse_window_field(
    text: str | None, missing_code: str, invalid_code: str
) -> tuple[tuple[int, int] | None, str | None]:
    if text is None:
        return None, missing_code
    parsed = _parse_mmdd(text)
    if parsed is None:
        return None, invalid_code
    return parsed, None


def _parse_mmdd(text: str) -> tuple[int, int] | None:
    match = _MMDD_RE.fullmatch(text)
    if match is None:
        return None
    month, day = int(match.group(1)), int(match.group(2))
    try:
        dt.date(2024, month, day)
    except ValueError:
        return None
    return month, day


def _parse_optional_bool(value: object) -> bool | None:
    if isinstance(value, bool):
        return value
    if value is None:
        return None
    text = str(value).strip().upper()
    if text == "TRUE":
        return True
    if text == "FALSE":
        return False
    return None


def _field_value(profile: dict, field: str) -> object:
    value = profile.get(field)
    if value is not None:
        return value
    raw = profile.get("raw")
    if isinstance(raw, dict):
        return raw.get(field)
    return None


def _normalized_text(profile: dict, field: str) -> str | None:
    value = profile.get(field)
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _text(profile: dict, field: str) -> str | None:
    value = _field_value(profile, field)
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _missing_reason(field: str) -> str:
    return (
        f"The crop profile has no usable {field}; calendar fit is unknown rather "
        "than an automatic pass."
    )


def _date_missing_reason(fields: str, proposed: dt.date) -> str:
    return (
        f"The preferred window boundary {fields} does not exist in the year "
        f"required for {proposed.isoformat()} (for example 02-29 outside a leap "
        "year); the preferred window cannot be attached."
    )
