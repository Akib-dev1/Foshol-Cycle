"""Seasonal outlook label and warning definitions (v1.md §6.2, §9.3, §14.4)."""

from __future__ import annotations

OUTLOOK_LABEL = (
    "Seasonal outlook — based on historical conditions, not a weather forecast."
)

_WEATHER_RISK_THRESHOLD_TEXT = (
    "Weather warnings usually create cautions. Hard rejection requires a "
    "documented rule appropriate to the variable, crop, stage, location, and "
    "time scale."
)

WARNING_DEFINITIONS = {
    "wheat_tmax_gt_30c": {
        "id": "wheat_tmax_gt_30c",
        "enabled": False,
        "variable": "T2M_MAX",
        "comparison": "gt",
        "threshold": 30.0,
        "unit": "C",
        "indicator_text": (
            "Heat exposure: at least one day with T2M_MAX above 30.0 C in an "
            "evaluated historical season."
        ),
        "weather_risk_threshold_text": _WEATHER_RISK_THRESHOLD_TEXT,
    },
    "wheat_tmin_lt_15c": {
        "id": "wheat_tmin_lt_15c",
        "enabled": False,
        "variable": "T2M_MIN",
        "comparison": "lt",
        "threshold": 15.0,
        "unit": "C",
        "indicator_text": (
            "Low-temperature exposure: at least one day with T2M_MIN below "
            "15.0 C in an evaluated historical season."
        ),
        "weather_risk_threshold_text": _WEATHER_RISK_THRESHOLD_TEXT,
    },
    "mustard_precip_gt_50mm": {
        "id": "mustard_precip_gt_50mm",
        "enabled": False,
        "variable": "PRECTOTCORR",
        "comparison": "gt",
        "threshold": 50.0,
        "unit": "mm/day",
        "indicator_text": (
            "Heavy-rain exposure: at least one day with PRECTOTCORR above "
            "50.0 mm/day in an evaluated historical season."
        ),
        "weather_risk_threshold_text": _WEATHER_RISK_THRESHOLD_TEXT,
    },
}
