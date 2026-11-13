# E8 W1 revision - corner-extreme completion range

Replaced decision A with corner extremes in `calculate_completion_time`:
`min = third_harvest.earliest - first_planting.latest` (fastest realization);
`max = third_harvest.latest - first_planting.earliest` (slowest realization).
Returns `min_realization` / `max_realization` (first-planting and third-harvest dates), `range_basis="corner_extremes"`, and keeps `ranking_value_days=max`. `min <= max` now holds for every valid branch; `COMPLETION_RANGE_INVALID` remains only as a negative/reversed fallback, and reversed ISO ranges remain unavailable.

Added `enumerate_completion_range(branch)` full enumeration with `enumeration_used=True`; it matches the corner range on synthetic cases. Added tests for min<=max across all 420 real branches, the 57 previously inverted branches now valid (example `b_82899e8d6941` -> 655..682), 300 fixed-seed random realizations (no fallback needed), enumeration fallback, and the old reversed-date unavailable case. Updated W5 real ranking: fastest completion now ranks 420/420 conditional, 0 unranked, candidate 0, overlap note retained.

Negative-corner addendum: first planting `2027-01-01..2027-12-31`, third harvest `2027-06-01..2027-07-01` -> both `calculate_completion_time` and `enumerate_completion_range` return `status="unavailable"`, `completion_days=None`, `ranking_value_days=None`, `COMPLETION_RANGE_INVALID`; enumeration keeps `enumeration_used=true`. The calculate guard-removal mutation fails the test. `enumerate_completion_range` now rejects any negative or min>max enumerated result instead of returning `ok`.

Full suite: `python -X utf8 -m unittest discover -s tests -v`
```text
Ran 271 tests in 1.420s

OK
```
Focused `test_branch_metrics.py`: `Ran 46 tests in 0.285s`, `OK`. E6 smoke (`2026-11-06`, max 365): 420 branches, 0 candidate / 420 conditional, 15 exclusions all `WINDOW_GEOGRAPHY_UNKNOWN`; unchanged. Test count 264 -> 271 (+7).

No E6/E7/W2-W5 behavior changed beyond completion counts. This addendum changed `src/branch_metrics.py`, `tests/test_branch_metrics.py`, and this report. No commits.
