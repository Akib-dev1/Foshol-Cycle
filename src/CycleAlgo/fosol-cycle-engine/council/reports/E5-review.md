# E5 — Soil/land + water checks: round-2 review

Scope: `src/soil_water.py`, `tests/test_soil_water.py`, `docs/SOIL_WATER.md`, `council/reports/E5-builder.md` | Spec: `v1.md` §5, §7, §8, §14.4 | No permanent source/test edits; only this report; no direct `Data/` access.
**Verdict: PASS** — all round-1 findings fixed; full/focused suites green; 5/5 mutations killed. One low JSON edge remains.
## Real output
Full: `Ran 136 tests in 0.124s`, `OK` (exit 0). Focused E5: `Ran 20 tests in 0.003s`, `OK` (exit 0).
## Round-1 fixes (code / test citations)
| finding | code | test |
|---|---|---|
| negative salinity / invalid range | 388-397 | 267-277 |
| missing or wrong unit | 398-418 | 270-271 |
| strict `<N` threshold | 446-477 | 255-265 |
| pH evidence + crop-rule validity | 199-209, 490-518 | 215-241 |
| local provenance guard | 239-248, 432-441 | 180-187, 279-283 |
| negative water demand | 119-129 | 399-413 |
## Mutation gate (5/5 killed, isolated pycache)
| mutation | failing test | hash OK |
|---|---|---|
| salinity wrong-unit guard | `test_salinity_comparisons` | yes |
| strict `<N` threshold | `test_salinity_comparisons` | yes |
| pH rule containment | `test_ph_invalid_range_and_missing_crop_rule` | yes |
| pH provenance guard | `test_ph_inclusive_boundaries_and_inside_optimum_are_pass` | yes |
| demand-invalid guard | `test_local_phase_total_alone_counts_as_demand` | yes |
All restored; final SHA-256 `BDE94F01...D1B7EB` matches backup; focused suite OK after each restore.
## New findings
Low: `details["unit"]` stores the raw unit; a non-string unit (e.g. `set()`/`bytes`) returns `SOIL_SALINITY_UNIT_INVALID` but is not JSON-serializable. Store `unit_text` (or a string) in details.
Regression sweep: pH inclusive/overlap/outside-tolerance, wet/dry moisture, all water-access branches, rainfall ignored, precedence, JSON/determinism, no crop-ID branches; no false pass found. Demo_check: N/A until E8–E9.
