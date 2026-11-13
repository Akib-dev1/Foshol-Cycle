# E6 limit wording review - product cutoff basis
Verdict: PASS. Bugs: none.
Full suite: `python -X utf8 -m unittest discover -s tests -v`
```text
Ran 188 tests in 1.096s
OK
```
Focused E6: `test_timeline` 20, `test_rotation` 8, `test_branch_expander` 24 = 52, all OK.
`test_limit_error_states_product_basis` passes and verifies the reason keeps the date/wait/limit facts plus:
- "product relevance cutoff"
- "not a scientifically safe maximum"
- "not a biological impossibility"
- no "longer fallow is impossible"

Reason: "The limit is a product relevance cutoff, not a scientifically safe maximum and not a biological impossibility; longer fallow is not claimed impossible."

Mutation:
| mutation | failing test | hash OK |
|---|---|---|
| remove disclaimer from `_limit_error` | `test_limit_error_states_product_basis` -> `AssertionError: 'product relevance cutoff' not found` | yes |

Before/after SHA-256 `9BD95844...`; mutated `C0F0AE81...`; restored hash matches the backup, no mutation remains.
Smoke (`2026-11-06`, max 365): 420 branches, 15 exclusions all `WINDOW_GEOGRAPHY_UNKNOWN`, 0 candidate / 420 conditional.
Low-limit smoke (245): `FUTURE_WINDOW_EXCEEDS_LIMIT` reason includes the new product-basis wording.
No permanent edits; no commits.
