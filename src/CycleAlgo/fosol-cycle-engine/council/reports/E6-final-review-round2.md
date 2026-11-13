# E6 final gate round 2
Fixes 1-5: PASS. E6 milestone: PASS. No blocking criteria remain.
Full suite: `python -X utf8 -m unittest discover -s tests -v`
```text
Ran 187 tests in 1.018s
OK
```
Focused E6: `test_timeline` 20, `test_rotation` 8, `test_branch_expander` 23 = 51 OK.

Mutation gate (6 categories / 7 probes, 7/7 killed):
| mutation | failing test | hash OK |
|---|---|---|
| next-season roll guard | `test_next_season_windows_roll_forward_within_limit` | yes |
| max-waiting comparison | `test_waiting_limit_statuses_are_inclusive_and_distinguish_overlap` | yes |
| rotation all-prior comparison | `test_non_consecutive_family_repeat_is_caution` | yes |
| uniqueness duplicate detection | `test_uniqueness_flags_duplicate_branch_ids` | yes |
| exactly-3 stop / prep-unknown guard | `test_every_branch_has_exactly_three_crops_and_two_transitions` / `test_missing_preparation_is_unknown_not_zero` | yes / yes |
| null-latest handling | `test_clipped_latest_keeps_earliest_end_only` | yes |

Restored SHA-256: timeline `FE72D446...`, rotation `941BEDE6...`, branch_expander `C0F0AE81...`; all match backups, no mutation remains.
Smoke no-prep: 420 branches, 15 exclusions (all `WINDOW_GEOGRAPHY_UNKNOWN`), 0 candidate / 420 conditional; boro first 55; 150 pos-1/3 family repeats all caution (81 `FAMILY_REPEAT_IN_PATH` + 69 `SAME_FAMILY_REPEAT`); uniqueness 420/420 IDs and sequences, 0 duplicates.
Smoke prep 7-10: 419 branches, 16 exclusions, 0 candidate / 419 conditional; total<prep 30 -> 0; 30 `latest_invalid` all waiting/total `max=null`; 78 caution transitions, 0 pass `_transition_ok`; 760 pass-status transitions, 376 pass.
419/16 vs 420/15: the extra p3 exclusion is `aman->wheat->mung` (`WINDOW_GEOGRAPHY_UNKNOWN`); prep shifts wheat ready earliest to 2028-03-26, just after mung's 2028-03-25 support. Prep-timing effect, not a fix4/5 branch loss.
Path-level: all 30 `latest_invalid` retain `NEXT_PLANTING_LATEST_CLIPPED` / `latest_clipped=true` with limit `partial`; `_transition_ok` rejects `latest_invalid` and caution transitions; all branches conditional.
Remaining (non-blocking): docs omit rotation `FAMILY_REPEAT_IN_PATH`/`matched_positions`; `_limit_error` wording lacks the product-cutoff disclaimer.
No permanent edits; no commits.
