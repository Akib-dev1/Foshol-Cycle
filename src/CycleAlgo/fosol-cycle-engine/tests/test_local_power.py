"""Tests for the local POWER loader and seasonal ranges (v1.md §9)."""

import unittest

from src.local_power import load_local_power
from src.outlook import build_seasonal_ranges


class LocalPowerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.environment = load_local_power()

    def test_local_power_is_normalized_by_header(self) -> None:
        """Spec §15 | Bug it catches: local POWER columns/units/fill values drift."""
        env = self.environment
        self.assertEqual(env["source_id"], "local_power_2000_2026")
        self.assertEqual(env["observation_start"], "2000-01-01")
        self.assertEqual(env["observation_end"], "2026-10-20")
        self.assertEqual(len(env["observations"]), 9790)
        self.assertEqual(env["variables"]["T2M"]["units"], "C")
        self.assertEqual(env["variables"]["PRECTOTCORR"]["units"], "mm/day")
        self.assertIsNone(env["observations"]["2026-10-20"]["PRECTOTCORR"])

    def test_seasonal_ranges_cover_2000_to_2025(self) -> None:
        """Spec §9.1 | Bug it catches: seasonal ranges use wrong years or non-numeric ordering."""
        ranges = build_seasonal_ranges(
            self.environment,
            "2027-12-25",
            "2028-07-10",
            last_complete_data_date="2026-10-20",
        )
        self.assertEqual(ranges["status"], "ok")
        self.assertEqual(
            ranges["analysis_period"], {"start_year": 2000, "end_year": 2025}
        )
        self.assertEqual(ranges["coverage"]["seasons_total"], 26)
        self.assertEqual(
            [item["variable"] for item in ranges["indicators"]],
            ["T2M", "PRECTOTCORR", "GWETTOP"],
        )
        for indicator in ranges["indicators"]:
            self.assertLessEqual(indicator["min"], indicator["median"])
            self.assertLessEqual(indicator["median"], indicator["max"])
        self.assertFalse(ranges["thresholds_applied"])
        self.assertEqual(ranges["warnings"], [])
        self.assertEqual(ranges["source_ids"], ["local_power_2000_2026"])
        self.assertTrue(any("not a forecast" in note for note in ranges["notes"]))
        self.assertTrue(any("1991-1999" in note for note in ranges["notes"]))
        self.assertTrue(any("not SMAP" in note for note in ranges["notes"]))

    def test_api_history_does_not_inherit_local_precipitation_note(self) -> None:
        """Spec §9.1 | Bug it catches: API history is described with the local 1991-1999 exclusion."""
        api_environment = {
            **self.environment,
            "source_id": "nasa_power_daily",
        }
        ranges = build_seasonal_ranges(
            api_environment,
            "2027-12-25",
            "2028-07-10",
            start_year=2000,
            end_year=2025,
            last_complete_data_date="2026-10-20",
        )
        self.assertEqual(ranges["source_ids"], ["nasa_power_daily"])
        self.assertFalse(
            any("1991-1999" in note for note in ranges["notes"])
        )

    def test_missing_observations_make_ranges_unavailable(self) -> None:
        """Spec §9.1 | Bug it catches: missing POWER data becomes a zero range."""
        ranges = build_seasonal_ranges(
            {"observations": {}},
            "2027-12-25",
            "2028-07-10",
            last_complete_data_date="2026-10-20",
        )
        self.assertEqual(ranges["status"], "unavailable")
        for indicator in ranges["indicators"]:
            self.assertIsNone(indicator["min"])
            self.assertIsNone(indicator["median"])
            self.assertIsNone(indicator["max"])


if __name__ == "__main__":
    unittest.main()
