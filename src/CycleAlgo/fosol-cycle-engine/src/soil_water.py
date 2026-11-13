"""Shared soil/land and water-compatibility checks (v1.md §7, §8).

One evaluator serves every crop. Soil properties are only evaluated when
explicit local evidence is supplied; the crop CSV's EcoCrop pH/texture/
drainage/salinity text stays crop guidance, never a district measurement.
Missing evidence returns ``unknown`` and never an automatic pass.

SMAP/POWER wetness is context only and cannot change a soil status: all
current profiles record ``surface_wetness_threshold_validated = FALSE``.

Water checks never calculate demand minus rainfall. Quantified demand is
FAO/local phase guidance; water access is a user scenario. Every
demand-present case is a caution, including ``irrigation_available``.
"""

from __future__ import annotations

import math
import re

WATER_ACCESS_VALUES = ("rainfed", "irrigation_available", "unknown")

_PRECEDENCE = {"pass": 0, "unknown": 1, "caution": 2, "unsupported": 3}
_SALINITY_RULE_RE = re.compile(r"<\s*(\d+(?:\.\d+)?)\s*dS/m", re.IGNORECASE)


def evaluate_soil_fit(
    profile: dict,
    soil_evidence: dict | None = None,
    moisture_context: dict | None = None,
) -> dict:
    """Evaluate the crop profile's soil/land fit for one district.

    ``soil_evidence`` is optional local evidence:
    ``{"ph": {"min", "max", "source_ids"}, "texture": {"value", "source_ids"},
    "drainage": {"value", "source_ids"},
    "salinity": {"min", "max", "unit": "dS/m", "source_ids"}}``.

    ``moisture_context`` (for example SMAP ``sm_surface``/``sm_rootzone``) is
    recorded but never used for the status.
    """
    evidence = soil_evidence if isinstance(soil_evidence, dict) else {}
    checks = {
        "ph": _check_ph(profile, evidence.get("ph")),
        "texture": _check_texture(profile, evidence.get("texture")),
        "drainage": _check_drainage(profile, evidence.get("drainage")),
        "salinity": _check_salinity(profile, evidence.get("salinity")),
    }
    result = _aggregate("Soil", checks)
    result["checks"] = checks
    result["moisture_context"] = _moisture_context(profile, moisture_context)
    return result


def evaluate_water_fit(
    profile: dict,
    water_access: str = "unknown",
    environment: dict | None = None,
) -> dict:
    """Evaluate water compatibility without computing a water balance.

    ``water_access`` is one of ``rainfed``, ``irrigation_available``,
    ``unknown``; any other value raises ``ValueError``. ``environment`` is
    accepted for contract symmetry but never changes the status.
    """
    if not isinstance(water_access, str) or water_access not in WATER_ACCESS_VALUES:
        raise ValueError(
            "water_access must be one of "
            + ", ".join(WATER_ACCESS_VALUES)
            + f": {water_access!r}"
        )

    demand = {
        "fao_crop_water_need_min_mm": _number(
            _field_value(profile, "fao_crop_water_need_min_mm")
        ),
        "fao_crop_water_need_max_mm": _number(
            _field_value(profile, "fao_crop_water_need_max_mm")
        ),
        "local_phase_water_total_mm": _number(
            _field_value(profile, "local_phase_water_total_mm")
        ),
    }
    has_demand = any(value is not None for value in demand.values())

    sources: list[str] = []
    if (
        demand["fao_crop_water_need_min_mm"] is not None
        or demand["fao_crop_water_need_max_mm"] is not None
    ):
        sources.extend(_sources({"source_ids": [_text(profile, "source_water")]}))
    if demand["local_phase_water_total_mm"] is not None:
        sources.extend(
            _sources({"source_ids": [_text(profile, "source_local_calendar")]})
        )
    sources = _dedupe(sources)

    result = {
        "status": "unknown",
        "code": "WATER_DEMAND_EVIDENCE_MISSING",
        "reason": (
            "The crop profile has no quantified water-demand evidence (an FAO "
            "range or a local phase water total), so water fit stays unknown even "
            "when irrigation is reported available."
        ),
        "source_ids": sources,
        "missing_evidence": ["crop_water_demand_evidence"],
        "water_access": water_access,
        "has_quantified_demand": has_demand,
        "demand_evidence": {
            **demand,
            "is_crop_guidance": True,
            "unit": "mm",
        },
        "irrigation_guidance": _text(profile, "irrigation_guidance"),
        "irrigation_demand_calculated": False,
        "environment_used_for_status": False,
    }
    if any(value is not None and value < 0 for value in demand.values()):
        result.update(
            status="unknown",
            code="WATER_DEMAND_EVIDENCE_INVALID",
            reason=(
                "The crop profile has a negative water-demand value; negative "
                "demand is not usable evidence, so water fit is unknown."
            ),
            has_quantified_demand=False,
        )
        return result
    if not has_demand:
        return result

    result["missing_evidence"] = []
    if water_access == "unknown":
        result.update(
            status="caution",
            code="IRRIGATION_CONFIRMATION_REQUIRED",
            reason=(
                "Irrigation confirmation required. The crop profile carries "
                "quantified water-demand guidance, but water access was not "
                "confirmed, so this prerequisite remains unresolved."
            ),
        )
    elif water_access == "rainfed":
        result.update(
            status="caution",
            code="RAINFED_GUIDANCE_REVIEW",
            reason=(
                "Rainfed water access does not establish that rainfall will meet "
                "this crop's documented water-demand guidance. Rainfall is not "
                "assumed to satisfy the requirement."
            ),
        )
    else:  # irrigation_available
        result.update(
            status="caution",
            code="IRRIGATION_PARTIAL_CONFIRMATION",
            reason=(
                "Irrigation is reported as available, but the amount, timing, "
                "reliability, and cost are not confirmed. This addresses only "
                "part of the prerequisite."
            ),
        )
    return result


def evaluate_soil_water(
    profile: dict,
    water_access: str = "unknown",
    soil_evidence: dict | None = None,
    moisture_context: dict | None = None,
    environment: dict | None = None,
) -> dict:
    """Combine soil/land and water checks with the shared precedence."""
    soil = evaluate_soil_fit(profile, soil_evidence, moisture_context)
    water = evaluate_water_fit(profile, water_access, environment)
    checks = {"soil": soil, "water": water}
    result = _aggregate("Soil and water", checks)
    result["checks"] = checks
    return result


def _check_ph(profile: dict, evidence: object) -> dict:
    local = evidence if isinstance(evidence, dict) else None
    low = _number(local.get("min")) if local is not None else None
    high = _number(local.get("max")) if local is not None else None
    sources = _sources(local)

    if low is None or high is None:
        return _check(
            "unknown",
            "SOIL_PH_EVIDENCE_MISSING",
            "No local district pH evidence was supplied; pH fit is unknown "
            "rather than an automatic pass.",
            sources,
            ["district_soil_ph"],
            {"local": None},
        )
    if low < 0 or high > 14 or low > high:
        return _check(
            "unknown",
            "SOIL_PH_EVIDENCE_INVALID",
            f"Local pH evidence {_fmt(low)}-{_fmt(high)} is outside the valid "
            "0-14 range or has min greater than max; the range cannot be "
            "interpreted.",
            sources,
            ["district_soil_ph"],
            {"local": {"min": low, "max": high}},
        )

    rule, rule_code = _ph_rule(profile)
    if rule is None:
        if rule_code == "SOIL_PH_CROP_RULE_MISSING":
            reason = (
                "The crop profile has no complete pH optimum/tolerance rule; pH "
                "fit is unknown."
            )
        else:
            reason = (
                "The crop pH optimum/tolerance rule is not usable: it must be "
                "within 0-14, correctly ordered, and its tolerance must contain "
                "its optimum; pH fit is unknown."
            )
        return _check(
            "unknown",
            rule_code,
            reason,
            sources,
            ["crop_soil_ph_rule"],
            {"local": {"min": low, "max": high}},
        )

    opt_min, opt_max, tol_min, tol_max = rule
    details = {
        "local": {"min": low, "max": high},
        "crop_optimum": {"min": opt_min, "max": opt_max},
        "crop_tolerance": {"min": tol_min, "max": tol_max},
    }
    if not sources:
        return _check(
            "unknown",
            "SOIL_EVIDENCE_SOURCE_MISSING",
            "Local pH evidence has no source_ids; a pH result cannot be "
            "reported without provenance.",
            sources,
            ["local_soil_evidence_source"],
            details,
        )
    sources = _dedupe(
        sources + _sources({"source_ids": [_text(profile, "source_ecocrop")]})
    )

    if low >= opt_min and high <= opt_max:
        return _check(
            "pass",
            "SOIL_PH_WITHIN_OPTIMUM",
            f"The local pH range {_fmt(low)}-{_fmt(high)} lies wholly inside the "
            f"crop optimum {_fmt(opt_min)}-{_fmt(opt_max)} (inclusive).",
            sources,
            [],
            details,
        )
    if high < tol_min or low > tol_max:
        return _check(
            "unsupported",
            "SOIL_PH_OUTSIDE_TOLERANCE",
            f"The local pH range {_fmt(low)}-{_fmt(high)} lies wholly outside the "
            f"crop tolerance {_fmt(tol_min)}-{_fmt(tol_max)}; the documented rule "
            "conflicts with this scenario.",
            sources,
            [],
            details,
        )
    if low < tol_min or high > tol_max:
        return _check(
            "caution",
            "SOIL_PH_PARTIALLY_OUTSIDE_TOLERANCE",
            f"The local pH range {_fmt(low)}-{_fmt(high)} extends outside the crop "
            f"tolerance {_fmt(tol_min)}-{_fmt(tol_max)}; a caution applies.",
            sources,
            [],
            details,
        )
    if high < opt_min or low > opt_max:
        return _check(
            "caution",
            "SOIL_PH_OUTSIDE_OPTIMUM_WITHIN_TOLERANCE",
            f"The local pH range {_fmt(low)}-{_fmt(high)} lies outside the crop "
            f"optimum {_fmt(opt_min)}-{_fmt(opt_max)} but inside the tolerance "
            f"{_fmt(tol_min)}-{_fmt(tol_max)}; a caution applies.",
            sources,
            [],
            details,
        )
    return _check(
        "caution",
        "SOIL_PH_OVERLAPS_OPTIMUM",
        f"The local pH range {_fmt(low)}-{_fmt(high)} overlaps the crop optimum "
        f"{_fmt(opt_min)}-{_fmt(opt_max)} but is not wholly inside it; a caution "
        "applies.",
        sources,
        [],
        details,
    )


def _check_texture(profile: dict, evidence: object) -> dict:
    value = _local_value(evidence)
    sources = _sources(evidence)
    if value is None:
        return _check(
            "unknown",
            "SOIL_TEXTURE_EVIDENCE_MISSING",
            "No local district texture evidence was supplied; texture fit is "
            "unknown rather than an automatic pass.",
            sources,
            ["district_soil_texture"],
            {"ecocrop_guidance": _text(profile, "soil_texture_ecocrop")},
        )
    return _check(
        "unknown",
        "SOIL_TEXTURE_MAPPING_UNVALIDATED",
        "Local texture evidence was supplied, but v1 has no validated "
        "texture-to-crop mapping; texture fit is unknown. EcoCrop texture text is "
        "crop guidance, not a local measurement.",
        sources,
        [],
        {
            "local_value": value,
            "mapping_validated": False,
            "ecocrop_guidance": _text(profile, "soil_texture_ecocrop"),
        },
    )


def _check_drainage(profile: dict, evidence: object) -> dict:
    value = _local_value(evidence)
    sources = _sources(evidence)
    if value is None:
        return _check(
            "unknown",
            "SOIL_DRAINAGE_EVIDENCE_MISSING",
            "No local district drainage evidence was supplied; drainage fit is "
            "unknown rather than an automatic pass.",
            sources,
            ["district_soil_drainage"],
            {"ecocrop_guidance": _text(profile, "drainage_ecocrop")},
        )
    return _check(
        "unknown",
        "SOIL_DRAINAGE_MAPPING_UNVALIDATED",
        "Local drainage evidence was supplied, but v1 has no validated "
        "drainage-to-crop mapping; drainage fit is unknown. EcoCrop drainage text "
        "is crop guidance, not a local measurement.",
        sources,
        [],
        {
            "local_value": value,
            "mapping_validated": False,
            "ecocrop_guidance": _text(profile, "drainage_ecocrop"),
        },
    )


def _check_salinity(profile: dict, evidence: object) -> dict:
    local = evidence if isinstance(evidence, dict) else None
    low = _number(local.get("min")) if local is not None else None
    high = _number(local.get("max")) if local is not None else None
    sources = _sources(local)
    unit = local.get("unit") if local is not None else None
    details = {
        "local": (
            None if low is None or high is None else {"min": low, "max": high}
        ),
        "unit": unit,
    }

    if low is None or high is None:
        return _check(
            "unknown",
            "SOIL_SALINITY_EVIDENCE_MISSING",
            "No local district salinity evidence was supplied; salinity fit is "
            "unknown rather than an automatic pass.",
            sources,
            ["district_soil_salinity"],
            details,
        )
    if low < 0 or high < 0 or low > high:
        return _check(
            "unknown",
            "SOIL_SALINITY_EVIDENCE_INVALID",
            f"Local salinity evidence {_fmt(low)}-{_fmt(high)} is negative or has "
            "min greater than max; the range cannot be interpreted.",
            sources,
            ["district_soil_salinity"],
            details,
        )
    unit_text = None if unit is None else str(unit).strip()
    if not unit_text:
        return _check(
            "unknown",
            "SOIL_SALINITY_UNIT_MISSING",
            "Local salinity evidence has no unit; dS/m cannot be assumed, so "
            "salinity fit is unknown.",
            sources,
            ["district_soil_salinity"],
            details,
        )
    if unit_text != "dS/m":
        return _check(
            "unknown",
            "SOIL_SALINITY_UNIT_INVALID",
            f"Local salinity unit {unit!r} is not dS/m; it cannot be compared "
            "with the crop guidance rule.",
            sources,
            ["district_soil_salinity"],
            details,
        )

    threshold = _salinity_threshold(profile)
    if threshold is None:
        return _check(
            "unknown",
            "SOIL_SALINITY_RULE_UNVALIDATED",
            "The crop salinity guidance could not be parsed as a '<N dS/m' "
            "rule; salinity fit is unknown.",
            sources,
            ["crop_soil_salinity_rule"],
            details,
        )

    if not sources:
        return _check(
            "unknown",
            "SOIL_EVIDENCE_SOURCE_MISSING",
            "Local salinity evidence has no source_ids; a salinity result cannot "
            "be reported without provenance.",
            sources,
            ["local_soil_evidence_source"],
            details,
        )
    sources = _dedupe(
        sources + _sources({"source_ids": [_text(profile, "source_ecocrop")]})
    )
    details["crop_low_guidance_ds_m"] = threshold
    if high < threshold:
        return _check(
            "pass",
            "SOIL_SALINITY_WITHIN_LOW_GUIDANCE",
            f"The local salinity maximum {_fmt(high)} dS/m is below the crop "
            f"low-salinity guidance (<{_fmt(threshold)} dS/m).",
            sources,
            [],
            details,
        )
    if low > threshold:
        return _check(
            "caution",
            "SOIL_SALINITY_ABOVE_LOW_GUIDANCE",
            f"The local salinity minimum {_fmt(low)} dS/m is above the crop "
            f"low-salinity guidance (<{_fmt(threshold)} dS/m); salinity needs "
            "review.",
            sources,
            [],
            details,
        )
    if high == threshold:
        return _check(
            "caution",
            "SOIL_SALINITY_AT_LOW_GUIDANCE",
            f"The local salinity maximum {_fmt(high)} dS/m equals the crop "
            f"low-salinity guidance boundary (<{_fmt(threshold)} dS/m is strict); "
            "salinity needs review.",
            sources,
            [],
            details,
        )
    return _check(
        "caution",
        "SOIL_SALINITY_PARTIALLY_ABOVE_LOW_GUIDANCE",
        f"The local salinity range {_fmt(low)}-{_fmt(high)} dS/m straddles the "
        f"crop low-salinity guidance (<{_fmt(threshold)} dS/m); salinity needs "
        "review.",
        sources,
        [],
        details,
    )


def _ph_rule(
    profile: dict,
) -> tuple[tuple[float, float, float, float] | None, str | None]:
    """Return ``((opt_min, opt_max, tol_min, tol_max), error_code)``.

    A usable rule is within pH 0-14, correctly ordered, and has a tolerance
    that contains the optimum.
    """
    values = (
        _number(_field_value(profile, "ph_opt_min")),
        _number(_field_value(profile, "ph_opt_max")),
        _number(_field_value(profile, "ph_tol_min")),
        _number(_field_value(profile, "ph_tol_max")),
    )
    if any(value is None for value in values):
        return None, "SOIL_PH_CROP_RULE_MISSING"
    opt_min, opt_max, tol_min, tol_max = values
    if (
        opt_min < 0
        or opt_max > 14
        or tol_min < 0
        or tol_max > 14
        or opt_min > opt_max
        or tol_min > tol_max
        or tol_min > opt_min
        or tol_max < opt_max
    ):
        return None, "SOIL_PH_CROP_RULE_INVALID"
    return (opt_min, opt_max, tol_min, tol_max), None


def _salinity_threshold(profile: dict) -> float | None:
    text = _text(profile, "salinity_ecocrop")
    if text is None:
        return None
    match = _SALINITY_RULE_RE.search(text)
    return float(match.group(1)) if match else None


def _moisture_context(profile: dict, context: object) -> dict:
    data = context if isinstance(context, dict) else {}
    flag = _field_value(profile, "surface_wetness_threshold_validated")
    validated = flag is True or (
        isinstance(flag, str) and flag.strip().upper() == "TRUE"
    )
    return {
        "used_for_status": False,
        "threshold_validated": validated,
        "surface": _number(data.get("sm_surface", data.get("surface"))),
        "rootzone": _number(data.get("sm_rootzone", data.get("rootzone"))),
        "source_ids": _sources(data),
    }


def _aggregate(label: str, checks: dict[str, dict]) -> dict:
    dominant = max(checks.values(), key=lambda check: _PRECEDENCE[check["status"]])
    status = dominant["status"]
    return {
        "status": status,
        "code": dominant["code"],
        "reason": f"{label} fit is {status}. {dominant['reason']}",
        "source_ids": _dedupe(
            [source for check in checks.values() for source in check["source_ids"]]
        ),
        "missing_evidence": _dedupe(
            [
                item
                for check in checks.values()
                for item in check["missing_evidence"]
            ]
        ),
    }


def _check(
    status: str,
    code: str,
    reason: str,
    source_ids: list[str],
    missing_evidence: list[str],
    details: dict,
) -> dict:
    return {
        "status": status,
        "code": code,
        "reason": reason,
        "source_ids": source_ids,
        "missing_evidence": missing_evidence,
        "details": details,
    }


def _field_value(profile: dict, field: str) -> object:
    value = profile.get(field)
    if value is not None:
        return value
    raw = profile.get("raw")
    if isinstance(raw, dict):
        return raw.get(field)
    return None


def _text(profile: dict, field: str) -> str | None:
    value = _field_value(profile, field)
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _local_value(evidence: object) -> str | None:
    if not isinstance(evidence, dict):
        return None
    value = evidence.get("value")
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _sources(evidence: object) -> list[str]:
    if not isinstance(evidence, dict):
        return []
    values = evidence.get("source_ids")
    if isinstance(values, str):
        values = [values]
    if not isinstance(values, (list, tuple)):
        return []
    return _dedupe(
        [
            str(value).strip()
            for value in values
            if value is not None and str(value).strip()
        ]
    )


def _number(value: object) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(number):
        return None
    return number


def _dedupe(values: list[str]) -> list[str]:
    return list(dict.fromkeys(values))


def _fmt(value: float) -> str:
    return f"{value:g}"
