"""Tests for historical seasonal replay mapping and coverage (v1.md §9.2, §17.11)."""

import datetime as dt
import json
import unittest
from pathlib import Path

from src.seasonal_replay import map_schedule_to_seasons

VARIABLE = "T2M"
SRC = Path(__file__).resolve().parents[1] / "src" / "seasonal_replay.py"


def _obs(start: str, end: str, value: object = 1.0) -> dict:
    observations = {}
    current = dt.date.fromisoformat(start)
    last = dt.date.fromisoformat(end)
    while current <= last:
        observations[current.isoformat()] = {VARIABLE: value}
        current += dt.timedelta(days=1)
    return observations


class SeasonalReplayTests(unittest.TestCase):
    def _map(self, observations=None, **overrides):
        values = {
            "period_start": "2026-11-15",
            "period_end": "2027-03-22",
            "observations": observations or {},
            "variable": VARIABLE,
            "last_complete_data_date": "2026-10-23",
        }
        values.update(overrides)
        return map_schedule_to_seasons(**values)

    def test_default_analysis_period_maps_35_seasons(self) -> None:
        """Spec §9.2 | Bug it catches: analysis years are dropped or mislabeled."""
        result = self._map()
        self.assertEqual(result["period_basis"], "union_span")
        self.assertIn("union span", result["period_definition"])
        self.assertEqual(
            result["analysis_period"], {"start_year": 1991, "end_year": 2025}
        )
        self.assertEqual(len(result["seasons"]), 35)
        self.assertEqual(
            [season["season_start_year"] for season in result["seasons"]],
            list(range(1991, 2026)),
        )

    def test_cross_year_mapping_uses_next_year_end(self) -> None:
        """Spec §9.2 | Bug it catches: a Nov-Mar crop ends in the same year."""
        observations = _obs("2024-11-15", "2025-03-22")
        observations.update(_obs("2025-11-15", "2026-03-22"))
        result = self._map(
            observations,
            start_year=2024,
            end_year=2025,
        )
        self.assertTrue(result["crosses_year"])
        self.assertEqual(len(result["evaluated_seasons"]), 2)
        first, second = result["seasons"]
        self.assertEqual(first["start_date"], "2024-11-15")
        self.assertEqual(first["end_date"], "2025-03-22")
        self.assertEqual(second["start_date"], "2025-11-15")
        self.assertEqual(second["end_date"], "2026-03-22")

    def test_2025_season_included_when_data_is_complete(self) -> None:
        """Spec §9.2 | Bug it catches: a 2026 season end is hard-excluded."""
        observations = _obs("2025-11-15", "2026-03-22")
        result = self._map(
            observations,
            period_start="2025-11-15",
            period_end="2026-03-22",
            start_year=2025,
            end_year=2025,
        )
        self.assertEqual(len(result["evaluated_seasons"]), 1)
        self.assertEqual(result["excluded_seasons"], [])
        self.assertEqual(result["seasons"][0]["end_date"], "2026-03-22")

    def test_2025_season_excluded_when_last_complete_is_earlier(self) -> None:
        """Spec §9.2 | Bug it catches: incomplete seasons are kept as complete."""
        observations = _obs("2025-11-15", "2026-03-22")
        result = self._map(
            observations,
            period_start="2025-11-15",
            period_end="2026-03-22",
            start_year=2025,
            end_year=2025,
            last_complete_data_date="2026-03-21",
        )
        self.assertEqual(result["evaluated_seasons"], [])
        self.assertEqual(len(result["excluded_seasons"]), 1)
        season = result["excluded_seasons"][0]
        self.assertEqual(season["valid_days"], season["total_days"])
        self.assertIn("after last_complete_data_date", season["reason"])

    def test_leap_day_endpoint_adjusts_only_in_non_leap_years(self) -> None:
        """Spec §9.2 | Bug it catches: Feb 29 fails or shifts silently in non-leap years."""
        observations = _obs("2023-02-28", "2023-03-05")
        observations.update(_obs("2024-02-29", "2024-03-05"))
        result = self._map(
            observations,
            period_start="2024-02-29",
            period_end="2024-03-05",
            start_year=2023,
            end_year=2024,
            last_complete_data_date="2025-12-31",
        )
        self.assertEqual(len(result["evaluated_seasons"]), 2)
        non_leap, leap = result["seasons"]
        self.assertEqual(non_leap["start_date"], "2023-02-28")
        self.assertTrue(non_leap["leap_day_adjusted"])
        self.assertEqual(non_leap["leap_day_adjustments"], ["start"])
        self.assertEqual(leap["start_date"], "2024-02-29")
        self.assertFalse(leap["leap_day_adjusted"])
        self.assertTrue(any("February 29" in note for note in result["notes"]))

    def test_season_end_equal_last_complete_is_included(self) -> None:
        """Spec §9.2 | Bug it catches: equality with last_complete_data_date is excluded."""
        observations = _obs("2020-01-01", "2020-01-10")
        result = self._map(
            observations,
            period_start="2020-01-01",
            period_end="2020-01-10",
            start_year=2020,
            end_year=2020,
            last_complete_data_date="2020-01-10",
        )
        self.assertEqual(len(result["evaluated_seasons"]), 1)
        self.assertEqual(result["excluded_seasons"], [])
        self.assertEqual(result["seasons"][0]["end_date"], "2020-01-10")

    def test_end_only_feb_29_adjusts_in_non_leap_year(self) -> None:
        """Spec §9.2 | Bug it catches: only the start Feb 29 endpoint is adjusted."""
        observations = _obs("2023-02-28", "2023-02-28")
        result = self._map(
            observations,
            period_start="2024-02-28",
            period_end="2024-02-29",
            start_year=2023,
            end_year=2023,
            last_complete_data_date="2024-12-31",
        )
        self.assertEqual(len(result["evaluated_seasons"]), 1)
        season = result["seasons"][0]
        self.assertEqual(season["start_date"], "2023-02-28")
        self.assertEqual(season["end_date"], "2023-02-28")
        self.assertTrue(season["leap_day_adjusted"])
        self.assertEqual(season["leap_day_adjustments"], ["end"])
        self.assertTrue(any("February 29" in note for note in result["notes"]))

    def test_stats_min_90_boundary_includes_exact_and_excludes_below(self) -> None:
        """Spec §9.2 | Bug it catches: 90% boundary is rounded or off by one."""
        observations = _obs("2020-01-01", "2020-01-10")
        del observations["2020-01-10"]
        exact = self._map(
            observations,
            period_start="2020-01-01",
            period_end="2020-01-10",
            start_year=2020,
            end_year=2020,
            last_complete_data_date="2021-12-31",
        )
        self.assertEqual(len(exact["evaluated_seasons"]), 1)
        self.assertEqual(exact["seasons"][0]["valid_days"], 9)
        self.assertEqual(exact["seasons"][0]["total_days"], 10)
        self.assertEqual(exact["seasons"][0]["coverage_fraction"], 0.9)

        del observations["2020-01-09"]
        below = self._map(
            observations,
            period_start="2020-01-01",
            period_end="2020-01-10",
            start_year=2020,
            end_year=2020,
            last_complete_data_date="2021-12-31",
        )
        self.assertEqual(below["evaluated_seasons"], [])
        self.assertEqual(len(below["excluded_seasons"]), 1)
        self.assertIn("stats_min_90", below["excluded_seasons"][0]["reason"])

    def test_warnings_100_boundary_includes_exact_and_excludes_99(self) -> None:
        """Spec §9.2 | Bug it catches: warnings rule accepts incomplete coverage."""
        observations = _obs("2020-01-01", "2020-01-10")
        exact = self._map(
            observations,
            period_start="2020-01-01",
            period_end="2020-01-10",
            start_year=2020,
            end_year=2020,
            last_complete_data_date="2021-12-31",
            coverage_rule="warnings_100",
        )
        self.assertEqual(len(exact["evaluated_seasons"]), 1)

        del observations["2020-01-10"]
        below = self._map(
            observations,
            period_start="2020-01-01",
            period_end="2020-01-10",
            start_year=2020,
            end_year=2020,
            last_complete_data_date="2021-12-31",
            coverage_rule="warnings_100",
        )
        self.assertEqual(below["evaluated_seasons"], [])
        self.assertEqual(len(below["excluded_seasons"]), 1)
        self.assertIn("warnings_100", below["excluded_seasons"][0]["reason"])

    def test_missing_none_and_fill_values_are_invalid(self) -> None:
        """Spec §9.2 | Bug it catches: missing or fill values count as valid coverage."""
        cases = {
            "missing": {},
            "none": _obs("2020-01-01", "2020-01-10", None),
            "power_fill": _obs("2020-01-01", "2020-01-10", -999),
            "smap_fill": _obs("2020-01-01", "2020-01-10", -9999),
            "nan": _obs("2020-01-01", "2020-01-10", float("nan")),
        }
        for name, observations in cases.items():
            with self.subTest(name=name):
                result = self._map(
                    observations,
                    period_start="2020-01-01",
                    period_end="2020-01-10",
                    start_year=2020,
                    end_year=2020,
                    last_complete_data_date="2021-12-31",
                )
                self.assertEqual(result["evaluated_seasons"], [])
                self.assertEqual(len(result["excluded_seasons"]), 1)
                self.assertEqual(
                    result["excluded_seasons"][0]["valid_days"], 0
                )

    def test_invalid_coverage_rule_raises(self) -> None:
        """Spec §9.2 | Bug it catches: an unknown coverage rule silently falls back."""
        with self.assertRaises(ValueError):
            self._map(
                period_start="2020-01-01",
                period_end="2020-01-10",
                start_year=2020,
                end_year=2020,
                last_complete_data_date="2021-12-31",
                coverage_rule="unknown",
            )

    def test_result_is_json_serializable(self) -> None:
        """Spec §9.2 | Bug it catches: dates or non-finite values leak into JSON."""
        observations = _obs("2020-01-01", "2020-01-10")
        result = self._map(
            observations,
            period_start="2020-01-01",
            period_end="2020-01-10",
            start_year=2020,
            end_year=2020,
            last_complete_data_date="2021-12-31",
        )
        encoded = json.dumps(result, allow_nan=False)
        decoded = json.loads(encoded)
        self.assertEqual(decoded["seasons"][0]["valid_days"], 10)
        self.assertNotIn("NaN", encoded)

    def test_module_has_no_crop_id_branches(self) -> None:
        """Spec §9.2 | Bug it catches: a crop-specific branch is added to replay mapping."""
        source = SRC.read_text(encoding="utf-8")
        self.assertNotIn("crop_id", source)


if __name__ == "__main__":
    unittest.main()
