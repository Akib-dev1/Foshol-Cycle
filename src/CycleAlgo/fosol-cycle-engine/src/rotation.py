"""Rotation compatibility for second and third crops (v1.md §11).

The crop CSV carries advisory rotation text but no structured, sourced
crop-to-crop restriction. Same-family repetition is therefore a transparent
diversity caution, never a rejection. A family change is not evidence of
disease control, soil-carbon improvement, or nitrogen balance, and legume
presence is a potential biological-nitrogen-fixation indicator rather than a
guaranteed nitrogen credit.
"""

from __future__ import annotations


def evaluate_rotation(
    profile: dict,
    previous_profile: dict | None,
    path_profiles: list[dict] | tuple[dict, ...] | None,
) -> dict:
    """Compare the current crop family with every prior family in the path.

    ``path_profiles`` is the ordered prior-crop path; the current crop is
    appended at its actual position, so duplicate crop IDs are preserved.
    No machine-readable blocking rule exists in the current data, so ``status``
    is never ``unsupported`` and ``blocking`` is always false.
    """
    path = _path_profiles(path_profiles, previous_profile, profile)
    current_family = _profile_text(profile, "family")
    previous_family = (
        _profile_text(path[-2], "family") if len(path) >= 2 else None
    )
    prior_families = [_profile_text(item, "family") for item in path[:-1]]
    legume_profiles = [
        item
        for item in path
        if _is_true(item.get("is_legume_n_fixing"))
    ]
    legume_ids = _dedupe(
        [
            crop_id
            for crop_id in (
                _profile_text(item, "crop_id") for item in legume_profiles
            )
            if crop_id is not None
        ]
    )

    matched_positions: list[int] = []
    if (
        current_family is None
        or not prior_families
        or any(family is None for family in prior_families)
    ):
        status = "unknown"
        code = "ROTATION_FAMILY_EVIDENCE_MISSING"
        reason = (
            "The current or a prior crop family is missing; rotation "
            "compatibility is unknown rather than an automatic pass."
        )
        missing = ["crop_family"]
    else:
        matched_positions = [
            position
            for position, family in enumerate(prior_families, start=1)
            if _same_family(current_family, family)
        ]
        if matched_positions:
            matched_positions.append(len(path))
            if _same_family(current_family, prior_families[-1]):
                status = "caution"
                code = "SAME_FAMILY_REPEAT"
                reason = (
                    f"Both the previous crop and this crop are in {current_family}. "
                    "Same-family repetition is a diversity caution only; it is not "
                    "rejected because no structured, sourced restriction exists."
                )
            else:
                status = "caution"
                code = "FAMILY_REPEAT_IN_PATH"
                reason = (
                    f"The current crop family {current_family} also appears at "
                    f"position(s) {', '.join(str(p) for p in matched_positions[:-1])} "
                    "earlier in the three-crop path. Repeated families are a "
                    "diversity caution only; they are not rejected because no "
                    "structured, sourced restriction exists."
                )
            missing = []
        else:
            status = "pass"
            code = "FAMILY_DIVERSIFIED"
            reason = (
                f"The family changes from {previous_family} to {current_family}. "
                "Family diversification alone does not establish disease control, "
                "soil-carbon improvement, or nitrogen balance."
            )
            missing = []

    return {
        "status": status,
        "code": code,
        "reason": reason,
        "source_ids": ["rotation_family_rule"],
        "family": current_family,
        "previous_family": previous_family,
        "matched_positions": matched_positions,
        "diversity_indicator": True,
        "blocking": False,
        "rule_machine_readable": False,
        "machine_readable_rule_source_ids": [],
        "rotation_family_rule": _advisory_text(profile, "rotation_family_rule"),
        "rotation_note": _advisory_text(profile, "rotation_note"),
        "legume_present_in_path": bool(legume_profiles),
        "legume_crop_ids": legume_ids,
        "legume_note": (
            "A legume is present in the path; this is potential biological "
            "nitrogen fixation under suitable conditions, not a guaranteed "
            "nitrogen credit or fertilizer saving."
            if legume_profiles
            else "No legume is present in the path."
        ),
        "path_length": len(path),
        "path_crop_ids": [
            crop_id
            for crop_id in (_profile_text(item, "crop_id") for item in path)
            if crop_id is not None
        ],
        "missing_evidence": missing,
    }


def _path_profiles(
    path_profiles: list[dict] | tuple[dict, ...] | None,
    previous_profile: dict | None,
    profile: dict,
) -> list[dict]:
    if isinstance(path_profiles, dict):
        path = [path_profiles]
    elif isinstance(path_profiles, (list, tuple)):
        path = [item for item in path_profiles if isinstance(item, dict)]
    else:
        path = []

    if not path and isinstance(previous_profile, dict):
        path = [previous_profile]
    path.append(profile)
    return path


def _same_family(left: str, right: str) -> bool:
    return left.strip().casefold() == right.strip().casefold()


def _is_true(value: object) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().upper() == "TRUE"
    return False


def _dedupe(values) -> list:
    return list(dict.fromkeys(values))


def _profile_text(profile: dict, field: str) -> str | None:
    value = profile.get(field)
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _advisory_text(profile: dict, field: str) -> str | None:
    value = profile.get(field)
    if value is None:
        raw = profile.get("raw")
        if isinstance(raw, dict):
            value = raw.get(field)
    if value is None:
        return None
    text = str(value).strip()
    return text or None
