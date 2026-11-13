"""Contract checks for the iteration-2 climate metric and ranking shapes."""

from __future__ import annotations

import copy
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from contract_check import validate_response  # noqa: E402

EXAMPLE = ROOT / "examples" / "example_response_climate.json"


class ClimateContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.payload = json.loads(EXAMPLE.read_text(encoding="utf-8"))

    def test_saved_climate_response_is_valid(self) -> None:
        self.assertEqual(validate_response(self.payload), [])

    def test_broken_branch_climate_metrics_fail(self) -> None:
        payload = copy.deepcopy(self.payload)
        payload["branches"][0]["metrics"]["climate"] = {
            "status": "ok",
            "per_schedule": "broken",
        }
        errors = validate_response(payload)
        self.assertTrue(any("metrics.climate" in error for error in errors))

    def test_broken_ranking_climate_metadata_fails(self) -> None:
        payload = copy.deepcopy(self.payload)
        payload["ranking"]["climate"] = {
            "status": "ok",
            "per_schedule": "broken",
        }
        errors = validate_response(payload)
        self.assertTrue(any("ranking.climate" in error for error in errors))

    def test_invalid_climate_numeric_bounds_fail(self) -> None:
        payload = copy.deepcopy(self.payload)
        entry = payload["ranking"]["groups"]["conditional"]["ranked"][0]
        entry["climate"]["per_schedule"]["max_realization"]["per_crop"][0][
            "heavy_rain"
        ]["frequency"] = 2
        errors = validate_response(payload)
        self.assertTrue(any("heavy_rain.frequency" in error for error in errors))

    def test_unavailable_climate_metrics_are_allowed(self) -> None:
        payload = copy.deepcopy(self.payload)
        payload["branches"][0]["metrics"]["climate"] = {
            "status": "unavailable",
            "reason": "POWER units unconfirmed.",
        }
        self.assertFalse(
            any("metrics.climate" in error for error in validate_response(payload))
        )


if __name__ == "__main__":
    unittest.main()
