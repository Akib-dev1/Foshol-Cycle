"""Tests for the iteration-3 featured Rajshahi comparison artifact."""

from __future__ import annotations

import copy
import datetime as dt
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import featured_comparison as featured
from src.crop_profiles import load_crop_profiles
from src.explore import explore

ARTIFACT = ROOT / "examples" / "featured_comparison.json"
DATA = ROOT.parent / "Data" / "fosol_cycle_rajshahi_crop_dataset.csv"
NOW = dt.datetime(2026, 11, 12, 12, 0, tzinfo=dt.timezone.utc)
CONFIG = {
    "max_initial_wait_days": 180,
    "max_waiting_days": None,
    "max_branches": None,
}
EXPECTED = {
    "baseline": (
        "mustard_binasarisha9",
        "boro_brri_dhan28",
        "aman_br11",
    ),
    "mung": (
        "mustard_binasarisha9",
        "mung_bari_mung6_kharif1",
        "aman_br11",
    ),
    "wheat": (
        "wheat_bari_gom33",
        "mung_bari_mung6_kharif1",
        "aman_br11",
    ),
}
EXPECTED_VALUES = {
    "baseline": (0.0, 42.833333333333336, 0.026837637909406836),
    "mung": (0.0, 38.5, 0.0236496721130529),
    "wheat": (0.0, 40.333333333333336, 0.02375791980539704),
}


def load_artifact() -> dict:
    return json.loads(ARTIFACT.read_text(encoding="utf-8"))


def _raw_climate(
    temperature_years: tuple[int, ...] = (1991, 1992),
    rain_years: tuple[int, ...] = (1991, 1992),
) -> dict:
    """Small deterministic raw-climate fixture for period-selection tests."""
    base = {
        1991: {
            "temperature_distance_c": 10.0,
            "t2m_median_c": 20.0,
            "temperature_within_optimum": False,
            "temperature_within_tolerance": True,
            "longest_dry_run_days": 5,
            "growing_days": 10,
            "rain_total_mm": 100.0,
            "heavy_rain_days": 1,
            "rain_valid_days": 10,
        },
        1992: {
            "temperature_distance_c": 0.0,
            "t2m_median_c": 22.0,
            "temperature_within_optimum": True,
            "temperature_within_tolerance": True,
            "longest_dry_run_days": 50,
            "growing_days": 10,
            "rain_total_mm": 500.0,
            "heavy_rain_days": 5,
            "rain_valid_days": 10,
        },
        1993: {
            "temperature_distance_c": 20.0,
            "t2m_median_c": 25.0,
            "temperature_within_optimum": False,
            "temperature_within_tolerance": True,
            "longest_dry_run_days": 90,
            "growing_days": 10,
            "rain_total_mm": 900.0,
            "heavy_rain_days": 9,
            "rain_valid_days": 10,
        },
    }
    years = sorted(set(temperature_years) | set(rain_years))
    crops = []
    for position, crop_id in enumerate(("syn_a", "syn_b", "syn_c"), start=1):
        crops.append(
            {
                "crop_id": crop_id,
                "position": position,
                "seasons": len(years),
                "season_records": {
                    str(year): copy.deepcopy(base[year]) for year in years
                },
                "temperature_seasons": list(temperature_years),
                "rain_seasons": list(rain_years),
                "temperature_range": {
                    "optimum": {"min": 15.0, "max": 25.0},
                    "tolerance": {"min": 5.0, "max": 35.0},
                },
                "temperature_provenance": {
                    "source": "test://fixture",
                    "eco_port_code": "test",
                    "scientific_name": "Test crop",
                },
                "status": "ok",
            }
        )

    def schedule() -> dict:
        return {
            "status": "ok",
            "crops": copy.deepcopy(crops),
            "temperature_complete_seasons": list(temperature_years),
            "rain_complete_seasons": list(rain_years),
        }

    return {
        "per_schedule": {
            "min_realization": schedule(),
            "max_realization": schedule(),
        },
        "views": {
            "temperature": {"status": "ok", "reason": None},
            "rain": {"status": "ok", "reason": None},
        },
    }


class FeaturedComparisonTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.payload = load_artifact()

    def test_three_selected_sequences_resolve(self):
        examples = {example["key"]: example for example in self.payload["examples"]}
        self.assertEqual(set(examples), set(EXPECTED))
        for key, crop_ids in EXPECTED.items():
            example = examples[key]
            self.assertEqual(tuple(example["crop_ids"]), crop_ids)
            self.assertEqual(len(example["crops"]), 3)
            self.assertEqual(example["status"], "conditional")
            self.assertTrue(example["branch_id"])
            self.assertEqual(
                [crop["position"] for crop in example["crops"]],
                [1, 2, 3],
            )
            self.assertEqual(
                [crop["crop_id"] for crop in example["crops"]],
                list(crop_ids),
            )
            self.assertEqual(
                set(example["completion"]["completion_days"]),
                {"min", "max"},
            )
            for schedule_name in ("min_realization", "max_realization"):
                schedule = example["completion"][schedule_name]
                self.assertTrue(
                    {"p1", "h1", "p2", "h2", "p3", "h3", "completion_days"}
                    <= set(schedule)
                )

    def test_artifact_weather_values_ties_and_consistency(self):
        examples = {item["key"]: item for item in self.payload["examples"]}
        for key, expected in EXPECTED_VALUES.items():
            for view, value in zip(featured.VIEWS, expected):
                observed = examples[key]["weather_views"][view]
                self.assertEqual(observed["status"], "ok")
                self.assertAlmostEqual(observed["value"], value, places=12)
                self.assertEqual(
                    observed["value"],
                    max(observed["schedule_values"].values()),
                )
                self.assertEqual(
                    observed["common_seasons_count"],
                    len(observed["common_seasons"]),
                )
                self.assertEqual(observed["common_seasons_count"], 34)
                for schedule in ("min_realization", "max_realization"):
                    per_crop = observed["per_schedule"][schedule]["per_crop"]
                    self.assertEqual(len(per_crop), 3)
                    for crop in per_crop:
                        self.assertIsNotNone(crop["seasons"])
                        self.assertIsNotNone(crop["temperature_seasons"])
                        self.assertIsNotNone(crop["rain_seasons"])

        temperature = [
            examples[key]["weather_views"]["closest_temperature_match"]["value"]
            for key in EXPECTED
        ]
        self.assertEqual(temperature, [0.0, 0.0, 0.0])
        for view_name in featured.VIEWS:
            values = [
                examples[key]["weather_views"][view_name]["value"]
                for key in EXPECTED
            ]
            for key in EXPECTED:
                view = examples[key]["weather_views"][view_name]
                self.assertEqual(view["is_tie"], values.count(view["value"]) > 1)
                self.assertEqual(view["tie_count"], values.count(view["value"]))
        for key in EXPECTED:
            view = examples[key]["weather_views"]["closest_temperature_match"]
            self.assertTrue(view["is_tie"])
            self.assertEqual(view["tie_count"], 3)

    def test_common_periods_are_independent_and_use_exact_values(self):
        raw_a = _raw_climate(temperature_years=(1991,), rain_years=(1991, 1992))
        raw_b = _raw_climate(temperature_years=(1992,), rain_years=(1991, 1992))
        periods = featured._common_periods(
            {
                "a": {"metrics": {"climate": raw_a}},
                "b": {"metrics": {"climate": raw_b}},
            }
        )
        self.assertFalse(periods["closest_temperature_match"]["available"])
        self.assertEqual(periods["closest_temperature_match"]["seasons"], [])
        self.assertIn(
            "NO_COMMON_SEASONS",
            periods["closest_temperature_match"]["reason"],
        )
        self.assertTrue(periods["least_dry_spell_exposure"]["available"])
        self.assertEqual(
            periods["least_dry_spell_exposure"]["seasons"],
            [1991, 1992],
        )

        overlapping = featured._common_periods(
            {
                "a": {
                    "metrics": {
                        "climate": _raw_climate(
                            temperature_years=(1991, 1992),
                            rain_years=(1991, 1992),
                        )
                    }
                },
                "b": {
                    "metrics": {
                        "climate": _raw_climate(
                            temperature_years=(1992,),
                            rain_years=(1992, 1993),
                        )
                    }
                },
            }
        )
        self.assertTrue(overlapping["closest_temperature_match"]["available"])
        self.assertEqual(
            overlapping["closest_temperature_match"]["seasons"],
            [1992],
        )
        self.assertTrue(overlapping["least_dry_spell_exposure"]["available"])
        self.assertEqual(
            overlapping["least_dry_spell_exposure"]["seasons"],
            [1992],
        )

        unavailable = featured._weather_view(
            raw_a,
            "closest_temperature_match",
            periods["closest_temperature_match"]["seasons"],
            periods["closest_temperature_match"]["reason"],
        )
        self.assertEqual(unavailable["status"], "unavailable")
        self.assertIsNone(unavailable["value"])
        self.assertIsNone(unavailable["schedule_values"]["min_realization"])
        self.assertEqual(unavailable["common_seasons"], [])

        rain = featured._weather_view(
            raw_a,
            "least_dry_spell_exposure",
            periods["least_dry_spell_exposure"]["seasons"],
            None,
        )
        self.assertEqual(rain["status"], "ok")
        self.assertAlmostEqual(rain["value"], 27.5, places=12)
        self.assertEqual(
            rain["per_schedule"]["min_realization"]["per_crop"][0]["dry_spell"][
                "median_longest_run_days"
            ],
            27.5,
        )
        self.assertEqual(rain["common_seasons"], [1991, 1992])

        both_years = featured._weather_view(
            _raw_climate(),
            "least_dry_spell_exposure",
            [1991, 1992],
            None,
        )
        one_year = featured._weather_view(
            _raw_climate(),
            "least_dry_spell_exposure",
            [1991],
            None,
        )
        self.assertNotEqual(both_years["value"], one_year["value"])
        self.assertAlmostEqual(one_year["value"], 5.0, places=12)
        self.assertEqual(one_year["schedule_values"], {
            "min_realization": 5.0,
            "max_realization": 5.0,
        })
        self.assertEqual(one_year["common_seasons"], [1991])
        self.assertEqual(
            one_year["per_schedule"]["max_realization"]["per_crop"][0]["dry_spell"][
                "median_longest_run_days"
            ],
            5.0,
        )

        text = featured._what_nasa_shows(
            {
                "closest_temperature_match": unavailable,
                "least_dry_spell_exposure": rain,
                "least_heavy_rain_exposure": featured._weather_view(
                    _raw_climate(), "least_heavy_rain_exposure", [1991, 1992], None
                ),
            }
        )
        self.assertIn("Unavailable", text["temperature"])
        self.assertIn("27.5", text["dry_spell"])

    def test_unavailable_view_controls_are_disabled(self):
        availability = {
            "closest_temperature_match": {
                "available": False,
                "reason": "NO_COMMON_SEASONS: no shared T2M years.",
            },
            "least_dry_spell_exposure": {"available": True, "reason": None},
            "least_heavy_rain_exposure": {"available": True, "reason": None},
        }
        controls = {item["id"]: item for item in featured._comparison_controls(availability)}
        self.assertFalse(controls["closest_temperature_match"]["enabled"])
        self.assertIn("NO_COMMON_SEASONS", controls["closest_temperature_match"]["reason"])
        self.assertTrue(controls["least_dry_spell_exposure"]["enabled"])
        self.assertTrue(controls["least_heavy_rain_exposure"]["enabled"])
        self.assertFalse(controls["lowest_total_cost"]["enabled"])

    def test_unavailable_cache_raises_without_network(self):
        with tempfile.TemporaryDirectory() as cache_dir:
            with self.assertRaises(RuntimeError) as raised:
                featured.build_featured_comparison(
                    cache_dir=cache_dir,
                    now=NOW,
                )
        self.assertIn("cache", str(raised.exception).lower())

    def test_interactive_api_is_not_limited_to_featured_examples(self):
        profiles = load_crop_profiles(DATA)
        initial = explore(
            {
                "district_id": "rajshahi",
                "start_date": "2026-11-06",
                "first_crop_id": None,
                "water_access": "unknown",
                "preference": "fastest_completion",
            },
            profiles=profiles,
            config=CONFIG,
            now=NOW,
        )
        self.assertEqual(initial["branches"], [])
        self.assertEqual(len(initial["crop_options"]), 8)

        selected = explore(
            {
                "district_id": "rajshahi",
                "start_date": "2026-11-07",
                "first_crop_id": "mustard_binasarisha9",
                "water_access": "rainfed",
                "preference": "more_crop_diversity",
            },
            profiles=profiles,
            config=CONFIG,
            now=NOW,
        )
        self.assertEqual(selected["request"]["start_date"], "2026-11-07")
        self.assertEqual(selected["request"]["water_access"], "rainfed")
        self.assertEqual(selected["request"]["preference"], "more_crop_diversity")
        self.assertGreater(len(selected["branches"]), 3)
        self.assertEqual(
            len(selected["branches"]),
            selected["branch_summary"]["conditional_count"],
        )
        self.assertTrue(all(len(branch["crops"]) == 3 for branch in selected["branches"]))

    def test_missing_evidence_is_not_zero_or_pass(self):
        for example in self.payload["examples"]:
            self.assertEqual(example["status"], "conditional")
            self.assertEqual(
                example["prerequisites"]["economics"]["status"],
                "unavailable",
            )
            self.assertEqual(
                example["prerequisites"]["irrigation"]["ranking_status"],
                "unranked",
            )
            self.assertIsNone(example["prerequisites"]["irrigation"]["total"])
            self.assertEqual(
                example["prerequisites"]["equipment"]["status"],
                "unavailable",
            )
            self.assertTrue(
                "unknown" in example["prerequisites"]["preparation"]
            )
            for transition in example["transitions"]:
                self.assertIsNone(transition["waiting_range"])
                self.assertIsNone(transition["total_interval_range_days"])
                self.assertFalse(transition["preparation_known"])
        counts = self.payload["exploratory_scope"]["first_crop_counts"]
        self.assertEqual(counts["mustard_binasarisha9"]["candidate_count"], 0)
        self.assertEqual(counts["mustard_binasarisha9"]["conditional_count"], 54)
        self.assertEqual(counts["wheat_bari_gom33"]["candidate_count"], 0)
        self.assertEqual(counts["wheat_bari_gom33"]["conditional_count"], 48)

    def test_sources_assumptions_controls_and_provenance(self):
        self.assertTrue(self.payload["no_overall_winner"])
        self.assertFalse(self.payload["repeatable_rotation_checked"])
        self.assertEqual(self.payload["data_mode"], "offline_api_cache")
        self.assertFalse(self.payload["offline_fixture"])
        self.assertEqual(
            self.payload["environment"]["observation_start"],
            "1991-01-01",
        )
        self.assertEqual(
            self.payload["environment"]["observation_end"],
            "2025-12-31",
        )
        self.assertTrue(self.payload["environment"]["retrieved_at"])
        self.assertIn(
            self.payload["environment"]["cache"]["status"],
            {"fresh", "stale", "uncached"},
        )
        self.assertEqual(
            self.payload["temperature_source"]["status"],
            "data mirror, not independent agronomic validation",
        )
        self.assertIn(
            "OpenCLIM/ecocrop",
            self.payload["temperature_source"]["url"],
        )
        self.assertTrue(
            self.payload["coverage_unit_check"]["temperature_and_rain_independent"]
        )
        self.assertTrue(
            self.payload["coverage_unit_check"]["common_periods_computed_independently"]
        )
        for example in self.payload["examples"]:
            self.assertEqual(example["unit_validation"]["T2M"]["status"], "ok")
            self.assertEqual(
                example["unit_validation"]["PRECTOTCORR"]["status"],
                "ok",
            )
            self.assertEqual(
                example["weather_views"]["least_dry_spell_exposure"]["view_status"]["status"],
                "ok",
            )
        for view, data in self.payload["common_seasons_by_view"].items():
            self.assertEqual(data["count"], len(data["years"]))
            self.assertEqual(data["count"], 34)
            self.assertEqual(data["years"][0], 1991)
            self.assertEqual(data["years"][-1], 2024)
            self.assertIn(view, featured.VIEWS)
            self.assertEqual(data["status"], "ok")

        controls = {item["id"]: item for item in self.payload["comparison_controls"]}
        for view in featured.VIEWS:
            self.assertTrue(controls[view]["enabled"])
        for control in (
            "lowest_total_cost",
            "highest_net_return",
            "lowest_upfront_cash",
            "least_irrigation_dependence",
        ):
            self.assertFalse(controls[control]["enabled"])
            self.assertTrue(controls[control]["reason"])

        examples = {item["key"]: item for item in self.payload["examples"]}
        self.assertTrue(
            any(
                "banglajol.info" in source["url"]
                for source in examples["baseline"]["sources"]
            )
        )
        self.assertTrue(
            any(
                "apps.barc.gov.bd" in source["url"]
                for source in examples["mung"]["sources"]
            )
        )
        self.assertTrue(
            any(
                "apps.barc.gov.bd" in source["url"]
                for source in examples["wheat"]["sources"]
            )
        )
        self.assertIn("Kushtia", examples["wheat"]["documentation_status"])
        self.assertIn(
            "local applicability is unverified",
            examples["wheat"]["why_explore"],
        )
        self.assertNotIn("substitution", examples["wheat"]["why_explore"].lower())
        for example in self.payload["examples"]:
            self.assertTrue(example["sources"])
            self.assertTrue(all(source["url"].startswith("https://") for source in example["sources"]))
            self.assertTrue(example["does_not_establish"])
        self.assertTrue(self.payload["assumptions"])
        self.assertIn(
            "No overall weighted score",
            " ".join(self.payload["assumptions"]),
        )
        self.assertIn(
            "Third-to-first crop compatibility is not checked",
            " ".join(self.payload["limitations"]),
        )

    def test_artifact_scope_is_exploratory_not_a_winner(self):
        self.assertTrue(self.payload["exploratory_scope"]["description"])
        self.assertEqual(self.payload["exploratory_scope"]["featured_count"], 3)
        self.assertEqual(
            self.payload["exploratory_scope"]["first_crop_counts"]["mustard_binasarisha9"]["conditional_count"],
            54,
        )
        for example in self.payload["examples"]:
            self.assertIn("not summed", example["what_nasa_shows"]["rainfall"].lower())
            self.assertIn("not overall", example["does_not_establish"].lower())

    @unittest.skipUnless(
        os.environ.get("FEATURED_POWER_INTEGRATION") == "1",
        "set FEATURED_POWER_INTEGRATION=1 to run the real-cache integration check",
    )
    def test_real_cache_generation_matches_artifact(self):
        engine = featured.build_featured_comparison(now=NOW)
        engine_examples = {item["key"]: item for item in engine["examples"]}
        artifact_examples = {item["key"]: item for item in self.payload["examples"]}
        self.assertEqual(
            self.payload["common_seasons_by_view"],
            engine["common_seasons_by_view"],
        )
        for key in EXPECTED:
            artifact = artifact_examples[key]
            engine_item = engine_examples[key]
            self.assertEqual(artifact["branch_id"], engine_item["branch_id"])
            self.assertEqual(artifact["initial_wait_days"], engine_item["initial_wait_days"])
            self.assertEqual(artifact["completion"], engine_item["completion"])
            for view in featured.VIEWS:
                self.assertEqual(
                    artifact["weather_views"][view]["value"],
                    engine_item["weather_views"][view]["value"],
                )
                self.assertEqual(
                    artifact["weather_views"][view]["schedule_values"],
                    engine_item["weather_views"][view]["schedule_values"],
                )
                self.assertEqual(
                    artifact["weather_views"][view]["common_seasons_count"],
                    engine_item["weather_views"][view]["common_seasons_count"],
                )


if __name__ == "__main__":
    unittest.main()
