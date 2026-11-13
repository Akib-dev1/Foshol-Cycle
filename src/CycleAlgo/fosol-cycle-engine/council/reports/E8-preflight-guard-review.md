# E8 preflight guard review - local POWER CSVs
Verdict: PASS. Bugs: none.
Full suite: `python -X utf8 -m unittest discover -s tests -v`
```text
Ran 225 tests in 1.229s
OK
```
Focused guard: `Ran 1 test in 0.201s`, OK.

Guard verified:
- T2M/QV2M/GWETTOP mismatch dates are exactly 2026-09-01..30 (30 each); a drift end of 2026-08-31 fails.
- PRECIP A = 24 x B on 6,175 nonzero pairs; bad dates are exactly 2026-09-01..30. Changing 24 to 1 fails.
- Live fixture is POWER API v2.10.3 for 2026-09-01..03; A/24 = API PREC (28.04/29.67/9.16), A matches T2M/T2M_MAX/T2M_MIN/QV2M/GWETTOP, and B is stale on the common variables. Disabling/emptying the fixture fails.
- 1991-1999 A-only PRECIP rows: 3,287; A-only/range checks remain.

| mutation | failing test | hash OK |
|---|---|---|
| drift end -> 2026-08-31 | `test_local_power_csvs_are_consistent` | yes |
| PRECIP 24x -> 1x | `test_local_power_csvs_are_consistent` | yes |
| live fixture disabled | `test_local_power_csvs_are_consistent` (KeyError) | yes |

Restored SHA-256 `A6C1DDAF...`; no mutation remains.

Sources: `tests/fixtures/power_daily_drift_20260901_20260903.json` (live POWER API v2.10.3), local A `POWER_Point_Daily_19900101_20261023_024d38N_088d60E_LST.csv`, local B `NASA_RAJ_DATA_2000_2026.csv`, and the E7 mustard audit. A/24 equals API; raw A is 24x. No 1990 CSV PREC values were copied into the fixture/expected values.

E6 smoke (`2026-11-06`, max 365): 420 branches, 0 candidate / 420 conditional, 15 exclusions.
No permanent edits; no commits.
