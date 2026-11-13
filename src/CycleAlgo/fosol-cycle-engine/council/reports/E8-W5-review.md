# E8 W5 - preference ranking review

**Verdict: PASS. No numbered bugs.**

Full suite: `Ran 264 tests in 8.652s`, `OK` (exit 0). Focused W5: `Ran 11 tests in 0.087s`, `OK`.

## Mutation gate (5/5 killed; hashes restored)
| mutation | failing test | hash OK |
|---|---|---|
| completion asc -> desc | `test_fastest_completion_ranks_conditional_and_notes_empty_candidate` | yes |
| diversity desc -> asc | `test_diversity_ranks_descending_and_shows_legume_separately` | yes |
| candidate/conditional merge | `test_candidate_and_conditional_groups_stay_separate` | yes |
| missing -> zero | `test_economic_and_irrigation_preferences_are_unranked_no_winner` | yes |
| blocked revival | `test_blocked_branch_is_excluded_not_revived` | yes |
Restored SHA-256 `1452...DEFC`; no mutation remains.

## Behavior checks
- Candidate and conditional groups stay separate; unsupported/blocked branches go to `excluded`, never revived.
- Fastest completion ranks by `completion_days.max` ascending with branch-id tie-break; top-two overlap adds a visible note.
- Diversity ranks by `distinct_family_count` descending; legume presence is separate; product-convention wording retained.
- Cost, net return, upfront cash, and irrigation dependence are unranked with `no_winner=true`; missing completion is unranked, not zero.
- Invalid preference raises `ValueError`; ties are deterministic by branch ID; JSON serializable; no crop-ID branches.
- Real E6 smoke branches: 420, candidate 0; fastest and diversity rank conditional branches; economics has no winner.

E6 smoke: 420 branches, 0 candidate / 420 conditional, 15 exclusions all `WINDOW_GEOGRAPHY_UNKNOWN`; no E6/E7 changes.

No permanent edits; no commits.
