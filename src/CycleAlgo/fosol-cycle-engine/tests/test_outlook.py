"""Tests for the seasonal outlook assembler (v1.md §9.1-9.3, §14.4)."""

import datetime as dt
import json
import unittest
from pathlib import Path

from src.outlook import build_outlook
from src.outlook_config import OUTLOOK_LABEL, WARNING_DEFINITIONS

SRC_DIR = Path(__file__).resolve().parents[1] / "src"


def _series(start: str, values: list, variable: str) -> dict:
    current = dt.date.fromisoformat(start)
    observations = {}
    for value in values:
        observations[current.isoformat()] = {variable: value}
        current += dt.timedelta(days=1)
    return observations


def _observations(*series: dict) -> dict:
    merged = {}
    for item in series:
        for date, record in item.items():
            merged.setdefault(date, {}).update(record)
    return merged


def _environment(observations: dict, **overrides) -> dict:
    dates = sorted(observations)
    variables = sorted(
        {
            variable
            for record in observations.values()
            if isinstance(record, dict)
            for variable in record
        }
    )
    environment = {
        "observations": observations,
        "product_version": "v2.10.3",
        "provider": "POWER",
        "product": "POWER Daily",
        "variables": {
            variable: {"units": "synthetic", "longname": variable}
            for variable in variables
        },
        "fill_value": -999,
        "observation_start": dates[0] if dates else None,
        "observation_end": dates[-1] if dates else None,
        "retrieved_at": "2026-11-06T00:00:00Z",
    }
    environment.update(overrides)
    return environment


def _build(environment: dict, **overrides) -> dict:
    values = {
        "crop_id": "wheat_bari_gom33",
        "period_start": "2020-01-01",
        "period_end": "2020-01-02",
        "environment": environment,
        "start_year": 2020,
        "end_year": 2020,
        "last_complete_data_date": "2030-12-31",
    }
    values.update(overrides)
    return build_outlook(**values)


class OutlookAssemblerTests(unittest.TestCase):
    def test_default_stats_only_label_and_indicators(self) -> None:
        """Spec §9.1/§9.3 | Bug it catches: warnings included by default or label paraphrased."""
        observations = _observations(
            _series("2020-01-01", [10, 20], "T2M"),
            _series("2020-01-01", [1, 2], "PRECTOTCORR"),
        )
        result = _build(_environment(observations))
        self.assertEqual(result["label"], OUTLOOK_LABEL)
        self.assertEqual(
            result["label"],
            "Seasonal outlook — based on historical conditions, not a weather forecast.",
        )
        self.assertEqual(result["status"], "ok")
        self.assertEqual(
            [item["indicator"] for item in result["indicators"]],
            ["temperature_statistics", "precipitation_statistics"],
        )
        self.assertEqual(result["period_basis"], "union_span")
        self.assertEqual(
            result["coverage_rule"],
            {
                "statistics": "min_90_percent_valid_days",
                "warnings": "required_100_percent_valid_days",
            },
        )
        self.assertEqual(
            result["analysis_period"], {"start_year": 2020, "end_year": 2020}
        )
        self.assertEqual(
            result["season_coverage"]["seasons_total"], 1
        )
        self.assertEqual(
            result["missing"],
            {"fill_value": -999, "missing_days": 0, "failed_requests": None},
        )
        self.assertEqual(result["sources"][0]["version"], "v2.10.3")
        self.assertEqual(result["sources"][0]["variables"], ["T2M", "PRECTOTCORR"])
        source_id = result["sources"][0]["source_id"]
        self.assertEqual(source_id, "nasa_power_daily")
        for indicator in result["indicators"]:
            self.assertEqual(indicator["source_ids"], [source_id])

    def test_enabled_heat_warning_has_text_and_x_y(self) -> None:
        """Spec §9.1 | Bug it catches: an enabled warning is omitted or loses X/Y/text."""
        observations = _observations(
            _series("2020-01-01", [10, 20], "T2M"),
            _series("2020-01-01", [1, 2], "PRECTOTCORR"),
            _series("2020-01-01", [31, 31], "T2M_MAX"),
        )
        result = _build(
            _environment(observations),
            warning_config={
                **WARNING_DEFINITIONS["wheat_tmax_gt_30c"],
                "enabled": True,
            },
        )
        warning = next(
            item
            for item in result["indicators"]
            if item["indicator"] == "wheat_tmax_gt_30c"
        )
        self.assertEqual(result["status"], "ok")
        self.assertEqual(warning["status"], "ok")
        self.assertEqual(warning["numerator"], 1)
        self.assertEqual(warning["denominator"], 1)
        self.assertEqual(warning["days_meeting"], 2)
        self.assertIn("Heat exposure", warning["text"])
        self.assertIn("1 of 1", warning["text"])
        self.assertTrue(warning["definition"]["enabled"])
        self.assertIn("T2M_MAX", result["sources"][0]["variables"])

    def test_low_temp_and_heavy_rain_keep_distinct_text(self) -> None:
        """Spec §6.2 | Bug it catches: low-temperature and heavy-rain warnings share text."""
        observations = _observations(
            _series("2020-01-01", [10, 20], "T2M"),
            _series("2020-01-01", [51, 49], "PRECTOTCORR"),
            _series("2020-01-01", [14, 16], "T2M_MIN"),
        )
        result = _build(
            _environment(observations),
            warning_config={
                "wheat_tmin_lt_15c": True,
                "mustard_precip_gt_50mm": True,
            },
        )
        low = next(
            item
            for item in result["indicators"]
            if item["indicator"] == "wheat_tmin_lt_15c"
        )
        rain = next(
            item
            for item in result["indicators"]
            if item["indicator"] == "mustard_precip_gt_50mm"
        )
        self.assertIn("Low-temperature", low["text"])
        self.assertIn("Heavy-rain", rain["text"])
        self.assertNotIn("Heat exposure", low["text"])
        self.assertNotIn("Low-temperature", rain["text"])
        self.assertEqual((low["numerator"], low["days_meeting"]), (1, 1))
        self.assertEqual((rain["numerator"], rain["days_meeting"]), (1, 1))

    def test_unavailable_without_observations(self) -> None:
        """Spec §9.1/§14.4 | Bug it catches: no valid seasons becomes zero risk or ok."""
        result = _build(
            _environment({}),
            warning_config={"wheat_tmax_gt_30c": True},
        )
        self.assertEqual(result["status"], "unavailable")
        self.assertEqual(
            [item["status"] for item in result["indicators"]],
            ["unavailable", "unavailable", "unavailable"],
        )
        self.assertIsNone(result["indicators"][0]["stats"])
        self.assertIsNone(result["indicators"][1]["stats"])
        self.assertEqual(result["indicators"][0]["sample"]["valid_days"], 0)
        self.assertEqual(result["indicators"][0]["sample"]["seasons"], 0)
        self.assertEqual(result["indicators"][1]["sample"], {"seasons": 0})
        warning = result["indicators"][2]
        self.assertIsNone(warning["numerator"])
        self.assertEqual(warning["denominator"], 0)
        self.assertIsNone(warning["days_meeting"])
        self.assertEqual(warning["sample"], {"seasons": 0})
        self.assertIn("not zero", warning["text"])
        self.assertEqual(result["missing"]["missing_days"], 6)

    def test_source_ids_and_unavailable_counts_are_pinned(self) -> None:
        """Spec §14.4 | Bug it catches: indicator source_ids dropped or unavailable warning returns 0/0."""
        observations = _observations(
            _series("2020-01-01", [10, 20], "T2M"),
            _series("2020-01-01", [1, 2], "PRECTOTCORR"),
            _series("2020-01-01", [31, 31], "T2M_MAX"),
        )
        normal = _build(
            _environment(observations),
            warning_config={"wheat_tmax_gt_30c": True},
        )
        source_id = normal["sources"][0]["source_id"]
        self.assertEqual(source_id, "nasa_power_daily")
        for indicator in normal["indicators"]:
            self.assertEqual(indicator["source_ids"], [source_id])

        unavailable = _build(
            _environment({}),
            warning_config={"wheat_tmax_gt_30c": True},
        )
        warning = next(
            item
            for item in unavailable["indicators"]
            if item["indicator"] == "wheat_tmax_gt_30c"
        )
        self.assertIsNone(warning["numerator"])
        self.assertIsNone(warning["days_meeting"])
        self.assertEqual(warning["denominator"], 0)

    def test_partial_with_one_excluded_season(self) -> None:
        """Spec §9.2 | Bug it catches: an excluded season still yields ok or full counts."""
        observations = _observations(
            _series("2020-01-01", [10, 20], "T2M"),
            _series("2020-01-01", [1, 2], "PRECTOTCORR"),
        )
        result = _build(
            _environment(observations),
            start_year=2020,
            end_year=2021,
        )
        self.assertEqual(result["status"], "partial")
        self.assertEqual(
            result["season_coverage"]["seasons_total"], 2
        )
        self.assertEqual(
            result["season_coverage"]["seasons_evaluated_statistics"], 1
        )
        self.assertEqual(
            result["season_coverage"]["seasons_evaluated_warnings"], 1
        )
        self.assertEqual(
            len(result["season_coverage"]["excluded_seasons"]), 1
        )
        self.assertTrue(any("excluded" in note.lower() for note in result["notes"]))
        self.assertEqual(
            result["season_coverage"]["excluded_seasons"][0]["rules"],
            ["statistics", "warnings"],
        )
        self.assertTrue(
            result["season_coverage"]["excluded_seasons"][0]["reason"]
        )

    def test_sources_and_missing_use_environment_metadata(self) -> None:
        """Spec §9.1/§14.4 | Bug it catches: source version/fill/missing hardcoded."""
        values = [1.0] * 9 + [-1234]
        observations = _observations(
            _series("2020-01-01", values, "T2M"),
            _series("2020-01-01", [1.0] * 10, "PRECTOTCORR"),
        )
        result = _build(
            _environment(
                observations,
                product_version="v9.9.9",
                provider="POWER-X",
                product="POWER Daily Test",
                fill_value=-1234,
                failed_requests=2,
                retrieved_at="2026-11-06T12:34:56Z",
            ),
            period_end="2020-01-10",
        )
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["indicators"][0]["sample"]["valid_days"], 9)
        self.assertEqual(
            result["missing"],
            {
                "fill_value": -1234,
                "missing_days": 1,
                "failed_requests": 2,
            },
        )
        source = result["sources"][0]
        self.assertEqual(source["version"], "v9.9.9")
        self.assertEqual(source["provider"], "POWER-X")
        self.assertEqual(source["product"], "POWER Daily Test")
        self.assertEqual(source["retrieved_at"], "2026-11-06T12:34:56Z")
        self.assertEqual(source["variables"], ["T2M", "PRECTOTCORR"])

    def test_notes_json_and_no_crop_id_branches(self) -> None:
        """Spec §9.3/§14.4 | Bug it catches: union/leap notes, JSON, or crop branching lost."""
        observations = _observations(
            _series("2020-02-29", [10, 11, 12, 13], "T2M"),
            _series("2020-02-29", [1, 2, 3, 4], "PRECTOTCORR"),
        )
        result = _build(
            _environment(observations),
            period_start="2020-02-29",
            period_end="2020-03-02",
        )
        self.assertTrue(any("union span" in note.lower() for note in result["notes"]))
        self.assertTrue(any("February 29" in note for note in result["notes"]))
        encoded = json.dumps(result, allow_nan=False)
        self.assertNotIn("NaN", encoded)
        self.assertEqual(json.loads(encoded)["label"], OUTLOOK_LABEL)

        source = (SRC_DIR / "outlook.py").read_text(encoding="utf-8")
        self.assertNotIn("if crop_id", source)
        for crop_id in ("wheat_bari_gom33", "mustard_binasarisha9"):
            self.assertNotIn(crop_id, source)


if __name__ == "__main__":
    unittest.main()
