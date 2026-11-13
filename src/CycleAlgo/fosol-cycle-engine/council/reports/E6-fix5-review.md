# E6 fix 5 - caution next-planting transitions cannot be candidates

**Verdict: PASS. No numbered bugs.** The final review's candidate-caution criterion is closed.

Full suite `python -X utf8 -m unittest discover -s tests -v`: `Ran 187 tests in 0.986s`, `OK` (exit 0). Focused E6: 20+8+23=51 OK.
Synthetic test `test_caution_next_planting_transition_is_conditional`: caution transition -> `_transition_ok` false and mixed branch conditional; all-pass control -> candidate. Pre-fix builder output: `AssertionError: True is not false`; after fix: `Ran 1 test in 0.001s`, `OK`.

## Mutation
| mutation | failing test | hash OK |
|---|---|---|
| remove `next_planting.status == "pass"` guard | `test_caution_next_planting_transition_is_conditional` | yes |
Guard disabled -> `FAIL: test_caution_next_planting_transition_is_conditional`, `Ran 1 test`, `FAILED (failures=1)`; restored SHA-256 `C0F0...E454` matches backup.

## Smoke (`2026-11-06`, max 365)
- No prep: 420 branches, 15 exclusions, 0 candidate/420 conditional; 840 `next_planting.status="unknown"`, 0 pass `_transition_ok`; unchanged.
- Prep 7-10: 419 branches, 16 exclusions, 0 candidate/419 conditional; 760 pass + 78 caution transitions; 78 caution -> 0 pass `_transition_ok`; 376 pass-status transitions still pass.
- One extra exclusion vs no-prep: `aman->wheat->mung` at p3 is `WINDOW_GEOGRAPHY_UNKNOWN` under prep because prep shifts `aman->wheat` readiness later, so third-position mung's reference falls after support; no-prep has this branch. Fix5 does not add it.
- Fix4 null-latest unchanged: 30 `latest_invalid`, all waiting/total `max=null`, 0 total<prep; example `aman->mustard` t2 waiting {0,null}, total {7,null}, `NEXT_PLANTING_LATEST_CLIPPED`, `latest_clipped=true`.

No permanent edits; no commits.
