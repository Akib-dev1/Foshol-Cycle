"""Tests for soil/land and water compatibility (v1.md §7, §8, §14.4)."""

import copy
import json
import unittest
from pathlib import Path

from src.crop_profiles import load_crop_profiles
from src.soil_water import (
    evaluate_soil_fit,
    evaluate_soil_water,
    evaluate_water_fit,
)

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
PH_EVIDENCE = {"min": 6.0, "max": 7.0, "source_ids": ["synthetic://soil_ph"]}
SYNTHETIC_SOURCE = "synthetic://soil_ph"


def _synthetic_profile(**overrides) -> dict:
    """A crop-profile-shaped dict; every value here is synthetic test data."""
    profile = {
        "crop_id": "synthetic",
        "ph_opt_min": 6.0,
        "ph_opt_max": 7.0,
        "ph_tol_min": 5.0,
        "ph_tol_max": 8.0,
        "salinity_ecocrop": "low (<4 dS/m)",
        "irrigation_guidance": "Synthetic test guidance only.",
        "source_ecocrop": "synthetic://ecocrop",
        "source_water": "synthetic://water",
        "source_local_calendar": "synthetic://local-calendar",
    }
    profile.update(overrides)
    profile["raw"] = {
        key: ("" if value is None else str(value))
        for key, value in profile.items()
        if key != "raw"
    }
    return profile


def _ph_evidence(low: float, high: float) -> dict:
    return {
        "ph": {"min": low, "max": high, "source_ids": [SYNTHETIC_SOURCE]}
    }


class RealProfileSoilTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.profiles = load_crop_profiles(REAL_CSV)
        cls.aman = cls.profiles["aman_br11"]

    def test_real_crops_without_local_soil_evidence_are_unknown_with_named_missing(
        self,
    ) -> None:
        """Spec §7 | Bug it catches: a missing district measurement becomes a pass."""
        named = {
            "ph": "district_soil_ph",
            "texture": "district_soil_texture",
            "drainage": "district_soil_drainage",
            "salinity": "district_soil_salinity",
        }
        for crop_id, profile in self.profiles.items():
            result = evaluate_soil_fit(profile)
            with self.subTest(crop_id=crop_id):
                self.assertEqual(result["status"], "unknown")
                for prop, missing_id in named.items():
                    self.assertEqual(result["checks"][prop]["status"], "unknown")
                    self.assertIn(missing_id, result["missing_evidence"])
                self.assertEqual(
                    result["checks"]["ph"]["code"], "SOIL_PH_EVIDENCE_MISSING"
                )

    def test_smap_moisture_is_context_only(self) -> None:
        """Spec §7 | Bug it catches: wet SMAP readings change the soil status."""
        wet = evaluate_soil_fit(
            self.aman,
            moisture_context={"sm_surface": 0.45, "sm_rootzone": 0.35},
        )
        dry = evaluate_soil_fit(
            self.aman,
            moisture_context={"sm_surface": 0.02, "sm_rootzone": 0.01},
        )
        self.assertEqual((wet["status"], wet["code"]), (dry["status"], dry["code"]))
        self.assertFalse(wet["moisture_context"]["used_for_status"])
        self.assertFalse(wet["moisture_context"]["threshold_validated"])
        self.assertEqual(wet["moisture_context"]["surface"], 0.45)
        self.assertEqual(wet["moisture_context"]["rootzone"], 0.35)
        self.assertEqual(dry["moisture_context"]["surface"], 0.02)

    def test_threshold_flag_requires_explicit_true(self) -> None:
        """Spec §7 | Bug it catches: an invalidated wetness threshold looks validated."""
        profile = copy.deepcopy(self.aman)
        profile["raw"]["surface_wetness_threshold_validated"] = "TRUE"
        validated = evaluate_soil_fit(profile, moisture_context={"sm_surface": 0.4})
        baseline = evaluate_soil_fit(self.aman)
        self.assertTrue(validated["moisture_context"]["threshold_validated"])
        self.assertEqual(baseline["moisture_context"]["threshold_validated"], False)
        self.assertEqual(validated["status"], baseline["status"])

    def test_texture_and_drainage_local_but_unvalidated_are_unknown(self) -> None:
        """Spec §7 | Bug it catches: EcoCrop text or a local value fakes a mapping."""
        profile = _synthetic_profile()
        texture = evaluate_soil_fit(
            profile, {"texture": {"value": "clay loam", "source_ids": ["synthetic://texture"]}}
        )
        drainage = evaluate_soil_fit(
            profile, {"drainage": {"value": "poor", "source_ids": ["synthetic://drainage"]}}
        )
        self.assertEqual(
            texture["checks"]["texture"]["code"], "SOIL_TEXTURE_MAPPING_UNVALIDATED"
        )
        self.assertEqual(
            drainage["checks"]["drainage"]["code"], "SOIL_DRAINAGE_MAPPING_UNVALIDATED"
        )
        no_local = evaluate_soil_fit(self.aman)
        self.assertEqual(
            no_local["checks"]["texture"]["code"], "SOIL_TEXTURE_EVIDENCE_MISSING"
        )
        self.assertEqual(
            no_local["checks"]["texture"]["details"]["ecocrop_guidance"], "wide"
        )

    def test_missing_soil_evidence_forms_are_unknown(self) -> None:
        """Spec §7 | Bug it catches: a null, empty, or malformed form crashes or passes."""
        forms = (
            None,
            {},
            {"ph": None},
            {"ph": {"min": None, "max": 7}},
            {"ph": {"min": "bad", "max": 7}},
            "not-a-dict",
        )
        for form in forms:
            result = evaluate_soil_fit(self.aman, form)
            with self.subTest(form=form):
                self.assertEqual(result["status"], "unknown")
                self.assertEqual(
                    result["checks"]["ph"]["code"], "SOIL_PH_EVIDENCE_MISSING"
                )


class SyntheticSoilTests(unittest.TestCase):
    def test_ph_inclusive_boundaries_and_inside_optimum_are_pass(self) -> None:
        """Spec §7 | Bug it catches: inclusive bounds fail or a source-less pH result is favourable."""
        profile = _synthetic_profile()
        for low, high in ((6.0, 7.0), (6.5, 6.5)):
            result = evaluate_soil_fit(profile, _ph_evidence(low, high))
            with self.subTest(low=low, high=high):
                self.assertEqual(result["checks"]["ph"]["status"], "pass")
                self.assertEqual(
                    result["checks"]["ph"]["code"], "SOIL_PH_WITHIN_OPTIMUM"
                )
                self.assertIn(
                    SYNTHETIC_SOURCE, result["checks"]["ph"]["source_ids"]
                )
        no_crop_source = evaluate_soil_fit(
            _synthetic_profile(source_ecocrop=None), _ph_evidence(6.0, 7.0)
        )
        self.assertEqual(
            no_crop_source["checks"]["ph"]["source_ids"], [SYNTHETIC_SOURCE]
        )
        no_local_source = evaluate_soil_fit(
            profile, {"ph": {"min": 6.0, "max": 7.0}}
        )
        self.assertEqual(no_local_source["status"], "unknown")
        self.assertEqual(
            no_local_source["checks"]["ph"]["code"],
            "SOIL_EVIDENCE_SOURCE_MISSING",
        )

    def test_ph_overlap_and_tolerance_caution(self) -> None:
        """Spec §7 | Bug it catches: a pH outside optimum or tolerance is passed."""
        profile = _synthetic_profile()
        cases = (
            (7.5, 8.5, "SOIL_PH_PARTIALLY_OUTSIDE_TOLERANCE"),
            (7.5, 8.0, "SOIL_PH_OUTSIDE_OPTIMUM_WITHIN_TOLERANCE"),
            (5.0, 5.5, "SOIL_PH_OUTSIDE_OPTIMUM_WITHIN_TOLERANCE"),
            (6.5, 7.5, "SOIL_PH_OVERLAPS_OPTIMUM"),
        )
        for low, high, code in cases:
            result = evaluate_soil_fit(profile, _ph_evidence(low, high))
            with self.subTest(low=low, high=high):
                self.assertEqual(result["checks"]["ph"]["status"], "caution")
                self.assertEqual(result["checks"]["ph"]["code"], code)

    def test_ph_wholly_outside_tolerance_is_unsupported(self) -> None:
        """Spec §7 | Bug it catches: a documented conflict becomes a caution or pass."""
        profile = _synthetic_profile()
        for low, high in ((4.0, 4.9), (8.1, 9.0)):
            result = evaluate_soil_fit(profile, _ph_evidence(low, high))
            with self.subTest(low=low, high=high):
                self.assertEqual(result["checks"]["ph"]["status"], "unsupported")
                self.assertEqual(
                    result["checks"]["ph"]["code"], "SOIL_PH_OUTSIDE_TOLERANCE"
                )

    def test_ph_invalid_range_and_missing_crop_rule(self) -> None:
        """Spec §7 | Bug it catches: invalid local pH or an unusable crop rule is evaluated."""
        for low, high in ((-0.5, 6.0), (8.0, 7.0), (6.0, 14.5)):
            inverted = evaluate_soil_fit(
                _synthetic_profile(), _ph_evidence(low, high)
            )
            with self.subTest(low=low, high=high):
                self.assertEqual(inverted["checks"]["ph"]["status"], "unknown")
                self.assertEqual(
                    inverted["checks"]["ph"]["code"],
                    "SOIL_PH_EVIDENCE_INVALID",
                )
        no_rule = _synthetic_profile(
            ph_opt_min=None, ph_opt_max=None, ph_tol_min=None, ph_tol_max=None
        )
        missing_rule = evaluate_soil_fit(no_rule, _ph_evidence(6.0, 7.0))
        self.assertEqual(
            missing_rule["checks"]["ph"]["code"], "SOIL_PH_CROP_RULE_MISSING"
        )
        bad_rule = _synthetic_profile(ph_tol_min=6.5, ph_tol_max=6.8)
        invalid_rule = evaluate_soil_fit(bad_rule, _ph_evidence(6.0, 7.0))
        self.assertEqual(
            invalid_rule["checks"]["ph"]["status"], "unknown"
        )
        self.assertEqual(
            invalid_rule["checks"]["ph"]["code"], "SOIL_PH_CROP_RULE_INVALID"
        )

    def test_salinity_comparisons(self) -> None:
        """Spec §7 | Bug it catches: a local salinity range is validated or compared wrongly."""
        profile = _synthetic_profile()

        def evidence(low, high, unit="dS/m", source=True):
            data = {"min": low, "max": high}
            if unit is not None:
                data["unit"] = unit
            if source:
                data["source_ids"] = ["synthetic://salinity"]
            return {"salinity": data}

        cases = (
            (2.0, 3.9, "pass", "SOIL_SALINITY_WITHIN_LOW_GUIDANCE"),
            (2.0, 4.0, "caution", "SOIL_SALINITY_AT_LOW_GUIDANCE"),
            (4.1, 5.0, "caution", "SOIL_SALINITY_ABOVE_LOW_GUIDANCE"),
            (3.0, 6.0, "caution", "SOIL_SALINITY_PARTIALLY_ABOVE_LOW_GUIDANCE"),
        )
        for low, high, status, code in cases:
            result = evaluate_soil_fit(profile, evidence(low, high))
            with self.subTest(low=low, high=high):
                self.assertEqual(result["checks"]["salinity"]["status"], status)
                self.assertEqual(result["checks"]["salinity"]["code"], code)

        invalid = (
            (-1.0, 3.0, "dS/m", "SOIL_SALINITY_EVIDENCE_INVALID"),
            (5.0, 2.0, "dS/m", "SOIL_SALINITY_EVIDENCE_INVALID"),
            (2.0, 3.0, None, "SOIL_SALINITY_UNIT_MISSING"),
            (2.0, 3.0, "ppt", "SOIL_SALINITY_UNIT_INVALID"),
        )
        for low, high, unit, code in invalid:
            result = evaluate_soil_fit(profile, evidence(low, high, unit))
            with self.subTest(low=low, high=high, unit=unit):
                self.assertEqual(result["checks"]["salinity"]["status"], "unknown")
                self.assertEqual(result["checks"]["salinity"]["code"], code)

        no_source = evaluate_soil_fit(profile, evidence(2.0, 3.0, source=False))
        self.assertEqual(
            no_source["checks"]["salinity"]["code"],
            "SOIL_EVIDENCE_SOURCE_MISSING",
        )
        unparsable = evaluate_soil_fit(
            _synthetic_profile(salinity_ecocrop="moderate"),
            evidence(2.0, 3.0),
        )
        self.assertEqual(
            unparsable["checks"]["salinity"]["code"],
            "SOIL_SALINITY_RULE_UNVALIDATED",
        )

    def test_soil_aggregate_precedence(self) -> None:
        """Spec §7 | Bug it catches: unknown or pass outranks a harder soil status."""
        profile = _synthetic_profile()
        unsupported = evaluate_soil_fit(profile, _ph_evidence(8.1, 9.0))
        caution = evaluate_soil_fit(profile, _ph_evidence(5.0, 5.5))
        passed = evaluate_soil_fit(profile, _ph_evidence(6.0, 7.0))
        self.assertEqual(unsupported["status"], "unsupported")
        self.assertEqual(caution["status"], "caution")
        self.assertEqual(passed["status"], "unknown")
        self.assertEqual(passed["checks"]["ph"]["status"], "pass")
        self.assertEqual(passed["checks"]["texture"]["status"], "unknown")


class WaterTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.profiles = load_crop_profiles(REAL_CSV)
        cls.aman = cls.profiles["aman_br11"]

    def test_real_crops_without_demand_are_unknown_even_with_irrigation(self) -> None:
        """Spec §8 | Bug it catches: missing demand becomes a favorable resource state."""
        for crop_id in ("mustard_binasarisha9", "lentil_binamasur9", "mung_bari_mung6_kharif1"):
            for access in ("unknown", "irrigation_available"):
                result = evaluate_water_fit(self.profiles[crop_id], access)
                with self.subTest(crop_id=crop_id, access=access):
                    self.assertEqual(result["status"], "unknown")
                    self.assertEqual(result["code"], "WATER_DEMAND_EVIDENCE_MISSING")
                    self.assertFalse(result["has_quantified_demand"])
                    self.assertTrue(
                        all(
                            value is None
                            for key, value in result["demand_evidence"].items()
                            if key.endswith("_mm")
                        )
                    )

    def test_water_unknown_access_requires_confirmation(self) -> None:
        """Spec §8 | Bug it catches: unknown access is treated as irrigation available."""
        result = evaluate_water_fit(self.aman)
        self.assertEqual(result["status"], "caution")
        self.assertEqual(result["code"], "IRRIGATION_CONFIRMATION_REQUIRED")
        self.assertIn("Irrigation confirmation required.", result["reason"])
        self.assertEqual(result["demand_evidence"]["fao_crop_water_need_min_mm"], 450.0)
        self.assertEqual(result["demand_evidence"]["fao_crop_water_need_max_mm"], 700.0)
        self.assertEqual(result["demand_evidence"]["local_phase_water_total_mm"], 631.0)

    def test_water_rainfed_is_caution_not_assumed(self) -> None:
        """Spec §8 | Bug it catches: rainfed access is assumed to meet crop demand."""
        result = evaluate_water_fit(self.aman, "rainfed")
        self.assertEqual(result["status"], "caution")
        self.assertEqual(result["code"], "RAINFED_GUIDANCE_REVIEW")
        self.assertIn("rainfall", result["reason"])
        self.assertNotEqual(result["status"], "pass")

    def test_water_irrigation_available_is_partial_confirmation(self) -> None:
        """Spec §8 | Bug it catches: irrigation access alone becomes a pass."""
        result = evaluate_water_fit(self.profiles["boro_brri_dhan28"], "irrigation_available")
        self.assertEqual(result["status"], "caution")
        self.assertEqual(result["code"], "IRRIGATION_PARTIAL_CONFIRMATION")
        for word in ("amount", "timing", "reliability", "cost"):
            self.assertIn(word, result["reason"])
        self.assertNotEqual(result["status"], "pass")

    def test_invalid_water_access_raises(self) -> None:
        """Spec §14.2 | Bug it catches: an invalid enum silently becomes a scenario."""
        for value in ("", "irrigated", "RAINFED", None, 1):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    evaluate_water_fit(self.aman, value)

    def test_environment_rainfall_does_not_change_water_status(self) -> None:
        """Spec §8 | Bug it catches: demand-minus-rainfall changes the outcome."""
        baseline = evaluate_water_fit(self.aman)
        with_rain = evaluate_water_fit(
            self.aman, environment={"rainfall_mm": 1200.0, "PRECTOTCORR": 12.0}
        )
        self.assertEqual(
            (baseline["status"], baseline["code"]),
            (with_rain["status"], with_rain["code"]),
        )
        self.assertFalse(with_rain["irrigation_demand_calculated"])
        self.assertFalse(with_rain["environment_used_for_status"])
        self.assertNotIn("irrigation_demand_mm", with_rain)
        json.dumps(with_rain, allow_nan=False)

    def test_local_phase_total_alone_counts_as_demand(self) -> None:
        """Spec §8 | Bug it catches: zero, negative, or missing demand evidence is misclassified."""
        profile = _synthetic_profile(
            fao_crop_water_need_min_mm=None,
            fao_crop_water_need_max_mm=None,
            local_phase_water_total_mm=500,
        )
        result = evaluate_water_fit(profile)
        self.assertTrue(result["has_quantified_demand"])
        self.assertEqual(result["status"], "caution")
        self.assertEqual(
            result["demand_evidence"]["local_phase_water_total_mm"], 500.0
        )
        zero = _synthetic_profile(
            fao_crop_water_need_min_mm=None,
            fao_crop_water_need_max_mm=None,
            local_phase_water_total_mm=0,
        )
        zero_result = evaluate_water_fit(zero)
        self.assertTrue(zero_result["has_quantified_demand"])
        self.assertEqual(zero_result["status"], "caution")
        demand_fields = (
            "fao_crop_water_need_min_mm",
            "fao_crop_water_need_max_mm",
            "local_phase_water_total_mm",
        )
        for field in demand_fields:
            overrides = {name: None for name in demand_fields}
            overrides[field] = -10
            negative = evaluate_water_fit(_synthetic_profile(**overrides))
            with self.subTest(field=field):
                self.assertEqual(negative["status"], "unknown")
                self.assertEqual(
                    negative["code"], "WATER_DEMAND_EVIDENCE_INVALID"
                )
                self.assertFalse(negative["has_quantified_demand"])
        empty = _synthetic_profile(
            fao_crop_water_need_min_mm=None,
            fao_crop_water_need_max_mm=None,
            local_phase_water_total_mm=None,
        )
        self.assertEqual(
            evaluate_water_fit(empty)["code"], "WATER_DEMAND_EVIDENCE_MISSING"
        )


class CombinedAndContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.profiles = load_crop_profiles(REAL_CSV)

    def test_combined_precedence_and_shape(self) -> None:
        """Spec §7-§8 | Bug it catches: combining checks changes the documented precedence."""
        profile = _synthetic_profile()
        unsupported = evaluate_soil_water(
            profile, "unknown", _ph_evidence(8.1, 9.0)
        )
        caution = evaluate_soil_water(
            profile, "unknown", _ph_evidence(5.0, 5.5)
        )
        missing = evaluate_soil_water(
            self.profiles["mustard_binasarisha9"], "unknown"
        )
        self.assertEqual(unsupported["status"], "unsupported")
        self.assertEqual(caution["status"], "caution")
        self.assertEqual(missing["status"], "unknown")
        self.assertEqual(set(unsupported["checks"]), {"soil", "water"})

    def test_outputs_are_json_serializable_and_no_crop_id_branch(self) -> None:
        """Spec §14.4 | Bug it catches: a non-JSON value or crop-specific branch ships."""
        soil = evaluate_soil_fit(
            self.profiles["aman_br11"],
            _ph_evidence(6.0, 7.0),
            {"sm_surface": 0.3},
        )
        water = evaluate_water_fit(self.profiles["aman_br11"], "rainfed")
        combined = evaluate_soil_water(
            self.profiles["aman_br11"], "irrigation_available", _ph_evidence(6.0, 7.0)
        )
        for result in (soil, water, combined):
            json.dumps(result, allow_nan=False)
        source = (SRC_DIR / "soil_water.py").read_text(encoding="utf-8")
        for crop_id in CROP_IDS:
            self.assertNotIn(crop_id, source)


if __name__ == "__main__":
    unittest.main()
