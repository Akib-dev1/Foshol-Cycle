"""Load and normalize the local crop-profile CSV.

The CSV is the only crop-data source. Values are never defaulted: an empty
cell becomes ``None`` and is recorded in ``data_quality.missing_fields``. The
original row is preserved under ``"raw"``.
"""

from __future__ import annotations

import csv
import datetime as dt
import math
import re
from pathlib import Path

TEXT_FIELDS = (
    "name_en",
    "name_bn",
    "scientific_name",
    "family",
    "season_profile",
    "crop_role",
    "reference_variety",
    "establishment_method",
    "duration_precision",
    "decision_duration_source",
    "irrigation_guidance",
    "yield_basis",
    "market_price_mode",
    "rotation_family_rule",
    "rotation_note",
)

BOOL_FIELDS = (
    "is_legume_n_fixing",
    "window_crosses_year",
)

WINDOW_FIELDS = (
    "preferred_start_mmdd",
    "preferred_end_mmdd",
    "supported_late_end_mmdd",
)

INTEGER_FIELDS = (
    "variety_duration_min_days",
    "variety_duration_max_days",
    "seedling_age_min_days",
    "seedling_age_max_days",
    "turnaround_days_min",
    "turnaround_days_max",
)

NUMERIC_FIELDS = (
    "temp_opt_min_c",
    "temp_opt_max_c",
    "temp_tol_min_c",
    "temp_tol_max_c",
    "precip_opt_min_mm",
    "precip_opt_max_mm",
    "precip_tol_min_mm",
    "precip_tol_max_mm",
    "ph_opt_min",
    "ph_opt_max",
    "ph_tol_min",
    "ph_tol_max",
)

# (min field, max field) pairs checked for min > max after parsing.
MIN_MAX_PAIRS = (
    ("variety_duration_min_days", "variety_duration_max_days"),
    ("seedling_age_min_days", "seedling_age_max_days"),
    ("turnaround_days_min", "turnaround_days_max"),
    ("temp_opt_min_c", "temp_opt_max_c"),
    ("temp_tol_min_c", "temp_tol_max_c"),
    ("precip_opt_min_mm", "precip_opt_max_mm"),
    ("precip_tol_min_mm", "precip_tol_max_mm"),
    ("ph_opt_min", "ph_opt_max"),
    ("ph_tol_min", "ph_tol_max"),
)

NORMALIZED_FIELDS = (
    TEXT_FIELDS + BOOL_FIELDS + WINDOW_FIELDS + INTEGER_FIELDS + NUMERIC_FIELDS
)

_MMDD_RE = re.compile(r"^(\d{2})-(\d{2})$")
_LEAP_YEAR = 2024

# Normalized name -> CSV column, for the two columns whose names differ.
SOURCE_FIELDS = {
    "name_en": "crop_name_en",
    "name_bn": "crop_name_bn",
}


def _clean(value: object) -> str | None:
    """Strip a CSV cell; empty cells become None."""
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _parse_bool(text: str) -> bool | None:
    upper = text.upper()
    if upper == "TRUE":
        return True
    if upper == "FALSE":
        return False
    return None


def _parse_mmdd(text: str) -> str | None:
    """Return the MM-DD string only if it is a real leap-year date."""
    match = _MMDD_RE.fullmatch(text)
    if match is None:
        return None
    month, day = int(match.group(1)), int(match.group(2))
    try:
        dt.date(_LEAP_YEAR, month, day)
    except ValueError:
        return None
    return text


def _parse_integer(text: str) -> int | None:
    try:
        value = float(text)
    except ValueError:
        return None
    if not math.isfinite(value) or not value.is_integer():
        return None
    return int(value)


def _parse_number(text: str) -> float | None:
    try:
        value = float(text)
    except ValueError:
        return None
    if not math.isfinite(value):
        return None
    return value


def _normalize_row(row: dict[str, str], crop_id: str) -> dict:
    profile: dict = {"crop_id": crop_id}
    missing: list[str] = []
    unclear: list[str] = []
    notes: list[str] = []

    for field in NORMALIZED_FIELDS:
        text = _clean(row.get(SOURCE_FIELDS.get(field, field)))
        if text is None:
            profile[field] = None
            missing.append(field)
            continue

        if field in TEXT_FIELDS:
            profile[field] = text
        elif field in BOOL_FIELDS:
            value = _parse_bool(text)
            profile[field] = value
            if value is None:
                unclear.append(field)
        elif field in WINDOW_FIELDS:
            value = _parse_mmdd(text)
            profile[field] = value
            if value is None:
                unclear.append(field)
        elif field in INTEGER_FIELDS:
            value = _parse_integer(text)
            profile[field] = value
            if value is None:
                unclear.append(field)
        else:  # NUMERIC_FIELDS
            value = _parse_number(text)
            profile[field] = value
            if value is None:
                unclear.append(field)

    for min_field, max_field in MIN_MAX_PAIRS:
        low, high = profile[min_field], profile[max_field]
        if low is None or high is None or low <= high:
            continue
        profile[min_field] = None
        profile[max_field] = None
        for field in (min_field, max_field):
            if field not in unclear:
                unclear.append(field)
        notes.append(f"{min_field}/{max_field}: min>max")

    profile["data_quality"] = {
        "missing_fields": missing,
        "unclear_fields": unclear,
        "notes": notes,
    }
    profile["raw"] = dict(row)
    return profile


def load_crop_profiles(path: str | Path) -> dict[str, dict]:
    """Load crop profiles keyed by ``crop_id``.

    Raises ``ValueError`` for an empty file, a blank ``crop_id``, or a
    duplicate ``crop_id``.
    """
    with open(path, "r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))

    if not rows:
        raise ValueError("crop-profile CSV contains no rows")

    profiles: dict[str, dict] = {}
    for row in rows:
        crop_id = _clean(row.get("crop_id"))
        if crop_id is None:
            raise ValueError("crop-profile row has an empty crop_id")
        if crop_id in profiles:
            raise ValueError(f"duplicate crop_id: {crop_id}")
        profiles[crop_id] = _normalize_row(row, crop_id)
    return profiles
