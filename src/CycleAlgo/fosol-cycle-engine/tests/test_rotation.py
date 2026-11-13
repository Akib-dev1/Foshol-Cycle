"""Tests for rotation compatibility indicators (v1.md §11)."""

import copy
import unittest
from pathlib import Path

from src.crop_profiles import load_crop_profiles
from src.rotation import evaluate_rotation

REAL_CSV = (
    Path(__file__).resolve().parents[2]
    / "Data"
    / "fosol_cycle_rajshahi_crop_dataset.csv"
)


class RotationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.profiles = load_crop_profiles(REAL_CSV)
        cls.aman = cls.profiles["aman_br11"]
        cls.boro = cls.profiles["boro_brri_dhan28"]
        cls.wheat = cls.profiles["wheat_bari_gom33"]
        cls.mustard = cls.profiles["mustard_binasarisha9"]
        cls.lentil = cls.profiles["lentil_binamasur9"]

    def test_same_family_is_caution_not_rejection(self) -> None:
        """Spec §11 | Bug it catches: consecutive Poaceae blocked instead of flagged for diversity."""
        result = evaluate_rotation(self.boro, self.aman, [self.aman])
        self.assertEqual(result["status"], "caution")
        self.assertEqual(result["code"], "SAME_FAMILY_REPEAT")
        self.assertEqual(result["matched_positions"], [1, 2])
        self.assertEqual(result["path_length"], 2)
        self.assertFalse(result["blocking"])
        self.assertTrue(result["diversity_indicator"])
        self.assertEqual(result["source_ids"], ["rotation_family_rule"])

    def test_non_consecutive_family_repeat_is_caution(self) -> None:
        """Spec §11 | Bug it catches: position-1 family repeat missed by previous-only comparison."""
        result = evaluate_rotation(self.boro, self.lentil, [self.boro, self.lentil])
        self.assertEqual(result["status"], "caution")
        self.assertEqual(result["code"], "FAMILY_REPEAT_IN_PATH")
        self.assertEqual(result["matched_positions"], [1, 3])
        self.assertEqual(result["path_length"], 3)
        self.assertEqual(
            result["path_crop_ids"],
            ["boro_brri_dhan28", "lentil_binamasur9", "boro_brri_dhan28"],
        )
        self.assertFalse(result["blocking"])
        self.assertFalse(result["rule_machine_readable"])

        maize = evaluate_rotation(
            self.profiles["maize_rabi_bari_hybrid13"],
            self.lentil,
            [self.boro, self.lentil],
        )
        self.assertEqual(maize["status"], "caution")
        self.assertEqual(maize["code"], "FAMILY_REPEAT_IN_PATH")
        self.assertEqual(maize["matched_positions"], [1, 3])
        self.assertEqual(maize["path_length"], 3)

    def test_family_change_passes_without_overclaiming(self) -> None:
        """Spec §11 | Bug it catches: family change claimed to establish disease or soil benefits."""
        result = evaluate_rotation(self.mustard, self.lentil, [self.lentil])
        self.assertEqual(result["status"], "pass")
        self.assertEqual(result["code"], "FAMILY_DIVERSIFIED")
        self.assertEqual(result["matched_positions"], [])
        self.assertEqual(result["path_length"], 2)
        self.assertIn("does not establish", result["reason"])
        self.assertFalse(result["blocking"])

    def test_legume_presence_is_potential_not_guaranteed(self) -> None:
        """Spec §11 | Bug it catches: legume path treated as a guaranteed nitrogen credit."""
        with_legume = evaluate_rotation(
            self.wheat, self.mustard, [self.lentil, self.mustard]
        )
        without = evaluate_rotation(self.boro, self.aman, [self.aman])
        self.assertTrue(with_legume["legume_present_in_path"])
        self.assertEqual(with_legume["path_length"], 3)
        self.assertIn("lentil_binamasur9", with_legume["legume_crop_ids"])
        self.assertIn("not a guaranteed", with_legume["legume_note"])
        self.assertFalse(without["legume_present_in_path"])

    def test_advisory_text_is_not_machine_readable(self) -> None:
        """Spec §11 | Bug it catches: free-text rotation rule treated as a blocking rule."""
        result = evaluate_rotation(self.lentil, self.wheat, [self.wheat])
        self.assertIsNotNone(result["rotation_family_rule"])
        self.assertIsNotNone(result["rotation_note"])
        self.assertFalse(result["rule_machine_readable"])
        self.assertEqual(result["machine_readable_rule_source_ids"], [])
        self.assertFalse(result["blocking"])

    def test_missing_family_is_unknown_not_pass(self) -> None:
        """Spec §11 | Bug it catches: absent family evidence becomes an automatic pass."""
        profile = copy.deepcopy(self.mustard)
        profile["family"] = None
        result = evaluate_rotation(profile, self.lentil, [self.lentil])
        self.assertEqual(result["status"], "unknown")
        self.assertEqual(result["code"], "ROTATION_FAMILY_EVIDENCE_MISSING")
        self.assertEqual(result["matched_positions"], [])
        self.assertIn("crop_family", result["missing_evidence"])
        self.assertFalse(result["blocking"])

        prior_missing = copy.deepcopy(self.lentil)
        prior_missing["family"] = None
        prior_result = evaluate_rotation(self.boro, prior_missing, [prior_missing])
        self.assertEqual(prior_result["status"], "unknown")
        self.assertEqual(prior_result["code"], "ROTATION_FAMILY_EVIDENCE_MISSING")

    def test_family_comparison_ignores_case_and_surrounding_space(self) -> None:
        """Spec §11 | Bug it catches: ' Poaceae ' treated as a different family."""
        profile = copy.deepcopy(self.boro)
        profile["family"] = " poaceae "
        result = evaluate_rotation(profile, self.aman, [self.aman])
        self.assertEqual(result["status"], "caution")
        self.assertEqual(result["code"], "SAME_FAMILY_REPEAT")

    def test_path_keeps_positions_and_reads_text_legume_flag(self) -> None:
        """Spec §11 | Bug it catches: duplicate crop ID dropped from path positions or 'TRUE' legume flag ignored."""
        profile = copy.deepcopy(self.mustard)
        profile["is_legume_n_fixing"] = "TRUE"
        result = evaluate_rotation(profile, profile, [profile])
        self.assertEqual(result["status"], "caution")
        self.assertEqual(result["code"], "SAME_FAMILY_REPEAT")
        self.assertEqual(result["path_length"], 2)
        self.assertEqual(
            result["path_crop_ids"],
            ["mustard_binasarisha9", "mustard_binasarisha9"],
        )
        self.assertTrue(result["legume_present_in_path"])
        self.assertEqual(result["legume_crop_ids"], ["mustard_binasarisha9"])


if __name__ == "__main__":
    unittest.main()
