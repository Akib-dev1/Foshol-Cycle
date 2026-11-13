"""Historical POWER exposure metrics for the three iteration-2 views.

These are growing-period adaptations of meteorological indices and a
crop-guidance temperature match. They are not annual Climdex outputs, crop
damage thresholds, irrigation demand, or agricultural suitability scores.
"""

from __future__ import annotations

import datetime as dt
import math
import statistics

from src.seasonal_replay import map_schedule_to_seasons

TEMPERATURE_VARIABLE = "T2M"
RAIN_VARIABLE = "PRECTOTCORR"
DRY_DAY_MM = 1.0
HEAVY_RAIN_MM = 20.0
SCHEDULES = ("min_realization", "max_realization")
_TEMPERATURE_UNITS = frozenset(
    {"c", "deg c", "degc", "degree c", "degrees c", "celsius"}
)
_RAIN_UNITS = frozenset(
    {
        "mm/day",
        "mm/d",
        "mm day-1",
        "mm day^-1",
        "mm/day-1",
        "kg m-2 day-1",
        "kg/m2/day",
    }
)
_ECOCROP_PROVENANCE = {
    "Oryza sativa": ("1574", "Oryza sativa"),
    "Triticum aestivum": ("2114", "Triticum aestivum"),
    "Brassica juncea": ("548", "Brassica juncea"),
    "Lens culinaris": ("7209", "Lens culinaris"),
    "Vigna radiata": ("2150", "Vigna radiata"),
    "Zea mays": ("2175", "Zea mays"),
    "Solanum tuberosum": ("1971", "Solanum tuberosum"),
}
_ECOCROP_SOURCE = (
    "FAO EcoCrop database, OpenCLIM mirror EcoCrop_DB.csv "
    "(https://github.com/OpenCLIM/ecocrop)"
)
CLIMATE_PREFERENCES = (
    "closest_temperature_match",
    "least_dry_spell_exposure",
    "least_heavy_rain_exposure",
)
CLIMATE_METRICS = {
    "closest_temperature_match": "temperature_distance_c",
    "least_dry_spell_exposure": "dry_spell_days",
    "least_heavy_rain_exposure": "heavy_rain_frequency",
}
CLIMATE_UNITS = {
    "closest_temperature_match": "C",
    "least_dry_spell_exposure": "days",
    "least_heavy_rain_exposure": "heavy days per valid growing day",
}


def climate_definitions() -> dict:
    return {
        "temperature": {
            "variable": "T2M",
            "required_units": ["C", "degC", "Celsius"],
            "season_statistic": "median_daily_t2m",
            "match": (
                "distance from the crop profile's EcoCrop temperature optimum "
                "range; 0 when the seasonal median is inside the range"
            ),
            "source": _ECOCROP_SOURCE,
            "applicability": (
                "published general species/crop-level EcoCrop range; not "
                "variety- or stage-specific"
            ),
            "seasonal_matching": (
                "project-defined median of daily T2M over the realized growing "
                "period"
            ),
            "ordering": "lower median seasonal distance is closer to guidance",
            "tolerance": "reported as context only; not used for ordering",
            "scope": "general crop guidance, not variety- or stage-specific damage",
        },
        "dry_spell": {
            "required_units": ["mm/day"],
            "dry_day": "PRECTOTCORR < 1 mm/day",
            "statistic": "longest consecutive dry-day run within one crop period",
            "ordering": "lower equal-crop-weighted median longest run",
            "scope": "growing-period exposure, not inherent drought tolerance",
        },
        "heavy_rain": {
            "required_units": ["mm/day"],
            "heavy_day": "PRECTOTCORR >= 20 mm/day (R20mm adaptation)",
            "statistic": "heavy-rain days per valid growing day",
            "ordering": "lower equal-crop-weighted frequency",
            "scope": "meteorological exposure, not crop damage or waterlogging",
        },
        "common_seasons": (
            "only seasons with complete daily T2M and PRECTOTCORR for every "
            "crop in both completion-optimized schedules"
        ),
        "schedules": (
            "min_realization and max_realization are completion-optimized "
            "examples; ordering uses the higher exposure of the two, not a "
            "worst-case bound over all possible schedules"
        ),
        "equal_crop_weighting": True,
    }


def climate_limitations() -> list[str]:
    return [
        "Temperature uses general EcoCrop optimum/tolerance guidance; it is not a stage-specific daily damage threshold or a variety validation.",
        "Dry spell and heavy rain are growing-period adaptations of meteorological indices, not standard annual Climdex outputs and not crop-damage predictions.",
        "Rainfall totals are descriptive context; no irrigation demand is inferred and no rainfall-minus-demand calculation is made.",
        "GWETTOP is regional MERRA-2 surface wetness context, not root-zone moisture or a crop threshold.",
        "Equal weighting of the three crop summaries is a disclosed product convention, not proof of duration neutrality or agricultural suitability.",
        "Missing days are excluded; they are never treated as zero rain or joined across gaps.",
    ]


def _normalized_unit(value: object) -> str | None:
    if not isinstance(value, str) or not value.strip():
        return None
    return " ".join(value.strip().lower().replace("°", "deg").split())


def _unit_status(environment: dict, variable: str, aliases: frozenset[str]) -> dict:
    variables = environment.get("variables")
    metadata = variables.get(variable) if isinstance(variables, dict) else None
    units = metadata.get("units") if isinstance(metadata, dict) else None
    normalized = _normalized_unit(units)
    if normalized is None:
        return {
            "status": "unavailable",
            "units": units,
            "reason": "UNITS_UNCONFIRMED",
        }
    if normalized not in aliases:
        return {
            "status": "unavailable",
            "units": units,
            "reason": "UNITS_INCOMPATIBLE",
        }
    return {"status": "ok", "units": units, "reason": None}


def _temperature_provenance(profile: dict) -> dict | None:
    explicit = profile.get("temperature_provenance")
    if isinstance(explicit, dict) and explicit.get("source") and explicit.get("eco_port_code"):
        return explicit
    scientific_name = profile.get("scientific_name")
    if not isinstance(scientific_name, str) or not scientific_name.strip():
        raw = profile.get("raw")
        scientific_name = raw.get("scientific_name") if isinstance(raw, dict) else None
    entry = (
        _ECOCROP_PROVENANCE.get(scientific_name.strip())
        if isinstance(scientific_name, str)
        else None
    )
    if entry is None:
        return None
    return {
        "source": _ECOCROP_SOURCE,
        "eco_port_code": entry[0],
        "scientific_name": entry[1],
        "applicability": (
            "published general species/crop-level EcoCrop range; not a "
            "variety- or stage-specific damage threshold"
        ),
        "seasonal_matching": (
            "project-defined median of daily T2M over the realized growing "
            "period, compared with the published optimum range"
        ),
    }


def build_climate_metrics(
    branch: dict,
    profiles: dict,
    environment: dict | None,
    completion: dict,
    *,
    start_year: int,
    end_year: int,
    last_complete_data_date: object,
    sanitized_observations: dict | None = None,
    cache: dict | None = None,
) -> dict:
    """Build per-crop, per-season evidence for the three climate views."""
    base = {
        "status": "unavailable",
        "analysis_period": {"start_year": start_year, "end_year": end_year},
        "definitions": climate_definitions(),
        "limitations": climate_limitations(),
    }
    if not isinstance(environment, dict):
        base["reason"] = "POWER environment is unavailable."
        return base
    observations = sanitized_observations
    if not isinstance(observations, dict):
        observations = environment.get("observations")
    if not isinstance(observations, dict):
        base["reason"] = "POWER observations are unavailable."
        return base
    if not isinstance(completion, dict) or completion.get("status") != "ok":
        base["reason"] = "Completion realizations are unavailable."
        return base
    if last_complete_data_date is None:
        base["reason"] = "last_complete_data_date is not configured."
        return base
    if not isinstance(branch, dict) or not isinstance(branch.get("crops"), list):
        base["reason"] = "Branch crop structure is invalid."
        return base

    temp_unit = _unit_status(environment, TEMPERATURE_VARIABLE, _TEMPERATURE_UNITS)
    rain_unit = _unit_status(environment, RAIN_VARIABLE, _RAIN_UNITS)
    provenance = {}
    for crop in branch["crops"]:
        crop_id = str(crop.get("crop_id") or "")
        profile = profiles.get(crop_id) if isinstance(profiles, dict) else None
        if not isinstance(profile, dict):
            profile = crop
        provenance[crop_id] = _temperature_provenance(profile)
    temp_ready = temp_unit["status"] == "ok" and all(provenance.values())
    rain_ready = rain_unit["status"] == "ok"
    base.update(
        {
            "unit_validation": {
                TEMPERATURE_VARIABLE: temp_unit,
                RAIN_VARIABLE: rain_unit,
            },
            "temperature_provenance": provenance,
        }
    )

    def map_variable(variable: str, start: str, end: str) -> dict:
        key = (
            "climate_map",
            variable,
            start,
            end,
            start_year,
            end_year,
            str(last_complete_data_date),
            "warnings_100",
            id(observations),
            id(environment),
            environment.get("fill_value"),
        )
        if cache is not None and key in cache:
            return cache[key]
        result = map_schedule_to_seasons(
            start,
            end,
            observations,
            variable,
            start_year=start_year,
            end_year=end_year,
            last_complete_data_date=last_complete_data_date,
            coverage_rule="warnings_100",
        )
        if cache is not None:
            cache[key] = result
        return result

    per_schedule: dict[str, dict] = {}
    for schedule in SCHEDULES:
        realization = completion.get(schedule)
        if not isinstance(realization, dict):
            per_schedule[schedule] = {
                "status": "unavailable",
                "crops": [],
                "temperature_complete_seasons": [],
                "rain_complete_seasons": [],
                "complete_seasons": [],
                "reason": f"{schedule} is unavailable.",
            }
            continue
        crops = []
        for index, crop in enumerate(branch["crops"]):
            crop_id = str(crop.get("crop_id") or "")
            profile = profiles.get(crop_id) if isinstance(profiles, dict) else None
            if not isinstance(profile, dict):
                profile = crop
            start_key = ("p1", "p2", "p3")[index]
            end_key = ("h1", "h2", "h3")[index]
            start = realization.get(start_key)
            end = realization.get(end_key)
            if not isinstance(start, str) or not isinstance(end, str):
                crops.append(_unavailable_crop(crop_id, index + 1, "schedule dates missing"))
                continue
            try:
                temp_seasons = (
                    {
                        season["season_start_year"]: season
                        for season in map_variable(TEMPERATURE_VARIABLE, start, end)[
                            "evaluated_seasons"
                        ]
                    }
                    if temp_ready
                    else {}
                )
                rain_seasons = (
                    {
                        season["season_start_year"]: season
                        for season in map_variable(RAIN_VARIABLE, start, end)[
                            "evaluated_seasons"
                        ]
                    }
                    if rain_ready
                    else {}
                )
            except (TypeError, ValueError) as exc:
                crops.append(
                    _unavailable_crop(crop_id, index + 1, str(exc) or "schedule mapping failed")
                )
                continue
            seasons = {}
            for year in sorted(set(temp_seasons) | set(rain_seasons)):
                season = temp_seasons.get(year) or rain_seasons.get(year)
                record_key = (
                    "climate_season", id(observations), id(environment), id(profile),
                    season["start_date"], season["end_date"],
                    year in temp_seasons, year in rain_seasons,
                )
                if cache is not None and record_key in cache:
                    record = cache[record_key]
                else:
                    record = _season_record(
                        observations,
                        season,
                        profile,
                        include_temperature=year in temp_seasons,
                        include_rain=year in rain_seasons,
                    )
                    if cache is not None:
                        cache[record_key] = record
                if record is not None:
                    seasons[str(year)] = record
            crops.append(
                {
                    "crop_id": crop_id,
                    "position": index + 1,
                    "seasons": len(seasons),
                    "season_records": seasons,
                    "temperature_seasons": sorted(temp_seasons),
                    "rain_seasons": sorted(rain_seasons),
                    "temperature_range": _temperature_range(profile),
                    "temperature_provenance": provenance.get(crop_id),
                    "status": "ok" if seasons else "unavailable",
                }
            )
        if len(crops) != 3:
            per_schedule[schedule] = {
                "status": "unavailable",
                "crops": crops,
                "temperature_complete_seasons": [],
                "rain_complete_seasons": [],
                "complete_seasons": [],
                "reason": "The branch does not contain three crops.",
            }
            continue
        temperature_complete = set(crops[0]["temperature_seasons"])
        rain_complete = set(crops[0]["rain_seasons"])
        for crop in crops[1:]:
            temperature_complete &= set(crop["temperature_seasons"])
            rain_complete &= set(crop["rain_seasons"])
        per_schedule[schedule] = {
            "status": (
                "ok"
                if temperature_complete and rain_complete
                else "partial"
                if temperature_complete or rain_complete
                else "unavailable"
            ),
            "crops": crops,
            "temperature_complete_seasons": sorted(temperature_complete),
            "rain_complete_seasons": sorted(rain_complete),
            "complete_seasons": sorted(temperature_complete & rain_complete),
        }

    missing_provenance = sorted(
        crop_id for crop_id, value in provenance.items() if not value
    )
    temp_view_ok = temp_ready and all(
        per_schedule[schedule]["temperature_complete_seasons"]
        for schedule in SCHEDULES
    )
    if temp_unit["status"] != "ok":
        temp_reason = (
            "TEMPERATURE_UNITS_UNAVAILABLE: "
            f"{temp_unit['reason']} for T2M."
        )
    elif missing_provenance:
        temp_reason = (
            "TEMPERATURE_PROVENANCE_UNVERIFIED: no EcoCrop entry for "
            + ", ".join(missing_provenance)
            + "."
        )
    elif not temp_view_ok:
        temp_reason = "TEMPERATURE_COVERAGE_UNAVAILABLE: no common complete T2M seasons."
    else:
        temp_reason = None
    rain_view_ok = rain_ready and all(
        per_schedule[schedule]["rain_complete_seasons"]
        for schedule in SCHEDULES
    )
    if rain_unit["status"] != "ok":
        rain_reason = (
            "RAIN_UNITS_UNAVAILABLE: "
            f"{rain_unit['reason']} for PRECTOTCORR."
        )
    elif not rain_view_ok:
        rain_reason = "RAIN_COVERAGE_UNAVAILABLE: no common complete PRECTOTCORR seasons."
    else:
        rain_reason = None
    result = {
        **base,
        "per_schedule": per_schedule,
        "summary": {
            schedule: _schedule_summary(per_schedule[schedule])
            for schedule in SCHEDULES
        },
        "views": {
            "temperature": {
                "status": "ok" if temp_view_ok else "unavailable",
                "reason": temp_reason,
            },
            "rain": {
                "status": "ok" if rain_view_ok else "unavailable",
                "reason": rain_reason,
            },
        },
    }
    temp_schedules = [
        schedule
        for schedule in SCHEDULES
        if per_schedule[schedule]["temperature_complete_seasons"]
    ]
    rain_schedules = [
        schedule
        for schedule in SCHEDULES
        if per_schedule[schedule]["rain_complete_seasons"]
    ]
    if len(temp_schedules) == len(SCHEDULES) and len(rain_schedules) == len(SCHEDULES):
        result["status"] = "ok"
    elif temp_schedules or rain_schedules:
        result["status"] = "partial"
        result["reason"] = "One climate view or completion schedule lacks complete seasons."
    else:
        result["reason"] = "No complete climate seasons are available."
    return result


def branch_common_seasons(climate: dict | None, view: str = "temperature") -> set[int]:
    if view not in ("temperature", "rain"):
        raise ValueError("view must be 'temperature' or 'rain'")
    if not isinstance(climate, dict):
        return set()
    field = (
        "temperature_complete_seasons"
        if view == "temperature"
        else "rain_complete_seasons"
    )
    sets = []
    per_schedule = climate.get("per_schedule")
    if not isinstance(per_schedule, dict):
        return set()
    for schedule in SCHEDULES:
        record = per_schedule.get(schedule)
        if not isinstance(record, dict) or not record.get(field):
            return set()
        sets.append(set(record[field]))
    return set.intersection(*sets) if sets else set()


def evaluate_climate(
    climate: dict | None,
    common_seasons: set[int],
    preference: str,
) -> dict | None:
    """Return the ordered exposure value and visible schedule/context summaries."""
    if preference not in CLIMATE_METRICS or not common_seasons:
        return None
    if not isinstance(climate, dict):
        return None
    per_schedule = climate.get("per_schedule")
    if not isinstance(per_schedule, dict):
        return None
    view = "temperature" if preference == "closest_temperature_match" else "rain"
    metric_key = CLIMATE_METRICS[preference]
    schedule_values = {}
    schedule_summaries = {}
    for schedule in SCHEDULES:
        record = per_schedule.get(schedule)
        if not isinstance(record, dict):
            return None
        keys = set(
            record.get(
                "temperature_complete_seasons"
                if view == "temperature"
                else "rain_complete_seasons",
                [],
            )
        )
        if not common_seasons <= keys:
            return None
        summary = _schedule_summary(
            record,
            temperature_seasons=common_seasons if view == "temperature" else None,
            rain_seasons=common_seasons if view == "rain" else None,
        )
        value = summary.get(metric_key)
        if value is None:
            return None
        schedule_values[schedule] = value
        schedule_summaries[schedule] = summary
    value = max(schedule_values.values())
    return {
        "view": view,
        "metric": metric_key,
        "value": value,
        "unit": CLIMATE_UNITS[preference],
        "schedule_values": schedule_values,
        "schedule_summaries": schedule_summaries,
        "common_seasons": sorted(common_seasons),
        "ordering_basis": (
            "higher exposure of the two completion-optimized schedules; "
            "not a worst-case bound over all possible schedules"
        ),
    }


def strip_climate_raw(branches: list[dict]) -> None:
    """Remove raw season records after ranking; keep summaries and coverage."""
    for branch in branches:
        if not isinstance(branch, dict):
            continue
        metrics = branch.get("metrics")
        climate = metrics.get("climate") if isinstance(metrics, dict) else None
        per_schedule = climate.get("per_schedule") if isinstance(climate, dict) else None
        if not isinstance(per_schedule, dict):
            continue
        for record in per_schedule.values():
            if not isinstance(record, dict):
                continue
            for crop in record.get("crops", []):
                if isinstance(crop, dict):
                    crop.pop("season_records", None)


def _season_record(
    observations: dict,
    season: dict,
    profile: dict,
    *,
    include_temperature: bool,
    include_rain: bool,
) -> dict | None:
    start = _date(season.get("start_date"))
    end = _date(season.get("end_date"))
    if start is None or end is None:
        return None
    temp_values = (
        _daily_values(observations, start, end, TEMPERATURE_VARIABLE)
        if include_temperature
        else None
    )
    rain_values = (
        _daily_values(observations, start, end, RAIN_VARIABLE)
        if include_rain
        else None
    )
    if temp_values is None and rain_values is None:
        return None
    if temp_values is not None and rain_values is not None:
        if len(temp_values) != len(rain_values):
            return None
    growing_days = len(rain_values) if rain_values is not None else len(temp_values)
    if growing_days == 0:
        return None
    range_info = _temperature_range(profile)
    temp_median = statistics.median(temp_values) if temp_values is not None else None
    distance = (
        _temperature_distance(temp_median, range_info)
        if temp_median is not None
        else None
    )
    within_optimum = (
        temp_median is not None
        and range_info["optimum_min"] is not None
        and range_info["optimum_max"] is not None
        and range_info["optimum_min"] <= temp_median <= range_info["optimum_max"]
    )
    within_tolerance = (
        temp_median is not None
        and range_info["tolerance_min"] is not None
        and range_info["tolerance_max"] is not None
        and range_info["tolerance_min"] <= temp_median <= range_info["tolerance_max"]
    )
    longest_dry = None
    if rain_values is not None:
        longest_dry = 0
        run = 0
        for value in rain_values:
            if value < DRY_DAY_MM:
                run += 1
                longest_dry = max(longest_dry, run)
            else:
                run = 0
    return {
        "season_start_year": season.get("season_start_year"),
        "start_date": season.get("start_date"),
        "end_date": season.get("end_date"),
        "growing_days": growing_days,
        "temperature_valid_days": (
            len(temp_values) if temp_values is not None else None
        ),
        "rain_valid_days": len(rain_values) if rain_values is not None else None,
        "t2m_median_c": temp_median,
        "temperature_distance_c": distance,
        "temperature_within_optimum": (
            within_optimum if temp_median is not None else None
        ),
        "temperature_within_tolerance": (
            within_tolerance if temp_median is not None else None
        ),
        "rain_total_mm": sum(rain_values) if rain_values is not None else None,
        "heavy_rain_days": (
            sum(1 for value in rain_values if value >= HEAVY_RAIN_MM)
            if rain_values is not None
            else None
        ),
        "longest_dry_run_days": longest_dry,
    }


def _schedule_summary(
    record: dict,
    *,
    temperature_seasons: object = None,
    rain_seasons: object = None,
) -> dict:
    if not isinstance(record, dict):
        return {"status": "unavailable"}
    if temperature_seasons is None:
        temperature_seasons = record.get("temperature_complete_seasons") or []
    if rain_seasons is None:
        rain_seasons = record.get("rain_complete_seasons") or []
    temp_keys = set(temperature_seasons)
    rain_keys = set(rain_seasons)
    crops = []
    for crop in record.get("crops", []):
        if not isinstance(crop, dict):
            continue
        crops.append(_crop_summary(crop, temp_keys, rain_keys))
    values = _branch_summary(crops)
    available = any(
        values[key] is not None
        for key in (
            "temperature_distance_c",
            "dry_spell_days",
            "heavy_rain_frequency",
        )
    )
    return {
        "status": "ok" if len(crops) == 3 and available else "partial",
        "seasons": len(temp_keys | rain_keys),
        "temperature_seasons": len(temp_keys),
        "rain_seasons": len(rain_keys),
        "per_crop": crops,
        "temperature_distance_c": values["temperature_distance_c"],
        "dry_spell_days": values["dry_spell_days"],
        "heavy_rain_frequency": values["heavy_rain_frequency"],
        "rainfall_median_mm": values["rainfall_median_mm"],
        "growing_days_median": values["growing_days_median"],
    }


def _crop_summary(
    crop: dict, temperature_seasons: set[int], rain_seasons: set[int]
) -> dict:
    all_seasons = (crop.get("season_records") or {})
    temp_records = [
        value
        for key, value in all_seasons.items()
        if int(key) in temperature_seasons
    ]
    rain_records = [
        value for key, value in all_seasons.items() if int(key) in rain_seasons
    ]
    temperatures = [
        item["temperature_distance_c"]
        for item in temp_records
        if isinstance(item.get("temperature_distance_c"), (int, float))
    ]
    temp_medians = [
        item["t2m_median_c"]
        for item in temp_records
        if isinstance(item.get("t2m_median_c"), (int, float))
    ]
    dry_runs = [
        item["longest_dry_run_days"]
        for item in rain_records
        if isinstance(item.get("longest_dry_run_days"), int)
    ]
    growing_days = [
        item["growing_days"]
        for item in rain_records
        if isinstance(item.get("growing_days"), int)
    ]
    if not growing_days:
        growing_days = [
            item["growing_days"]
            for item in temp_records
            if isinstance(item.get("growing_days"), int)
        ]
    rain_totals = [
        item["rain_total_mm"]
        for item in rain_records
        if isinstance(item.get("rain_total_mm"), (int, float))
    ]
    heavy_days = sum(
        item["heavy_rain_days"]
        for item in rain_records
        if isinstance(item.get("heavy_rain_days"), int)
    )
    valid_days = sum(
        item["rain_valid_days"]
        for item in rain_records
        if isinstance(item.get("rain_valid_days"), int)
    )
    return {
        "crop_id": crop.get("crop_id"),
        "position": crop.get("position"),
        "seasons": len(set(temperature_seasons) | set(rain_seasons)),
        "temperature_seasons": len(temperature_seasons),
        "rain_seasons": len(rain_seasons),
        "temperature": {
            "median_distance_c": statistics.median(temperatures) if temperatures else None,
            "median_t2m_c": statistics.median(temp_medians) if temp_medians else None,
            "within_optimum_fraction": _fraction(
                sum(1 for item in temp_records if item.get("temperature_within_optimum")),
                len(temp_records),
            ),
            "within_tolerance_fraction": _fraction(
                sum(1 for item in temp_records if item.get("temperature_within_tolerance")),
                len(temp_records),
            ),
            "optimum_range": crop.get("temperature_range", {}).get("optimum"),
            "tolerance_range": crop.get("temperature_range", {}).get("tolerance"),
        },
        "dry_spell": {
            "median_longest_run_days": statistics.median(dry_runs) if dry_runs else None,
            "min_longest_run_days": min(dry_runs) if dry_runs else None,
            "max_longest_run_days": max(dry_runs) if dry_runs else None,
            "median_growing_days": statistics.median(growing_days) if growing_days else None,
        },
        "heavy_rain": {
            "days": heavy_days if rain_records else None,
            "valid_days": valid_days if rain_records else None,
            "frequency": _fraction(heavy_days, valid_days) if rain_records else None,
        },
        "rainfall": {
            "median_total_mm": statistics.median(rain_totals) if rain_totals else None,
            "iqr_total_mm": _iqr(rain_totals),
            "min_total_mm": min(rain_totals) if rain_totals else None,
            "max_total_mm": max(rain_totals) if rain_totals else None,
        },
    }


def _branch_summary(crops: list[dict]) -> dict:
    def average(values):
        clean = [value for value in values if isinstance(value, (int, float))]
        return sum(clean) / len(clean) if len(clean) == len(values) and clean else None

    return {
        "temperature_distance_c": average(
            [crop["temperature"]["median_distance_c"] for crop in crops]
        ),
        "dry_spell_days": average(
            [crop["dry_spell"]["median_longest_run_days"] for crop in crops]
        ),
        "heavy_rain_frequency": average(
            [crop["heavy_rain"]["frequency"] for crop in crops]
        ),
        "rainfall_median_mm": average(
            [crop["rainfall"]["median_total_mm"] for crop in crops]
        ),
        "growing_days_median": average(
            [crop["dry_spell"]["median_growing_days"] for crop in crops]
        ),
    }


def _temperature_range(profile: dict) -> dict:
    opt_min = _number(profile.get("temp_opt_min_c"))
    opt_max = _number(profile.get("temp_opt_max_c"))
    tol_min = _number(profile.get("temp_tol_min_c"))
    tol_max = _number(profile.get("temp_tol_max_c"))
    optimum = (
        {"min": opt_min, "max": opt_max}
        if opt_min is not None and opt_max is not None and opt_min <= opt_max
        else None
    )
    tolerance = (
        {"min": tol_min, "max": tol_max}
        if tol_min is not None and tol_max is not None and tol_min <= tol_max
        else None
    )
    return {
        "optimum_min": optimum["min"] if optimum else None,
        "optimum_max": optimum["max"] if optimum else None,
        "tolerance_min": tolerance["min"] if tolerance else None,
        "tolerance_max": tolerance["max"] if tolerance else None,
        "optimum": optimum,
        "tolerance": tolerance,
    }


def _temperature_distance(value: float, info: dict) -> float | None:
    low = info.get("optimum_min")
    high = info.get("optimum_max")
    if low is None or high is None:
        return None
    if value < low:
        return low - value
    if value > high:
        return value - high
    return 0.0


def _daily_values(
    observations: dict, start: dt.date, end: dt.date, variable: str
) -> list[float] | None:
    values = []
    current = start
    while current <= end:
        record = observations.get(current.isoformat())
        if not isinstance(record, dict):
            return None
        value = _number(record.get(variable))
        if value is None:
            return None
        values.append(value)
        current += dt.timedelta(days=1)
    return values


def _date(value: object) -> dt.date | None:
    if isinstance(value, str):
        try:
            return dt.date.fromisoformat(value)
        except ValueError:
            return None
    return None


def _number(value: object) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    number = float(value)
    return number if math.isfinite(number) else None


def _fraction(numerator: int, denominator: int) -> float | None:
    if denominator <= 0:
        return None
    return numerator / denominator


def _iqr(values: list[float]) -> float | None:
    if len(values) < 2:
        return None
    ordered = sorted(values)
    return _quantile(ordered, 0.75) - _quantile(ordered, 0.25)


def _quantile(values: list[float], fraction: float) -> float:
    position = (len(values) - 1) * fraction
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return values[lower]
    weight = position - lower
    return values[lower] * (1 - weight) + values[upper] * weight
