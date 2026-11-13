"""Development HTTP wrapper for the explore engine (v1.md §14.3/§14.5)."""

from __future__ import annotations

import argparse
import datetime as dt
import gzip
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

from src.api import handle_explore
from src.crop_profiles import load_crop_profiles
from src.environment import (
    DEFAULT_POWER_VARIABLES,
    EnvironmentUnavailable,
    load_power_environment,
)
from src.environment_cache import EnvironmentCache
from src.error_contract import build_error_response
from src.request_validation import RequestValidationError, validate_explore_request

PROFILE_FILENAME = "fosol_cycle_rajshahi_crop_dataset.csv"
MAX_BODY_BYTES = 64 * 1024
DEFAULT_DATA_DIR = Path(__file__).resolve().parents[2] / "Data"
DEFAULT_CACHE_DIR = Path(__file__).resolve().parents[2] / ".cache" / "power"
POWER_LATITUDE = 24.3767
POWER_LONGITUDE = 88.6029
POWER_HISTORY_START = "1991-01-01"
POWER_HISTORY_END = "2025-12-31"
POWER_COVERAGE_START = "1981-01-01"
POWER_MAX_PARAMETERS = 20
DEFAULT_CONFIG = {
    "max_initial_wait_days": 180,
    "max_waiting_days": None,
    "analysis_start_year": 1991,
    "analysis_end_year": 2025,
    "max_branches": None,
}


def validate_power_history_request(
    start_date: str, end_date: str, variables: object
) -> list[str]:
    """Validate the documented POWER point request limits before fetching."""
    names = [str(name) for name in variables] if variables else []
    if not names:
        raise ValueError("at least one POWER variable is required")
    if len(names) > POWER_MAX_PARAMETERS:
        raise ValueError(
            "POWER daily point requests allow at most 20 parameters; split the "
            "parameter list before fetching."
        )
    start = dt.date.fromisoformat(start_date)
    end = dt.date.fromisoformat(end_date)
    coverage_start = dt.date.fromisoformat(POWER_COVERAGE_START)
    if start < coverage_start:
        raise ValueError(
            f"POWER daily coverage starts {POWER_COVERAGE_START}; "
            f"requested start is {start_date}."
        )
    if start > end:
        raise ValueError("POWER history start_date must not be after end_date")
    return names


def load_server_power(
    *,
    cache_dir: str | Path | None = None,
    start_date: str = POWER_HISTORY_START,
    end_date: str | None = None,
    variables: object = DEFAULT_POWER_VARIABLES,
    allow_network: bool = True,
    loader=load_power_environment,
    now: dt.datetime | dt.date | None = None,
) -> dict:
    """Load one cached POWER history at server startup.

    The default request is the stable complete comparison period
    1991-01-01..2025-12-31. A date-derived end date would change the cache key
    every day and prevent offline reuse during an outage. Explicit overrides
    remain supported. The full history is loaded once and reused for every
    explore request; the three-variable request is below the 20-parameter limit.
    """
    resolved_end = end_date or POWER_HISTORY_END
    names = validate_power_history_request(
        start_date,
        resolved_end,
        variables,
    )
    cache = EnvironmentCache(cache_dir or DEFAULT_CACHE_DIR)
    kwargs = {
        "latitude": POWER_LATITUDE,
        "longitude": POWER_LONGITUDE,
        "start_date": start_date,
        "end_date": resolved_end,
        "variables": names,
        "allow_network": allow_network,
    }
    if now is not None:
        if isinstance(now, dt.datetime):
            moment = (
                now
                if now.tzinfo is not None
                else now.replace(tzinfo=dt.timezone.utc)
            )
            kwargs["now"] = lambda: moment
        elif isinstance(now, dt.date):
            kwargs["now"] = lambda: dt.datetime.combine(
                now, dt.time.min, dt.timezone.utc
            )
        else:
            raise TypeError("now must be a datetime, date, or None")
    return loader(cache, **kwargs)


class ExploreHandler(BaseHTTPRequestHandler):
    """Small JSON HTTP surface; no provider calls happen here."""

    server_version = "FosolCycle/1"

    def do_GET(self) -> None:
        if self._path() == "/health":
            self._send_json(200, {"status": "ok"})
            return
        self._send_json(404, {"error": "not_found"})

    def do_POST(self) -> None:
        if self._path() != "/api/explore":
            self._send_json(404, {"error": "not_found"})
            return

        content_type = self.headers.get("Content-Type", "").split(";")[0].strip().lower()
        if content_type != "application/json":
            self._send_error(415, "Content-Type must be application/json.")
            return

        raw_length = self.headers.get("Content-Length")
        try:
            length = int(raw_length)
        except (TypeError, ValueError):
            self._send_error(400, "Content-Length is required.")
            return
        if length < 0:
            self._send_error(400, "Content-Length is invalid.")
            return
        if length > MAX_BODY_BYTES:
            self._send_error(413, "Request body is too large.")
            return

        raw = self.rfile.read(length)
        if len(raw) != length:
            self._send_error(400, "Request body is incomplete.")
            return
        try:
            payload = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            self._send_error(400, "Request body must be valid JSON.")
            return
        if not isinstance(payload, dict):
            self._send_error(400, "Request payload must be a JSON object.")
            return

        try:
            validate_explore_request(payload, self.server.profiles)
        except RequestValidationError as exc:
            self._send_json(400, build_error_response(exc))
            return

        status, body = handle_explore(
            payload,
            explore_fn=self.server.explore_fn,
            profiles=self.server.profiles,
            config=self.server.config,
            environment=self.server.environment,
            soil_evidence=self.server.soil_evidence,
            preparation_lookup=self.server.preparation_lookup,
            duration_reference_verified=self.server.duration_reference_verified,
            duration_reference_verified_crop_ids=(
                self.server.duration_reference_verified_crop_ids
            ),
            environment_error=self.server.environment_error,
        )
        self._send_json(status, body)

    def do_OPTIONS(self) -> None:
        if self._path() not in ("/api/explore", "/health"):
            self._send_json(404, {"error": "not_found"})
            return
        origin = self.headers.get("Origin")
        if origin is None:
            self._send_empty(204)
            return
        if origin not in self._allowed_origins():
            self._send_error(403, "CORS origin is not allowed.")
            return
        self._send_empty(204, self._cors_headers(origin))

    def log_message(self, format: str, *args: object) -> None:
        return

    def _path(self) -> str:
        return urlsplit(self.path).path

    def _allowed_origins(self) -> set[str]:
        port = self.server.server_address[1]
        return {
            f"http://localhost:{port}",
            f"http://127.0.0.1:{port}",
        }

    def _cors_headers(self, origin: str | None = None) -> dict[str, str]:
        origin = origin or self.headers.get("Origin")
        if origin not in self._allowed_origins():
            return {}
        return {
            "Access-Control-Allow-Origin": origin,
            "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type",
            "Vary": "Origin",
        }

    def _send_error(self, status: int, message: str) -> None:
        exc = RequestValidationError(message, None)
        self._send_json(status, build_error_response(exc))

    def _send_json(self, status: int, body: object) -> None:
        data = json.dumps(body, ensure_ascii=False, allow_nan=False).encode("utf-8")
        headers = self._cors_headers()
        headers["Vary"] = ", ".join(
            filter(None, (headers.get("Vary"), "Accept-Encoding"))
        )
        if len(data) >= 1024 and self._accepts_gzip():
            compressed = gzip.compress(data, compresslevel=1, mtime=0)
            if len(compressed) < len(data):
                data = compressed
                headers["Content-Encoding"] = "gzip"
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        for name, value in headers.items():
            self.send_header(name, value)
        self.end_headers()
        self.wfile.write(data)

    def _accepts_gzip(self) -> bool:
        qualities = {}
        for entry in self.headers.get("Accept-Encoding", "").lower().split(","):
            name, *parameters = entry.strip().split(";")
            quality = 1.0
            for parameter in parameters:
                key, _, value = parameter.strip().partition("=")
                if key == "q":
                    try:
                        quality = float(value)
                    except ValueError:
                        quality = 0.0
            qualities[name.strip()] = quality if 0 <= quality <= 1 else 0.0
        return qualities.get("gzip", qualities.get("*", 0.0)) > 0

    def _send_empty(self, status: int, headers: dict[str, str] | None = None) -> None:
        self.send_response(status)
        for name, value in (headers or {}).items():
            self.send_header(name, value)
        self.end_headers()


def create_server(
    host: str = "127.0.0.1",
    port: int = 8000,
    data_dir: str | Path | None = None,
    explore_fn=None,
    *,
    environment: dict | None = None,
    cache_dir: str | Path | None = None,
    power_loader=load_server_power,
    allow_network: bool = True,
    power_start_date: str = POWER_HISTORY_START,
    power_end_date: str | None = None,
    soil_evidence: dict | None = None,
    preparation_lookup: object = None,
    duration_reference_verified: bool = False,
    duration_reference_verified_crop_ids: object = None,
    now: dt.datetime | dt.date | None = None,
) -> ThreadingHTTPServer:
    """Build a server from local crop profiles plus cached POWER API history.

    Tests and host applications may inject ``environment`` or ``power_loader``.
    Provider failure is not replaced with the local CSV; it leaves the outlook
    explicitly unavailable and is reported in the response warnings.
    """
    directory = Path(data_dir) if data_dir is not None else DEFAULT_DATA_DIR
    profiles = load_crop_profiles(directory / PROFILE_FILENAME)
    environment_error = None
    if environment is None:
        try:
            environment = power_loader(
                cache_dir=cache_dir,
                start_date=power_start_date,
                end_date=power_end_date,
                allow_network=allow_network,
                now=now,
            )
        except EnvironmentUnavailable as exc:
            environment_error = exc.message
    server = ThreadingHTTPServer((host, port), ExploreHandler)
    server.daemon_threads = True
    server.explore_fn = explore_fn
    server.profiles = profiles
    server.config = dict(DEFAULT_CONFIG)
    server.environment = environment
    server.environment_error = environment_error
    server.soil_evidence = soil_evidence
    server.preparation_lookup = preparation_lookup
    server.duration_reference_verified = duration_reference_verified
    server.duration_reference_verified_crop_ids = (
        duration_reference_verified_crop_ids
    )
    server.data_dir = str(directory)
    return server


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Run the Fosol-Cycle explore API.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--data-dir", default=str(DEFAULT_DATA_DIR))
    args = parser.parse_args(argv)

    server = create_server(args.host, args.port, args.data_dir)
    print(f"Listening on http://{args.host}:{server.server_address[1]}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
