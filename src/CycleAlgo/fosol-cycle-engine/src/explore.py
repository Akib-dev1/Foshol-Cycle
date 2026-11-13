"""Explore response envelope (v1.md §14.3-14.4).

Spec decision: when ``first_crop_id`` is null, ``branches`` is empty because no
first crop has been selected, but ``branch_summary`` and status describe the
full internal expansion. Once a first crop is selected, only branches rooted at
that crop are returned and summarized.
"""

from __future__ import annotations

import copy
import datetime as dt

from src.branch_expander import expand_branches
from src.branch_metrics import (
    build_economics_metrics,
    build_resource_metrics,
    calculate_completion_time,
    calculate_diversity_metrics,
    rank_branches,
)
from src.calendar_evaluator import evaluate_calendar_fit
from src.climate_metrics import build_climate_metrics, strip_climate_raw
from src.outlook import (
    build_outlook,
    build_seasonal_ranges,
    sanitize_observations,
)
from src.outlook_config import OUTLOOK_LABEL
from src.request_validation import validate_explore_request
from src.soil_water import evaluate_soil_water

_DEFAULT_CONFIG = {
    "max_initial_wait_days": None,
    "max_waiting_days": None,
    "analysis_start_year": 1991,
    "analysis_end_year": 2025,
    "last_complete_data_date": None,
    "warning_config": None,
    "max_branches": None,
}
_CLIMATE_CHECK = {
    "status": "unknown",
    "code": "CLIMATE_EXPOSURE_DEFERRED",
    "reason": (
        "Current-season climate exposure (§6.2) is deferred; no climate "
        "evidence is applied to this option."
    ),
    "source_ids": [],
    "missing_evidence": ["current_season_climate_exposure"],
}
_SMAP_LABEL = "Context only - no effect on status or ranking"
_SUPPORTED_DISTRICTS = {"rajshahi"}


def explore(
    payload: dict,
    *,
    profiles: dict,
    config: dict | None = None,
    environment: dict | None = None,
    smap_context: dict | None = None,
    soil_evidence: dict | None = None,
    preparation_lookup: object = None,
    duration_reference_verified: bool = False,
    duration_reference_verified_crop_ids: object = None,
    environment_error: str | None = None,
    now: dt.datetime | dt.date | None = None,
    retain_climate_raw: bool = False,
) -> dict:
    """Return the §14.3 explore envelope.

    ``soil_evidence``, ``preparation_lookup``, and duration-reference
    verification are trusted host/server inputs, never request-payload fields.
    Missing evidence remains unknown. ``retain_climate_raw`` is an internal
    offline-demo hook; the API path leaves it false and keeps the normal stripped
    response shape.
    """
    if not isinstance(retain_climate_raw, bool):
        raise TypeError("retain_climate_raw must be a bool")
    if soil_evidence is not None and not isinstance(soil_evidence, dict):
        raise TypeError("soil_evidence must be a dict or None")
    if preparation_lookup is not None and not callable(preparation_lookup) and not isinstance(
        preparation_lookup, dict
    ):
        raise TypeError(
            "preparation_lookup must be a mapping, a preparation dict, a callable, or None"
        )
    if not isinstance(duration_reference_verified, bool):
        raise TypeError("duration_reference_verified must be a bool")
    known = set(profiles) if isinstance(profiles, dict) else set()
    request = validate_explore_request(payload, known)
    settings = _config(config)
    request = _request_with_limits(request, settings)
    generated_at = _generated_at(now)
    context = _environment_context(smap_context)

    district = _district(request["district_id"])
    if request["district_id"] not in _SUPPORTED_DISTRICTS:
        return _unsupported_district_response(
            request, district, settings, context, generated_at
        )
    if not isinstance(profiles, dict) or not profiles:
        return _data_unavailable_response(
            request, district, settings, context, generated_at
        )

    expansion = expand_branches(
        profiles,
        request["start_date"],
        water_access=request["water_access"],
        soil_evidence=soil_evidence,
        preparation_lookup=preparation_lookup,
        duration_reference_verified=duration_reference_verified,
        duration_reference_verified_crop_ids=duration_reference_verified_crop_ids,
        max_waiting_days=settings["max_waiting_days"],
        max_initial_wait_days=settings["max_initial_wait_days"],
        environment=environment,
        max_branches=settings["max_branches"],
    )
    internal_branches = expansion["branches"]
    excluded_paths = expansion["excluded_paths"]

    if request["first_crop_id"] is None:
        summary_branches = internal_branches
        summary_exclusions = excluded_paths
        returned_branches = []
    else:
        first = request["first_crop_id"]
        summary_branches = [
            branch
            for branch in internal_branches
            if branch["crops"][0]["crop_id"] == first
        ]
        summary_exclusions = [
            exclusion
            for exclusion in excluded_paths
            if exclusion.get("crop_ids")
            and exclusion["crop_ids"][0] == first
        ]
        returned_branches = summary_branches

    crop_options = _crop_options(
        profiles,
        request["start_date"],
        request["water_access"],
        soil_evidence,
        environment,
        settings["max_initial_wait_days"],
        internal_branches,
        excluded_paths,
    )
    branches = _prepare_branches(
        returned_branches, profiles, environment, settings
    )
    ranking = rank_branches(branches, request["preference"], profiles)
    if not retain_climate_raw:
        strip_climate_raw(branches)
    summary = _branch_summary(
        summary_branches,
        len(summary_exclusions),
        visible=bool(returned_branches),
    )
    status = _status(summary_branches, profiles)
    if not summary_branches:
        status = "no_supported_options"

    warnings = _warnings(
        request,
        environment,
        context,
        summary_branches,
        settings,
        visible=bool(returned_branches),
        environment_error=environment_error,
    )
    assumptions = _assumptions(
        request,
        settings,
        context,
        soil_evidence=soil_evidence,
        preparation_lookup=preparation_lookup,
        duration_reference_verified=duration_reference_verified,
        duration_reference_verified_crop_ids=duration_reference_verified_crop_ids,
    )
    missing = _missing_evidence(
        summary_branches, crop_options, environment, context
    )
    source_ids = set()
    _collect_source_ids(crop_options, source_ids)
    _collect_source_ids(branches, source_ids)
    data_sources = _data_sources(source_ids, environment, smap_context)

    return {
        "schema_version": "1",
        "generated_at": generated_at,
        "request": request,
        "status": status,
        "district": district,
        "assumptions": assumptions,
        "data_sources": data_sources,
        "crop_options": crop_options,
        "branches": branches,
        "ranking": ranking,
        "warnings": warnings,
        "branch_summary": summary,
        "environment_context": context,
        "missing_evidence": missing,
    }


def _request_with_limits(request: dict, settings: dict) -> dict:
    effective = dict(request)
    effective["max_initial_wait_days"] = settings["max_initial_wait_days"]
    effective["max_waiting_days"] = settings["max_waiting_days"]
    return effective


def _config(config: dict | None) -> dict:
    if config is None:
        return dict(_DEFAULT_CONFIG)
    if not isinstance(config, dict):
        raise TypeError("config must be a dict or None")
    settings = dict(_DEFAULT_CONFIG)
    settings.update(config)
    return settings


def _generated_at(now: dt.datetime | dt.date | None) -> str:
    if now is None:
        moment = dt.datetime.now(dt.timezone.utc)
    elif isinstance(now, dt.datetime):
        moment = now
    elif isinstance(now, dt.date):
        moment = dt.datetime.combine(now, dt.time.min)
    else:
        raise TypeError("now must be a datetime, date, or None")
    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=dt.timezone.utc)
    return moment.astimezone(dt.timezone.utc).isoformat()


def _district(district_id: str) -> dict:
    supported = district_id in _SUPPORTED_DISTRICTS
    return {
        "district_id": district_id,
        "display_name": "Rajshahi" if supported else district_id,
        "supported": supported,
        "geographic_scope": (
            "representative point/grid" if supported else "not evaluated"
        ),
    }


def _crop_options(
    profiles: dict,
    start_date: str,
    water_access: str,
    soil_evidence: dict | None,
    environment: dict | None,
    initial_limit: int | None,
    branches: list[dict],
    excluded_paths: list[dict],
) -> list[dict]:
    rooted: dict[str, list[dict]] = {}
    for branch in branches:
        rooted.setdefault(branch["crops"][0]["crop_id"], []).append(branch)
    options = []
    for crop_id in sorted(profiles):
        profile = profiles[crop_id]
        crop_branches = rooted.get(crop_id, [])
        if crop_branches:
            root = crop_branches[0]
            root_node = root["crops"][0]
            status = root_node.get("status")
            if status not in ("candidate", "conditional"):
                status = "conditional"
            checks = dict(root_node.get("checks") or {})
            checks["climate"] = dict(_CLIMATE_CHECK)
            reasons = list(root_node.get("reasons") or [])
            missing = list(root_node.get("missing_evidence") or [])
            sources = list(root_node.get("source_ids") or [])
            initial_wait = root.get("initial_wait_days")
        else:
            calendar = evaluate_calendar_fit(profile, start_date, initial_limit)
            soil_water = evaluate_soil_water(
                profile,
                water_access=water_access,
                soil_evidence=soil_evidence,
                environment=environment,
            )
            checks = {
                "calendar": calendar,
                "climate": dict(_CLIMATE_CHECK),
                "soil": soil_water["checks"]["soil"],
                "water": soil_water["checks"]["water"],
                "rotation": None,
            }
            status = "unsupported"
            reasons = [
                calendar.get("reason"),
                soil_water["checks"]["soil"].get("reason"),
                soil_water["checks"]["water"].get("reason"),
                _CLIMATE_CHECK["reason"],
            ]
            for exclusion in excluded_paths:
                if exclusion.get("at_position") == 1 and exclusion.get(
                    "crop_ids"
                ) == [crop_id]:
                    reasons.append(exclusion.get("reason"))
            missing = list(
                soil_water["checks"]["soil"].get("missing_evidence") or []
            ) + list(
                soil_water["checks"]["water"].get("missing_evidence") or []
            )
            sources = list(calendar.get("source_ids") or [])
            sources.extend(soil_water["checks"]["soil"].get("source_ids") or [])
            sources.extend(soil_water["checks"]["water"].get("source_ids") or [])
            initial_wait = _initial_wait_days(profile, start_date, initial_limit)
        missing.append("current_season_climate_exposure")
        options.append(
            {
                "crop_id": crop_id,
                "name_en": profile.get("name_en"),
                "name_bn": profile.get("name_bn"),
                "reference_variety": profile.get("reference_variety"),
                "status": status,
                "shown": status != "unsupported",
                "initial_wait_days": initial_wait,
                "checks": checks,
                "reasons": _strings(reasons),
                "missing_evidence": _strings(missing),
                "source_ids": _strings(sources),
            }
        )
    return options


def _initial_wait_days(
    profile: dict, start_date: str, initial_limit: int | None
) -> int | None:
    calendar = evaluate_calendar_fit(profile, start_date, initial_limit)
    details = calendar.get("details") or {}
    waiting = details.get("waiting_days")
    if isinstance(waiting, int) and not isinstance(waiting, bool):
        return max(0, waiting)
    preferred = _optional_date(details.get("preferred_start"))
    if preferred is None:
        return None
    start = _date(start_date)
    candidate = preferred
    while candidate < start:
        candidate = _add_year(candidate)
    return (candidate - start).days


def _prepare_branches(
    raw_branches: list[dict],
    profiles: dict,
    environment: dict | None,
    settings: dict,
) -> list[dict]:
    prepared = []
    request_cache = {}
    sanitized_observations = None
    if isinstance(environment, dict) and isinstance(
        environment.get("observations"), dict
    ):
        sanitized_observations = sanitize_observations(
            environment["observations"], environment.get("fill_value")
        )
    for raw in raw_branches:
        branch = copy.deepcopy(raw)
        branch["initial_wait_days"] = raw.get("initial_wait_days")
        completion = calculate_completion_time(branch)
        branch["metrics"] = {
            "completion": completion,
            "resources": build_resource_metrics(branch, profiles),
            "economics": build_economics_metrics(branch, profiles),
            "diversity": calculate_diversity_metrics(branch, profiles),
            "climate": build_climate_metrics(
                branch,
                profiles,
                environment,
                completion,
                start_year=settings["analysis_start_year"],
                end_year=settings["analysis_end_year"],
                last_complete_data_date=_last_complete(settings, environment),
                sanitized_observations=sanitized_observations,
                cache=request_cache,
            ),
        }
        for transition in branch.get("transitions", []):
            _attach_harvest_gap(transition, branch)
        for crop in branch.get("crops", []):
            checks = crop.get("checks")
            if not isinstance(checks, dict):
                checks = {}
                crop["checks"] = checks
            checks["climate"] = copy.deepcopy(_CLIMATE_CHECK)
        branch["missing_evidence"] = _strings(
            list(branch.get("missing_evidence") or [])
            + ["current_season_climate_exposure"]
        )
        outlook, per_crop = _branch_outlook(
            branch,
            environment,
            settings,
            cache=request_cache,
            sanitized_observations=sanitized_observations,
        )
        branch["outlook"] = outlook
        for crop, crop_outlook in zip(branch.get("crops", []), per_crop):
            crop["outlook"] = crop_outlook
        prepared.append(branch)
    return prepared


def _attach_harvest_gap(transition: dict, branch: dict) -> None:
    from_position = transition.get("from_position")
    crops = branch.get("crops")
    if not isinstance(from_position, int) or not isinstance(crops, list):
        transition["harvest_to_next_window_days"] = None
        transition["window_only_gap"] = None
        return
    if not 1 <= from_position <= len(crops):
        transition["harvest_to_next_window_days"] = None
        transition["window_only_gap"] = None
        return
    harvest = crops[from_position - 1].get("harvest_range")
    next_range = transition.get("next_planting_range")
    gap = _harvest_to_window_days(harvest, next_range)
    transition["harvest_to_next_window_days"] = gap
    transition["window_only_gap"] = (
        bool(not transition.get("preparation_known", False))
        if gap is not None
        else None
    )


def _harvest_to_window_days(
    harvest: object, next_range: object
) -> dict | None:
    if not isinstance(harvest, dict) or not isinstance(next_range, dict):
        return None
    harvest_start = _optional_date(harvest.get("earliest"))
    harvest_end = _optional_date(harvest.get("latest"))
    next_start = _optional_date(next_range.get("earliest"))
    next_end = _optional_date(next_range.get("latest"))
    if None in (harvest_start, harvest_end, next_start, next_end):
        return None
    low = (next_start - harvest_end).days
    high = (next_end - harvest_start).days
    return {
        "min": max(0, min(low, high)),
        "max": max(0, max(low, high)),
    }


def _branch_outlook(
    branch: dict,
    environment: dict | None,
    settings: dict,
    *,
    cache: dict | None = None,
    sanitized_observations: dict | None = None,
) -> tuple[dict, list[dict]]:
    if environment is None:
        block = _unavailable_outlook("POWER environment not supplied")
        return block, [dict(block) for _ in branch.get("crops", [])]
    last_complete = _last_complete(settings, environment)
    if last_complete is None:
        block = _unavailable_outlook("last_complete_data_date not configured")
        return block, [dict(block) for _ in branch.get("crops", [])]
    per_crop = []
    for crop in branch.get("crops", []):
        planting = crop.get("planting_range")
        harvest = crop.get("harvest_range")
        if not isinstance(planting, dict) or not isinstance(harvest, dict):
            per_crop.append(_unavailable_outlook("crop span unavailable"))
            continue
        crop_id = str(crop.get("crop_id") or "")
        cache_key = (
            "crop-outlook",
            crop_id,
            planting.get("earliest"),
            harvest.get("latest"),
            settings["analysis_start_year"],
            settings["analysis_end_year"],
            str(last_complete),
            repr(settings.get("warning_config")),
            id(environment),
        )
        if cache is not None and cache_key in cache:
            per_crop.append(copy.deepcopy(cache[cache_key]))
            continue
        try:
            outlook = build_outlook(
                crop_id,
                planting["earliest"],
                harvest["latest"],
                environment,
                start_year=settings["analysis_start_year"],
                end_year=settings["analysis_end_year"],
                last_complete_data_date=last_complete,
                warning_config=settings["warning_config"],
                sanitized_observations=sanitized_observations,
            )
            outlook["seasonal_ranges"] = build_seasonal_ranges(
                environment,
                planting["earliest"],
                harvest["latest"],
                start_year=settings["analysis_start_year"],
                end_year=settings["analysis_end_year"],
                last_complete_data_date=last_complete,
                sanitized_observations=sanitized_observations,
            )
            if cache is not None:
                cache[cache_key] = copy.deepcopy(outlook)
            per_crop.append(outlook)
        except (TypeError, ValueError) as exc:
            message = str(exc) or "outlook calculation failed"
            per_crop.append(_unavailable_outlook(message))
    statuses = [outlook.get("status") for outlook in per_crop]
    if statuses and all(status == "ok" for status in statuses):
        status = "ok"
    elif statuses and all(status == "unavailable" for status in statuses):
        status = "unavailable"
    else:
        status = "partial"
    indicators = []
    for outlook in per_crop:
        for indicator in outlook.get("indicators", []):
            item = copy.deepcopy(indicator)
            item["crop_id"] = outlook.get("crop_id")
            indicators.append(item)
    return (
        {
            "status": status,
            "label": OUTLOOK_LABEL,
            "indicators": indicators,
            "per_crop": per_crop,
        },
        per_crop,
    )


def _unavailable_outlook(reason: str) -> dict:
    return {
        "status": "unavailable",
        "label": OUTLOOK_LABEL,
        "indicators": [],
        "reason": reason,
    }


def _last_complete(settings: dict, environment: dict) -> object | None:
    configured = settings.get("last_complete_data_date")
    if configured is not None:
        return configured
    if isinstance(environment, dict):
        end = environment.get("observation_end")
        if isinstance(end, str) and len(end) >= 10:
            return end[:10]
        observations = environment.get("observations")
        if isinstance(observations, dict) and observations:
            return max(observations)
    return None


def _branch_summary(
    branches: list[dict], excluded_count: int, *, visible: bool = True
) -> dict:
    candidate = sum(1 for branch in branches if branch.get("status") == "candidate")
    conditional = sum(
        1 for branch in branches if branch.get("status") == "conditional"
    )
    branch_word = "branch" if conditional == 1 else "branches"
    if candidate == 0 and conditional == 0:
        message = "No candidate or conditional branches available."
    elif candidate == 0 and not visible:
        message = (
            f"No candidate branches - {conditional} conditional {branch_word} "
            "available; select a first crop to view them."
        )
    elif candidate == 0:
        message = (
            f"No candidate branches - {conditional} conditional {branch_word} shown."
        )
    elif visible:
        message = (
            f"{candidate} candidate branches and {conditional} conditional "
            f"{branch_word} shown."
        )
    else:
        message = (
            f"{candidate} candidate branches and {conditional} conditional "
            f"{branch_word} available; select a first crop to view them."
        )
    return {
        "candidate_count": candidate,
        "conditional_count": conditional,
        "excluded_count": excluded_count,
        "no_candidate_branches": candidate == 0,
        "message": message,
    }


def _status(branches: list[dict], profiles: dict) -> str:
    if not branches:
        return "no_supported_options"
    for branch in branches:
        if branch.get("status") != "candidate":
            return "partial"
        if branch.get("missing_evidence"):
            return "partial"
        if build_economics_metrics(branch, profiles).get("status") != "ok":
            return "partial"
    return "ok"


def _warnings(
    request: dict,
    environment: dict | None,
    context: dict,
    branches: list[dict],
    settings: dict,
    *,
    visible: bool,
    environment_error: str | None = None,
) -> list[dict]:
    warnings = [
        {
            "code": "CLIMATE_EXPOSURE_DEFERRED",
            "message": _CLIMATE_CHECK["reason"],
        },
        {
            "code": "ECONOMICS_UNAVAILABLE",
            "message": (
                "Economic estimates are unavailable because no sourced price, "
                "cost, yield, or cash-flow evidence was supplied."
            ),
        },
    ]
    if environment is None:
        warnings.append(
            {
                "code": (
                    "POWER_UNAVAILABLE"
                    if environment_error
                    else "POWER_OUTLOOK_UNAVAILABLE"
                ),
                "message": (
                    "POWER history could not be loaded; outlook is unavailable. "
                    + environment_error
                    if environment_error
                    else "POWER environment was not supplied; outlook is unavailable."
                ),
            }
        )
    elif isinstance(environment, dict):
        for warning in environment.get("warnings", []):
            if isinstance(warning, dict):
                warnings.append(dict(warning))
    for warning in context.get("warnings", []):
        warnings.append(dict(warning))
    if not any(branch.get("status") == "candidate" for branch in branches):
        warnings.append(
            {
                "code": "NO_CANDIDATE_BRANCHES",
                "message": _branch_summary(
                    branches, 0, visible=visible
                )["message"],
            }
        )
    return _dedupe_dicts(warnings, "code")


def _assumptions(
    request: dict,
    settings: dict,
    context: dict,
    *,
    soil_evidence: dict | None = None,
    preparation_lookup: object = None,
    duration_reference_verified: bool = False,
    duration_reference_verified_crop_ids: object = None,
) -> list[dict]:
    initial = settings.get("max_initial_wait_days")
    transition = settings.get("max_waiting_days")
    assumptions = [
        {
            "code": "INITIAL_WAIT_LIMIT",
            "message": (
                f"Maximum initial wait is {initial} days; this is a product "
                "relevance limit, not a scientific maximum."
                if initial is not None
                else "No maximum initial wait policy is configured."
            ),
        },
        {
            "code": "TRANSITION_WAIT_LIMIT",
            "message": (
                f"Maximum transition wait is {transition} days; this is a "
                "product relevance limit, not a scientific maximum."
                if transition is not None
                else "No maximum transition wait policy is configured."
            ),
        },
        {
            "code": "THREE_CROP_SEQUENCE_NOT_REPEATING_ROTATION",
            "message": (
                "A branch is one three-crop sequence, not a verified repeating "
                "rotation; repeated cycles require separate evidence."
            ),
        },
        {
            "code": "CLIMATE_EXPOSURE_DEFERRED",
            "message": _CLIMATE_CHECK["reason"],
        },
        {
            "code": "ECONOMICS_UNAVAILABLE",
            "message": (
                "No sourced economic evidence; cost, net return, and upfront "
                "cash remain unavailable."
            ),
        },
    ]
    if soil_evidence is None:
        assumptions.append(
            {
                "code": "SOIL_EVIDENCE_MISSING",
                "message": (
                    "No local district soil evidence was supplied; soil fit "
                    "remains unknown rather than an automatic pass."
                ),
            }
        )
    else:
        assumptions.append(
            {
                "code": "SOIL_EVIDENCE_SUPPLIED",
                "message": (
                    "Host-supplied soil evidence is used only where it passes "
                    "the documented crop rules; missing fields remain unknown."
                ),
            }
        )
    if preparation_lookup is None:
        assumptions.append(
            {
                "code": "PREPARATION_EVIDENCE_MISSING",
                "message": (
                    "Preparation evidence was not supplied; readiness and waiting "
                    "remain unknown rather than zero."
                ),
            }
        )
    else:
        assumptions.append(
            {
                "code": "PREPARATION_EVIDENCE_SUPPLIED",
                "message": (
                    "Host-supplied preparation evidence is used only for the "
                    "crops it covers; unspecified preparation remains unknown."
                ),
            }
        )
    if not duration_reference_verified:
        assumptions.append(
            {
                "code": "DURATION_REFERENCE_UNVERIFIED",
                "message": (
                    "Crop duration reference stage (sowing versus transplanting) "
                    "is unconfirmed; timing remains conditional."
                ),
            }
        )
    else:
        if isinstance(
            duration_reference_verified_crop_ids,
            (list, tuple, set, frozenset),
        ):
            crop_ids = sorted(
                {str(value) for value in duration_reference_verified_crop_ids}
            )
            coverage = ", ".join(crop_ids) if crop_ids else "no crops (empty set)"
        else:
            coverage = "all crops"
        assumptions.append(
            {
                "code": "DURATION_REFERENCE_VERIFIED",
                "message": (
                    "Duration reference verification is applied only to: "
                    + coverage
                    + "; other crops remain conditional."
                ),
            }
        )
    if context.get("status") == "available":
        assumptions.append(
            {
                "code": "SMAP_CONTEXT_ONLY",
                "message": _SMAP_LABEL,
            }
        )
    return assumptions


def _missing_evidence(
    branches: list[dict],
    crop_options: list[dict],
    environment: dict | None,
    context: dict,
) -> list[str]:
    missing = set()
    for branch in branches:
        missing.update(branch.get("missing_evidence") or [])
        metrics = branch.get("metrics") or {}
        economics = metrics.get("economics") or {}
        for key in (
            "production_cost_bdt_per_ha",
            "net_return_bdt_per_ha",
            "upfront_cash_bdt_per_ha",
        ):
            metric = economics.get(key)
            if isinstance(metric, dict):
                missing.update(metric.get("missing_evidence") or [])
    for option in crop_options:
        missing.update(option.get("missing_evidence") or [])
    missing.add("current_season_climate_exposure")
    if environment is None:
        missing.add("power_outlook_environment")
    if context.get("status") != "available":
        missing.add("smap_context")
    return sorted(str(value) for value in missing if value)


def _environment_context(smap_context: object) -> dict:
    base = {
        "product": "SPL4SMGP.008",
        "provider": "NASA SMAP via AppEEARS",
        "resolution": "9 km EASE-Grid 2.0",
        "temporal_resolution": "3-hourly",
        "observations": [],
        "observation_start": None,
        "observation_end": None,
        "retrieved_at": None,
        "label": _SMAP_LABEL,
        "warnings": [],
    }
    if not isinstance(smap_context, dict):
        base["status"] = "unavailable"
        base["warnings"] = [
            {
                "code": "SMAP_CONTEXT_UNAVAILABLE",
                "message": "SMAP context was not supplied; no moisture context is displayed.",
            }
        ]
        return base
    warnings = [
        dict(warning)
        for warning in (smap_context.get("warnings") or [])
        if isinstance(warning, dict)
    ]
    observations = smap_context.get("observations")
    unavailable = (
        smap_context.get("status") in ("unavailable", "error", "expired")
        or bool(smap_context.get("error"))
        or bool(smap_context.get("expired"))
        or not isinstance(observations, list)
        or not observations
    )
    base.update(
        {
            "product": smap_context.get("product") or base["product"],
            "provider": smap_context.get("provider") or base["provider"],
            "resolution": (
                smap_context.get("spatial_resolution") or base["resolution"]
            ),
            "temporal_resolution": (
                smap_context.get("temporal_resolution")
                or base["temporal_resolution"]
            ),
            "retrieved_at": smap_context.get("retrieved_at"),
        }
    )
    if unavailable:
        base["status"] = "unavailable"
        if not warnings:
            warnings = [
                {
                    "code": "SMAP_CONTEXT_UNAVAILABLE",
                    "message": "SMAP context is unavailable; no moisture context is displayed.",
                }
            ]
    else:
        base["status"] = "available"
        base["observations"] = observations
        base["observation_start"] = smap_context.get("observation_start")
        base["observation_end"] = smap_context.get("observation_end")
    base["warnings"] = warnings
    return base


def _unsupported_district_response(
    request: dict,
    district: dict,
    settings: dict,
    context: dict,
    generated_at: str,
) -> dict:
    ranking = rank_branches([], request["preference"])
    return {
        "schema_version": "1",
        "generated_at": generated_at,
        "request": request,
        "status": "unsupported_district",
        "district": district,
        "assumptions": [],
        "data_sources": _data_sources(set(), None, None),
        "crop_options": [],
        "branches": [],
        "ranking": ranking,
        "warnings": [
            {
                "code": "UNSUPPORTED_DISTRICT",
                "message": (
                    f"District {request['district_id']} is not supported; no "
                    "crop results are fabricated."
                ),
            }
        ],
        "branch_summary": _branch_summary([], 0),
        "environment_context": context,
        "missing_evidence": ["district_support"],
    }


def _data_unavailable_response(
    request: dict,
    district: dict,
    settings: dict,
    context: dict,
    generated_at: str,
) -> dict:
    ranking = rank_branches([], request["preference"])
    return {
        "schema_version": "1",
        "generated_at": generated_at,
        "request": request,
        "status": "data_unavailable",
        "district": district,
        "assumptions": [],
        "data_sources": _data_sources(set(), None, None),
        "crop_options": [],
        "branches": [],
        "ranking": ranking,
        "warnings": [
            {
                "code": "DATA_UNAVAILABLE",
                "message": "Crop profiles are unavailable; no branch can be evaluated.",
            }
        ],
        "branch_summary": _branch_summary([], 0),
        "environment_context": context,
        "missing_evidence": ["crop_profiles"],
    }


def _data_sources(
    source_ids: set[str], environment: dict | None, smap_context: object
) -> list[dict]:
    entries = {
        "crop_profiles_rajshahi_v1": {
            "source_id": "crop_profiles_rajshahi_v1",
            "provider": "Local crop dataset",
            "product": "Fosol-Cycle Rajshahi crop dataset",
            "version": "1",
            "coverage": "Rajshahi crop profiles",
            "retrieved_at": None,
        }
    }
    for source_id in sorted(source_ids):
        if source_id in entries or source_id in (
            "nasa_power_daily",
            "nasa_smap_appeears",
            "local_power_2000_2026",
        ):
            continue
        entries[source_id] = _generic_source(source_id)
    if environment is not None or "nasa_power_daily" in source_ids:
        entries["nasa_power_daily"] = _power_source(environment)
    if environment is not None and (
        environment.get("source_id") == "local_power_2000_2026"
        or "local_power_2000_2026" in source_ids
    ):
        entries["local_power_2000_2026"] = _local_power_source(environment)
    if smap_context is not None or "nasa_smap_appeears" in source_ids:
        entries["nasa_smap_appeears"] = _smap_source(smap_context)
    ordered = [entries["crop_profiles_rajshahi_v1"]]
    ordered.extend(
        entries[key] for key in sorted(entries) if key != "crop_profiles_rajshahi_v1"
    )
    return ordered


def _generic_source(source_id: str) -> dict:
    if source_id.startswith("http"):
        return {
            "source_id": source_id,
            "provider": "External reference",
            "product": "Crop dataset cited reference",
            "version": "referenced",
            "coverage": "External reference cited by the crop dataset",
            "retrieved_at": None,
        }
    return {
        "source_id": source_id,
        "provider": "Local crop dataset",
        "product": "Fosol-Cycle Rajshahi crop dataset",
        "version": "1",
        "coverage": "Rajshahi crop profile or evaluator field",
        "retrieved_at": None,
    }


def _power_source(environment: object) -> dict:
    env = environment if isinstance(environment, dict) else {}
    start = env.get("observation_start")
    end = env.get("observation_end")
    coverage = (
        f"{start}..{end}"
        if isinstance(start, str) and isinstance(end, str)
        else "Normalized POWER daily observations"
    )
    return {
        "source_id": "nasa_power_daily",
        "provider": env.get("provider") or "NASA POWER",
        "product": env.get("product") or "NASA POWER Daily Point",
        "version": env.get("product_version") or "unknown",
        "coverage": coverage,
        "observation_start": start,
        "observation_end": end,
        "retrieved_at": env.get("retrieved_at"),
        "temporal_resolution": env.get("temporal_resolution"),
        "spatial_resolution": env.get("spatial_resolution"),
        "is_forecast": False,
        "cache": copy.deepcopy(env.get("cache")),
        "warnings": copy.deepcopy(env.get("warnings") or []),
    }


def _local_power_source(environment: object) -> dict:
    env = environment if isinstance(environment, dict) else {}
    start = env.get("observation_start")
    end = env.get("observation_end")
    coverage = (
        f"{start}..{end}"
        if isinstance(start, str) and isinstance(end, str)
        else "Local 2000-2026 POWER daily observations"
    )
    return {
        "source_id": "local_power_2000_2026",
        "provider": env.get("provider") or "Local POWER CSV",
        "product": env.get("product") or "NASA POWER Daily Point (local subset)",
        "version": env.get("product_version") or "local_2000_2026",
        "coverage": coverage,
        "retrieved_at": env.get("retrieved_at"),
    }


def _smap_source(smap_context: object) -> dict:
    context = smap_context if isinstance(smap_context, dict) else {}
    return {
        "source_id": "nasa_smap_appeears",
        "provider": context.get("provider") or "NASA SMAP via AppEEARS",
        "product": context.get("product") or "SPL4SMGP.008",
        "version": context.get("product_version") or "008",
        "coverage": "SMAP context only",
        "retrieved_at": context.get("retrieved_at"),
    }


def _collect_source_ids(value: object, found: set[str]) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if key == "source_ids" and isinstance(item, (list, tuple)):
                found.update(
                    str(source_id)
                    for source_id in item
                    if isinstance(source_id, str) and source_id
                )
            elif key == "sources" and isinstance(item, list):
                for source in item:
                    if isinstance(source, dict) and isinstance(
                        source.get("source_id"), str
                    ):
                        found.add(source["source_id"])
                    else:
                        _collect_source_ids(source, found)
            else:
                _collect_source_ids(item, found)
    elif isinstance(value, (list, tuple)):
        for item in value:
            _collect_source_ids(item, found)


def _strings(values: list) -> list[str]:
    return _dedupe(
        [
            str(value).strip()
            for value in values
            if value is not None and str(value).strip()
        ]
    )


def _dedupe(values: list) -> list:
    return list(dict.fromkeys(values))


def _dedupe_dicts(values: list[dict], key: str) -> list[dict]:
    seen = set()
    result = []
    for value in values:
        marker = value.get(key)
        if marker in seen:
            continue
        seen.add(marker)
        result.append(value)
    return result


def _date(value: str) -> dt.date:
    return dt.date.fromisoformat(value)


def _optional_date(value: object) -> dt.date | None:
    if isinstance(value, dt.datetime):
        return value.date()
    if isinstance(value, dt.date):
        return value
    if isinstance(value, str):
        try:
            return dt.date.fromisoformat(value.strip())
        except ValueError:
            return None
    return None


def _add_year(value: dt.date) -> dt.date:
    try:
        return value.replace(year=value.year + 1)
    except ValueError:
        return value.replace(year=value.year + 1, day=28)
