"""Deterministic three-crop branch expansion (v1.md §10, §11, §14.4).

One shared evaluator path serves every crop. Calendar fit, soil/water fit,
timeline, and rotation checks are reused; the only crop-specific facts come
from the profiles and caller-supplied preparation evidence.

A branch has exactly three fully evaluated crops and two transitions. Paths
that hit an unsupported calendar/soil check, a missing duration, or a waiting
limit that exceeds the product cutoff are kept in ``excluded_paths`` and never
appear in ``branches``. Unknowns remain visible and make a branch conditional.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import json

from src.calendar_evaluator import evaluate_calendar_fit
from src.rotation import evaluate_rotation
from src.soil_water import WATER_ACCESS_VALUES, evaluate_soil_water
from src.timeline import (
    build_crop_timeline,
    calculate_next_planting,
    calculate_waiting,
    evaluate_waiting_limit,
)

# Calendar combination is deliberately stricter for missing evidence than for
# a documented caution: unsupported > unknown > caution > pass (v1.md §6.1).
_CALENDAR_PRECEDENCE = {"pass": 0, "caution": 1, "unknown": 2, "unsupported": 3}


def expand_branches(
    profiles: dict,
    start_date: dt.date | str,
    water_access: str = "unknown",
    soil_evidence: dict | None = None,
    preparation_lookup: object = None,
    max_waiting_days: int | None = None,
    max_initial_wait_days: int | None = None,
    duration_reference_verified: bool = False,
    duration_reference_verified_crop_ids: object = None,
    environment: dict | None = None,
    max_branches: int | None = None,
) -> dict:
    """Expand every supported three-crop path from ``start_date``.

    ``preparation_lookup`` may be a ``{crop_id: preparation}`` mapping, one
    preparation dict applied to every crop, a callable ``crop_id -> preparation``
    or ``None``. Preparation values are never read from the crop CSV.
    """
    if not isinstance(profiles, dict) or not profiles:
        raise ValueError("profiles must be a non-empty dict keyed by crop_id")
    if water_access not in WATER_ACCESS_VALUES:
        raise ValueError(
            "water_access must be one of " + ", ".join(WATER_ACCESS_VALUES)
        )
    if not isinstance(duration_reference_verified, bool):
        raise TypeError("duration_reference_verified must be a bool")
    verified_crop_ids = _verified_crop_ids(
        duration_reference_verified,
        duration_reference_verified_crop_ids,
        profiles,
    )
    transition_limit = _validate_limit(max_waiting_days)
    initial_limit = _validate_limit(
        max_initial_wait_days, "max_initial_wait_days"
    )
    branch_cap = _validate_max_branches(max_branches)
    start = _coerce_date(start_date, "start_date")

    crop_ids = sorted(profiles, key=str)
    excluded = _ExcludedPaths()
    soil_cache: dict[object, dict] = {}

    def soil_water(profile: dict) -> dict:
        key = profile.get("crop_id")
        if key is None:
            key = id(profile)
        if key not in soil_cache:
            soil_cache[key] = evaluate_soil_water(
                profile,
                water_access=water_access,
                soil_evidence=soil_evidence,
                environment=environment,
            )
        return soil_cache[key]

    roots: list[dict] = []
    for crop_id in crop_ids:
        profile = profiles[crop_id]
        calendar = evaluate_calendar_fit(profile, start, initial_limit)
        if calendar["status"] not in ("pass", "caution"):
            rolled_calendar, rolled_range, roll_error = _roll_root_window(
                profile, calendar, start, initial_limit
            )
            if roll_error is not None:
                excluded.add([crop_id], 1, roll_error[0], roll_error[1])
                continue
            if rolled_calendar is None:
                excluded.add(
                    [crop_id], 1, calendar["code"], calendar["reason"]
                )
                continue
            calendar = rolled_calendar
            planting_range = rolled_range
        else:
            planting_range, window_error = _root_planting_range(
                profile, calendar, start, initial_limit
            )
            if window_error is not None:
                excluded.add([crop_id], 1, window_error[0], window_error[1])
                continue

        timeline = build_crop_timeline(
            profile,
            planting_range,
            _resolve_preparation(preparation_lookup, crop_id),
            _duration_verified(
                crop_id, duration_reference_verified, verified_crop_ids
            ),
            transition_limit,
        )
        if timeline["harvest_range"] is None:
            excluded.add(
                [crop_id],
                1,
                timeline["timing_code"] or "DURATION_EVIDENCE_MISSING",
                timeline["reason"] or "Harvest timing is unknown.",
            )
            continue

        combined = soil_water(profile)
        unsupported = _unsupported_check(combined)
        if unsupported is not None:
            excluded.add([crop_id], 1, unsupported["code"], unsupported["reason"])
            continue

        node = _crop_node(
            position=1,
            profile=profile,
            planting_range=planting_range,
            calendar=calendar,
            rotation=None,
            timeline=timeline,
            soil_water_result=combined,
        )
        roots.append(
            {
                "crop_id": crop_id,
                "profile": profile,
                "planting_range": planting_range,
                "timeline": timeline,
                "node": node,
            }
        )

    branches: list[dict] = []
    for root in roots:
        second_candidates: list[dict] = []
        for crop_id in crop_ids:
            result, failure = _try_next(
                profile=profiles[crop_id],
                previous_profile=root["profile"],
                previous_timeline=root["timeline"],
                previous_position=1,
                path_profiles=[root["profile"]],
                preparation_lookup=preparation_lookup,
                duration_reference_verified=duration_reference_verified,
                duration_reference_verified_crop_ids=verified_crop_ids,
                max_waiting_days=transition_limit,
                soil_water=soil_water,
            )
            if failure is not None:
                excluded.add(
                    [root["crop_id"], crop_id],
                    2,
                    failure[0],
                    failure[1],
                )
                continue
            node, timeline, transition = result
            second_candidates.append(
                {
                    "crop_id": crop_id,
                    "profile": profiles[crop_id],
                    "timeline": timeline,
                    "node": node,
                    "transition": transition,
                }
            )

        for second in second_candidates:
            third_candidates: list[dict] = []
            for crop_id in crop_ids:
                result, failure = _try_next(
                    profile=profiles[crop_id],
                    previous_profile=second["profile"],
                    previous_timeline=second["timeline"],
                    previous_position=2,
                    path_profiles=[root["profile"], second["profile"]],
                    preparation_lookup=preparation_lookup,
                    duration_reference_verified=duration_reference_verified,
                    duration_reference_verified_crop_ids=verified_crop_ids,
                    max_waiting_days=transition_limit,
                    soil_water=soil_water,
                )
                if failure is not None:
                    excluded.add(
                        [root["crop_id"], second["crop_id"], crop_id],
                        3,
                        failure[0],
                        failure[1],
                    )
                    continue
                node, timeline, transition = result
                third_candidates.append(
                    {
                        "crop_id": crop_id,
                        "timeline": timeline,
                        "node": node,
                        "transition": transition,
                    }
                )

            if not third_candidates:
                excluded.add(
                    [root["crop_id"], second["crop_id"]],
                    3,
                    "NO_SUPPORTED_THIRD_CROP",
                    "No evaluated crop completed a supported third position.",
                )
                continue

            for third in third_candidates:
                branches.append(
                    _branch(
                        start,
                        [root["node"], second["node"], third["node"]],
                        [second["transition"], third["transition"]],
                    )
                )

    if branch_cap is not None:
        branches = branches[:branch_cap]

    return {
        "start_date": start.isoformat(),
        "request": {
            "start_date": start.isoformat(),
            "water_access": water_access,
            "max_waiting_days": transition_limit,
            "max_initial_wait_days": initial_limit,
            "duration_reference_verified": duration_reference_verified,
            "duration_reference_verified_crop_ids": (
                sorted(verified_crop_ids) if verified_crop_ids is not None else None
            ),
            "max_branches": branch_cap,
        },
        "branches": branches,
        "excluded_paths": excluded.as_list(),
        "uniqueness": check_branch_uniqueness(branches),
    }


def check_branch_uniqueness(branches: list[dict] | tuple[dict, ...]) -> dict:
    """Report duplicate crop sequences and branch IDs without collapsing branches.

    §14.4 makes ``branch_id`` unique for the selected request and ordered
    crop/window choices. The same crop sequence with different ordered windows
    is therefore two branches, not one; duplicate sequences are reported, while
    duplicate branch IDs are a hard failure.
    """
    if not isinstance(branches, (list, tuple)):
        raise TypeError("branches must be a list or tuple of branch dicts")

    branch_ids: list[object] = []
    sequences: dict[tuple, list[dict]] = {}
    for branch in branches:
        if not isinstance(branch, dict):
            raise TypeError("each branch must be a dict")
        crops = branch.get("crops")
        if not isinstance(crops, (list, tuple)):
            raise ValueError("each branch must contain a crops list")
        branch_ids.append(branch.get("branch_id"))
        sequence = tuple(
            crop.get("crop_id") if isinstance(crop, dict) else None
            for crop in crops
        )
        sequences.setdefault(sequence, []).append(branch)

    id_counts: dict[object, int] = {}
    for branch_id in branch_ids:
        id_counts[branch_id] = id_counts.get(branch_id, 0) + 1
    duplicate_branch_ids = [
        branch_id for branch_id, count in id_counts.items() if count > 1
    ]

    duplicate_sequences = []
    for sequence, grouped in sequences.items():
        if len(grouped) < 2:
            continue
        duplicate_sequences.append(
            {
                "crop_ids": list(sequence),
                "branch_ids": [branch.get("branch_id") for branch in grouped],
                "window_keys": [
                    _branch_window_key(branch) for branch in grouped
                ],
            }
        )

    return {
        "branch_count": len(branches),
        "branch_ids_unique": not duplicate_branch_ids,
        "duplicate_branch_ids": duplicate_branch_ids,
        "sequence_count": len(sequences),
        "duplicate_sequences": duplicate_sequences,
        "rule": (
            "v1.md §14.4: branch_id is deterministic and unique for the "
            "selected request and ordered crop/window choices. The same crop "
            "sequence with different ordered windows is two branches with "
            "distinct branch_ids, not one; duplicate crop sequences are "
            "reported without collapsing branches. Duplicate branch_ids are "
            "a hard failure."
        ),
    }


def _branch_window_key(branch: dict) -> str:
    crops = branch.get("crops")
    ranges = (
        [
            crop.get("planting_range") if isinstance(crop, dict) else None
            for crop in crops
        ]
        if isinstance(crops, (list, tuple))
        else []
    )
    return json.dumps(ranges, sort_keys=True, separators=(",", ":"))


def _try_next(
    profile: dict,
    previous_profile: dict,
    previous_timeline: dict,
    previous_position: int,
    path_profiles: list[dict],
    preparation_lookup: object,
    duration_reference_verified: bool,
    duration_reference_verified_crop_ids: set[str] | None,
    max_waiting_days: int | None,
    soil_water,
):
    ready = previous_timeline["ready_range"]
    harvest = previous_timeline["harvest_range"]
    if ready is not None:
        reference = _coerce_date(ready["earliest"], "ready_range.earliest")
        preparation_known = True
    elif harvest is not None:
        reference = _coerce_date(harvest["earliest"], "harvest_range.earliest")
        preparation_known = False
    else:
        return None, (
            "DURATION_EVIDENCE_MISSING",
            "The previous crop has no harvest date, so no next window can be resolved.",
        )

    window, reference_check, error = _resolve_window(
        profile, reference, max_waiting_days
    )
    if error is not None:
        return None, error

    next_planting = calculate_next_planting(
        ready, window, preparation_known
    )
    if next_planting["next_planting_range"] is None:
        return None, (next_planting["code"], next_planting["reason"])

    planting_range = next_planting["next_planting_range"]
    earliest_check = evaluate_calendar_fit(
        profile, planting_range["earliest"], max_waiting_days
    )
    latest_check = evaluate_calendar_fit(
        profile, planting_range["latest"], max_waiting_days
    )
    calendar = _combine_calendar(earliest_check, latest_check)
    if calendar["status"] == "unsupported":
        return None, (calendar["code"], calendar["reason"])

    timeline = build_crop_timeline(
        profile,
        planting_range,
        _resolve_preparation(preparation_lookup, _profile_id(profile)),
        _duration_verified(
            _profile_id(profile),
            duration_reference_verified,
            duration_reference_verified_crop_ids,
        ),
        max_waiting_days,
    )
    if timeline["harvest_range"] is None:
        return None, (
            timeline["timing_code"] or "DURATION_EVIDENCE_MISSING",
            timeline["reason"] or "Harvest timing is unknown.",
        )

    combined = soil_water(profile)
    unsupported = _unsupported_check(combined)
    if unsupported is not None:
        return None, (unsupported["code"], unsupported["reason"])

    rotation = evaluate_rotation(profile, previous_profile, path_profiles)
    node = _crop_node(
        position=previous_position + 1,
        profile=profile,
        planting_range=planting_range,
        calendar=calendar,
        rotation=rotation,
        timeline=timeline,
        soil_water_result=combined,
    )
    if node["status"] == "unsupported":
        return None, ("UNSUPPORTED_CROP_CHECK", "A crop check rejected this node.")

    waiting = calculate_waiting(
        planting_range,
        ready,
        harvest,
        preparation_known,
        latest_invalid=next_planting["latest_clipped"],
    )
    waiting_limit = evaluate_waiting_limit(
        waiting["waiting_range"], max_waiting_days
    )
    if waiting_limit["status"] == "exceeds":
        return None, ("WAITING_LIMIT_EXCEEDED", waiting_limit["reason"])

    transition = _transition(
        previous_position=previous_position,
        previous_profile=previous_profile,
        profile=profile,
        reference=reference,
        preparation_known=preparation_known,
        previous_timeline=previous_timeline,
        window=window,
        reference_check=reference_check,
        next_planting=next_planting,
        planting_range=planting_range,
        calendar=calendar,
        waiting=waiting,
        waiting_limit=waiting_limit,
    )
    return (node, timeline, transition), None


def _root_planting_range(
    profile: dict,
    calendar: dict,
    start: dt.date,
    max_waiting_days: int | None,
):
    details = calendar["details"]
    next_start = details.get("next_window_start")
    if next_start is not None:
        resolved = _coerce_date(next_start, "next_window_start")
        check = evaluate_calendar_fit(profile, resolved, max_waiting_days)
        if check["status"] not in ("pass", "caution"):
            return None, (check["code"], check["reason"])
        details = check["details"]
        preferred_start = _optional_date(details.get("preferred_start"))
        preferred_end = _optional_date(details.get("preferred_end"))
        if preferred_start is None or preferred_end is None:
            return None, (
                "WINDOW_DETAILS_MISSING",
                "The future window could not be attached to dates.",
            )
        earliest = max(resolved, preferred_start)
        if earliest > preferred_end:
            return None, (
                "WINDOW_DETAILS_MISSING",
                "The future window range is empty.",
            )
        return _iso_range(earliest, preferred_end), None

    if calendar["code"] == "LATE_WINDOW":
        preferred_end = _optional_date(details.get("preferred_end"))
        late_end = _optional_date(details.get("supported_late_end"))
        if preferred_end is None or late_end is None:
            return None, (
                "WINDOW_DETAILS_MISSING",
                "The late window could not be attached to dates.",
            )
        earliest = max(start, preferred_end + dt.timedelta(days=1))
        if earliest > late_end:
            return None, (
                "WINDOW_DETAILS_MISSING",
                "The late window range is empty.",
            )
        return _iso_range(earliest, late_end), None

    preferred_start = _optional_date(details.get("preferred_start"))
    preferred_end = _optional_date(details.get("preferred_end"))
    if preferred_start is None or preferred_end is None:
        return None, (
            "WINDOW_DETAILS_MISSING",
            "The preferred window could not be attached to dates.",
        )
    earliest = max(start, preferred_start)
    if earliest > preferred_end:
        return None, (
            "WINDOW_DETAILS_MISSING",
            "The preferred window range is empty.",
        )
    return _iso_range(earliest, preferred_end), None


def _resolve_window(
    profile: dict,
    reference: dt.date,
    max_waiting_days: int | None,
):
    first = evaluate_calendar_fit(profile, reference, max_waiting_days)
    details = first["details"]
    next_start = details.get("next_window_start")
    if next_start is not None:
        resolved = _coerce_date(next_start, "next_window_start")
        wait = (resolved - reference).days
        if max_waiting_days is not None and wait > max_waiting_days:
            return None, _check_summary(first), _limit_error(
                resolved, wait, max_waiting_days
            )
        return _resolve_future_window(
            profile,
            resolved,
            reference,
            max_waiting_days,
            first,
            rolled=first["status"] == "unsupported"
            and max_waiting_days is not None,
        )

    if first["status"] == "unsupported":
        if max_waiting_days is None:
            return None, _check_summary(first), (first["code"], first["reason"])
        resolved = _next_season_start(details)
        if resolved is None:
            return None, _check_summary(first), (first["code"], first["reason"])
        wait = (resolved - reference).days
        if wait < 0 or wait > max_waiting_days:
            return None, _check_summary(first), _limit_error(
                resolved, wait, max_waiting_days
            )
        return _resolve_future_window(
            profile,
            resolved,
            reference,
            max_waiting_days,
            first,
            rolled=True,
        )

    preferred_start = _optional_date(details.get("preferred_start"))
    preferred_end = _optional_date(details.get("preferred_end"))
    if preferred_start is None or preferred_end is None:
        return None, _check_summary(first), (
            "WINDOW_DETAILS_MISSING",
            "The crop window could not be attached to dates.",
        )
    late_end = _optional_date(details.get("supported_late_end"))
    support_end = late_end or preferred_end

    if reference > support_end:
        return None, _check_summary(first), (
            first["code"],
            first["reason"],
        )
    if reference > preferred_end:
        if late_end is None or reference > late_end:
            return None, _check_summary(first), (
                "OUTSIDE_SUPPORTED_WINDOW",
                "The reference date is after the supported window end.",
            )
        window_start = preferred_end + dt.timedelta(days=1)
    else:
        window_start = preferred_start

    window = _window(
        preferred_start,
        preferred_end,
        late_end,
        window_start,
        reference,
        first,
    )
    return window, _check_summary(first), None


def _resolve_future_window(
    profile: dict,
    next_start: dt.date,
    reference: dt.date,
    max_waiting_days: int | None,
    first: dict,
    rolled: bool,
):
    second = evaluate_calendar_fit(profile, next_start, max_waiting_days)
    if second["status"] == "unsupported":
        return None, _check_summary(second), (second["code"], second["reason"])
    details = second["details"]
    preferred_start = _optional_date(details.get("preferred_start"))
    preferred_end = _optional_date(details.get("preferred_end"))
    if preferred_start is None or preferred_end is None:
        return None, _check_summary(second), (
            "WINDOW_DETAILS_MISSING",
            "The future window could not be attached to dates.",
        )
    window = _window(
        preferred_start,
        preferred_end,
        _optional_date(details.get("supported_late_end")),
        preferred_start,
        reference,
        first,
        second,
    )
    if rolled:
        wait = (next_start - reference).days
        future = _future_calendar(
            first, next_start, wait, max_waiting_days, details
        )
        return window, _check_summary(future), None
    return window, _check_summary(first), None


def _roll_root_window(
    profile: dict,
    calendar: dict,
    start: dt.date,
    max_waiting_days: int | None,
):
    if max_waiting_days is None:
        return None, None, None

    details = calendar["details"]
    next_start = details.get("next_window_start")
    if next_start is not None:
        resolved = _coerce_date(next_start, "next_window_start")
        wait = (resolved - start).days
        if wait < 0:
            return None, None, None
        if wait > max_waiting_days:
            return None, None, _limit_error(
                resolved, wait, max_waiting_days
            )
    elif calendar["status"] == "unsupported":
        resolved = _next_season_start(details)
        if resolved is None:
            return None, None, None
        wait = (resolved - start).days
        if wait < 0:
            return None, None, None
        if wait > max_waiting_days:
            return None, None, _limit_error(
                resolved, wait, max_waiting_days
            )
    else:
        return None, None, None

    future = evaluate_calendar_fit(profile, resolved, max_waiting_days)
    if future["status"] not in ("pass", "caution"):
        return None, None, (future["code"], future["reason"])
    future_details = future["details"]
    preferred_start = _optional_date(future_details.get("preferred_start"))
    preferred_end = _optional_date(future_details.get("preferred_end"))
    if (
        preferred_start is None
        or preferred_end is None
        or resolved > preferred_end
    ):
        return None, None, (
            "WINDOW_DETAILS_MISSING",
            "The rolled future window could not be attached to dates.",
        )
    rolled_calendar = _future_calendar(
        calendar, resolved, wait, max_waiting_days, future_details
    )
    planting_range = _iso_range(max(resolved, preferred_start), preferred_end)
    return rolled_calendar, planting_range, None


def _next_season_start(details: dict) -> dt.date | None:
    preferred_start = _optional_date(details.get("preferred_start"))
    if preferred_start is None:
        return None
    try:
        return preferred_start.replace(year=preferred_start.year + 1)
    except ValueError:
        return None


def _future_calendar(
    calendar: dict,
    next_start: dt.date,
    wait: int,
    max_waiting_days: int,
    future_details: dict,
) -> dict:
    result = dict(calendar)
    result["status"] = "caution"
    result["code"] = "FUTURE_WINDOW_WITHIN_LIMIT"
    result["reason"] = (
        f"The next documented preferred window starts {next_start.isoformat()} "
        f"({wait} days after the reference date), within the configured maximum "
        f"of {max_waiting_days} days. This is a future option, not a plant-now "
        "option."
    )
    details = dict(calendar.get("details") or {})
    for field in (
        "preferred_start",
        "preferred_end",
        "supported_late_end",
        "window_start_year",
        "date_precision",
        "hard_deadline_validated",
        "window_basis",
        "window_type",
        "window_guard_readiness",
        "algorithm_use_note",
    ):
        if field in future_details:
            details[field] = future_details[field]
    details.update(
        {
            "plant_now": False,
            "next_window_start": next_start.isoformat(),
            "waiting_days": wait,
            "waiting_limit_days": max_waiting_days,
            "waiting_limit_status": "within_limit",
        }
    )
    result["details"] = details
    return result


def _limit_error(next_start: dt.date, wait: int, limit: int):
    return (
        "FUTURE_WINDOW_EXCEEDS_LIMIT",
        (
            f"The next documented window starts {next_start.isoformat()} "
            f"({wait} days after the reference date), which exceeds this "
            f"explorer's maximum waiting gap of {limit} days. The limit is a "
            "product relevance cutoff, not a scientifically safe maximum and "
            "not a biological impossibility; longer fallow is not claimed "
            "impossible."
        ),
    )


def _window(
    preferred_start: dt.date,
    preferred_end: dt.date,
    late_end: dt.date | None,
    window_start: dt.date,
    reference: dt.date,
    *checks: dict,
) -> dict:
    return {
        "preferred_start": preferred_start,
        "preferred_end": preferred_end,
        "supported_late_end": late_end,
        "window_start": window_start,
        "reference_date": reference,
        "source_ids": _dedupe(
            [
                source
                for check in checks
                for source in check.get("source_ids", [])
            ]
        ),
    }


def _transition(
    previous_position: int,
    previous_profile: dict,
    profile: dict,
    reference: dt.date,
    preparation_known: bool,
    previous_timeline: dict,
    window: dict,
    reference_check: dict,
    next_planting: dict,
    planting_range: dict,
    calendar: dict,
    waiting: dict,
    waiting_limit: dict,
) -> dict:
    reasons: list[str] = []
    cautions: list[str] = []
    missing: list[str] = []
    sources: list[str] = list(window["source_ids"])
    latest_invalid = bool(waiting.get("latest_invalid"))

    if latest_invalid:
        invalid_reason = (
            "The latest next-planting realization was clipped below the latest "
            "field-ready or harvest date; latest waiting and total interval "
            "endpoints are unknown."
        )
        cautions.append(invalid_reason)
        missing.append("latest_waiting_total")

    if next_planting["status"] != "pass":
        reasons.append(f"Next planting: {next_planting['reason']}")
        if next_planting["status"] == "caution":
            cautions.append(next_planting["reason"])
        elif next_planting["status"] == "unknown":
            missing.append("preparation_time")
    if calendar["status"] != "pass":
        reasons.append(f"Calendar: {calendar['reason']}")
        if calendar["status"] == "caution":
            cautions.append(calendar["reason"])
        elif calendar["status"] == "unknown":
            missing.append("calendar_evidence")
    if waiting_limit["status"] == "partial":
        reasons.append(waiting_limit["reason"])
        cautions.append(waiting_limit["reason"])
    elif waiting_limit["status"] == "unknown":
        reasons.append(waiting_limit["reason"])
        missing.append("waiting_days")
    elif waiting_limit["status"] == "not_configured":
        reasons.append(waiting_limit["reason"])
        missing.append("max_waiting_days_policy")

    reasons.extend(previous_timeline["reasons"])
    cautions.extend(previous_timeline["cautions"])
    missing.extend(previous_timeline["missing_evidence"])
    sources.extend(previous_timeline["source_ids"])
    sources.extend(next_planting["source_ids"])
    sources.extend(calendar["source_ids"])

    return {
        "from_position": previous_position,
        "to_position": previous_position + 1,
        "from_crop_id": _profile_id(previous_profile),
        "to_crop_id": _profile_id(profile),
        "reference_date": reference.isoformat(),
        "reference_basis": (
            "earliest_ready"
            if preparation_known
            else "earliest_harvest_preparation_unknown"
        ),
        "window": {
            "preferred_start": window["preferred_start"].isoformat(),
            "preferred_end": window["preferred_end"].isoformat(),
            "supported_late_end": (
                window["supported_late_end"].isoformat()
                if window["supported_late_end"] is not None
                else None
            ),
            "window_start": window["window_start"].isoformat(),
            "reference_date": window["reference_date"].isoformat(),
            "source_ids": list(window["source_ids"]),
        },
        "preparation_range": previous_timeline["preparation_range"],
        "preparation_known": preparation_known,
        "next_planting_range": planting_range,
        "next_planting": {
            "status": next_planting["status"],
            "code": next_planting["code"],
            "reason": next_planting["reason"],
            "timing_basis": next_planting["timing_basis"],
            "timing_status": next_planting["timing_status"],
            "latest_clipped": next_planting["latest_clipped"],
        },
        "waiting_range": waiting["waiting_range"],
        "total_interval_range_days": waiting["total_interval_range_days"],
        "latest_invalid": latest_invalid,
        "calendar_check": calendar,
        "window_reference_check": reference_check,
        "waiting_limit_status": waiting_limit["status"],
        "waiting_limit": waiting_limit,
        "reasons": _dedupe(reasons),
        "cautions": _dedupe(cautions),
        "missing_evidence": _dedupe(missing),
        "source_ids": _dedupe(sources),
    }


def _crop_node(
    position: int,
    profile: dict,
    planting_range: dict,
    calendar: dict,
    rotation: dict | None,
    timeline: dict,
    soil_water_result: dict,
) -> dict:
    checks = {
        "calendar": calendar,
        "soil": soil_water_result["checks"]["soil"],
        "water": soil_water_result["checks"]["water"],
        "rotation": rotation,
    }
    status = _crop_status(checks, timeline)

    reasons: list[str] = []
    cautions: list[str] = []
    missing: list[str] = []
    sources: list[str] = []
    for name, check in checks.items():
        if check is None:
            continue
        sources.extend(check.get("source_ids", []))
        missing.extend(check.get("missing_evidence", []))
        if check["status"] != "pass":
            reasons.append(f"{name}: {check['reason']}")
            if check["status"] == "caution":
                cautions.append(check["reason"])
    reasons.extend(timeline["reasons"])
    cautions.extend(timeline["cautions"])
    missing.extend(timeline["missing_evidence"])
    sources.extend(timeline["source_ids"])

    return {
        "position": position,
        "crop_id": _profile_id(profile),
        "name_en": _profile_text(profile, "name_en"),
        "name_bn": _profile_text(profile, "name_bn"),
        "reference_variety": _profile_text(profile, "reference_variety"),
        "family": _profile_text(profile, "family"),
        "establishment_method": _profile_text(profile, "establishment_method"),
        "status": status,
        "checks": checks,
        "rotation": rotation,
        "planting_range": planting_range,
        "harvest_range": timeline["harvest_range"],
        "preparation_range": timeline["preparation_range"],
        "ready_range": timeline["ready_range"],
        "duration": timeline["duration"],
        "timing_status": timeline["timing_status"],
        "timing_code": timeline["timing_code"],
        "timing_codes": timeline["timing_codes"],
        "nursery_age_days": timeline["nursery_age_days"],
        "nursery_age_added": False,
        "reasons": _dedupe(reasons),
        "cautions": _dedupe(cautions),
        "missing_evidence": _dedupe(missing),
        "source_ids": _dedupe(sources),
    }


def _crop_status(checks: dict, timeline: dict) -> str:
    statuses = [
        check["status"] for check in checks.values() if isinstance(check, dict)
    ]
    if "unsupported" in statuses:
        return "unsupported"
    if any(status in ("caution", "unknown") for status in statuses):
        return "conditional"
    if (
        timeline["timing_status"] != "known"
        or timeline["cautions"]
        or timeline["missing_evidence"]
    ):
        return "conditional"
    return "candidate"


def _branch(start: dt.date, crops: list[dict], transitions: list[dict]) -> dict:
    identity = {
        "start_date": start.isoformat(),
        "crops": [
            {
                "crop_id": crop["crop_id"],
                "planting_range": crop["planting_range"],
            }
            for crop in crops
        ],
    }
    digest = hashlib.sha256(
        json.dumps(identity, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()[:12]
    initial_wait_days = max(
        0,
        (
            dt.date.fromisoformat(crops[0]["planting_range"]["earliest"]) - start
        ).days,
    )

    candidate = all(crop["status"] == "candidate" for crop in crops) and all(
        _transition_ok(transition) for transition in transitions
    )
    reasons: list[str] = []
    cautions: list[str] = []
    missing: list[str] = []
    sources: list[str] = []
    for crop in crops:
        reasons.extend(crop["reasons"])
        cautions.extend(crop["cautions"])
        missing.extend(crop["missing_evidence"])
        sources.extend(crop["source_ids"])
    for transition in transitions:
        reasons.extend(transition["reasons"])
        cautions.extend(transition["cautions"])
        missing.extend(transition["missing_evidence"])
        sources.extend(transition["source_ids"])

    return {
        "branch_id": "b_" + digest,
        "status": "candidate" if candidate else "conditional",
        "initial_wait_days": initial_wait_days,
        "crops": crops,
        "transitions": transitions,
        "reasons": _dedupe(reasons),
        "cautions": _dedupe(cautions),
        "missing_evidence": _dedupe(missing),
        "source_ids": _dedupe(sources),
    }


def _transition_ok(transition: dict) -> bool:
    if transition["next_planting"]["status"] != "pass":
        return False
    if transition["calendar_check"]["status"] != "pass":
        return False
    if transition["waiting_limit_status"] != "within":
        return False
    if transition.get("latest_invalid"):
        return False
    if transition["waiting_range"] is None:
        return False
    if transition["waiting_range"].get("max") is None:
        return False
    total = transition.get("total_interval_range_days")
    if total is None or total.get("max") is None:
        return False
    return True


def _combine_calendar(earliest: dict, latest: dict) -> dict:
    status = max(
        (earliest, latest), key=lambda check: _CALENDAR_PRECEDENCE[check["status"]]
    )["status"]
    dominant = max(
        (earliest, latest),
        key=lambda check: (_CALENDAR_PRECEDENCE[check["status"]], check is latest),
    )
    combined = dict(dominant)
    combined["status"] = status
    combined["checks"] = {"earliest": earliest, "latest": latest}
    combined["main_label"] = "latest" if dominant is latest else "earliest"
    return combined


def _check_summary(check: dict) -> dict:
    return {
        "status": check["status"],
        "code": check["code"],
        "reason": check["reason"],
        "source_ids": list(check["source_ids"]),
    }


def _unsupported_check(combined: dict) -> dict | None:
    for check in combined["checks"].values():
        if check["status"] == "unsupported":
            return check
    return None


def _verified_crop_ids(
    verified: bool, crop_ids: object, profiles: dict
) -> set[str] | None:
    if crop_ids is None:
        return None
    if isinstance(crop_ids, str) or not isinstance(
        crop_ids, (list, tuple, set, frozenset)
    ):
        raise TypeError(
            "duration_reference_verified_crop_ids must be a collection of crop IDs or None"
        )
    if not verified:
        raise ValueError(
            "duration_reference_verified_crop_ids requires duration_reference_verified=True"
        )
    resolved = {str(crop_id) for crop_id in crop_ids}
    unknown = sorted(resolved - {str(crop_id) for crop_id in profiles})
    if unknown:
        raise ValueError(
            "duration_reference_verified_crop_ids contains unknown crop IDs: "
            + ", ".join(unknown)
        )
    return resolved


def _duration_verified(
    crop_id: str, verified: bool, crop_ids: set[str] | None
) -> bool:
    if not verified:
        return False
    return crop_ids is None or crop_id in crop_ids


def _resolve_preparation(lookup: object, crop_id: str) -> dict | None:
    if lookup is None:
        return None
    if callable(lookup):
        return lookup(crop_id)
    if isinstance(lookup, dict):
        if "min_days" in lookup or "max_days" in lookup:
            return lookup
        return lookup.get(crop_id)
    raise TypeError(
        "preparation_lookup must be a mapping, a preparation dict, a callable, or None"
    )


def _profile_id(profile: dict) -> str:
    value = profile.get("crop_id")
    return str(value) if value is not None else ""


def _profile_text(profile: dict, field: str) -> str | None:
    value = profile.get(field)
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _optional_date(value: object) -> dt.date | None:
    if value is None:
        return None
    return _coerce_date(value, "date")


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


def _iso_range(earliest: dt.date, latest: dt.date) -> dict:
    return {"earliest": earliest.isoformat(), "latest": latest.isoformat()}


def _validate_limit(
    value: int | None, name: str = "max_waiting_days"
) -> int | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{name} must be an integer or None")
    if value < 0:
        raise ValueError(f"{name} cannot be negative")
    return value


def _validate_max_branches(value: int | None) -> int | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError("max_branches must be an integer or None")
    if value < 0:
        raise ValueError("max_branches cannot be negative")
    return value


def _dedupe(values) -> list:
    return list(dict.fromkeys(values))


class _ExcludedPaths:
    """Compact insertion-ordered, deduplicated exclusion explanations."""

    def __init__(self) -> None:
        self._items: dict[tuple, dict] = {}

    def add(
        self,
        crop_ids: list[str],
        at_position: int,
        code: str,
        reason: str,
    ) -> None:
        key = (tuple(crop_ids), at_position, code)
        if key in self._items:
            return
        self._items[key] = {
            "crop_ids": list(crop_ids),
            "at_position": at_position,
            "code": code,
            "reason": reason,
        }

    def as_list(self) -> list[dict]:
        return list(self._items.values())
