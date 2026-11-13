# E8 preflight guard - local POWER CSVs

Added `tests/test_local_power_data.py` and live fixture `tests/fixtures/power_daily_drift_20260901_20260903.json` (test-only; no production/Data changes). The guard loads both CSVs by header and checks dates, row lengths, coverage, overlap, A-only rows, common variables, and the PRECIP relation.

Structural checks PASS: A 13,445 rows 1990-01-01..2026-10-23 (1991-2026 present), B 9,790 rows 2000-01-01..2026-10-20; overlap 9,790, A-only 3,655, no duplicate dates or bad lengths; A-only 1991-1999 PRECIP rows 3,287.

Known drift PASS: mismatches for T2M/QV2M/GWETTOP and A=24xB PRECIP are exactly 2026-09-01..30; any mismatch outside that set, extra day, missing day, or new common-variable mismatch fails. PRECIP has 6,175 nonzero pairs.

Live fixture PASS: real POWER API v2.10.3 for 2026-09-01..03; A matches T2M/T2M_MAX/T2M_MIN/QV2M/GWETTOP exactly, A PREC/24 matches API PREC, and B is stale on those dates.

Full suite: `python -X utf8 -m unittest discover -s tests -q`
```text
Ran 225 tests in 1.214s

OK
```
E6 smoke (`2026-11-06`, max 365): 420 branches, 0 candidate / 420 conditional, 15 exclusions (`WINDOW_GEOGRAPHY_UNKNOWN`); unchanged.

Fixture provenance: `power_daily_rajshahi_20250101_20250103.json` is live POWER API v2.10.3 (PREC 0.0); `power_daily_synthetic_missing.json` is synthetic (PREC 0/1.5); the new drift fixture is live API v2.10.3 (PREC 28.04/29.67/9.16). No 1990 CSV PREC values were copied; no E7 fixture uses 1990 values.

No commits.
