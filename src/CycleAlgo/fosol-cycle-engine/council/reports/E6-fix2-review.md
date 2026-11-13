# E6 fix 2 — rotation family repeats: review
Scope: `src/rotation.py`, `tests/test_rotation.py`, `council/reports/E6-fix2-builder.md`; `v1.md` §11. Fix1 (`branch_expander.py`) not reviewed.

**Verdict: PASS.** No blocking bug; the non-consecutive family-repeat defect is fixed and the smoke is stable.
Full `python -X utf8 -m unittest discover -s tests -v`: `Ran 178 tests in 0.848s`, `OK`; E6 focused `18+8+16=42` OK.

## Mutation check
Backed up `rotation.py` (SHA-256 `941BEDE6F5A078326830274C39A33B028BAEE7867335077E6F989A513A2F6940`), changed `prior_families` to previous-only; `test_non_consecutive_family_repeat_is_caution` failed `AssertionError: 'pass' != 'caution'` (`Ran 1 test`, `FAILED (failures=1)`). Restored; SHA matches; full suite 178 OK; no repo mutation remains.

## Behavior
| Case | Result |
|---|---|
| `boro->lentil->boro` | `caution`/`FAMILY_REPEAT_IN_PATH`, `matched_positions=[1,3]`, `path_length=3`, duplicate IDs preserved, `blocking=false` |
| immediate same-family | `caution`/`SAME_FAMILY_REPEAT`, `[1,2]` |
| different family | `pass`/`FAMILY_DIVERSIFIED`, `[]` |
| missing family | `unknown`/`ROTATION_FAMILY_EVIDENCE_MISSING`, `[]` |
| legume | present, unique IDs, note "not a guaranteed"; `blocking=false` |
| advisory text | `rule_machine_readable=false`, `machine_readable_rule_source_ids=[]`, `blocking=false` |

## Smoke (`2026-11-06`, max 365)
420 branches, 15 exclusions (all `WINDOW_GEOGRAPHY_UNKNOWN`), 0 candidate/420 conditional; 150 position-1/3 family-repeat branches, all third-crop rotation `caution` (81 `FAMILY_REPEAT_IN_PATH` + 69 `SAME_FAMILY_REPEAT`), 0 `FAMILY_DIVERSIFIED`.
Matches E6-fix1-builder 420/15. E6-review's 295/56 is pre-fix1; fix1 added 125 branches and cut exclusions 56→15, so repeats rose 62→150 (+88); fix2 changes no counts.
## Spec §11
`v1.md:330-339`: repeated families/previous occurrences are sequence checks; same-family repetition is a diversity indicator, not automatic rejection unless local evidence supports it; legume presence is potential BNF, not a guaranteed fertilizer saving.

## Bugs
1. Low: `_path_profiles` appends current unconditionally and `previous_family` uses `path[-2]`; a caller passing a path that already includes current or does not end with `previous_profile` gets a duplicate/wrong previous. Repo caller `branch_expander` passes prior-only, so no observed failure.
2. Low: `docs/TIMELINE.md:53-56` still names only `SAME_FAMILY_REPEAT`; `FAMILY_REPEAT_IN_PATH` and `matched_positions` are undocumented.
No commits; no permanent source/test edits.
