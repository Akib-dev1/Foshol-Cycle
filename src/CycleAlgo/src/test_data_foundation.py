"""Run: python -B -m unittest discover -s src -p 'test_*.py'"""

import csv
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from data_foundation import (
    DEFAULT_CROPS, boolean, build_foundation, check_mmdd, check_range, load_climate,
    load_crops, number,
)


class DataFoundationTests(unittest.TestCase):
    def test_repository_data_preserves_evidence_and_quarantines_rainfall(self):
        result = build_foundation()
        crops = result["crop_data"]["crops"]
        self.assertEqual(len(crops), 8)
        with DEFAULT_CROPS.open(encoding="utf-8-sig", newline="") as stream:
            originals = list(csv.DictReader(stream))
        for original in originals:
            research = crops[original["crop_id"]]["research"]
            self.assertEqual(set(research), set(original))
            self.assertEqual(research["source_variety"], original["source_variety"])
            self.assertIsNone(research["turnaround_days_min"])
        self.assertIsNone(crops["aman_br11"]["duration"]["reference_event"])
        self.assertEqual(crops["boro_brri_dhan28"]["duration"]["reference_event"], "NURSERY_SOWING")
        self.assertTrue(crops["lentil_binamasur9"]["research"]["is_legume_n_fixing"])
        self.assertTrue(crops["boro_brri_dhan28"]["planting_window"]["crosses_year"])
        self.assertEqual(crops["wheat_bari_gom33"]["duration"]["variety_days"], {"min": 108, "max": 112})
        climate = result["climate_data"]
        self.assertEqual(climate["metadata"]["precipitation_status"], "QUARANTINED_SOURCE")
        self.assertIsNone(climate["daily"]["2020-07-02"]["precipitation_mm"])
        self.assertEqual(climate["daily"]["2020-07-02"]["precipitation_source_value"], 259.68)
        self.assertIn("temperature_max_c", climate["daily"]["2020-07-02"])
        self.assertFalse(climate["metadata"]["years"]["2026"]["calendar_complete"])
        json.dumps(result, allow_nan=False)

    def test_invalid_values_are_not_defaults(self):
        for value in ("garbage", "nan", "inf"):
            with self.assertRaises(ValueError):
                number(value, "test")
        with self.assertRaises(ValueError):
            number("1.5", "test", integer=True)
        with self.assertRaises(ValueError):
            boolean("yes", "test")
        with self.assertRaises(ValueError):
            check_range(5, 3, "test")
        with self.assertRaises(ValueError):
            check_mmdd("02-30", "test")
        self.assertIsNone(number("", "test"))
        self.assertFalse(boolean("FALSE", "test"))
        check_mmdd("02-29", "test")

    def test_cli_export_and_overwrite_protection(self):
        script = Path(__file__).with_name("data_foundation.py")
        with tempfile.TemporaryDirectory() as folder:
            output = Path(folder) / "foundation.json"
            command = [sys.executable, "-B", str(script), "--output", str(output)]
            run = subprocess.run(command, capture_output=True, text=True, encoding="utf-8")
            self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
            artifact = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(artifact["schema_version"], "1.0")
            self.assertEqual(artifact["validation_report"], json.loads(run.stdout))
            original = output.read_bytes()
            repeated = subprocess.run(command, capture_output=True, text=True, encoding="utf-8")
            self.assertEqual(repeated.returncode, 1)
            self.assertEqual(json.loads(repeated.stdout)["status"], "INVALID")
            self.assertEqual(output.read_bytes(), original)

    def test_duplicate_crops_fail_without_overwriting(self):
        with DEFAULT_CROPS.open(encoding="utf-8-sig", newline="") as stream:
            reader = csv.DictReader(stream)
            fields, rows = reader.fieldnames, list(reader)
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "crops.csv"
            with path.open("w", encoding="utf-8", newline="") as stream:
                writer = csv.DictWriter(stream, fieldnames=fields)
                writer.writeheader()
                writer.writerows([rows[0], rows[0]])
            with self.assertRaisesRegex(ValueError, "duplicate crop_id"):
                load_crops(path, [])

    def test_climate_dates_missing_values_and_units(self):
        header = ("-BEGIN HEADER-\nLocation: latitude 24.3769 longitude 88.6031\n"
                  "Dates: in LST\nT2M Temperature (C)\nPRECTOTCORR Rainfall (mm/day)\n"
                  "-END HEADER-\nYEAR,DOY,T2M,PRECTOTCORR\n")
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "weather.csv"
            path.write_text(header + "2020,60,-999,2.5\n2020,62,25,0\n", encoding="utf-8")
            issues = []
            climate = load_climate(path, issues)
            self.assertIsNone(climate["daily"]["2020-02-29"]["temperature_mean_c"])
            self.assertEqual(climate["daily"]["2020-02-29"]["precipitation_mm"], 2.5)
            self.assertEqual(climate["metadata"]["missing_date_count"], 1)
            self.assertIsNone(climate["daily"]["2020-02-29"]["temperature_max_c"])
            for rows, error in [
                ("2021,366,25,0\n", "invalid YEAR/DOY"),
                ("2020,1,25,0\n2020,1,26,1\n", "duplicate date"),
                ("2020,1,25,-1\n", "negative value"),
            ]:
                path.write_text(header + rows, encoding="utf-8")
                with self.assertRaisesRegex(ValueError, error):
                    load_climate(path, [])
            path.write_text(header.replace("mm/day", "mm/hour") + "2020,1,25,0\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "unit"):
                load_climate(path, [])


if __name__ == "__main__":
    unittest.main()
