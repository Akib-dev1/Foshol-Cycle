"""Tests for the development server's POWER API/cache delivery path."""

from __future__ import annotations

import datetime as dt
import tempfile
import unittest
from pathlib import Path

from src.environment import EnvironmentUnavailable, load_power_environment
from src.environment_cache import EnvironmentCache
from src.power_api import PowerApiError
from src.server import (
    DEFAULT_CONFIG,
    POWER_HISTORY_END,
    POWER_HISTORY_START,
    create_server,
    load_server_power,
    validate_power_history_request,
)

DATA_DIR = Path(__file__).resolve().parents[2] / "Data"


def _environment() -> dict:
    return {
        "provider": "NASA POWER",
        "product": "NASA POWER Daily Point",
        "product_version": "test",
        "observations": {},
        "observation_start": "1991-01-01",
        "observation_end": POWER_HISTORY_END,
        "fill_value": -999.0,
        "retrieved_at": "2026-11-12T00:00:00+00:00",
        "warnings": [],
        "cache": {"hit": False, "stale": False, "age_seconds": 0.0},
    }


class CountingFetcher:
    def __init__(self, fail: bool = False) -> None:
        self.calls = 0
        self.fail = fail

    def __call__(self, *args: object, **kwargs: object) -> dict:
        self.calls += 1
        if self.fail:
            raise PowerApiError("provider down")
        return {}


def _cached_loader(fetcher: CountingFetcher, retrieved_at: str):
    def loader(cache, **kwargs):
        return load_power_environment(
            cache,
            fetcher=fetcher,
            normalizer=lambda raw: {
                **_environment(),
                "retrieved_at": retrieved_at,
            },
            **kwargs,
        )

    return loader


class PowerHistoryRequestTests(unittest.TestCase):
    def test_load_uses_rajshahi_coordinates_and_stable_period(self) -> None:
        calls = {}

        def loader(cache, **kwargs):
            calls["cache"] = cache
            calls.update(kwargs)
            return _environment()

        with tempfile.TemporaryDirectory() as tmp:
            result = load_server_power(
                cache_dir=tmp,
                start_date=POWER_HISTORY_START,
                loader=loader,
            )
            self.assertEqual(
                Path(calls["cache"].cache_dir), Path(tmp)
            )
        self.assertEqual(result["provider"], "NASA POWER")
        self.assertEqual(calls["latitude"], 24.3767)
        self.assertEqual(calls["longitude"], 88.6029)
        self.assertEqual(calls["start_date"], "1991-01-01")
        self.assertEqual(calls["end_date"], POWER_HISTORY_END)
        self.assertEqual(calls["variables"], ["T2M", "PRECTOTCORR", "GWETTOP"])
        self.assertIsInstance(calls["cache"], EnvironmentCache)

    def test_explicit_end_date_override_is_preserved(self) -> None:
        calls = {}

        def loader(cache, **kwargs):
            calls.update(kwargs)
            return _environment()

        with tempfile.TemporaryDirectory() as tmp:
            load_server_power(
                cache_dir=tmp,
                end_date="2026-11-09",
                loader=loader,
            )
        self.assertEqual(calls["end_date"], "2026-11-09")

    def test_default_cache_is_reused_offline_on_the_next_day(self) -> None:
        day_one = dt.datetime(2026, 11, 1, 12, 0, tzinfo=dt.timezone.utc)
        day_two = day_one + dt.timedelta(days=1)
        with tempfile.TemporaryDirectory() as tmp:
            first = CountingFetcher()
            first_result = load_server_power(
                cache_dir=tmp,
                loader=_cached_loader(first, day_one.isoformat()),
                now=day_one,
            )
            second = CountingFetcher()
            second_result = load_server_power(
                cache_dir=tmp,
                loader=_cached_loader(second, day_one.isoformat()),
                now=day_two,
                allow_network=False,
            )
        self.assertEqual(first.calls, 1)
        self.assertEqual(second.calls, 0)
        self.assertTrue(second_result["cache"]["hit"])
        self.assertFalse(second_result["cache"]["stale"])
        self.assertEqual(
            first_result["observation_end"], POWER_HISTORY_END
        )

    def test_expired_cache_refresh_failure_uses_stale_cache(self) -> None:
        day_one = dt.datetime(2026, 11, 1, 12, 0, tzinfo=dt.timezone.utc)
        expired = day_one + dt.timedelta(days=10)
        with tempfile.TemporaryDirectory() as tmp:
            seed = CountingFetcher()
            load_server_power(
                cache_dir=tmp,
                loader=_cached_loader(seed, day_one.isoformat()),
                now=day_one,
            )
            failed = CountingFetcher(fail=True)
            result = load_server_power(
                cache_dir=tmp,
                loader=_cached_loader(failed, day_one.isoformat()),
                now=expired,
            )
        self.assertEqual(failed.calls, 1)
        self.assertTrue(result["cache"]["hit"])
        self.assertTrue(result["cache"]["stale"])
        self.assertEqual(result["warnings"][0]["code"], "STALE_CACHE")

    def test_default_history_without_cache_fails(self) -> None:
        day_one = dt.datetime(2026, 11, 1, 12, 0, tzinfo=dt.timezone.utc)
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(EnvironmentUnavailable):
                load_server_power(
                    cache_dir=tmp,
                    loader=_cached_loader(CountingFetcher(), day_one.isoformat()),
                    now=day_one,
                    allow_network=False,
                )

    def test_parameter_limit_is_checked_before_fetch(self) -> None:
        with self.assertRaises(ValueError):
            validate_power_history_request(
                "1991-01-01",
                "2026-11-09",
                [f"P{index}" for index in range(21)],
            )

    def test_start_before_power_coverage_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            validate_power_history_request(
                "1980-12-31",
                "2026-11-09",
                ["T2M"],
            )


class ServerPowerTests(unittest.TestCase):
    def test_injected_environment_bypasses_provider_loader(self) -> None:
        environment = _environment()
        called = []

        def loader(**kwargs):
            called.append(kwargs)
            raise AssertionError("provider loader should not run")

        server = create_server(
            "127.0.0.1",
            0,
            data_dir=DATA_DIR,
            environment=environment,
            power_loader=loader,
        )
        try:
            self.assertIs(server.environment, environment)
            self.assertEqual(called, [])
            self.assertEqual(server.config, DEFAULT_CONFIG)
        finally:
            server.server_close()

    def test_provider_failure_leaves_explicit_unavailable_state(self) -> None:
        def loader(**kwargs):
            raise EnvironmentUnavailable("POWER provider unavailable")

        server = create_server(
            "127.0.0.1",
            0,
            data_dir=DATA_DIR,
            power_loader=loader,
        )
        try:
            self.assertIsNone(server.environment)
            self.assertEqual(
                server.environment_error, "POWER provider unavailable"
            )
        finally:
            server.server_close()

    def test_trusted_evidence_is_stored_on_server_not_request(self) -> None:
        evidence = {"ph": {"min": 6.5, "max": 7.0, "source_ids": ["test://soil"]}}
        preparation = {
            "lentil_binamasur9": {
                "min_days": 7,
                "max_days": 10,
                "source_ids": ["test://prep"],
            }
        }
        server = create_server(
            "127.0.0.1",
            0,
            data_dir=DATA_DIR,
            environment=_environment(),
            soil_evidence=evidence,
            preparation_lookup=preparation,
            duration_reference_verified=True,
            duration_reference_verified_crop_ids={"lentil_binamasur9"},
        )
        try:
            self.assertEqual(server.soil_evidence, evidence)
            self.assertEqual(server.preparation_lookup, preparation)
            self.assertTrue(server.duration_reference_verified)
            self.assertEqual(
                server.duration_reference_verified_crop_ids,
                {"lentil_binamasur9"},
            )
        finally:
            server.server_close()


if __name__ == "__main__":
    unittest.main()
