"""Seasonal outlook assembler (v1.md §9.1-9.3, §14.4)."""

from __future__ import annotations

import datetime as dt
import math
import statistics

from src.outlook_config import OUTLOOK_LABEL, WARNING_DEFINITIONS
from src.outlook_indicators import (
    calculate_precipitation_statistics,
    calculate_temperature_statistics,
    calculate_warning_indicator,
)
from src.seasonal_replay import map_schedule_to_seasons

_STATISTICS_VARIABLE = "T2M"
_PRECIPITATION_VARIABLE = "PRECTOTCORR"
_SOURCE_ID = "nasa_power_daily"
_FIXED_FILLS = frozenset({-999.0, -9999.0})


def build_outlook(
    crop_id: str,
    period_start: dt.date | str,
    period_end: dt.date | str,
    environment: dict,
    *,
    start_year: int = 1991,
    end_year: int = 2025,
    last_complete_data_date: dt.date | str,
    warning_config: dict | None = None,
    sanitized_observations: dict | None = None,
) -> dict:
    """Assemble the seasonal outlook from W1 mappings and W2 indicators.

    ``environment`` is the normalized POWER payload. ``warning_config`` may be
    ``None`` (all configured warnings disabled), a mapping of warning IDs to
    booleans, or a mapping of warning IDs to definition overrides.
    """
    if not isinstance(crop_id, str) or not crop_id.strip():
        raise ValueError("crop_id must be a non-empty string")
    if not isinstance(environment, dict):
        raise TypeError("environment must be a dict")
    observations = environment.get("observations")
    if not isinstance(observations, dict):
        raise ValueError("environment must contain an observations dict")

    fill_value = environment.get("fill_value")
    sanitized = (
        sanitized_observations
        if isinstance(sanitized_observations, dict)
        else _sanitize_observations(observations, fill_value)
    )
    definitions = _warning_definitions(warning_config)
    enabled = [
        definition
        for definition in definitions.values()
        if bool(definition.get("enabled", False))
    ]

    t2m_result = map_schedule_to_seasons(
        period_start,
        period_end,
        sanitized,
        _STATISTICS_VARIABLE,
        start_year=start_year,
        end_year=end_year,
        last_complete_data_date=last_complete_data_date,
        coverage_rule="stats_min_90",
    )
    precip_result = map_schedule_to_seasons(
        period_start,
        period_end,
        sanitized,
        _PRECIPITATION_VARIABLE,
        start_year=start_year,
        end_year=end_year,
        last_complete_data_date=last_complete_data_date,
        coverage_rule="warnings_100",
    )

    warning_mappings: dict[str, dict] = {}
    for definition in enabled:
        variable = definition.get("variable")
        if not isinstance(variable, str) or not variable.strip():
            raise ValueError("enabled warning definition must have a variable")
        if variable == _PRECIPITATION_VARIABLE:
            warning_mappings[variable] = precip_result
        elif variable not in warning_mappings:
            warning_mappings[variable] = map_schedule_to_seasons(
                period_start,
                period_end,
                sanitized,
                variable,
                start_year=start_year,
                end_year=end_year,
                last_complete_data_date=last_complete_data_date,
                coverage_rule="warnings_100",
            )

    indicators = [
        calculate_temperature_statistics(sanitized, t2m_result),
        calculate_precipitation_statistics(sanitized, precip_result),
    ]
    for definition in enabled:
        indicators.append(
            calculate_warning_indicator(
                sanitized,
                warning_mappings[definition["variable"]],
                definition,
            )
        )
    for indicator in indicators:
        indicator["source_ids"] = [_SOURCE_ID]

    warning_results = [precip_result]
    for mapping in warning_mappings.values():
        if mapping is not precip_result and all(
            mapping is not existing for existing in warning_results
        ):
            warning_results.append(mapping)

    used_variables = _used_variables(enabled)
    seasons_total = len(t2m_result["seasons"])
    stats_evaluated = len(t2m_result["evaluated_seasons"])
    warnings_evaluated = min(
        len(result["evaluated_seasons"]) for result in warning_results
    )
    excluded = _merge_excluded(
        [("statistics", t2m_result)]
        + [("warnings", result) for result in warning_results]
    )
    missing_days = _missing_days(
        observations, t2m_result["seasons"], used_variables, fill_value
    )

    notes: list[str] = []
    for result in [t2m_result, precip_result, *warning_mappings.values()]:
        notes.extend(result.get("notes", []))
    if t2m_result["excluded_seasons"]:
        notes.append(
            f"{len(t2m_result['excluded_seasons'])} historical season(s) were "
            "excluded from statistics; see season_coverage.excluded_seasons."
        )
    excluded_warning_years = {
        _season_key(season) for result in warning_results
        for season in result["excluded_seasons"]
    }
    if excluded_warning_years:
        notes.append(
            f"{len(excluded_warning_years)} historical season(s) were excluded "
            "from warnings; see season_coverage.excluded_seasons."
        )

    season_coverage = {
        "seasons_total": seasons_total,
        "seasons_evaluated_statistics": stats_evaluated,
        "seasons_evaluated_warnings": warnings_evaluated,
        "excluded_seasons": excluded,
    }
    source_coverage = {
        "observation_start": environment.get("observation_start"),
        "observation_end": environment.get("observation_end"),
        "seasons_total": seasons_total,
        "seasons_evaluated_statistics": stats_evaluated,
        "seasons_evaluated_warnings": warnings_evaluated,
    }
    sources = [
        {
            "source_id": _SOURCE_ID,
            "provider": environment.get("provider"),
            "product": environment.get("product"),
            "version": environment.get("product_version"),
            "variables": used_variables,
            "coverage": source_coverage,
            "retrieved_at": environment.get("retrieved_at"),
        }
    ]

    return {
        "label": OUTLOOK_LABEL,
        "crop_id": crop_id,
        "status": _overall_status(indicators),
        "period_basis": "union_span",
        "period_definition": t2m_result["period_definition"],
        "analysis_period": t2m_result["analysis_period"],
        "coverage_rule": {
            "statistics": "min_90_percent_valid_days",
            "warnings": "required_100_percent_valid_days",
        },
        "season_coverage": season_coverage,
        "indicators": indicators,
        "missing": {
            "fill_value": fill_value,
            "missing_days": missing_days,
            "failed_requests": environment.get("failed_requests"),
        },
        "sources": sources,
        "notes": _dedupe(notes),
    }


def build_seasonal_ranges(
    environment: dict,
    period_start: dt.date | str,
    period_end: dt.date | str,
    *,
    start_year: int = 2000,
    end_year: int = 2025,
    last_complete_data_date: dt.date | str,
    sanitized_observations: dict | None = None,
) -> dict:
    """Return historical per-season ranges for the local POWER outlook demo."""
    if not isinstance(environment, dict):
        raise TypeError("environment must be a dict")
    observations = environment.get("observations")
    if not isinstance(observations, dict):
        raise ValueError("environment must contain an observations dict")
    sanitized = (
        sanitized_observations
        if isinstance(sanitized_observations, dict)
        else _sanitize_observations(observations, environment.get("fill_value"))
    )

    specifications = (
        ("T2M", "Temperature at 2 Meters", "C", "stats_min_90", "mean"),
        (
            "PRECTOTCORR",
            "Precipitation Corrected",
            "mm",
            "warnings_100",
            "total",
        ),
        (
            "GWETTOP",
            "MERRA-2 Surface Soil Wetness (not SMAP)",
            "1",
            "stats_min_90",
            "mean",
        ),
    )
    indicators = []
    seasons_total = None
    for variable, label, unit, rule, statistic in specifications:
        result = map_schedule_to_seasons(
            period_start,
            period_end,
            sanitized,
            variable,
            start_year=start_year,
            end_year=end_year,
            last_complete_data_date=last_complete_data_date,
            coverage_rule=rule,
        )
        if seasons_total is None:
            seasons_total = len(result["seasons"])
        values = []
        for season in result["evaluated_seasons"]:
            season_values = _season_values(sanitized, variable, season)
            if not season_values:
                continue
            values.append(
                sum(season_values)
                if statistic == "total"
                else sum(season_values) / len(season_values)
            )
        stats = _range_stats(values)
        indicators.append(
            {
                "variable": variable,
                "label": label,
                "unit": unit,
                "statistic": (
                    "per_season_total" if statistic == "total" else "per_season_mean"
                ),
                "coverage_rule": rule,
                "seasons_total": len(result["seasons"]),
                "seasons_evaluated": len(result["evaluated_seasons"]),
                "seasons_excluded": len(result["excluded_seasons"]),
                "min": stats["min"],
                "median": stats["median"],
                "max": stats["max"],
            }
        )

    has_values = all(item["min"] is not None for item in indicators)
    has_exclusions = any(item["seasons_excluded"] for item in indicators)
    if not has_values:
        status = "unavailable"
    elif has_exclusions:
        status = "partial"
    else:
        status = "ok"

    return {
        "status": status,
        "label": OUTLOOK_LABEL,
        "period_basis": "union_span",
        "period_start": str(period_start),
        "period_end": str(period_end),
        "analysis_period": {"start_year": start_year, "end_year": end_year},
        "coverage": {
            "start_year": start_year,
            "end_year": end_year,
            "seasons_total": seasons_total or 0,
            "seasons_evaluated": indicators[0]["seasons_evaluated"],
            "seasons_excluded": indicators[0]["seasons_excluded"],
        },
        "indicators": indicators,
        "thresholds_applied": False,
        "warnings": [],
        "notes": _seasonal_range_notes(environment),
        "source_ids": [environment.get("source_id") or "nasa_power_daily"],
    }


def _seasonal_range_notes(environment: dict) -> list[str]:
    notes = [
        "Seasonal ranges are historical ranges, not a forecast.",
        "GWETTOP is MERRA-2 surface soil wetness, not SMAP.",
    ]
    if environment.get("source_id") == "local_power_2000_2026":
        notes.insert(
            1,
            "1991-1999 is excluded because the local precipitation series is invalid.",
        )
    return notes


def _season_values(observations: dict, variable: str, season: dict) -> list[float]:
    start = dt.date.fromisoformat(season["start_date"])
    end = dt.date.fromisoformat(season["end_date"])
    values = []
    current = start
    while current <= end:
        record = observations.get(current.isoformat())
        value = record.get(variable) if isinstance(record, dict) else None
        if (
            isinstance(value, (int, float))
            and not isinstance(value, bool)
            and math.isfinite(float(value))
        ):
            values.append(float(value))
        current += dt.timedelta(days=1)
    return values


def _range_stats(values: list[float]) -> dict:
    if not values:
        return {"min": None, "median": None, "max": None}
    return {
        "min": min(values),
        "median": statistics.median(values),
        "max": max(values),
    }


def _warning_definitions(config: dict | None) -> dict:
    if config is None:
        return {key: dict(value) for key, value in WARNING_DEFINITIONS.items()}
    if not isinstance(config, dict):
        raise TypeError("warning_config must be a dict or None")
    if "id" in config and "variable" in config:
        config = {str(config["id"]): config}
    definitions: dict = {}
    for key, value in config.items():
        if not isinstance(key, str) or not key:
            raise ValueError("warning_config keys must be warning IDs")
        base = WARNING_DEFINITIONS.get(key)
        if isinstance(value, bool):
            if base is None:
                raise ValueError(f"unknown warning ID: {key}")
            definitions[key] = {**base, "enabled": value}
        elif isinstance(value, dict):
            merged = dict(base or {})
            merged.update(value)
            merged.setdefault("id", key)
            definitions[key] = merged
        else:
            raise TypeError("warning_config values must be bool or dict")
    return definitions


def _used_variables(enabled: list[dict]) -> list[str]:
    variables: list[str] = []
    for variable in (
        _STATISTICS_VARIABLE,
        _PRECIPITATION_VARIABLE,
        *(definition.get("variable") for definition in enabled),
    ):
        if isinstance(variable, str) and variable.strip() and variable not in variables:
            variables.append(variable)
    return variables


def sanitize_observations(observations: dict, fill_value: object) -> dict:
    """Return a fresh observation map with provider fill values set to None."""
    return _sanitize_observations(observations, fill_value)


def _sanitize_observations(observations: dict, fill_value: object) -> dict:
    sanitized = {}
    for date, record in observations.items():
        if not isinstance(record, dict):
            sanitized[date] = record
            continue
        sanitized[date] = {
            variable: (
                None if _is_fill(value, fill_value) else value
            )
            for variable, value in record.items()
        }
    return sanitized


def _is_fill(value: object, fill_value: object) -> bool:
    if fill_value is None or isinstance(value, bool):
        return False
    if not isinstance(value, (int, float)):
        return False
    try:
        number = float(value)
        target = float(fill_value)
    except (TypeError, ValueError):
        return False
    return math.isfinite(number) and math.isfinite(target) and number == target


def _missing_days(
    observations: dict,
    seasons: list[dict],
    variables: list[str],
    fill_value: object,
) -> int:
    count = 0
    for season in seasons:
        start = _coerce_date(season.get("start_date"), "season.start_date")
        end = _coerce_date(season.get("end_date"), "season.end_date")
        current = start
        while current <= end:
            record = observations.get(current.isoformat())
            for variable in variables:
                value = record.get(variable) if isinstance(record, dict) else None
                if _invalid_value(value, fill_value):
                    count += 1
            current += dt.timedelta(days=1)
    return count


def _invalid_value(value: object, fill_value: object) -> bool:
    if value is None:
        return True
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return True
    number = float(value)
    if not math.isfinite(number) or number in _FIXED_FILLS:
        return True
    return _is_fill(value, fill_value)


def _merge_excluded(results: list[tuple[str, dict]]) -> list[dict]:
    merged: dict[tuple, dict] = {}
    for rule, result in results:
        for season in result.get("excluded_seasons", []):
            key = _season_key(season)
            entry = merged.get(key)
            if entry is None:
                entry = {
                    "season_start_year": season.get("season_start_year"),
                    "start_date": season.get("start_date"),
                    "end_date": season.get("end_date"),
                    "valid_days": season.get("valid_days"),
                    "total_days": season.get("total_days"),
                    "coverage_fraction": season.get("coverage_fraction"),
                    "coverage_percent": season.get("coverage_percent"),
                    "included": False,
                    "reason": None,
                    "rules": [],
                    "reasons": [],
                }
                merged[key] = entry
            if rule not in entry["rules"]:
                entry["rules"].append(rule)
            reason = season.get("reason")
            if (
                isinstance(reason, str)
                and reason
                and reason not in entry["reasons"]
            ):
                entry["reasons"].append(reason)
    for entry in merged.values():
        entry["reason"] = entry["reasons"][0] if entry["reasons"] else None
    return sorted(
        merged.values(),
        key=lambda entry: (
            entry["season_start_year"] or 0,
            entry["start_date"] or "",
        ),
    )


def _season_key(season: dict) -> tuple:
    return (
        season.get("season_start_year"),
        season.get("start_date"),
        season.get("end_date"),
    )


def _overall_status(indicators: list[dict]) -> str:
    statuses = [indicator["status"] for indicator in indicators]
    if not statuses or all(status == "unavailable" for status in statuses):
        return "unavailable"
    if all(status == "ok" for status in statuses):
        return "ok"
    return "partial"


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


def _dedupe(values: list[str]) -> list[str]:
    return list(dict.fromkeys(values))
