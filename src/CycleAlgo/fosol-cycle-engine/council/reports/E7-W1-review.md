# E7 W1 review - map_schedule_to_seasons
Verdict: PASS. Bugs: none. Both previous test gaps are closed; source is unchanged.
Full suite: `python -X utf8 -m unittest discover -s tests -v`
```text
Ran 201 tests in 1.085s
OK
```
Focused W1: `Ran 13 tests`, OK.

| mutation | failing test | hash OK |
|---|---|---|
| 90% `>=` -> `>` | `test_stats_min_90_boundary_includes_exact_and_excludes_below` | yes |
| 100% equality weakened to `total-1` | `test_warnings_100_boundary_includes_exact_and_excludes_99` | yes |
| `last_complete` `>` -> `>=` | `test_season_end_equal_last_complete_is_included` | yes |
| cross-year end-year rule | `test_cross_year_mapping_uses_next_year_end` | yes |
| leap-day adjustment removed | `test_leap_day_endpoint_adjusts_only_in_non_leap_years` | yes |
| end-only Feb 29 adjustment disabled | `test_end_only_feb_29_adjusts_in_non_leap_year` | yes |

Restored SHA-256 `869C3E84...`; no mutation remains.
Boundary recheck: last_complete `>` -> `>=` fails with `AssertionError: 0 != 1`; end-only Feb 29 disabled fails with `ValueError: day is out of range for month`. Both new tests now kill their mutation.
Decisions verified: no hardcoded 2026; 2025 season ending 2026 included when complete; missing/None/NaN/-999/-9999 invalid; JSON serializable; no crop-ID branches; union span labeled; stats >=90 and warnings 100.
E6 smoke: 420 branches, 0 candidate / 420 conditional, 15 exclusions all `WINDOW_GEOGRAPHY_UNKNOWN`; no E6 file changed.
No permanent edits; no commits.
