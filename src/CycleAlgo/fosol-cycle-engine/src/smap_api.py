"""NASA SMAP point observations through the AppEEARS API.

The selected product is ``SPL4SMGP.008`` with the two documented soil-moisture
layers. AppEEARS tokens are read from a gitignored local file and are never
printed or included in error messages.
"""

from __future__ import annotations

import csv
import datetime as dt
import io
import json
import math
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from collections.abc import Callable, Sequence
from pathlib import Path

API_BASE = "https://appeears.earthdatacloud.nasa.gov/api"
PRODUCT = "SPL4SMGP"
PRODUCT_VERSION = "008"
PRODUCT_ID = f"{PRODUCT}.{PRODUCT_VERSION}"
PROVIDER = "NASA SMAP via AppEEARS"
SPATIAL_RESOLUTION = "9 km EASE-Grid 2.0"
TEMPORAL_RESOLUTION = "3-hourly"
UNITS = "m^3/m^3"
FILL_VALUE = -9999
LAYER_SURFACE = "Geophysical_Data_sm_surface"
LAYER_ROOTZONE = "Geophysical_Data_sm_rootzone"
DEFAULT_LAYERS = (LAYER_SURFACE, LAYER_ROOTZONE)
LAYER_NAMES = {
    LAYER_SURFACE: "sm_surface",
    LAYER_ROOTZONE: "sm_rootzone",
}

TOKEN_ENV = "APPEARS_TOKEN_FILE"
DEFAULT_TOKEN_PATH = Path(__file__).resolve().parents[2] / "appeears_token.txt"
AUTH_ERROR_MESSAGE = (
    "AppEEARS token expired or invalid; run tools/appeears_login.py"
)

DEFAULT_REQUEST_TIMEOUT_SECONDS = 60.0
DEFAULT_TASK_TIMEOUT_SECONDS = 900.0
DEFAULT_POLL_SECONDS = 10.0
DEFAULT_MAX_RETRIES = 3
DEFAULT_BACKOFF_SECONDS = 1.0

TASK_WAIT_STATUSES = frozenset({"pending", "queued", "processing"})


class AppEEarsError(Exception):
    """An AppEEARS request, task, or response that could not be used."""

    code = "APPEEARS_ERROR"

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


class AppEEarsAuthError(AppEEarsError):
    """Missing, expired, or rejected AppEEARS credentials."""

    code = "APPEEARS_AUTH"


class AppEEarsResponseError(AppEEarsError):
    """A provider response or task result that is not usable."""

    code = "APPEEARS_RESPONSE"


class _TaskComplete(Exception):
    """Internal signal for the documented 303 task-complete redirect."""


def _to_appeears_date(value: object, field: str) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{field} must be a YYYY-MM-DD string")
    try:
        parsed = dt.date.fromisoformat(value)
    except ValueError:
        raise ValueError(f"{field} must be a YYYY-MM-DD string") from None
    if parsed.isoformat() != value:
        raise ValueError(f"{field} must be a YYYY-MM-DD string")
    return parsed.strftime("%m-%d-%Y")


def _coordinate(value: object, field: str, low: float, high: float) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{field} must be a finite number")
    number = float(value)
    if not math.isfinite(number) or not low <= number <= high:
        raise ValueError(f"{field} must be between {low} and {high}")
    return number


def _require_text(value: object, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be a non-empty string")
    return value


def default_point_id(latitude: float, longitude: float) -> str:
    """Return the stable coordinate id used when the caller supplies none."""
    lat = _coordinate(latitude, "latitude", -90.0, 90.0)
    lon = _coordinate(longitude, "longitude", -180.0, 180.0)
    return f"{lat},{lon}"


def resolve_point_id(
    point_id: str | None, latitude: float, longitude: float
) -> str:
    """Return the caller's point id or the stable ``lat,lon`` default."""
    if point_id is None:
        return default_point_id(latitude, longitude)
    return _require_text(point_id, "point_id")


def token_file_path(path: str | Path | None = None) -> Path:
    """Return the explicit path, the env override, or the default token file."""
    if path is not None:
        return Path(path)
    override = os.environ.get(TOKEN_ENV)
    if override:
        return Path(override)
    return DEFAULT_TOKEN_PATH


def _parse_timestamp(value: object) -> dt.datetime | None:
    if not isinstance(value, str) or not value.strip():
        return None
    text = value.strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        parsed = dt.datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=dt.timezone.utc)
    return parsed


def load_token(
    path: str | Path | None = None,
    *,
    now: dt.datetime | None = None,
) -> str:
    """Load the AppEEARS token from the documented local JSON file.

    A known expired token raises ``AppEEarsAuthError`` before any request.
    The token value is never included in an error message.
    """
    token_path = token_file_path(path)
    try:
        payload = json.loads(token_path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise AppEEarsAuthError(
            "AppEEARS token file not found; run tools/appeears_login.py"
        ) from None
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        raise AppEEarsAuthError(
            "AppEEARS token file is unreadable; run tools/appeears_login.py"
        ) from None

    if not isinstance(payload, dict):
        raise AppEEarsAuthError(
            "AppEEARS token file has an invalid shape; run tools/appeears_login.py"
        )
    token = payload.get("token")
    if not isinstance(token, str) or not token.strip():
        raise AppEEarsAuthError(
            "AppEEARS token file has no token; run tools/appeears_login.py"
        )

    expiration = _parse_timestamp(payload.get("expiration"))
    if expiration is not None:
        current = now or dt.datetime.now(dt.timezone.utc)
        if current.tzinfo is None:
            current = current.replace(tzinfo=dt.timezone.utc)
        if expiration <= current:
            raise AppEEarsAuthError(AUTH_ERROR_MESSAGE)

    return token.strip()


def _error_detail(exc: urllib.error.HTTPError) -> str:
    detail = ""
    try:
        payload = json.loads(exc.read().decode("utf-8"))
    except Exception:  # noqa: BLE001 - error bodies are best effort
        payload = None
    if isinstance(payload, dict):
        message = payload.get("message")
        if isinstance(message, str) and message:
            detail = message
        else:
            errors = payload.get("errors")
            if isinstance(errors, list):
                detail = "; ".join(str(item) for item in errors if item)
    suffix = f" {detail}" if detail else ""
    return f"AppEEARS returned HTTP {exc.code}.{suffix}"


def _retryable_http(method: str, status_code: int) -> bool:
    """GETs retry 429/5xx; task submission retries 429/503 only."""
    if status_code == 429:
        return True
    if method == "GET":
        return 500 <= status_code <= 599
    return status_code == 503


def _open_bytes(
    request: urllib.request.Request,
    *,
    method: str,
    timeout: float,
    opener: Callable[..., object],
    allow_303: bool,
    max_retries: int = DEFAULT_MAX_RETRIES,
    backoff_seconds: float = DEFAULT_BACKOFF_SECONDS,
    sleep: Callable[[float], None] = time.sleep,
) -> bytes:
    if (
        isinstance(max_retries, bool)
        or not isinstance(max_retries, int)
        or max_retries < 0
    ):
        raise ValueError("max_retries must be a non-negative integer")
    if (
        isinstance(backoff_seconds, bool)
        or not isinstance(backoff_seconds, (int, float))
        or not math.isfinite(backoff_seconds)
        or backoff_seconds < 0
    ):
        raise ValueError("backoff_seconds must be a non-negative finite number")

    for attempt in range(max_retries + 1):
        try:
            with opener(request, timeout=timeout) as response:
                return response.read()
        except urllib.error.HTTPError as exc:
            if exc.code == 303 and allow_303:
                raise _TaskComplete from None
            if exc.code in (401, 403):
                raise AppEEarsAuthError(AUTH_ERROR_MESSAGE) from None
            if _retryable_http(method, exc.code) and attempt < max_retries:
                exc.close()
                sleep(backoff_seconds * (2**attempt))
                continue
            raise AppEEarsResponseError(
                _error_detail(exc), status_code=exc.code
            ) from None
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            if method == "GET" and attempt < max_retries:
                sleep(backoff_seconds * (2**attempt))
                continue
            raise AppEEarsError(
                f"AppEEARS request failed: {type(exc).__name__}.",
                code="APPEEARS_NETWORK_ERROR",
            ) from None

    raise AppEEarsError("AppEEARS request failed.")  # pragma: no cover


def _request_json(
    method: str,
    url: str,
    token: str,
    *,
    body: dict | None = None,
    timeout: float = DEFAULT_REQUEST_TIMEOUT_SECONDS,
    opener: Callable[..., object] = urllib.request.urlopen,
    allow_303: bool = False,
    max_retries: int = DEFAULT_MAX_RETRIES,
    backoff_seconds: float = DEFAULT_BACKOFF_SECONDS,
    sleep: Callable[[float], None] = time.sleep,
) -> dict:
    if not math.isfinite(timeout) or timeout <= 0:
        raise ValueError("timeout must be a positive finite number")

    headers = {"Accept": "application/json"}
    data: bytes | None = None
    if token:
        headers["Authorization"] = f"Bearer {token}"
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        headers["Content-Type"] = "application/json"

    request = urllib.request.Request(url, data=data, method=method, headers=headers)
    raw = _open_bytes(
        request,
        method=method,
        timeout=timeout,
        opener=opener,
        allow_303=allow_303,
        max_retries=max_retries,
        backoff_seconds=backoff_seconds,
        sleep=sleep,
    )
    try:
        payload = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        raise AppEEarsResponseError("AppEEARS returned a response that is not JSON.") from None
    if not isinstance(payload, dict):
        raise AppEEarsResponseError("AppEEARS returned a non-object JSON response.")
    return payload


def _request_bytes(
    url: str,
    token: str,
    *,
    timeout: float = DEFAULT_REQUEST_TIMEOUT_SECONDS,
    opener: Callable[..., object] = urllib.request.urlopen,
    max_retries: int = DEFAULT_MAX_RETRIES,
    backoff_seconds: float = DEFAULT_BACKOFF_SECONDS,
    sleep: Callable[[float], None] = time.sleep,
) -> bytes:
    if not math.isfinite(timeout) or timeout <= 0:
        raise ValueError("timeout must be a positive finite number")
    headers = {"Accept": "text/csv, application/octet-stream"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = urllib.request.Request(url, method="GET", headers=headers)
    return _open_bytes(
        request,
        method="GET",
        timeout=timeout,
        opener=opener,
        allow_303=False,
        max_retries=max_retries,
        backoff_seconds=backoff_seconds,
        sleep=sleep,
    )


def submit_point_task(
    token: str,
    *,
    task_name: str,
    latitude: float,
    longitude: float,
    point_id: str | None = None,
    start_date: str,
    end_date: str,
    timeout: float = DEFAULT_REQUEST_TIMEOUT_SECONDS,
    opener: Callable[..., object] = urllib.request.urlopen,
    max_retries: int = DEFAULT_MAX_RETRIES,
    backoff_seconds: float = DEFAULT_BACKOFF_SECONDS,
    sleep: Callable[[float], None] = time.sleep,
) -> dict:
    """Submit the documented SPL4SMGP.008 point task and return its ID."""
    _require_text(token, "token")
    _require_text(task_name, "task_name")
    lat = _coordinate(latitude, "latitude", -90.0, 90.0)
    lon = _coordinate(longitude, "longitude", -180.0, 180.0)
    resolved_point_id = resolve_point_id(point_id, lat, lon)
    start = _to_appeears_date(start_date, "start_date")
    end = _to_appeears_date(end_date, "end_date")
    if dt.datetime.strptime(start, "%m-%d-%Y") > dt.datetime.strptime(
        end, "%m-%d-%Y"
    ):
        raise ValueError("start_date must not be after end_date")

    body = {
        "task_name": task_name,
        "task_type": "point",
        "params": {
            "dates": [{"startDate": start, "endDate": end}],
            "layers": [
                {"product": PRODUCT_ID, "layer": layer}
                for layer in DEFAULT_LAYERS
            ],
            "coordinates": [
                {"id": resolved_point_id, "latitude": lat, "longitude": lon}
            ],
        },
    }
    try:
        payload = _request_json(
            "POST",
            f"{API_BASE}/task",
            token,
            body=body,
            timeout=timeout,
            opener=opener,
            max_retries=max_retries,
            backoff_seconds=backoff_seconds,
            sleep=sleep,
        )
    except _TaskComplete:
        raise AppEEarsResponseError(
            "AppEEARS returned an unexpected redirect for task submission."
        ) from None

    task_id = payload.get("task_id")
    if not isinstance(task_id, str) or not task_id:
        raise AppEEarsResponseError("AppEEARS task response has no task_id.")
    status = payload.get("status")
    return {"status": status if isinstance(status, str) else None, "task_id": task_id}


def wait_for_task(
    token: str,
    task_id: str,
    *,
    timeout_seconds: float = DEFAULT_TASK_TIMEOUT_SECONDS,
    poll_seconds: float = DEFAULT_POLL_SECONDS,
    request_timeout: float = DEFAULT_REQUEST_TIMEOUT_SECONDS,
    max_retries: int = DEFAULT_MAX_RETRIES,
    backoff_seconds: float = DEFAULT_BACKOFF_SECONDS,
    sleep: Callable[[float], None] = time.sleep,
    clock: Callable[[], float] = time.monotonic,
    opener: Callable[..., object] = urllib.request.urlopen,
) -> dict:
    """Poll a task until ``done``, honouring the documented 303 completion.

    Timeouts and task ``error`` statuses raise typed ``AppEEarsError`` values.
    """
    _require_text(token, "token")
    _require_text(task_id, "task_id")
    if not math.isfinite(timeout_seconds) or timeout_seconds <= 0:
        raise ValueError("timeout_seconds must be a positive finite number")
    if not math.isfinite(poll_seconds) or poll_seconds <= 0:
        raise ValueError("poll_seconds must be a positive finite number")

    started = clock()
    while True:
        elapsed = clock() - started
        if elapsed >= timeout_seconds:
            raise AppEEarsError(
                f"AppEEARS task {task_id} did not finish within the timeout.",
                code="APPEEARS_TIMEOUT",
            )
        try:
            payload = _request_json(
                "GET",
                f"{API_BASE}/task/{task_id}",
                token,
                timeout=request_timeout,
                opener=opener,
                allow_303=True,
                max_retries=max_retries,
                backoff_seconds=backoff_seconds,
                sleep=sleep,
            )
        except _TaskComplete:
            return {"task_id": task_id, "status": "done"}

        status = payload.get("status")
        if status == "done":
            return payload
        if status == "error":
            message = payload.get("message")
            detail = f": {message}" if isinstance(message, str) and message else "."
            raise AppEEarsResponseError(
                f"AppEEARS task {task_id} failed{detail}",
                code="APPEEARS_TASK_ERROR",
            )
        if status not in TASK_WAIT_STATUSES:
            raise AppEEarsResponseError(
                f"AppEEARS task {task_id} reported an unknown status.",
                code="APPEEARS_TASK_STATUS",
            )

        elapsed = clock() - started
        remaining = timeout_seconds - elapsed
        if remaining <= 0:
            raise AppEEarsError(
                f"AppEEARS task {task_id} did not finish within the timeout.",
                code="APPEEARS_TIMEOUT",
            )
        sleep(min(poll_seconds, remaining))


def get_bundle(
    token: str,
    task_id: str,
    *,
    timeout: float = DEFAULT_REQUEST_TIMEOUT_SECONDS,
    opener: Callable[..., object] = urllib.request.urlopen,
    max_retries: int = DEFAULT_MAX_RETRIES,
    backoff_seconds: float = DEFAULT_BACKOFF_SECONDS,
    sleep: Callable[[float], None] = time.sleep,
) -> list[dict]:
    """Return the bundle's file entries for a completed task."""
    _require_text(token, "token")
    _require_text(task_id, "task_id")
    try:
        payload = _request_json(
            "GET",
            f"{API_BASE}/bundle/{task_id}",
            token,
            timeout=timeout,
            opener=opener,
            max_retries=max_retries,
            backoff_seconds=backoff_seconds,
            sleep=sleep,
        )
    except _TaskComplete:
        raise AppEEarsResponseError(
            "AppEEARS returned an unexpected redirect for the bundle."
        ) from None

    files = payload.get("files")
    if not isinstance(files, list):
        raise AppEEarsResponseError("AppEEARS bundle response has no files list.")
    entries: list[dict] = []
    for entry in files:
        if not isinstance(entry, dict):
            raise AppEEarsResponseError("AppEEARS bundle contains an invalid file entry.")
        file_id = entry.get("file_id")
        file_name = entry.get("file_name")
        file_type = entry.get("file_type")
        if not isinstance(file_id, str) or not file_id:
            raise AppEEarsResponseError("AppEEARS bundle entry has no file_id.")
        if not isinstance(file_name, str) or not file_name:
            raise AppEEarsResponseError("AppEEARS bundle entry has no file_name.")
        if not isinstance(file_type, str) or not file_type:
            raise AppEEarsResponseError("AppEEARS bundle entry has no file_type.")
        entries.append(
            {"file_id": file_id, "file_name": file_name, "file_type": file_type}
        )
    return entries


def select_result_file(files: Sequence[dict]) -> dict:
    """Select the results CSV, never the statistics CSV."""
    csv_files = [
        entry
        for entry in files
        if isinstance(entry.get("file_type"), str)
        and entry["file_type"].lower() == "csv"
    ]
    results = [
        entry
        for entry in csv_files
        if "results" in entry["file_name"].lower()
    ]
    if len(results) == 1:
        return results[0]
    if len(results) > 1:
        raise AppEEarsResponseError("AppEEARS bundle contains multiple results CSVs.")
    raise AppEEarsResponseError("AppEEARS bundle contains no usable results CSV.")


def download_result_csv(
    token: str,
    task_id: str,
    file_id: str,
    *,
    timeout: float = DEFAULT_REQUEST_TIMEOUT_SECONDS,
    opener: Callable[..., object] = urllib.request.urlopen,
    max_retries: int = DEFAULT_MAX_RETRIES,
    backoff_seconds: float = DEFAULT_BACKOFF_SECONDS,
    sleep: Callable[[float], None] = time.sleep,
) -> str:
    """Download and decode a bundle CSV (urllib follows the S3 redirect)."""
    _require_text(token, "token")
    _require_text(task_id, "task_id")
    _require_text(file_id, "file_id")
    url = (
        f"{API_BASE}/bundle/{urllib.parse.quote(task_id, safe='')}/"
        f"{urllib.parse.quote(file_id, safe='')}"
    )
    raw = _request_bytes(
        url,
        token,
        timeout=timeout,
        opener=opener,
        max_retries=max_retries,
        backoff_seconds=backoff_seconds,
        sleep=sleep,
    )
    try:
        return raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        raise AppEEarsResponseError("AppEEARS results file is not UTF-8 text.") from None


def _csv_value(text: object) -> float | None:
    if text is None:
        return None
    stripped = str(text).strip()
    if not stripped:
        return None
    try:
        value = float(stripped)
    except ValueError:
        raise AppEEarsResponseError(
            "AppEEARS results contain a non-numeric soil-moisture value."
        ) from None
    if not math.isfinite(value):
        return None
    if value == FILL_VALUE:
        return None
    return value


def _parse_observation_date(text: object) -> dt.datetime:
    if not isinstance(text, str) or not text.strip():
        raise AppEEarsResponseError("AppEEARS results contain an empty Date value.")
    try:
        return dt.datetime.strptime(
            text.strip(), "%Y-%m-%d %H:%M:%S UTC"
        ).replace(tzinfo=dt.timezone.utc)
    except ValueError:
        raise AppEEarsResponseError(
            "AppEEARS results contain an invalid UTC timestamp."
        ) from None


def parse_appeears_csv(csv_text: str, retrieved_at: str | None = None) -> dict:
    """Parse the real AppEEARS point-results CSV for SPL4SMGP.008.

    ``-9999``, empty cells, and non-finite numbers become ``None``. The
    returned observations are sorted by ISO UTC timestamp.
    """
    if not isinstance(csv_text, str) or not csv_text.strip():
        raise AppEEarsResponseError("AppEEARS results CSV is empty.")

    reader = csv.DictReader(io.StringIO(csv_text.lstrip("\ufeff")))
    fieldnames = reader.fieldnames or []
    expected_columns = {
        layer: f"{PRODUCT}_{PRODUCT_VERSION}_{layer}"
        for layer in DEFAULT_LAYERS
    }
    for layer, column in expected_columns.items():
        if column not in fieldnames:
            raise AppEEarsResponseError(
                f"AppEEARS results CSV is missing the {layer} column."
            )
    for column in ("ID", "Latitude", "Longitude", "Date"):
        if column not in fieldnames:
            raise AppEEarsResponseError(
                f"AppEEARS results CSV is missing the {column} column."
            )

    try:
        rows = list(reader)
    except csv.Error:
        raise AppEEarsResponseError("AppEEARS results CSV is malformed.") from None
    if not rows:
        raise AppEEarsResponseError("AppEEARS results CSV contains no observations.")

    point_id = ""
    latitude: float | None = None
    longitude: float | None = None
    unique: dict[str, dict] = {}
    duplicate_timestamps = 0

    for row in rows:
        row_id = row.get("ID")
        if not isinstance(row_id, str) or not row_id.strip():
            raise AppEEarsResponseError("AppEEARS results contain an empty ID.")
        row_id = row_id.strip()
        try:
            row_latitude = float(row.get("Latitude", ""))
            row_longitude = float(row.get("Longitude", ""))
        except (TypeError, ValueError):
            raise AppEEarsResponseError(
                "AppEEARS results contain invalid coordinates."
            ) from None
        if not math.isfinite(row_latitude) or not math.isfinite(row_longitude):
            raise AppEEarsResponseError(
                "AppEEARS results contain invalid coordinates."
            )

        if latitude is None:
            point_id = row_id
            latitude = row_latitude
            longitude = row_longitude
        elif (
            row_id != point_id
            or abs(row_latitude - latitude) > 1e-6
            or abs(row_longitude - longitude) > 1e-6
        ):
            raise AppEEarsResponseError(
                "AppEEARS results contain more than one point."
            )

        timestamp = _parse_observation_date(row.get("Date")).isoformat()
        observation = {"timestamp": timestamp}
        for layer in DEFAULT_LAYERS:
            observation[LAYER_NAMES[layer]] = _csv_value(
                row.get(expected_columns[layer])
            )

        if timestamp not in unique:
            unique[timestamp] = observation
        elif unique[timestamp] == observation:
            duplicate_timestamps += 1
        else:
            raise AppEEarsResponseError(
                "AppEEARS results contain conflicting values for timestamp "
                f"{timestamp}."
            )

    observations = [unique[key] for key in sorted(unique)]
    missing_counts = {
        LAYER_NAMES[layer]: sum(
            1 for observation in observations
            if observation[LAYER_NAMES[layer]] is None
        )
        for layer in DEFAULT_LAYERS
    }

    return {
        "product": PRODUCT,
        "product_version": PRODUCT_VERSION,
        "provider": PROVIDER,
        "variables": {
            LAYER_NAMES[layer]: {"units": UNITS, "layer": layer}
            for layer in DEFAULT_LAYERS
        },
        "observations": observations,
        "observation_start": observations[0]["timestamp"],
        "observation_end": observations[-1]["timestamp"],
        "point": {
            "id": point_id,
            "latitude": latitude,
            "longitude": longitude,
        },
        "missing_counts": missing_counts,
        "duplicate_timestamps": duplicate_timestamps,
        "fill_value": FILL_VALUE,
        "spatial_resolution": SPATIAL_RESOLUTION,
        "temporal_resolution": TEMPORAL_RESOLUTION,
        "retrieved_at": retrieved_at
        or dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
    }


def fetch_smap_point(
    latitude: float,
    longitude: float,
    start_date: str,
    end_date: str,
    *,
    point_id: str | None = None,
    token: str | None = None,
    token_path: str | Path | None = None,
    task_name: str | None = None,
    task_timeout_seconds: float = DEFAULT_TASK_TIMEOUT_SECONDS,
    poll_seconds: float = DEFAULT_POLL_SECONDS,
    request_timeout: float = DEFAULT_REQUEST_TIMEOUT_SECONDS,
    max_retries: int = DEFAULT_MAX_RETRIES,
    backoff_seconds: float = DEFAULT_BACKOFF_SECONDS,
    sleep: Callable[[float], None] = time.sleep,
    clock: Callable[[], float] = time.monotonic,
    opener: Callable[..., object] = urllib.request.urlopen,
) -> dict:
    """Run the full submit -> wait -> bundle -> download -> parse flow."""
    auth_token = token if token is not None else load_token(token_path)
    resolved_point_id = resolve_point_id(point_id, latitude, longitude)
    name = task_name or f"fosol-{resolved_point_id}-{start_date}-{end_date}"

    submitted = submit_point_task(
        auth_token,
        task_name=name,
        latitude=latitude,
        longitude=longitude,
        point_id=resolved_point_id,
        start_date=start_date,
        end_date=end_date,
        timeout=request_timeout,
        opener=opener,
        max_retries=max_retries,
        backoff_seconds=backoff_seconds,
        sleep=sleep,
    )
    task_id = submitted["task_id"]
    wait_for_task(
        auth_token,
        task_id,
        timeout_seconds=task_timeout_seconds,
        poll_seconds=poll_seconds,
        request_timeout=request_timeout,
        max_retries=max_retries,
        backoff_seconds=backoff_seconds,
        sleep=sleep,
        clock=clock,
        opener=opener,
    )
    files = get_bundle(
        auth_token,
        task_id,
        timeout=request_timeout,
        opener=opener,
        max_retries=max_retries,
        backoff_seconds=backoff_seconds,
        sleep=sleep,
    )
    entry = select_result_file(files)
    csv_text = download_result_csv(
        auth_token,
        task_id,
        entry["file_id"],
        timeout=request_timeout,
        opener=opener,
        max_retries=max_retries,
        backoff_seconds=backoff_seconds,
        sleep=sleep,
    )
    result = parse_appeears_csv(csv_text)
    result["task_id"] = task_id
    return result
