"""Contract checker for explore responses (v1.md §14.4).

Usage:
    python scripts/contract_check.py examples/example_response.json
    python scripts/contract_check.py examples/example_error.json --error
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import math
import sys
from pathlib import Path

VALID_STATUS = {
    "ok",
    "partial",
    "no_supported_options",
    "unsupported_district",
    "data_unavailable",
}
VALID_PREFERENCES = {
    "fastest_completion",
    "lowest_total_cost",
    "least_irrigation_dependence",
    "highest_net_return",
    "more_crop_diversity",
    "closest_temperature_match",
    "least_dry_spell_exposure",
    "least_heavy_rain_exposure",
}
_ECONOMIC_VALUE_KEYS = (
    "gross_revenue_bdt_per_ha",
    "production_cost_bdt_per_ha",
    "net_return_bdt_per_ha",
    "upfront_cash_bdt_per_ha",
)
CLIMATE_PREFERENCES = {
    "closest_temperature_match",
    "least_dry_spell_exposure",
    "least_heavy_rain_exposure",
}
CLIMATE_SCHEDULES = ("min_realization", "max_realization")


def _check_economics(value: object, field: str, errors: list[str]) -> None:
    if not isinstance(value, dict):
        errors.append(f"{field} must be an object")
        return
    if value.get("status") != "unavailable":
        return
    if value.get("scenarios") != []:
        errors.append(f"{field}.scenarios must be empty when unavailable")
    for key in _ECONOMIC_VALUE_KEYS:
        metric = value.get(key)
        if not isinstance(metric, dict):
            errors.append(f"{field}.{key} must be an object")
        elif metric.get("value_bdt_per_ha") is not None:
            errors.append(
                f"{field}.{key}.value_bdt_per_ha must be null when unavailable"
            )
    price = value.get("price_evidence")
    if not isinstance(price, dict):
        errors.append(f"{field}.price_evidence must be an object")
    elif price.get("price_value") is not None:
        errors.append(f"{field}.price_evidence.price_value must be null when unavailable")


def _climate_number(
    value: object,
    field: str,
    errors: list[str],
    *,
    minimum: float | None = None,
    maximum: float | None = None,
) -> None:
    if value is None:
        return
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        errors.append(f"{field} must be numeric or null")
        return
    number = float(value)
    if not math.isfinite(number):
        errors.append(f"{field} must be finite")
    elif minimum is not None and number < minimum:
        errors.append(f"{field} must be >= {minimum}")
    elif maximum is not None and number > maximum:
        errors.append(f"{field} must be <= {maximum}")


def _climate_range(value: object, field: str, errors: list[str]) -> None:
    if value is None:
        return
    if not isinstance(value, dict):
        errors.append(f"{field} must be an object or null")
        return
    low = value.get("min")
    high = value.get("max")
    _climate_number(low, f"{field}.min", errors)
    _climate_number(high, f"{field}.max", errors)
    if isinstance(low, (int, float)) and isinstance(high, (int, float)) and low > high:
        errors.append(f"{field}.min must not exceed max")


def _check_climate_crop(value: object, field: str, errors: list[str]) -> None:
    if not isinstance(value, dict):
        errors.append(f"{field} must be an object")
        return
    if not isinstance(value.get("crop_id"), str):
        errors.append(f"{field}.crop_id must be a string")
    position = value.get("position")
    if not isinstance(position, int) or isinstance(position, bool) or position not in (1, 2, 3):
        errors.append(f"{field}.position must be 1, 2, or 3")
    seasons = value.get("seasons")
    if not isinstance(seasons, int) or isinstance(seasons, bool) or seasons < 0:
        errors.append(f"{field}.seasons must be a non-negative integer")
    if "temperature" not in value and "temperature_seasons" in value:
        for key in ("temperature_seasons", "rain_seasons"):
            values = value.get(key)
            if not isinstance(values, list) or any(
                isinstance(item, bool) or not isinstance(item, int)
                for item in values
            ):
                errors.append(f"{field}.{key} must be a list of integers")
        if value.get("status") not in {"ok", "partial", "unavailable"}:
            errors.append(f"{field}.status invalid")
        return
    temperature = value.get("temperature")
    if not isinstance(temperature, dict):
        errors.append(f"{field}.temperature must be an object")
    else:
        _climate_number(
            temperature.get("median_distance_c"),
            f"{field}.temperature.median_distance_c",
            errors,
            minimum=0,
        )
        _climate_number(
            temperature.get("median_t2m_c"),
            f"{field}.temperature.median_t2m_c",
            errors,
        )
        _climate_number(
            temperature.get("within_optimum_fraction"),
            f"{field}.temperature.within_optimum_fraction",
            errors,
            minimum=0,
            maximum=1,
        )
        _climate_number(
            temperature.get("within_tolerance_fraction"),
            f"{field}.temperature.within_tolerance_fraction",
            errors,
            minimum=0,
            maximum=1,
        )
        _climate_range(
            temperature.get("optimum_range"),
            f"{field}.temperature.optimum_range",
            errors,
        )
        _climate_range(
            temperature.get("tolerance_range"),
            f"{field}.temperature.tolerance_range",
            errors,
        )
    dry = value.get("dry_spell")
    if not isinstance(dry, dict):
        errors.append(f"{field}.dry_spell must be an object")
    else:
        for key in (
            "median_longest_run_days",
            "min_longest_run_days",
            "max_longest_run_days",
            "median_growing_days",
        ):
            _climate_number(
                dry.get(key), f"{field}.dry_spell.{key}", errors, minimum=0
            )
        if all(
            isinstance(dry.get(key), (int, float))
            for key in (
                "min_longest_run_days",
                "median_longest_run_days",
                "max_longest_run_days",
            )
        ) and not (
            dry["min_longest_run_days"]
            <= dry["median_longest_run_days"]
            <= dry["max_longest_run_days"]
        ):
            errors.append(f"{field}.dry_spell run bounds are not ordered")
    heavy = value.get("heavy_rain")
    if not isinstance(heavy, dict):
        errors.append(f"{field}.heavy_rain must be an object")
    else:
        _climate_number(heavy.get("days"), f"{field}.heavy_rain.days", errors, minimum=0)
        _climate_number(
            heavy.get("valid_days"), f"{field}.heavy_rain.valid_days", errors, minimum=0
        )
        _climate_number(
            heavy.get("frequency"),
            f"{field}.heavy_rain.frequency",
            errors,
            minimum=0,
            maximum=1,
        )
        if (
            isinstance(heavy.get("days"), (int, float))
            and isinstance(heavy.get("valid_days"), (int, float))
            and heavy["days"] > heavy["valid_days"]
        ):
            errors.append(f"{field}.heavy_rain.days must not exceed valid_days")
    rainfall = value.get("rainfall")
    if not isinstance(rainfall, dict):
        errors.append(f"{field}.rainfall must be an object")
    else:
        for key in (
            "median_total_mm",
            "iqr_total_mm",
            "min_total_mm",
            "max_total_mm",
        ):
            _climate_number(
                rainfall.get(key), f"{field}.rainfall.{key}", errors, minimum=0
            )
        if all(
            isinstance(rainfall.get(key), (int, float))
            for key in ("min_total_mm", "median_total_mm", "max_total_mm")
        ) and not (
            rainfall["min_total_mm"]
            <= rainfall["median_total_mm"]
            <= rainfall["max_total_mm"]
        ):
            errors.append(f"{field}.rainfall totals are not ordered")


def _check_climate_summary(value: object, field: str, errors: list[str]) -> None:
    if not isinstance(value, dict):
        errors.append(f"{field} must be an object")
        return
    if value.get("status") not in {"ok", "partial", "unavailable"}:
        errors.append(f"{field}.status invalid")
    for key in (
        "temperature_distance_c",
        "dry_spell_days",
        "heavy_rain_frequency",
        "rainfall_median_mm",
        "growing_days_median",
    ):
        _climate_number(value.get(key), f"{field}.{key}", errors, minimum=0)
    per_crop = value.get("per_crop")
    if per_crop is not None:
        if not isinstance(per_crop, list):
            errors.append(f"{field}.per_crop must be a list")
        else:
            for index, crop in enumerate(per_crop):
                _check_climate_crop(crop, f"{field}.per_crop[{index}]", errors)


def _check_climate_metrics(value: object, field: str, errors: list[str]) -> None:
    if not isinstance(value, dict):
        errors.append(f"{field} must be an object")
        return
    if value.get("status") not in {"ok", "partial", "unavailable"}:
        errors.append(f"{field}.status invalid")
    if value.get("status") == "unavailable":
        return
    for key in ("definitions", "unit_validation", "views"):
        if not isinstance(value.get(key), dict):
            errors.append(f"{field}.{key} must be an object")
    if not isinstance(value.get("limitations"), list):
        errors.append(f"{field}.limitations must be a list")
    period = value.get("analysis_period")
    if not isinstance(period, dict) or not all(
        isinstance(period.get(key), int) for key in ("start_year", "end_year")
    ):
        errors.append(f"{field}.analysis_period must contain integer years")
    per_schedule = value.get("per_schedule")
    if not isinstance(per_schedule, dict):
        errors.append(f"{field}.per_schedule must be an object")
        return
    for schedule in CLIMATE_SCHEDULES:
        record = per_schedule.get(schedule)
        label = f"{field}.per_schedule.{schedule}"
        if not isinstance(record, dict):
            errors.append(f"{label} must be an object")
            continue
        if record.get("status") not in {"ok", "partial", "unavailable"}:
            errors.append(f"{label}.status invalid")
        for key in ("temperature_complete_seasons", "rain_complete_seasons", "complete_seasons"):
            values = record.get(key)
            if not isinstance(values, list) or any(
                isinstance(item, bool) or not isinstance(item, int)
                for item in values
            ):
                errors.append(f"{label}.{key} must be a list of integers")
        crops = record.get("crops")
        if not isinstance(crops, list):
            errors.append(f"{label}.crops must be a list")
        else:
            for index, crop in enumerate(crops):
                _check_climate_crop(crop, f"{label}.crops[{index}]", errors)
    summary = value.get("summary")
    if not isinstance(summary, dict):
        errors.append(f"{field}.summary must be an object")
    else:
        for schedule in CLIMATE_SCHEDULES:
            _check_climate_summary(
                summary.get(schedule), f"{field}.summary.{schedule}", errors
            )


def _check_climate_ranking(ranking: dict, errors: list[str]) -> None:
    if ranking.get("preference") in CLIMATE_PREFERENCES and "climate" not in ranking:
        errors.append("ranking.climate is required for a climate preference")
        return
    value = ranking.get("climate")
    if value is None:
        return
    if not isinstance(value, dict):
        errors.append("ranking.climate must be an object")
        return
    for key in ("definitions", "common_seasons", "common_season_counts", "top_ties"):
        if not isinstance(value.get(key), dict):
            errors.append(f"ranking.climate.{key} must be an object")
    if not isinstance(value.get("limitations"), list):
        errors.append("ranking.climate.limitations must be a list")
    if not isinstance(value.get("equal_crop_weighting"), bool):
        errors.append("ranking.climate.equal_crop_weighting must be boolean")
    if value.get("no_overall_score") is not True:
        errors.append("ranking.climate.no_overall_score must be true")
    if not isinstance(value.get("ordering_basis"), str) or not value["ordering_basis"]:
        errors.append("ranking.climate.ordering_basis must be non-empty")
    for group in ("candidate", "conditional"):
        seasons = value.get("common_seasons", {}).get(group)
        count = value.get("common_season_counts", {}).get(group)
        if not isinstance(seasons, list) or any(
            isinstance(item, bool) or not isinstance(item, int) for item in seasons
        ):
            errors.append(f"ranking.climate.common_seasons.{group} must be integers")
        if not isinstance(count, int) or isinstance(count, bool) or count < 0:
            errors.append(f"ranking.climate.common_season_counts.{group} invalid")
        elif isinstance(seasons, list) and count != len(seasons):
            errors.append(
                f"ranking.climate.common_season_counts.{group} != common_seasons length"
            )
        tie = value.get("top_ties", {}).get(group)
        if tie is not None:
            if not isinstance(tie, dict):
                errors.append(f"ranking.climate.top_ties.{group} must be an object")
            else:
                _climate_number(
                    tie.get("value"),
                    f"ranking.climate.top_ties.{group}.value",
                    errors,
                )
                if not isinstance(tie.get("branch_ids"), list):
                    errors.append(
                        f"ranking.climate.top_ties.{group}.branch_ids must be a list"
                    )
    if ranking.get("preference") in CLIMATE_PREFERENCES:
        groups = ranking.get("groups")
        if isinstance(groups, dict):
            for group_name in ("candidate", "conditional"):
                group = groups.get(group_name)
                if not isinstance(group, dict):
                    continue
                for index, entry in enumerate(group.get("ranked", [])):
                    label = f"ranking.groups.{group_name}.ranked[{index}]"
                    _climate_number(
                        entry.get("metric_value"),
                        f"{label}.metric_value",
                        errors,
                    )
                    if not isinstance(entry.get("unit"), str) or not entry["unit"]:
                        errors.append(f"{label}.unit must be non-empty")
                    schedule_values = entry.get("schedule_values")
                    if not isinstance(schedule_values, dict):
                        errors.append(f"{label}.schedule_values must be an object")
                    else:
                        for schedule in CLIMATE_SCHEDULES:
                            _climate_number(
                                schedule_values.get(schedule),
                                f"{label}.schedule_values.{schedule}",
                                errors,
                            )
                    if not isinstance(entry.get("ordering_basis"), str) or not entry["ordering_basis"]:
                        errors.append(f"{label}.ordering_basis must be non-empty")
                    seasons = entry.get("common_seasons")
                    if not isinstance(seasons, list) or any(
                        isinstance(item, bool) or not isinstance(item, int)
                        for item in seasons
                    ):
                        errors.append(f"{label}.common_seasons must be integers")
                    climate = entry.get("climate")
                    if not isinstance(climate, dict):
                        errors.append(f"{label}.climate must be an object")
                        continue
                    if climate.get("view") not in {"temperature", "rain"}:
                        errors.append(f"{label}.climate.view invalid")
                    summaries = climate.get("per_schedule")
                    if not isinstance(summaries, dict):
                        errors.append(f"{label}.climate.per_schedule must be an object")
                    else:
                        for schedule in CLIMATE_SCHEDULES:
                            _check_climate_summary(
                                summaries.get(schedule),
                                f"{label}.climate.per_schedule.{schedule}",
                                errors,
                            )


def _check_outlook(
    value: object, field: str, catalog: set[str], errors: list[str]
) -> None:
    if not isinstance(value, dict):
        errors.append(f"{field} must be an object")
        return
    if value.get("status") not in {"ok", "partial", "unavailable"}:
        errors.append(f"{field}.status invalid")
    if not isinstance(value.get("label"), str) or not value["label"]:
        errors.append(f"{field}.label must be non-empty")
    for source in value.get("sources", []):
        if isinstance(source, dict) and source.get("source_id") not in catalog:
            errors.append(f"{field}.sources references unknown source_id")
    ranges = value.get("seasonal_ranges")
    if ranges is None:
        return
    if not isinstance(ranges, dict):
        errors.append(f"{field}.seasonal_ranges must be an object")
        return
    if ranges.get("status") not in {"ok", "partial", "unavailable"}:
        errors.append(f"{field}.seasonal_ranges.status invalid")
    if not isinstance(ranges.get("label"), str) or not ranges["label"]:
        errors.append(f"{field}.seasonal_ranges.label must be non-empty")
    coverage = ranges.get("coverage")
    if not isinstance(coverage, dict):
        errors.append(f"{field}.seasonal_ranges.coverage must be an object")
    else:
        for key in ("start_year", "end_year", "seasons_total"):
            if not isinstance(coverage.get(key), int):
                errors.append(f"{field}.seasonal_ranges.coverage.{key} must be int")
    if ranges.get("thresholds_applied") is not False:
        errors.append(f"{field}.seasonal_ranges.thresholds_applied must be false")
    if ranges.get("warnings") != []:
        errors.append(f"{field}.seasonal_ranges.warnings must be empty")
    _source_ids(
        ranges.get("source_ids"),
        f"{field}.seasonal_ranges.source_ids",
        catalog,
        errors,
    )
    for indicator in ranges.get("indicators", []):
        if not isinstance(indicator, dict):
            errors.append(f"{field}.seasonal_ranges.indicators must contain objects")
            continue
        for key in ("min", "median", "max"):
            if not isinstance(indicator.get(key), (int, float)):
                errors.append(
                    f"{field}.seasonal_ranges indicator {key} must be numeric"
                )
        if all(
            isinstance(indicator.get(key), (int, float))
            for key in ("min", "median", "max")
        ) and not (
            indicator["min"] <= indicator["median"] <= indicator["max"]
        ):
            errors.append(
                f"{field}.seasonal_ranges indicator ordering invalid"
            )


def _strict_load(path: Path) -> dict:
    def reject(value: str) -> None:
        raise ValueError(f"non-finite JSON constant: {value}")

    text = path.read_text(encoding="utf-8")
    if "NaN" in text or "Infinity" in text:
        raise ValueError("NaN/Infinity is not allowed in the contract")
    payload = json.loads(text, parse_constant=reject)
    if not isinstance(payload, dict):
        raise ValueError("response must be a JSON object")
    # unknown values must never be NaN/Inf; allow_nan=False proves serialization.
    json.dumps(payload, allow_nan=False)
    return payload


def _date(value: object, field: str, errors: list[str]) -> None:
    if not isinstance(value, str):
        errors.append(f"{field} must be an ISO date string")
        return
    try:
        dt.date.fromisoformat(value)
    except ValueError:
        errors.append(f"{field} is not YYYY-MM-DD: {value!r}")


def _range(value: object, field: str, errors: list[str]) -> None:
    if not isinstance(value, dict):
        errors.append(f"{field} must be an object")
        return
    _date(value.get("earliest"), f"{field}.earliest", errors)
    _date(value.get("latest"), f"{field}.latest", errors)
    if (
        isinstance(value.get("earliest"), str)
        and isinstance(value.get("latest"), str)
        and value["earliest"] > value["latest"]
    ):
        errors.append(f"{field}.earliest > latest")


def _source_ids(value: object, field: str, catalog: set[str], errors: list[str]) -> None:
    if value is None:
        return
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        errors.append(f"{field} must be a list of source IDs")
        return
    for source_id in value:
        if source_id not in catalog:
            errors.append(f"{field} references unknown source_id {source_id!r}")


def validate_request(payload: dict) -> list[str]:
    errors: list[str] = []
    if not isinstance(payload.get("district_id"), str) or not payload["district_id"]:
        errors.append("district_id must be a non-empty string")
    _date(payload.get("start_date"), "start_date", errors)
    first = payload.get("first_crop_id")
    if first is not None and (not isinstance(first, str) or not first):
        errors.append("first_crop_id must be null or a non-empty string")
    if payload.get("water_access", "unknown") not in {
        "rainfed",
        "irrigation_available",
        "unknown",
    }:
        errors.append("water_access is invalid")
    if payload.get("preference", "fastest_completion") not in VALID_PREFERENCES:
        errors.append("preference is invalid")
    return errors


def validate_response(payload: dict) -> list[str]:
    errors: list[str] = []
    if payload.get("schema_version") != "1":
        errors.append("schema_version must be '1'")
    if "error" in payload:
        error = payload["error"]
        if not isinstance(error, dict):
            errors.append("error must be an object")
        else:
            for key in ("code", "message"):
                if not isinstance(error.get(key), str) or not error[key]:
                    errors.append(f"error.{key} must be a non-empty string")
            if "stack" in error or "traceback" in error:
                errors.append("error must not contain a stack trace")
        return errors

    required = (
        "generated_at",
        "request",
        "status",
        "district",
        "assumptions",
        "data_sources",
        "crop_options",
        "branches",
        "ranking",
        "warnings",
        "branch_summary",
        "environment_context",
        "missing_evidence",
    )
    for key in required:
        if key not in payload:
            errors.append(f"missing top-level key {key}")

    if not isinstance(payload.get("request"), dict):
        errors.append("request must be an object")
    else:
        request = payload["request"]
        for key in ("max_initial_wait_days", "max_waiting_days"):
            if key not in request:
                errors.append(f"request.{key} is required")
            else:
                value = request[key]
                if value is not None and (
                    isinstance(value, bool)
                    or not isinstance(value, int)
                    or value < 0
                ):
                    errors.append(
                        f"request.{key} must be a non-negative integer or null"
                    )
    status = payload.get("status")
    if status not in VALID_STATUS:
        errors.append(f"invalid status {status!r}")
    generated = payload.get("generated_at")
    if not isinstance(generated, str) or not generated.endswith("+00:00"):
        errors.append("generated_at must be a UTC ISO timestamp")
    if not isinstance(payload.get("assumptions"), list):
        errors.append("assumptions must be a list")
    if not isinstance(payload.get("warnings"), list):
        errors.append("warnings must be a list")
    if not isinstance(payload.get("missing_evidence"), list):
        errors.append("missing_evidence must be a list")

    sources = payload.get("data_sources")
    source_ids: set[str] = set()
    if not isinstance(sources, list):
        errors.append("data_sources must be a list")
        sources = []
    for index, source in enumerate(sources):
        if not isinstance(source, dict) or not isinstance(source.get("source_id"), str):
            errors.append(f"data_sources[{index}] missing source_id")
            continue
        source_ids.add(source["source_id"])

    crop_options = payload.get("crop_options")
    if not isinstance(crop_options, list):
        errors.append("crop_options must be a list")
        crop_options = []
    for index, option in enumerate(crop_options):
        if not isinstance(option, dict):
            errors.append(f"crop_options[{index}] must be an object")
            continue
        if not isinstance(option.get("crop_id"), str):
            errors.append(f"crop_options[{index}] missing crop_id")
        if option.get("status") not in {"candidate", "conditional", "unsupported"}:
            errors.append(f"crop_options[{index}] invalid status")
        _source_ids(option.get("source_ids"), f"crop_options[{index}].source_ids", source_ids, errors)

    branches = payload.get("branches")
    if not isinstance(branches, list):
        errors.append("branches must be a list")
        branches = []
    branch_ids: set[str] = set()
    status_counts = {"candidate": 0, "conditional": 0}
    for index, branch in enumerate(branches):
        label = f"branches[{index}]"
        if not isinstance(branch, dict):
            errors.append(f"{label} must be an object")
            continue
        branch_id = branch.get("branch_id")
        if not isinstance(branch_id, str) or not branch_id:
            errors.append(f"{label} missing branch_id")
        elif branch_id in branch_ids:
            errors.append(f"duplicate branch_id {branch_id!r}")
        else:
            branch_ids.add(branch_id)
        branch_status = branch.get("status")
        if branch_status not in {"candidate", "conditional"}:
            errors.append(f"{label} invalid status {branch_status!r}")
        else:
            status_counts[branch_status] += 1
        crops = branch.get("crops")
        transitions = branch.get("transitions")
        if not isinstance(crops, list) or len(crops) != 3:
            errors.append(f"{label} must have exactly 3 crops")
            crops = []
        if not isinstance(transitions, list) or len(transitions) != 2:
            errors.append(f"{label} must have exactly 2 transitions")
        for position, crop in enumerate(crops, 1):
            if not isinstance(crop, dict) or crop.get("position") != position:
                errors.append(f"{label}.crops[{position - 1}] position must be {position}")
                continue
            if not isinstance(crop.get("crop_id"), str):
                errors.append(f"{label}.crops[{position - 1}] missing crop_id")
            if "outlook" in crop:
                _check_outlook(
                    crop["outlook"],
                    f"{label}.crops[{position - 1}].outlook",
                    source_ids,
                    errors,
                )
            for key in ("planting_range", "harvest_range"):
                if crop.get(key) is not None:
                    _range(crop[key], f"{label}.crops[{position - 1}].{key}", errors)
            _source_ids(crop.get("source_ids"), f"{label}.crops[{position - 1}].source_ids", source_ids, errors)
        for index_t, transition in enumerate(transitions, 1):
            if not isinstance(transition, dict):
                errors.append(f"{label}.transitions[{index_t - 1}] must be an object")
                continue
            if transition.get("from_position") != index_t:
                errors.append(f"{label}.transitions[{index_t - 1}] from_position must be {index_t}")
            if transition.get("to_position") != index_t + 1:
                errors.append(f"{label}.transitions[{index_t - 1}] to_position must be {index_t + 1}")
            for key in ("preparation_range", "waiting_range", "next_planting_range"):
                if transition.get(key) is not None:
                    _range(transition[key], f"{label}.transitions[{index_t - 1}].{key}", errors)
            _source_ids(transition.get("source_ids"), f"{label}.transitions[{index_t - 1}].source_ids", source_ids, errors)
        _source_ids(branch.get("source_ids"), f"{label}.source_ids", source_ids, errors)
        metrics = branch.get("metrics")
        if not isinstance(metrics, dict):
            errors.append(f"{label}.metrics must be an object")
        else:
            _check_economics(metrics.get("economics"), f"{label}.metrics.economics", errors)
            if "climate" in metrics:
                _check_climate_metrics(
                    metrics["climate"], f"{label}.metrics.climate", errors
                )
        if "outlook" in branch:
            _check_outlook(
                branch["outlook"], f"{label}.outlook", source_ids, errors
            )

    summary = payload.get("branch_summary")
    if not isinstance(summary, dict):
        errors.append("branch_summary must be an object")
    else:
        initial_null = (payload.get("request") or {}).get("first_crop_id") is None
        for key in ("candidate_count", "conditional_count"):
            if not isinstance(summary.get(key), int) or summary.get(key) < 0:
                errors.append(f"branch_summary.{key} must be a non-negative integer")
            elif not initial_null and summary.get(key) != status_counts[key[:-6]]:
                errors.append(f"branch_summary.{key} != branch status count")
        if initial_null and branches:
            errors.append("branches must be empty when first_crop_id is null")
        if not isinstance(summary.get("no_candidate_branches"), bool):
            errors.append("branch_summary.no_candidate_branches must be boolean")
        if not isinstance(summary.get("message"), str):
            errors.append("branch_summary.message must be a string")

    ranking = payload.get("ranking")
    if not isinstance(ranking, dict):
        errors.append("ranking must be an object")
    else:
        if ranking.get("preference") not in VALID_PREFERENCES:
            errors.append("ranking.preference is invalid")
        groups = ranking.get("groups")
        if not isinstance(groups, dict):
            errors.append("ranking.groups must be an object")
        else:
            for group_name in ("candidate", "conditional"):
                group = groups.get(group_name)
                if not isinstance(group, dict):
                    errors.append(f"ranking.groups.{group_name} must be an object")
                    continue
                for list_name in ("ranked", "unranked"):
                    entries = group.get(list_name)
                    if not isinstance(entries, list):
                        errors.append(f"ranking.groups.{group_name}.{list_name} must be a list")
                        continue
                    for entry in entries:
                        if not isinstance(entry, dict) or entry.get("branch_id") not in branch_ids:
                            errors.append(f"ranking references unknown branch in {group_name}.{list_name}")
                            continue
                        if "initial_wait_days" not in entry:
                            errors.append(
                                f"ranking entry in {group_name}.{list_name} missing initial_wait_days"
                            )
                        else:
                            wait = entry["initial_wait_days"]
                            if wait is not None and (
                                isinstance(wait, bool)
                                or not isinstance(wait, int)
                                or wait < 0
                            ):
                                errors.append(
                                    f"ranking entry in {group_name}.{list_name} has invalid initial_wait_days"
                                )
                if group.get("count") != len(group.get("ranked", [])) + len(group.get("unranked", [])):
                    errors.append(f"ranking.groups.{group_name}.count mismatch")
        _check_climate_ranking(ranking, errors)

    context = payload.get("environment_context")
    if not isinstance(context, dict):
        errors.append("environment_context must be an object")
    else:
        if context.get("status") not in {"available", "unavailable"}:
            errors.append("environment_context.status invalid")
        if context.get("status") == "unavailable" and not context.get("warnings"):
            errors.append("unavailable environment_context needs a warning")
        if "context only" not in str(context.get("label", "")).lower():
            errors.append("environment_context label must say context only")

    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("path", nargs="?", default="examples/example_response.json")
    parser.add_argument("--error", action="store_true")
    args = parser.parse_args(argv)
    path = Path(args.path)
    try:
        payload = _strict_load(path)
    except Exception as exc:  # noqa: BLE001 - CLI reports, never hides
        print(f"FAIL {path}: {exc}")
        return 1
    is_request = "schema_version" not in payload and "district_id" in payload
    if is_request and not args.error:
        errors = validate_request(payload)
        kind = "request"
    else:
        errors = validate_response(payload)
        kind = "response"
        if args.error and "error" not in payload:
            errors.append("expected an error response")
    if errors:
        print(f"FAIL {path}")
        for error in errors[:20]:
            print(f"- {error}")
        return 1
    print(f"PASS {path} ({kind})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
