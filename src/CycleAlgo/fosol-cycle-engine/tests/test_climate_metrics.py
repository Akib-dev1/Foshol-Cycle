"""Tests for the three iteration-2 historical POWER comparison views."""

from __future__ import annotations

import datetime as dt
import unittest
from unittest.mock import patch

from src import climate_metrics
from src.branch_metrics import rank_branches
from src.climate_metrics import (
    branch_common_seasons,
    build_climate_metrics,
    evaluate_climate,
)


def _profile(crop_id, optimum=(15, 25), tolerance=(5, 35)):
    return {
        "crop_id": crop_id,
        "temp_opt_min_c": optimum[0],
        "temp_opt_max_c": optimum[1],
        "temp_tol_min_c": tolerance[0],
        "temp_tol_max_c": tolerance[1],
        "temperature_provenance": {
            "source": "test://ecocrop",
            "eco_port_code": "test",
            "scientific_name": "test crop",
        },
    }


PROFILES = {crop_id: _profile(crop_id) for crop_id in ("a", "b", "c")}


def _series(start: dt.date, temps: list[float], rains: list[float]) -> dict:
    observations = {}
    for index, (temp, rain) in enumerate(zip(temps, rains)):
        date = (start + dt.timedelta(days=index)).isoformat()
        observations[date] = {
            "T2M": temp,
            "PRECTOTCORR": rain,
            "QV2M": 10.0,
        }
    return observations


def _environment(*series: dict) -> dict:
    observations = {}
    for item in series:
        observations.update(item)
    return {
        "observations": observations,
        "observation_start": min(observations),
        "observation_end": max(observations),
        "fill_value": -999.0,
        "variables": {
            "T2M": {"units": "C", "longname": "Temperature at 2 Meters"},
            "PRECTOTCORR": {
                "units": "mm/day",
                "longname": "Precipitation Corrected",
            },
        },
    }


def _completion(start: dt.date, days: int) -> dict:
    end = start + dt.timedelta(days=days - 1)
    realization = {
        "p1": start.isoformat(),
        "h1": end.isoformat(),
        "p2": start.isoformat(),
        "h2": end.isoformat(),
        "p3": start.isoformat(),
        "h3": end.isoformat(),
    }
    return {
        "status": "ok",
        "min_realization": dict(realization),
        "max_realization": dict(realization),
        "completion_days": {"min": days, "max": days},
    }


def _branch(branch_id: str, start: dt.date, days: int, status="conditional"):
    return {
        "branch_id": branch_id,
        "status": status,
        "crops": [{"crop_id": crop_id} for crop_id in ("a", "b", "c")],
        "transitions": [{}, {}],
        "metrics": {"completion": _completion(start, days)},
    }


def _attach(branch, environment, start_year=2020, end_year=2021, last="2021-12-31"):
    climate = build_climate_metrics(
        branch,
        PROFILES,
        environment,
        branch["metrics"]["completion"],
        start_year=start_year,
        end_year=end_year,
        last_complete_data_date=last,
    )
    branch["metrics"]["climate"] = climate
    return climate


class ClimateMetricTests(unittest.TestCase):
    def _hand_environment(self):
        return _environment(
            _series(
                dt.date(2020, 1, 1),
                [20] * 10,
                [0, 0, 1, 0, 0, 0, 20, 0, 5, 0],
            ),
            _series(dt.date(2021, 1, 1), [30] * 10, [0] * 10),
        )

    def test_hand_calculated_temperature_dry_spell_and_heavy_rain(self) -> None:
        branch = _branch("b_hand", dt.date(2026, 1, 1), 10)
        climate = _attach(branch, self._hand_environment())
        self.assertEqual(climate["status"], "ok")
        self.assertEqual(
            sorted(branch_common_seasons(climate, "temperature")), [2020, 2021]
        )
        self.assertEqual(
            sorted(branch_common_seasons(climate, "rain")), [2020, 2021]
        )
        summary = climate["summary"]["min_realization"]
        self.assertEqual(summary["temperature_distance_c"], 2.5)
        self.assertEqual(summary["dry_spell_days"], 6.5)
        self.assertAlmostEqual(summary["heavy_rain_frequency"], 0.05)
        self.assertEqual(summary["rainfall_median_mm"], 13.0)
        crop = summary["per_crop"][0]
        self.assertEqual(crop["temperature"]["median_distance_c"], 2.5)
        self.assertEqual(crop["dry_spell"]["median_longest_run_days"], 6.5)
        self.assertEqual(crop["heavy_rain"]["days"], 1)
        self.assertEqual(crop["heavy_rain"]["valid_days"], 20)
        self.assertEqual(crop["rainfall"]["median_total_mm"], 13.0)
        self.assertEqual(crop["rainfall"]["iqr_total_mm"], 13.0)

    def test_threshold_boundaries_and_dry_run_reset(self) -> None:
        environment = _environment(
            _series(
                dt.date(2020, 1, 1),
                [20] * 10,
                [0.99, 1.0, 19.99, 20.0, 0, 0, 0, 0, 0, 0],
            )
        )
        branch = _branch("b_boundary", dt.date(2026, 1, 1), 10)
        climate = _attach(
            branch, environment, start_year=2020, end_year=2020, last="2020-12-31"
        )
        record = climate["per_schedule"]["min_realization"]["crops"][0]["season_records"]["2020"]
        self.assertEqual(record["longest_dry_run_days"], 6)
        self.assertEqual(record["heavy_rain_days"], 1)
        self.assertEqual(record["rain_total_mm"], 41.98)

    def test_missing_rain_day_excludes_the_season(self) -> None:
        environment = self._hand_environment()
        del environment["observations"]["2020-01-05"]["PRECTOTCORR"]
        branch = _branch("b_missing", dt.date(2026, 1, 1), 10)
        climate = _attach(branch, environment)
        self.assertEqual(branch_common_seasons(climate, "rain"), {2021})
        self.assertEqual(
            branch_common_seasons(climate, "temperature"), {2020, 2021}
        )
        self.assertNotIn(
            "2020",
            climate["per_schedule"]["min_realization"]["crops"][0]["rain_seasons"],
        )

    def test_missing_temperature_units_keep_rain_views(self) -> None:
        environment = self._hand_environment()
        environment["variables"].pop("T2M")
        branch = _branch("b_no_temp_units", dt.date(2026, 1, 1), 10)
        climate = _attach(branch, environment)
        self.assertEqual(branch_common_seasons(climate, "temperature"), set())
        self.assertEqual(
            branch_common_seasons(climate, "rain"), {2020, 2021}
        )
        self.assertIsNotNone(
            evaluate_climate(
                climate,
                branch_common_seasons(climate, "rain"),
                "least_heavy_rain_exposure",
            )
        )
        self.assertIsNone(
            evaluate_climate(
                climate,
                branch_common_seasons(climate, "temperature"),
                "closest_temperature_match",
            )
        )

    def test_incompatible_rain_units_keep_temperature_view(self) -> None:
        environment = self._hand_environment()
        environment["variables"]["PRECTOTCORR"]["units"] = "inch/day"
        branch = _branch("b_bad_rain_units", dt.date(2026, 1, 1), 10)
        climate = _attach(branch, environment)
        self.assertEqual(
            branch_common_seasons(climate, "temperature"), {2020, 2021}
        )
        self.assertEqual(branch_common_seasons(climate, "rain"), set())
        self.assertIsNotNone(
            evaluate_climate(
                climate,
                branch_common_seasons(climate, "temperature"),
                "closest_temperature_match",
            )
        )
        self.assertIsNone(
            evaluate_climate(
                climate,
                branch_common_seasons(climate, "rain"),
                "least_dry_spell_exposure",
            )
        )

    def test_missing_temperature_observations_do_not_remove_rain_seasons(self) -> None:
        environment = self._hand_environment()
        for values in environment["observations"].values():
            values.pop("T2M")
        branch = _branch("b_no_temp", dt.date(2026, 1, 1), 10)
        climate = _attach(branch, environment)
        self.assertEqual(branch_common_seasons(climate, "temperature"), set())
        self.assertEqual(branch_common_seasons(climate, "rain"), {2020, 2021})

    def test_unequal_durations_use_heavy_rain_frequency_not_raw_count(self) -> None:
        environment = _environment(
            _series(dt.date(2020, 1, 1), [20] * 20, [20] * 20),
            _series(dt.date(2021, 1, 1), [20] * 20, [20] * 20),
        )
        short = _branch("b_short", dt.date(2026, 1, 1), 10)
        long = _branch("b_long", dt.date(2026, 1, 1), 20)
        short_climate = _attach(short, environment)
        long_climate = _attach(long, environment)
        short_summary = short_climate["summary"]["min_realization"]
        long_summary = long_climate["summary"]["min_realization"]
        self.assertEqual(short_summary["heavy_rain_frequency"], 1.0)
        self.assertEqual(long_summary["heavy_rain_frequency"], 1.0)
        self.assertEqual(short_summary["per_crop"][0]["heavy_rain"]["days"], 20)
        self.assertEqual(long_summary["per_crop"][0]["heavy_rain"]["days"], 40)

    def test_temperature_ranking_reverses_when_observations_change(self) -> None:
        jan = _series(dt.date(2020, 1, 1), [30] * 10, [0] * 10)
        feb = _series(dt.date(2020, 2, 1), [20] * 10, [0] * 10)
        jan_2021 = _series(dt.date(2021, 1, 1), [30] * 10, [0] * 10)
        feb_2021 = _series(dt.date(2021, 2, 1), [20] * 10, [0] * 10)
        first_env = _environment(jan, feb, jan_2021, feb_2021)
        first_a = _branch("b_a", dt.date(2026, 1, 1), 10)
        first_b = _branch("b_b", dt.date(2026, 2, 1), 10)
        _attach(first_a, first_env)
        _attach(first_b, first_env)
        first = rank_branches(
            [first_a, first_b], "closest_temperature_match"
        )
        self.assertEqual(
            [entry["branch_id"] for entry in first["groups"]["conditional"]["ranked"]],
            ["b_b", "b_a"],
        )

        jan2 = _series(dt.date(2020, 1, 1), [20] * 10, [0] * 10)
        feb2 = _series(dt.date(2020, 2, 1), [30] * 10, [0] * 10)
        jan_2021_2 = _series(dt.date(2021, 1, 1), [20] * 10, [0] * 10)
        feb_2021_2 = _series(dt.date(2021, 2, 1), [30] * 10, [0] * 10)
        second_env = _environment(jan2, feb2, jan_2021_2, feb_2021_2)
        second_a = _branch("b_a", dt.date(2026, 1, 1), 10)
        second_b = _branch("b_b", dt.date(2026, 2, 1), 10)
        _attach(second_a, second_env)
        _attach(second_b, second_env)
        second = rank_branches(
            [second_a, second_b], "closest_temperature_match"
        )
        self.assertEqual(
            [entry["branch_id"] for entry in second["groups"]["conditional"]["ranked"]],
            ["b_a", "b_b"],
        )

    def _two_period_environment(self, january_rain, february_rain):
        return _environment(
            _series(dt.date(2020, 1, 1), [20] * 10, january_rain),
            _series(dt.date(2020, 2, 1), [20] * 10, february_rain),
            _series(dt.date(2021, 1, 1), [20] * 10, january_rain),
            _series(dt.date(2021, 2, 1), [20] * 10, february_rain),
        )

    def test_dry_spell_ranking_reverses_when_rain_changes(self) -> None:
        first_env = self._two_period_environment([0] * 10, [1] * 10)
        first_a = _branch("b_a", dt.date(2026, 1, 1), 10)
        first_b = _branch("b_b", dt.date(2026, 2, 1), 10)
        _attach(first_a, first_env)
        _attach(first_b, first_env)
        first = rank_branches(
            [first_a, first_b], "least_dry_spell_exposure"
        )
        self.assertEqual(
            [e["branch_id"] for e in first["groups"]["conditional"]["ranked"]],
            ["b_b", "b_a"],
        )

        second_env = self._two_period_environment([1] * 10, [0] * 10)
        second_a = _branch("b_a", dt.date(2026, 1, 1), 10)
        second_b = _branch("b_b", dt.date(2026, 2, 1), 10)
        _attach(second_a, second_env)
        _attach(second_b, second_env)
        second = rank_branches(
            [second_a, second_b], "least_dry_spell_exposure"
        )
        self.assertEqual(
            [e["branch_id"] for e in second["groups"]["conditional"]["ranked"]],
            ["b_a", "b_b"],
        )

    def test_heavy_rain_ranking_reverses_when_rain_changes(self) -> None:
        first_env = self._two_period_environment([0] * 10, [20] * 10)
        first_a = _branch("b_a", dt.date(2026, 1, 1), 10)
        first_b = _branch("b_b", dt.date(2026, 2, 1), 10)
        _attach(first_a, first_env)
        _attach(first_b, first_env)
        first = rank_branches(
            [first_a, first_b], "least_heavy_rain_exposure"
        )
        self.assertEqual(
            [e["branch_id"] for e in first["groups"]["conditional"]["ranked"]],
            ["b_a", "b_b"],
        )

        second_env = self._two_period_environment([20] * 10, [0] * 10)
        second_a = _branch("b_a", dt.date(2026, 1, 1), 10)
        second_b = _branch("b_b", dt.date(2026, 2, 1), 10)
        _attach(second_a, second_env)
        _attach(second_b, second_env)
        second = rank_branches(
            [second_a, second_b], "least_heavy_rain_exposure"
        )
        self.assertEqual(
            [e["branch_id"] for e in second["groups"]["conditional"]["ranked"]],
            ["b_b", "b_a"],
        )

    def test_missing_temperature_units_do_not_change_rain_ranking(self) -> None:
        environment = self._two_period_environment([0] * 10, [1] * 10)
        branches = [
            _branch("b_a", dt.date(2026, 1, 1), 10),
            _branch("b_b", dt.date(2026, 2, 1), 10),
        ]
        for branch in branches:
            _attach(branch, environment)
        baseline = rank_branches(branches, "least_dry_spell_exposure")
        baseline_order = [
            e["branch_id"] for e in baseline["groups"]["conditional"]["ranked"]
        ]
        baseline_common = baseline["climate"]["common_season_counts"][
            "conditional"
        ]

        missing = {
            **environment,
            "variables": {
                key: value
                for key, value in environment["variables"].items()
                if key != "T2M"
            },
        }
        branches2 = [
            _branch("b_a", dt.date(2026, 1, 1), 10),
            _branch("b_b", dt.date(2026, 2, 1), 10),
        ]
        for branch in branches2:
            _attach(branch, missing)
        result = rank_branches(branches2, "least_dry_spell_exposure")
        self.assertEqual(
            [e["branch_id"] for e in result["groups"]["conditional"]["ranked"]],
            baseline_order,
        )
        self.assertEqual(
            result["climate"]["common_season_counts"]["conditional"],
            baseline_common,
        )

    def test_missing_rain_units_do_not_change_temperature_ranking(self) -> None:
        environment = _environment(
            _series(dt.date(2020, 1, 1), [30] * 10, [0] * 10),
            _series(dt.date(2020, 2, 1), [20] * 10, [0] * 10),
            _series(dt.date(2021, 1, 1), [30] * 10, [0] * 10),
            _series(dt.date(2021, 2, 1), [20] * 10, [0] * 10),
        )
        branches = [
            _branch("b_a", dt.date(2026, 1, 1), 10),
            _branch("b_b", dt.date(2026, 2, 1), 10),
        ]
        for branch in branches:
            _attach(branch, environment)
        baseline = rank_branches(branches, "closest_temperature_match")
        baseline_order = [
            e["branch_id"] for e in baseline["groups"]["conditional"]["ranked"]
        ]
        baseline_common = baseline["climate"]["common_season_counts"][
            "conditional"
        ]

        missing = {
            **environment,
            "variables": {
                key: value
                for key, value in environment["variables"].items()
                if key != "PRECTOTCORR"
            },
        }
        branches2 = [
            _branch("b_a", dt.date(2026, 1, 1), 10),
            _branch("b_b", dt.date(2026, 2, 1), 10),
        ]
        for branch in branches2:
            _attach(branch, missing)
        result = rank_branches(branches2, "closest_temperature_match")
        self.assertEqual(
            [e["branch_id"] for e in result["groups"]["conditional"]["ranked"]],
            baseline_order,
        )
        self.assertEqual(
            result["climate"]["common_season_counts"]["conditional"],
            baseline_common,
        )

    def test_cache_is_isolated_between_environments(self) -> None:
        first_env = self._hand_environment()
        second_env = _environment(
            _series(dt.date(2020, 1, 1), [20] * 10, [20] * 10),
            _series(dt.date(2021, 1, 1), [20] * 10, [20] * 10),
        )
        cache = {}
        first = _branch("b_a", dt.date(2026, 1, 1), 10)
        second = _branch("b_a", dt.date(2026, 1, 1), 10)
        first_climate = build_climate_metrics(
            first,
            PROFILES,
            first_env,
            first["metrics"]["completion"],
            start_year=2020,
            end_year=2021,
            last_complete_data_date="2021-12-31",
            cache=cache,
        )
        second_climate = build_climate_metrics(
            second,
            PROFILES,
            second_env,
            second["metrics"]["completion"],
            start_year=2020,
            end_year=2021,
            last_complete_data_date="2021-12-31",
            cache=cache,
        )
        self.assertNotEqual(
            first_climate["summary"]["min_realization"]["dry_spell_days"],
            second_climate["summary"]["min_realization"]["dry_spell_days"],
        )
        self.assertNotEqual(
            first_climate["summary"]["min_realization"]["heavy_rain_frequency"],
            second_climate["summary"]["min_realization"]["heavy_rain_frequency"],
        )

    def test_request_cache_reuses_crop_periods_without_changing_results(self) -> None:
        environment = self._hand_environment()
        branch = _branch("b_cached", dt.date(2026, 1, 1), 10)
        kwargs = {
            "start_year": 2020,
            "end_year": 2021,
            "last_complete_data_date": "2021-12-31",
        }
        expected = build_climate_metrics(
            branch, PROFILES, environment, branch["metrics"]["completion"], **kwargs
        )
        cache = {}
        with patch.object(
            climate_metrics, "_season_record", wraps=climate_metrics._season_record
        ) as calculate:
            for _ in range(2):
                actual = build_climate_metrics(
                    branch, PROFILES, environment, branch["metrics"]["completion"],
                    cache=cache, **kwargs
                )
                self.assertEqual(actual, expected)
            self.assertEqual(calculate.call_count, 6)  # Three crops, two years.

    def test_unused_qv2m_does_not_change_climate_or_ranking(self) -> None:
        environment = self._hand_environment()
        branch = _branch("b_a", dt.date(2026, 1, 1), 10)
        climate = _attach(branch, environment)
        before = evaluate_climate(
            climate, branch_common_seasons(climate), "least_dry_spell_exposure"
        )
        changed = {
            **environment,
            "observations": {
                date: {**values, "QV2M": 999.0}
                for date, values in environment["observations"].items()
            },
        }
        branch2 = _branch("b_a", dt.date(2026, 1, 1), 10)
        climate2 = _attach(branch2, changed)
        after = evaluate_climate(
            climate2, branch_common_seasons(climate2), "least_dry_spell_exposure"
        )
        self.assertEqual(before["value"], after["value"])

    def test_common_seasons_and_cross_year_mapping(self) -> None:
        environment = _environment(
            _series(
                dt.date(2020, 12, 25),
                [20] * 12,
                [0, 0, 1] * 4,
            ),
            _series(
                dt.date(2021, 12, 25),
                [20] * 12,
                [0, 0, 1] * 4,
            ),
        )
        branch = _branch("b_cross", dt.date(2026, 12, 25), 12)
        climate = _attach(
            branch, environment, start_year=2020, end_year=2021, last="2021-12-31"
        )
        self.assertEqual(branch_common_seasons(climate, "rain"), {2020})
        self.assertEqual(
            climate["per_schedule"]["min_realization"]["crops"][0]["season_records"]["2020"][
                "start_date"
            ],
            "2020-12-25",
        )

    def test_schedule_labels_and_ties_are_explicit(self) -> None:
        environment = self._hand_environment()
        first = _branch("b_a", dt.date(2026, 1, 1), 10)
        second = _branch("b_b", dt.date(2026, 1, 1), 10)
        _attach(first, environment)
        _attach(second, environment)
        result = rank_branches([first, second], "least_dry_spell_exposure")
        ranked = result["groups"]["conditional"]["ranked"]
        self.assertEqual([entry["branch_id"] for entry in ranked], ["b_a", "b_b"])
        self.assertEqual(ranked[0]["metric_value"], ranked[1]["metric_value"])
        self.assertEqual(
            ranked[0]["ordering_basis"],
            "higher exposure of the two completion-optimized schedules; "
            "not a worst-case bound over all possible schedules",
        )
        self.assertEqual(set(ranked[0]["schedule_values"]), {"min_realization", "max_realization"})
        self.assertIn("common_seasons", ranked[0])

    def test_candidate_and_conditional_groups_remain_separate(self) -> None:
        environment = self._hand_environment()
        candidate = _branch("b_candidate", dt.date(2026, 1, 1), 10, "candidate")
        conditional = _branch("b_conditional", dt.date(2026, 1, 1), 10)
        _attach(candidate, environment)
        _attach(conditional, environment)
        result = rank_branches(
            [candidate, conditional], "least_heavy_rain_exposure"
        )
        self.assertEqual(
            [e["branch_id"] for e in result["groups"]["candidate"]["ranked"]],
            ["b_candidate"],
        )
        self.assertEqual(
            [e["branch_id"] for e in result["groups"]["conditional"]["ranked"]],
            ["b_conditional"],
        )


if __name__ == "__main__":
    unittest.main()
