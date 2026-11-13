"""Tests for timeline, preparation, and waiting calculations (v1.md §10, §17.6-8)."""

import copy
import unittest
from pathlib import Path

from src.crop_profiles import load_crop_profiles
from src.timeline import (
    build_crop_timeline,
    calculate_next_planting,
    calculate_waiting,
    evaluate_waiting_limit,
)

REAL_CSV = (
    Path(__file__).resolve().parents[2]
    / "Data"
    / "fosol_cycle_rajshahi_crop_dataset.csv"
)
PREP = {"min_days": 7, "max_days": 10, "source_ids": ["synthetic://prep"]}


class TimelineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.profiles = load_crop_profiles(REAL_CSV)
        cls.wheat = cls.profiles["wheat_bari_gom33"]
        cls.aman = cls.profiles["aman_br11"]

    def _timeline(self, profile=None, preparation=None, verified=False):
        return build_crop_timeline(
            profile or self.wheat,
            {"earliest": "2026-11-15", "latest": "2026-11-30"},
            preparation,
            verified,
        )

    def test_harvest_range_propagates_both_duration_endpoints(self) -> None:
        """Spec §10.2 / §17.6 | Bug it catches: averaging or swapping duration endpoints."""
        result = self._timeline()
        self.assertEqual(
            result["harvest_range"],
            {"earliest": "2027-03-03", "latest": "2027-03-22"},
        )
        self.assertEqual(result["duration"]["min_days"], 108)
        self.assertEqual(result["duration"]["max_days"], 112)
        self.assertIsNone(result["ready_range"])

    def test_missing_duration_is_unknown_not_zero(self) -> None:
        """Spec §17.6 | Bug it catches: missing duration becomes zero or an invented harvest."""
        profile = copy.deepcopy(self.wheat)
        profile["variety_duration_min_days"] = None
        profile["variety_duration_max_days"] = None
        result = self._timeline(profile)
        self.assertIsNone(result["duration"])
        self.assertIsNone(result["harvest_range"])
        self.assertEqual(result["timing_status"], "unknown")
        self.assertEqual(result["timing_code"], "DURATION_EVIDENCE_MISSING")
        self.assertIn("preparation_time", result["missing_evidence"])

    def test_duration_crossing_leap_day_stays_calendar_correct(self) -> None:
        """Spec §17.5 | Bug it catches: day arithmetic skips or miscounts 29 February."""
        profile = copy.deepcopy(self.wheat)
        profile["variety_duration_min_days"] = 90
        profile["variety_duration_max_days"] = 91
        result = build_crop_timeline(
            profile,
            {"earliest": "2027-12-01", "latest": "2027-12-02"},
        )
        self.assertEqual(
            result["harvest_range"],
            {"earliest": "2028-02-29", "latest": "2028-03-02"},
        )

    def test_invalid_duration_forms_are_unknown(self) -> None:
        """Spec §17.6 | Bug it catches: min>max, negative, or text duration treated as usable."""
        cases = (
            (112, 108, "DURATION_EVIDENCE_INVALID"),
            (-1, 112, "DURATION_EVIDENCE_INVALID"),
            ("108", 112, "DURATION_EVIDENCE_INVALID"),
            (108, None, "DURATION_EVIDENCE_MISSING"),
        )
        for minimum, maximum, code in cases:
            with self.subTest(minimum=minimum, maximum=maximum):
                profile = copy.deepcopy(self.wheat)
                profile["variety_duration_min_days"] = minimum
                profile["variety_duration_max_days"] = maximum
                result = self._timeline(profile)
                self.assertIsNone(result["harvest_range"])
                self.assertEqual(result["timing_status"], "unknown")
                self.assertEqual(result["timing_code"], code)

    def test_transplanting_does_not_add_nursery_age(self) -> None:
        """Spec §10.1 | Bug it catches: 30-day Aman nursery age added to 145-day duration."""
        profile = copy.deepcopy(self.aman)
        result = build_crop_timeline(
            profile,
            {"earliest": "2026-07-10", "latest": "2026-07-24"},
        )
        self.assertEqual(
            result["harvest_range"],
            {"earliest": "2026-12-02", "latest": "2026-12-16"},
        )
        self.assertIn("NURSERY_AGE_NOT_ADDED", result["timing_codes"])
        self.assertFalse(result["nursery_age_added"])
        self.assertEqual(result["nursery_age_days"], {"min_days": 30, "max_days": 30})

    def test_unverified_duration_reference_is_conditional(self) -> None:
        """Spec §10.1 | Bug it catches: default duration stage silently assumed verified."""
        unverified = self._timeline(preparation=PREP)
        verified = self._timeline(preparation=PREP, verified=True)
        self.assertEqual(unverified["timing_status"], "conditional")
        self.assertIn("DURATION_REFERENCE_UNRESOLVED", unverified["timing_codes"])
        self.assertEqual(verified["timing_status"], "known")
        self.assertIsNone(verified["timing_code"])

    def test_missing_preparation_is_unknown_not_zero(self) -> None:
        """Spec §17.7 | Bug it catches: blank preparation replaced by a zero-day interval."""
        result = self._timeline()
        self.assertIsNone(result["preparation_range"])
        self.assertIsNone(result["ready_range"])
        self.assertEqual(result["timing_status"], "unknown")
        self.assertEqual(result["timing_code"], "PREPARATION_EVIDENCE_MISSING")
        self.assertIsNotNone(result["harvest_range"])

    def test_preparation_offsets_harvest_endpoints(self) -> None:
        """Spec §10.2 | Bug it catches: preparation added to the wrong endpoint or averaged."""
        result = self._timeline(preparation=PREP, verified=True)
        self.assertEqual(result["preparation_range"], {**PREP})
        self.assertEqual(
            result["ready_range"],
            {"earliest": "2027-03-10", "latest": "2027-04-01"},
        )

    def test_explicit_zero_preparation_is_valid_not_missing(self) -> None:
        """Spec §10.2 | Bug it catches: an explicit immediate-ready 0 confused with missing."""
        prep = {"min_days": 0, "max_days": 0, "source_ids": ["synthetic://prep"]}
        result = self._timeline(preparation=prep, verified=True)
        self.assertEqual(result["ready_range"], result["harvest_range"])
        self.assertEqual(result["timing_status"], "known")
        self.assertNotIn("PREPARATION_EVIDENCE_MISSING", result["timing_codes"])

    def test_invalid_preparation_forms_are_unknown(self) -> None:
        """Spec §10.2 | Bug it catches: negative, reversed, float, or text preparation accepted."""
        cases = (
            ({"min_days": -1, "max_days": 5}, "PREPARATION_EVIDENCE_INVALID"),
            ({"min_days": 8, "max_days": 3}, "PREPARATION_EVIDENCE_INVALID"),
            ({"min_days": 1.5, "max_days": 2}, "PREPARATION_EVIDENCE_INVALID"),
            ({"min_days": None, "max_days": 2}, "PREPARATION_EVIDENCE_MISSING"),
            ("seven days", "PREPARATION_EVIDENCE_INVALID"),
        )
        for prep, code in cases:
            with self.subTest(prep=prep):
                result = self._timeline(preparation=prep, verified=True)
                self.assertIsNone(result["preparation_range"])
                self.assertIsNone(result["ready_range"])
                self.assertEqual(result["timing_code"], code)

    def test_preparation_without_source_is_cautious(self) -> None:
        """Spec §10.2 | Bug it catches: unsourced preparation silently treated as verified."""
        prep = {"min_days": 7, "max_days": 10}
        result = self._timeline(preparation=prep, verified=True)
        self.assertIsNotNone(result["ready_range"])
        self.assertEqual(result["timing_status"], "conditional")
        self.assertEqual(result["timing_code"], "PREPARATION_SOURCE_MISSING")
        self.assertIn("preparation_source_ids", result["missing_evidence"])

    def test_single_day_planting_range_and_reversed_range_rejected(self) -> None:
        """Spec §10.2 | Bug it catches: endpoint off-by-one, or reversed range silently swapped."""
        result = build_crop_timeline(
            self.wheat,
            {"earliest": "2026-11-15", "latest": "2026-11-15"},
        )
        self.assertEqual(
            result["harvest_range"],
            {"earliest": "2027-03-03", "latest": "2027-03-07"},
        )
        with self.assertRaises(ValueError):
            build_crop_timeline(
                self.wheat,
                {"earliest": "2026-11-30", "latest": "2026-11-15"},
            )

    def test_next_planting_boundaries_and_clipping(self) -> None:
        """Spec §10.3 | Bug it catches: preferred/late/support boundaries and latest clipping."""
        window = {
            "preferred_start": "2027-02-01",
            "preferred_end": "2027-03-01",
            "supported_late_end": "2027-03-10",
        }
        cases = (
            (("2027-01-01", "2027-01-05"), "pass", "2027-02-01", "2027-02-01", False),
            (("2027-02-10", "2027-02-20"), "pass", "2027-02-10", "2027-02-20", False),
            (("2027-03-05", "2027-03-08"), "caution", "2027-03-05", "2027-03-08", False),
            (("2027-03-05", "2027-03-10"), "caution", "2027-03-05", "2027-03-10", False),
            (("2027-03-10", "2027-03-10"), "caution", "2027-03-10", "2027-03-10", False),
            (("2027-02-20", "2027-03-20"), "caution", "2027-02-20", "2027-03-10", True),
        )
        for ready, status, earliest, latest, clipped in cases:
            with self.subTest(ready=ready):
                result = calculate_next_planting(
                    {"earliest": ready[0], "latest": ready[1]}, window, True
                )
                self.assertEqual(result["status"], status)
                self.assertEqual(
                    result["next_planting_range"],
                    {"earliest": earliest, "latest": latest},
                )
                self.assertEqual(result["latest_clipped"], clipped)

        unsupported = calculate_next_planting(
            {"earliest": "2027-03-20", "latest": "2027-03-25"}, window, True
        )
        self.assertEqual(unsupported["status"], "unsupported")
        self.assertIsNone(unsupported["next_planting_range"])

    def test_unknown_preparation_uses_window_range_only(self) -> None:
        """Spec §10.3 | Bug it catches: claiming the crop follows on time when prep is unknown."""
        window = {
            "preferred_start": "2027-03-01",
            "preferred_end": "2027-03-31",
            "reference_date": "2027-02-01",
        }
        result = calculate_next_planting(None, window, False)
        self.assertEqual(
            result["next_planting_range"],
            {"earliest": "2027-03-01", "latest": "2027-03-31"},
        )
        self.assertEqual(result["timing_basis"], "window_only_preparation_unknown")
        self.assertEqual(result["timing_status"], "unknown")
        self.assertEqual(result["status"], "unknown")

        late = calculate_next_planting(
            None,
            {
                "preferred_start": "2027-03-01",
                "preferred_end": "2027-03-31",
                "supported_late_end": "2027-04-20",
                "reference_date": "2027-04-05",
            },
            False,
        )
        self.assertEqual(
            late["next_planting_range"],
            {"earliest": "2027-04-05", "latest": "2027-04-20"},
        )

    def test_waiting_range_is_ordered_and_total_matches_next_minus_harvest(self) -> None:
        """Spec §10.4 | Bug it catches: paired subtraction inverted when both dates precede the window."""
        result = calculate_waiting(
            {"earliest": "2027-02-01", "latest": "2027-02-01"},
            {"earliest": "2027-01-01", "latest": "2027-01-05"},
            {"earliest": "2026-12-20", "latest": "2026-12-25"},
            True,
        )
        self.assertEqual(result["waiting_range"], {"min": 27, "max": 31})
        self.assertEqual(result["total_interval_range_days"], {"min": 38, "max": 43})
        self.assertLessEqual(
            result["waiting_range"]["min"], result["waiting_range"]["max"]
        )

        clipped = calculate_waiting(
            {"earliest": "2027-02-01", "latest": "2027-03-10"},
            {"earliest": "2027-02-01", "latest": "2027-03-20"},
            {"earliest": "2026-12-01", "latest": "2026-12-20"},
            True,
        )
        self.assertGreaterEqual(clipped["waiting_range"]["min"], 0)
        self.assertGreaterEqual(clipped["total_interval_range_days"]["min"], 0)

    def test_clipped_latest_keeps_earliest_end_only(self) -> None:
        """Spec §10.4 | Bug it catches: clipped latest paired with latest ready/harvest."""
        result = calculate_waiting(
            {"earliest": "2027-02-01", "latest": "2027-03-10"},
            {"earliest": "2027-02-01", "latest": "2027-03-20"},
            {"earliest": "2026-12-01", "latest": "2026-12-20"},
            True,
            latest_invalid=True,
        )
        self.assertEqual(result["waiting_range"], {"min": 0, "max": None})
        self.assertEqual(
            result["total_interval_range_days"], {"min": 62, "max": None}
        )
        self.assertTrue(result["latest_invalid"])

    def test_waiting_limit_with_unknown_latest_is_partial_or_exceeds(self) -> None:
        """Spec §10.4 | Bug it catches: null latest treated as within or zero."""
        for waiting, limit, expected in (
            ({"min": 5, "max": None}, 10, "partial"),
            ({"min": 10, "max": None}, 10, "partial"),
            ({"min": 11, "max": None}, 10, "exceeds"),
        ):
            with self.subTest(waiting=waiting, limit=limit):
                result = evaluate_waiting_limit(waiting, limit)
                self.assertEqual(result["status"], expected)
                self.assertEqual(result["limit_days"], limit)

    def test_waiting_limit_statuses_are_inclusive_and_distinguish_overlap(self) -> None:
        """Spec §17.8 | Bug it catches: equality excludes, or partial overlap labeled complete."""
        cases = (
            ({"min": 5, "max": 10}, 10, "within"),
            ({"min": 5, "max": 10}, 9, "partial"),
            ({"min": 5, "max": 10}, 4, "exceeds"),
            ({"min": 5, "max": 10}, None, "not_configured"),
            (None, 10, "unknown"),
        )
        for waiting, limit, expected in cases:
            with self.subTest(waiting=waiting, limit=limit):
                result = evaluate_waiting_limit(waiting, limit)
                self.assertEqual(result["status"], expected)
                expected_basis = (
                    "not_configured" if expected == "not_configured" else "product_policy"
                )
                self.assertEqual(result["basis"], expected_basis)
                if expected != "not_configured":
                    self.assertEqual(result["limit_days"], limit)

    def test_waiting_and_total_are_none_without_preparation(self) -> None:
        """Spec §10.4 | Bug it catches: zero-filled waiting/total when readiness is unknown."""
        result = calculate_waiting(
            {"earliest": "2027-02-01", "latest": "2027-02-01"},
            None,
            {"earliest": "2026-12-20", "latest": "2026-12-25"},
            False,
        )
        self.assertIsNone(result["waiting_range"])
        self.assertIsNone(result["total_interval_range_days"])

    def test_known_preparation_requires_ready_range(self) -> None:
        """Spec §10.3 | Bug it catches: preparation_known=True silently falls back to window-only."""
        with self.assertRaises(ValueError):
            calculate_next_planting(
                None,
                {"preferred_start": "2027-02-01", "preferred_end": "2027-03-01"},
                True,
            )


if __name__ == "__main__":
    unittest.main()
