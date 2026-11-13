# E7 W2 review - statistics + warning flags
Verdict: PASS. Bugs: none. Both previous 100% guard test gaps are closed; temperature `coverage.excluded_seasons` now exists.
Full suite: `python -X utf8 -m unittest discover -s tests -v`
```text
Ran 216 tests in 1.073s
OK
```
Focused W2: `Ran 15 tests`, OK.

| mutation | failing test | hash OK |
|---|---|---|
| IQR interpolation removed | `test_temperature_statistics_known_values_and_linear_iqr` | yes |
| precip season sum -> last value | `test_precipitation_statistics_per_season_totals_and_stats` | yes |
| 100% precip guard `!=` -> `< days-1` | `test_precipitation_skips_direct_incomplete_evaluated_season` | yes |
| 100% warning guard `!=` -> `< days-1` | `test_warning_skips_direct_incomplete_evaluated_season` | yes |
| warning default flag enabled | `test_disabled_warning_returns_disabled_without_x_y` | yes |
| X-count counts days | `test_enabled_heat_warning_counts_at_least_one_day_per_season` | yes |
| Y=0 mapping changed | `test_warning_y_zero_is_unavailable_not_zero_risk` | yes |

Restored SHA-256 `B0DD8A64...` / `1C4B83DC...`; no mutation remains.
Temperature coverage check: direct W1 `stats_min_90` result with an excluded season returns `coverage.excluded_seasons=1`.
Verified: pooled daily T2M >=90%; linear IQR/median/min/max; precip per-season totals in mm, sample=seasons; warnings default OFF, per-indicator text, X/Y + days_meeting, Y=0 unavailable, disabled no X/Y; exact em-dash label; JSON; no crop-ID branches.
E6 smoke: 420 branches, 0 candidate / 420 conditional, 15 exclusions all `WINDOW_GEOGRAPHY_UNKNOWN`; no E6/W1 source changed.
No permanent edits; no commits.
