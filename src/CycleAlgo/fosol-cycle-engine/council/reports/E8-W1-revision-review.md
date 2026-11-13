# E8 W1 revision review - corner-extreme completion
Verdict: PASS. Bugs: none.
Full suite: `python -X utf8 -m unittest discover -s tests -v`
```text
Ran 271 tests in 1.434s
OK
```
Focused metrics: `Ran 46 tests`, OK.

Verified: `min = H3.earliest - P1.latest`, `max = H3.latest - P1.earliest`; both realizations returned; `range_basis="corner_extremes"`. All 420 real branches are `ok` with `min <= max`; the 57 old-A inversions are valid; `b_82899e8d6941` is 655..682. Property test covers 300 fixed-seed realizations with no fallback. `enumerate_completion_range` matches the corner range and reports `enumeration_used=true`. The synthetic negative-corner branch returns unavailable/null with `COMPLETION_RANGE_INVALID` from both `calculate_completion_time` and `enumerate_completion_range` (`enumeration_used=true`); no negative range is `ok` across the 420 real branches. Reversed ISO ranges remain unavailable. Fastest completion ranks 420 conditional / 0 candidate / 0 unranked, with the overlap note.

Mutation gate (6/6 killed):
| mutation | failing test | hash OK |
|---|---|---|
| min latest -> earliest | `test_known_ranges_use_earliest_and_latest_pairing` | yes |
| max earliest -> latest | `test_known_ranges_use_earliest_and_latest_pairing` | yes |
| property upper bound collapsed | `test_completion_property_300_random_realizations` | yes |
| enumeration fallback bypassed | `test_enumerate_completion_range_matches_corner_extremes` | yes |
| `COMPLETION_RANGE_INVALID` guard removed | `test_negative_corner_min_is_unavailable` | yes |
| enumeration negative guard removed | `test_negative_corner_enumeration_is_unavailable` | yes |

Restored SHA-256 `9641C172...`; no mutation remains.
E6 smoke (`2026-11-06`, max 365): 420 branches, 0 candidate / 420 conditional, 15 exclusions.
No E6/E7 source changed; no permanent edits; no commits.
