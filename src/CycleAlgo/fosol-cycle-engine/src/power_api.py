"""NASA POWER daily point API client and response normalizer.

Only the documented daily point endpoint is used. Provider fill values are
converted to ``None``; they are never turned into physical observations.
"""

from __future__ import annotations

import datetime as dt
import json
import math
import time
import urllib.error
import urllib.parse
import urllib.request
from collections.abc import Callable, Sequence

POWER_DAILY_URL = "https://power.larc.nasa.gov/api/temporal/daily/point"
PROVIDER = "NASA POWER"
PRODUCT = "NASA POWER Daily Point"
POWER_PRODUCT_VERSION = "v2.10.3"
COMMUNITY = "AG"
UNITS = "metric"
TIME_STANDARD = "LST"
SPATIAL_RESOLUTION = "0.5 x 0.625 degree lat/lon region (MERRA-2)"
TEMPORAL_RESOLUTION = "daily"

DEFAULT_TIMEOUT_SECONDS = 30.0
DEFAULT_MAX_RETRIES = 3
DEFAULT_BACKOFF_SECONDS = 1.0

# 429 and all 5xx responses are retryable. Other 4xx responses are not.
RETRYABLE_STATUS_CODES = frozenset({429})


class PowerApiError(Exception):
    """A POWER request or response that could not be used."""

    code = "POWER_API_ERROR"

    def __init__(
        self,
        message: str,
        *,
        status_code: int | None = None,
        code: str | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.code = code or type(self).code


def _iso_date(value: object, field: str) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{field} must be a YYYY-MM-DD string")
    try:
        parsed = dt.date.fromisoformat(value)
    except ValueError:
        raise ValueError(f"{field} must be a YYYY-MM-DD string") from None
    if parsed.isoformat() != value:
        raise ValueError(f"{field} must be a YYYY-MM-DD string")
    return value


def _coordinate(value: object, field: str, low: float, high: float) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{field} must be a finite number")
    number = float(value)
    if not math.isfinite(number) or not low <= number <= high:
        raise ValueError(f"{field} must be between {low} and {high}")
    return number


def _power_date(value: object) -> str:
    if not isinstance(value, str) or len(value) != 8 or not value.isascii():
        raise PowerApiError("POWER response contains a non-YYYYMMDD observation date.")
    if not value.isdigit():
        raise PowerApiError("POWER response contains a non-YYYYMMDD observation date.")
    try:
        parsed = dt.date(int(value[0:4]), int(value[4:6]), int(value[6:8]))
    except ValueError:
        raise PowerApiError(
            "POWER response contains an invalid observation date."
        ) from None
    return parsed.isoformat()


def _http_detail(exc: urllib.error.HTTPError) -> str:
    """Return a short provider message without headers or request data."""
    detail = ""
    try:
        body = exc.read()
        payload = json.loads(body.decode("utf-8"))
    except Exception:  # noqa: BLE001 - error bodies are best effort
        payload = None
    if isinstance(payload, dict):
        messages = payload.get("messages")
        if isinstance(messages, list):
            detail = "; ".join(str(item) for item in messages if item)
        elif isinstance(messages, str):
            detail = messages
        elif isinstance(payload.get("message"), str):
            detail = payload["message"]
    suffix = f" {detail}" if detail else ""
    return f"POWER API returned HTTP {exc.code}.{suffix}"


def build_power_url(
    latitude: float,
    longitude: float,
    start_date: str,
    end_date: str,
    parameters: Sequence[str],
    *,
    community: str = COMMUNITY,
    units: str = UNITS,
    time_standard: str = TIME_STANDARD,
) -> str:
    """Build the documented daily point URL. Inputs are not silently coerced."""
    start = _iso_date(start_date, "start_date")
    end = _iso_date(end_date, "end_date")
    if start > end:
        raise ValueError("start_date must not be after end_date")
    _coordinate(latitude, "latitude", -90.0, 90.0)
    _coordinate(longitude, "longitude", -180.0, 180.0)

    names: list[str] = []
    for name in parameters:
        if not isinstance(name, str) or not name:
            raise ValueError("parameters must be non-empty strings")
        if name not in names:
            names.append(name)
    if not names:
        raise ValueError("at least one parameter is required")

    query = urllib.parse.urlencode(
        {
            "start": start.replace("-", ""),
            "end": end.replace("-", ""),
            "latitude": latitude,
            "longitude": longitude,
            "community": community,
            "parameters": ",".join(names),
            "format": "JSON",
            "units": units,
            "time-standard": time_standard,
        }
    )
    return f"{POWER_DAILY_URL}?{query}"


def fetch_power_daily(
    latitude: float,
    longitude: float,
    start_date: str,
    end_date: str,
    parameters: Sequence[str],
    *,
    community: str = COMMUNITY,
    units: str = UNITS,
    time_standard: str = TIME_STANDARD,
    timeout: float = DEFAULT_TIMEOUT_SECONDS,
    max_retries: int = DEFAULT_MAX_RETRIES,
    backoff_seconds: float = DEFAULT_BACKOFF_SECONDS,
    sleep: Callable[[float], None] = time.sleep,
    opener: Callable[..., object] = urllib.request.urlopen,
) -> dict:
    """Fetch and decode a POWER daily point response.

    Retries are bounded to ``max_retries`` additional attempts for HTTP 429,
    HTTP 5xx, and network/timeout failures. HTTP 422 and other 4xx failures
    are raised immediately.
    """
    if max_retries < 0:
        raise ValueError("max_retries must not be negative")
    if not math.isfinite(timeout) or timeout <= 0:
        raise ValueError("timeout must be a positive finite number")
    if not math.isfinite(backoff_seconds) or backoff_seconds < 0:
        raise ValueError("backoff_seconds must be a non-negative finite number")

    url = build_power_url(
        latitude,
        longitude,
        start_date,
        end_date,
        parameters,
        community=community,
        units=units,
        time_standard=time_standard,
    )
    request = urllib.request.Request(
        url, method="GET", headers={"Accept": "application/json"}
    )

    for attempt in range(max_retries + 1):
        try:
            with opener(request, timeout=timeout) as response:
                body = response.read()
        except urllib.error.HTTPError as exc:
            error = PowerApiError(_http_detail(exc), status_code=exc.code)
            retryable = exc.code in RETRYABLE_STATUS_CODES or exc.code >= 500
            if retryable and attempt < max_retries:
                sleep(backoff_seconds * (2**attempt))
                continue
            raise error from None
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            error = PowerApiError(
                f"POWER request failed: {type(exc).__name__}.",
                code="POWER_NETWORK_ERROR",
            )
            if attempt < max_retries:
                sleep(backoff_seconds * (2**attempt))
                continue
            raise error from None

        try:
            payload = json.loads(body.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            raise PowerApiError("POWER returned a response that is not JSON.") from None
        if not isinstance(payload, dict):
            raise PowerApiError("POWER returned a non-object JSON response.")
        return payload

    raise PowerApiError("POWER request failed.")  # pragma: no cover - loop exits


def _number(value: object, field: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise PowerApiError(f"POWER response has a non-numeric {field}.")
    number = float(value)
    if not math.isfinite(number):
        raise PowerApiError(f"POWER response has a non-finite {field}.")
    return number


def _observation_value(value: object, fill_value: float) -> float | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise PowerApiError("POWER response contains a non-numeric observation.")
    number = float(value)
    if not math.isfinite(number):
        return None
    if number == fill_value:
        return None
    return number


def normalize_power_response(
    raw: object,
    retrieved_at: str | None = None,
) -> dict:
    """Validate and normalize a POWER daily point response.

    Observations are keyed by ISO date. Provider fill values, JSON nulls, and
    non-finite numbers become ``None``. Malformed responses raise
    ``PowerApiError``.
    """
    if not isinstance(raw, dict):
        raise PowerApiError("POWER response is not a JSON object.")

    header = raw.get("header")
    if not isinstance(header, dict):
        raise PowerApiError("POWER response is missing header metadata.")
    api = header.get("api")
    if not isinstance(api, dict) or not isinstance(api.get("version"), str):
        raise PowerApiError("POWER response is missing the API version.")
    version = api["version"]
    if not version:
        raise PowerApiError("POWER response has an empty API version.")

    fill_value = _number(header.get("fill_value"), "fill_value")

    properties = raw.get("properties")
    if not isinstance(properties, dict):
        raise PowerApiError("POWER response is missing properties.")
    parameter_values = properties.get("parameter")
    if not isinstance(parameter_values, dict) or not parameter_values:
        raise PowerApiError("POWER response is missing parameter observations.")

    metadata = raw.get("parameters")
    if not isinstance(metadata, dict) or not metadata:
        raise PowerApiError("POWER response is missing parameter metadata.")
    if set(metadata) != set(parameter_values):
        raise PowerApiError(
            "POWER response parameter metadata does not match its observations."
        )

    variables: dict[str, dict[str, str]] = {}
    for name, meta in metadata.items():
        if not isinstance(name, str) or not name or not isinstance(meta, dict):
            raise PowerApiError("POWER response has invalid parameter metadata.")
        units = meta.get("units")
        longname = meta.get("longname")
        if not isinstance(units, str) or not isinstance(longname, str):
            raise PowerApiError(
                f"POWER response is missing units or longname for {name}."
            )
        variables[name] = {"units": units, "longname": longname}

    rows: dict[str, dict[str, float | None]] = {}
    for name, series in parameter_values.items():
        if not isinstance(series, dict):
            raise PowerApiError(f"POWER response observations for {name} are invalid.")
        for date_key, value in series.items():
            iso_date = _power_date(date_key)
            rows.setdefault(iso_date, {})[name] = _observation_value(
                value, fill_value
            )

    if not rows:
        raise PowerApiError("POWER response contains no observations.")

    observations = {
        date: {name: row.get(name) for name in variables}
        for date, row in sorted(rows.items())
    }

    start = header.get("start")
    end = header.get("end")
    if start is None or end is None:
        raise PowerApiError("POWER response is missing its observation range.")
    try:
        observation_start = _power_date(start)
    except PowerApiError:
        raise PowerApiError("POWER header has an invalid start date.") from None
    try:
        observation_end = _power_date(end)
    except PowerApiError:
        raise PowerApiError("POWER header has an invalid end date.") from None
    if observation_start > observation_end:
        raise PowerApiError("POWER header start date is after its end date.")

    messages = raw.get("messages", [])
    if not isinstance(messages, list):
        raise PowerApiError("POWER response messages are not a list.")

    return {
        "product": PRODUCT,
        "product_version": version,
        "provider": PROVIDER,
        "variables": variables,
        "observations": observations,
        "observation_start": observation_start,
        "observation_end": observation_end,
        "fill_value": fill_value,
        "messages": list(messages),
        "spatial_resolution": SPATIAL_RESOLUTION,
        "temporal_resolution": TEMPORAL_RESOLUTION,
        "retrieved_at": retrieved_at
        or dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
    }
