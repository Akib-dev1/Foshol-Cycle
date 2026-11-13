"""Validate and default a §14.2 explore request.

Only shape/type/enum validation and documented defaults live here. District
support is decided downstream (E9); a well-formed district ID is accepted
regardless of whether local evidence exists for it.
"""

from __future__ import annotations

import datetime as dt
import re
from collections.abc import Collection

WATER_ACCESS_VALUES = ("rainfed", "irrigation_available", "unknown")
PREFERENCE_VALUES = (
    "fastest_completion",
    "lowest_total_cost",
    "least_irrigation_dependence",
    "highest_net_return",
    "more_crop_diversity",
    "closest_temperature_match",
    "least_dry_spell_exposure",
    "least_heavy_rain_exposure",
)

DEFAULT_WATER_ACCESS = "unknown"
DEFAULT_PREFERENCE = "fastest_completion"

# Leave room for the previous calendar year and multi-year three-crop schedules.
MIN_START_DATE = "0002-01-01"
MAX_START_DATE = "9990-12-31"

_DATE_RE = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}")


class RequestValidationError(Exception):
    """A request that violates the §14.2 contract."""

    code = "INVALID_REQUEST"

    def __init__(self, message: str, field: str | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.field = field


def validate_explore_request(
    payload: object, known_crop_ids: Collection[str]
) -> dict:
    """Return the effective request with defaults applied.

    Unknown extra keys are ignored. Raises ``RequestValidationError`` rather
    than coercing a wrong type or substituting an invalid enum value.
    """
    if not isinstance(payload, dict):
        raise RequestValidationError("Request payload must be a JSON object.", None)

    if "district_id" not in payload:
        raise RequestValidationError("district_id is required.", "district_id")
    district_id = payload["district_id"]
    if not isinstance(district_id, str) or not district_id.strip():
        raise RequestValidationError(
            "district_id must be a non-empty string.", "district_id"
        )

    if "start_date" not in payload:
        raise RequestValidationError("start_date is required.", "start_date")
    start_date = payload["start_date"]
    if not isinstance(start_date, str) or _DATE_RE.fullmatch(start_date) is None:
        raise RequestValidationError(
            "start_date must be a valid YYYY-MM-DD date.", "start_date"
        )
    try:
        dt.date(
            int(start_date[0:4]), int(start_date[5:7]), int(start_date[8:10])
        )
    except ValueError:
        raise RequestValidationError(
            "start_date must be a valid YYYY-MM-DD date.", "start_date"
        ) from None
    if not MIN_START_DATE <= start_date <= MAX_START_DATE:
        raise RequestValidationError(
            f"start_date must be between {MIN_START_DATE} and {MAX_START_DATE}.",
            "start_date",
        )

    if "first_crop_id" not in payload:
        raise RequestValidationError(
            "first_crop_id is required.", "first_crop_id"
        )
    first_crop_id = payload["first_crop_id"]
    if first_crop_id is not None and (
        not isinstance(first_crop_id, str) or first_crop_id not in known_crop_ids
    ):
        raise RequestValidationError(
            "first_crop_id must be null or an existing crop ID.",
            "first_crop_id",
        )

    water_access = payload.get("water_access", DEFAULT_WATER_ACCESS)
    if not isinstance(water_access, str) or water_access not in WATER_ACCESS_VALUES:
        raise RequestValidationError(
            "water_access must be one of: "
            + ", ".join(WATER_ACCESS_VALUES)
            + ".",
            "water_access",
        )

    preference = payload.get("preference", DEFAULT_PREFERENCE)
    if not isinstance(preference, str) or preference not in PREFERENCE_VALUES:
        raise RequestValidationError(
            "preference must be one of: "
            + ", ".join(PREFERENCE_VALUES)
            + ".",
            "preference",
        )

    return {
        "district_id": district_id,
        "start_date": start_date,
        "first_crop_id": first_crop_id,
        "water_access": water_access,
        "preference": preference,
    }
