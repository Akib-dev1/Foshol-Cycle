"""Tests for the E9 explore envelope (v1.md §14.3-14.4)."""

import copy
import datetime as dt
import json
import sys
import unittest
from pathlib import Path

from src.crop_profiles import load_crop_profiles
from src.explore import explore
from src.request_validation import RequestValidationError

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from contract_check import validate_response  # noqa: E402

REAL_CSV = (
    Path(__file__).resolve().parents[2]
    / "Data"
    / "fosol_cycle_rajshahi_crop_dataset.csv"
)
NOW = dt.datetime(2026, 11, 7, 12, 0, tzinfo=dt.timezone.utc)
CONFIG = {"max_initial_wait_days": 180, "max_waiting_days": None}
SMAP_AVAILABLE = {
    "product": "SPL4SMGP.008",
    "product_version": "008",
    "provider": "NASA SMAP via AppEEARS",
    "spatial_resolution": "9 km EASE-Grid 2.0",
    "temporal_resolution": "3-hourly",
    "observations": [
        {
            "timestamp": "2026-11-01T00:00:00Z",
            "sm_surface": 0.2,
            "sm_rootzone": 0.25,
        }
    ],
    "observation_start": "2026-11-01T00:00:00Z",
    "observation_end": "2026-11-01T00:00:00Z",
    "retrieved_at": "2026-11-07T00:00:00+00:00",
    "warnings": [],
}
SMAP_UNAVAILABLE = {
    **SMAP_AVAILABLE,
    "status": "unavailable",
    "observations": [],
    "warnings": [
        {
            "code": "SMAP_CONTEXT_UNAVAILABLE",
            "message": "SMAP context fetch failed.",
        }
    ],
}
POWER_ENVIRONMENT = {
    "observations": {},
    "observation_start": "2020-01-01",
    "observation_end": "2022-12-31",
    "provider": "NASA POWER",
    "product": "NASA POWER Daily Point",
    "product_version": "v2.10.3",
    "fill_value": -999.0,
    "retrieved_at": "2026-11-07T00:00:00+00:00",
}


def _payload(first_crop_id=None, preference="fastest_completion", district="rajshahi"):
    return {
        "district_id": district,
        "start_date": "2026-11-06",
        "first_crop_id": first_crop_id,
        "water_access": "unknown",
        "preference": preference,
    }


def _synthetic_profiles():
    base = {
        "name_en": "Synthetic crop",
        "name_bn": "Synthetic crop",
        "reference_variety": "synthetic",
        "establishment_method": "Direct seeded",
        "preferred_start_mmdd": "05-05",
        "preferred_end_mmdd": "05-10",
        "supported_late_end_mmdd": None,
        "window_crosses_year": False,
        "source_planting_window": "synthetic://window",
        "source_local_calendar": "synthetic://calendar",
        "window_basis": "synthetic",
        "planting_window_type": "SYNTHETIC",
        "date_precision": "DAY",
        "hard_deadline_validated": False,
        "variety_duration_min_days": 1,
        "variety_duration_max_days": 2,
        "seedling_age_min_days": None,
        "seedling_age_max_days": None,
        "duration_precision": "synthetic",
        "decision_duration_source": "synthetic://duration",
    }
    profiles = {}
    for suffix, family, legume in (
        ("a", "Poaceae", False),
        ("b", "Fabaceae", True),
        ("c", "Brassicaceae", False),
    ):
        profile = copy.deepcopy(base)
        profile.update(
            {
                "crop_id": f"syn_{suffix}",
                "family": family,
                "is_legume_n_fixing": legume,
            }
        )
        profiles[f"syn_{suffix}"] = profile
    return profiles


def _source_ids(value, found=None):
    found = set() if found is None else found
    if isinstance(value, dict):
        for key, item in value.items():
            if key == "source_ids" and isinstance(item, list):
                found.update(item)
            elif key == "sources" and isinstance(item, list):
                for source in item:
                    if isinstance(source, dict):
                        found.add(source.get("source_id"))
            else:
                _source_ids(item, found)
    elif isinstance(value, list):
        for item in value:
            _source_ids(item, found)
    return {item for item in found if isinstance(item, str) and item}


def _has_empty_string(value) -> bool:
    if isinstance(value, str):
        return value == ""
    if isinstance(value, dict):
        return any(_has_empty_string(item) for item in value.values())
    if isinstance(value, list):
        return any(_has_empty_string(item) for item in value)
    return False


class ExploreTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.profiles = load_crop_profiles(REAL_CSV)

    def _run(
        self,
        first_crop_id=None,
        preference="fastest_completion",
        district="rajshahi",
        **kwargs,
    ):
        payload = _payload(first_crop_id, preference, district)
        return explore(
            payload,
            profiles=self.profiles,
            config=CONFIG,
            now=NOW,
            **kwargs,
        )

    def test_envelope_has_contract_keys(self) -> None:
        """Spec §14.3 | Bug it catches: required envelope fields are missing."""
        result = self._run()
        required = {
            "schema_version",
            "generated_at",
            "request",
            "status",
            "district",
            "assumptions",
            "data_sources",
            "crop_options",
            "branches",
            "ranking",
            "warnings",
            "branch_summary",
            "environment_context",
            "missing_evidence",
        }
        self.assertTrue(required <= set(result))
        self.assertEqual(result["schema_version"], "1")
        self.assertEqual(result["generated_at"], "2026-11-07T12:00:00+00:00")
        self.assertEqual(result["request"]["first_crop_id"], None)
        self.assertEqual(result["request"]["max_initial_wait_days"], 180)
        self.assertIsNone(result["request"]["max_waiting_days"])
        self.assertTrue(
            any(
                "180" in item["message"]
                and "product relevance" in item["message"]
                for item in result["assumptions"]
            )
        )

    def test_demo_status_and_summary(self) -> None:
        """Spec §14.3/§17.17 | Bug it catches: current demo claims ok or loses the summary."""
        result = self._run()
        self.assertEqual(result["status"], "partial")
        self.assertEqual(
            result["branch_summary"]["candidate_count"], 0
        )
        self.assertEqual(
            result["branch_summary"]["conditional_count"], 295
        )
        self.assertEqual(result["branch_summary"]["excluded_count"], 56)
        self.assertEqual(
            result["branch_summary"]["message"],
            "No candidate branches - 295 conditional branches available; "
            "select a first crop to view them.",
        )

    def test_initial_response_has_no_branches_but_full_summary(self) -> None:
        """Spec §14.3 | Bug it catches: branches are returned before first-crop selection."""
        result = self._run()
        self.assertEqual(result["branches"], [])
        self.assertEqual(result["branch_summary"]["conditional_count"], 295)
        self.assertEqual(result["ranking"]["groups"]["candidate"]["count"], 0)
        self.assertEqual(result["ranking"]["groups"]["conditional"]["count"], 0)
        self.assertTrue(result["ranking"]["no_winner"])

    def test_selected_first_crop_returns_rooted_branches(self) -> None:
        """Spec §14.3 | Bug it catches: selected first crop returns other roots or no branches."""
        result = self._run("boro_brri_dhan28")
        self.assertEqual(result["status"], "partial")
        self.assertEqual(len(result["branches"]), 42)
        self.assertEqual(result["branch_summary"]["conditional_count"], 42)
        for branch in result["branches"]:
            self.assertEqual(branch["crops"][0]["crop_id"], "boro_brri_dhan28")

    def test_crop_options_cover_all_eight_with_aman_mung_unsupported(self) -> None:
        """Spec §14.3 | Bug it catches: first-crop options are missing or unsupported roots look shown."""
        result = self._run()
        options = {option["crop_id"]: option for option in result["crop_options"]}
        self.assertEqual(len(options), 8)
        self.assertEqual(options["aman_br11"]["status"], "unsupported")
        self.assertEqual(options["mung_bari_mung6_kharif1"]["status"], "unsupported")
        self.assertFalse(options["aman_br11"]["shown"])
        self.assertFalse(options["mung_bari_mung6_kharif1"]["shown"])
        self.assertTrue(options["boro_brri_dhan28"]["shown"])
        self.assertEqual(
            options["boro_brri_dhan28"]["checks"]["climate"]["code"],
            "CLIMATE_EXPOSURE_DEFERRED",
        )
        self.assertEqual(
            options["boro_brri_dhan28"]["checks"]["climate"]["missing_evidence"],
            ["current_season_climate_exposure"],
        )
        self.assertEqual(
            options["boro_brri_dhan28"]["checks"]["climate"]["source_ids"], []
        )

    def test_initial_wait_days_are_surfaced(self) -> None:
        """Spec §14.3 | Bug it catches: initial wait is hidden or lost for future/unsupported crops."""
        result = self._run()
        options = {option["crop_id"]: option for option in result["crop_options"]}
        self.assertEqual(options["aman_br11"]["initial_wait_days"], 246)
        self.assertEqual(options["mung_bari_mung6_kharif1"]["initial_wait_days"], 129)
        self.assertEqual(options["boro_brri_dhan28"]["initial_wait_days"], 49)
        selected = self._run("boro_brri_dhan28")
        self.assertEqual(selected["branches"][0]["initial_wait_days"], 49)

    def test_initial_wait_boundary_is_exact(self) -> None:
        """Spec §14.3 | Bug it catches: 180-day initial-wait boundary is off by one or uses < instead of <=."""
        profiles = _synthetic_profiles()
        for limit, expected_status, expected_code, expected_branches in (
            (179, "no_supported_options", "FUTURE_WINDOW_EXCEEDS_LIMIT", 0),
            (180, "partial", "FUTURE_WINDOW_WITHIN_LIMIT", 9),
            (181, "partial", "FUTURE_WINDOW_WITHIN_LIMIT", 9),
        ):
            with self.subTest(limit=limit):
                result = explore(
                    _payload("syn_a"),
                    profiles=profiles,
                    config={
                        "max_initial_wait_days": limit,
                        "max_waiting_days": None,
                    },
                    now=NOW,
                )
                options = {
                    option["crop_id"]: option
                    for option in result["crop_options"]
                }
                self.assertEqual(result["status"], expected_status)
                self.assertEqual(
                    options["syn_a"]["checks"]["calendar"]["code"],
                    expected_code,
                )
                self.assertEqual(
                    options["syn_a"]["initial_wait_days"], 180
                )
                self.assertEqual(len(result["branches"]), expected_branches)
                if expected_branches:
                    self.assertTrue(
                        all(
                            branch["status"] == "conditional"
                            for branch in result["branches"]
                        )
                    )

    def test_window_only_gap_is_separate_from_waiting(self) -> None:
        """Spec §14.3/§9 | Bug it catches: window-only gap is labeled waiting or hidden."""
        result = self._run("boro_brri_dhan28")
        transition = result["branches"][0]["transitions"][0]
        self.assertIsNone(transition["waiting_range"])
        self.assertIsInstance(transition["harvest_to_next_window_days"], dict)
        self.assertTrue(transition["window_only_gap"])

    def test_smap_context_does_not_change_status_or_ranking(self) -> None:
        """Spec §14.3 | Bug it catches: SMAP context affects status/checks/ranking."""
        without = self._run("boro_brri_dhan28")
        with_context = self._run("boro_brri_dhan28", smap_context=SMAP_AVAILABLE)
        self.assertEqual(with_context["status"], without["status"])
        self.assertEqual(
            json.dumps(with_context["ranking"], sort_keys=True),
            json.dumps(without["ranking"], sort_keys=True),
        )
        context = with_context["environment_context"]
        self.assertEqual(context["status"], "available")
        self.assertEqual(
            context["label"], "Context only - no effect on status or ranking"
        )
        self.assertEqual(context["product"], "SPL4SMGP.008")
        self.assertEqual(context["provider"], "NASA SMAP via AppEEARS")
        self.assertEqual(context["resolution"], "9 km EASE-Grid 2.0")
        self.assertEqual(context["temporal_resolution"], "3-hourly")

    def test_smap_unavailable_is_warning_not_zero(self) -> None:
        """Spec §14.3 | Bug it catches: missing/expired SMAP becomes zero or changes status."""
        without = self._run("boro_brri_dhan28")
        result = self._run("boro_brri_dhan28", smap_context=SMAP_UNAVAILABLE)
        context = result["environment_context"]
        self.assertEqual(result["status"], without["status"])
        self.assertEqual(context["status"], "unavailable")
        self.assertEqual(context["observations"], [])
        self.assertTrue(context["warnings"])
        self.assertEqual(
            json.dumps(result["ranking"], sort_keys=True),
            json.dumps(without["ranking"], sort_keys=True),
        )

    def test_unknowns_are_null_and_json_is_strict(self) -> None:
        """Spec §14.3/§14.4 | Bug it catches: NaN, Infinity, or empty strings leak."""
        result = self._run()
        encoded = json.dumps(result, allow_nan=False)
        self.assertNotIn("NaN", encoded)
        self.assertFalse(_has_empty_string(result))

    def test_unsupported_district_is_not_fabricated(self) -> None:
        """Spec §14.3 | Bug it catches: unsupported district inherits Rajshahi results."""
        result = self._run(district="dhaka")
        self.assertEqual(result["status"], "unsupported_district")
        self.assertEqual(result["branches"], [])
        self.assertEqual(result["crop_options"], [])
        self.assertFalse(result["district"]["supported"])

    def test_ranking_groups_reference_returned_branch_ids(self) -> None:
        """Spec §14.3/§14.4 | Bug it catches: ranking references unknown or blocked branches."""
        result = self._run("boro_brri_dhan28")
        branch_ids = {branch["branch_id"] for branch in result["branches"]}
        groups = result["ranking"]["groups"]
        self.assertEqual(groups["candidate"]["count"], 0)
        self.assertEqual(groups["conditional"]["count"], 42)
        for group in ("candidate", "conditional"):
            for entry in groups[group]["ranked"] + groups[group]["unranked"]:
                self.assertIn(entry["branch_id"], branch_ids)
                self.assertIn("initial_wait_days", entry)
        self.assertFalse(result["ranking"]["no_winner"])

    def test_no_candidate_message_is_explicit(self) -> None:
        """Spec §14.3/§13 | Bug it catches: no-candidate state is left to the frontend."""
        initial = self._run(None)
        self.assertTrue(initial["branch_summary"]["no_candidate_branches"])
        self.assertEqual(
            initial["branch_summary"]["message"],
            "No candidate branches - 295 conditional branches available; "
            "select a first crop to view them.",
        )
        selected = self._run("boro_brri_dhan28")
        self.assertTrue(selected["branch_summary"]["no_candidate_branches"])
        self.assertEqual(
            selected["branch_summary"]["message"],
            "No candidate branches - 42 conditional branches shown.",
        )
        empty = self._run("aman_br11")
        self.assertEqual(empty["status"], "no_supported_options")
        self.assertEqual(
            empty["branch_summary"]["message"],
            "No candidate or conditional branches available.",
        )

    def test_single_conditional_branch_uses_singular_message(self) -> None:
        """Spec §14.3 | Bug it catches: one branch is labeled 'branches'."""
        result = explore(
            _payload("boro_brri_dhan28"),
            profiles=self.profiles,
            config={**CONFIG, "max_branches": 1},
            now=NOW,
        )
        self.assertEqual(
            result["branch_summary"]["message"],
            "No candidate branches - 1 conditional branch shown.",
        )

    def test_repeated_request_is_deterministic(self) -> None:
        """Spec §14.4 | Bug it catches: identical requests produce different envelopes."""
        first = self._run("boro_brri_dhan28")
        second = self._run("boro_brri_dhan28")
        self.assertEqual(json.dumps(first, sort_keys=True), json.dumps(second, sort_keys=True))

    def test_diversity_ranking_is_descending_and_separate(self) -> None:
        """Spec §13 | Bug it catches: diversity preference uses the wrong metric or direction."""
        result = self._run("boro_brri_dhan28", "more_crop_diversity")
        self.assertEqual(result["ranking"]["metric"], "distinct_family_count")
        self.assertEqual(result["ranking"]["direction"], "descending")
        self.assertEqual(result["ranking"]["groups"]["candidate"]["count"], 0)
        self.assertEqual(len(result["ranking"]["groups"]["conditional"]["ranked"]), 42)
        entry = result["ranking"]["groups"]["conditional"]["ranked"][0]
        self.assertIn("legume_present", entry)
        self.assertIn("families", entry)

    def test_economics_preference_has_no_winner(self) -> None:
        """Spec §13/§17.15 | Bug it catches: unavailable economics produces a ranked winner."""
        result = self._run("boro_brri_dhan28", "lowest_total_cost")
        self.assertTrue(result["ranking"]["no_winner"])
        self.assertEqual(result["ranking"]["groups"]["conditional"]["ranked"], [])
        self.assertEqual(len(result["ranking"]["groups"]["conditional"]["unranked"]), 42)

    def test_branch_metrics_are_attached(self) -> None:
        """Spec §14.4 | Bug it catches: branch metrics are missing or collapsed."""
        branch = self._run("boro_brri_dhan28")["branches"][0]
        metrics = branch["metrics"]
        self.assertEqual(
            set(metrics),
            {"completion", "resources", "economics", "diversity", "climate"},
        )
        self.assertEqual(
            set(metrics["resources"]),
            {"cash_cost", "irrigation", "labor", "equipment"},
        )
        self.assertEqual(metrics["economics"]["status"], "unavailable")
        self.assertIn("distinct_family_count", metrics["diversity"])
        self.assertEqual(metrics["climate"]["status"], "unavailable")

    def test_branch_climate_check_is_deferred(self) -> None:
        """Spec §14.3/§6.2 | Bug it catches: branch crop nodes omit the deferred climate check."""
        branch = self._run("boro_brri_dhan28")["branches"][0]
        for crop in branch["crops"]:
            climate = crop["checks"]["climate"]
            self.assertEqual(climate["status"], "unknown")
            self.assertEqual(climate["code"], "CLIMATE_EXPOSURE_DEFERRED")
            self.assertEqual(
                climate["missing_evidence"],
                ["current_season_climate_exposure"],
            )
            self.assertEqual(climate["source_ids"], [])
        self.assertIn(
            "current_season_climate_exposure", branch["missing_evidence"]
        )

    def test_economics_values_are_null_and_checker_rejects_zero(self) -> None:
        """Spec §14.4/§17.15 | Bug it catches: unavailable economics is zero-filled."""
        result = self._run("boro_brri_dhan28")
        economics = result["branches"][0]["metrics"]["economics"]
        self.assertEqual(economics["status"], "unavailable")
        self.assertEqual(economics["scenarios"], [])
        for key in (
            "gross_revenue_bdt_per_ha",
            "production_cost_bdt_per_ha",
            "net_return_bdt_per_ha",
            "upfront_cash_bdt_per_ha",
        ):
            self.assertIsNone(economics[key]["value_bdt_per_ha"])
        self.assertIsNone(economics["price_evidence"]["price_value"])
        self.assertEqual(validate_response(result), [])
        zeroed = copy.deepcopy(result)
        zeroed["branches"][0]["metrics"]["economics"][
            "gross_revenue_bdt_per_ha"
        ]["value_bdt_per_ha"] = 0.0
        self.assertTrue(
            any("gross_revenue_bdt_per_ha" in error for error in validate_response(zeroed))
        )

    def test_outlook_is_unavailable_without_environment(self) -> None:
        """Spec §14.3/§9 | Bug it catches: outlook is fabricated without POWER input."""
        branch = self._run("boro_brri_dhan28")["branches"][0]
        self.assertEqual(branch["outlook"]["status"], "unavailable")
        self.assertEqual(branch["outlook"]["reason"], "POWER environment not supplied")
        self.assertEqual(branch["outlook"]["label"], "Seasonal outlook — based on historical conditions, not a weather forecast.")
        self.assertEqual(branch["outlook"]["indicators"], [])

    def test_outlook_uses_power_environment_when_supplied(self) -> None:
        """Spec §14.3/§9 | Bug it catches: supplied POWER is ignored by branch outlook."""
        result = explore(
            _payload("boro_brri_dhan28"),
            profiles=self.profiles,
            config={
                **CONFIG,
                "analysis_start_year": 2020,
                "analysis_end_year": 2021,
                "last_complete_data_date": "2022-12-31",
            },
            environment=POWER_ENVIRONMENT,
            now=NOW,
        )
        outlook = result["branches"][0]["outlook"]
        self.assertIn("per_crop", outlook)
        self.assertEqual(
            outlook["per_crop"][0]["sources"][0]["source_id"],
            "nasa_power_daily",
        )
        self.assertIn(
            "nasa_power_daily",
            {source["source_id"] for source in result["data_sources"]},
        )

    def test_trusted_evidence_threads_to_expansion_without_payload_input(self) -> None:
        """Spec §10/§14 | Bug it catches: server-side evidence is dropped or user payload evidence is trusted."""
        preparation = {
            crop_id: {
                "min_days": 7,
                "max_days": 10,
                "source_ids": ["test://preparation"],
            }
            for crop_id in self.profiles
        }
        soil = {
            "ph": {
                "min": 6.5,
                "max": 7.0,
                "source_ids": ["test://soil"],
            }
        }
        payload = _payload("lentil_binamasur9")
        payload["soil_evidence"] = {"ph": {"min": 0, "max": 0}}
        result = explore(
            payload,
            profiles=self.profiles,
            config={**CONFIG, "max_waiting_days": 365},
            soil_evidence=soil,
            preparation_lookup=preparation,
            duration_reference_verified=True,
            duration_reference_verified_crop_ids={"lentil_binamasur9"},
            now=NOW,
        )
        self.assertTrue(result["branches"])
        for crop in result["branches"][0]["crops"]:
            self.assertEqual(
                crop["duration"]["reference_verified"],
                crop["crop_id"] == "lentil_binamasur9",
            )
            self.assertEqual(crop["preparation_range"]["min_days"], 7)
        codes = {item["code"] for item in result["assumptions"]}
        self.assertIn("SOIL_EVIDENCE_SUPPLIED", codes)
        self.assertIn("PREPARATION_EVIDENCE_SUPPLIED", codes)
        self.assertIn("DURATION_REFERENCE_VERIFIED", codes)
        self.assertNotIn("soil_evidence", result["request"])

    def test_power_provider_failure_is_explicitly_unavailable(self) -> None:
        """Spec §9/§14.3 | Bug it catches: a failed POWER load becomes fabricated observations or a silent fallback."""
        result = explore(
            _payload("boro_brri_dhan28"),
            profiles=self.profiles,
            config=CONFIG,
            environment=None,
            environment_error="POWER provider unavailable",
            now=NOW,
        )
        warning = next(
            item
            for item in result["warnings"]
            if item["code"] == "POWER_UNAVAILABLE"
        )
        self.assertIn("POWER provider unavailable", warning["message"])
        self.assertEqual(
            result["branches"][0]["outlook"]["status"], "unavailable"
        )

    def test_environment_cache_metadata_and_stale_warning_are_exposed(self) -> None:
        """Spec §14.3/§9 | Bug it catches: stale POWER metadata is hidden from the caller."""
        environment = {
            **POWER_ENVIRONMENT,
            "cache": {"hit": True, "stale": True, "age_seconds": 900.0},
            "warnings": [
                {
                    "code": "STALE_CACHE",
                    "message": "POWER data came from a stale cache.",
                }
            ],
        }
        result = explore(
            _payload("boro_brri_dhan28"),
            profiles=self.profiles,
            config={
                **CONFIG,
                "analysis_start_year": 2020,
                "analysis_end_year": 2021,
                "last_complete_data_date": "2022-12-31",
            },
            environment=environment,
            now=NOW,
        )
        self.assertTrue(
            any(
                warning["code"] == "STALE_CACHE"
                for warning in result["warnings"]
            )
        )
        source = next(
            item
            for item in result["data_sources"]
            if item["source_id"] == "nasa_power_daily"
        )
        self.assertEqual(source["observation_start"], "2020-01-01")
        self.assertEqual(source["observation_end"], "2022-12-31")
        self.assertFalse(source["is_forecast"])
        self.assertTrue(source["cache"]["stale"])

    def test_data_sources_cover_every_referenced_source_id(self) -> None:
        """Spec §14.4 | Bug it catches: a referenced source ID is missing from data_sources."""
        result = self._run("boro_brri_dhan28")
        source_ids = _source_ids(result["crop_options"]) | _source_ids(result["branches"])
        catalog = {source["source_id"] for source in result["data_sources"]}
        self.assertIn("crop_profiles_rajshahi_v1", catalog)
        self.assertTrue(source_ids <= catalog)

    def test_invalid_request_is_rejected(self) -> None:
        """Spec §14.2 | Bug it catches: invalid request values are silently defaulted."""
        with self.assertRaises(RequestValidationError):
            explore(
                _payload("not_a_crop"),
                profiles=self.profiles,
                config=CONFIG,
                now=NOW,
            )
        with self.assertRaises(RequestValidationError):
            explore(
                _payload(preference="unknown_preference"),
                profiles=self.profiles,
                config=CONFIG,
                now=NOW,
            )


if __name__ == "__main__":
    unittest.main()
