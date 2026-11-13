"""Tests for seasonal outlook statistics and warning indicators (v1.md §6.2, §9.1-9.3, §14.4)."""

import datetime as dt
import json
import unittest
from pathlib import Path

from src.outlook_config import OUTLOOK_LABEL, WARNING_DEFINITIONS
from src.outlook_indicators import (
    calculate_precipitation_statistics,
    calculate_temperature_statistics,
    calculate_warning_indicator,
)
from src.seasonal_replay import map_schedule_to_seasons

SRC_DIR = Path(__file__).resolve().parents[1] / "src"


def _series(start: str, values: list, variable: str) -> dict:
    current = dt.date.fromisoformat(start)
    observations = {}
    for value in values:
        observations[current.isoformat()] = {variable: value}
        current += dt.timedelta(days=1)
    return observations


def _season_result(
    observations: dict,
    variable: str,
    *,
    period_start: str = "2020-01-01",
    period_end: str = "2020-01-02",
    start_year: int = 2020,
    end_year: int = 2020,
    coverage_rule: str = "stats_min_90",
) -> dict:
    return map_schedule_to_seasons(
        period_start=period_start,
        period_end=period_end,
        observations=observations,
        variable=variable,
        start_year=start_year,
        end_year=end_year,
        last_complete_data_date="2030-12-31",
        coverage_rule=coverage_rule,
    )


def _direct_season(
    start: str, end: str, valid_days: int, total_days: int, year: int
) -> dict:
    return {
        "season_start_year": year,
        "start_date": start,
        "end_date": end,
        "valid_days": valid_days,
        "total_days": total_days,
        "coverage_fraction": valid_days / total_days,
        "coverage_percent": valid_days * 100 / total_days,
        "included": True,
    }


def _direct_season_result(
    evaluated: list[dict], excluded: list[dict] | None = None
) -> dict:
    return {
        "period_start": "2020-01-01",
        "period_end": "2020-01-02",
        "analysis_period": {"start_year": 2020, "end_year": 2021},
        "crosses_year": False,
        "coverage_rule": "warnings_100",
        "evaluated_seasons": evaluated,
        "excluded_seasons": excluded or [],
    }


class OutlookIndicatorTests(unittest.TestCase):
    def test_temperature_statistics_known_values_and_linear_iqr(self) -> None:
        """Spec §9.1 | Bug it catches: pooled T2M uses an averaged or non-linear IQR."""
        observations = {
            **_series("2020-01-01", [10, 20], "T2M"),
            **_series("2021-01-01", [30, 40], "T2M"),
        }
        season_result = _season_result(
            observations, "T2M", start_year=2020, end_year=2021
        )
        result = calculate_temperature_statistics(observations, season_result)
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["sample"]["valid_days"], 4)
        self.assertEqual(result["sample"]["seasons"], 2)
        self.assertEqual(result["stats"]["median"], 25.0)
        self.assertEqual(result["stats"]["q1"], 17.5)
        self.assertEqual(result["stats"]["q3"], 32.5)
        self.assertEqual(result["stats"]["iqr"], 15.0)
        self.assertEqual(result["stats"]["min"], 10.0)
        self.assertEqual(result["stats"]["max"], 40.0)
        self.assertEqual(result["definition"]["unit"], "C")
        self.assertEqual(result["coverage"]["rule"], "stats_min_90")

    def test_temperature_statistics_90_percent_boundary_and_missing_invalid(self) -> None:
        """Spec §9.2 | Bug it catches: 90% boundary or missing values enter pooled T2M."""
        observations = {
            **_series("2020-01-01", [1, 2, 3, 4, 5, 6, 7, 8, 9, None], "T2M"),
            **_series(
                "2021-01-01",
                [1, 2, 3, 4, 5, 6, 7, 8, float("nan"), -999],
                "T2M",
            ),
        }
        season_result = _season_result(
            observations,
            "T2M",
            period_end="2020-01-10",
            start_year=2020,
            end_year=2021,
        )
        self.assertEqual(
            [season["season_start_year"] for season in season_result["evaluated_seasons"]],
            [2020],
        )
        self.assertEqual(
            [season["season_start_year"] for season in season_result["excluded_seasons"]],
            [2021],
        )
        result = calculate_temperature_statistics(observations, season_result)
        self.assertEqual(result["status"], "partial")
        self.assertEqual(result["sample"]["valid_days"], 9)
        self.assertEqual(result["sample"]["seasons"], 1)
        self.assertEqual(result["stats"]["median"], 5.0)
        self.assertEqual(result["stats"]["q1"], 3.0)
        self.assertEqual(result["stats"]["q3"], 7.0)
        self.assertTrue(any("excluded" in note for note in result["notes"]))

    def test_temperature_coverage_reports_excluded_incomplete_season(self) -> None:
        """Spec §14.4 | Bug it catches: an excluded incomplete season is only in notes, not coverage."""
        observations = {
            **_series("2020-01-01", [10, 20], "T2M"),
            **_series("2021-01-01", [10, None], "T2M"),
        }
        season_result = _direct_season_result(
            [_direct_season("2020-01-01", "2020-01-02", 2, 2, 2020)],
            [_direct_season("2021-01-01", "2021-01-02", 1, 2, 2021)],
        )
        result = calculate_temperature_statistics(observations, season_result)
        self.assertEqual(result["status"], "partial")
        self.assertEqual(result["sample"]["seasons"], 1)
        self.assertEqual(result["coverage"]["excluded_seasons"], 1)
        self.assertTrue(any("excluded" in note for note in result["notes"]))

    def test_precipitation_statistics_per_season_totals_and_stats(self) -> None:
        """Spec §9.1 | Bug it catches: precipitation statistics use daily values instead of season totals."""
        observations = {
            **_series("2020-01-01", [1, 2], "PRECTOTCORR"),
            **_series("2021-01-01", [3, 4], "PRECTOTCORR"),
            **_series("2022-01-01", [5, 6], "PRECTOTCORR"),
        }
        season_result = _season_result(
            observations,
            "PRECTOTCORR",
            start_year=2020,
            end_year=2022,
            coverage_rule="warnings_100",
        )
        result = calculate_precipitation_statistics(observations, season_result)
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["sample"], {"seasons": 3})
        self.assertEqual(
            [item["total_mm"] for item in result["per_season_totals"]],
            [3.0, 7.0, 11.0],
        )
        self.assertEqual(result["stats"]["median"], 7.0)
        self.assertEqual(result["stats"]["q1"], 5.0)
        self.assertEqual(result["stats"]["q3"], 9.0)
        self.assertEqual(result["stats"]["iqr"], 4.0)
        self.assertEqual(result["stats"]["min"], 3.0)
        self.assertEqual(result["stats"]["max"], 11.0)
        self.assertEqual(result["unit"], "mm")

    def test_precipitation_requires_100_percent_per_season(self) -> None:
        """Spec §9.2 | Bug it catches: an incomplete season contributes a precipitation total."""
        observations = {
            **_series("2020-01-01", [1, 2], "PRECTOTCORR"),
            **_series("2021-01-01", [1, None], "PRECTOTCORR"),
        }
        season_result = _season_result(
            observations,
            "PRECTOTCORR",
            start_year=2020,
            end_year=2021,
            coverage_rule="warnings_100",
        )
        result = calculate_precipitation_statistics(observations, season_result)
        self.assertEqual(result["status"], "partial")
        self.assertEqual(result["sample"], {"seasons": 1})
        self.assertEqual(
            [item["total_mm"] for item in result["per_season_totals"]],
            [3.0],
        )
        self.assertEqual(result["stats"]["median"], 3.0)
        self.assertEqual(result["stats"]["iqr"], 0.0)
        self.assertTrue(any("excluded" in note for note in result["notes"]))

    def test_precipitation_skips_direct_incomplete_evaluated_season(self) -> None:
        """Spec §9.2 | Bug it catches: W2's 100% guard is weakened to < days-1."""
        observations = {
            **_series("2020-01-01", [1, 2], "PRECTOTCORR"),
            **_series("2021-01-01", [1, None], "PRECTOTCORR"),
        }
        season_result = _direct_season_result(
            [
                _direct_season("2020-01-01", "2020-01-02", 2, 2, 2020),
                _direct_season("2021-01-01", "2021-01-02", 1, 2, 2021),
            ]
        )
        result = calculate_precipitation_statistics(observations, season_result)
        self.assertEqual(result["status"], "partial")
        self.assertEqual(result["sample"], {"seasons": 1})
        self.assertEqual(
            [item["total_mm"] for item in result["per_season_totals"]],
            [3.0],
        )
        self.assertEqual(result["coverage"]["excluded_seasons"], 1)

    def test_disabled_warning_returns_disabled_without_x_y(self) -> None:
        """Spec §9.1 | Bug it catches: a disabled warning reports a zero-risk X/Y."""
        observations = _series("2020-01-01", [31, 31], "T2M_MAX")
        season_result = _season_result(
            observations, "T2M_MAX", coverage_rule="warnings_100"
        )
        definition = WARNING_DEFINITIONS["wheat_tmax_gt_30c"]
        result = calculate_warning_indicator(observations, season_result, definition)
        self.assertEqual(result["status"], "disabled")
        self.assertFalse(result["enabled"])
        self.assertNotIn("numerator", result)
        self.assertNotIn("denominator", result)
        self.assertNotIn("days_meeting", result)
        self.assertEqual(result["text"], definition["indicator_text"])
        empty = calculate_warning_indicator({}, {}, definition)
        self.assertEqual(empty["status"], "disabled")
        self.assertEqual(
            set(WARNING_DEFINITIONS),
            {"wheat_tmax_gt_30c", "wheat_tmin_lt_15c", "mustard_precip_gt_50mm"},
        )
        self.assertEqual(WARNING_DEFINITIONS["wheat_tmax_gt_30c"]["threshold"], 30.0)
        self.assertEqual(WARNING_DEFINITIONS["wheat_tmin_lt_15c"]["threshold"], 15.0)
        self.assertEqual(WARNING_DEFINITIONS["mustard_precip_gt_50mm"]["threshold"], 50.0)
        expected_source_text = (
            "Weather warnings usually create cautions. Hard rejection requires a "
            "documented rule appropriate to the variable, crop, stage, location, "
            "and time scale."
        )
        for item in WARNING_DEFINITIONS.values():
            self.assertFalse(item["enabled"])
            self.assertEqual(item["weather_risk_threshold_text"], expected_source_text)
        texts = [item["indicator_text"] for item in WARNING_DEFINITIONS.values()]
        self.assertEqual(len(set(texts)), 3)
        self.assertNotIn("heat-warning", " ".join(texts).lower())

    def test_enabled_heat_warning_counts_at_least_one_day_per_season(self) -> None:
        """Spec §9.1 | Bug it catches: numerator counts days instead of seasons, or shares warning text."""
        observations = {
            **_series("2020-01-01", [31, 32], "T2M_MAX"),
            **_series("2021-01-01", [29, 29], "T2M_MAX"),
        }
        season_result = _season_result(
            observations,
            "T2M_MAX",
            start_year=2020,
            end_year=2021,
            coverage_rule="warnings_100",
        )
        definition = {**WARNING_DEFINITIONS["wheat_tmax_gt_30c"], "enabled": True}
        result = calculate_warning_indicator(observations, season_result, definition)
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["numerator"], 1)
        self.assertEqual(result["denominator"], 2)
        self.assertEqual(result["days_meeting"], 2)
        self.assertEqual(result["sample"], {"seasons": 2})
        self.assertIn("Heat exposure", result["text"])
        self.assertIn("1 of 2", result["text"])
        self.assertNotIn("heat-warning", result["text"].lower())

    def test_enabled_low_temperature_warning_uses_its_own_text(self) -> None:
        """Spec §6.2 | Bug it catches: low-temperature and heat indicators share text or threshold."""
        observations = {
            **_series("2020-01-01", [14, 16], "T2M_MIN"),
            **_series("2021-01-01", [15, 15], "T2M_MIN"),
        }
        season_result = _season_result(
            observations,
            "T2M_MIN",
            start_year=2020,
            end_year=2021,
            coverage_rule="warnings_100",
        )
        definition = {**WARNING_DEFINITIONS["wheat_tmin_lt_15c"], "enabled": True}
        result = calculate_warning_indicator(observations, season_result, definition)
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["numerator"], 1)
        self.assertEqual(result["denominator"], 2)
        self.assertEqual(result["days_meeting"], 1)
        self.assertIn("Low-temperature", result["text"])
        self.assertNotIn("Heat exposure", result["text"])

    def test_enabled_heavy_rain_warning_uses_strict_threshold(self) -> None:
        """Spec §6.2 | Bug it catches: heavy rain uses >= 50 or the wrong text."""
        observations = {
            **_series("2020-01-01", [51, 50], "PRECTOTCORR"),
            **_series("2021-01-01", [49, 50], "PRECTOTCORR"),
        }
        season_result = _season_result(
            observations,
            "PRECTOTCORR",
            start_year=2020,
            end_year=2021,
            coverage_rule="warnings_100",
        )
        definition = {**WARNING_DEFINITIONS["mustard_precip_gt_50mm"], "enabled": True}
        result = calculate_warning_indicator(observations, season_result, definition)
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["numerator"], 1)
        self.assertEqual(result["denominator"], 2)
        self.assertEqual(result["days_meeting"], 1)
        self.assertIn("Heavy-rain", result["text"])

    def test_warning_requires_100_percent_coverage(self) -> None:
        """Spec §9.2 | Bug it catches: an incomplete season enters warning X/Y."""
        observations = {
            **_series("2020-01-01", [31, 31], "T2M_MAX"),
            **_series("2021-01-01", [31, None], "T2M_MAX"),
        }
        season_result = _season_result(
            observations,
            "T2M_MAX",
            start_year=2020,
            end_year=2021,
            coverage_rule="warnings_100",
        )
        definition = {**WARNING_DEFINITIONS["wheat_tmax_gt_30c"], "enabled": True}
        result = calculate_warning_indicator(observations, season_result, definition)
        self.assertEqual(result["status"], "partial")
        self.assertEqual(result["numerator"], 1)
        self.assertEqual(result["denominator"], 1)
        self.assertEqual(result["days_meeting"], 2)
        self.assertTrue(any("excluded" in note for note in result["notes"]))

    def test_warning_skips_direct_incomplete_evaluated_season(self) -> None:
        """Spec §9.2 | Bug it catches: W2's 100% guard is weakened to < days-1."""
        observations = {
            **_series("2020-01-01", [31, 31], "T2M_MAX"),
            **_series("2021-01-01", [31, None], "T2M_MAX"),
        }
        season_result = _direct_season_result(
            [
                _direct_season("2020-01-01", "2020-01-02", 2, 2, 2020),
                _direct_season("2021-01-01", "2021-01-02", 1, 2, 2021),
            ]
        )
        definition = {**WARNING_DEFINITIONS["wheat_tmax_gt_30c"], "enabled": True}
        result = calculate_warning_indicator(observations, season_result, definition)
        self.assertEqual(result["status"], "partial")
        self.assertEqual(result["numerator"], 1)
        self.assertEqual(result["denominator"], 1)
        self.assertEqual(result["days_meeting"], 2)
        self.assertEqual(result["coverage"]["excluded_seasons"], 1)

    def test_warning_y_zero_is_unavailable_not_zero_risk(self) -> None:
        """Spec §14.4 | Bug it catches: no evaluated seasons becomes zero risk."""
        observations = _series(
            "2020-01-01",
            [31, 31, 31, 31, 31, 31, 31, 31, 31, None],
            "T2M_MAX",
        )
        season_result = _season_result(
            observations,
            "T2M_MAX",
            period_end="2020-01-10",
            coverage_rule="warnings_100",
        )
        definition = {**WARNING_DEFINITIONS["wheat_tmax_gt_30c"], "enabled": True}
        result = calculate_warning_indicator(observations, season_result, definition)
        self.assertEqual(result["status"], "unavailable")
        self.assertIsNone(result["numerator"])
        self.assertEqual(result["denominator"], 0)
        self.assertIsNone(result["days_meeting"])
        self.assertIn("not zero", result["text"])

    def test_outlook_label_is_exact_with_em_dash(self) -> None:
        """Spec §9.3 | Bug it catches: the outlook label is paraphrased or uses a hyphen."""
        self.assertEqual(
            OUTLOOK_LABEL,
            "Seasonal outlook — based on historical conditions, not a weather forecast.",
        )
        self.assertIn("\u2014", OUTLOOK_LABEL)

    def test_results_are_json_serializable_and_no_crop_id_branches(self) -> None:
        """Spec §14.4 | Bug it catches: non-JSON values or a crop-ID branch enter outlook code."""
        observations = _series("2020-01-01", [10, 20], "T2M")
        season_result = _season_result(observations, "T2M")
        temperature = calculate_temperature_statistics(observations, season_result)

        precip_observations = _series("2020-01-01", [1, 2], "PRECTOTCORR")
        precip_season = _season_result(
            precip_observations, "PRECTOTCORR", coverage_rule="warnings_100"
        )
        precipitation = calculate_precipitation_statistics(
            precip_observations, precip_season
        )

        heat_observations = _series("2020-01-01", [31, 31], "T2M_MAX")
        heat_season = _season_result(
            heat_observations, "T2M_MAX", coverage_rule="warnings_100"
        )
        warning = calculate_warning_indicator(
            heat_observations,
            heat_season,
            {**WARNING_DEFINITIONS["wheat_tmax_gt_30c"], "enabled": True},
        )
        payload = {
            "label": OUTLOOK_LABEL,
            "definitions": WARNING_DEFINITIONS,
            "temperature": temperature,
            "precipitation": precipitation,
            "warning": warning,
        }
        encoded = json.dumps(payload, allow_nan=False)
        self.assertNotIn("NaN", encoded)
        self.assertEqual(json.loads(encoded)["label"], OUTLOOK_LABEL)

        for name in ("outlook_indicators.py", "outlook_config.py"):
            source = (SRC_DIR / name).read_text(encoding="utf-8")
            self.assertNotIn("crop_id", source)
            for crop_id in ("wheat_bari_gom33", "mustard_binasarisha9"):
                self.assertNotIn(crop_id, source)


if __name__ == "__main__":
    unittest.main()
