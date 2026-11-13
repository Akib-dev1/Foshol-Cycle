# E6 fix 1 - next-season window roll
Defect: §10.3/§10.5. A next-year crop window was terminal `OUTSIDE_SUPPORTED_WINDOW`. Only `src/branch_expander.py` and `tests/test_branch_expander.py` changed; rotation, timeline, soil/water, prep, duration untouched.
Failing test before fix (`test_next_season_windows_roll_forward_within_limit`):
```text
AssertionError: [] is not true
Ran 1 test in 0.034s
FAILED (failures=1)
```
Fix: `_next_season_start` rolls E4 `details.preferred_start` by one year. `_resolve_window` and `_roll_root_window` resolve that start through E4; E4 `next_window_start` is still checked first. Roll only when `max_waiting_days` is set and reference-to-start wait is within it. Rolled options become `caution` / `FUTURE_WINDOW_WITHIN_LIMIT`; `max_waiting_days=None` does not roll.
Boundary addendum: exact tests assert Aman 246 days in / 245 out; `mustard->mung->boro` 230 in / 229 out; `max_waiting_days=None` gives Aman first-crop count 0.
Focused E6: `test_timeline.py` 18, `test_rotation.py` 7, `test_branch_expander.py` 16 = 41 tests, all OK.
Full suite: `python -X utf8 -m unittest discover -s tests -v`
```text
Ran 177 tests in 0.824s

OK
```
OLD -> NEW (`2026-11-06`, max 365):
- total: 295 -> 420. Aman root +62; existing roots boro +13, lentil +7, maize +13, mustard +8, potato +8, wheat +14.
- status: 0 candidate / 295 conditional -> 0 candidate / 420 conditional.
- exclusions: 56 -> 15. Removed 46 `OUTSIDE_SUPPORTED_WINDOW` (p1 1, p2 3, p3 42); geography 10 -> 15 (p3 7 -> 12). 56 - 46 + 5 = 15.
- first crops OLD: boro 42, lentil 55, maize 42, mustard 54, potato 54, wheat 48.
- first crops NEW: aman 62, boro 55, lentil 62, maize 55, mustard 62, potato 62, wheat 62.
- boro: any 86 -> 158; pos1 42 -> 55, pos2 19 -> 49, pos3 25 -> 54.
- second crops OLD -> NEW: aman 24->56, boro 19->49, lentil 48->56, maize 42->56, mung 24->35, mustard 48->56, potato 48->56, wheat 42->56.
Explanation: +63 existing-root branches are extra third crops unlocked by rolled windows. Boro/mung second paths have 7 third completions each because a third-position mung remains geography-excluded; mung second is reachable only from 5 roots. All 15 remaining exclusions are `WINDOW_GEOGRAPHY_UNKNOWN`. No commits. Test-only boundary extension; no source behavior change.
