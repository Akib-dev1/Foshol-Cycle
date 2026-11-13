"""Timeline, preparation, waiting, and next-planting calculations (v1.md §10).

Harvest dates come only from the selected variety duration range. Preparation
times come only from the caller's explicit lookup; the blank crop-CSV
turnaround fields are deliberately never read. Missing preparation never
becomes zero. The duration reference stage is unconfirmed by the CSV, so the
default timeline is conditional rather than exact.

Ranges propagate: earliest and latest endpoints are kept separately and are
never averaged. The next planting range is clipped to the documented
supported-late end, with the clip exposed as a caution.
"""

from __future__ import annotations

import datetime as dt

_DURATION_FIELDS = ("variety_duration_min_days", "variety_duration_max_days")


def build_crop_timeline(
    profile: dict,
    planting_range: dict | None,
    preparation: dict | None = None,
    duration_reference_verified: bool = False,
    max_waiting_days: int | None = None,
) -> dict:
    """Build one crop's planting, harvest, preparation, and readiness ranges.

    ``planting_range`` is ``{"earliest": "YYYY-MM-DD", "latest": "..."}``.
    ``preparation`` is ``{"min_days", "max_days", "source_ids"}`` or ``None``.
    ``max_waiting_days`` is carried for transition evaluation; it does not
    change the single-crop timeline.
    """
    limit = _validate_limit(max_waiting_days)
    planting = _parse_range(planting_range, "planting_range")

    codes: list[str] = []
    reasons: list[str] = []
    cautions: list[str] = []
    missing: list[str] = []
    sources: list[str] = []
    reason_by_code: dict[str, str] = {}

    duration, duration_code = _duration_range(profile)
    if duration is None:
        codes.append(duration_code)
        missing.extend(_DURATION_FIELDS)
        reason_by_code[duration_code] = _duration_reason(duration_code)
        reasons.append(reason_by_code[duration_code])
        harvest = None
    else:
        harvest = (
            planting[0] + dt.timedelta(days=duration[0]),
            planting[1] + dt.timedelta(days=duration[1]),
        )
        sources.extend(_DURATION_FIELDS)

    prep, prep_code, prep_reason = _normalize_preparation(preparation)
    if prep is None:
        codes.append(prep_code)
        missing.append("preparation_time")
        reason_by_code[prep_code] = prep_reason
        reasons.append(prep_reason)
    else:
        sources.extend(prep["source_ids"])
        if not prep["source_ids"]:
            codes.append("PREPARATION_SOURCE_MISSING")
            source_reason = (
                "Preparation days were supplied without source_ids; they are a "
                "caller assumption, not verified local evidence."
            )
            reason_by_code["PREPARATION_SOURCE_MISSING"] = source_reason
            cautions.append(source_reason)
            reasons.append(source_reason)
            missing.append("preparation_source_ids")

    ready = None
    if harvest is not None and prep is not None:
        ready = (
            harvest[0] + dt.timedelta(days=prep["min_days"]),
            harvest[1] + dt.timedelta(days=prep["max_days"]),
        )

    establishment = _text(profile, "establishment_method")
    transplanted = establishment is not None and "transplant" in establishment.lower()
    seedling = _seedling_age(profile)
    if transplanted:
        codes.append("NURSERY_AGE_NOT_ADDED")
        cautions.append(
            "This crop is transplanted. Seedling/nursery age is recorded but not "
            "added to variety duration because the duration reference stage is "
            "not confirmed by the crop data."
        )

    if duration is not None and not duration_reference_verified:
        codes.append("DURATION_REFERENCE_UNRESOLVED")
        reference_reason = (
            "The variety duration range does not record whether it starts at "
            "sowing or transplanting; timing is conditional until that reference "
            "stage is verified."
        )
        reason_by_code["DURATION_REFERENCE_UNRESOLVED"] = reference_reason
        reasons.append(reference_reason)

    if duration is None or prep is None:
        timing_status = "unknown"
    elif (
        not duration_reference_verified
        or not prep["source_ids"]
    ):
        timing_status = "conditional"
    else:
        timing_status = "known"

    primary_code = _primary_code(codes)
    primary_reason = reason_by_code.get(primary_code)

    return {
        "crop_id": _text(profile, "crop_id"),
        "name_en": _text(profile, "name_en"),
        "name_bn": _text(profile, "name_bn"),
        "reference_variety": _text(profile, "reference_variety"),
        "family": _text(profile, "family"),
        "establishment_method": establishment,
        "planting_range": _iso_range(*planting),
        "duration": (
            {
                "min_days": duration[0],
                "max_days": duration[1],
                "reference_verified": bool(duration_reference_verified),
                "precision": _text(profile, "duration_precision"),
                "decision_source": _text(profile, "decision_duration_source"),
            }
            if duration is not None
            else None
        ),
        "harvest_range": _iso_range(*harvest) if harvest is not None else None,
        "preparation_range": (
            {
                "min_days": prep["min_days"],
                "max_days": prep["max_days"],
                "source_ids": list(prep["source_ids"]),
            }
            if prep is not None
            else None
        ),
        "ready_range": _iso_range(*ready) if ready is not None else None,
        "timing_status": timing_status,
        "code": primary_code,
        "timing_code": primary_code,
        "timing_codes": _dedupe(codes),
        "reason": primary_reason,
        "reasons": _dedupe(reasons),
        "cautions": _dedupe(cautions),
        "missing_evidence": _dedupe(missing),
        "source_ids": _dedupe(sources),
        "waiting_limit_days": limit,
        "nursery_age_days": seedling,
        "nursery_age_added": False,
    }


def calculate_next_planting(
    ready_range: dict | None,
    window: dict,
    preparation_known: bool,
) -> dict:
    """Resolve the next planting range inside one crop window.

    ``window`` uses the calendar evaluator's names:
    ``preferred_start``, ``preferred_end``, optional ``supported_late_end``,
    optional ``window_start`` (defaults to ``preferred_start``), and optional
    ``reference_date``.

    When ``preparation_known`` is false, the result is explicitly window-only:
    preparation/readiness is unknown, so the crop is not claimed to follow on
    time even though a window range is shown.
    """
    parsed = _parse_window(window)
    if preparation_known:
        if ready_range is None:
            raise ValueError(
                "preparation_known=True requires a known ready_range"
            )
        ready = _parse_range(ready_range, "ready_range")
        return _next_from_ready(ready, parsed)
    return _next_from_window(parsed)


def calculate_waiting(
    next_planting_range: dict | None,
    ready_range: dict | None,
    harvest_range: dict | None,
    preparation_known: bool,
    latest_invalid: bool = False,
) -> dict:
    """Return waiting and total between-crop interval ranges.

    Waiting is ``next planting - ready`` and total is ``next planting -
    harvest``. Both are ``None`` when preparation or readiness is unknown.
    When the latest realization is invalid (the latest next planting is clipped
    below the latest ready/harvest endpoint), only the earliest pairing is
    returned and the latest endpoints are ``None``.
    """
    if (
        not preparation_known
        or next_planting_range is None
        or ready_range is None
        or harvest_range is None
    ):
        return {
            "waiting_range": None,
            "total_interval_range_days": None,
            "latest_invalid": bool(latest_invalid),
        }

    next_range = _parse_range(next_planting_range, "next_planting_range")
    ready = _parse_range(ready_range, "ready_range")
    harvest = _parse_range(harvest_range, "harvest_range")

    latest_invalid = bool(latest_invalid) or (
        next_range[1] < ready[1] or next_range[1] < harvest[1]
    )
    if latest_invalid:
        waiting_min = (next_range[0] - ready[0]).days
        if waiting_min < 0:
            return {
                "waiting_range": None,
                "total_interval_range_days": None,
                "latest_invalid": True,
            }
        total_min = (next_range[0] - harvest[0]).days
        return {
            "waiting_range": {"min": waiting_min, "max": None},
            "total_interval_range_days": {"min": total_min, "max": None},
            "latest_invalid": True,
        }

    waiting = _range_difference(next_range, ready)
    total = _range_difference(next_range, harvest)
    return {
        "waiting_range": waiting,
        "total_interval_range_days": total,
        "latest_invalid": False,
    }


def evaluate_waiting_limit(
    waiting_range: dict | None,
    max_waiting_days: int | None,
) -> dict:
    """Classify a waiting range against the configured product limit.

    The limit is a product relevance cutoff, not a sourced agronomic maximum.
    Equality at the limit is inclusive and returns ``within``.
    """
    limit = _validate_limit(max_waiting_days)
    if limit is None:
        return {
            "status": "not_configured",
            "limit_days": None,
            "basis": "not_configured",
            "reason": (
                "No maximum waiting policy is configured; long waits are shown "
                "but are not cut off."
            ),
        }

    if waiting_range is None:
        return {
            "status": "unknown",
            "limit_days": limit,
            "basis": "product_policy",
            "reason": (
                "Waiting cannot be calculated because preparation or field "
                "readiness is unknown."
            ),
        }

    waiting = _validate_days_range(
        waiting_range, "waiting_range", allow_null_max=True
    )
    if waiting["max"] is None:
        if waiting["min"] > limit:
            status = "exceeds"
            reason = (
                f"The earliest waiting ({waiting['min']} days) already exceeds "
                f"this explorer's maximum waiting gap of {limit} days; the latest "
                "is unknown because the latest next-planting realization is "
                "invalid. The limit is a product relevance cutoff, not a "
                "biological impossibility."
            )
        else:
            status = "partial"
            reason = (
                f"The earliest waiting ({waiting['min']} days) is within the "
                f"configured maximum of {limit} days, but the latest waiting is "
                "unknown because the latest next-planting realization is invalid; "
                "the branch remains conditional."
            )
    elif waiting["max"] <= limit:
        status = "within"
        reason = (
            f"The whole waiting range ({waiting['min']}-{waiting['max']} days) "
            f"is within the configured maximum of {limit} days."
        )
    elif waiting["min"] <= limit:
        status = "partial"
        reason = (
            f"Part of the waiting range exceeds the configured maximum of "
            f"{limit} days; the branch remains conditional."
        )
    else:
        status = "exceeds"
        reason = (
            f"The whole waiting range exceeds this explorer's maximum waiting "
            f"gap of {limit} days. The limit is a product relevance cutoff, not "
            "a biological impossibility."
        )
    return {
        "status": status,
        "limit_days": limit,
        "basis": "product_policy",
        "reason": reason,
    }


def _next_from_ready(ready: tuple[dt.date, dt.date], window: dict) -> dict:
    start = max(ready[0], window["window_start"])
    latest = max(ready[1], window["window_start"])
    support_end = window["supported_late_end"] or window["preferred_end"]
    clipped = False

    if start > support_end:
        return _next_result(
            None,
            "unsupported",
            "NEXT_PLANTING_OUTSIDE_SUPPORTED_WINDOW",
            (
                "Even the earliest field-ready date falls after the documented "
                "supported planting end; this next-crop window is not supported."
            ),
            window,
            "unsupported",
            False,
        )

    if latest > support_end:
        latest = support_end
        clipped = True
        status = "caution"
        code = "NEXT_PLANTING_LATEST_CLIPPED"
        reason = (
            "The latest candidate next planting exceeded the documented "
            "supported-late end and was clipped to that end. The uncertainty is "
            "exposed rather than averaged."
        )
    elif latest > window["preferred_end"]:
        status = "caution"
        code = "NEXT_PLANTING_LATE_WINDOW"
        reason = (
            "The next planting range extends into the documented supported-late "
            "window; late planting carries documented risk."
        )
    else:
        status = "pass"
        code = "NEXT_PLANTING_WITHIN_PREFERRED"
        reason = "The next planting range lies inside the documented preferred window."

    return _next_result(
        {"earliest": start.isoformat(), "latest": latest.isoformat()},
        status,
        code,
        reason,
        window,
        "known" if status == "pass" else "conditional",
        clipped,
    )


def _next_from_window(window: dict) -> dict:
    reference = window["reference_date"] or window["window_start"]
    support_end = window["supported_late_end"] or window["preferred_end"]

    if reference > support_end:
        return _next_result(
            None,
            "unsupported",
            "NEXT_PLANTING_OUTSIDE_SUPPORTED_WINDOW",
            (
                "The reference date is after the documented supported planting "
                "end; no next planting range can be claimed for this window."
            ),
            window,
            "unsupported",
            False,
        )

    if reference > window["preferred_end"]:
        late = window["supported_late_end"]
        if late is None or reference > late:
            return _next_result(
                None,
                "unsupported",
                "NEXT_PLANTING_OUTSIDE_SUPPORTED_WINDOW",
                (
                    "The reference date is after the preferred window and no "
                    "usable late support exists; the next planting range is "
                    "unknown rather than assumed."
                ),
                window,
                "unsupported",
                False,
            )
        start = max(reference, window["preferred_end"] + dt.timedelta(days=1))
        latest = late
    else:
        start = max(reference, window["window_start"])
        latest = window["preferred_end"]

    if start > latest:
        return _next_result(
            None,
            "unsupported",
            "NEXT_PLANTING_OUTSIDE_SUPPORTED_WINDOW",
            "The resolved window range is empty; no next planting is shown.",
            window,
            "unsupported",
            False,
        )

    return _next_result(
        {"earliest": start.isoformat(), "latest": latest.isoformat()},
        "unknown",
        "PREPARATION_EVIDENCE_MISSING",
        (
            "Preparation time is unknown, so the crop window range is shown only "
            "as the next planting opportunity. This does not claim that the crop "
            "completes in time."
        ),
        window,
        "unknown",
        False,
        timing_basis="window_only_preparation_unknown",
    )


def _next_result(
    next_range: dict | None,
    status: str,
    code: str,
    reason: str,
    window: dict,
    timing_status: str,
    latest_clipped: bool,
    timing_basis: str = "ready_dates",
) -> dict:
    return {
        "next_planting_range": next_range,
        "status": status,
        "code": code,
        "reason": reason,
        "timing_basis": timing_basis,
        "timing_status": timing_status,
        "latest_clipped": latest_clipped,
        "window": {
            "preferred_start": window["preferred_start"].isoformat(),
            "preferred_end": window["preferred_end"].isoformat(),
            "supported_late_end": (
                window["supported_late_end"].isoformat()
                if window["supported_late_end"] is not None
                else None
            ),
            "window_start": window["window_start"].isoformat(),
            "reference_date": (
                window["reference_date"].isoformat()
                if window["reference_date"] is not None
                else None
            ),
        },
        "source_ids": list(window["source_ids"]),
    }


def _parse_window(window: dict) -> dict:
    if not isinstance(window, dict):
        raise TypeError("window must be a dict with preferred_start/preferred_end")
    preferred_start = _coerce_date(
        window.get("preferred_start", window.get("start")), "preferred_start"
    )
    preferred_end = _coerce_date(
        window.get("preferred_end", window.get("end")), "preferred_end"
    )
    if preferred_start > preferred_end:
        raise ValueError("preferred_start cannot be after preferred_end")
    late = window.get("supported_late_end", window.get("late_end"))
    supported_late_end = (
        _coerce_date(late, "supported_late_end") if late is not None else None
    )
    if supported_late_end is not None and supported_late_end < preferred_end:
        raise ValueError("supported_late_end cannot precede preferred_end")
    window_start = window.get("window_start")
    start = (
        _coerce_date(window_start, "window_start")
        if window_start is not None
        else preferred_start
    )
    reference = window.get("reference_date", window.get("reference"))
    reference_date = (
        _coerce_date(reference, "reference_date") if reference is not None else None
    )
    sources = window.get("source_ids")
    if isinstance(sources, str):
        sources = [sources]
    if not isinstance(sources, (list, tuple)):
        sources = []
    return {
        "preferred_start": preferred_start,
        "preferred_end": preferred_end,
        "supported_late_end": supported_late_end,
        "window_start": start,
        "reference_date": reference_date,
        "source_ids": _dedupe(
            str(value).strip()
            for value in sources
            if value is not None and str(value).strip()
        ),
    }


def _duration_range(profile: dict) -> tuple[tuple[int, int] | None, str | None]:
    values = []
    for field in _DURATION_FIELDS:
        value = profile.get(field)
        if value is None:
            values.append(None)
            continue
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            return None, "DURATION_EVIDENCE_INVALID"
        values.append(value)

    if values[0] is None or values[1] is None:
        return None, "DURATION_EVIDENCE_MISSING"
    if values[0] > values[1]:
        return None, "DURATION_EVIDENCE_INVALID"
    return (values[0], values[1]), None


def _normalize_preparation(
    preparation: dict | None,
) -> tuple[dict | None, str | None, str | None]:
    if preparation is None:
        return (
            None,
            "PREPARATION_EVIDENCE_MISSING",
            (
                "No preparation-time evidence was supplied for this crop; harvest "
                "is known but field readiness is unknown, never zero."
            ),
        )
    if not isinstance(preparation, dict):
        return (
            None,
            "PREPARATION_EVIDENCE_INVALID",
            "Preparation evidence must be a dict with min_days and max_days.",
        )

    minimum = preparation.get("min_days")
    maximum = preparation.get("max_days")
    if minimum is None or maximum is None:
        return (
            None,
            "PREPARATION_EVIDENCE_MISSING",
            "Preparation days are incomplete; field readiness remains unknown.",
        )
    for value, name in ((minimum, "min_days"), (maximum, "max_days")):
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            return (
                None,
                "PREPARATION_EVIDENCE_INVALID",
                f"Preparation {name} must be a non-negative integer.",
            )
    if minimum > maximum:
        return (
            None,
            "PREPARATION_EVIDENCE_INVALID",
            "Preparation min_days cannot exceed max_days.",
        )

    sources = preparation.get("source_ids")
    if isinstance(sources, str):
        sources = [sources]
    if not isinstance(sources, (list, tuple)):
        sources = []
    return (
        {
            "min_days": minimum,
            "max_days": maximum,
            "source_ids": _dedupe(
                str(value).strip()
                for value in sources
                if value is not None and str(value).strip()
            ),
        },
        None,
        None,
    )


def _parse_range(value: dict | None, field: str) -> tuple[dt.date, dt.date]:
    if not isinstance(value, dict):
        raise TypeError(f"{field} must be a dict with earliest and latest")
    earliest = _coerce_date(value.get("earliest"), f"{field}.earliest")
    latest = _coerce_date(value.get("latest"), f"{field}.latest")
    if earliest > latest:
        raise ValueError(f"{field}.earliest cannot be after latest")
    return earliest, latest


def _validate_days_range(
    value: dict, field: str, allow_null_max: bool = False
) -> dict:
    if not isinstance(value, dict):
        raise TypeError(f"{field} must be a dict with min and max")
    minimum = value.get("min")
    maximum = value.get("max")
    if isinstance(minimum, bool) or not isinstance(minimum, int) or minimum < 0:
        raise ValueError(f"{field}.min must be a non-negative integer")
    if maximum is None:
        if not allow_null_max:
            raise ValueError(f"{field}.max must be a non-negative integer")
    else:
        if (
            isinstance(maximum, bool)
            or not isinstance(maximum, int)
            or maximum < 0
        ):
            raise ValueError(f"{field}.max must be a non-negative integer")
        if minimum > maximum:
            raise ValueError(f"{field}.min cannot exceed max")
    return {"min": minimum, "max": maximum}


def _range_difference(
    later: tuple[dt.date, dt.date], earlier: tuple[dt.date, dt.date]
) -> dict:
    first = (later[0] - earlier[0]).days
    second = (later[1] - earlier[1]).days
    if first < 0 or second < 0:
        raise ValueError("later range cannot precede the earlier range")
    return {"min": min(first, second), "max": max(first, second)}


def _coerce_date(value: object, field: str) -> dt.date:
    if isinstance(value, dt.datetime):
        return value.date()
    if isinstance(value, dt.date):
        return value
    if isinstance(value, str):
        try:
            return dt.date.fromisoformat(value.strip())
        except ValueError as exc:
            raise ValueError(
                f"{field} must be an ISO date (YYYY-MM-DD): {value!r}"
            ) from exc
    raise TypeError(f"{field} must be an ISO date string or date")


def _validate_limit(value: int | None) -> int | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError("max_waiting_days must be an integer or None")
    if value < 0:
        raise ValueError("max_waiting_days cannot be negative")
    return value


def _seedling_age(profile: dict) -> dict | None:
    minimum = profile.get("seedling_age_min_days")
    maximum = profile.get("seedling_age_max_days")
    if minimum is None and maximum is None:
        return None
    return {"min_days": minimum, "max_days": maximum}


def _primary_code(codes: list[str]) -> str | None:
    for code in (
        "DURATION_EVIDENCE_MISSING",
        "DURATION_EVIDENCE_INVALID",
        "PREPARATION_EVIDENCE_MISSING",
        "PREPARATION_EVIDENCE_INVALID",
        "DURATION_REFERENCE_UNRESOLVED",
        "PREPARATION_SOURCE_MISSING",
    ):
        if code in codes:
            return code
    return None


def _duration_reason(code: str) -> str:
    if code == "DURATION_EVIDENCE_INVALID":
        return (
            "DURATION_EVIDENCE_INVALID: the variety duration values are not a "
            "valid non-negative min/max range, so harvest timing is unknown."
        )
    return (
        "DURATION_EVIDENCE_MISSING: the crop profile has no variety duration "
        "range, so harvest and readiness timing are unknown rather than zero."
    )


def _iso_range(earliest: dt.date, latest: dt.date) -> dict:
    return {"earliest": earliest.isoformat(), "latest": latest.isoformat()}


def _text(profile: dict, field: str) -> str | None:
    value = profile.get(field)
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _dedupe(values) -> list:
    return list(dict.fromkeys(values))
