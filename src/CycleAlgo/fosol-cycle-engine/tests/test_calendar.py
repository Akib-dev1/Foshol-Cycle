"""Tests for the shared calendar evaluator (v1.md §6.1, §17.1–17.5)."""

import copy
import json
import unittest
from pathlib import Path

from src.calendar_evaluator import evaluate_calendar_fit
from src.crop_profiles import load_crop_profiles

REAL_CSV = (
    Path(__file__).resolve().parents[2]
    / "Data"
    / "fosol_cycle_rajshahi_crop_dataset.csv"
)
SRC_DIR = Path(__file__).resolve().parents[1] / "src"
CROP_IDS = (
    "aman_br11",
    "boro_brri_dhan28",
    "wheat_bari_gom33",
    "mustard_binasarisha9",
    "lentil_binamasur9",
    "mung_bari_mung6_kharif1",
    "maize_rabi_bari_hybrid13",
    "potato_bari_alu41",
)
REQUIRED_DETAIL_KEYS = {
    "planting_date",
    "plant_now",
    "preferred_start",
    "preferred_end",
    "supported_late_end",
    "next_window_start",
    "waiting_days",
    "waiting_limit_days",
    "waiting_limit_status",
    "date_precision",
    "hard_deadline_validated",
    "window_basis",
    "window_type",
    "algorithm_use_note",
}


def _synthetic_profile(**overrides) -> dict:
    """Build a profile shaped like ``load_crop_profiles`` output.

    Window bounds stay normalized at the top level; descriptive metadata lives
    only under ``raw`` so the evaluator's documented raw fallback is exercised.
    """
    values = {
        "preferred_start_mmdd": "07-10",
        "preferred_end_mmdd": "07-24",
        "supported_late_end_mmdd": None,
        "window_crosses_year": False,
        "planting_window_type": "SYNTHETIC_DAY_EXACT",
        "date_precision": "DAY",
        "window_basis": "synthetic test window",
        "hard_deadline_validated": "FALSE",
        "window_guard_readiness": "SYNTHETIC",
        "algorithm_use_note": "synthetic test only",
        "source_planting_window": "synthetic://planting",
        "source_local_calendar": "synthetic://calendar",
    }
    values.update(overrides)
    raw = {
        key: ("" if value is None else str(value)) for key, value in values.items()
    }
    return {
        "crop_id": "synthetic",
        "preferred_start_mmdd": values["preferred_start_mmdd"],
        "preferred_end_mmdd": values["preferred_end_mmdd"],
        "supported_late_end_mmdd": values["supported_late_end_mmdd"],
        "window_crosses_year": values["window_crosses_year"],
        "raw": raw,
    }


class RealProfileCalendarTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.profiles = load_crop_profiles(REAL_CSV)
        cls.aman = cls.profiles["aman_br11"]
        cls.boro = cls.profiles["boro_brri_dhan28"]

    def test_aman_preferred_window_passes_at_both_boundaries(self) -> None:
        for iso in ("2026-07-10", "2026-07-24"):
            with self.subTest(iso=iso):
                result = evaluate_calendar_fit(self.aman, iso)
                self.assertEqual(result["status"], "pass")
                self.assertEqual(result["code"], "PREFERRED_WINDOW")
                self.assertTrue(result["details"]["plant_now"])
                self.assertEqual(
                    result["details"]["preferred_start"], "2026-07-10"
                )
                self.assertEqual(result["details"]["preferred_end"], "2026-07-24")
                self.assertIsNone(result["details"]["supported_late_end"])
                self.assertEqual(result["details"]["date_precision"], "DAY")
                self.assertIs(
                    result["details"]["hard_deadline_validated"], False
                )
                self.assertEqual(
                    result["source_ids"],
                    ["source_planting_window", "source_local_calendar"],
                )

    def test_boro_documented_late_date_is_caution(self) -> None:
        result = evaluate_calendar_fit(self.boro, "2026-02-01")
        self.assertEqual(result["status"], "caution")
        self.assertEqual(result["code"], "LATE_WINDOW")
        self.assertTrue(result["details"]["plant_now"])
        self.assertEqual(result["details"]["preferred_start"], "2025-12-25")
        self.assertEqual(result["details"]["preferred_end"], "2026-01-10")
        self.assertEqual(result["details"]["supported_late_end"], "2026-02-28")
        self.assertEqual(result["details"]["window_start_year"], 2025)

    def test_aman_after_support_is_not_a_normal_candidate(self) -> None:
        result = evaluate_calendar_fit(self.aman, "2026-08-01")
        self.assertEqual(result["status"], "unsupported")
        self.assertEqual(result["code"], "OUTSIDE_SUPPORTED_WINDOW")
        self.assertFalse(result["details"]["plant_now"])
        self.assertIsNone(result["details"]["next_window_start"])

    def test_missing_late_window_is_not_a_biological_impossibility(self) -> None:
        result = evaluate_calendar_fit(self.aman, "2026-07-25")
        self.assertEqual(result["status"], "unsupported")
        self.assertEqual(result["code"], "OUTSIDE_SUPPORTED_WINDOW")
        reason = result["reason"].lower()
        self.assertIn("no documented late window", reason)
        self.assertIn("not a biological impossibility", reason)
        self.assertIn("not a proven deadline", reason)

    def test_boro_cross_year_windows_resolve_to_correct_years(self) -> None:
        january = evaluate_calendar_fit(self.boro, "2026-01-05")
        self.assertEqual(january["status"], "pass")
        self.assertEqual(january["code"], "PREFERRED_WINDOW")
        self.assertEqual(january["details"]["preferred_start"], "2025-12-25")
        self.assertEqual(january["details"]["preferred_end"], "2026-01-10")
        self.assertEqual(january["details"]["supported_late_end"], "2026-02-28")
        self.assertEqual(january["details"]["window_start_year"], 2025)

        december = evaluate_calendar_fit(self.boro, "2026-12-25")
        self.assertEqual(december["status"], "pass")
        self.assertEqual(december["code"], "PREFERRED_WINDOW")
        self.assertEqual(december["details"]["preferred_start"], "2026-12-25")
        self.assertEqual(december["details"]["preferred_end"], "2027-01-10")
        self.assertEqual(december["details"]["supported_late_end"], "2027-02-28")
        self.assertEqual(december["details"]["window_start_year"], 2026)

    def test_future_aman_window_starts_2026_07_10(self) -> None:
        result = evaluate_calendar_fit(self.aman, "2026-06-01")
        self.assertEqual(result["status"], "unknown")
        self.assertEqual(result["code"], "FUTURE_WINDOW_WAIT_POLICY_UNKNOWN")
        self.assertFalse(result["details"]["plant_now"])
        self.assertEqual(result["details"]["next_window_start"], "2026-07-10")
        self.assertEqual(result["details"]["waiting_days"], 39)
        self.assertIsNone(result["details"]["waiting_limit_days"])
        self.assertEqual(result["details"]["waiting_limit_status"], "unknown")

    def test_aman_january_is_a_future_option(self) -> None:
        result = evaluate_calendar_fit(self.aman, "2026-01-01")
        self.assertEqual(result["status"], "unknown")
        self.assertEqual(result["code"], "FUTURE_WINDOW_WAIT_POLICY_UNKNOWN")
        self.assertEqual(result["details"]["next_window_start"], "2026-07-10")
        self.assertEqual(result["details"]["waiting_days"], 190)
        self.assertFalse(result["details"]["plant_now"])

    def test_boro_after_late_support_is_unsupported(self) -> None:
        result = evaluate_calendar_fit(self.boro, "2026-06-01")
        self.assertEqual(result["status"], "unsupported")
        self.assertEqual(result["code"], "OUTSIDE_SUPPORTED_WINDOW")
        self.assertFalse(result["details"]["plant_now"])
        self.assertIsNone(result["details"]["next_window_start"])

    def test_boro_before_december_window_is_future(self) -> None:
        result = evaluate_calendar_fit(self.boro, "2026-11-01")
        self.assertEqual(result["status"], "unknown")
        self.assertEqual(result["code"], "FUTURE_WINDOW_WAIT_POLICY_UNKNOWN")
        self.assertEqual(result["details"]["next_window_start"], "2026-12-25")
        self.assertEqual(result["details"]["waiting_days"], 54)
        self.assertFalse(result["details"]["plant_now"])

    def test_boro_late_leap_bound_keeps_preferred_and_future_results(self) -> None:
        boro = copy.deepcopy(self.boro)
        boro["supported_late_end_mmdd"] = "02-29"
        boro["raw"]["supported_late_end_mmdd"] = "02-29"

        preferred = evaluate_calendar_fit(boro, "2026-01-05")
        self.assertEqual(preferred["status"], "pass")
        self.assertEqual(preferred["code"], "PREFERRED_WINDOW")
        self.assertTrue(preferred["details"]["plant_now"])
        self.assertEqual(preferred["details"]["preferred_start"], "2025-12-25")
        self.assertEqual(preferred["details"]["preferred_end"], "2026-01-10")
        self.assertIsNone(preferred["details"]["supported_late_end"])

        future = evaluate_calendar_fit(boro, "2026-12-01")
        self.assertEqual(future["status"], "unknown")
        self.assertEqual(future["code"], "FUTURE_WINDOW_WAIT_POLICY_UNKNOWN")
        self.assertEqual(future["details"]["next_window_start"], "2026-12-25")
        self.assertEqual(future["details"]["waiting_days"], 24)

        late = evaluate_calendar_fit(boro, "2026-02-01")
        self.assertEqual(late["status"], "unknown")
        self.assertEqual(late["code"], "WINDOW_LATE_END_UNRESOLVED")
        self.assertFalse(late["details"]["plant_now"])
        self.assertIsNone(late["details"]["supported_late_end"])
        self.assertIn("02-29", late["reason"])
        self.assertIn("late", late["reason"].lower())

        leap_late = evaluate_calendar_fit(boro, "2028-02-01")
        self.assertEqual(leap_late["status"], "caution")
        self.assertEqual(leap_late["code"], "LATE_WINDOW")
        self.assertEqual(
            leap_late["details"]["supported_late_end"], "2028-02-29"
        )

    def test_boro_boundary_edges(self) -> None:
        february = evaluate_calendar_fit(self.boro, "2025-02-28")
        self.assertEqual(february["status"], "caution")
        self.assertEqual(february["code"], "LATE_WINDOW")
        self.assertEqual(february["details"]["preferred_start"], "2024-12-25")
        self.assertEqual(february["details"]["preferred_end"], "2025-01-10")
        self.assertEqual(february["details"]["supported_late_end"], "2025-02-28")
        self.assertEqual(february["details"]["window_start_year"], 2024)

        march = evaluate_calendar_fit(self.boro, "2026-03-01")
        self.assertEqual(march["status"], "unsupported")
        self.assertEqual(march["code"], "OUTSIDE_SUPPORTED_WINDOW")

        december_24 = evaluate_calendar_fit(self.boro, "2025-12-24")
        self.assertEqual(december_24["status"], "unknown")
        self.assertEqual(
            december_24["code"], "FUTURE_WINDOW_WAIT_POLICY_UNKNOWN"
        )
        self.assertEqual(
            december_24["details"]["next_window_start"], "2025-12-25"
        )
        self.assertEqual(december_24["details"]["waiting_days"], 1)

        december_25 = evaluate_calendar_fit(self.boro, "2025-12-25")
        self.assertEqual(december_25["status"], "pass")
        self.assertEqual(december_25["code"], "PREFERRED_WINDOW")
        self.assertEqual(december_25["details"]["preferred_start"], "2025-12-25")

    def test_waiting_limit_zero_and_boro_exact_boundary(self) -> None:
        zero = evaluate_calendar_fit(
            self.aman, "2026-06-01", max_waiting_days=0
        )
        self.assertEqual(zero["status"], "unsupported")
        self.assertEqual(zero["code"], "FUTURE_WINDOW_EXCEEDS_LIMIT")
        self.assertEqual(zero["details"]["waiting_limit_days"], 0)
        self.assertEqual(zero["details"]["waiting_limit_status"], "exceeds_limit")

        exact = evaluate_calendar_fit(
            self.boro, "2026-11-01", max_waiting_days=54
        )
        self.assertEqual(exact["status"], "caution")
        self.assertEqual(exact["code"], "FUTURE_WINDOW_WITHIN_LIMIT")
        self.assertEqual(exact["details"]["waiting_days"], 54)
        self.assertEqual(exact["details"]["waiting_limit_status"], "within_limit")

        over = evaluate_calendar_fit(
            self.boro, "2026-11-01", max_waiting_days=53
        )
        self.assertEqual(over["status"], "unsupported")
        self.assertEqual(over["code"], "FUTURE_WINDOW_EXCEEDS_LIMIT")
        self.assertEqual(over["details"]["waiting_limit_status"], "exceeds_limit")

    def test_real_crop_status_contract_at_preferred_boundaries(self) -> None:
        cases = {
            "aman_br11": ("2026-07-10", "pass", "PREFERRED_WINDOW"),
            "boro_brri_dhan28": ("2025-12-25", "pass", "PREFERRED_WINDOW"),
            "wheat_bari_gom33": ("2026-11-15", "pass", "PREFERRED_WINDOW"),
            "mustard_binasarisha9": (
                "2026-10-25",
                "caution",
                "PREFERRED_WINDOW_APPROXIMATE",
            ),
            "lentil_binamasur9": (
                "2026-10-25",
                "caution",
                "PREFERRED_WINDOW_APPROXIMATE",
            ),
            "mung_bari_mung6_kharif1": (
                "2026-03-15",
                "unknown",
                "WINDOW_GEOGRAPHY_UNKNOWN",
            ),
            "maize_rabi_bari_hybrid13": (
                "2026-10-15",
                "pass",
                "PREFERRED_WINDOW",
            ),
            "potato_bari_alu41": (
                "2026-11-01",
                "caution",
                "PREFERRED_WINDOW_APPROXIMATE",
            ),
        }
        for crop_id, (iso, expected_status, expected_code) in cases.items():
            with self.subTest(crop_id=crop_id):
                result = evaluate_calendar_fit(self.profiles[crop_id], iso)
                self.assertEqual(result["status"], expected_status)
                self.assertEqual(result["code"], expected_code)
                self.assertEqual(result["details"]["preferred_start"], iso)

    def test_lentil_approximate_window_is_caution(self) -> None:
        result = evaluate_calendar_fit(
            self.profiles["lentil_binamasur9"], "2026-10-30"
        )
        self.assertEqual(result["status"], "caution")
        self.assertEqual(result["code"], "PREFERRED_WINDOW_APPROXIMATE")
        self.assertTrue(result["details"]["plant_now"])
        reason = result["reason"].lower()
        self.assertIn("approximate", reason)
        self.assertIn("not exact", reason)

    def test_mung_is_geography_unknown_even_inside_encoded_dates(self) -> None:
        result = evaluate_calendar_fit(
            self.profiles["mung_bari_mung6_kharif1"], "2026-03-20"
        )
        self.assertEqual(result["status"], "unknown")
        self.assertEqual(result["code"], "WINDOW_GEOGRAPHY_UNKNOWN")
        self.assertFalse(result["details"]["plant_now"])


class SyntheticCalendarTests(unittest.TestCase):
    def test_leap_day_window_accepts_leap_year_and_rejects_other_years(self) -> None:
        profile = _synthetic_profile(
            preferred_start_mmdd="02-29",
            preferred_end_mmdd="03-10",
        )
        leap = evaluate_calendar_fit(profile, "2028-02-29")
        self.assertEqual(leap["status"], "pass")
        self.assertEqual(leap["code"], "PREFERRED_WINDOW")
        self.assertEqual(leap["details"]["preferred_start"], "2028-02-29")
        self.assertEqual(leap["details"]["preferred_end"], "2028-03-10")

        for iso in ("2027-02-28", "2027-03-01"):
            with self.subTest(iso=iso):
                missing = evaluate_calendar_fit(profile, iso)
                self.assertEqual(missing["status"], "unknown")
                self.assertEqual(missing["code"], "WINDOW_DATE_MISSING")

    def test_early_january_window_uses_next_year_candidate(self) -> None:
        profile = _synthetic_profile(
            preferred_start_mmdd="01-05",
            preferred_end_mmdd="01-20",
        )
        inside = evaluate_calendar_fit(profile, "2026-01-10")
        self.assertEqual(inside["status"], "pass")
        self.assertEqual(inside["code"], "PREFERRED_WINDOW")

        future = evaluate_calendar_fit(profile, "2026-12-31")
        self.assertEqual(future["status"], "unknown")
        self.assertEqual(future["code"], "FUTURE_WINDOW_WAIT_POLICY_UNKNOWN")
        self.assertEqual(future["details"]["next_window_start"], "2027-01-05")
        self.assertEqual(future["details"]["waiting_days"], 5)

    def test_future_window_limit_within_and_exceeds(self) -> None:
        profile = _synthetic_profile()
        within = evaluate_calendar_fit(
            profile, "2026-06-01", max_waiting_days=39
        )
        self.assertEqual(within["status"], "caution")
        self.assertEqual(within["code"], "FUTURE_WINDOW_WITHIN_LIMIT")
        self.assertEqual(within["details"]["waiting_limit_days"], 39)
        self.assertEqual(within["details"]["waiting_limit_status"], "within_limit")
        self.assertFalse(within["details"]["plant_now"])

        exceeds = evaluate_calendar_fit(
            profile, "2026-06-01", max_waiting_days=38
        )
        self.assertEqual(exceeds["status"], "unsupported")
        self.assertEqual(exceeds["code"], "FUTURE_WINDOW_EXCEEDS_LIMIT")
        self.assertEqual(exceeds["details"]["waiting_limit_days"], 38)
        self.assertEqual(
            exceeds["details"]["waiting_limit_status"], "exceeds_limit"
        )

    def test_missing_required_fields_are_specific_unknowns(self) -> None:
        cases = (
            ("preferred_start_mmdd", "WINDOW_START_MISSING"),
            ("preferred_end_mmdd", "WINDOW_END_MISSING"),
            ("window_basis", "WINDOW_BASIS_MISSING"),
            ("planting_window_type", "WINDOW_TYPE_MISSING"),
            ("window_crosses_year", "WINDOW_CROSS_YEAR_MISSING"),
            ("date_precision", "WINDOW_PRECISION_MISSING"),
        )
        for field, expected_code in cases:
            with self.subTest(field=field):
                result = evaluate_calendar_fit(
                    _synthetic_profile(**{field: None}), "2026-07-10"
                )
                self.assertEqual(result["status"], "unknown")
                self.assertEqual(result["code"], expected_code)
                self.assertFalse(result["details"]["plant_now"])

    def test_inconsistent_cross_year_flag_is_unknown(self) -> None:
        cases = (
            {
                "preferred_start_mmdd": "07-10",
                "preferred_end_mmdd": "07-24",
                "window_crosses_year": True,
            },
            {
                "preferred_start_mmdd": "12-25",
                "preferred_end_mmdd": "01-10",
                "window_crosses_year": False,
            },
        )
        for overrides in cases:
            with self.subTest(overrides=overrides):
                result = evaluate_calendar_fit(
                    _synthetic_profile(**overrides), "2026-07-10"
                )
                self.assertEqual(result["status"], "unknown")
                self.assertEqual(result["code"], "WINDOW_DATA_INCONSISTENT")

    def test_late_bound_order_is_validated(self) -> None:
        cases = (
            (
                "non-cross next-year late",
                {
                    "preferred_start_mmdd": "11-15",
                    "preferred_end_mmdd": "11-30",
                    "supported_late_end_mmdd": "01-15",
                    "window_crosses_year": False,
                },
                "2027-01-05",
            ),
            (
                "cross-year December late",
                {
                    "preferred_start_mmdd": "12-25",
                    "preferred_end_mmdd": "01-10",
                    "supported_late_end_mmdd": "12-30",
                    "window_crosses_year": True,
                },
                "2026-06-01",
            ),
            (
                "late before preferred end",
                {
                    "preferred_start_mmdd": "01-01",
                    "preferred_end_mmdd": "03-01",
                    "supported_late_end_mmdd": "02-01",
                    "window_crosses_year": False,
                },
                "2026-02-15",
            ),
        )
        for label, overrides, iso in cases:
            with self.subTest(label=label):
                result = evaluate_calendar_fit(
                    _synthetic_profile(**overrides), iso
                )
                self.assertEqual(result["status"], "unknown")
                self.assertEqual(result["code"], "WINDOW_DATA_INCONSISTENT")
                self.assertFalse(result["details"]["plant_now"])

    def test_missing_precision_after_preferred_is_unknown(self) -> None:
        profile = _synthetic_profile(
            preferred_start_mmdd="12-25",
            preferred_end_mmdd="01-10",
            supported_late_end_mmdd="02-28",
            window_crosses_year=True,
            date_precision=None,
        )
        for iso in ("2026-01-05", "2026-02-01", "2026-03-01"):
            with self.subTest(iso=iso):
                result = evaluate_calendar_fit(profile, iso)
                self.assertEqual(result["status"], "unknown")
                self.assertEqual(result["code"], "WINDOW_PRECISION_MISSING")
                self.assertFalse(result["details"]["plant_now"])

    def test_mmdd_fields_use_normalized_top_level_only(self) -> None:
        start = _synthetic_profile()
        start["preferred_start_mmdd"] = None
        start["raw"]["preferred_start_mmdd"] = "07-10"
        result = evaluate_calendar_fit(start, "2026-07-10")
        self.assertEqual(result["status"], "unknown")
        self.assertEqual(result["code"], "WINDOW_START_MISSING")

        late = _synthetic_profile()
        late["supported_late_end_mmdd"] = None
        late["raw"]["supported_late_end_mmdd"] = "08-15"
        result = evaluate_calendar_fit(late, "2026-08-01")
        self.assertEqual(result["status"], "unsupported")
        self.assertEqual(result["code"], "OUTSIDE_SUPPORTED_WINDOW")

    def test_missing_sources_is_unknown(self) -> None:
        profile = _synthetic_profile(
            source_planting_window=None,
            source_local_calendar=None,
        )
        result = evaluate_calendar_fit(profile, "2026-07-10")
        self.assertEqual(result["status"], "unknown")
        self.assertEqual(result["code"], "WINDOW_SOURCE_MISSING")
        self.assertEqual(result["source_ids"], [])
        self.assertFalse(result["details"]["plant_now"])

    def test_non_crossing_december_window_new_year_policy(self) -> None:
        profile = _synthetic_profile(
            preferred_start_mmdd="12-20",
            preferred_end_mmdd="12-31",
        )
        december = evaluate_calendar_fit(profile, "2026-12-31")
        self.assertEqual(december["status"], "pass")
        self.assertEqual(december["code"], "PREFERRED_WINDOW")

        # Deliberate product policy: after New Year the just-ended December
        # season is not revived; the next December window is the future option.
        january = evaluate_calendar_fit(profile, "2027-01-01")
        self.assertEqual(january["status"], "unknown")
        self.assertEqual(
            january["code"], "FUTURE_WINDOW_WAIT_POLICY_UNKNOWN"
        )
        self.assertEqual(january["details"]["next_window_start"], "2027-12-20")
        self.assertEqual(january["details"]["waiting_days"], 353)
        self.assertFalse(january["details"]["plant_now"])

    def test_future_result_does_not_need_preferred_end(self) -> None:
        profile = _synthetic_profile(
            preferred_start_mmdd="08-01",
            preferred_end_mmdd="02-29",
            window_crosses_year=True,
        )
        result = evaluate_calendar_fit(profile, "2026-07-01")
        self.assertEqual(result["status"], "unknown")
        self.assertEqual(result["code"], "FUTURE_WINDOW_WAIT_POLICY_UNKNOWN")
        self.assertEqual(result["details"]["next_window_start"], "2026-08-01")
        self.assertEqual(result["details"]["waiting_days"], 31)
        self.assertIsNone(result["details"]["preferred_end"])

    def test_invalid_late_text_does_not_break_preferred_or_future(self) -> None:
        profile = _synthetic_profile(supported_late_end_mmdd="02-30")

        inside = evaluate_calendar_fit(profile, "2026-07-10")
        self.assertEqual(inside["status"], "pass")
        self.assertEqual(inside["code"], "PREFERRED_WINDOW")

        future = evaluate_calendar_fit(profile, "2026-06-01")
        self.assertEqual(future["status"], "unknown")
        self.assertEqual(
            future["code"], "FUTURE_WINDOW_WAIT_POLICY_UNKNOWN"
        )

        after = evaluate_calendar_fit(profile, "2026-08-01")
        self.assertEqual(after["status"], "unknown")
        self.assertEqual(after["code"], "WINDOW_LATE_END_INVALID")
        self.assertFalse(after["details"]["plant_now"])

    def test_invalid_inputs_are_rejected(self) -> None:
        profile = _synthetic_profile()
        with self.assertRaises(ValueError):
            evaluate_calendar_fit(profile, "2026-02-30")
        with self.assertRaises(ValueError):
            evaluate_calendar_fit(profile, "2026-07-10", max_waiting_days=-1)
        with self.assertRaises(TypeError):
            evaluate_calendar_fit(profile, "2026-07-10", max_waiting_days=1.5)


class ResultContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.profiles = load_crop_profiles(REAL_CSV)

    def test_every_result_is_json_serializable_and_complete(self) -> None:
        dates = (
            "2026-01-05",
            "2026-02-01",
            "2026-03-20",
            "2026-06-01",
            "2026-07-10",
            "2026-07-25",
            "2026-08-01",
            "2026-10-30",
            "2026-12-25",
        )
        allowed_statuses = {"pass", "caution", "unsupported", "unknown"}
        for crop_id, profile in self.profiles.items():
            for iso in dates:
                with self.subTest(crop_id=crop_id, iso=iso):
                    result = evaluate_calendar_fit(profile, iso)
                    self.assertEqual(
                        set(result),
                        {"status", "code", "reason", "source_ids", "details"},
                    )
                    self.assertIn(result["status"], allowed_statuses)
                    self.assertTrue(result["code"])
                    self.assertTrue(result["reason"])
                    self.assertTrue(result["source_ids"])
                    self.assertTrue(
                        REQUIRED_DETAIL_KEYS.issubset(result["details"])
                    )
                    self.assertEqual(result["details"]["planting_date"], iso)
                    json.dumps(result, allow_nan=False)

    def test_no_crop_id_specific_branch_in_src(self) -> None:
        source = "\n".join(
            path.read_text(encoding="utf-8") for path in SRC_DIR.glob("*.py")
        )
        for crop_id in CROP_IDS:
            with self.subTest(crop_id=crop_id):
                self.assertNotIn(crop_id, source)


if __name__ == "__main__":
    unittest.main()
