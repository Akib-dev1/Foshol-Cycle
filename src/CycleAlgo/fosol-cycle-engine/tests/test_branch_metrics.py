"""Tests for branch completion-time and diversity metrics (v1.md §12.1, §13, §14.4)."""

import datetime as dt
import json
import random
import unittest
from pathlib import Path

from src.branch_expander import expand_branches
from src.branch_metrics import (
    build_economics_metrics,
    build_resource_metrics,
    calculate_completion_time,
    calculate_diversity_metrics,
    enumerate_completion_range,
    rank_branches,
    realize_completion,
)
from src.crop_profiles import load_crop_profiles

SRC = Path(__file__).resolve().parents[1] / "src" / "branch_metrics.py"
DATA_CSV = (
    Path(__file__).resolve().parents[2]
    / "Data"
    / "fosol_cycle_rajshahi_crop_dataset.csv"
)
_MISSING = object()
_CROP_IDS = (
    "aman_br11",
    "boro_brri_dhan28",
    "lentil_binamasur9",
    "maize_rabi_bari_hybrid13",
    "mung_bari_mung6_kharif1",
    "mustard_binasarisha9",
    "potato_bari_alu41",
    "wheat_bari_gom33",
)


def _diversity_branch(
    families=("Poaceae", "Fabaceae", "Brassicaceae"),
    legume_flags=(False, True, False),
    crop_ids=("crop_a", "crop_b", "crop_c"),
) -> dict:
    return {
        "crops": [
            {
                "crop_id": crop_id,
                "family": family,
                "is_legume_n_fixing": flag,
            }
            for crop_id, family, flag in zip(crop_ids, families, legume_flags)
        ],
        "transitions": [{}, {}],
    }


def _real_branches():
    profiles = load_crop_profiles(DATA_CSV)
    branches = expand_branches(
        profiles,
        "2026-11-06",
        max_waiting_days=365,
        max_initial_wait_days=365,
    )["branches"]
    return profiles, branches


def _real_branches_295():
    profiles = load_crop_profiles(DATA_CSV)
    branches = expand_branches(
        profiles,
        "2026-11-06",
        max_initial_wait_days=180,
        max_waiting_days=None,
    )["branches"]
    return profiles, branches


def _random_date(rng: random.Random, start: dt.date, end: dt.date) -> dt.date:
    return start + dt.timedelta(days=rng.randint(0, (end - start).days))


def _feasible_completion_sample(branch: dict, rng: random.Random) -> int | None:
    """Return a completion sample that follows every intermediate harvest."""
    crops = branch["crops"]
    p1 = _random_date(
        rng,
        dt.date.fromisoformat(crops[0]["planting_range"]["earliest"]),
        dt.date.fromisoformat(crops[0]["planting_range"]["latest"]),
    )
    d1 = rng.randint(
        crops[0]["duration"]["min_days"], crops[0]["duration"]["max_days"]
    )
    h1 = p1 + dt.timedelta(days=d1)

    second_start = dt.date.fromisoformat(crops[1]["planting_range"]["earliest"])
    second_end = dt.date.fromisoformat(crops[1]["planting_range"]["latest"])
    p2_start = max(second_start, h1)
    if p2_start > second_end:
        return None
    p2 = _random_date(rng, p2_start, second_end)
    d2 = rng.randint(
        crops[1]["duration"]["min_days"], crops[1]["duration"]["max_days"]
    )
    h2 = p2 + dt.timedelta(days=d2)

    third_start = dt.date.fromisoformat(crops[2]["planting_range"]["earliest"])
    third_end = dt.date.fromisoformat(crops[2]["planting_range"]["latest"])
    p3_start = max(third_start, h2)
    if p3_start > third_end:
        return None
    p3 = _random_date(rng, p3_start, third_end)
    d3 = rng.randint(
        crops[2]["duration"]["min_days"], crops[2]["duration"]["max_days"]
    )
    h3 = p3 + dt.timedelta(days=d3)
    return (h3 - p1).days


def _prep_known_branch() -> dict:
    return {
        "crops": [
            {
                "planting_range": {
                    "earliest": "2026-01-01",
                    "latest": "2026-01-10",
                },
                "harvest_range": {
                    "earliest": "2026-01-11",
                    "latest": "2026-01-20",
                },
                "duration": {"min_days": 10, "max_days": 10},
                "preparation_range": {
                    "min_days": 5,
                    "max_days": 30,
                },
            },
            {
                "planting_range": {
                    "earliest": "2026-02-01",
                    "latest": "2026-02-28",
                },
                "harvest_range": {
                    "earliest": "2026-02-11",
                    "latest": "2026-03-10",
                },
                "duration": {"min_days": 10, "max_days": 10},
                "preparation_range": {
                    "min_days": 5,
                    "max_days": 30,
                },
            },
            {
                "planting_range": {
                    "earliest": "2026-03-01",
                    "latest": "2026-04-30",
                },
                "harvest_range": {
                    "earliest": "2026-03-11",
                    "latest": "2026-05-10",
                },
                "duration": {"min_days": 10, "max_days": 10},
                "preparation_range": {
                    "min_days": 5,
                    "max_days": 30,
                },
            },
        ],
        "transitions": [
            {
                "preparation_known": True,
                "preparation_range": {"min_days": 5, "max_days": 30},
                "window": {
                    "preferred_start": "2026-02-01",
                    "preferred_end": "2026-02-28",
                    "supported_late_end": None,
                    "window_start": "2026-02-01",
                },
            },
            {
                "preparation_known": True,
                "preparation_range": {"min_days": 5, "max_days": 30},
                "window": {
                    "preferred_start": "2026-03-01",
                    "preferred_end": "2026-03-31",
                    "supported_late_end": None,
                    "window_start": "2026-03-01",
                },
            },
        ],
    }


def _economics_profiles() -> dict:
    return {
        crop_id: {
            "yield_reference_low_t_ha": 4.0,
            "yield_reference_high_t_ha": 5.0,
            "yield_basis": "synthetic test reference",
            "market_price_mode": "DYNAMIC_EXTERNAL",
            "source_barc_zoning": "https://example.test/barc",
        }
        for crop_id in ("crop_a", "crop_b", "crop_c")
    }


def _resource_branch(
    contexts: tuple[dict, ...] | None = None,
    crop_count: int = 3,
    transition_count: int = 2,
) -> dict:
    crops = []
    for index, suffix in enumerate(("a", "b", "c")):
        crop = {"crop_id": f"crop_{suffix}"}
        if contexts is not None:
            crop.update(contexts[index])
        crops.append(crop)
    return {
        "crops": crops[:crop_count],
        "transitions": [{} for _ in range(transition_count)],
    }


def _ranking_branch(
    branch_id: str,
    status: str = "conditional",
    first_planting: object = _MISSING,
    third_harvest: object = _MISSING,
    families: tuple = ("Poaceae", "Fabaceae", "Brassicaceae"),
    legume_flags: tuple = (False, True, False),
    reasons: list | None = None,
    cautions: list | None = None,
) -> dict:
    first = (
        {"earliest": "2026-01-01", "latest": "2026-01-02"}
        if first_planting is _MISSING
        else first_planting
    )
    third = (
        {"earliest": "2026-04-01", "latest": "2026-04-12"}
        if third_harvest is _MISSING
        else third_harvest
    )
    crops = []
    for index, (family, flag) in enumerate(zip(families, legume_flags)):
        if index == 0:
            planting = first
            harvest = _shift_range(first, 2)
            duration = {"min_days": 2, "max_days": 2}
        elif index == 1:
            planting = {"earliest": "2026-01-11", "latest": "2026-01-12"}
            harvest = _shift_range(planting, 2)
            duration = {"min_days": 2, "max_days": 2}
        else:
            planting = {"earliest": "2026-01-21", "latest": "2026-01-22"}
            harvest = third
            try:
                duration = {
                    "min_days": (
                        dt.date.fromisoformat(third["earliest"])
                        - dt.date.fromisoformat(planting["earliest"])
                    ).days,
                    "max_days": (
                        dt.date.fromisoformat(third["latest"])
                        - dt.date.fromisoformat(planting["latest"])
                    ).days,
                }
            except (KeyError, TypeError, ValueError):
                duration = None
        crops.append(
            {
                "crop_id": f"{branch_id}_crop_{index}",
                "family": family,
                "is_legume_n_fixing": flag,
                "planting_range": planting,
                "harvest_range": harvest,
                "duration": duration,
            }
        )
    return {
        "branch_id": branch_id,
        "status": status,
        "crops": crops,
        "transitions": [{}, {}],
        "reasons": reasons or [],
        "cautions": cautions or [],
    }


def _shift_range(value: dict, days: int) -> dict:
    return {
        "earliest": (
            dt.date.fromisoformat(value["earliest"]) + dt.timedelta(days=days)
        ).isoformat(),
        "latest": (
            dt.date.fromisoformat(value["latest"]) + dt.timedelta(days=days)
        ).isoformat(),
    }


def _custom_branch(
    first: tuple[str, str],
    second: tuple[str, str],
    third: tuple[str, str],
    durations: tuple[tuple[int, int], tuple[int, int], tuple[int, int]],
    *,
    prep2: dict | None = None,
    prep3: dict | None = None,
) -> dict:
    crops = []
    for planting, duration in zip((first, second, third), durations):
        crops.append(
            {
                "planting_range": {
                    "earliest": planting[0],
                    "latest": planting[1],
                },
                "harvest_range": {
                    "earliest": (
                        dt.date.fromisoformat(planting[0])
                        + dt.timedelta(days=duration[0])
                    ).isoformat(),
                    "latest": (
                        dt.date.fromisoformat(planting[1])
                        + dt.timedelta(days=duration[1])
                    ).isoformat(),
                },
                "duration": {
                    "min_days": duration[0],
                    "max_days": duration[1],
                },
            }
        )
    transitions = []
    for prep in (prep2, prep3):
        transition = {"preparation_known": prep is not None}
        if prep is not None:
            transition["preparation_range"] = prep
        transitions.append(transition)
    return {"crops": crops, "transitions": transitions}


def _oracle_completion(branch: dict) -> tuple[int, int, int] | None:
    """Exhaustively enumerate tiny schedules without calling production search."""

    def parse_range(value: dict) -> tuple[dt.date, dt.date]:
        return (
            dt.date.fromisoformat(value["earliest"]),
            dt.date.fromisoformat(value["latest"]),
        )

    def dates(value: tuple[dt.date, dt.date]):
        current, end = value
        while current <= end:
            yield current
            current += dt.timedelta(days=1)

    def limits(crop: dict, transition: dict) -> tuple[dt.date, dt.date]:
        low, high = parse_range(crop["planting_range"])
        window = transition.get("window")
        if isinstance(window, dict):
            start = window.get("window_start") or window.get("preferred_start")
            end = window.get("supported_late_end") or window.get("preferred_end")
            if start is not None:
                low = max(low, dt.date.fromisoformat(start))
            if end is not None:
                high = min(high, dt.date.fromisoformat(end))
        return low, high

    def prep_min(transition: dict) -> int:
        if not transition.get("preparation_known"):
            return 0
        return transition["preparation_range"]["min_days"]

    crops = branch["crops"]
    transitions = branch["transitions"]
    first_range = parse_range(crops[0]["planting_range"])
    second_range = limits(crops[1], transitions[0])
    third_range = limits(crops[2], transitions[1])
    durations = [
        (
            crop["duration"]["min_days"],
            crop["duration"]["max_days"],
        )
        for crop in crops
    ]
    prep2 = prep_min(transitions[0])
    prep3 = prep_min(transitions[1])
    found = []

    for p1 in dates(first_range):
        for d1 in range(durations[0][0], durations[0][1] + 1):
            h1 = p1 + dt.timedelta(days=d1)
            for p2 in dates(second_range):
                if p2 < h1 + dt.timedelta(days=prep2):
                    continue
                for d2 in range(durations[1][0], durations[1][1] + 1):
                    h2 = p2 + dt.timedelta(days=d2)
                    for p3 in dates(third_range):
                        if p3 < h2 + dt.timedelta(days=prep3):
                            continue
                        for d3 in range(
                            durations[2][0], durations[2][1] + 1
                        ):
                            h3 = p3 + dt.timedelta(days=d3)
                            found.append((h3 - p1).days)
    if not found:
        return None
    return min(found), max(found), len(found)


def _branch(
    first_planting: object = _MISSING,
    third_harvest: object = _MISSING,
    crop_count: int = 3,
    transition_count: int = 2,
) -> dict:
    """Build a chronologically ordered synthetic branch.

    Each default crop follows the previous harvest. Custom third-harvest dates
    are paired with a ten-day third-crop duration; if those dates cannot follow
    the first two crops, completion must fail rather than be invented.
    """
    default_first = {"earliest": "2026-01-01", "latest": "2026-01-10"}
    first_p = default_first if first_planting is _MISSING else first_planting
    try:
        first_h = _shift_range(first_p, 2) if isinstance(first_p, dict) else None
    except (KeyError, TypeError, ValueError):
        first_h = None
    second_p = (
        {
            "earliest": (
                dt.date.fromisoformat(first_h["earliest"])
                + dt.timedelta(days=1)
            ).isoformat(),
            "latest": (
                dt.date.fromisoformat(first_h["latest"])
                + dt.timedelta(days=10)
            ).isoformat(),
        }
        if first_h is not None
        else default_first
    )
    second_h = _shift_range(second_p, 2)
    if third_harvest is _MISSING:
        third_p = {
            "earliest": (
                dt.date.fromisoformat(second_h["earliest"])
                + dt.timedelta(days=1)
            ).isoformat(),
            "latest": (
                dt.date.fromisoformat(second_h["latest"])
                + dt.timedelta(days=10)
            ).isoformat(),
        }
        third_h = _shift_range(third_p, 10)
        third_duration = {"min_days": 10, "max_days": 10}
    elif third_harvest is None:
        third_p = second_p
        third_h = None
        third_duration = None
    else:
        third_h = third_harvest
        try:
            third_p = (
                _shift_range(third_h, -10)
                if isinstance(third_h, dict)
                else second_p
            )
            third_duration = (
                {"min_days": 10, "max_days": 10}
                if isinstance(third_h, dict)
                else None
            )
        except (KeyError, TypeError, ValueError):
            third_p = second_p
            third_duration = None
    crops = [
        {
            "planting_range": first_p,
            "harvest_range": first_h,
            "duration": {"min_days": 2, "max_days": 2},
        },
        {
            "planting_range": second_p,
            "harvest_range": second_h,
            "duration": {"min_days": 2, "max_days": 2},
        },
        {
            "planting_range": third_p,
            "harvest_range": third_h,
            "duration": third_duration,
        },
    ]
    return {
        "crops": crops[:crop_count],
        "transitions": [{} for _ in range(transition_count)],
    }


class CompletionTimeTests(unittest.TestCase):
    def test_known_ranges_use_valid_realized_schedules(self) -> None:
        """Spec §12.1 | Bug it catches: completion endpoints are averaged or paired across an invalid intermediate crop."""
        result = calculate_completion_time(
            _branch(
                first_planting={
                    "earliest": "2026-01-01",
                    "latest": "2026-01-10",
                },
                third_harvest={
                    "earliest": "2026-04-01",
                    "latest": "2026-04-20",
                },
            )
        )
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["completion_days"], {"min": 81, "max": 109})
        self.assertEqual(result["earliest_completion_date"], "2026-04-01")
        self.assertEqual(result["latest_completion_date"], "2026-04-20")
        self.assertEqual(result["ranking_value_days"], 109)
        self.assertEqual(
            result["basis"], "third_harvest_minus_first_planting"
        )
        self.assertEqual(result["range_basis"], "realized_corners")
        self.assertEqual(
            result["min_realization"],
            {
                "p1": "2026-01-10",
                "h1": "2026-01-12",
                "p2": "2026-01-12",
                "h2": "2026-01-14",
                "p3": "2026-03-22",
                "h3": "2026-04-01",
                "completion_days": 81,
            },
        )
        self.assertEqual(
            result["max_realization"],
            {
                "p1": "2026-01-01",
                "h1": "2026-01-03",
                "p2": "2026-01-04",
                "h2": "2026-01-06",
                "p3": "2026-04-10",
                "h3": "2026-04-20",
                "completion_days": 109,
            },
        )
        for realization in (result["min_realization"], result["max_realization"]):
            self.assertLessEqual(realization["p1"], realization["h1"])
            self.assertLessEqual(realization["h1"], realization["p2"])
            self.assertLessEqual(realization["p2"], realization["h2"])
            self.assertLessEqual(realization["h2"], realization["p3"])
            self.assertLessEqual(realization["p3"], realization["h3"])
        self.assertEqual(
            result["first_planting_range"],
            {"earliest": "2026-01-01", "latest": "2026-01-10"},
        )
        self.assertEqual(
            result["third_harvest_range"],
            {"earliest": "2026-04-01", "latest": "2026-04-20"},
        )
        self.assertIn("overlapping", result["range_overlap_note"])

    def test_single_date_ranges_give_single_completion_value(self) -> None:
        """Spec §12.1 | Bug it catches: a single-date range invents a wider completion."""
        result = calculate_completion_time(
            _branch(
                first_planting={
                    "earliest": "2026-01-01",
                    "latest": "2026-01-01",
                },
                third_harvest={
                    "earliest": "2026-02-01",
                    "latest": "2026-02-01",
                },
            )
        )
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["completion_days"], {"min": 31, "max": 31})
        self.assertEqual(result["ranking_value_days"], 31)

    def test_missing_or_invalid_ranges_are_unavailable(self) -> None:
        """Spec §12.1 | Bug it catches: missing/invalid timing becomes a zero or invented range."""
        cases = (
            ("missing_third_harvest", _branch(third_harvest=None), "third_harvest_range"),
            ("missing_first_planting", _branch(first_planting=None), "first_planting_range"),
            (
                "invalid_iso",
                _branch(
                    third_harvest={
                        "earliest": "not-a-date",
                        "latest": "2026-04-20",
                    }
                ),
                "third_harvest_range",
            ),
            (
                "reversed_harvest",
                _branch(
                    third_harvest={
                        "earliest": "2026-04-20",
                        "latest": "2026-04-01",
                    }
                ),
                "third_harvest_range",
            ),
        )
        for name, branch, missing in cases:
            with self.subTest(name=name):
                result = calculate_completion_time(branch)
                self.assertEqual(result["status"], "unavailable")
                self.assertIsNone(result["completion_days"])
                self.assertIsNone(result["ranking_value_days"])
                self.assertIn(missing, result["missing_evidence"])

    def test_malformed_branch_shape_is_unavailable_without_crash(self) -> None:
        """Spec §12.1 | Bug it catches: malformed branches crash or look complete."""
        cases = (
            None,
            {},
            _branch(crop_count=2),
            _branch(transition_count=1),
        )
        for branch in cases:
            with self.subTest(branch=branch):
                result = calculate_completion_time(branch)
                self.assertEqual(result["status"], "unavailable")
                self.assertIsNone(result["completion_days"])
                self.assertEqual(result["reason"], "INVALID_BRANCH_SHAPE")

    def test_short_third_window_uses_valid_schedules(self) -> None:
        """Spec §12.1 | Bug it catches: an inverted corner range is reported instead of valid schedules."""
        result = calculate_completion_time(
            _branch(
                first_planting={
                    "earliest": "2026-01-01",
                    "latest": "2026-01-10",
                },
                third_harvest={
                    "earliest": "2026-01-20",
                    "latest": "2026-01-25",
                },
            )
        )
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["completion_days"], {"min": 14, "max": 24})
        self.assertEqual(result["range_basis"], "realized_corners")
        self.assertEqual(
            result["min_realization"],
            {
                "p1": "2026-01-06",
                "h1": "2026-01-08",
                "p2": "2026-01-08",
                "h2": "2026-01-10",
                "p3": "2026-01-10",
                "h3": "2026-01-20",
                "completion_days": 14,
            },
        )
        self.assertEqual(
            result["max_realization"],
            {
                "p1": "2026-01-01",
                "h1": "2026-01-03",
                "p2": "2026-01-04",
                "h2": "2026-01-06",
                "p3": "2026-01-15",
                "h3": "2026-01-25",
                "completion_days": 24,
            },
        )

    def test_no_feasible_chain_is_unavailable(self) -> None:
        """Spec §12.1 | Bug it catches: a negative endpoint-only range is returned as valid."""
        result = calculate_completion_time(
            _branch(
                first_planting={
                    "earliest": "2027-08-01",
                    "latest": "2027-12-31",
                },
                third_harvest={
                    "earliest": "2027-01-01",
                    "latest": "2027-02-01",
                },
            )
        )
        self.assertEqual(result["status"], "unavailable")
        self.assertIsNone(result["completion_days"])
        self.assertIsNone(result["ranking_value_days"])
        self.assertEqual(result["reason"], "COMPLETION_RANGE_INVALID")

    def test_no_feasible_chain_enumeration_is_unavailable(self) -> None:
        """Spec §12.1 | Bug it catches: enumeration turns an infeasible chain into ok."""
        branch = _branch(
            first_planting={
                "earliest": "2027-08-01",
                "latest": "2027-12-31",
            },
            third_harvest={
                "earliest": "2027-01-01",
                "latest": "2027-02-01",
            },
        )
        result = enumerate_completion_range(branch)
        self.assertEqual(result["status"], "unavailable")
        self.assertIsNone(result["completion_days"])
        self.assertIsNone(result["ranking_value_days"])
        self.assertTrue(result["enumeration_used"])
        self.assertEqual(result["reason"], "COMPLETION_RANGE_INVALID")

    def test_reversed_date_range_is_unavailable(self) -> None:
        """Spec §12.1 | Bug it catches: reversed ISO endpoints are silently accepted."""
        result = calculate_completion_time(
            _branch(
                third_harvest={
                    "earliest": "2026-04-20",
                    "latest": "2026-04-01",
                }
            )
        )
        self.assertEqual(result["status"], "unavailable")
        self.assertIsNone(result["completion_days"])
        self.assertIn("third_harvest_range", result["missing_evidence"])

    def test_realized_corners_are_tight_for_all_real_branches(self) -> None:
        """Spec §12.1 | Bug it catches: a valid branch still gets an inverted completion range."""
        _, branches = _real_branches()
        self.assertEqual(len(branches), 420)
        for branch in branches:
            result = calculate_completion_time(branch)
            self.assertEqual(result["status"], "ok", branch["branch_id"])
            self.assertLessEqual(
                result["completion_days"]["min"],
                result["completion_days"]["max"],
            )
            for name in ("min_realization", "max_realization"):
                realization = result[name]
                dates = [
                    dt.date.fromisoformat(realization[key])
                    for key in ("p1", "h1", "p2", "h2", "p3", "h3")
                ]
                self.assertEqual(dates, sorted(dates), branch["branch_id"])
                for index, crop in enumerate(branch["crops"]):
                    planting = dates[index * 2]
                    harvest = dates[index * 2 + 1]
                    planting_range = crop["planting_range"]
                    harvest_range = crop["harvest_range"]
                    self.assertGreaterEqual(
                        planting, dt.date.fromisoformat(planting_range["earliest"])
                    )
                    self.assertLessEqual(
                        planting, dt.date.fromisoformat(planting_range["latest"])
                    )
                    self.assertGreaterEqual(
                        harvest, dt.date.fromisoformat(harvest_range["earliest"])
                    )
                    self.assertLessEqual(
                        harvest, dt.date.fromisoformat(harvest_range["latest"])
                    )
                    duration = crop["duration"]
                    self.assertGreaterEqual(
                        (harvest - planting).days, duration["min_days"]
                    )
                    self.assertLessEqual(
                        (harvest - planting).days, duration["max_days"]
                    )
                if branch["transitions"][0]["preparation_known"]:
                    self.assertGreaterEqual(
                        (dates[2] - dates[1]).days,
                        branch["transitions"][0]["preparation_range"]["min_days"],
                    )
                if branch["transitions"][1]["preparation_known"]:
                    self.assertGreaterEqual(
                        (dates[4] - dates[3]).days,
                        branch["transitions"][1]["preparation_range"]["min_days"],
                    )
                self.assertEqual(
                    (dates[5] - dates[0]).days,
                    realization["completion_days"],
                )
            self.assertEqual(result["range_basis"], "realized_corners")

    def test_real_branch_49429_overlap_regression(self) -> None:
        """Spec §12.1 | Bug it catches: lentil harvest 2027-02-22 followed by Boro planting 2027-02-14."""
        _, branches = _real_branches_295()
        branch = next(
            item for item in branches if item["branch_id"] == "b_49429e0d044b"
        )
        result = calculate_completion_time(branch)
        self.assertEqual(result["status"], "ok")
        for name in ("min_realization", "max_realization"):
            realization = result[name]
            self.assertLessEqual(realization["p1"], realization["h1"])
            self.assertLessEqual(realization["h1"], realization["p2"])
            self.assertLessEqual(realization["p2"], realization["h2"])
            self.assertLessEqual(realization["h2"], realization["p3"])
            self.assertLessEqual(realization["p3"], realization["h3"])
        self.assertGreaterEqual(
            result["min_realization"]["p2"], result["min_realization"]["h1"]
        )
        self.assertEqual(result["completion_days"]["min"], 385)

    def test_known_preparation_sequence_is_chronological(self) -> None:
        """Spec §12.1 | Bug it catches: known preparation bounds are ignored by completion."""
        branch = _prep_known_branch()
        result = calculate_completion_time(branch)
        self.assertEqual(result["status"], "ok")
        for name in ("min_realization", "max_realization"):
            realization = result[name]
            self.assertLessEqual(realization["p1"], realization["h1"])
            self.assertLessEqual(realization["h1"], realization["p2"])
            self.assertLessEqual(realization["p2"], realization["h2"])
            self.assertLessEqual(realization["h2"], realization["p3"])
            self.assertLessEqual(realization["p3"], realization["h3"])
            self.assertGreaterEqual(
                (dt.date.fromisoformat(realization["p2"])
                 - dt.date.fromisoformat(realization["h1"])).days,
                5,
            )
            self.assertGreaterEqual(
                (dt.date.fromisoformat(realization["p3"])
                 - dt.date.fromisoformat(realization["h2"])).days,
                5,
            )

    def test_feasible_shorter_duration_beats_infeasible_maximum(self) -> None:
        """Spec §12.1 | Bug it catches: maximum durations hide a valid shorter schedule."""
        branch = _custom_branch(
            ("2026-01-01", "2026-01-01"),
            ("2026-01-03", "2026-01-03"),
            ("2026-01-05", "2026-01-05"),
            ((1, 10), (1, 1), (1, 1)),
        )
        result = calculate_completion_time(branch)
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["completion_days"], {"min": 5, "max": 5})
        self.assertEqual(_oracle_completion(branch), (5, 5, 2))

    def test_completion_bounds_match_exhaustive_tiny_oracle(self) -> None:
        """Spec §12.1 | Bug it catches: production min/max differs from exhaustive feasible schedules."""
        branch = _custom_branch(
            ("2026-01-01", "2026-01-02"),
            ("2026-01-03", "2026-01-05"),
            ("2026-01-06", "2026-01-08"),
            ((1, 2), (1, 2), (1, 2)),
            prep2={
                "min_days": 1,
                "max_days": 3,
                "source_ids": ["test://prep"],
            },
        )
        oracle = _oracle_completion(branch)
        self.assertIsNotNone(oracle)
        result = calculate_completion_time(branch)
        self.assertEqual(result["status"], "ok")
        self.assertEqual(
            result["completion_days"],
            {"min": oracle[0], "max": oracle[1]},
        )
        self.assertGreater(oracle[2], 1)

    def test_completion_bounds_match_oracle_across_tiny_random_cases(self) -> None:
        """Spec §12.1 | Bug it catches: a duration/window corner disagrees with exhaustive feasible schedules."""
        rng = random.Random(42)
        base = dt.date(2026, 1, 1)

        def random_range(offset):
            start = base + dt.timedelta(days=offset + rng.randint(0, 3))
            end = start + dt.timedelta(days=rng.randint(0, 3))
            return (start.isoformat(), end.isoformat())

        for _ in range(100):
            durations = []
            for _ in range(3):
                low = rng.randint(1, 3)
                high = rng.randint(3, 5)
                durations.append((low, high) if low <= high else (high, low))
            prep2 = (
                {
                    "min_days": rng.randint(0, 2),
                    "max_days": 3,
                    "source_ids": ["test://prep"],
                }
                if rng.random() < 0.5
                else None
            )
            prep3 = (
                {
                    "min_days": rng.randint(0, 2),
                    "max_days": 3,
                    "source_ids": ["test://prep"],
                }
                if rng.random() < 0.5
                else None
            )
            branch = _custom_branch(
                random_range(0),
                random_range(rng.randint(0, 6)),
                random_range(rng.randint(0, 10)),
                tuple(durations),
                prep2=prep2,
                prep3=prep3,
            )
            oracle = _oracle_completion(branch)
            result = calculate_completion_time(branch)
            if oracle is None:
                self.assertEqual(result["status"], "unavailable")
            else:
                self.assertEqual(result["status"], "ok")
                self.assertEqual(
                    result["completion_days"],
                    {"min": oracle[0], "max": oracle[1]},
                )

    def test_impossible_sequence_matches_exhaustive_tiny_oracle(self) -> None:
        """Spec §12.1 | Bug it catches: an impossible chain is reported as feasible."""
        branch = _custom_branch(
            ("2026-01-05", "2026-01-05"),
            ("2026-01-01", "2026-01-02"),
            ("2026-01-01", "2026-01-02"),
            ((1, 1), (1, 1), (1, 1)),
        )
        self.assertIsNone(_oracle_completion(branch))
        result = calculate_completion_time(branch)
        self.assertEqual(result["status"], "unavailable")
        self.assertEqual(result["reason"], "COMPLETION_RANGE_INVALID")

    def test_previously_inverted_branches_are_now_valid(self) -> None:
        """Spec §12.1 | Bug it catches: the 57 decision-A inversions remain unranked."""
        _, branches = _real_branches()
        inverted = []
        for branch in branches:
            planting = branch["crops"][0]["planting_range"]
            harvest = branch["crops"][2]["harvest_range"]
            planting_earliest = dt.date.fromisoformat(planting["earliest"])
            planting_latest = dt.date.fromisoformat(planting["latest"])
            harvest_earliest = dt.date.fromisoformat(harvest["earliest"])
            harvest_latest = dt.date.fromisoformat(harvest["latest"])
            if (harvest_latest - planting_latest).days < (
                harvest_earliest - planting_earliest
            ).days:
                inverted.append(branch)
        self.assertEqual(len(inverted), 57)
        for branch in inverted:
            result = calculate_completion_time(branch)
            self.assertEqual(result["status"], "ok")
            self.assertLessEqual(
                result["completion_days"]["min"],
                result["completion_days"]["max"],
            )

        example = next(
            branch
            for branch in branches
            if branch["branch_id"] == "b_82899e8d6941"
        )
        result = calculate_completion_time(example)
        self.assertEqual(result["completion_days"], {"min": 655, "max": 682})
        self.assertEqual(result["range_basis"], "realized_corners")
        self.assertEqual(result["min_realization"]["p1"], "2027-07-24")
        self.assertEqual(result["min_realization"]["h3"], "2029-05-09")
        self.assertEqual(result["max_realization"]["p1"], "2027-07-10")
        self.assertEqual(result["max_realization"]["h3"], "2029-05-22")

    def test_realized_corners_not_widest_span(self) -> None:
        """Spec §12.1 | Bug it catches: widest-span endpoints replace actual realizations."""
        branch = _prep_known_branch()
        result = calculate_completion_time(branch)
        fastest = realize_completion(branch, "fastest")
        slowest = realize_completion(branch, "slowest")
        self.assertEqual(fastest["completion_days"], 60)
        self.assertEqual(slowest["completion_days"], 99)
        self.assertEqual(result["completion_days"], {"min": 60, "max": 99})
        self.assertEqual(result["range_basis"], "realized_corners")
        self.assertEqual(result["min_realization"]["h3"], "2026-03-11")
        self.assertEqual(result["max_realization"]["h3"], "2026-04-10")
        self.assertEqual(
            {
                "min": (
                    dt.date(2026, 3, 11) - dt.date(2026, 1, 10)
                ).days,
                "max": (
                    dt.date(2026, 5, 10) - dt.date(2026, 1, 1)
                ).days,
            },
            {"min": 60, "max": 129},
        )
        self.assertLess(result["completion_days"]["max"], 129)

    def test_sampling_within_realized_bounds(self) -> None:
        """Spec §12.1 | Bug it catches: a feasible sampled schedule falls outside the reported range."""
        _, branches = _real_branches()
        rng = random.Random(20261108)
        for branch in rng.sample(branches, 10):
            result = calculate_completion_time(branch)
            days = []
            for _ in range(30):
                sample = _feasible_completion_sample(branch, rng)
                if sample is not None:
                    days.append(sample)
            self.assertTrue(days, branch["branch_id"])
            self.assertGreaterEqual(min(days), result["completion_days"]["min"])
            self.assertLessEqual(max(days), result["completion_days"]["max"])

    def test_infeasible_known_preparation_is_unavailable(self) -> None:
        """Spec §12.1 | Bug it catches: an infeasible prep bound is bypassed by enumeration."""
        branch = _prep_known_branch()
        branch["transitions"][0]["preparation_range"]["min_days"] = 100
        branch["transitions"][0]["preparation_range"]["max_days"] = 100
        result = calculate_completion_time(branch)
        self.assertEqual(result["status"], "unavailable")
        self.assertIsNone(result["completion_days"])
        self.assertEqual(result["reason"], "COMPLETION_RANGE_INVALID")
        self.assertFalse(result["enumeration_used"])

    def test_completion_property_300_feasible_realizations(self) -> None:
        """Spec §12.1 | Bug it catches: a feasible schedule falls outside the reported completion range."""
        _, branches = _real_branches()
        rng = random.Random(20261107)
        cache = {}
        sampled = 0
        for _ in range(300):
            branch = rng.choice(branches)
            days = _feasible_completion_sample(branch, rng)
            if days is None:
                continue
            sampled += 1
            result = cache.get(branch["branch_id"])
            if result is None:
                result = calculate_completion_time(branch)
                cache[branch["branch_id"]] = result
            self.assertGreaterEqual(days, result["completion_days"]["min"])
            self.assertLessEqual(days, result["completion_days"]["max"])
        self.assertGreaterEqual(sampled, 250)

    def test_enumerate_completion_range_matches_realized_schedules(self) -> None:
        """Spec §12.1 | Bug it catches: the compatibility enumeration returns a different range."""
        branch = _branch(
            first_planting={
                "earliest": "2026-01-01",
                "latest": "2026-01-10",
            },
            third_harvest={
                "earliest": "2026-04-01",
                "latest": "2026-04-20",
            },
        )
        corner = calculate_completion_time(branch)
        enumerated = enumerate_completion_range(branch)
        self.assertTrue(enumerated["enumeration_used"])
        self.assertEqual(enumerated["range_basis"], "enumerated_realizations")
        self.assertEqual(
            enumerated["completion_days"], corner["completion_days"]
        )
        self.assertEqual(
            enumerated["min_realization"]["first_planting"],
            corner["min_realization"]["p1"],
        )
        self.assertEqual(
            enumerated["min_realization"]["third_harvest"],
            corner["min_realization"]["h3"],
        )
        self.assertEqual(
            enumerated["max_realization"]["first_planting"],
            corner["max_realization"]["p1"],
        )
        self.assertEqual(
            enumerated["max_realization"]["third_harvest"],
            corner["max_realization"]["h3"],
        )

    def test_result_is_json_serializable(self) -> None:
        """Spec §14.4 | Bug it catches: dates or non-finite values leak into JSON."""
        result = calculate_completion_time(_branch())
        encoded = json.dumps(result, allow_nan=False)
        self.assertNotIn("NaN", encoded)
        self.assertIsInstance(json.loads(encoded)["completion_days"]["min"], int)

    def test_three_families_counts_all_distinct(self) -> None:
        """Spec §13 | Bug it catches: distinct family count is wrong or a soil-health claim appears."""
        result = calculate_diversity_metrics(_diversity_branch())
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["distinct_family_count"], 3)
        self.assertEqual(
            result["families"], ["Poaceae", "Fabaceae", "Brassicaceae"]
        )
        self.assertEqual(result["family_repeat_count"], 0)
        self.assertEqual(result["legume_present"], True)
        self.assertEqual(result["legume_crop_ids"], ["crop_b"])
        self.assertEqual(
            result["basis"], "crop_family_count_product_convention"
        )
        self.assertIn("not a measured soil-health", result["diversity_note"])
        self.assertIn("not a guaranteed", result["legume_note"])

    def test_two_families_reports_repeat_proxy(self) -> None:
        """Spec §13 | Bug it catches: repeated family values are counted as distinct."""
        result = calculate_diversity_metrics(
            _diversity_branch(families=(" Poaceae ", "poaceae", "Fabaceae"))
        )
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["distinct_family_count"], 2)
        self.assertEqual(result["families"], ["Poaceae", "Fabaceae"])
        self.assertEqual(result["family_repeat_count"], 1)

    def test_legume_presence_true_and_false(self) -> None:
        """Spec §13 | Bug it catches: legume presence is inverted or overclaimed as N credit."""
        with_legume = calculate_diversity_metrics(
            _diversity_branch(legume_flags=(False, True, False))
        )
        without = calculate_diversity_metrics(
            _diversity_branch(legume_flags=(False, False, False))
        )
        self.assertTrue(with_legume["legume_present"])
        self.assertEqual(with_legume["legume_crop_ids"], ["crop_b"])
        self.assertIn("not a guaranteed", with_legume["legume_note"])
        self.assertFalse(without["legume_present"])
        self.assertEqual(without["legume_crop_ids"], [])
        self.assertIn("No legume", without["legume_note"])

    def test_missing_family_or_legume_flag_is_unknown(self) -> None:
        """Spec §13 | Bug it catches: missing family or legume evidence becomes zero/false."""
        missing_family = calculate_diversity_metrics(
            _diversity_branch(families=(None, "Fabaceae", "Poaceae"))
        )
        self.assertEqual(missing_family["status"], "unknown")
        self.assertIsNone(missing_family["distinct_family_count"])
        self.assertIsNone(missing_family["families"])
        self.assertIsNone(missing_family["family_repeat_count"])
        self.assertIn("crop_family", missing_family["missing_evidence"])

        missing_legume = calculate_diversity_metrics(
            _diversity_branch(legume_flags=(False, None, False))
        )
        self.assertEqual(missing_legume["status"], "unknown")
        self.assertEqual(missing_legume["distinct_family_count"], 3)
        self.assertIsNone(missing_legume["legume_present"])
        self.assertEqual(missing_legume["legume_crop_ids"], [])
        self.assertIn("is_legume_n_fixing", missing_legume["missing_evidence"])

    def test_malformed_branch_shape_is_unavailable(self) -> None:
        """Spec §14.4 | Bug it catches: malformed branches crash or return metrics."""
        base = _diversity_branch()
        cases = (
            None,
            {},
            {"crops": base["crops"][:2], "transitions": base["transitions"]},
            {"crops": base["crops"], "transitions": base["transitions"][:1]},
        )
        for branch in cases:
            with self.subTest(branch=branch):
                result = calculate_diversity_metrics(branch)
                self.assertEqual(result["status"], "unavailable")
                self.assertIsNone(result["distinct_family_count"])
                self.assertIsNone(result["families"])
                self.assertIsNone(result["family_repeat_count"])
                self.assertIsNone(result["legume_present"])
                self.assertEqual(result["reason"], "INVALID_BRANCH_SHAPE")

    def test_diversity_result_is_json_serializable(self) -> None:
        """Spec §14.4 | Bug it catches: non-JSON values leak from diversity metrics."""
        result = calculate_diversity_metrics(_diversity_branch())
        encoded = json.dumps(result, allow_nan=False)
        self.assertNotIn("NaN", encoded)
        self.assertEqual(json.loads(encoded)["distinct_family_count"], 3)

    def test_real_branch_uses_profile_legume_fallback(self) -> None:
        """Spec §13 | Bug it catches: real E6 branches lose legume presence without profile lookup."""
        profiles = load_crop_profiles(DATA_CSV)
        expanded = expand_branches(
            profiles,
            "2026-11-06",
            max_waiting_days=365,
            max_initial_wait_days=365,
        )
        legume_ids = {"lentil_binamasur9", "mung_bari_mung6_kharif1"}
        branch = next(
            branch
            for branch in expanded["branches"]
            if any(crop["crop_id"] in legume_ids for crop in branch["crops"])
        )
        with_profiles = calculate_diversity_metrics(branch, profiles)
        self.assertEqual(with_profiles["status"], "ok")
        self.assertTrue(with_profiles["legume_present"])
        self.assertTrue(
            set(with_profiles["legume_crop_ids"]) & legume_ids
        )
        without_profiles = calculate_diversity_metrics(branch)
        self.assertEqual(without_profiles["status"], "unknown")
        self.assertIsNone(without_profiles["legume_present"])
        self.assertIn(
            "is_legume_n_fixing", without_profiles["missing_evidence"]
        )

    def test_profile_family_and_legume_fallback_with_node_precedence(self) -> None:
        """Spec §13 | Bug it catches: profile fallback is ignored or overrides crop-node values."""
        profiles = {
            "crop_a": {"family": "Poaceae", "is_legume_n_fixing": False},
            "crop_b": {"family": "Fabaceae", "is_legume_n_fixing": True},
            "crop_c": {"family": "Poaceae", "is_legume_n_fixing": False},
        }
        fallback = calculate_diversity_metrics(
            _diversity_branch(
                families=(None, None, None),
                legume_flags=(None, None, None),
            ),
            profiles,
        )
        self.assertEqual(fallback["status"], "ok")
        self.assertEqual(fallback["distinct_family_count"], 2)
        self.assertEqual(fallback["families"], ["Poaceae", "Fabaceae"])
        self.assertTrue(fallback["legume_present"])
        self.assertEqual(fallback["legume_crop_ids"], ["crop_b"])

        node = _diversity_branch(
            families=("Brassicaceae", "Fabaceae", "Poaceae"),
            legume_flags=(False, False, False),
        )
        precedence = calculate_diversity_metrics(node, profiles)
        self.assertIn("Brassicaceae", precedence["families"])
        self.assertFalse(precedence["legume_present"])

    def test_economics_metrics_are_unavailable_and_scenarios_empty(self) -> None:
        """Spec §12.3/§17.15 | Bug it catches: missing economics becomes zero or estimated."""
        result = build_economics_metrics(_diversity_branch(), _economics_profiles())
        self.assertEqual(result["status"], "unavailable")
        self.assertEqual(result["reason"], "Economic estimate unavailable.")
        self.assertEqual(result["scenarios"], [])
        for key in (
            "gross_revenue_bdt_per_ha",
            "production_cost_bdt_per_ha",
            "net_return_bdt_per_ha",
            "upfront_cash_bdt_per_ha",
        ):
            with self.subTest(metric=key):
                metric = result[key]
                self.assertEqual(metric["status"], "unavailable")
                self.assertIsNone(metric["value_bdt_per_ha"])
                self.assertEqual(metric["unit"], "BDT/ha")

    def test_yield_reference_context_is_not_used_for_revenue(self) -> None:
        """Spec §12.3 | Bug it catches: static reference yields are converted into revenue."""
        result = build_economics_metrics(_diversity_branch(), _economics_profiles())
        context = result["yield_reference_context"]
        self.assertEqual(len(context), 3)
        for item in context:
            self.assertEqual(item["status"], "static_reference_not_used")
            self.assertEqual(item["yield_reference_low_t_ha"], 4.0)
            self.assertEqual(item["yield_reference_high_t_ha"], 5.0)
            self.assertEqual(item["yield_basis"], "synthetic test reference")
        self.assertIsNone(
            result["gross_revenue_bdt_per_ha"]["value_bdt_per_ha"]
        )

        without_profiles = build_economics_metrics(_diversity_branch())
        self.assertTrue(
            all(
                item["yield_reference_low_t_ha"] is None
                for item in without_profiles["yield_reference_context"]
            )
        )
        self.assertIsNone(
            without_profiles["price_evidence"]["market_price_mode"]
        )

    def test_price_evidence_is_dynamic_external_without_value(self) -> None:
        """Spec §12.3 | Bug it catches: a price value or static price is invented."""
        result = build_economics_metrics(_diversity_branch(), _economics_profiles())
        price = result["price_evidence"]
        self.assertEqual(price["status"], "unavailable")
        self.assertEqual(price["market_price_mode"], "DYNAMIC_EXTERNAL")
        self.assertEqual(price["source_barc_zoning"], "https://example.test/barc")
        self.assertIsNone(price["price_value"])
        self.assertEqual(len(price["per_crop"]), 3)
        self.assertNotIn("price_value", price["per_crop"][0])

    def test_economics_missing_evidence_ids_are_exact(self) -> None:
        """Spec §12.3/§12.4 | Bug it catches: missing economic evidence IDs are omitted."""
        result = build_economics_metrics(_diversity_branch(), _economics_profiles())
        self.assertEqual(
            result["missing_evidence"],
            [
                "production_cost_evidence",
                "farm_gate_price_evidence",
                "validated_typical_yield_or_attainable_basis",
                "cash_flow_schedule",
            ],
        )

    def test_economics_malformed_branch_is_unavailable(self) -> None:
        """Spec §14.4 | Bug it catches: malformed branches crash or return economics."""
        base = _diversity_branch()
        cases = (
            None,
            {},
            {"crops": base["crops"][:2], "transitions": base["transitions"]},
            {"crops": base["crops"], "transitions": base["transitions"][:1]},
        )
        for branch in cases:
            with self.subTest(branch=branch):
                result = build_economics_metrics(branch)
                self.assertEqual(result["status"], "unavailable")
                self.assertEqual(result["reason"], "INVALID_BRANCH_SHAPE")
                self.assertEqual(result["scenarios"], [])
                self.assertEqual(result["yield_reference_context"], [])
                self.assertIsNone(
                    result["gross_revenue_bdt_per_ha"]["value_bdt_per_ha"]
                )

    def test_economics_result_is_json_serializable(self) -> None:
        """Spec §14.4 | Bug it catches: non-JSON values leak from economics metrics."""
        result = build_economics_metrics(_diversity_branch(), _economics_profiles())
        encoded = json.dumps(result, allow_nan=False)
        self.assertNotIn("NaN", encoded)
        self.assertIsNone(
            json.loads(encoded)["net_return_bdt_per_ha"]["value_bdt_per_ha"]
        )

    def test_economics_module_has_no_crop_id_branches(self) -> None:
        """Spec §14.4 | Bug it catches: a crop-specific branch is added to economics."""
        source = SRC.read_text(encoding="utf-8")
        for crop_id in _CROP_IDS:
            self.assertNotIn(crop_id, source)

    def test_module_has_no_crop_id_branches(self) -> None:
        """Spec §14.4 | Bug it catches: a crop-specific branch is added to branch metrics."""
        source = SRC.read_text(encoding="utf-8")
        for crop_id in _CROP_IDS:
            self.assertNotIn(crop_id, source)


class ResourceMetricsTests(unittest.TestCase):
    def test_resources_remain_four_separate_metrics(self) -> None:
        """Spec §12.2 | Bug it catches: unlike resource units collapsed into one score."""
        result = build_resource_metrics(_resource_branch())
        self.assertEqual(
            set(result), {"cash_cost", "irrigation", "labor", "equipment"}
        )
        self.assertFalse(any("score" in key for key in result))
        self.assertFalse(any(key.startswith("total") for key in result))

    def test_cash_labor_and_equipment_are_unavailable(self) -> None:
        """Spec §12.2 | Bug it catches: missing cost/labor/equipment evidence becomes zero."""
        result = build_resource_metrics(_resource_branch())
        cash = result["cash_cost"]
        self.assertEqual(cash["status"], "unavailable")
        self.assertIsNone(cash["value_bdt_per_ha"])
        self.assertEqual(cash["missing_evidence"], ["production_cost_evidence"])
        for name, evidence in (("labor", "labor_evidence"), ("equipment", "equipment_evidence")):
            with self.subTest(name=name):
                metric = result[name]
                self.assertEqual(metric["status"], "unavailable")
                self.assertIsNone(metric["value"])
                self.assertEqual(metric["missing_evidence"], [evidence])
                self.assertTrue(metric["reason"])

    def test_irrigation_is_context_only_without_numeric_total(self) -> None:
        """Spec §12.2 | Bug it catches: qualitative irrigation guidance summed or ranked."""
        result = build_resource_metrics(_resource_branch())
        irrigation = result["irrigation"]
        self.assertEqual(irrigation["status"], "context_only")
        self.assertEqual(irrigation["ranking_status"], "unranked")
        self.assertIsNone(irrigation["total"])
        self.assertNotIn("dependence_score", irrigation)
        self.assertEqual(len(irrigation["per_crop"]), 3)
        self.assertIn("not comparable", irrigation["reason"])

    def test_irrigation_per_crop_uses_node_then_profile_fallback(self) -> None:
        """Spec §12.2 | Bug it catches: per-crop irrigation context lost or node value overridden."""
        contexts = (
            {
                "crop_id": "crop_a",
                "irrigation_guidance": "node guidance",
                "fao_crop_water_need_min_mm": 100.0,
                "fao_crop_water_need_max_mm": 200.0,
                "local_phase_water_total_mm": 150.0,
                "water_ranking_readiness": "HIGH",
            },
            {"crop_id": "crop_b"},
            {"crop_id": "crop_c"},
        )
        profiles = {
            "crop_a": {
                "irrigation_guidance": "profile A",
                "fao_crop_water_need_min_mm": 999.0,
                "fao_crop_water_need_max_mm": 999.0,
                "local_phase_water_total_mm": 999.0,
                "water_ranking_readiness": "LOW",
            },
            "crop_b": {
                "irrigation_guidance": "profile B",
                "fao_crop_water_need_min_mm": 10.0,
                "fao_crop_water_need_max_mm": 20.0,
                "local_phase_water_total_mm": 15.0,
                "water_ranking_readiness": "PARTIAL",
            },
            "crop_c": {},
        }
        result = build_resource_metrics(_resource_branch(contexts), profiles)
        per_crop = result["irrigation"]["per_crop"]
        self.assertEqual(
            [item["crop_id"] for item in per_crop],
            ["crop_a", "crop_b", "crop_c"],
        )
        self.assertEqual(per_crop[0]["irrigation_guidance"], "node guidance")
        self.assertEqual(per_crop[0]["fao_crop_water_need_min_mm"], 100.0)
        self.assertEqual(per_crop[0]["local_phase_water_total_mm"], 150.0)
        self.assertEqual(per_crop[0]["water_ranking_readiness"], "HIGH")
        self.assertEqual(per_crop[1]["irrigation_guidance"], "profile B")
        self.assertEqual(per_crop[1]["fao_crop_water_need_max_mm"], 20.0)
        self.assertEqual(per_crop[1]["water_ranking_readiness"], "PARTIAL")
        self.assertIsNone(per_crop[2]["irrigation_guidance"])
        self.assertIsNone(per_crop[2]["fao_crop_water_need_min_mm"])

    def test_malformed_branch_makes_all_resources_unavailable(self) -> None:
        """Spec §14.4 | Bug it catches: malformed branches return context or numeric resources."""
        base = _resource_branch()
        cases = (
            None,
            {},
            _resource_branch(crop_count=2),
            _resource_branch(transition_count=1),
            {"crops": base["crops"], "transitions": [None, None]},
        )
        for branch in cases:
            with self.subTest(branch=branch):
                result = build_resource_metrics(branch)
                for name in ("cash_cost", "irrigation", "labor", "equipment"):
                    self.assertEqual(result[name]["status"], "unavailable")
                    self.assertEqual(
                        result[name]["reason"], "INVALID_BRANCH_SHAPE"
                    )
                self.assertIsNone(result["cash_cost"]["value_bdt_per_ha"])
                self.assertIsNone(result["labor"]["value"])
                self.assertIsNone(result["equipment"]["value"])
                self.assertEqual(result["irrigation"]["per_crop"], [])
                self.assertIsNone(result["irrigation"]["total"])

    def test_resource_metrics_are_json_serializable(self) -> None:
        """Spec §14.4 | Bug it catches: non-JSON values leak from resource metrics."""
        result = build_resource_metrics(_resource_branch())
        encoded = json.dumps(result, allow_nan=False)
        self.assertNotIn("NaN", encoded)
        self.assertEqual(
            json.loads(encoded)["irrigation"]["ranking_status"], "unranked"
        )


class RankingTests(unittest.TestCase):
    def test_fastest_completion_ranks_conditional_and_notes_empty_candidate(self) -> None:
        """Spec §12.1/§13 | Bug it catches: fastest ranking crosses groups or claims a winner."""
        slow = _ranking_branch(
            "b_slow",
            third_harvest={"earliest": "2026-04-01", "latest": "2026-05-01"},
        )
        fast = _ranking_branch("b_fast")
        result = rank_branches([slow, fast], "fastest_completion")
        self.assertEqual(result["preference"], "fastest_completion")
        self.assertEqual(result["metric"], "completion_days.max")
        self.assertEqual(result["direction"], "ascending")
        self.assertEqual(result["groups"]["candidate"]["count"], 0)
        self.assertEqual(result["groups"]["candidate"]["ranked"], [])
        conditional = result["groups"]["conditional"]
        self.assertEqual(conditional["count"], 2)
        self.assertEqual(
            [entry["branch_id"] for entry in conditional["ranked"]],
            ["b_fast", "b_slow"],
        )
        self.assertEqual(conditional["ranked"][0]["metric_value"], 101)
        self.assertEqual(
            conditional["ranked"][0]["completion_days"],
            {"min": 89, "max": 101},
        )
        self.assertFalse(result["no_winner"])
        self.assertTrue(
            any("Candidate group is empty" in note for note in result["notes"])
        )

    def test_fastest_completion_overlap_note_is_visible(self) -> None:
        """Spec §12.1/§13 | Bug it catches: overlapping completion ranges claim a definitive winner."""
        result = rank_branches(
            [
                _ranking_branch("b_early"),
                _ranking_branch(
                    "b_late",
                    third_harvest={
                        "earliest": "2026-04-06",
                        "latest": "2026-04-17",
                    },
                ),
            ],
            "fastest_completion",
        )
        self.assertEqual(
            [entry["branch_id"] for entry in result["groups"]["conditional"]["ranked"]],
            ["b_early", "b_late"],
        )
        self.assertTrue(any("overlap" in note.lower() for note in result["notes"]))
        self.assertFalse(result["no_winner"])

    def test_diversity_ranks_descending_and_shows_legume_separately(self) -> None:
        """Spec §13 | Bug it catches: diversity order is ascending or legume is folded into family count."""
        result = rank_branches(
            [
                _ranking_branch(
                    "b_two",
                    families=("Poaceae", "Poaceae", "Fabaceae"),
                    legume_flags=(False, False, False),
                ),
                _ranking_branch("b_three"),
            ],
            "more_crop_diversity",
        )
        ranked = result["groups"]["conditional"]["ranked"]
        self.assertEqual([entry["branch_id"] for entry in ranked], ["b_three", "b_two"])
        self.assertEqual(ranked[0]["metric_value"], 3)
        self.assertEqual(ranked[0]["family_repeat_count"], 0)
        self.assertTrue(ranked[0]["legume_present"])
        self.assertEqual(ranked[0]["legume_crop_ids"], ["b_three_crop_1"])
        self.assertEqual(ranked[1]["metric_value"], 2)
        self.assertEqual(ranked[1]["family_repeat_count"], 1)
        self.assertEqual(
            ranked[0]["basis"], "crop_family_count_product_convention"
        )
        self.assertIn("product convention", ranked[0]["diversity_note"])

    def test_economic_and_irrigation_preferences_are_unranked_no_winner(self) -> None:
        """Spec §13/§17.15 | Bug it catches: unavailable cost/return/irrigation becomes zero and ranks."""
        branches = [_ranking_branch("b_one"), _ranking_branch("b_two")]
        expected = {
            "lowest_total_cost": "production_cost_bdt_per_ha",
            "highest_net_return": "net_return_bdt_per_ha",
            "lowest_upfront_cash": "upfront_cash_bdt_per_ha",
            "least_irrigation_dependence": "irrigation_dependence",
        }
        for preference, metric in expected.items():
            with self.subTest(preference=preference):
                result = rank_branches(branches, preference)
                self.assertEqual(result["metric"], metric)
                self.assertEqual(result["direction"], "unavailable")
                self.assertTrue(result["no_winner"])
                for name in ("candidate", "conditional"):
                    group = result["groups"][name]
                    self.assertEqual(group["ranked"], [])
                    self.assertEqual(group["count"], 2 if name == "conditional" else 0)
                    for entry in group["unranked"]:
                        self.assertIsNone(entry["metric_value"])
                        self.assertTrue(entry["reason"])
                        self.assertTrue(entry["missing_evidence"])

    def test_missing_completion_is_unranked_not_favorable(self) -> None:
        """Spec §13/§14.4 | Bug it catches: missing completion gets a zero or favorable rank."""
        result = rank_branches(
            [_ranking_branch("b_missing", third_harvest=None)],
            "fastest_completion",
        )
        conditional = result["groups"]["conditional"]
        self.assertEqual(conditional["count"], 1)
        self.assertEqual(conditional["ranked"], [])
        self.assertEqual(len(conditional["unranked"]), 1)
        self.assertTrue(result["no_winner"])
        self.assertIsNone(conditional["unranked"][0]["metric_value"])
        self.assertIn("third_harvest_range", conditional["unranked"][0]["missing_evidence"])

    def test_blocked_branch_is_excluded_not_revived(self) -> None:
        """Spec §13/§17.14 | Bug it catches: a preference revives an unsupported branch."""
        result = rank_branches(
            [
                _ranking_branch("b_blocked", status="unsupported"),
                _ranking_branch("b_ok"),
            ],
            "fastest_completion",
        )
        self.assertEqual(result["excluded"], ["b_blocked"])
        self.assertEqual(
            [entry["branch_id"] for entry in result["groups"]["conditional"]["ranked"]],
            ["b_ok"],
        )
        self.assertFalse(result["no_winner"])

    def test_candidate_and_conditional_groups_stay_separate(self) -> None:
        """Spec §13 | Bug it catches: candidate and conditional branches share one ranking."""
        result = rank_branches(
            [
                _ranking_branch("b_candidate", status="candidate"),
                _ranking_branch("b_conditional", status="conditional"),
            ],
            "fastest_completion",
        )
        self.assertEqual(result["groups"]["candidate"]["count"], 1)
        self.assertEqual(result["groups"]["conditional"]["count"], 1)
        self.assertEqual(
            [entry["branch_id"] for entry in result["groups"]["candidate"]["ranked"]],
            ["b_candidate"],
        )
        self.assertEqual(
            [entry["branch_id"] for entry in result["groups"]["conditional"]["ranked"]],
            ["b_conditional"],
        )

    def test_ties_break_deterministically_by_branch_id(self) -> None:
        """Spec §13/§14.4 | Bug it catches: equal metrics order nondeterministically."""
        result = rank_branches(
            [_ranking_branch("b_b"), _ranking_branch("b_a")],
            "fastest_completion",
        )
        self.assertEqual(
            [entry["branch_id"] for entry in result["groups"]["conditional"]["ranked"]],
            ["b_a", "b_b"],
        )
        self.assertIn("branch_id", result["method"])

    def test_invalid_preference_raises(self) -> None:
        """Spec §13 | Bug it catches: an unknown preference silently falls back."""
        with self.assertRaises(ValueError):
            rank_branches([], "unknown_preference")

    def test_real_420_branches_rank_fastest_and_diversity(self) -> None:
        """Spec §13/§17.14-17 | Bug it catches: real conditional branches are not ranked or groups mix."""
        profiles = load_crop_profiles(DATA_CSV)
        expanded = expand_branches(
            profiles,
            "2026-11-06",
            max_waiting_days=365,
            max_initial_wait_days=365,
        )
        branches = expanded["branches"]
        self.assertEqual(len(branches), 420)
        fastest = rank_branches(branches, "fastest_completion", profiles)
        self.assertEqual(fastest["groups"]["candidate"]["count"], 0)
        self.assertEqual(fastest["groups"]["conditional"]["count"], 420)
        self.assertEqual(len(fastest["groups"]["conditional"]["ranked"]), 420)
        self.assertEqual(fastest["groups"]["conditional"]["unranked"], [])
        self.assertTrue(any("overlap" in note.lower() for note in fastest["notes"]))
        diversity = rank_branches(branches, "more_crop_diversity", profiles)
        self.assertEqual(diversity["groups"]["candidate"]["count"], 0)
        self.assertGreater(len(diversity["groups"]["conditional"]["ranked"]), 0)
        economics = rank_branches(branches, "lowest_total_cost", profiles)
        self.assertTrue(economics["no_winner"])
        self.assertEqual(economics["groups"]["conditional"]["ranked"], [])
        self.assertEqual(len(economics["groups"]["conditional"]["unranked"]), 420)

    def test_ranking_is_json_serializable(self) -> None:
        """Spec §14.4 | Bug it catches: non-JSON values leak from ranking output."""
        result = rank_branches([_ranking_branch("b_one")], "fastest_completion")
        encoded = json.dumps(result, allow_nan=False)
        self.assertNotIn("NaN", encoded)
        self.assertFalse(json.loads(encoded)["no_winner"])


if __name__ == "__main__":
    unittest.main()
