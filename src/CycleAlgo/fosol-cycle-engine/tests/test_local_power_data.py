"""Cross-source guard for the two local POWER daily CSVs (v1.md §15)."""

import csv
import datetime as dt
import json
import math
import unittest
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parents[2] / "Data"
FILE_A = DATA_DIR / "POWER_Point_Daily_19900101_20261023_024d38N_088d60E_LST.csv"
FILE_B = DATA_DIR / "NASA_RAJ_DATA_2000_2026.csv"
FIXTURE_DRIFT = (
    Path(__file__).resolve().parent
    / "fixtures"
    / "power_daily_drift_20260901_20260903.json"
)
FILL_VALUES = frozenset({-999.0, -9999.0})
TOLERANCE = 1e-9


def _load(path: Path):
    lines = path.read_text(encoding="utf-8-sig").splitlines()
    header_end = lines.index("-END HEADER-")
    reader = csv.reader(lines[header_end + 1 :])
    header = next(reader)
    rows = [row for row in reader if row]
    bad_lengths = [index for index, row in enumerate(rows, 1) if len(row) != len(header)]
    records = {}
    for row in rows:
        year = int(row[header.index("YEAR")])
        doy = int(row[header.index("DOY")])
        date = dt.datetime.strptime(f"{year}-{doy:03d}", "%Y-%j").date()
        records[date] = {
            name: float(row[index])
            for index, name in enumerate(header)
            if name not in ("YEAR", "DOY")
        }
    return header, rows, records, bad_lengths


def _valid(value: float) -> bool:
    return math.isfinite(value) and value not in FILL_VALUES


class LocalPowerCsvGuardTests(unittest.TestCase):
    def test_local_power_csvs_are_consistent(self) -> None:
        """Spec §15 | Bug it catches: local CSV unit/column drift"""
        header_a, rows_a, a, bad_a = _load(FILE_A)
        header_b, rows_b, b, bad_b = _load(FILE_B)
        a_dates, b_dates = set(a), set(b)

        self.assertEqual(bad_a, [])
        self.assertEqual(bad_b, [])
        self.assertEqual(len(rows_a), len(a_dates))
        self.assertEqual(len(rows_b), len(b_dates))
        self.assertEqual(len(rows_a), 13445)
        self.assertEqual(len(rows_b), 9790)
        self.assertEqual(min(a_dates), dt.date(1990, 1, 1))
        self.assertEqual(max(a_dates), dt.date(2026, 10, 23))
        self.assertEqual(min(b_dates), dt.date(2000, 1, 1))
        self.assertEqual(max(b_dates), dt.date(2026, 10, 20))
        self.assertTrue(all(year in {d.year for d in a_dates} for year in range(1991, 2027)))
        self.assertTrue(all(year in {d.year for d in b_dates} for year in range(2000, 2027)))

        overlap = a_dates & b_dates
        a_only = a_dates - b_dates
        self.assertEqual(len(overlap), 9790)
        self.assertEqual(len(a_only), 3655)
        self.assertEqual(b_dates - a_dates, set())

        common = sorted((set(header_a) & set(header_b)) - {"YEAR", "DOY", "PRECTOTCORR"})
        drift_dates = {
            dt.date(2026, 9, 1) + dt.timedelta(days=offset)
            for offset in range(30)
        }
        known_drift_variables = {"T2M", "QV2M", "GWETTOP"}
        failures = []
        for variable in common:
            mismatches = [
                (date, a[date][variable], b[date][variable])
                for date in sorted(overlap)
                if _valid(a[date][variable])
                and _valid(b[date][variable])
                and abs(a[date][variable] - b[date][variable]) > TOLERANCE
            ]
            mismatch_dates = {date for date, _, _ in mismatches}
            if variable in known_drift_variables:
                if mismatch_dates != drift_dates:
                    failures.append(
                        (
                            variable,
                            len(mismatches),
                            sorted(mismatch_dates ^ drift_dates)[:3],
                        )
                    )
            elif mismatches:
                failures.append((variable, len(mismatches), mismatches[0]))

        pairs = [
            (date, a[date]["PRECTOTCORR"], b[date]["PRECTOTCORR"])
            for date in sorted(overlap)
            if _valid(a[date]["PRECTOTCORR"])
            and _valid(b[date]["PRECTOTCORR"])
            and b[date]["PRECTOTCORR"] != 0
        ]
        self.assertGreaterEqual(len(pairs), 6000)
        bad_precip = [
            (date, value_a, value_b)
            for date, value_a, value_b in pairs
            if abs(value_a - 24.0 * value_b) > TOLERANCE
        ]
        bad_precip_dates = {date for date, _, _ in bad_precip}
        if bad_precip_dates != drift_dates:
            failures.append(
                (
                    "PRECTOTCORR",
                    len(bad_precip),
                    sorted(bad_precip_dates ^ drift_dates)[:3],
                )
            )

        fixture = json.loads(FIXTURE_DRIFT.read_text(encoding="utf-8"))
        fixture_header = fixture["header"]
        fixture_parameters = fixture["properties"]["parameter"]
        self.assertEqual(fixture_header["start"], "20260901")
        self.assertEqual(fixture_header["end"], "20260903")
        self.assertEqual(fixture_header["api"]["version"], "v2.10.3")
        self.assertIn("MERRA2", fixture_header["sources"])
        self.assertEqual(
            set(fixture_parameters),
            {"T2M", "T2M_MAX", "T2M_MIN", "QV2M", "GWETTOP", "PRECTOTCORR"},
        )
        for variable, values in fixture_parameters.items():
            for key, api_value in values.items():
                date = dt.datetime.strptime(key, "%Y%m%d").date()
                self.assertIn(date, a_dates)
                if variable == "PRECTOTCORR":
                    self.assertLessEqual(
                        abs(a[date][variable] / 24.0 - api_value), TOLERANCE
                    )
                else:
                    self.assertLessEqual(
                        abs(a[date][variable] - api_value), TOLERANCE
                    )
                if variable not in b[date]:
                    continue
                if variable == "PRECTOTCORR":
                    self.assertGreater(
                        abs(b[date][variable] - api_value * 24.0), TOLERANCE
                    )
                else:
                    self.assertGreater(
                        abs(b[date][variable] - api_value), TOLERANCE
                    )

        a_only_precip = [
            date
            for date in sorted(a_only)
            if 1991 <= date.year <= 1999
            and _valid(a[date]["PRECTOTCORR"])
        ]
        self.assertGreater(len(a_only_precip), 0)
        self.assertTrue(all(date in a_dates for date in a_only_precip))
        self.assertTrue(all(date not in b_dates for date in a_only_precip))
        self.assertTrue(all(1991 <= date.year <= 1999 for date in a_only_precip))

        self.assertEqual(failures, [])


if __name__ == "__main__":
    unittest.main()
