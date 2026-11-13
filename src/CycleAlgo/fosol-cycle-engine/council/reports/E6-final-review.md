# E6 final milestone gate review

**Verdict: fixes 1-3 PASS; E6 milestone FAIL.** Full suite `Ran 181 tests in 0.903s`, `OK` (exit 0); focused E6 `18+8+19=45`, all OK.

## Mutation gate (5 categories / 6 probes, 6/6 killed; hashes restored)
| mutation | failing test | hash OK |
|---|---|---|
| next-season roll guard | `test_next_season_windows_roll_forward_within_limit` | yes |
| max-waiting `<=` -> `<` | `test_waiting_limit_statuses_are_inclusive_and_distinguish_overlap` | yes |
| rotation all-prior | `test_non_consecutive_family_repeat_is_caution` | yes |
| uniqueness duplicate detection | `test_uniqueness_flags_duplicate_branch_ids` | yes |
| exactly-3 stop (4 nodes) | `test_every_branch_has_exactly_three_crops_and_two_transitions` | yes |
| prep-unknown guard | `test_missing_preparation_is_unknown_not_zero` | yes |
SHA-256 restored: `6677...FA3`, `941B...6940`, `9DA4...07CC`; all match backups, no mutation remains.

## Smoke (`2026-11-06`, max 365)
420 branches, 15 exclusions all `WINDOW_GEOGRAPHY_UNKNOWN`, 0 candidate/420 conditional, boro first 55, 150 pos-1/3 family repeats all caution (81 `FAMILY_REPEAT_IN_PATH` + 69 `SAME_FAMILY_REPEAT`), uniqueness 420/420 IDs and sequences, 0 duplicates. Matches context; no discrepancy.

## Remaining §10.4 defect (blocking)
Prep 7-10: 419 branches, 16 exclusions; 30 transitions have total below prep (30 min < prep min; 23 max < prep max). Example `aman->mustard->aman`, transition 2: prep {7,10}, next {2027-12-09..21}, total {5,7}, waiting {0,0}, `NEXT_PLANTING_LATEST_CLIPPED`. The clipped latest next planting is paired with latest ready/harvest; total must be >= prep for every realization.
Candidate check: 78 transitions have `next_planting.status=="caution"`; 1 (`lentil->boro->aman`, p3) passes current `_transition_ok` (calendar pass, waiting within, waiting non-null); 0 candidate branches because all 1,257 crop nodes are conditional (soil/water unknown/caution). `_transition_ok` omits `next_planting.status`, so a candidate is possible if crop checks pass.

## Remaining criteria
1. Fix waiting/total pairing: 0 transitions with total < prep at prep 7-10; clipped latest must not undercut prep; add regression test.
2. Require `next_planting.status == "pass"` in `_transition_ok` (or equivalent) and test; no candidate with a caution transition.
3. Low/non-blocking: update `docs/TIMELINE.md` for `FAMILY_REPEAT_IN_PATH`/`matched_positions`; `_limit_error` wording.

No permanent edits; no commits.
