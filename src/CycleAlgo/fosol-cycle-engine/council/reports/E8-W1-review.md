# E8 W1 review - calculate_completion_time
Verdict: PASS. Bugs: none.
Full suite: `python -X utf8 -m unittest discover -s tests -v`
```text
Ran 232 tests in 1.464s
OK
```
Focused W1: `Ran 7 tests`, OK.

Decision A verified: known ranges give `completion_days={min:90,max:100}` from `H3.earliest-P1.earliest` and `H3.latest-P1.latest`; `ranking_value_days=100` (max); single-date ranges stay single. Missing/invalid/reversed component ranges return unavailable/null with missing evidence. `max < min` returns `COMPLETION_RANGE_INVALID`, never swapped. Malformed branch/crops/3-2 shape returns `INVALID_BRANCH_SHAPE`. Output includes `basis`, both source ranges, completion dates, and the overlap note; JSON serializable; no crop-ID branches.

Mutation gate (5/5 killed):
| mutation | failing test | hash OK |
|---|---|---|
| min endpoint earliest -> latest | `test_known_ranges_use_earliest_and_latest_pairing` | yes |
| max endpoint latest -> earliest | `test_known_ranges_use_earliest_and_latest_pairing` | yes |
| max<min guard removed | `test_max_below_min_is_unavailable_not_swapped` | yes |
| missing range -> 0 days | `test_missing_or_invalid_ranges_are_unavailable` | yes |
| shape 3/2 guard removed | `test_malformed_branch_shape_is_unavailable_without_crash` | yes |

Restored SHA-256 `3F06E878...`; no mutation remains.
E6 smoke (`2026-11-06`, max 365): 420 branches, 0 candidate / 420 conditional, 15 exclusions.
No E6/E7 source changed; no permanent edits; no commits.
