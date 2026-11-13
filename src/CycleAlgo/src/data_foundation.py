"""Load Fosol-Cycle research data without inventing missing agricultural evidence."""

import argparse
import calendar
import csv
import hashlib
import io
import json
import math
import re
from datetime import date, timedelta
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CROPS = ROOT / "Data/fosol_cycle_rajshahi_crop_dataset.csv"
DEFAULT_CLIMATE = ROOT / "Data/POWER_Point_Daily_19900101_20261023_024d38N_088d60E_LST.csv"

# This exact download has a sampled 24x rainfall discrepancy against NASA's API.
# Preserve its source values, but do not publish them as usable precipitation.
QUARANTINED_RAINFALL_SHA256 = "22cfb654a4ab8a2a12d7d4a4a97a088e375673539364b015d6b51110f71d9e42"
BORO_DURATION_SOURCE = "https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0250897"

BOOLEAN_FIELDS = {
    "is_legume_n_fixing", "window_crosses_year", "hard_deadline_validated",
    "barc_zoning_required", "surface_wetness_threshold_validated",
}
INTEGER_FIELDS = {
    "regional_calendar_start_std_week", "regional_calendar_end_std_week",
    "regional_calendar_duration_min_days", "regional_calendar_duration_max_days",
    "variety_duration_min_days", "variety_duration_max_days",
    "seedling_age_min_days", "seedling_age_max_days", "ecocrop_duration_min_days",
    "ecocrop_duration_max_days", "turnaround_days_min", "turnaround_days_max",
}
NUMBER_FIELDS = INTEGER_FIELDS | {
    "temp_opt_min_c", "temp_opt_max_c", "temp_tol_min_c", "temp_tol_max_c",
    "precip_opt_min_mm", "precip_opt_max_mm", "precip_tol_min_mm", "precip_tol_max_mm",
    "ph_opt_min", "ph_opt_max", "ph_tol_min", "ph_tol_max",
    "local_phase_water_total_mm", "fao_crop_water_need_min_mm",
    "fao_crop_water_need_max_mm", "yield_reference_low_t_ha", "yield_reference_high_t_ha",
}
WEATHER_FIELDS = {
    "T2M": "temperature_mean_c",
    "T2M_MAX": "temperature_max_c",
    "T2M_MIN": "temperature_min_c",
    "PRECTOTCORR": "precipitation_mm",
    "GWETTOP": "surface_soil_wetness",
    "QV2M": "specific_humidity_g_kg",
}
EXPECTED_UNITS = {
    "T2M": "C", "T2M_MAX": "C", "T2M_MIN": "C",
    "PRECTOTCORR": "mm/day", "GWETTOP": "1", "QV2M": "g/kg",
}


def source_metadata(path, raw):
    return {"file": path.name, "sha256": hashlib.sha256(raw).hexdigest()}


def issue(issues, scope, field, message):
    issues.append({"scope": scope, "field": field, "message": message})


def number(value, context, integer=False):
    if value is None or not str(value).strip():
        return None
    try:
        result = float(value)
    except (ValueError, TypeError) as exc:
        raise ValueError(f"{context}: invalid number {value!r}") from exc
    if not math.isfinite(result) or (integer and not result.is_integer()):
        raise ValueError(f"{context}: expected a finite {'integer' if integer else 'number'}")
    return int(result) if integer else result


def boolean(value, context):
    if value is None or not str(value).strip():
        return None
    text = str(value).strip().lower()
    if text not in {"true", "false"}:
        raise ValueError(f"{context}: expected TRUE or FALSE, got {value!r}")
    return text == "true"


def check_range(low, high, context):
    if low is not None and high is not None and low > high:
        raise ValueError(f"{context}: minimum exceeds maximum")


def check_mmdd(value, context):
    if value is not None:
        if not re.fullmatch(r"\d{2}-\d{2}", value):
            raise ValueError(f"{context}: expected MM-DD")
        try:
            date.fromisoformat(f"2000-{value}")
        except ValueError as exc:
            raise ValueError(f"{context}: invalid calendar date {value}") from exc


def load_crops(path, issues):
    path = Path(path)
    raw = path.read_bytes()
    reader = csv.DictReader(io.StringIO(raw.decode("utf-8-sig")))
    required = {"crop_id", "crop_name_en", "reference_variety", "family",
                "preferred_start_mmdd", "preferred_end_mmdd", "window_crosses_year",
                "variety_duration_min_days", "variety_duration_max_days"}
    if not reader.fieldnames or not required <= set(reader.fieldnames):
        raise ValueError("Crop CSV: required columns are missing")
    if len(reader.fieldnames) != len(set(reader.fieldnames)):
        raise ValueError("Crop CSV: duplicate column names")
    crops = {}
    for line, raw_row in enumerate(reader, 2):
        if None in raw_row or any(value is None for value in raw_row.values()):
            raise ValueError(f"Crop CSV line {line}: inconsistent column count")
        row = {}
        for key, value in raw_row.items():
            value = value.strip() or None
            context = f"Crop CSV line {line}, {key}"
            if key in BOOLEAN_FIELDS:
                value = boolean(value, context)
            elif key in NUMBER_FIELDS:
                value = number(value, context, key in INTEGER_FIELDS)
            row[key] = value
        crop_id = row["crop_id"]
        if not crop_id or crop_id in crops:
            raise ValueError(f"Crop CSV line {line}: missing or duplicate crop_id {crop_id!r}")
        for key in NUMBER_FIELDS & row.keys():
            value = row[key]
            if value is not None and not key.startswith("temp_") and value < 0:
                raise ValueError(f"{crop_id}.{key}: negative value is invalid")
            if value is not None and key.startswith("ph_") and value > 14:
                raise ValueError(f"{crop_id}.{key}: pH must be between 0 and 14")
            if key.endswith("_std_week") and value is not None and not 1 <= value <= 53:
                raise ValueError(f"{crop_id}.{key}: invalid standard week")
            counterpart = key.replace("_min", "_max")
            if counterpart != key and counterpart in row:
                check_range(value, row[counterpart], f"{crop_id}.{key}")
        check_range(row.get("yield_reference_low_t_ha"), row.get("yield_reference_high_t_ha"),
                    f"{crop_id}.yield")
        for key in ("preferred_start_mmdd", "preferred_end_mmdd", "supported_late_end_mmdd"):
            check_mmdd(row.get(key), f"{crop_id}.{key}")
        start, end, crosses = (row.get(k) for k in
                              ("preferred_start_mmdd", "preferred_end_mmdd", "window_crosses_year"))
        if start and end and crosses is not None and (end < start) != crosses:
            raise ValueError(f"{crop_id}: preferred window disagrees with window_crosses_year")
        late = row.get("supported_late_end_mmdd")
        if start and end and late:
            # Compare seasonal ordering, allowing a late extension across New Year.
            if (late < start, late) < (end < start, end):
                raise ValueError(f"{crop_id}: supported late endpoint precedes preferred end")
        for key in ("preferred_start_mmdd", "preferred_end_mmdd", "window_crosses_year",
                    "variety_duration_min_days", "variety_duration_max_days"):
            if row.get(key) is None:
                issue(issues, crop_id, key, "Missing; dependent calendar calculations remain UNKNOWN")
        for key in ("variety_duration_min_days", "variety_duration_max_days"):
            if row.get(key) is not None and row[key] <= 0:
                raise ValueError(f"{crop_id}.{key}: duration must be positive")

        # A reviewed interpretation, not an inference from the establishment method.
        reference_event = None
        reference_source = None
        if (crop_id == "boro_brri_dhan28" and row.get("source_variety") == BORO_DURATION_SOURCE
                and row["variety_duration_min_days"] == row["variety_duration_max_days"] == 140):
            reference_event = "NURSERY_SOWING"
            reference_source = BORO_DURATION_SOURCE
        if reference_event is None:
            issue(issues, crop_id, "duration.reference_event",
                  "Duration starting event is unverified; do not calculate harvest from establishment")
        for key in ("turnaround_days_min", "turnaround_days_max"):
            if row.get(key) is None:
                issue(issues, crop_id, key, "Not sourced; do not assume zero preparation time")
        if not row.get("source_variety") or not row.get("source_planting_window"):
            issue(issues, crop_id, "evidence", "Duration or planting-window source is missing")
        if row.get("supported_late_end_mmdd") is None:
            issue(issues, crop_id, "planting_window.supported_late_end_mmdd",
                  "No late endpoint supplied; this does not establish a biological cutoff")
        if row.get("date_precision") not in (None, "DAY"):
            issue(issues, crop_id, "planting_window.date_precision", row["date_precision"])

        crops[crop_id] = {
            "identity": {k: row.get(k) for k in (
                "crop_id", "crop_name_en", "crop_name_bn", "reference_variety",
                "season_profile", "crop_role", "scientific_name", "family")},
            "establishment": {
                "method": row.get("establishment_method"),
                "seedling_age_days": {"min": row.get("seedling_age_min_days"),
                                      "max": row.get("seedling_age_max_days")},
            },
            "planting_window": {
                "preferred_start_mmdd": start, "preferred_end_mmdd": end,
                "supported_late_end_mmdd": row.get("supported_late_end_mmdd"),
                "crosses_year": crosses, "date_precision": row.get("date_precision"),
                "basis": row.get("window_basis"),
                "hard_deadline_validated": row.get("hard_deadline_validated"),
            },
            "duration": {
                "variety_days": {"min": row["variety_duration_min_days"],
                                 "max": row["variety_duration_max_days"]},
                "reference_event": reference_event, "reference_evidence": reference_source,
                "precision": row.get("duration_precision"),
            },
            "evidence": {
                "sources": {k.removeprefix("source_"): v for k, v in row.items()
                            if k.startswith("source_")},
                "location_scope": row.get("location_scope"),
                "location_note": row.get("rajshahi_location_note"),
                "research_notes": row.get("research_notes"),
                "overall_data_confidence": row.get("overall_data_confidence"),
            },
            # Complete typed research row retains environmental/water/rotation details
            # and qualifications without maintaining a second, lossy field mapping.
            "research": row,
        }
    if not crops:
        raise ValueError("Crop CSV: no crop records")
    return {"metadata": {**source_metadata(path, raw), "crop_count": len(crops)}, "crops": crops}


def load_climate(path, issues):
    path = Path(path)
    raw = path.read_bytes()
    lines = raw.decode("utf-8-sig").splitlines()
    try:
        header_end = next(i for i, line in enumerate(lines) if line.strip() == "-END HEADER-")
    except StopIteration as exc:
        raise ValueError("Climate CSV: NASA header terminator is missing") from exc
    header = "\n".join(lines[:header_end])
    reader = csv.DictReader(io.StringIO("\n".join(lines[header_end + 1:])))
    fields = reader.fieldnames or []
    if not {"YEAR", "DOY", "T2M", "PRECTOTCORR"} <= set(fields):
        raise ValueError("Climate CSV: YEAR, DOY, T2M and PRECTOTCORR are required")
    if len(fields) != len(set(fields)):
        raise ValueError("Climate CSV: duplicate column names")
    units = {}
    for parameter in WEATHER_FIELDS:
        if parameter not in fields:
            issue(issues, "climate", parameter, "Variable is absent; output values remain null")
            continue
        match = re.search(rf"^{parameter}\s+.*\(([^()]*)\)\s*$", header, re.MULTILINE)
        if not match or match[1] != EXPECTED_UNITS[parameter]:
            raise ValueError(f"Climate CSV: missing or unexpected unit for {parameter}")
        units[parameter] = match[1]
    metadata = source_metadata(path, raw)
    quarantined = metadata["sha256"] == QUARANTINED_RAINFALL_SHA256
    if quarantined:
        issue(issues, "climate", "precipitation_mm",
              "Exact source quarantined: sampled rainfall is 24x NASA API values; no correction applied")
    location = re.search(r"latitude\s+([-\d.]+)\s+longitude\s+([-\d.]+)", header)
    time_standard = re.search(r"\bin (LST|UTC)\b", header)
    if not location or not time_standard:
        raise ValueError("Climate CSV: coordinates or time standard are missing")
    latitude, longitude = float(location[1]), float(location[2])
    if not (-90 <= latitude <= 90 and -180 <= longitude <= 180):
        raise ValueError("Climate CSV: invalid coordinates")
    daily = {}
    missing = {parameter: 0 for parameter in WEATHER_FIELDS if parameter in fields}
    year_counts = {}
    for line, row in enumerate(reader, header_end + 3):
        if None in row or any(value is None for value in row.values()):
            raise ValueError(f"Climate CSV line {line}: inconsistent column count")
        year = number(row["YEAR"], f"Climate line {line}.YEAR", integer=True)
        doy = number(row["DOY"], f"Climate line {line}.DOY", integer=True)
        if year is None or not 1 <= year <= 9999 or doy is None or not 1 <= doy <= 365 + calendar.isleap(year):
            raise ValueError(f"Climate line {line}: invalid YEAR/DOY")
        key = (date(year, 1, 1) + timedelta(days=doy - 1)).isoformat()
        if key in daily:
            raise ValueError(f"Climate CSV: duplicate date {key}")
        weather = {}
        for parameter, output in WEATHER_FIELDS.items():
            value = number(row.get(parameter), f"Climate {key}.{parameter}")
            if value == -999:
                value = None
            if value is None and parameter in missing:
                missing[parameter] += 1
            if value is not None:
                if parameter in {"PRECTOTCORR", "QV2M"} and value < 0:
                    raise ValueError(f"Climate {key}.{parameter}: negative value")
                if parameter == "GWETTOP" and not 0 <= value <= 1:
                    raise ValueError(f"Climate {key}.GWETTOP: expected 0..1")
            weather[output] = value
        check_range(weather["temperature_min_c"], weather["temperature_max_c"], f"Climate {key}.temperature")
        check_range(weather["temperature_min_c"], weather["temperature_mean_c"], f"Climate {key}.minimum/mean")
        check_range(weather["temperature_mean_c"], weather["temperature_max_c"], f"Climate {key}.mean/maximum")
        if quarantined:
            weather["precipitation_source_value"] = weather["precipitation_mm"]
            weather["precipitation_mm"] = None
        daily[key] = weather
        year_counts[year] = year_counts.get(year, 0) + 1
    if not daily:
        raise ValueError("Climate CSV: no observations")
    first, last = min(daily), max(daily)
    missing_date_count = (date.fromisoformat(last) - date.fromisoformat(first)).days + 1 - len(daily)
    if missing_date_count:
        issue(issues, "climate", "dates", f"{missing_date_count} dates absent inside source coverage")
    for parameter, count in missing.items():
        if count:
            issue(issues, "climate", parameter, f"{count} missing observations; represented as null")
    years = {str(year): {"rows": count, "expected_days": 365 + calendar.isleap(year),
                         "calendar_complete": count == 365 + calendar.isleap(year)}
             for year, count in sorted(year_counts.items())}
    metadata.update({
        "latitude": latitude, "longitude": longitude, "time_standard": time_standard[1],
        "source_units": units, "first_date": first, "last_date": last,
        "daily_count": len(daily), "missing_date_count": missing_date_count,
        "missing_observations": missing, "years": years,
        "precipitation_status": "QUARANTINED_SOURCE" if quarantined else "SOURCE_UNITS_ACCEPTED",
        "transformations": ["NASA -999 and blank observations become null"],
        "coverage_note": "Calendar completeness does not establish variable-specific completeness or scientific validation",
    })
    return {"metadata": metadata, "daily": dict(sorted(daily.items()))}


def build_foundation(crop_path=DEFAULT_CROPS, climate_path=DEFAULT_CLIMATE):
    issues = []
    crops = load_crops(crop_path, issues)
    climate = load_climate(climate_path, issues)
    return {
        "schema_version": "1.0",
        "crop_data": crops, "climate_data": climate,
        "validation_report": {
            "status": "VALID_WITH_WARNINGS" if issues else "VALID",
            "crop_count": len(crops["crops"]), "climate_days": len(climate["daily"]),
            "warning_count": len(issues), "warnings": issues,
            "note": "Structural validation is not agricultural validation or calculation readiness",
        },
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--crops", type=Path, default=DEFAULT_CROPS)
    parser.add_argument("--climate", type=Path, default=DEFAULT_CLIMATE)
    parser.add_argument("--output", type=Path, help="Optional internal JSON artifact; existing files are never overwritten")
    args = parser.parse_args()
    try:
        result = build_foundation(args.crops, args.climate)
        if args.output:
            # Serialize before opening; invalid data cannot leave a partial export.
            payload = json.dumps(result, indent=2, ensure_ascii=False, allow_nan=False)
            with args.output.open("x", encoding="utf-8") as stream:
                stream.write(payload + "\n")
        print(json.dumps(result["validation_report"], indent=2, ensure_ascii=False))
    except (ValueError, OSError, csv.Error) as exc:
        print(json.dumps({"status": "INVALID", "error": str(exc)}, ensure_ascii=False))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
