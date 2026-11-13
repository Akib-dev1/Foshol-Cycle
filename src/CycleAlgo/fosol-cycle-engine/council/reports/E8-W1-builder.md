# E8 W1 - completion-time metric

Delivered `src/branch_metrics.py` with `calculate_completion_time(branch)` using decision A: `min = third_harvest.earliest - first_planting.earliest`, `max = third_harvest.latest - first_planting.latest`, and `ranking_value_days=max` (latest completion). It returns the completion range, earliest/latest completion dates, both source ranges, `basis="third_harvest_minus_first_planting"`, reasons, missing evidence, and a `range_overlap_note` disclosing that overlapping branch ranges are not a definitive timing winner. No annualization.

Validation: malformed branch shape (not exactly 3 crops/2 transitions, non-dict branch/crops) -> `unavailable`, `completion_days=None`, `reason="INVALID_BRANCH_SHAPE"`, no crash. Missing/invalid first planting or third harvest ranges -> unavailable/null with `missing_evidence`. Reversed/invalid completion ranges and `max < min` -> unavailable, never silently swapped. Valid output is JSON-serializable and has no crop-specific branches.

Tests: `tests/test_branch_metrics.py`, 7 synthetic-branch tests with `Spec §12.1`/`§14.4` docstrings: known ranges, single-date ranges, missing/invalid ranges, malformed shape, max<min, JSON, no crop-ID branches.

Full suite: `python -X utf8 -m unittest discover -s tests -v`
```text
Ran 232 tests in 2.049s

OK
```
Focused W1: `Ran 7 tests in 0.001s`, `OK`. Test count 225 -> 232 (+7).

E6 smoke (`2026-11-06`, max 365): 420 branches, 0 candidate / 420 conditional, 15 exclusions all `WINDOW_GEOGRAPHY_UNKNOWN`; unchanged.

No commits; only `src/branch_metrics.py`, `tests/test_branch_metrics.py`, and this report.
