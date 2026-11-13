"""Tests for the crop-profile loader."""

import tempfile
import unittest
from pathlib import Path

from src.crop_profiles import load_crop_profiles

REAL_CSV = (
    Path(__file__).resolve().parents[2]
    / "Data"
    / "fosol_cycle_rajshahi_crop_dataset.csv"
)

EXPECTED_CROP_IDS = {
    "aman_br11",
    "boro_brri_dhan28",
    "wheat_bari_gom33",
    "mustard_binasarisha9",
    "lentil_binamasur9",
    "mung_bari_mung6_kharif1",
    "maize_rabi_bari_hybrid13",
    "potato_bari_alu41",
}


def _load_csv_text(text: str) -> dict[str, dict]:
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "crops.csv"
        path.write_text(text, encoding="utf-8")
        return load_crop_profiles(path)


class RealDatasetTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.profiles = load_crop_profiles(REAL_CSV)

    def test_loads_exactly_eight_profiles(self) -> None:
        self.assertEqual(len(self.profiles), 8)
        self.assertEqual(set(self.profiles), EXPECTED_CROP_IDS)

    def test_requested_crop_ids_are_present(self) -> None:
        for crop_id in (
            "aman_br11",
            "boro_brri_dhan28",
            "wheat_bari_gom33",
            "mustard_binasarisha9",
            "lentil_binamasur9",
            "mung_bari_mung6_kharif1",
            "maize_rabi_bari_hybrid13",
            "potato_bari_alu41",
        ):
            with self.subTest(crop_id=crop_id):
                self.assertIn(crop_id, self.profiles)

    def test_removed_crops_are_absent_from_ids_and_names(self) -> None:
        for profile in self.profiles.values():
            searchable = " ".join(
                str(profile.get(field) or "")
                for field in ("crop_id", "name_en", "name_bn")
            ).lower()
            for crop in ("tomato", "cucumber", "garlic"):
                with self.subTest(crop_id=profile["crop_id"], crop=crop):
                    self.assertNotIn(crop, searchable)

    def test_names_and_variety_are_normalized(self) -> None:
        aman = self.profiles["aman_br11"]
        self.assertEqual(aman["name_en"], "T. Aman rice")
        self.assertEqual(aman["name_bn"], "আমন ধান")
        self.assertEqual(aman["reference_variety"], "BR11")
        self.assertNotIn("name_en", aman["data_quality"]["missing_fields"])
        self.assertNotIn("name_bn", aman["data_quality"]["missing_fields"])

    def test_boro_window_crosses_year_with_parsed_bounds(self) -> None:
        boro = self.profiles["boro_brri_dhan28"]
        self.assertIs(boro["window_crosses_year"], True)
        self.assertEqual(boro["preferred_start_mmdd"], "12-25")
        self.assertEqual(boro["preferred_end_mmdd"], "01-10")

    def test_duration_ranges_are_integers_in_order(self) -> None:
        for crop_id, profile in self.profiles.items():
            for suffix in ("variety_duration", "seedling_age"):
                low = profile[f"{suffix}_min_days"]
                high = profile[f"{suffix}_max_days"]
                with self.subTest(crop_id=crop_id, field=suffix):
                    if low is not None:
                        self.assertIsInstance(low, int)
                    if high is not None:
                        self.assertIsInstance(high, int)
                    if low is not None and high is not None:
                        self.assertLessEqual(low, high)


class ValidationTests(unittest.TestCase):
    def test_empty_csv_raises_value_error(self) -> None:
        with self.assertRaises(ValueError):
            _load_csv_text("")

    def test_header_only_csv_raises_value_error(self) -> None:
        with self.assertRaises(ValueError):
            _load_csv_text("crop_id,crop_name_en\n")

    def test_duplicate_crop_id_raises_value_error(self) -> None:
        text = "crop_id,crop_name_en\naman_br11,T. Aman rice\naman_br11,Duplicate\n"
        with self.assertRaises(ValueError):
            _load_csv_text(text)

    def test_blank_value_is_none_and_missing(self) -> None:
        text = (
            "crop_id,crop_name_en,crop_name_bn,preferred_start_mmdd\n"
            "mung_test,Mung,,03-15\n"
        )
        profile = _load_csv_text(text)["mung_test"]
        self.assertIsNone(profile["name_bn"])
        self.assertIn("name_bn", profile["data_quality"]["missing_fields"])
        self.assertNotIn("name_bn", profile["data_quality"]["unclear_fields"])

    def test_invalid_mmdd_is_none_and_unclear(self) -> None:
        text = "crop_id,preferred_start_mmdd\nmung_test,13-40\n"
        profile = _load_csv_text(text)["mung_test"]
        self.assertIsNone(profile["preferred_start_mmdd"])
        self.assertIn(
            "preferred_start_mmdd", profile["data_quality"]["unclear_fields"]
        )

    def test_leap_day_is_valid_but_february_30_is_not(self) -> None:
        text = (
            "crop_id,preferred_start_mmdd,preferred_end_mmdd\n"
            "valid_test,02-29,02-29\n"
            "invalid_test,02-30,03-01\n"
        )
        profiles = _load_csv_text(text)
        self.assertEqual(profiles["valid_test"]["preferred_start_mmdd"], "02-29")
        self.assertIsNone(profiles["invalid_test"]["preferred_start_mmdd"])
        self.assertIn(
            "preferred_start_mmdd",
            profiles["invalid_test"]["data_quality"]["unclear_fields"],
        )

    def test_min_greater_than_max_clears_pair_and_flags_unclear(self) -> None:
        text = (
            "crop_id,variety_duration_min_days,variety_duration_max_days\n"
            "bad_range,120,100\n"
        )
        profile = _load_csv_text(text)["bad_range"]
        self.assertIsNone(profile["variety_duration_min_days"])
        self.assertIsNone(profile["variety_duration_max_days"])
        self.assertIn(
            "variety_duration_min_days",
            profile["data_quality"]["unclear_fields"],
        )
        self.assertIn(
            "variety_duration_max_days",
            profile["data_quality"]["unclear_fields"],
        )
        self.assertTrue(profile["data_quality"]["notes"])

    def test_raw_row_is_preserved(self) -> None:
        text = "crop_id,crop_name_en,unknown_column\ncrop_x,Crop X,keep me\n"
        profile = _load_csv_text(text)["crop_x"]
        self.assertEqual(profile["raw"]["unknown_column"], "keep me")
        self.assertNotIn("unknown_column", profile)


if __name__ == "__main__":
    unittest.main()
