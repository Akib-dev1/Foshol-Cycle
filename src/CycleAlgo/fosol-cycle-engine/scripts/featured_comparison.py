#!/usr/bin/env python3
"""Generate the offline three-example Rajshahi comparison from the engine cache.

Every displayed weather value comes from ``src.explore.explore``. This script
does not score branches; it only selects three known sequences, preserves the
engine's separate candidate/conditional groups, and records provenance.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.climate_metrics import branch_common_seasons, evaluate_climate
from src.crop_profiles import load_crop_profiles
from src.explore import explore
from src.server import DEFAULT_CONFIG, load_server_power

DATA = ROOT.parent / "Data" / "fosol_cycle_rajshahi_crop_dataset.csv"
OUTPUT = ROOT / "examples" / "featured_comparison.json"
START_DATE = "2026-11-06"
WATER_ACCESS = "unknown"
NOW = dt.datetime.now(dt.timezone.utc)

VIEWS = (
    "closest_temperature_match",
    "least_dry_spell_exposure",
    "least_heavy_rain_exposure",
)
VIEW_LABELS = {
    "closest_temperature_match": "Temperature match",
    "least_dry_spell_exposure": "Dry-spell exposure",
    "least_heavy_rain_exposure": "Heavy-rain exposure",
}
VIEW_DIRECTIONS = {
    "closest_temperature_match": "lower is closer to the general EcoCrop optimum range",
    "least_dry_spell_exposure": "lower is less dry-spell exposure in this view",
    "least_heavy_rain_exposure": "lower is less heavy-rain exposure in this view",
}
VIEW_CONFIG = {
    "closest_temperature_match": {
        "climate_view": "temperature",
        "metric_key": "temperature_distance_c",
        "unit": "C",
    },
    "least_dry_spell_exposure": {
        "climate_view": "rain",
        "metric_key": "dry_spell_days",
        "unit": "days",
    },
    "least_heavy_rain_exposure": {
        "climate_view": "rain",
        "metric_key": "heavy_rain_frequency",
        "unit": "heavy days per valid growing day",
    },
}
ORDERING_BASIS = (
    "higher exposure of the two completion-optimized schedules; "
    "not a worst-case bound over all possible schedules"
)

FEATURED = (
    {
        "key": "baseline",
        "label": "Mustard → Boro → T. Aman",
        "crop_ids": (
            "mustard_binasarisha9",
            "boro_brri_dhan28",
            "aman_br11",
        ),
        "documentation_status": "Locally documented existing Rajshahi sequence",
        "role": "baseline",
        "why_explore": (
            "Reference the locally documented pattern, not a universal practice. "
            "The BARC trial summary reports this pattern had the highest water use "
            "among the compared patterns, which is a reason to compare alternatives."
        ),
        "what_changes": "Reference sequence; no change from itself.",
        "must_confirm": [
            "Whether this regional pattern is actually used on the field and with which varieties.",
            "Field soil pH, texture, drainage, and salinity; local preparation time; irrigation source and schedule.",
            "The engine's reference varieties (Binasarisha-9, BRRI dhan28, BR11) are not the survey's varieties.",
        ],
        "sources": [
            {
                "label": "Rashid et al. (2018), Cropping Systems and Land Use Pattern in Rajshahi Region",
                "url": "https://www.banglajol.info/index.php/BRJ/article/view/38209",
                "supports": (
                    "A 2014-15 survey of Rajshahi region reports Mustard-Boro-T. Aman "
                    "as the 4th dominant cropping pattern (Bangladesh Rice Journal 21(2):237-254)."
                ),
                "limitations": (
                    "Region-level survey, not a field prescription or variety trial. "
                    "The engine's reference varieties are not necessarily the surveyed varieties."
                ),
            },
            {
                "label": "BARC ARMIS research summary 38215",
                "url": "https://apps.barc.gov.bd/armis/home/research/detail/38215",
                "supports": (
                    "The 2014-16 water-management trial summary includes Mustard-Boro-T. Aman "
                    "and reports it had the highest water use among the compared patterns."
                ),
                "limitations": (
                    "Multi-location trial, not a Rajshahi-only test of this sequence; "
                    "it is not yield, income, or irrigation-demand validation for this field."
                ),
            },
        ],
    },
    {
        "key": "mung",
        "label": "Mustard → Mung → T. Aman",
        "crop_ids": (
            "mustard_binasarisha9",
            "mung_bari_mung6_kharif1",
            "aman_br11",
        ),
        "documentation_status": "Documented pattern outside Rajshahi; exploratory here",
        "role": "alternative",
        "why_explore": (
            "BARC's saline-prone-area trial reports the lowest total water use for "
            "Mustard-Mung-T. Aman and lists the Khulna version with BARI Sarisha 14, "
            "BARI Mung 6, and BINAdhan 7. It adds a legume and removes Boro, but it "
            "is not a Rajshahi-specific rotation."
        ),
        "what_changes": "Replaces Boro with mung; adds Fabaceae and a legume; completion range is unchanged in this run.",
        "must_confirm": [
            "Whether the Khulna mung calendar transfers to this Rajshahi field; the crop data flags the exact mung window as medium-transferability.",
            "Field soil pH, texture, drainage, and salinity; local preparation time; irrigation source and schedule.",
            "Mung variety, market access, and whether the short window is practical after mustard.",
            "The BARC water result is from a saline-prone-area trial, not this field or Rajshahi.",
        ],
        "sources": [
            {
                "label": "BARC ARMIS research summary 38215",
                "url": "https://apps.barc.gov.bd/armis/home/research/detail/38215",
                "supports": (
                    "Reports lowest total water use for Mustard-Mung-T. Aman and lists "
                    "the Khulna pattern: BARI Sarisha 14, BARI Mung 6, BINAdhan 7."
                ),
                "limitations": (
                    "The low-water result is from a saline-prone-area trial, not a "
                    "Rajshahi trial; the listed varieties differ from the engine's references."
                ),
            },
            {
                "label": "BAMIS Rajshahi mung calendar",
                "url": "https://www.bamis.gov.bd/en/calendar/1/86/2/",
                "supports": "Local calendar source used by the crop dataset for mung.",
                "limitations": "The crop dataset says the exact mung window has medium transferability; it is not Rajshahi-exact evidence.",
            },
            {
                "label": "PLOS Climate mung study",
                "url": "https://journals.plos.org/climate/article?id=10.1371/journal.pclm.0000180",
                "supports": "Planting-window reference cited by the crop dataset.",
                "limitations": "Study geography and variety must be checked against this field; it is not a local validation.",
            },
        ],
    },
    {
        "key": "wheat",
        "label": "Wheat → Mung → T. Aman",
        "crop_ids": (
            "wheat_bari_gom33",
            "mung_bari_mung6_kharif1",
            "aman_br11",
        ),
        "documentation_status": "Documented Kushtia sequence explored under Rajshahi weather; local applicability unverified",
        "role": "alternative",
        "why_explore": (
            "A documented Kushtia sequence explored under Rajshahi weather and the engine's "
            "reference crop profiles; local applicability is unverified. It adds a legume "
            "and a locally supported wheat row. Related Rajshahi evidence documents "
            "Wheat-Mung-T. Aus, but that is not a validation of this sequence."
        ),
        "what_changes": "Replaces mustard and Boro with wheat and mung; starts 9 days later; adds a legume; keeps two crop families.",
        "must_confirm": [
            "Whether the documented Kushtia sequence and its local applicability transfer to this Rajshahi field.",
            "Field soil pH, texture, drainage, and salinity; local preparation time; irrigation source and schedule.",
            "Wheat and mung varieties, planting windows, and market access.",
            "Related Rajshahi evidence uses T. Aus; it is not a validation of this Wheat-Mung-Aman sequence.",
            "This is not a researched Rajshahi rotation merely because the engine can generate it.",
        ],
        "sources": [
            {
                "label": "BARC ARMIS research summary 38215",
                "url": "https://apps.barc.gov.bd/armis/home/research/detail/38215",
                "supports": (
                    "Directly documents Wheat-Mung-T. Aman in Kushtia and separately lists "
                    "Wheat-Mung-T. Aus for Rajshahi as related evidence."
                ),
                "limitations": (
                    "The Kushtia pattern is not a Rajshahi validation. Rajshahi's documented "
                    "wheat-mung pattern uses T. Aus; that is related evidence, not a validation "
                    "of the featured sequence."
                ),
            },
            {
                "label": "BAMIS Rajshahi wheat calendar",
                "url": "https://www.bamis.gov.bd/en/calendar/1/9/2/",
                "supports": "Local calendar source used by the crop dataset for wheat.",
                "limitations": "Calendar guidance, not a field prescription or variety trial.",
            },
            {
                "label": "BWMRI wheat variety source",
                "url": "https://bwmri.gov.bd/pages/static-pages/6922e0b6933eb65569e28480",
                "supports": "Reference source cited for the engine's BARI Gom-33 profile.",
                "limitations": "Variety guidance; not a validation of this three-crop sequence.",
            },
        ],
    },
)

CONTROLS = (
    {
        "id": "fastest_completion",
        "label": "Fastest completion",
        "enabled": True,
        "reason": None,
    },
    {
        "id": "more_crop_diversity",
        "label": "More crop diversity",
        "enabled": True,
        "reason": None,
    },
    {
        "id": "closest_temperature_match",
        "label": "Closest temperature match",
        "enabled": True,
        "reason": None,
    },
    {
        "id": "least_dry_spell_exposure",
        "label": "Least dry-spell exposure",
        "enabled": True,
        "reason": None,
    },
    {
        "id": "least_heavy_rain_exposure",
        "label": "Least heavy-rain exposure",
        "enabled": True,
        "reason": None,
    },
    {
        "id": "lowest_total_cost",
        "label": "Lowest total cost",
        "enabled": False,
        "reason": "Disabled: no sourced production-cost, price, cash-flow, or validated-yield evidence.",
    },
    {
        "id": "highest_net_return",
        "label": "Highest net return",
        "enabled": False,
        "reason": "Disabled: economics are unavailable; reference yields are context only.",
    },
    {
        "id": "lowest_upfront_cash",
        "label": "Lowest upfront cash",
        "enabled": False,
        "reason": "Disabled: no sourced cash-flow schedule or production costs.",
    },
    {
        "id": "least_irrigation_dependence",
        "label": "Least irrigation dependence",
        "enabled": False,
        "reason": "Disabled: irrigation guidance is context only; no comparable irrigation-dependence evidence exists.",
    },
)

GLOSSARY = {
    "conditional": "A path that remains inspectable while field evidence is missing; it is not a recommendation.",
    "common_season": "A historical season with complete daily data for every crop in both completion-optimized schedules.",
    "T2M": "NASA POWER daily temperature at 2 m, required in Celsius.",
    "PRECTOTCORR": "NASA POWER corrected daily precipitation, required in mm/day.",
    "dry_day": "A day with PRECTOTCORR below 1 mm/day.",
    "heavy_day": "A day with PRECTOTCORR at or above 20 mm/day (R20mm adaptation).",
    "completion_schedule": "A min-realization or max-realization example optimized for completion; not a weather-optimized or worst-case schedule.",
    "equal_crop_weighting": "Each crop contributes equally to the branch weather value; a disclosed convention, not duration neutrality.",
    "tie": "Examples with the same displayed value; ties are kept, not forced apart.",
}


def _format(value: object, digits: int) -> str:
    if value is None:
        return "unavailable"
    if isinstance(value, float):
        text = f"{value:.{digits}f}".rstrip("0").rstrip(".")
        return text or "0"
    return str(value)


def _find_branch(result: dict, crop_ids: tuple[str, ...]) -> dict:
    for branch in result["branches"]:
        if tuple(crop["crop_id"] for crop in branch["crops"]) == crop_ids:
            return branch
    raise RuntimeError(f"featured branch not generated: {crop_ids}")


def _trim_check(check: object) -> object:
    if not isinstance(check, dict):
        return check
    return {
        key: check.get(key)
        for key in ("status", "code", "reason", "source_ids")
        if key in check
    }


def _trim_crop_weather(crop: dict) -> dict:
    return {
        "crop_id": crop.get("crop_id"),
        "position": crop.get("position"),
        "seasons": crop.get("seasons"),
        "temperature_seasons": crop.get("temperature_seasons"),
        "rain_seasons": crop.get("rain_seasons"),
        "temperature": crop.get("temperature"),
        "dry_spell": crop.get("dry_spell"),
        "heavy_rain": crop.get("heavy_rain"),
        "rainfall": crop.get("rainfall"),
    }


def _common_periods(branches: dict[str, dict]) -> dict[str, dict]:
    """Intersect complete seasons across featured examples, independently per view."""
    periods = {}
    for view in VIEWS:
        climate_view = VIEW_CONFIG[view]["climate_view"]
        season_sets = []
        reasons = []
        statuses_ok = True
        for branch in branches.values():
            climate = branch.get("metrics", {}).get("climate", {})
            status = (climate.get("views") or {}).get(climate_view, {})
            if status.get("status") != "ok":
                statuses_ok = False
                if status.get("reason"):
                    reasons.append(status["reason"])
            season_sets.append(branch_common_seasons(climate, climate_view))
        common = set.intersection(*season_sets) if season_sets else set()
        if common and statuses_ok:
            reason = None
        elif reasons:
            reason = "; ".join(dict.fromkeys(reasons))
        else:
            reason = (
                f"NO_COMMON_SEASONS: no complete {climate_view} seasons are "
                "shared by all featured examples."
            )
        periods[view] = {
            "available": bool(common) and statuses_ok,
            "seasons": sorted(common),
            "reason": reason,
        }
    return periods


def _unavailable_weather_view(view: str, climate: dict, reason: str | None) -> dict:
    config = VIEW_CONFIG[view]
    climate_view = config["climate_view"]
    status = (climate.get("views") or {}).get(climate_view, {})
    if not reason and isinstance(status, dict):
        reason = status.get("reason")
    reason = reason or f"NO_COMMON_SEASONS: {climate_view} view unavailable."
    return {
        "status": "unavailable",
        "reason": reason,
        "metric": config["metric_key"],
        "unit": config["unit"],
        "value": None,
        "schedule_values": {"min_realization": None, "max_realization": None},
        "ordering_basis": ORDERING_BASIS,
        "common_seasons": [],
        "common_seasons_count": 0,
        "is_tie": False,
        "tie_count": 0,
        "direction": VIEW_DIRECTIONS[view],
        "view_status": status,
        "source": "evaluate_climate on cross-example common seasons",
        "per_schedule": {},
    }


def _weather_view(climate: dict, view: str, common_seasons: list[int], reason: str | None) -> dict:
    """Evaluate one view over exactly the supplied common seasons.

    ``evaluate_climate`` supplies the headline, schedule values, per-crop details,
    and season list from one calculation. Unavailable views keep null values.
    """
    if not common_seasons:
        return _unavailable_weather_view(view, climate, reason)
    result = evaluate_climate(climate, set(common_seasons), view)
    if result is None or result.get("value") is None:
        return _unavailable_weather_view(
            view,
            climate,
            reason or "ENGINE_EVALUATION_UNAVAILABLE: engine could not evaluate this view.",
        )
    per_schedule = {}
    for schedule, summary in result.get("schedule_summaries", {}).items():
        per_schedule[schedule] = {
            "status": summary.get("status"),
            "seasons": summary.get("seasons"),
            "temperature_seasons": summary.get("temperature_seasons"),
            "rain_seasons": summary.get("rain_seasons"),
            "per_crop": [
                _trim_crop_weather(crop) for crop in summary.get("per_crop", [])
            ],
        }
    return {
        "status": "ok",
        "reason": None,
        "metric": result.get("metric"),
        "unit": result.get("unit"),
        "value": result.get("value"),
        "schedule_values": result.get("schedule_values"),
        "ordering_basis": result.get("ordering_basis"),
        "common_seasons": result.get("common_seasons", []),
        "common_seasons_count": len(result.get("common_seasons") or []),
        "is_tie": False,
        "tie_count": 0,
        "direction": VIEW_DIRECTIONS[view],
        "view_status": (climate.get("views") or {}).get(
            VIEW_CONFIG[view]["climate_view"], {}
        ),
        "source": "evaluate_climate on cross-example common seasons",
        "per_schedule": per_schedule,
    }


def _what_nasa_shows(view_data: dict) -> dict:
    temperature = view_data["closest_temperature_match"]
    dry = view_data["least_dry_spell_exposure"]
    heavy = view_data["least_heavy_rain_exposure"]
    if temperature.get("value") is None:
        temperature_text = (
            "Unavailable: "
            + (temperature.get("reason") or "no common temperature seasons.")
        )
    else:
        temperature_text = (
            f"{temperature['value']:.1f} °C median distance; 0 means the seasonal "
            "median is inside the general EcoCrop optimum range. Ties are shown as "
            "exact ties; 0 is not proof of no heat stress."
        )
    dry_text = (
        "Unavailable: " + (dry.get("reason") or "no common rain seasons.")
        if dry.get("value") is None
        else f"{_format(dry['value'], 2)} days "
        "(higher-exposure schedule; one separate view)."
    )
    heavy_text = (
        "Unavailable: " + (heavy.get("reason") or "no common rain seasons.")
        if heavy.get("value") is None
        else f"{_format(heavy['value'], 5)} heavy days per valid growing day "
        "(higher-exposure schedule; one separate view)."
    )
    if dry.get("value") is None and heavy.get("value") is None:
        rainfall_text = (
            "Rainfall context unavailable for this featured view; no zero-fill was used."
        )
    else:
        rainfall_text = (
            "Per-crop period medians and IQRs are in weather_views. They are not summed "
            "across unequal crop periods and do not imply irrigation demand."
        )
    return {
        "temperature": temperature_text,
        "dry_spell": dry_text,
        "heavy_rain": heavy_text,
        "rainfall": rainfall_text,
    }


def _comparison_controls(availability: dict[str, dict]) -> list[dict]:
    controls = [dict(item) for item in CONTROLS]
    for view in VIEWS:
        info = availability.get(view, {})
        if info.get("available"):
            continue
        for control in controls:
            if control["id"] == view:
                control["enabled"] = False
                control["reason"] = (
                    "Disabled: " + (info.get("reason") or "view unavailable.")
                )
    return controls


def _crop_node(crop: dict) -> dict:
    checks = crop.get("checks") or {}
    return {
        "position": crop.get("position"),
        "crop_id": crop.get("crop_id"),
        "name_en": crop.get("name_en"),
        "name_bn": crop.get("name_bn"),
        "family": crop.get("family"),
        "is_legume": crop.get("is_legume", crop.get("family") == "Fabaceae"),
        "reference_variety": crop.get("reference_variety"),
        "establishment_method": crop.get("establishment_method"),
        "status": crop.get("status"),
        "planting_range": crop.get("planting_range"),
        "harvest_range": crop.get("harvest_range"),
        "preparation_range": crop.get("preparation_range"),
        "preparation_known": crop.get("preparation_range") is not None,
        "duration": crop.get("duration"),
        "timing_status": crop.get("timing_status"),
        "checks": {name: _trim_check(value) for name, value in checks.items()},
        "missing_evidence": crop.get("missing_evidence", []),
    }


def _transition_node(transition: dict) -> dict:
    return {
        "from_position": transition.get("from_position"),
        "to_position": transition.get("to_position"),
        "from_crop_id": transition.get("from_crop_id"),
        "to_crop_id": transition.get("to_crop_id"),
        "next_planting_range": transition.get("next_planting_range"),
        "preparation_range": transition.get("preparation_range"),
        "preparation_known": transition.get("preparation_known"),
        "waiting_range": transition.get("waiting_range"),
        "total_interval_range_days": transition.get("total_interval_range_days"),
        "harvest_to_next_window_days": transition.get("harvest_to_next_window_days"),
        "window_only_gap": transition.get("window_only_gap"),
        "waiting_limit_status": transition.get("waiting_limit_status"),
        "latest_invalid": transition.get("latest_invalid"),
    }


def _completion_metrics(branch: dict) -> dict:
    completion = branch.get("metrics", {}).get("completion", {})
    return {
        key: completion.get(key)
        for key in (
            "status",
            "completion_days",
            "earliest_completion_date",
            "latest_completion_date",
            "ranking_value_days",
            "basis",
            "range_basis",
            "range_overlap_note",
            "min_realization",
            "max_realization",
            "missing_evidence",
            "enumeration_used",
        )
    }


def _prerequisites(branch: dict) -> dict:
    resources = branch.get("metrics", {}).get("resources", {})
    economics = branch.get("metrics", {}).get("economics", {})
    irrigation = resources.get("irrigation", {})
    return {
        "soil": "unknown; no local district pH, texture, drainage, or salinity measurement was supplied.",
        "preparation": "unknown; preparation ranges are null, so field-ready waiting is not calculated.",
        "drainage": "unknown; no field drainage or waterlogging evidence was supplied.",
        "irrigation": {
            "status": irrigation.get("status"),
            "ranking_status": irrigation.get("ranking_status"),
            "per_crop": irrigation.get("per_crop", []),
            "total": irrigation.get("total"),
            "reason": irrigation.get("reason"),
            "missing_evidence": irrigation.get("missing_evidence", []),
        },
        "labor": resources.get("labor"),
        "equipment": resources.get("equipment"),
        "cash_cost": resources.get("cash_cost"),
        "market": {
            "status": "unavailable",
            "reason": "No farm-gate price value; market price mode is dynamic external.",
            "price_evidence": economics.get("price_evidence"),
        },
        "economics": {
            "status": economics.get("status"),
            "reason": economics.get("reason"),
            "missing_evidence": economics.get("missing_evidence", []),
            "yield_reference_context": economics.get("yield_reference_context", []),
        },
    }


def _diversity(branch: dict) -> dict:
    diversity = branch.get("metrics", {}).get("diversity", {})
    return {
        "status": diversity.get("status"),
        "distinct_family_count": diversity.get("distinct_family_count"),
        "families": diversity.get("families", []),
        "family_repeat_count": diversity.get("family_repeat_count"),
        "legume_present": diversity.get("legume_present"),
        "legume_crop_ids": diversity.get("legume_crop_ids", []),
        "note": diversity.get("diversity_note")
        or "Family count is a product convention, not a measured soil-health ranking.",
    }


def _power_environment(result: dict) -> dict:
    source = next(
        (item for item in result.get("data_sources", []) if item.get("source_id") == "nasa_power_daily"),
        None,
    )
    if not source:
        raise RuntimeError("NASA POWER source metadata is missing from the engine response")
    cache = source.get("cache") or {}
    stale = bool(cache.get("stale"))
    return {
        "source_id": "nasa_power_daily",
        "provider": source.get("provider"),
        "product": source.get("product"),
        "version": source.get("version"),
        "observation_start": source.get("observation_start"),
        "observation_end": source.get("observation_end"),
        "retrieved_at": source.get("retrieved_at"),
        "temporal_resolution": source.get("temporal_resolution"),
        "spatial_resolution": source.get("spatial_resolution"),
        "is_forecast": source.get("is_forecast"),
        "cache": {
            "hit": cache.get("hit"),
            "stale": stale,
            "status": "stale" if stale else ("fresh" if cache.get("hit") else "uncached"),
        },
        "data_mode": "offline_api_cache",
        "live_fetch": False,
        "offline_fixture": False,
        "note": (
            "Generated with allow_network=False from the local NASA POWER API cache. "
            "The 2000-2025 local POWER CSV used by scripts/demo_check.py is a separate offline fixture."
        ),
        "warnings": source.get("warnings", []),
    }


def _explore_results(profiles: dict, environment: dict, now: dt.datetime) -> dict:
    """One engine call per first crop; branch summaries retain all three views."""
    results = {}
    for first_crop in sorted({item["crop_ids"][0] for item in FEATURED}):
        payload = {
            "district_id": "rajshahi",
            "start_date": START_DATE,
            "first_crop_id": first_crop,
            "water_access": WATER_ACCESS,
            "preference": "least_dry_spell_exposure",
        }
        results[first_crop] = explore(
            payload,
            profiles=profiles,
            config=DEFAULT_CONFIG,
            environment=environment,
            now=now,
            retain_climate_raw=True,
        )
    return results


def build_featured_comparison(
    *, now: dt.datetime | None = None, cache_dir: str | Path | None = None
) -> dict:
    moment = now or NOW
    profiles = load_crop_profiles(DATA)
    try:
        environment = load_server_power(
            cache_dir=cache_dir,
            allow_network=False,
            now=moment,
        )
    except Exception as exc:  # noqa: BLE001 - surfaced as a clear offline-generation error
        raise RuntimeError(
            "NASA POWER cache is unavailable. Populate the 1991-2025 server cache first; "
            "this generator never falls back to a different data source."
        ) from exc
    if not environment.get("observations"):
        raise RuntimeError(
            "NASA POWER observations are unavailable. Populate the 1991-2025 server cache first; "
            "this generator never falls back to a different data source."
        )

    results = _explore_results(profiles, environment, moment)
    baseline_ids = FEATURED[0]["crop_ids"]
    branches = {
        item["key"]: _find_branch(results[item["crop_ids"][0]], item["crop_ids"])
        for item in FEATURED
    }
    baseline_branch = branches["baseline"]
    periods = _common_periods(branches)

    examples = []
    for item in FEATURED:
        branch = branches[item["key"]]
        view_data = {
            view: _weather_view(
                branch["metrics"]["climate"],
                view,
                periods[view]["seasons"],
                periods[view]["reason"],
            )
            for view in VIEWS
        }
        completion = _completion_metrics(branch)
        diversity = _diversity(branch)
        baseline_completion = baseline_branch["metrics"]["completion"]["ranking_value_days"]
        completion_max = completion.get("ranking_value_days")
        baseline_wait = baseline_branch.get("initial_wait_days")
        changes = {
            "summary": item["what_changes"],
            "removed_crop_ids": [
                crop_id for crop_id in baseline_ids if crop_id not in item["crop_ids"]
            ],
            "added_crop_ids": [
                crop_id for crop_id in item["crop_ids"] if crop_id not in baseline_ids
            ],
            "family_count_delta": (
                diversity["distinct_family_count"]
                - _diversity(baseline_branch)["distinct_family_count"]
            ),
            "legume_change": (
                "absent_to_present"
                if diversity["legume_present"] and not _diversity(baseline_branch)["legume_present"]
                else "unchanged"
            ),
            "initial_wait_delta_days": (
                branch.get("initial_wait_days") - baseline_wait
                if branch.get("initial_wait_days") is not None and baseline_wait is not None
                else None
            ),
            "completion_max_delta_days": (
                completion_max - baseline_completion
                if completion_max is not None and baseline_completion is not None
                else None
            ),
        }
        example = {
            "key": item["key"],
            "label": item["label"],
            "sequence": [crop["name_en"] for crop in branch["crops"]],
            "crop_ids": list(item["crop_ids"]),
            "branch_id": branch["branch_id"],
            "status": branch["status"],
            "documentation_status": item["documentation_status"],
            "role": item["role"],
            "initial_wait_days": branch.get("initial_wait_days"),
            "completion": completion,
            "crops": [_crop_node(crop) for crop in branch["crops"]],
            "transitions": [_transition_node(transition) for transition in branch["transitions"]],
            "diversity": diversity,
            "weather_views": view_data,
            "prerequisites": _prerequisites(branch),
            "unit_validation": branch.get("metrics", {}).get(
                "climate", {}
            ).get("unit_validation", {}),
            "temperature_provenance": branch.get("metrics", {}).get(
                "climate", {}
            ).get("temperature_provenance", {}),
            "cautions": branch.get("cautions", []),
            "missing_evidence": branch.get("missing_evidence", []),
            "what_changes_from_baseline": changes,
            "why_explore": item["why_explore"],
            "must_confirm": item["must_confirm"],
            "sources": item["sources"],
        }
        example["what_nasa_shows"] = _what_nasa_shows(view_data)
        example["does_not_establish"] = (
            "Weather exposure is not overall agricultural suitability. These results do not "
            "establish yield, income, crop damage, field flooding, irrigation demand, or a "
            "repeatable rotation; third-to-first compatibility is not checked."
        )
        examples.append(example)

    # Mark only exact ties among available displayed values. Unavailable views
    # keep null values and are not converted into ties or zeros.
    for view in VIEWS:
        values = [example["weather_views"][view]["value"] for example in examples]
        available_values = [value for value in values if value is not None]
        for example in examples:
            value = example["weather_views"][view]["value"]
            count = available_values.count(value) if value is not None else 0
            example["weather_views"][view]["is_tie"] = count > 1
            example["weather_views"][view]["tie_count"] = count

    temperature_values = [
        example["weather_views"]["closest_temperature_match"]["value"]
        for example in examples
    ]
    temperature_available = all(value is not None for value in temperature_values)
    temperature_tie = (
        temperature_available
        and len(set(temperature_values)) == 1
        and len(temperature_values) > 1
    )
    for example in examples:
        if temperature_available:
            note = (
                " The three featured values are an exact tie."
                if temperature_tie
                else " The three featured values are not all tied; no tie is forced."
            )
        else:
            note = " Not all temperature values are available; no tie is forced."
        example["what_nasa_shows"]["temperature"] += note

    availability = {}
    for view in VIEWS:
        unavailable_reasons = [
            example["weather_views"][view].get("reason")
            for example in examples
            if example["weather_views"][view].get("status") != "ok"
            or example["weather_views"][view].get("value") is None
        ]
        available = not unavailable_reasons
        availability[view] = {
            "available": available,
            "status": "ok" if available else "unavailable",
            "reason": (
                None
                if available
                else (
                    unavailable_reasons[0]
                    or periods[view].get("reason")
                    or "View unavailable."
                )
            ),
            "common_seasons_count": len(periods[view]["seasons"]) if available else 0,
        }

    first_crop_counts = {}
    for first_crop in sorted({item["crop_ids"][0] for item in FEATURED}):
        result = results[first_crop]
        summary = result.get("branch_summary", {})
        first_crop_counts[first_crop] = {
            "candidate_count": summary.get("candidate_count"),
            "conditional_count": summary.get("conditional_count"),
            "excluded_count": summary.get("excluded_count"),
        }

    power = _power_environment(results[baseline_ids[0]])
    return {
        "schema_version": "1",
        "generated_at": moment.isoformat(),
        "data_mode": "offline_api_cache",
        "offline_fixture": False,
        "request": {
            "district_id": "rajshahi",
            "start_date": START_DATE,
            "water_access": WATER_ACCESS,
            "max_initial_wait_days": DEFAULT_CONFIG["max_initial_wait_days"],
            "max_waiting_days": DEFAULT_CONFIG["max_waiting_days"],
            "analysis_start_year": DEFAULT_CONFIG["analysis_start_year"],
            "analysis_end_year": DEFAULT_CONFIG["analysis_end_year"],
            "first_crop_ids": sorted({item["crop_ids"][0] for item in FEATURED}),
        },
        "environment": power,
        "temperature_source": {
            "source": "FAO EcoCrop database, OpenCLIM mirror EcoCrop_DB.csv",
            "url": "https://github.com/OpenCLIM/ecocrop/blob/main/EcoCrop_DB.csv",
            "status": "data mirror, not independent agronomic validation",
            "verified_species_entries": {
                "mustard_binasarisha9": {
                    "eco_port_code": "548",
                    "scientific_name": "Brassica juncea",
                },
                "boro_brri_dhan28": {
                    "eco_port_code": "1574",
                    "scientific_name": "Oryza sativa",
                },
                "mung_bari_mung6_kharif1": {
                    "eco_port_code": "2150",
                    "scientific_name": "Vigna radiata",
                },
                "wheat_bari_gom33": {
                    "eco_port_code": "2114",
                    "scientific_name": "Triticum aestivum",
                },
                "aman_br11": {
                    "eco_port_code": "1574",
                    "scientific_name": "Oryza sativa",
                },
            },
            "project_convention": (
                "Median daily T2M over the realized growing period is compared with the "
                "published species optimum range; distance is 0 inside the range. "
                "This is a project-defined seasonal match, not a damage threshold."
            ),
            "not_confirmed": [
                "Species-level EcoCrop ranges are not variety-specific Rajshahi validation.",
                "A 0 °C distance does not establish absence of heat stress or overall suitability.",
                "The mirror alone is not independent agronomic validation.",
            ],
        },
        "coverage_unit_check": {
            "temperature_and_rain_independent": True,
            "common_periods_computed_independently": True,
            "nonidentical_availability_allowed_with_nonempty_intersection": True,
            "unit_failure_scope": "A missing/incompatible unit disables only the affected temperature or rain view.",
            "note": "Each view reports its own complete-season list, status, and unit status; missing data is not zero-filled.",
        },
        "view_availability": availability,
        "common_seasons_by_view": {
            view: {
                "years": periods[view]["seasons"],
                "count": len(periods[view]["seasons"]),
                "status": availability[view]["status"],
                "reason": availability[view]["reason"],
            }
            for view in VIEWS
        },
        "comparison_controls": _comparison_controls(availability),
        "examples": examples,
        "exploratory_scope": {
            "description": (
                "The three featured examples are selected from engine-generated conditional paths; "
                "they are not a full ranking. The wider paths remain exploratory."
            ),
            "first_crop_counts": first_crop_counts,
            "featured_count": len(examples),
        },
        "no_overall_winner": True,
        "repeatable_rotation_checked": False,
        "assumptions": [
            "The same start date (2026-11-06) and water-access assumption (unknown) are used for every example.",
            "The two completion-optimized schedules are examples; ordering uses the higher exposure of the two, not a worst-case bound.",
            "Weather coverage is independent for temperature and rainfall. No missing value is zero-filled or joined across a gap.",
            "Each view uses its own cross-example common-season intersection. A view with no intersection is returned unavailable without disabling the other view.",
            "Candidate and conditional groups stay separate. All featured examples are conditional; none is a recommendation.",
            "No overall weighted score, winner badge, economics, irrigation-dependence score, or repeatable-rotation claim is produced.",
        ],
        "limitations": [
            "Historical POWER exposure is not a forecast, crop-damage rule, yield model, field measurement, or irrigation-demand calculation.",
            "Temperature uses species/crop-level EcoCrop guidance and a project-defined seasonal-median convention; it is not variety- or stage-specific validation.",
            "The baseline is a locally documented regional pattern, not a universal practice. The alternatives are documented outside Rajshahi and are not locally validated recommendations.",
            "Family count and legume presence are context only; they do not promise fertilizer savings, pest control, or soil improvement.",
            "Economics, labor, equipment, comparable irrigation dependence, field preparation, and local soil evidence remain unavailable or unknown.",
            "Third-to-first crop compatibility is not checked; a three-crop sequence is not presented as a repeatable rotation.",
        ],
        "glossary": GLOSSARY,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=OUTPUT,
        help=f"output JSON path (default: {OUTPUT})",
    )
    args = parser.parse_args()
    started = time.perf_counter()
    payload = build_featured_comparison()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    elapsed = time.perf_counter() - started
    print(f"Wrote {args.output} in {elapsed:.2f}s")
    print(
        "Featured: "
        + "; ".join(
            f"{item['label'].replace(chr(8594), '->')} [{item['branch_id']}]"
            for item in payload["examples"]
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
