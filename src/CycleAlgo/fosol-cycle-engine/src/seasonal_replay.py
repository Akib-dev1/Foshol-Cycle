"""Historical seasonal replay mapping and coverage (v1.md §9.2, §17.11).

The E6 union span is mapped to each historical season by month/day. Coverage is
assessed on the actual mapped crop period; missing dates, ``None``, non-finite
values, and provider fill values are invalid and never favorable.
"""

from __future__ import annotations

import datetime as dt
import math

_COVERAGE_RULES = {"stats_min_90": 90, "warnings_100": 100}
_FILL_VALUES = frozenset({-999.0, -9999.0})


def map_schedule_to_seasons(
    period_start: dt.date | str,
    period_end: dt.date | str,
    observations: dict,
    variable: str,
    *,
    start_year: int = 1991,
    end_year: int = 2025,
    last_complete_data_date: dt.date | str,
    coverage_rule: str = "stats_min_90",
) -> dict:
    """Map one union-span schedule to historical seasons and assess coverage."""
    if coverage_rule not in _COVERAGE_RULES:
        raise ValueError(
            "coverage_rule must be one of " + ", ".join(_COVERAGE_RULES)
        )
    if isinstance(start_year, bool) or not isinstance(start_year, int):
        raise TypeError("start_year must be an integer")
    if isinstance(end_year, bool) or not isinstance(end_year, int):
        raise TypeError("end_year must be an integer")
    if not 1 <= start_year <= end_year <= 9999:
        raise ValueError("start_year must be between 1 and end_year")
    if not isinstance(variable, str) or not variable.strip():
        raise ValueError("variable must be a non-empty string")
    if not isinstance(observations, dict):
        raise TypeError("observations must be a dict keyed by ISO date")

    start = _coerce_date(period_start, "period_start")
    end = _coerce_date(period_end, "period_end")
    if end < start:
        raise ValueError("period_end must not be before period_start")
    last_complete = _coerce_date(
        last_complete_data_date, "last_complete_data_date"
    )

    start_month_day = (start.month, start.day)
    end_month_day = (end.month, end.day)
    crosses_year = end_month_day < start_month_day
    notes = [
        "The union span from earliest planting to latest harvest is "
        "conservative; it may include days from alternative timing "
        "realizations rather than one actual crop."
    ]

    seasons: list[dict] = []
    evaluated: list[dict] = []
    excluded: list[dict] = []
    leap_adjusted_any = False
    leap_endpoint = (2, 29) in (start_month_day, end_month_day)

    for season_start_year in range(start_year, end_year + 1):
        season_start, start_adjusted = _season_date(
            season_start_year, *start_month_day
        )
        end_year_actual = season_start_year + 1 if crosses_year else season_start_year
        season_end, end_adjusted = _season_date(
            end_year_actual, *end_month_day
        )
        total_days = (season_end - season_start).days + 1
        valid_days = _valid_days(observations, variable, season_start, season_end)
        coverage_fraction = round(valid_days / total_days, 6)
        coverage_percent = round(valid_days * 100 / total_days, 2)
        leap_adjusted = start_adjusted or end_adjusted
        leap_adjusted_any = leap_adjusted_any or leap_adjusted
        season = {
            "season_start_year": season_start_year,
            "start_date": season_start.isoformat(),
            "end_date": season_end.isoformat(),
            "total_days": total_days,
            "valid_days": valid_days,
            "coverage_fraction": coverage_fraction,
            "coverage_percent": coverage_percent,
            "leap_day_adjusted": leap_adjusted,
            "leap_day_adjustments": [
                name
                for name, adjusted in (
                    ("start", start_adjusted),
                    ("end", end_adjusted),
                )
                if adjusted
            ],
            "included": False,
        }

        if season_end > last_complete:
            reason = (
                f"Mapped season end {season_end.isoformat()} is after "
                f"last_complete_data_date {last_complete.isoformat()}."
            )
        elif not _coverage_ok(valid_days, total_days, coverage_rule):
            reason = (
                f"Valid coverage {valid_days}/{total_days} days "
                f"({coverage_percent}%) is below {coverage_rule}."
            )
        else:
            reason = None

        if reason is None:
            season["included"] = True
            evaluated.append(season)
        else:
            season["reason"] = reason
            excluded.append(season)
        seasons.append(season)

    if leap_endpoint:
        if leap_adjusted_any:
            notes.append(
                "February 29 endpoints were adjusted to February 28 in "
                "non-leap seasons."
            )
        else:
            notes.append(
                "February 29 endpoints were retained in leap seasons."
            )
    notes.append(
        "Coverage counts only finite numeric observations; missing dates, "
        "None, non-finite values, and provider fill values are invalid."
    )

    return {
        "period_basis": "union_span",
        "period_definition": (
            "E6 union span from planting_range.earliest to "
            "harvest_range.latest; the end month-day maps to the next year "
            "when it precedes the start month-day."
        ),
        "period_start": start.isoformat(),
        "period_end": end.isoformat(),
        "start_month_day": f"{start_month_day[0]:02d}-{start_month_day[1]:02d}",
        "end_month_day": f"{end_month_day[0]:02d}-{end_month_day[1]:02d}",
        "crosses_year": crosses_year,
        "analysis_period": {
            "start_year": start_year,
            "end_year": end_year,
        },
        "last_complete_data_date": last_complete.isoformat(),
        "coverage_rule": coverage_rule,
        "variable": variable,
        "seasons": seasons,
        "evaluated_seasons": evaluated,
        "excluded_seasons": excluded,
        "notes": notes,
    }


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


def _season_date(year: int, month: int, day: int) -> tuple[dt.date, bool]:
    try:
        return dt.date(year, month, day), False
    except ValueError:
        if month == 2 and day == 29:
            return dt.date(year, 2, 28), True
        raise


def _valid_days(
    observations: dict, variable: str, start: dt.date, end: dt.date
) -> int:
    valid = 0
    current = start
    while current <= end:
        record = observations.get(current.isoformat())
        if isinstance(record, dict):
            value = record.get(variable)
            if _valid_value(value):
                valid += 1
        current += dt.timedelta(days=1)
    return valid


def _valid_value(value: object) -> bool:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return False
    number = float(value)
    return math.isfinite(number) and number not in _FILL_VALUES


def _coverage_ok(valid_days: int, total_days: int, rule: str) -> bool:
    if rule == "stats_min_90":
        return valid_days * 100 >= total_days * 90
    return valid_days == total_days
