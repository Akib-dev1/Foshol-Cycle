# E8 realization revision - actual fastest/slowest schedules

Replaced widest-span completion with actual realized schedules. `realize_completion(branch, mode)` reports P1,H1,P2,H2,P3,H3: `fastest` uses latest P1, min durations, and earliest feasible prep/window dates; `slowest` uses earliest P1, max durations, and the **latest feasible** prep/window planting (up to the window/support end). Prep-unknown branches use crop-2/3 window ranges earliest/latest with min/max durations. Prep-known branches use prep + transition-window/clamp logic; infeasible corners fall back to `enumerate_completion_range`.

`calculate_completion_time` now uses the two realization completions, `range_basis="realized_corners"`, and both full realization date sets. `COMPLETION_RANGE_INVALID` remains only a fallback for invalid/infeasible corners. Example `b_82899e8d6941`: 655..682 days; fastest P1 2027-07-24, H3 2029-05-09; slowest P1 2027-07-10, H3 2029-05-22.

Tests added: independent manual tightness across all 420 real prep-unknown branches; the prep-known synthetic slowest is now 99 (latest feasible window), and a clamped synthetic branch gives real 60..99 versus widest-span 60..129; 300 sampled realizations per selected branches with sampled min/max equal to realized corners; prep-known infeasible-corner enumeration fallback. W5 fastest now ranks 420/420 conditional, 0 unranked, candidate 0, overlap note retained.

Full suite: `python -X utf8 -m unittest discover -s tests -v`
```text
Ran 274 tests in 1.734s

OK
```
Focused `test_branch_metrics.py`: `Ran 49 tests in 0.393s`, `OK`. E6 smoke (`2026-11-06`, max 365): 420 branches, 0 candidate / 420 conditional, 15 exclusions all `WINDOW_GEOGRAPHY_UNKNOWN`; unchanged. Test count 271 -> 274 (+3).

No E6/E7/W2-W5 behavior changed. No commits; only `src/branch_metrics.py`, `tests/test_branch_metrics.py`, and this report.
