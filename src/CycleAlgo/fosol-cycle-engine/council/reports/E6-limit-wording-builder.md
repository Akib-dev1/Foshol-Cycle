# E6 limit wording fix - product cutoff basis

Defect: §10.4. `_limit_error` stated the wait/limit but not the limit basis; a product cutoff could read as a scientific or biological maximum.

Failing test before fix (`test_limit_error_states_product_basis`):
```text
AssertionError: 'product relevance cutoff' not found in "The next documented window starts 2027-01-01 (10 days after the reference date), which exceeds this explorer's maximum waiting gap of 5 days."
Ran 1 test in 0.002s
FAILED (failures=1)
```

Fix: `_limit_error` now appends: "The limit is a product relevance cutoff, not a scientifically safe maximum and not a biological impossibility; longer fallow is not claimed impossible." Existing next-window/date/wait/limit facts unchanged.

Full suite: `python -X utf8 -m unittest discover -s tests -v`
```text
Ran 188 tests in 1.258s

OK
```
Focused E6: `test_timeline` 20, `test_rotation` 8, `test_branch_expander` 24 = 52, all OK. Test count 187 -> 188 (+1 wording test).

Smoke (`2026-11-06`, max 365): 420 branches, 0 candidate / 420 conditional, 15 exclusions all `WINDOW_GEOGRAPHY_UNKNOWN`; unchanged. Low-limit smoke now reports the new basis wording on `FUTURE_WINDOW_EXCEEDS_LIMIT`.

No behavior change; no commits. This task changed only `src/branch_expander.py`, `tests/test_branch_expander.py`, and this report.
