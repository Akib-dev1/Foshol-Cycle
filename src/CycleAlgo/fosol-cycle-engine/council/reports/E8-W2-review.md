# E8 W2 - diversity metrics review

**Verdict: PASS. No numbered bugs.**

Full suite: `Ran 240 tests in 1.578s`, `OK` (exit 0). Focused W2: `Ran 8 tests in 0.070s`, `OK`.

## Mutation gate (5/5 killed; hashes restored)
| mutation | failing test | hash OK |
|---|---|---|
| distinct count list vs set | `test_two_families_reports_repeat_proxy` | yes |
| legume OR vs AND | `test_legume_presence_true_and_false` | yes |
| missing -> false/0 | `test_missing_family_or_legume_flag_is_unknown` | yes |
| profile fallback removed | `test_profile_family_and_legume_fallback_with_node_precedence` | yes |
| shape guard removed | `test_malformed_branch_shape_is_unavailable` | yes |
Restored SHA-256 `FFE1...9C5D`; no mutation remains.

## Behavior checks
- 3 families -> 3; 2 families -> 2; `family_repeat_count=3-distinct`; case/space normalized; basis `crop_family_count_product_convention`.
- Legume true/false verified; note says potential BNF, not guaranteed nitrogen credit.
- Real E6 branch with lentil/mung: profile fallback -> `legume_present=True`; without profiles -> `unknown`/null.
- Missing family -> family metrics null; missing legume -> `legume_present=None` (empty ID list), status `unknown`, `missing_evidence` populated; never false/zero.
- Malformed branch shape -> `unavailable`/null/`INVALID_BRANCH_SHAPE`; no crash.
- `diversity_note` explicitly says not a measured soil-health ranking; no crop-ID branches; JSON serializable.

E6 smoke: 420 branches, 0 candidate / 420 conditional, 15 exclusions all `WINDOW_GEOGRAPHY_UNKNOWN`; no E6 changes.

No permanent edits; no commits.
