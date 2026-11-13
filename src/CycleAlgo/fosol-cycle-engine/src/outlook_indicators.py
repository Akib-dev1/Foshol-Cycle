"""Seasonal outlook statistics and warning indicators (v1.md §6.2, §9.1-9.3, §14.4)."""

from __future__ import annotations

import datetime as dt
import math

_FILL_VALUES = frozenset({-999.0, -9999.0})
_STATS_RULE = "stats_min_90"
_WARNINGS_RULE = "warnings_100"


def calculate_temperature_statistics(
    observations: dict, season_result: dict
) -> dict:
    """Pool daily T2M across evaluated seasons and return descriptive statistics."""
    _validate_inputs(observations, season_result)
    seasons = _evaluated_seasons(season_result)
    excluded = _excluded_seasons(season_result)
    values: list[float] = []
    valid_days = 0
    total_days = 0
    for season in seasons:
        start, end = _season_bounds(season)
        total_days += (end - start).days + 1
        for day in _days(start, end):
            value = _value(observations, day, "T2M")
            if _valid_value(value):
                values.append(float(value))
                valid_days += 1

    notes: list[str] = []
    if not seasons or not values:
        status = "unavailable"
        stats = None
        notes.append(
            "No evaluated historical seasons with valid T2M observations; "
            "temperature statistics are unavailable."
        )
    else:
        stats = _statistics(values)
        status = "ok"
        if excluded:
            status = "partial"
            notes.append(
                f"{len(excluded)} historical season(s) were excluded by the "
                "stats_min_90 coverage rule."
            )
        if valid_days * 100 < total_days * 90:
            status = "partial"
            notes.append(
                "Pooled T2M valid coverage is below the 90% stats_min_90 threshold."
            )

    coverage = _coverage(valid_days, total_days, _STATS_RULE)
    coverage["excluded_seasons"] = len(excluded)
    return {
        "indicator": "temperature_statistics",
        "status": status,
        "definition": {
            "variable": "T2M",
            "statistic": "pooled_daily",
            "coverage_rule": _STATS_RULE,
            "coverage_min_percent": 90,
            "unit": "C",
            "statistics": ["median", "iqr", "q1", "q3", "min", "max"],
            "description": (
                "Pooled daily T2M across evaluated historical seasons; "
                "median and IQR use linear interpolation."
            ),
        },
        "period": _period(season_result),
        "sample": {
            "valid_days": valid_days,
            "seasons": len(seasons),
            "total_days": total_days,
        },
        "coverage": coverage,
        "stats": stats,
        "notes": notes,
        "source_ids": _source_ids(season_result),
    }


def calculate_precipitation_statistics(
    observations: dict, season_result: dict
) -> dict:
    """Return per-season precipitation totals and their cross-season statistics."""
    _validate_inputs(observations, season_result)
    seasons = _evaluated_seasons(season_result)
    excluded = _excluded_seasons(season_result)
    per_season_totals: list[dict] = []
    skipped = 0
    total_valid_days = 0
    total_days = 0
    for season in seasons:
        start, end = _season_bounds(season)
        days = (end - start).days + 1
        valid_days = 0
        total_mm = 0.0
        for day in _days(start, end):
            value = _value(observations, day, "PRECTOTCORR")
            if _valid_value(value):
                valid_days += 1
                total_mm += float(value)
        if valid_days != days:
            skipped += 1
            continue
        total_valid_days += valid_days
        total_days += days
        per_season_totals.append(
            {
                "season_start_year": season.get("season_start_year"),
                "start_date": season.get("start_date"),
                "end_date": season.get("end_date"),
                "total_mm": total_mm,
                "valid_days": valid_days,
                "total_days": days,
            }
        )

    notes: list[str] = []
    if not per_season_totals:
        status = "unavailable"
        stats = None
        notes.append(
            "No evaluated historical seasons with 100% valid PRECTOTCORR days; "
            "precipitation statistics are unavailable."
        )
    else:
        stats = _statistics([item["total_mm"] for item in per_season_totals])
        status = "ok"
        if excluded or skipped:
            status = "partial"
            if excluded:
                notes.append(
                    f"{len(excluded)} historical season(s) were excluded by the "
                    "warnings_100 coverage rule."
                )
            if skipped:
                notes.append(
                    f"{skipped} evaluated season(s) lacked 100% valid days and "
                    "were skipped."
                )

    coverage = _coverage(
        total_valid_days, total_days, _WARNINGS_RULE, len(per_season_totals)
    )
    coverage["excluded_seasons"] = len(excluded) + skipped
    return {
        "indicator": "precipitation_statistics",
        "status": status,
        "definition": {
            "variable": "PRECTOTCORR",
            "statistic": "per_season_totals",
            "coverage_rule": _WARNINGS_RULE,
            "coverage_min_percent": 100,
            "unit": "mm",
            "statistics": ["median", "iqr", "q1", "q3", "min", "max"],
            "description": (
                "Per-season PRECTOTCORR totals across evaluated historical "
                "seasons; median and IQR use linear interpolation."
            ),
        },
        "period": _period(season_result),
        "sample": {"seasons": len(per_season_totals)},
        "coverage": coverage,
        "per_season_totals": per_season_totals,
        "stats": stats,
        "unit": "mm",
        "notes": notes,
        "source_ids": _source_ids(season_result),
    }


def calculate_warning_indicator(
    observations: dict, season_result: dict, definition: dict
) -> dict:
    """Evaluate one configured warning indicator without a shared warning text."""
    if not isinstance(observations, dict):
        raise TypeError("observations must be a dict keyed by ISO date")
    if not isinstance(season_result, dict):
        raise TypeError("season_result must be a dict")
    if not isinstance(definition, dict):
        raise TypeError("definition must be a dict")
    enabled = bool(definition.get("enabled", False))
    base = {
        "indicator": definition.get("id"),
        "enabled": enabled,
        "definition": definition,
        "period": _period(season_result),
        "unit": definition.get("unit"),
        "source_ids": _source_ids(season_result),
    }
    if not enabled:
        return {
            **base,
            "status": "disabled",
            "text": definition.get("indicator_text"),
            "notes": ["Warning indicator is disabled by configuration."],
        }

    _validate_inputs(observations, season_result)
    _validate_definition(definition)
    seasons = _evaluated_seasons(season_result)
    excluded = _excluded_seasons(season_result)
    complete_seasons = 0
    numerator = 0
    days_meeting = 0
    total_valid_days = 0
    total_days = 0
    skipped = 0
    variable = definition["variable"]
    comparison = definition["comparison"]
    threshold = float(definition["threshold"])
    for season in seasons:
        start, end = _season_bounds(season)
        days = (end - start).days + 1
        valid_days = 0
        season_days_meeting = 0
        for day in _days(start, end):
            value = _value(observations, day, variable)
            if not _valid_value(value):
                continue
            valid_days += 1
            if _meets(float(value), comparison, threshold):
                season_days_meeting += 1
        if valid_days != days:
            skipped += 1
            continue
        complete_seasons += 1
        total_valid_days += valid_days
        total_days += days
        if season_days_meeting:
            numerator += 1
            days_meeting += season_days_meeting

    denominator = complete_seasons
    coverage = _coverage(
        total_valid_days, total_days, _WARNINGS_RULE, denominator
    )
    coverage["excluded_seasons"] = len(excluded) + skipped
    notes: list[str] = []
    if denominator == 0:
        status = "unavailable"
        numerator = None
        days_meeting = None
        notes.append(
            "No evaluated historical seasons with 100% valid days; risk is "
            "unavailable, not zero."
        )
        text = (
            f"{definition['indicator_text']} No evaluated historical seasons; "
            "risk is unavailable, not zero."
        )
    else:
        status = "ok"
        if excluded or skipped:
            status = "partial"
            if excluded:
                notes.append(
                    f"{len(excluded)} historical season(s) were excluded by the "
                    "warnings_100 coverage rule."
                )
            if skipped:
                notes.append(
                    f"{skipped} evaluated season(s) lacked 100% valid days and "
                    "were skipped."
                )
        text = (
            f"{definition['indicator_text']} Occurred in {numerator} of "
            f"{denominator} evaluated historical seasons."
        )

    return {
        **base,
        "status": status,
        "numerator": numerator,
        "denominator": denominator,
        "days_meeting": days_meeting,
        "sample": {"seasons": denominator},
        "coverage": coverage,
        "text": text,
        "notes": notes,
    }


def _statistics(values: list[float]) -> dict:
    ordered = sorted(float(value) for value in values)
    q1 = _quantile_linear(ordered, 0.25)
    median = _quantile_linear(ordered, 0.5)
    q3 = _quantile_linear(ordered, 0.75)
    return {
        "median": median,
        "iqr": q3 - q1,
        "q1": q1,
        "q3": q3,
        "min": ordered[0],
        "max": ordered[-1],
    }


def _quantile_linear(ordered: list[float], q: float) -> float:
    """Return a quantile using linear interpolation between closest ranks."""
    if not ordered:
        raise ValueError("quantile requires at least one value")
    if len(ordered) == 1:
        return ordered[0]
    position = (len(ordered) - 1) * q
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[lower]
    fraction = position - lower
    return ordered[lower] + (ordered[upper] - ordered[lower]) * fraction


def _coverage(
    valid_days: int, total_days: int, rule: str, seasons: int | None = None
) -> dict:
    coverage = {
        "rule": rule,
        "valid_days": valid_days,
        "total_days": total_days,
        "coverage_percent": (
            round(valid_days * 100 / total_days, 2) if total_days else 0.0
        ),
    }
    if seasons is not None:
        coverage["seasons"] = seasons
    return coverage


def _validate_inputs(observations: object, season_result: object) -> None:
    if not isinstance(observations, dict):
        raise TypeError("observations must be a dict keyed by ISO date")
    if not isinstance(season_result, dict):
        raise TypeError("season_result must be a dict")
    if not isinstance(season_result.get("evaluated_seasons"), (list, tuple)):
        raise ValueError("season_result must contain an evaluated_seasons list")


def _validate_definition(definition: dict) -> None:
    variable = definition.get("variable")
    if not isinstance(variable, str) or not variable.strip():
        raise ValueError("warning definition variable must be a non-empty string")
    if definition.get("comparison") not in ("gt", "lt"):
        raise ValueError("warning definition comparison must be 'gt' or 'lt'")
    threshold = definition.get("threshold")
    if (
        isinstance(threshold, bool)
        or not isinstance(threshold, (int, float))
        or not math.isfinite(float(threshold))
    ):
        raise ValueError("warning definition threshold must be a finite number")
    for field in ("indicator_text", "weather_risk_threshold_text"):
        text = definition.get(field)
        if not isinstance(text, str) or not text.strip():
            raise ValueError(f"warning definition {field} must be non-empty")


def _evaluated_seasons(season_result: dict) -> list[dict]:
    seasons = season_result.get("evaluated_seasons")
    if not isinstance(seasons, (list, tuple)):
        raise ValueError("season_result must contain an evaluated_seasons list")
    return [season for season in seasons if isinstance(season, dict)]


def _excluded_seasons(season_result: dict) -> list[dict]:
    seasons = season_result.get("excluded_seasons")
    if not isinstance(seasons, (list, tuple)):
        return []
    return [season for season in seasons if isinstance(season, dict)]


def _season_bounds(season: dict) -> tuple[dt.date, dt.date]:
    start = _coerce_date(season.get("start_date"), "season.start_date")
    end = _coerce_date(season.get("end_date"), "season.end_date")
    if end < start:
        raise ValueError("season.end_date must not be before start_date")
    return start, end


def _days(start: dt.date, end: dt.date):
    current = start
    while current <= end:
        yield current
        current += dt.timedelta(days=1)


def _value(observations: dict, day: dt.date, variable: str):
    record = observations.get(day.isoformat())
    if not isinstance(record, dict):
        return None
    return record.get(variable)


def _valid_value(value: object) -> bool:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return False
    number = float(value)
    return math.isfinite(number) and number not in _FILL_VALUES


def _meets(value: float, comparison: str, threshold: float) -> bool:
    if comparison == "gt":
        return value > threshold
    if comparison == "lt":
        return value < threshold
    raise ValueError("comparison must be 'gt' or 'lt'")


def _period(season_result: dict) -> dict:
    return {
        "period_start": season_result.get("period_start"),
        "period_end": season_result.get("period_end"),
        "analysis_period": season_result.get("analysis_period"),
        "crosses_year": season_result.get("crosses_year"),
        "coverage_rule": season_result.get("coverage_rule"),
    }


def _source_ids(season_result: dict) -> list:
    source_ids = season_result.get("source_ids")
    if isinstance(source_ids, str):
        return [source_ids]
    if isinstance(source_ids, (list, tuple)):
        return list(source_ids)
    return []


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
