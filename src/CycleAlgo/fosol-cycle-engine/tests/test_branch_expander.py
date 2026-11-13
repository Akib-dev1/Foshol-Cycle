"""Tests for deterministic three-crop branch expansion (v1.md §10, §11, §17.12)."""

import copy
import datetime as dt
import json
import re
import unittest
from pathlib import Path

import src.branch_expander as branch_expander
from src.branch_expander import expand_branches
from src.crop_profiles import load_crop_profiles

REAL_CSV = (
    Path(__file__).resolve().parents[2]
    / "Data"
    / "fosol_cycle_rajshahi_crop_dataset.csv"
)
SRC_DIR = Path(__file__).resolve().parents[1] / "src"
SUBSET = ("mustard_binasarisha9", "boro_brri_dhan28", "aman_br11")


def _synthetic_branch(branch_id, ranges, crop_ids=("crop_a", "crop_b", "crop_c")):
    return {
        "branch_id": branch_id,
        "crops": [
            {
                "position": index + 1,
                "crop_id": crop_id,
                "planting_range": {"earliest": window[0], "latest": window[1]},
            }
            for index, (crop_id, window) in enumerate(zip(crop_ids, ranges))
        ],
        "transitions": [],
    }


class BranchExpanderTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.profiles = load_crop_profiles(REAL_CSV)

    def _run(self, profiles=None, start="2026-11-06", **overrides):
        # Legacy E6 cases used one shared limit; mirror it for the initial
        # window only when the test supplies it explicitly.
        if (
            "max_initial_wait_days" not in overrides
            and overrides.get("max_waiting_days") is not None
        ):
            overrides["max_initial_wait_days"] = overrides["max_waiting_days"]
        return expand_branches(profiles or self.profiles, start, **overrides)

    def _branches_with(self, result, crop_id, position=None):
        found = []
        for branch in result["branches"]:
            for index, crop in enumerate(branch["crops"]):
                if crop["crop_id"] == crop_id and position in (None, index + 1):
                    found.append(branch)
                    break
        return found

    def test_every_branch_has_exactly_three_crops_and_two_transitions(self) -> None:
        """Spec §10.5 / §17.12 | Bug it catches: a fourth crop or a missing transition.""" 
        result = self._run(max_waiting_days=365, max_branches=20)
        self.assertTrue(result["branches"])
        for branch in result["branches"]:
            with self.subTest(branch=branch["branch_id"]):
                self.assertEqual(len(branch["crops"]), 3)
                self.assertEqual(len(branch["transitions"]), 2)
                self.assertEqual(
                    [crop["position"] for crop in branch["crops"]], [1, 2, 3]
                )
                self.assertEqual(
                    [t["to_position"] for t in branch["transitions"]], [2, 3]
                )
                self.assertIn(branch["status"], ("candidate", "conditional"))
                self.assertRegex(branch["branch_id"], r"^b_[0-9a-f]{12}$")

    def test_result_is_json_serializable_without_nan(self) -> None:
        """Spec §14.4 | Bug it catches: NaN or a non-serializable date leaks into JSON."""
        result = self._run(max_waiting_days=365, max_branches=5)
        encoded = json.dumps(result, allow_nan=False)
        decoded = json.loads(encoded)
        self.assertNotIn("NaN", encoded)
        self.assertEqual(len(decoded["branches"]), 5)

    def test_repeated_request_is_identical(self) -> None:
        """Spec §14.4 | Bug it catches: branch IDs or ordering change between identical calls."""
        first = self._run(max_waiting_days=365, max_branches=5)
        second = self._run(max_waiting_days=365, max_branches=5)
        self.assertEqual(json.dumps(first, sort_keys=True), json.dumps(second, sort_keys=True))
        self.assertEqual(
            [branch["branch_id"] for branch in first["branches"]],
            [branch["branch_id"] for branch in second["branches"]],
        )

    def test_uniqueness_contract_is_present(self) -> None:
        """Spec §14.4 | Bug it catches: response omits uniqueness, so duplicate IDs/sequences go unchecked."""
        result = self._run(max_waiting_days=365, max_branches=5)
        uniqueness = result["uniqueness"]
        self.assertEqual(uniqueness["branch_count"], 5)
        self.assertTrue(uniqueness["branch_ids_unique"])
        self.assertEqual(uniqueness["duplicate_branch_ids"], [])
        self.assertEqual(uniqueness["sequence_count"], 5)
        self.assertEqual(uniqueness["duplicate_sequences"], [])
        self.assertIn("unique for the selected request", uniqueness["rule"])

    def test_uniqueness_allows_same_sequence_with_different_windows(self) -> None:
        """Spec §14.4 | Bug it catches: same crop sequence with different windows collapsed or rejected."""
        branches = [
            _synthetic_branch(
                "b_000000000001",
                [
                    ("2027-01-01", "2027-01-02"),
                    ("2027-02-01", "2027-02-02"),
                    ("2027-03-01", "2027-03-02"),
                ],
            ),
            _synthetic_branch(
                "b_000000000002",
                [
                    ("2027-04-01", "2027-04-02"),
                    ("2027-05-01", "2027-05-02"),
                    ("2027-06-01", "2027-06-02"),
                ],
            ),
        ]
        result = branch_expander.check_branch_uniqueness(branches)
        self.assertEqual(result["branch_count"], 2)
        self.assertTrue(result["branch_ids_unique"])
        self.assertEqual(result["duplicate_branch_ids"], [])
        self.assertEqual(result["sequence_count"], 1)
        self.assertEqual(len(result["duplicate_sequences"]), 1)
        duplicate = result["duplicate_sequences"][0]
        self.assertEqual(duplicate["crop_ids"], ["crop_a", "crop_b", "crop_c"])
        self.assertEqual(
            duplicate["branch_ids"],
            ["b_000000000001", "b_000000000002"],
        )
        self.assertEqual(len(duplicate["window_keys"]), 2)
        self.assertNotEqual(duplicate["window_keys"][0], duplicate["window_keys"][1])
        self.assertIn("ordered crop/window choices", result["rule"])

    def test_uniqueness_flags_duplicate_branch_ids(self) -> None:
        """Spec §14.4 | Bug it catches: duplicate branch_id accepted as unique."""
        branches = [
            _synthetic_branch(
                "b_000000000001",
                [
                    ("2027-01-01", "2027-01-02"),
                    ("2027-02-01", "2027-02-02"),
                    ("2027-03-01", "2027-03-02"),
                ],
            ),
            _synthetic_branch(
                "b_000000000001",
                [
                    ("2027-04-01", "2027-04-02"),
                    ("2027-05-01", "2027-05-02"),
                    ("2027-06-01", "2027-06-02"),
                ],
            ),
        ]
        result = branch_expander.check_branch_uniqueness(branches)
        self.assertEqual(result["branch_count"], 2)
        self.assertFalse(result["branch_ids_unique"])
        self.assertEqual(result["duplicate_branch_ids"], ["b_000000000001"])
        self.assertEqual(result["sequence_count"], 1)
        self.assertEqual(len(result["duplicate_sequences"]), 1)
        self.assertEqual(
            result["duplicate_sequences"][0]["branch_ids"],
            ["b_000000000001", "b_000000000001"],
        )

    def test_first_crop_roots_exclude_unknown_and_unsupported(self) -> None:
        """Spec §6.1 | Bug it catches: mung root shown despite missing window geography."""
        result = self._run(max_waiting_days=365)
        root_ids = {branch["crops"][0]["crop_id"] for branch in result["branches"]}
        self.assertNotIn("mung_bari_mung6_kharif1", root_ids)
        self.assertIn("boro_brri_dhan28", root_ids)
        self.assertTrue(
            any(
                exclusion["at_position"] == 1
                and exclusion["crop_ids"] == ["mung_bari_mung6_kharif1"]
                and exclusion["code"] == "WINDOW_GEOGRAPHY_UNKNOWN"
                for exclusion in result["excluded_paths"]
            )
        )

        no_wait = self._run(max_waiting_days=0)
        no_wait_roots = {
            branch["crops"][0]["crop_id"] for branch in no_wait["branches"]
        }
        self.assertNotIn("boro_brri_dhan28", no_wait_roots)
        self.assertTrue(
            any(
                exclusion["code"] == "FUTURE_WINDOW_EXCEEDS_LIMIT"
                for exclusion in no_wait["excluded_paths"]
            )
        )

        no_policy = self._run(max_waiting_days=None)
        no_policy_roots = {
            branch["crops"][0]["crop_id"] for branch in no_policy["branches"]
        }
        self.assertNotIn("boro_brri_dhan28", no_policy_roots)
        self.assertNotIn("aman_br11", no_policy_roots)
        self.assertTrue(
            any(
                exclusion["code"] == "FUTURE_WINDOW_WAIT_POLICY_UNKNOWN"
                for exclusion in no_policy["excluded_paths"]
            )
        )

    def test_future_root_is_caution_and_uses_the_future_window(self) -> None:
        """Spec §6.1 / §10.3 | Bug it catches: a future window reported as plant-now or wrong range."""
        result = self._run(max_waiting_days=365)
        branches = self._branches_with(result, "boro_brri_dhan28", position=1)
        self.assertTrue(branches)
        crop = branches[0]["crops"][0]
        self.assertEqual(
            crop["planting_range"],
            {"earliest": "2026-12-25", "latest": "2027-01-10"},
        )
        self.assertEqual(crop["checks"]["calendar"]["status"], "caution")
        self.assertEqual(
            crop["checks"]["calendar"]["code"], "FUTURE_WINDOW_WITHIN_LIMIT"
        )
        self.assertEqual(branches[0]["status"], "conditional")

    def test_next_season_windows_roll_forward_within_limit(self) -> None:
        """Spec §10.3/§10.5 | Bug it catches: a next-year window rejected as OUTSIDE_SUPPORTED_WINDOW."""
        result = self._run(max_waiting_days=365)
        aman_roots = self._branches_with(result, "aman_br11", position=1)
        self.assertTrue(aman_roots)
        aman = aman_roots[0]["crops"][0]
        self.assertEqual(
            aman["planting_range"],
            {"earliest": "2027-07-10", "latest": "2027-07-24"},
        )
        self.assertEqual(aman["checks"]["calendar"]["status"], "caution")
        self.assertEqual(
            aman["checks"]["calendar"]["code"], "FUTURE_WINDOW_WITHIN_LIMIT"
        )

        rolled_profiles = {
            crop_id: self.profiles[crop_id]
            for crop_id in (
                "mustard_binasarisha9",
                "mung_bari_mung6_kharif1",
                "boro_brri_dhan28",
            )
        }
        path = [
            "mustard_binasarisha9",
            "mung_bari_mung6_kharif1",
            "boro_brri_dhan28",
        ]
        rolled = self._run(rolled_profiles, max_waiting_days=365)
        rolled_branch = next(
            (
                branch
                for branch in rolled["branches"]
                if [crop["crop_id"] for crop in branch["crops"]] == path
            ),
            None,
        )
        self.assertIsNotNone(rolled_branch)
        self.assertEqual(
            rolled_branch["crops"][2]["planting_range"],
            {"earliest": "2027-12-25", "latest": "2028-01-10"},
        )
        self.assertFalse(
            any(
                exclusion["crop_ids"] == path
                and exclusion["code"] == "OUTSIDE_SUPPORTED_WINDOW"
                for exclusion in rolled["excluded_paths"]
            )
        )

        for limit, expected in ((230, True), (229, False)):
            with self.subTest(transition_limit=limit):
                boundary = self._run(rolled_profiles, max_waiting_days=limit)
                present = any(
                    [crop["crop_id"] for crop in branch["crops"]] == path
                    for branch in boundary["branches"]
                )
                self.assertEqual(present, expected)
                if not expected:
                    self.assertTrue(
                        any(
                            exclusion["crop_ids"] == path
                            and exclusion["code"]
                            == "FUTURE_WINDOW_EXCEEDS_LIMIT"
                            for exclusion in boundary["excluded_paths"]
                        )
                    )

        aman_246 = self._run(max_waiting_days=246)
        self.assertGreater(
            len(self._branches_with(aman_246, "aman_br11", position=1)), 0
        )

        root_boundary = self._run(max_waiting_days=245)
        self.assertEqual(
            len(self._branches_with(root_boundary, "aman_br11", position=1)), 0
        )
        self.assertTrue(
            any(
                exclusion["crop_ids"] == ["aman_br11"]
                and exclusion["code"] == "FUTURE_WINDOW_EXCEEDS_LIMIT"
                for exclusion in root_boundary["excluded_paths"]
            )
        )

        no_policy = self._run(max_waiting_days=None)
        self.assertEqual(
            len(self._branches_with(no_policy, "aman_br11", position=1)), 0
        )

    def test_initial_wait_boundary_is_separate_from_transitions(self) -> None:
        """Spec §6.1/§10.4 | Bug it catches: root wait uses the transition limit."""
        start = dt.date(2026, 1, 1)
        future_start = start + dt.timedelta(days=180)
        profile = copy.deepcopy(self.profiles["wheat_bari_gom33"])
        profile.update(
            {
                "crop_id": "synthetic_initial_wait",
                "preferred_start_mmdd": future_start.strftime("%m-%d"),
                "preferred_end_mmdd": (future_start + dt.timedelta(days=20)).strftime(
                    "%m-%d"
                ),
                "supported_late_end_mmdd": None,
                "window_crosses_year": False,
                "planting_window_type": "SYNTHETIC_DAY_EXACT",
                "date_precision": "DAY",
                "window_basis": "synthetic initial-wait boundary",
            }
        )
        profiles = {"synthetic_initial_wait": profile}
        for limit in (180, 181):
            with self.subTest(limit=limit):
                result = expand_branches(
                    profiles,
                    start.isoformat(),
                    max_waiting_days=365,
                    max_initial_wait_days=limit,
                )
                self.assertTrue(result["branches"])
                self.assertEqual(result["request"]["max_initial_wait_days"], limit)
                crop = result["branches"][0]["crops"][0]
                self.assertEqual(crop["planting_range"]["earliest"], future_start.isoformat())
                self.assertEqual(result["branches"][0]["initial_wait_days"], 180)
                self.assertEqual(crop["checks"]["calendar"]["status"], "caution")
                self.assertEqual(
                    crop["checks"]["calendar"]["code"],
                    "FUTURE_WINDOW_WITHIN_LIMIT",
                )

        for limit, expected_code in ((179, "FUTURE_WINDOW_EXCEEDS_LIMIT"), (None, "FUTURE_WINDOW_WAIT_POLICY_UNKNOWN")):
            with self.subTest(limit=limit):
                result = expand_branches(
                    profiles,
                    start.isoformat(),
                    max_waiting_days=365,
                    max_initial_wait_days=limit,
                )
                self.assertEqual(result["branches"], [])
                self.assertTrue(
                    any(
                        exclusion["at_position"] == 1
                        and exclusion["crop_ids"] == ["synthetic_initial_wait"]
                        and exclusion["code"] == expected_code
                        for exclusion in result["excluded_paths"]
                    )
                )
                if limit == 179:
                    self.assertTrue(
                        any(
                            "product relevance cutoff" in exclusion["reason"]
                            for exclusion in result["excluded_paths"]
                        )
                    )

    def test_first_crop_late_window_uses_late_range(self) -> None:
        """Spec §6.1 / §10.3 | Bug it catches: late start uses the preferred end instead of its own range."""
        profiles = {crop_id: self.profiles[crop_id] for crop_id in SUBSET}
        result = self._run(profiles, start="2026-12-01", max_waiting_days=365)
        branches = self._branches_with(result, "mustard_binasarisha9", position=1)
        self.assertTrue(branches)
        crop = branches[0]["crops"][0]
        self.assertEqual(
            crop["planting_range"],
            {"earliest": "2026-12-01", "latest": "2026-12-21"},
        )
        self.assertEqual(crop["checks"]["calendar"]["code"], "LATE_WINDOW")
        self.assertEqual(crop["checks"]["calendar"]["status"], "caution")

    def test_missing_preparation_leaves_waiting_unknown(self) -> None:
        """Spec §17.7 | Bug it catches: unknown preparation produces zero waiting or readiness."""
        result = self._run(max_waiting_days=365, max_branches=5)
        for branch in result["branches"]:
            for crop in branch["crops"]:
                self.assertIsNone(crop["preparation_range"])
                self.assertIsNone(crop["ready_range"])
                self.assertEqual(crop["timing_status"], "unknown")
            for transition in branch["transitions"]:
                self.assertIsNone(transition["preparation_range"])
                self.assertIsNone(transition["waiting_range"])
                self.assertIsNone(transition["total_interval_range_days"])
                self.assertEqual(transition["waiting_limit_status"], "unknown")

    def test_preparation_interval_is_lower_bound_for_total(self) -> None:
        """Spec §10.4 | Bug it catches: clipped latest makes total interval below preparation."""
        preparation = {
            "min_days": 7,
            "max_days": 10,
            "source_ids": ["synthetic://e6-final"],
        }
        result = self._run(max_waiting_days=365, preparation_lookup=preparation)
        bad = []
        for branch in result["branches"]:
            for transition in branch["transitions"]:
                prep = transition["preparation_range"]
                total = transition["total_interval_range_days"]
                if prep is None or total is None:
                    continue
                below_min = (
                    total["min"] is not None
                    and total["min"] < prep["min_days"]
                )
                below_max = (
                    total["max"] is not None
                    and total["max"] < prep["max_days"]
                )
                if below_min or below_max:
                    bad.append((transition["to_crop_id"], total, prep))
        self.assertEqual(len(bad), 0)

    def test_clipped_latest_marks_waiting_and_total_latest_unknown(self) -> None:
        """Spec §10.4 | Bug it catches: clipped latest still reports a numeric latest waiting/total."""
        preparation = {
            "min_days": 7,
            "max_days": 10,
            "source_ids": ["synthetic://e6-final"],
        }
        result = self._run(max_waiting_days=365, preparation_lookup=preparation)
        clipped = [
            transition
            for branch in result["branches"]
            for transition in branch["transitions"]
            if transition["next_planting"]["latest_clipped"]
        ]
        self.assertTrue(clipped)
        for transition in clipped:
            self.assertTrue(transition["latest_invalid"])
            self.assertEqual(
                transition["next_planting"]["code"],
                "NEXT_PLANTING_LATEST_CLIPPED",
            )
            self.assertTrue(transition["next_planting"]["latest_clipped"])
            self.assertIsInstance(transition["waiting_range"]["min"], int)
            self.assertIsNone(transition["waiting_range"]["max"])
            self.assertIsInstance(
                transition["total_interval_range_days"]["min"], int
            )
            self.assertIsNone(transition["total_interval_range_days"]["max"])

    def test_synthetic_latest_invalid_transition_is_conditional(self) -> None:
        """Spec §10.4 | Bug it catches: latest_invalid transition still yields a candidate branch."""
        transition = {
            "next_planting": {
                "status": "pass",
                "code": "NEXT_PLANTING_WITHIN_PREFERRED",
            },
            "latest_invalid": True,
            "calendar_check": {"status": "pass"},
            "waiting_limit_status": "within",
            "waiting_range": {"min": 0, "max": None},
            "total_interval_range_days": {"min": 7, "max": None},
            "reasons": ["latest realization invalid"],
            "cautions": ["latest realization invalid"],
            "missing_evidence": ["latest_waiting_total"],
            "source_ids": [],
        }
        self.assertFalse(branch_expander._transition_ok(transition))
        crop = {
            "crop_id": "crop",
            "planting_range": {"earliest": "2027-01-01", "latest": "2027-01-02"},
            "status": "candidate",
            "reasons": [],
            "cautions": [],
            "missing_evidence": [],
            "source_ids": [],
        }
        branch = branch_expander._branch(
            dt.date(2026, 11, 6), [crop, crop, crop], [transition, transition]
        )
        self.assertEqual(branch["status"], "conditional")
        self.assertIn("latest_waiting_total", branch["missing_evidence"])

    def test_limit_error_states_product_basis(self) -> None:
        """Spec §10.4 | Bug it catches: product waiting cutoff labeled as scientific/biological limit."""
        code, reason = branch_expander._limit_error(
            dt.date(2027, 1, 1), 10, 5
        )
        self.assertEqual(code, "FUTURE_WINDOW_EXCEEDS_LIMIT")
        self.assertIn("2027-01-01", reason)
        self.assertIn("10 days", reason)
        self.assertIn("5 days", reason)
        self.assertIn("product relevance cutoff", reason)
        self.assertIn("not a scientifically safe maximum", reason)
        self.assertIn("not a biological impossibility", reason)
        self.assertIn("longer fallow", reason)
        self.assertNotIn("longer fallow is impossible", reason)

    def test_caution_next_planting_transition_is_conditional(self) -> None:
        """Spec §10.4/§14.4 | Bug it catches: a caution next-planting transition still yields a candidate."""
        crop = {
            "crop_id": "crop",
            "planting_range": {"earliest": "2027-01-01", "latest": "2027-01-02"},
            "status": "candidate",
            "reasons": [],
            "cautions": [],
            "missing_evidence": [],
            "source_ids": [],
        }
        caution = {
            "next_planting": {"status": "caution", "code": "NEXT_PLANTING_LATE_WINDOW"},
            "latest_invalid": False,
            "calendar_check": {"status": "pass"},
            "waiting_limit_status": "within",
            "waiting_range": {"min": 0, "max": 5},
            "total_interval_range_days": {"min": 7, "max": 12},
            "reasons": ["next planting is a caution"],
            "cautions": ["next planting is a caution"],
            "missing_evidence": [],
            "source_ids": [],
        }
        self.assertFalse(branch_expander._transition_ok(caution))

        passed = {
            **caution,
            "next_planting": {"status": "pass", "code": "NEXT_PLANTING_WITHIN_PREFERRED"},
            "reasons": [],
            "cautions": [],
        }
        self.assertTrue(branch_expander._transition_ok(passed))
        branch = branch_expander._branch(
            dt.date(2026, 11, 6), [crop, crop, crop], [caution, passed]
        )
        self.assertEqual(branch["status"], "conditional")
        candidate = branch_expander._branch(
            dt.date(2026, 11, 6), [crop, crop, crop], [passed, passed]
        )
        self.assertEqual(candidate["status"], "candidate")

    def test_known_preparation_propagates_waiting_and_total_ranges(self) -> None:
        """Spec §10.2-10.4 | Bug it catches: preparation, waiting, or total range mis-paired."""
        profiles = {crop_id: self.profiles[crop_id] for crop_id in SUBSET}
        preparation = {
            crop_id: {
                "min_days": 7,
                "max_days": 10,
                "source_ids": ["synthetic://prep"],
            }
            for crop_id in profiles
        }
        result = self._run(
            profiles,
            preparation_lookup=preparation,
            max_waiting_days=30,
            duration_reference_verified=True,
        )
        self.assertEqual(len(result["branches"]), 1)
        branch = result["branches"][0]
        self.assertEqual(
            [crop["crop_id"] for crop in branch["crops"]],
            ["mustard_binasarisha9", "boro_brri_dhan28", "aman_br11"],
        )
        self.assertEqual(branch["status"], "conditional")

        first, second = branch["transitions"]
        self.assertEqual(
            first["next_planting_range"],
            {"earliest": "2027-02-01", "latest": "2027-02-17"},
        )
        self.assertEqual(first["waiting_range"], {"min": 0, "max": 0})
        self.assertEqual(
            first["total_interval_range_days"], {"min": 7, "max": 10}
        )
        self.assertEqual(first["waiting_limit_status"], "within")
        self.assertEqual(first["preparation_range"]["min_days"], 7)

        self.assertEqual(
            second["next_planting_range"],
            {"earliest": "2027-07-10", "latest": "2027-07-17"},
        )
        self.assertEqual(second["waiting_range"], {"min": 0, "max": 12})
        self.assertEqual(
            second["total_interval_range_days"], {"min": 10, "max": 19}
        )
        self.assertEqual(second["waiting_limit_status"], "within")
        self.assertEqual(branch["crops"][0]["timing_status"], "known")

    def test_duration_verification_applies_only_to_listed_crops(self) -> None:
        """Spec §10 | Bug it catches: one global duration flag verifies every crop."""
        profiles = {crop_id: self.profiles[crop_id] for crop_id in SUBSET}
        result = self._run(
            profiles,
            max_waiting_days=365,
            duration_reference_verified=True,
            duration_reference_verified_crop_ids={"mustard_binasarisha9"},
        )
        branches = self._branches_with(result, "mustard_binasarisha9", position=1)
        self.assertTrue(branches)
        branch = branches[0]
        for crop in branch["crops"]:
            expected = crop["crop_id"] == "mustard_binasarisha9"
            self.assertEqual(
                crop["duration"]["reference_verified"], expected
            )
        self.assertEqual(
            result["request"]["duration_reference_verified_crop_ids"],
            ["mustard_binasarisha9"],
        )

    def test_duration_verification_ids_are_validated(self) -> None:
        """Spec §10 | Bug it catches: unknown crop IDs silently verify unrelated crops."""
        with self.assertRaises(ValueError):
            self._run(
                duration_reference_verified=True,
                duration_reference_verified_crop_ids={"unknown_crop"},
            )
        with self.assertRaises(ValueError):
            self._run(
                duration_reference_verified=False,
                duration_reference_verified_crop_ids={"mustard_binasarisha9"},
            )

    def test_small_waiting_limit_excludes_future_third_crop(self) -> None:
        """Spec §17.8 | Bug it catches: a future path beyond the configured waiting limit is kept."""
        profiles = {crop_id: self.profiles[crop_id] for crop_id in SUBSET}
        preparation = {
            crop_id: {"min_days": 0, "max_days": 0, "source_ids": ["synthetic://prep"]}
            for crop_id in profiles
        }
        within = self._run(
            profiles,
            preparation_lookup=preparation,
            max_waiting_days=30,
            duration_reference_verified=True,
        )
        self.assertEqual(len(within["branches"]), 1)
        self.assertEqual(
            within["branches"][0]["transitions"][1]["waiting_range"],
            {"min": 13, "max": 26},
        )
        self.assertEqual(
            within["branches"][0]["transitions"][1]["waiting_limit_status"],
            "within",
        )

        exceeded = self._run(
            profiles,
            preparation_lookup=preparation,
            max_waiting_days=20,
            duration_reference_verified=True,
        )
        self.assertEqual(exceeded["branches"], [])
        self.assertTrue(
            any(
                exclusion["at_position"] == 3
                and exclusion["code"]
                in ("FUTURE_WINDOW_EXCEEDS_LIMIT", "WAITING_LIMIT_EXCEEDED")
                for exclusion in exceeded["excluded_paths"]
            )
        )

    def test_rotation_starts_at_second_crop_and_same_family_keeps_path(self) -> None:
        """Spec §11 | Bug it catches: first crop gets a rotation check or same family blocks the path."""
        result = self._run(max_waiting_days=365)
        branches = self._branches_with(result, "boro_brri_dhan28", position=1)
        branch = next(
            item
            for item in branches
            if [crop["crop_id"] for crop in item["crops"]]
            == ["boro_brri_dhan28", "aman_br11", "boro_brri_dhan28"]
        )
        self.assertIsNone(branch["crops"][0]["rotation"])
        self.assertIsNone(branch["crops"][0]["checks"]["rotation"])
        for crop in branch["crops"][1:]:
            self.assertEqual(crop["rotation"]["code"], "SAME_FAMILY_REPEAT")
            self.assertEqual(crop["rotation"]["status"], "caution")
            self.assertFalse(crop["rotation"]["blocking"])
        self.assertEqual(branch["status"], "conditional")

    def test_legume_presence_reaches_later_crop_rotation(self) -> None:
        """Spec §11 | Bug it catches: lentil in the path not reflected in the next crop's rotation check."""
        result = self._run(max_waiting_days=365)
        for branch in result["branches"]:
            for index, crop in enumerate(branch["crops"][:-1]):
                if crop["crop_id"] != "lentil_binamasur9":
                    continue
                later = branch["crops"][index + 1]
                self.assertTrue(later["rotation"]["legume_present_in_path"])
                self.assertIn(
                    "lentil_binamasur9", later["rotation"]["legume_crop_ids"]
                )
                return
        self.fail("no branch placed lentil before another crop")

    def test_blocked_soil_paths_never_appear_in_branches(self) -> None:
        """Spec §17.9 / §17.14 | Bug it catches: an unsupported soil check still yields branches."""
        soil = {"ph": {"min": 0, "max": 0, "source_ids": ["synthetic://soil"]}}
        result = self._run(max_waiting_days=365, soil_evidence=soil)
        self.assertEqual(result["branches"], [])
        self.assertTrue(
            any(
                exclusion["at_position"] == 1
                and exclusion["code"] == "SOIL_PH_OUTSIDE_TOLERANCE"
                for exclusion in result["excluded_paths"]
            )
        )

    def test_missing_duration_excludes_every_path_with_that_crop(self) -> None:
        """Spec §17.6 | Bug it catches: a crop with no duration still appears in a branch."""
        profiles = {crop_id: copy.deepcopy(self.profiles[crop_id]) for crop_id in SUBSET}
        profiles["mustard_binasarisha9"]["variety_duration_min_days"] = None
        profiles["mustard_binasarisha9"]["variety_duration_max_days"] = None
        result = self._run(profiles, max_waiting_days=365)
        self.assertFalse(
            any(
                any(
                    crop["crop_id"] == "mustard_binasarisha9"
                    for crop in branch["crops"]
                )
                for branch in result["branches"]
            )
        )
        self.assertTrue(
            any(
                exclusion["at_position"] == 1
                and exclusion["crop_ids"] == ["mustard_binasarisha9"]
                and exclusion["code"] == "DURATION_EVIDENCE_MISSING"
                for exclusion in result["excluded_paths"]
            )
        )

    def test_max_branches_truncates_deterministically(self) -> None:
        """Spec §14.4 | Bug it catches: cap changes ordering or zero cap ignores the cap."""
        capped = self._run(max_waiting_days=365, max_branches=3)
        uncapped = self._run(max_waiting_days=365)
        self.assertEqual(len(capped["branches"]), 3)
        self.assertEqual(
            [branch["branch_id"] for branch in capped["branches"]],
            [branch["branch_id"] for branch in uncapped["branches"][:3]],
        )
        self.assertEqual(
            self._run(max_waiting_days=365, max_branches=0)["branches"], []
        )

    def test_e6_modules_have_no_crop_specific_branches(self) -> None:
        """Spec §14 | Bug it catches: a hard-coded crop ID branch added to the shared evaluator."""
        crop_ids = tuple(self.profiles)
        for name in ("timeline.py", "rotation.py", "branch_expander.py"):
            text = (SRC_DIR / name).read_text(encoding="utf-8")
            for crop_id in crop_ids:
                with self.subTest(module=name, crop_id=crop_id):
                    self.assertNotIn(crop_id, text)


if __name__ == "__main__":
    unittest.main()
