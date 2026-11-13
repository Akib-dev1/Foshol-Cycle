# E8 realization revision review
Verdict: PASS. Bugs: none.
Full suite: `python -X utf8 -m unittest discover -s tests -v`
```text
Ran 274 tests in 1.673s
OK
```
Focused metrics: `Ran 49 tests`, OK.

Verified: `b_82899e8d6941` is 655..682 with actual fastest P1 2027-07-24/H3 2029-05-09 and slowest P1 2027-07-10/H3 2029-05-22 from the crop ranges/durations. Prep-known synthetic is now real 60..99 (fastest P1 2026-01-10/H3 03-11, slowest P1 01-01/H3 04-10) versus clamped B 60..129. Independent manual tightness over all 420 checks completion days and both min/max realization dates. The 300-sample test hits the exact min/max corners. Infeasible prep-known corners use the enumeration fallback. W5 fastest ranks 420 conditional / 0 candidate / 0 unranked with the overlap note. E6 smoke 420/0/420/15.

Mutation gate (5/5 killed):
| mutation | failing test | hash OK |
|---|---|---|
| fastest P1 latest -> earliest | `test_realized_corners_are_tight_for_all_real_branches` | yes |
| slowest P1 earliest -> latest | `test_realized_corners_are_tight_for_all_real_branches` | yes |
| independent tightness upper bound collapsed | `test_realized_corners_are_tight_for_all_real_branches` | yes |
| sampling corners removed | `test_sampling_min_max_equal_realized_corners` | yes |
| fallback disabled | `test_prep_known_infeasible_corner_falls_back_to_enumeration` | yes |

Restored SHA-256 source `EE593061...`, test `BB5499F1...`; no mutation remains.
No E6/E7 source changed; no permanent edits; no commits.
