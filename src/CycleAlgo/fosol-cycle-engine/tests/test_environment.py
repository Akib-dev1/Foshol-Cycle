"""Tests for §15 environmental loading, caching, and missing-value handling."""

import datetime as dt
import io
import json
import os
import tempfile
import unittest
import urllib.error
from pathlib import Path
from unittest import mock

from src.environment import (
    EnvironmentUnavailable,
    load_environment,
    load_power_environment,
    load_smap_environment,
)
from src.environment_cache import EnvironmentCache, build_cache_key
from src.power_api import (
    PowerApiError,
    build_power_url,
    fetch_power_daily,
    normalize_power_response,
)
from src.smap_api import (
    API_BASE,
    AUTH_ERROR_MESSAGE,
    DEFAULT_LAYERS,
    AppEEarsAuthError,
    AppEEarsError,
    AppEEarsResponseError,
    download_result_csv,
    fetch_smap_point,
    get_bundle,
    load_token,
    parse_appeears_csv,
    select_result_file,
    submit_point_task,
    wait_for_task,
)

FIXTURES = Path(__file__).resolve().parent / "fixtures"
POWER_REAL = FIXTURES / "power_daily_rajshahi_20250101_20250103.json"
POWER_SYNTHETIC = FIXTURES / "power_daily_synthetic_missing.json"
SMAP_REAL = (
    FIXTURES / "appeears_spl4smgp_rajshahi_20250101_20250103.csv"
)
SMAP_SYNTHETIC = FIXTURES / "appeears_spl4smgp_synthetic_missing.csv"

T0 = dt.datetime(2026, 11, 6, 12, 0, tzinfo=dt.timezone.utc)


class FakeResponse:
    def __init__(self, payload: bytes | str) -> None:
        self.payload = payload.encode("utf-8") if isinstance(payload, str) else payload

    def read(self) -> bytes:
        return self.payload

    def __enter__(self) -> "FakeResponse":
        return self

    def __exit__(self, *exc_info: object) -> bool:
        return False


class SequenceOpener:
    """Fake urllib opener returning queued responses or raising queued errors."""

    def __init__(self, items: list[object]) -> None:
        self.items = list(items)
        self.requests = []

    def __call__(self, request: object, timeout: float | None = None) -> FakeResponse:
        self.requests.append(request)
        if not self.items:
            raise AssertionError("fake opener received an unexpected request")
        item = self.items.pop(0)
        if isinstance(item, BaseException):
            raise item
        if isinstance(item, bytes):
            return FakeResponse(item)
        if isinstance(item, str):
            return FakeResponse(item)
        return FakeResponse(json.dumps(item))


def http_error(code: int, body: bytes = b"") -> urllib.error.HTTPError:
    return urllib.error.HTTPError(
        "https://example.invalid", code, "error", {}, io.BytesIO(body)
    )


def real_power_raw() -> dict:
    return json.loads(POWER_REAL.read_text(encoding="utf-8"))


def real_smap_text() -> str:
    return SMAP_REAL.read_text(encoding="utf-8")


class PowerNormalizeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.raw = real_power_raw()

    def test_real_fixture_is_normalized(self) -> None:
        result = normalize_power_response(
            self.raw, retrieved_at="2026-11-06T12:00:00+00:00"
        )
        self.assertEqual(result["product"], "NASA POWER Daily Point")
        self.assertEqual(result["product_version"], "v2.10.3")
        self.assertEqual(result["provider"], "NASA POWER")
        self.assertEqual(result["observation_start"], "2025-01-01")
        self.assertEqual(result["observation_end"], "2025-01-03")
        self.assertEqual(result["fill_value"], -999.0)
        self.assertEqual(
            result["spatial_resolution"],
            "0.5 x 0.625 degree lat/lon region (MERRA-2)",
        )
        self.assertEqual(result["temporal_resolution"], "daily")
        self.assertEqual(result["retrieved_at"], "2026-11-06T12:00:00+00:00")
        self.assertEqual(
            result["variables"]["T2M"],
            {"units": "C", "longname": "Temperature at 2 Meters"},
        )
        self.assertEqual(result["variables"]["PRECTOTCORR"]["units"], "mm/day")
        self.assertEqual(result["observations"]["2025-01-01"]["T2M"], 15.21)
        self.assertEqual(result["observations"]["2025-01-02"]["T2M"], 14.87)
        self.assertEqual(result["observations"]["2025-01-03"]["GWETTOP"], 0.7)
        self.assertEqual(result["messages"], [])

    def test_fill_value_is_none_not_zero(self) -> None:
        raw = json.loads(POWER_SYNTHETIC.read_text(encoding="utf-8"))
        result = normalize_power_response(raw)
        self.assertIsNone(result["observations"]["2025-01-01"]["T2M"])
        self.assertIsNone(result["observations"]["2025-01-02"]["T2M"])
        self.assertIsNone(result["observations"]["2025-01-01"]["GWETTOP"])
        self.assertIsNone(result["observations"]["2025-01-02"]["GWETTOP"])
        self.assertEqual(result["observations"]["2025-01-01"]["PRECTOTCORR"], 0.0)
        self.assertEqual(result["observations"]["2025-01-02"]["PRECTOTCORR"], 1.5)

    def test_non_finite_values_become_none(self) -> None:
        raw = real_power_raw()
        raw["properties"]["parameter"]["T2M"]["20250101"] = float("nan")
        raw["properties"]["parameter"]["T2M"]["20250102"] = float("inf")
        result = normalize_power_response(raw)
        self.assertIsNone(result["observations"]["2025-01-01"]["T2M"])
        self.assertIsNone(result["observations"]["2025-01-02"]["T2M"])

    def test_malformed_responses_are_rejected(self) -> None:
        cases = []
        cases.append(("not an object", []))
        cases.append(("no header", {"properties": {"parameter": {"T2M": {}}}}))
        bad = real_power_raw()
        bad["parameters"] = {}
        cases.append(("no metadata", bad))
        bad = real_power_raw()
        bad["properties"]["parameter"]["T2M"]["2025-01-01"] = "warm"
        cases.append(("non-numeric", bad))
        bad = real_power_raw()
        bad["properties"]["parameter"]["T2M"] = {"2025-02-30": 1.0}
        cases.append(("bad date", bad))
        bad = real_power_raw()
        del bad["header"]["fill_value"]
        cases.append(("no fill value", bad))
        bad = real_power_raw()
        del bad["header"]["start"]
        cases.append(("no observation start", bad))

        for label, raw in cases:
            with self.subTest(label=label):
                with self.assertRaises(PowerApiError):
                    normalize_power_response(raw)

    def test_response_is_json_serializable(self) -> None:
        result = normalize_power_response(real_power_raw(), retrieved_at=T0.isoformat())
        json.dumps(result, allow_nan=False)


class PowerFetchTests(unittest.TestCase):
    def test_build_url_uses_documented_query(self) -> None:
        url = build_power_url(
            24.3767, 88.6029, "2025-01-01", "2025-01-03", ["T2M", "GWETTOP"]
        )
        self.assertIn("start=20250101", url)
        self.assertIn("end=20250103", url)
        self.assertIn("latitude=24.3767", url)
        self.assertIn("community=AG", url)
        self.assertIn("parameters=T2M%2CGWETTOP", url)
        self.assertIn("time-standard=LST", url)
        self.assertIn("units=metric", url)

    def test_retries_429_then_succeeds(self) -> None:
        opener = SequenceOpener([http_error(429), POWER_REAL.read_bytes()])
        sleeps: list[float] = []
        result = fetch_power_daily(
            24.3767,
            88.6029,
            "2025-01-01",
            "2025-01-03",
            ["T2M", "PRECTOTCORR", "GWETTOP"],
            max_retries=2,
            sleep=sleeps.append,
            opener=opener,
        )
        self.assertEqual(len(opener.requests), 2)
        self.assertEqual(len(sleeps), 1)
        self.assertIn("properties", result)

    def test_retries_network_failure_then_succeeds(self) -> None:
        opener = SequenceOpener(
            [urllib.error.URLError("offline"), POWER_REAL.read_bytes()]
        )
        fetcher_result = fetch_power_daily(
            24.3767,
            88.6029,
            "2025-01-01",
            "2025-01-03",
            ["T2M"],
            max_retries=1,
            sleep=lambda seconds: None,
            opener=opener,
        )
        self.assertEqual(len(opener.requests), 2)
        self.assertIn("header", fetcher_result)

    def test_retries_5xx_then_succeeds(self) -> None:
        opener = SequenceOpener([http_error(503), POWER_REAL.read_bytes()])
        result = fetch_power_daily(
            24.3767,
            88.6029,
            "2025-01-01",
            "2025-01-03",
            ["T2M"],
            max_retries=1,
            sleep=lambda seconds: None,
            opener=opener,
        )
        self.assertEqual(len(opener.requests), 2)
        self.assertIn("properties", result)

    def test_422_is_not_retried(self) -> None:
        opener = SequenceOpener([http_error(422, b'{"messages":["bad range"]}')])
        sleeps: list[float] = []
        with self.assertRaises(PowerApiError) as caught:
            fetch_power_daily(
                24.3767,
                88.6029,
                "2025-01-01",
                "2025-01-03",
                ["T2M"],
                max_retries=3,
                sleep=sleeps.append,
                opener=opener,
            )
        self.assertEqual(caught.exception.status_code, 422)
        self.assertEqual(len(opener.requests), 1)
        self.assertEqual(sleeps, [])


class SmapRequestTests(unittest.TestCase):
    TOKEN = "test-token-never-real"

    def test_submit_body_dates_and_coordinates_are_exact(self) -> None:
        opener = SequenceOpener([{"status": "pending", "task_id": "task-1"}])
        result = submit_point_task(
            self.TOKEN,
            task_name="fosol-test",
            latitude=24.3767,
            longitude=88.6029,
            point_id="rajshahi",
            start_date="2025-01-01",
            end_date="2025-01-03",
            opener=opener,
        )
        self.assertEqual(result, {"status": "pending", "task_id": "task-1"})
        request = opener.requests[0]
        self.assertEqual(request.full_url, f"{API_BASE}/task")
        self.assertEqual(request.get_method(), "POST")
        self.assertEqual(request.get_header("Authorization"), f"Bearer {self.TOKEN}")
        self.assertEqual(
            json.loads(request.data),
            {
                "task_name": "fosol-test",
                "task_type": "point",
                "params": {
                    "dates": [
                        {"startDate": "01-01-2025", "endDate": "01-03-2025"}
                    ],
                    "layers": [
                        {
                            "product": "SPL4SMGP.008",
                            "layer": "Geophysical_Data_sm_surface",
                        },
                        {
                            "product": "SPL4SMGP.008",
                            "layer": "Geophysical_Data_sm_rootzone",
                        },
                    ],
                    "coordinates": [
                        {
                            "id": "rajshahi",
                            "latitude": 24.3767,
                            "longitude": 88.6029,
                        }
                    ],
                },
            },
        )

    def test_submit_defaults_point_id_to_coordinates(self) -> None:
        opener = SequenceOpener([{"status": "pending", "task_id": "task-1"}])
        submit_point_task(
            self.TOKEN,
            task_name="fosol-test",
            latitude=24.3767,
            longitude=88.6029,
            point_id=None,
            start_date="2025-01-01",
            end_date="2025-01-03",
            opener=opener,
        )
        body = json.loads(opener.requests[0].data)
        self.assertEqual(
            body["params"]["coordinates"][0]["id"], "24.3767,88.6029"
        )

    def test_poll_queued_processing_done(self) -> None:
        opener = SequenceOpener(
            [
                {"status": "queued"},
                {"status": "processing"},
                {"status": "done", "task_id": "task-1"},
            ]
        )
        result = wait_for_task(
            self.TOKEN,
            "task-1",
            timeout_seconds=60,
            poll_seconds=1,
            sleep=lambda seconds: None,
            clock=lambda: 0.0,
            opener=opener,
        )
        self.assertEqual(result["status"], "done")
        self.assertEqual(len(opener.requests), 3)
        self.assertEqual(
            opener.requests[0].full_url, f"{API_BASE}/task/task-1"
        )

    def test_303_means_done(self) -> None:
        opener = SequenceOpener([http_error(303)])
        result = wait_for_task(
            self.TOKEN,
            "task-1",
            sleep=lambda seconds: None,
            clock=lambda: 0.0,
            opener=opener,
        )
        self.assertEqual(result, {"task_id": "task-1", "status": "done"})

    def test_error_status_raises(self) -> None:
        opener = SequenceOpener([{"status": "error", "message": "bad task"}])
        with self.assertRaises(AppEEarsResponseError) as caught:
            wait_for_task(
                self.TOKEN,
                "task-1",
                sleep=lambda seconds: None,
                clock=lambda: 0.0,
                opener=opener,
            )
        self.assertEqual(caught.exception.code, "APPEEARS_TASK_ERROR")
        self.assertIn("bad task", str(caught.exception))

    def test_timeout_is_bounded(self) -> None:
        opener = SequenceOpener([{"status": "processing"}] * 20)
        now = [0.0]

        def clock() -> float:
            return now[0]

        def sleep(seconds: float) -> None:
            now[0] += seconds

        with self.assertRaises(AppEEarsError) as caught:
            wait_for_task(
                self.TOKEN,
                "task-1",
                timeout_seconds=5,
                poll_seconds=2,
                sleep=sleep,
                clock=clock,
                opener=opener,
            )
        self.assertEqual(caught.exception.code, "APPEEARS_TIMEOUT")
        self.assertEqual(len(opener.requests), 3)

    def test_403_reports_expired_or_invalid_token(self) -> None:
        opener = SequenceOpener([http_error(403)])
        with self.assertRaises(AppEEarsAuthError) as caught:
            submit_point_task(
                self.TOKEN,
                task_name="fosol-test",
                latitude=24.3767,
                longitude=88.6029,
                point_id="rajshahi",
                start_date="2025-01-01",
                end_date="2025-01-03",
                opener=opener,
            )
        self.assertEqual(caught.exception.message, AUTH_ERROR_MESSAGE)
        self.assertNotIn(self.TOKEN, str(caught.exception))

    def test_bundle_picks_results_csv(self) -> None:
        files = [
            {
                "file_id": "stats",
                "file_name": "fosol-test-statistics.csv",
                "file_type": "csv",
            },
            {
                "file_id": "results",
                "file_name": "fosol-test-results.csv",
                "file_type": "csv",
            },
            {
                "file_id": "meta",
                "file_name": "fosol-test-metadata.json",
                "file_type": "json",
            },
        ]
        opener = SequenceOpener([{"files": files}])
        bundle = get_bundle(self.TOKEN, "task-1", opener=opener)
        self.assertEqual(select_result_file(bundle)["file_id"], "results")

    def test_download_decodes_csv(self) -> None:
        opener = SequenceOpener([SMAP_REAL.read_bytes()])
        text = download_result_csv(
            self.TOKEN, "task-1", "results", opener=opener
        )
        self.assertTrue(text.startswith("ID,Latitude,Longitude,Date"))

    def test_bundle_without_results_csv_is_rejected(self) -> None:
        with self.assertRaises(AppEEarsResponseError):
            select_result_file(
                [
                    {
                        "file_id": "stats",
                        "file_name": "fosol-test-statistics.csv",
                        "file_type": "csv",
                    }
                ]
            )


class SmapRetryTests(unittest.TestCase):
    TOKEN = "test-token-never-real"

    def _submit(self, opener: SequenceOpener, **overrides: object) -> dict:
        params = {
            "token": self.TOKEN,
            "task_name": "fosol-test",
            "latitude": 24.3767,
            "longitude": 88.6029,
            "point_id": "rajshahi",
            "start_date": "2025-01-01",
            "end_date": "2025-01-03",
            "opener": opener,
            "backoff_seconds": 0,
            "sleep": lambda seconds: None,
        }
        params.update(overrides)
        return submit_point_task(**params)

    def test_submit_retries_429_then_succeeds(self) -> None:
        opener = SequenceOpener(
            [http_error(429), {"status": "pending", "task_id": "task-1"}]
        )
        result = self._submit(opener, max_retries=1)
        self.assertEqual(result["task_id"], "task-1")
        self.assertEqual(len(opener.requests), 2)

    def test_submit_retries_503_then_succeeds(self) -> None:
        opener = SequenceOpener(
            [http_error(503), {"status": "pending", "task_id": "task-1"}]
        )
        result = self._submit(opener, max_retries=1)
        self.assertEqual(result["task_id"], "task-1")
        self.assertEqual(len(opener.requests), 2)

    def test_get_retries_5xx_then_succeeds(self) -> None:
        files = [
            {
                "file_id": "results",
                "file_name": "fosol-test-results.csv",
                "file_type": "csv",
            }
        ]
        opener = SequenceOpener([http_error(500), {"files": files}])
        result = get_bundle(
            self.TOKEN,
            "task-1",
            opener=opener,
            max_retries=1,
            backoff_seconds=0,
            sleep=lambda seconds: None,
        )
        self.assertEqual(result, files)
        self.assertEqual(len(opener.requests), 2)

    def test_retry_budget_is_bounded(self) -> None:
        opener = SequenceOpener([http_error(429)] * 10)
        with self.assertRaises(AppEEarsResponseError) as caught:
            self._submit(opener, max_retries=2)
        self.assertEqual(caught.exception.status_code, 429)
        self.assertEqual(len(opener.requests), 3)

    def test_post_500_is_not_retried(self) -> None:
        opener = SequenceOpener(
            [http_error(500), {"status": "pending", "task_id": "task-1"}]
        )
        with self.assertRaises(AppEEarsResponseError) as caught:
            self._submit(opener, max_retries=3)
        self.assertEqual(caught.exception.status_code, 500)
        self.assertEqual(len(opener.requests), 1)


class SmapTokenTests(unittest.TestCase):
    def test_token_is_loaded_and_expiry_is_enforced(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "token.json"
            path.write_text(
                json.dumps(
                    {
                        "token": "dummy-token-value",
                        "expiration": "2026-11-07T03:13:49Z",
                        "obtained_at": "2026-11-05T03:13:49Z",
                    }
                ),
                encoding="utf-8",
            )
            self.assertEqual(
                load_token(
                    path,
                    now=dt.datetime(2026, 11, 6, tzinfo=dt.timezone.utc),
                ),
                "dummy-token-value",
            )
            with self.assertRaises(AppEEarsAuthError) as caught:
                load_token(
                    path,
                    now=dt.datetime(2026, 11, 8, tzinfo=dt.timezone.utc),
                )
            self.assertEqual(caught.exception.message, AUTH_ERROR_MESSAGE)
            self.assertNotIn("dummy-token-value", str(caught.exception))

    def test_missing_token_file_raises(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(AppEEarsAuthError):
                load_token(Path(tmp) / "absent.json")

    def test_token_path_comes_from_documented_env_var(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "token.json"
            path.write_text(json.dumps({"token": "dummy-token-value"}), encoding="utf-8")
            with mock.patch.dict(os.environ, {"APPEARS_TOKEN_FILE": str(path)}):
                self.assertEqual(load_token(), "dummy-token-value")


class SmapFetchTests(unittest.TestCase):
    def test_full_orchestration_uses_the_results_csv(self) -> None:
        files = [
            {
                "file_id": "stats",
                "file_name": "fosol-test-statistics.csv",
                "file_type": "csv",
            },
            {
                "file_id": "results",
                "file_name": "fosol-test-results.csv",
                "file_type": "csv",
            },
        ]
        opener = SequenceOpener(
            [
                {"status": "pending", "task_id": "task-9"},
                {"status": "done", "task_id": "task-9"},
                {"files": files},
                SMAP_REAL.read_bytes(),
            ]
        )
        result = fetch_smap_point(
            24.3767,
            88.6029,
            "2025-01-01",
            "2025-01-03",
            point_id="rajshahi",
            token="test-token-never-real",
            opener=opener,
            sleep=lambda seconds: None,
            clock=lambda: 0.0,
        )
        self.assertEqual(result["task_id"], "task-9")
        self.assertEqual(len(result["observations"]), 24)
        self.assertEqual(result["point"]["id"], "rajshahi")
        self.assertEqual(len(opener.requests), 4)
        self.assertIn("/bundle/task-9/results", opener.requests[3].full_url)


class SmapParseTests(unittest.TestCase):
    def test_real_csv_is_parsed(self) -> None:
        result = parse_appeears_csv(
            real_smap_text(), retrieved_at="2026-11-06T12:00:00+00:00"
        )
        self.assertEqual(result["product"], "SPL4SMGP")
        self.assertEqual(result["product_version"], "008")
        self.assertEqual(result["provider"], "NASA SMAP via AppEEARS")
        self.assertEqual(result["spatial_resolution"], "9 km EASE-Grid 2.0")
        self.assertEqual(result["temporal_resolution"], "3-hourly")
        self.assertEqual(result["fill_value"], -9999)
        self.assertEqual(result["observation_start"], "2025-01-01T01:30:00+00:00")
        self.assertEqual(result["observation_end"], "2025-01-03T22:30:00+00:00")
        self.assertEqual(len(result["observations"]), 24)
        self.assertEqual(
            result["point"],
            {"id": "rajshahi", "latitude": 24.3767, "longitude": 88.6029},
        )
        self.assertEqual(
            result["variables"]["sm_surface"],
            {"units": "m^3/m^3", "layer": "Geophysical_Data_sm_surface"},
        )
        self.assertEqual(
            result["variables"]["sm_rootzone"],
            {"units": "m^3/m^3", "layer": "Geophysical_Data_sm_rootzone"},
        )
        self.assertEqual(result["missing_counts"], {"sm_surface": 0, "sm_rootzone": 0})
        self.assertEqual(result["duplicate_timestamps"], 0)
        self.assertEqual(
            result["observations"][0],
            {
                "timestamp": "2025-01-01T01:30:00+00:00",
                "sm_surface": 0.1858516,
                "sm_rootzone": 0.2432147,
            },
        )
        timestamps = [item["timestamp"] for item in result["observations"]]
        self.assertEqual(timestamps, sorted(timestamps))

    def test_fill_and_empty_become_none_not_zero(self) -> None:
        result = parse_appeears_csv(
            SMAP_SYNTHETIC.read_text(encoding="utf-8")
        )
        self.assertEqual(len(result["observations"]), 3)
        self.assertIsNone(result["observations"][0]["sm_surface"])
        self.assertEqual(result["observations"][0]["sm_rootzone"], 0.2)
        self.assertIsNone(result["observations"][1]["sm_rootzone"])
        self.assertIsNone(result["observations"][1]["sm_surface"])
        self.assertEqual(result["observations"][2]["sm_surface"], 0.18)
        self.assertEqual(
            result["missing_counts"], {"sm_surface": 2, "sm_rootzone": 1}
        )

    def test_identical_duplicate_timestamp_is_deduplicated(self) -> None:
        lines = real_smap_text().splitlines()
        text = "\n".join(lines + [lines[1]]) + "\n"
        result = parse_appeears_csv(text)
        self.assertEqual(len(result["observations"]), 24)
        self.assertEqual(result["duplicate_timestamps"], 1)
        self.assertEqual(
            result["missing_counts"], {"sm_surface": 0, "sm_rootzone": 0}
        )

    def test_conflicting_duplicate_timestamp_is_rejected(self) -> None:
        lines = real_smap_text().splitlines()
        conflicting = lines[1].replace("0.1858516", "0.19")
        text = "\n".join(lines + [conflicting]) + "\n"
        with self.assertRaises(AppEEarsResponseError):
            parse_appeears_csv(text)

    def test_malformed_csv_is_rejected(self) -> None:
        good = real_smap_text()
        cases = {
            "empty": "",
            "missing column": good.replace(
                "SPL4SMGP_008_Geophysical_Data_sm_surface",
                "not_the_surface_column",
            ),
            "bad timestamp": good.replace(
                "2025-01-01 01:30:00 UTC", "not-a-date"
            ),
            "non-numeric": good.replace("0.1858516", "wet"),
            "empty point": good.replace("rajshahi,24.3767", ",24.3767"),
        }
        for label, text in cases.items():
            with self.subTest(label=label):
                with self.assertRaises(AppEEarsResponseError):
                    parse_appeears_csv(text)

    def test_response_is_json_serializable(self) -> None:
        result = parse_appeears_csv(real_smap_text(), retrieved_at=T0.isoformat())
        json.dumps(result, allow_nan=False)


class CacheKeyTests(unittest.TestCase):
    BASE = dict(
        product="SPL4SMGP",
        product_version="008",
        latitude=24.3767,
        longitude=88.6029,
        start_date="2025-01-01",
        end_date="2025-01-03",
        variables=["a", "b"],
        settings={"units": "metric"},
    )

    def test_key_is_stable_and_variable_order_is_irrelevant(self) -> None:
        first = build_cache_key(**self.BASE)
        second = build_cache_key(**{**self.BASE, "variables": ("b", "a")})
        self.assertEqual(first, second)
        self.assertEqual(len(first), 64)

    def test_every_field_changes_the_key(self) -> None:
        keys = {build_cache_key(**self.BASE)}
        changes = {
            "product": "OTHER",
            "product_version": "009",
            "latitude": 24.0,
            "longitude": 88.0,
            "start_date": "2025-01-02",
            "end_date": "2025-01-04",
            "variables": ["a", "c"],
            "settings": {"units": "imperial"},
            "point_id": "other-point",
        }
        for field, value in changes.items():
            keys.add(build_cache_key(**{**self.BASE, field: value}))
        self.assertEqual(len(keys), 1 + len(changes))

    def test_point_id_is_part_of_the_key(self) -> None:
        self.assertNotEqual(
            build_cache_key(**self.BASE, point_id="point-a"),
            build_cache_key(**self.BASE, point_id="point-b"),
        )


class EnvironmentCacheTests(unittest.TestCase):
    def test_put_and_get_round_trip(self) -> None:
        key = build_cache_key(
            "p", "1", 1.0, 2.0, "2025-01-01", "2025-01-02", ["a"], {}
        )
        with tempfile.TemporaryDirectory() as tmp:
            cache = EnvironmentCache(tmp)
            self.assertIsNone(cache.get(key))
            cache.put(key, {"value": 1, "nested": {"ok": True}})
            self.assertEqual(
                cache.get(key), {"value": 1, "nested": {"ok": True}}
            )

    def test_corrupt_cache_is_a_miss(self) -> None:
        key = build_cache_key(
            "p", "1", 1.0, 2.0, "2025-01-01", "2025-01-02", ["a"], {}
        )
        with tempfile.TemporaryDirectory() as tmp:
            cache = EnvironmentCache(tmp)
            path = Path(tmp) / f"{key}.json"
            path.write_text("{not json", encoding="utf-8")
            self.assertIsNone(cache.get(key))

    def test_non_finite_json_constants_are_a_miss(self) -> None:
        key = build_cache_key(
            "p", "1", 1.0, 2.0, "2025-01-01", "2025-01-02", ["a"], {}
        )
        with tempfile.TemporaryDirectory() as tmp:
            cache = EnvironmentCache(tmp)
            path = Path(tmp) / f"{key}.json"
            for constant in ("NaN", "Infinity", "-Infinity", "1e999"):
                with self.subTest(constant=constant):
                    path.write_text(
                        '{"retrieved_at":"2026-11-06T12:00:00+00:00",'
                        f'"observations":{{"T2M":{constant}}}}}',
                        encoding="utf-8",
                    )
                    self.assertIsNone(cache.get(key))

    def test_invalid_key_and_non_finite_payload_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            cache = EnvironmentCache(tmp)
            with self.assertRaises(ValueError):
                cache.get("../escape")
            key = build_cache_key(
                "p", "1", 1.0, 2.0, "2025-01-01", "2025-01-02", ["a"], {}
            )
            with self.assertRaises(ValueError):
                cache.put(key, {"bad": float("nan")})
            with self.assertRaises(ValueError):
                cache.put(key, [])


class CountingPowerFetcher:
    def __init__(self) -> None:
        self.calls = 0

    def __call__(self, *args: object, **kwargs: object) -> dict:
        self.calls += 1
        return real_power_raw()


def fixed_normalizer(raw: dict) -> dict:
    return normalize_power_response(raw, retrieved_at=T0.isoformat())


def smap_fetcher(*args: object, **kwargs: object) -> dict:
    return parse_appeears_csv(real_smap_text(), retrieved_at=T0.isoformat())


class EnvironmentLoaderTests(unittest.TestCase):
    def test_fresh_cache_avoids_network(self) -> None:
        key_args = dict(
            latitude=24.3767,
            longitude=88.6029,
            start_date="2025-01-01",
            end_date="2025-01-03",
        )
        with tempfile.TemporaryDirectory() as tmp:
            cache = EnvironmentCache(tmp)
            first = CountingPowerFetcher()
            load_power_environment(
                cache,
                variables=["T2M", "PRECTOTCORR", "GWETTOP"],
                fetcher=first,
                normalizer=fixed_normalizer,
                now=lambda: T0,
                **key_args,
            )
            self.assertEqual(first.calls, 1)

            second = CountingPowerFetcher()
            result = load_power_environment(
                cache,
                variables=["T2M", "PRECTOTCORR", "GWETTOP"],
                fetcher=second,
                normalizer=fixed_normalizer,
                now=lambda: T0,
                **key_args,
            )
            self.assertEqual(second.calls, 0)
            self.assertTrue(result["cache"]["hit"])
            self.assertFalse(result["cache"]["stale"])
            self.assertEqual(result["warnings"], [])

    def test_fresh_cache_works_without_network(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            cache = EnvironmentCache(tmp)
            load_power_environment(
                cache,
                latitude=24.3767,
                longitude=88.6029,
                start_date="2025-01-01",
                end_date="2025-01-03",
                variables=["T2M"],
                fetcher=CountingPowerFetcher(),
                normalizer=fixed_normalizer,
                now=lambda: T0,
            )
            result = load_power_environment(
                cache,
                latitude=24.3767,
                longitude=88.6029,
                start_date="2025-01-01",
                end_date="2025-01-03",
                variables=["T2M"],
                allow_network=False,
                fetcher=CountingPowerFetcher(),
                normalizer=fixed_normalizer,
                now=lambda: T0,
            )
            self.assertEqual(result["observations"]["2025-01-01"]["T2M"], 15.21)

    def test_stale_cache_is_used_with_explicit_warning(self) -> None:
        later = T0 + dt.timedelta(days=10)

        def failing_fetcher(*args: object, **kwargs: object) -> dict:
            raise PowerApiError("provider down")

        with tempfile.TemporaryDirectory() as tmp:
            cache = EnvironmentCache(tmp)
            load_power_environment(
                cache,
                latitude=24.3767,
                longitude=88.6029,
                start_date="2025-01-01",
                end_date="2025-01-03",
                variables=["T2M"],
                fetcher=CountingPowerFetcher(),
                normalizer=fixed_normalizer,
                now=lambda: T0,
            )
            result = load_power_environment(
                cache,
                latitude=24.3767,
                longitude=88.6029,
                start_date="2025-01-01",
                end_date="2025-01-03",
                variables=["T2M"],
                fetcher=failing_fetcher,
                normalizer=fixed_normalizer,
                now=lambda: later,
            )
            self.assertTrue(result["cache"]["hit"])
            self.assertTrue(result["cache"]["stale"])
            self.assertEqual(len(result["warnings"]), 1)
            warning = result["warnings"][0]
            self.assertEqual(warning["code"], "STALE_CACHE")
            self.assertEqual(warning["provider"], "POWER")
            self.assertAlmostEqual(warning["cache_age_seconds"], 10 * 86400)
            self.assertEqual(result["observations"]["2025-01-01"]["T2M"], 15.21)

    def test_no_cache_and_failure_raises(self) -> None:
        def failing_fetcher(*args: object, **kwargs: object) -> dict:
            raise PowerApiError("provider down")

        with tempfile.TemporaryDirectory() as tmp:
            cache = EnvironmentCache(tmp)
            with self.assertRaises(EnvironmentUnavailable):
                load_power_environment(
                    cache,
                    latitude=24.3767,
                    longitude=88.6029,
                    start_date="2025-01-01",
                    end_date="2025-01-03",
                    variables=["T2M"],
                    fetcher=failing_fetcher,
                    normalizer=fixed_normalizer,
                    now=lambda: T0,
                )

    def test_auth_failure_hint_is_surfaced(self) -> None:
        def failing_fetcher(*args: object, **kwargs: object) -> dict:
            raise AppEEarsAuthError(AUTH_ERROR_MESSAGE)

        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(EnvironmentUnavailable) as caught:
                load_smap_environment(
                    EnvironmentCache(tmp),
                    latitude=24.3767,
                    longitude=88.6029,
                    start_date="2025-01-01",
                    end_date="2025-01-03",
                    point_id="rajshahi",
                    fetcher=failing_fetcher,
                    now=lambda: T0,
                )
            self.assertIn(AUTH_ERROR_MESSAGE, str(caught.exception))

    def test_smap_cache_is_separated_by_point_id(self) -> None:
        calls: list[str] = []

        def fetcher(*args: object, **kwargs: object) -> dict:
            calls.append(kwargs["point_id"])
            result = parse_appeears_csv(
                real_smap_text(), retrieved_at=T0.isoformat()
            )
            result["point"]["id"] = kwargs["point_id"]
            return result

        common = {
            "latitude": 24.3767,
            "longitude": 88.6029,
            "start_date": "2025-01-01",
            "end_date": "2025-01-03",
            "fetcher": fetcher,
            "now": lambda: T0,
        }
        with tempfile.TemporaryDirectory() as tmp:
            cache = EnvironmentCache(tmp)
            first = load_smap_environment(cache, point_id="point-a", **common)
            second = load_smap_environment(cache, point_id="point-b", **common)
            third = load_smap_environment(cache, point_id="point-a", **common)
            self.assertEqual(first["point"]["id"], "point-a")
            self.assertEqual(second["point"]["id"], "point-b")
            self.assertEqual(third["point"]["id"], "point-a")
            self.assertEqual(calls, ["point-a", "point-b"])
            self.assertTrue(third["cache"]["hit"])

    def test_smap_default_point_id_is_stable_coordinate_string(self) -> None:
        calls: list[str] = []

        def fetcher(*args: object, **kwargs: object) -> dict:
            calls.append(kwargs["point_id"])
            result = parse_appeears_csv(
                real_smap_text(), retrieved_at=T0.isoformat()
            )
            result["point"]["id"] = kwargs["point_id"]
            return result

        with tempfile.TemporaryDirectory() as tmp:
            cache = EnvironmentCache(tmp)
            first = load_smap_environment(
                cache,
                latitude=24.3767,
                longitude=88.6029,
                start_date="2025-01-01",
                end_date="2025-01-03",
                fetcher=fetcher,
                now=lambda: T0,
            )
            second = load_smap_environment(
                cache,
                latitude=24.3767,
                longitude=88.6029,
                start_date="2025-01-01",
                end_date="2025-01-03",
                fetcher=fetcher,
                now=lambda: T0,
            )
            self.assertEqual(first["request"]["point_id"], "24.3767,88.6029")
            self.assertEqual(second["request"]["point_id"], "24.3767,88.6029")
            self.assertEqual(calls, ["24.3767,88.6029"])
            self.assertTrue(second["cache"]["hit"])

    def test_non_finite_cache_is_refetched(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            cache = EnvironmentCache(tmp)
            load_power_environment(
                cache,
                latitude=24.3767,
                longitude=88.6029,
                start_date="2025-01-01",
                end_date="2025-01-03",
                variables=["T2M"],
                fetcher=CountingPowerFetcher(),
                normalizer=fixed_normalizer,
                now=lambda: T0,
            )
            cache_file = next(Path(tmp).glob("*.json"))
            payload = json.loads(cache_file.read_text(encoding="utf-8"))
            payload["observations"]["2025-01-01"]["T2M"] = float("nan")
            cache_file.write_text(json.dumps(payload), encoding="utf-8")
            self.assertIsNone(cache.get(cache_file.stem))

            refetch = CountingPowerFetcher()
            result = load_power_environment(
                cache,
                latitude=24.3767,
                longitude=88.6029,
                start_date="2025-01-01",
                end_date="2025-01-03",
                variables=["T2M"],
                fetcher=refetch,
                normalizer=fixed_normalizer,
                now=lambda: T0,
            )
            self.assertEqual(refetch.calls, 1)
            self.assertEqual(
                result["observations"]["2025-01-01"]["T2M"], 15.21
            )

    def test_smap_loader_and_json_serialization(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            cache = EnvironmentCache(tmp)
            result = load_smap_environment(
                cache,
                latitude=24.3767,
                longitude=88.6029,
                start_date="2025-01-01",
                end_date="2025-01-03",
                point_id="rajshahi",
                fetcher=smap_fetcher,
                now=lambda: T0,
            )
            self.assertEqual(result["product"], "SPL4SMGP")
            self.assertEqual(len(result["observations"]), 24)
            self.assertEqual(result["request"]["point_id"], "rajshahi")
            self.assertEqual(result["request"]["layers"], list(DEFAULT_LAYERS))
            json.dumps(result, allow_nan=False)


class EnvironmentOrchestratorTests(unittest.TestCase):
    def test_partial_result_when_one_provider_fails(self) -> None:
        def working_power(cache: EnvironmentCache, **kwargs: object) -> dict:
            return load_power_environment(
                cache,
                fetcher=CountingPowerFetcher(),
                normalizer=fixed_normalizer,
                **kwargs,
            )

        def failing_smap(cache: EnvironmentCache, **kwargs: object) -> dict:
            raise EnvironmentUnavailable("no smap", providers=("SMAP",))

        with tempfile.TemporaryDirectory() as tmp:
            result = load_environment(
                EnvironmentCache(tmp),
                latitude=24.3767,
                longitude=88.6029,
                start_date="2025-01-01",
                end_date="2025-01-03",
                point_id="rajshahi",
                power_loader=working_power,
                smap_loader=failing_smap,
                now=lambda: T0,
            )
            self.assertIsNotNone(result["sources"]["power"])
            self.assertIsNone(result["sources"]["smap"])
            self.assertEqual(len(result["warnings"]), 1)
            self.assertEqual(result["warnings"][0]["code"], "SMAP_UNAVAILABLE")
            self.assertEqual(result["request"]["point_id"], "rajshahi")
            json.dumps(result, allow_nan=False)

    def test_both_providers_succeed(self) -> None:
        def working_power(cache: EnvironmentCache, **kwargs: object) -> dict:
            return load_power_environment(
                cache,
                fetcher=CountingPowerFetcher(),
                normalizer=fixed_normalizer,
                **kwargs,
            )

        def working_smap(cache: EnvironmentCache, **kwargs: object) -> dict:
            return load_smap_environment(
                cache,
                fetcher=smap_fetcher,
                **kwargs,
            )

        with tempfile.TemporaryDirectory() as tmp:
            result = load_environment(
                EnvironmentCache(tmp),
                latitude=24.3767,
                longitude=88.6029,
                start_date="2025-01-01",
                end_date="2025-01-03",
                point_id="rajshahi",
                power_loader=working_power,
                smap_loader=working_smap,
                now=lambda: T0,
            )
            self.assertIsNotNone(result["sources"]["power"])
            self.assertIsNotNone(result["sources"]["smap"])
            self.assertEqual(result["warnings"], [])
            json.dumps(result, allow_nan=False)

    def test_both_providers_failing_raises(self) -> None:
        def failing(cache: EnvironmentCache, **kwargs: object) -> dict:
            raise EnvironmentUnavailable("down")

        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(EnvironmentUnavailable):
                load_environment(
                    EnvironmentCache(tmp),
                    latitude=24.3767,
                    longitude=88.6029,
                    start_date="2025-01-01",
                    end_date="2025-01-03",
                    point_id="rajshahi",
                    power_loader=failing,
                    smap_loader=failing,
                    now=lambda: T0,
                )


if __name__ == "__main__":
    unittest.main()
