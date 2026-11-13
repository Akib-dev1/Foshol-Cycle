# E6 fix 4 review - null latest / Option A refined
Verdict: PASS. Bugs: none in fix4 scope.
Full suite: `python -X utf8 -m unittest discover -s tests -v`
```text
Ran 186 tests in 0.972s
OK
```
Focused E6: `test_timeline` 20, `test_rotation` 8, `test_branch_expander` 22 = 50, all OK.
Failing-before: HEAD sources + current test `test_preparation_interval_is_lower_bound_for_total` -> `AssertionError: 30 != 0`; current test passes.
Clipped contract: direct call -> waiting `{0,null}`, total `{62,null}`, `latest_invalid=true`. Real `aman->mustard->boro` t2 -> waiting `{0,null}`, total `{7,null}`, `NEXT_PLANTING_LATEST_CLIPPED`, `latest_clipped=true`, limit `partial`.

| mutation | failing test | hash OK |
|---|---|---|
| `latest_invalid=False and (...)` | `test_clipped_latest_keeps_earliest_end_only` -> `ValueError: later range cannot precede the earlier range` | before/after `FE72D446C285427C1FF673E56BEF6E290415D46E9099784AB40CCF2E8A0C7056` |

Restored timeline/branch_expander SHA-256: `FE72D446...` / `298BC46F...`; no mutation remains.
Smoke no prep: 420 branches, 15 exclusions, 0 candidate / 420 conditional.
Smoke prep 7-10: 419 branches, 16 exclusions, 0 candidate / 419 conditional, uniqueness 419/419. The one extra p3 `WINDOW_GEOGRAPHY_UNKNOWN` is `aman->wheat->mung`: prep shifts wheat ready earliest to 2028-03-26, just after mung's 2028-03-25 support. It is a prep-timing effect, not a fix4 branch loss.
Invariant: 0 non-null total min/max below preparation min/max.
Path-level: 30 `latest_invalid` transitions, all `NEXT_PLANTING_LATEST_CLIPPED` + `latest_clipped=true` + limit `partial`; 78 next-planting cautions, 0 of those pass `_transition_ok`; `_transition_ok` rejects `latest_invalid`; all branches conditional.
Docs note matches the null-latest/waiting behavior.
No permanent edits; no commits.
