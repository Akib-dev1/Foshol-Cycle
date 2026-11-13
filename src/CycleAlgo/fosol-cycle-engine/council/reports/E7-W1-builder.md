# E7 W1 - seasonal replay mapping and coverage

Delivered `src/seasonal_replay.py` with one primary function `map_schedule_to_seasons`. It maps the E6 union span (`period_basis="union_span"`) by month/day to season start years 1991–2025 (configurable), using a next-year end when the end month-day precedes the start. It excludes only when the mapped end is after `last_complete_data_date` or coverage fails; no hardcoded 2026. Leap Feb 29 endpoints adjust to Feb 28 in non-leap years with `leap_day_adjusted` and notes. Coverage counts finite numeric days only; missing dates, `None`, `NaN`, `-999`, and `-9999` are invalid. `stats_min_90` includes >=90%; `warnings_100` includes only 100%; invalid rule raises `ValueError`. Returns all seasons, evaluated seasons, excluded seasons with reason/valid/total days, analysis period, and notes; JSON-serializable. No warning thresholds, statistics, or output labels added.

Tests: `tests/test_seasonal_replay.py`, 13 tests with `Spec §9.2 | Bug it catches: ...` docstrings. Covers 35 default seasons, cross-year mapping, the 2025 season ending 2026-03-22 with `last_complete_data_date=2026-10-23` (included) and earlier (excluded), leap-day adjustment, 90%/100% boundaries, missing/None/fill invalidity, invalid rule, JSON, and no crop-ID branches.

Boundary addendum: `test_season_end_equal_last_complete_is_included` kills `>` -> `>=`; `test_end_only_feb_29_adjusts_in_non_leap_year` kills a start-only leap adjustment. Both mutations failed the targeted test; source SHA-256 `869C...598` restored.

Full suite: `python -X utf8 -m unittest discover -s tests -v`
```text
Ran 201 tests in 1.031s

OK
```
E7 focused: `Ran 13 tests in 0.005s`, `OK`. Test count 188 -> 201 (+13).

E6 smoke unchanged: 420 branches, 0 candidate / 420 conditional, 15 exclusions all `WINDOW_GEOGRAPHY_UNKNOWN`. No E6 source changed.

No commits; this extension changed only `tests/test_seasonal_replay.py` and this report. `src/seasonal_replay.py` unchanged.
