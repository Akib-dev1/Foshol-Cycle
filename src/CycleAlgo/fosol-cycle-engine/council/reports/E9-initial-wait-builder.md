# E9 initial-wait policy - separate from transitions
`expand_branches` now accepts `max_initial_wait_days=None` (engine default). It is used only for first-crop future-window eligibility/roll in `evaluate_calendar_fit`, `_root_planting_range`, and `_roll_root_window`; transitions use `max_waiting_days` only. Both are validated as non-negative ints/None. The user policy 180 is caller-supplied. Branches expose `initial_wait_days`; the request exposes `max_initial_wait_days`. Root waits over the initial limit are excluded at position 1 with `FUTURE_WINDOW_EXCEEDS_LIMIT` and product-cutoff wording; default None does not roll.
Boundary: synthetic future window exactly 180 days out -> 180/181 included as future caution, 179 excluded, default None excluded. 365/365 smoke baseline remains explicit.
Counts (`2026-11-06`):
- 365/365: 420 branches, 0 candidate / 420 conditional, 15 exclusions. First: Aman 62, boro 55, lentil 62, maize 55, mustard 62, potato 62, wheat 62.
- 180 initial / transition None: 295 branches, 0 / 295, 56 exclusions. First: Aman 0, boro 42, lentil 55, maize 42, mustard 54, potato 54, wheat 48. Exclusions: p1 future 1 + geography 1; p2 outside 3 + geography 2; p3 outside 42 + geography 7.
- 180 initial / transition 365: 358 branches, 0 / 358, 14 exclusions. First: Aman 0, boro 55, lentil 62, maize 55, mustard 62, potato 62, wheat 62. Exclusions: p1 future 1 + geography 1; p2 geography 2; p3 geography 10.
Explanation: 180 excludes Aman (246-day wait) and its 62 branches: 420 - 62 = 358; Aman paths also account for two p3 geography exclusions and add one p1 future exclusion, so 15 -> 14. With transition None, same-year post-support transitions are no longer rolled, producing 295/56 (42 p3 + 3 p2 outside); no numeric transition policy is invented. 365/365 retains all prior branches/exclusions.
Full suite: `python -X utf8 -m unittest discover -s tests -v`
```text
Ran 275 tests in 1.554s
OK
```
Focused branch expander: `Ran 25 tests`, OK. E6 smoke explicit 365/365: 420/0/420/15. No E7/E8 behavior changed; no commits.
