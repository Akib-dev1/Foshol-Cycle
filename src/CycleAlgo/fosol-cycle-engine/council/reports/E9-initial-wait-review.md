# E9 initial-wait split review

**Verdict: PASS.** Initial-wait behavior and counts match; one low test-placement gap.

Full suite: `Ran 275 tests in 1.597s`, `OK` (exit 0). Focused branch expander: `Ran 25 tests in 0.916s`, `OK`.

## Mutation gate (5/5 killed; hashes restored)
| mutation | failing test | hash OK |
|---|---|---|
| swap root/transition limits | `test_initial_wait_boundary_is_separate_from_transitions` (179/None) | yes |
| 180 boundary `<=` -> `<` | `test_waiting_limit_zero_and_boro_exact_boundary` (E4) | yes |
| default None roll | `test_first_crop_roots_exclude_unknown_and_unsupported` / initial-wait None | yes |
| initial_wait_days off-by-one | `test_initial_wait_boundary_is_separate_from_transitions` (180/181) | yes |
| root exclusion removed | `test_initial_wait_boundary_is_separate_from_transitions` (179) | yes |
Restored SHA-256 `20AF...A503` / `44A9...8BEF`; no mutation remains.

## Behavior and counts
Roots use `max_initial_wait_days` only; transitions use `max_waiting_days` only. Default initial `None` does not roll. Boundary: 180/181 included as `FUTURE_WINDOW_WITHIN_LIMIT`; 179 excluded with `FUTURE_WINDOW_EXCEEDS_LIMIT`; `None` excluded with `FUTURE_WINDOW_WAIT_POLICY_UNKNOWN`. Branches expose `initial_wait_days`; request exposes `max_initial_wait_days`; first-crop exclusions appear at position 1. Separation probes: 365/None 322/64; None/365 241/12.

Counts (`2026-11-06`): 365/365 420 branches, 0 candidate / 420 conditional, 15 exclusions (p1 geography 1, p2 geography 2, p3 geography 12). 180 initial / transition None: 295/56; first crops Aman 0, boro 42, lentil 55, maize 42, mustard 54, potato 54, wheat 48; exclusions p1 future 1 + geography 1, p2 outside 3 + geography 2, p3 outside 42 + geography 7. 180 initial / transition 365: 358/14; first crops Aman 0, boro 55, lentil 62, maize 55, mustard 62, potato 62, wheat 62; exclusions p1 future 1 + geography 1, p2 geography 2, p3 geography 10. Matches builder: 180 removes Aman’s 62 branches; transition None removes rolled paths, while 365 transitions restore 63.

E6 smoke 365/365: 420 branches, 0 candidate / 420 conditional, 15 exclusions all `WINDOW_GEOGRAPHY_UNKNOWN`. E7/E8 source unchanged.

Low: the 180 boundary mutation is not killed by focused E6 because root rolling re-includes the window; the E4 exact-boundary test kills it. Add a direct calendar boundary assertion if the focused mutation gate must be 5/5. No permanent edits; no commits.
