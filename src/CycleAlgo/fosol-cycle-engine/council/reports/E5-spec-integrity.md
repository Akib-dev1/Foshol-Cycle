# E5 — SPEC + INTEGRITY audit (round 2): soil/land + water
Scope: `src/soil_water.py`, `tests/test_soil_water.py`, `docs/SOIL_WATER.md`, `council/reports/E5-builder.md`; `v1.md` §5/§7/§8/§14.4; crop CSV.

## Part A — fix/spec -> code/test -> verdict
| # | Rule | Code / test | Verdict |
|---|---|---|---|
| 1 | §7 only local soil evidence; no inference of local values from crop-CSV/SMAP/POWER | 42-48; tests 70, 118 | PASS |
| 2 | §7 SMAP context only, never a validated threshold | 529-541; tests 91, 108 | PASS |
| 3 | §7 pH evidence 0-14 and min<=max; invalid -> unknown | 199-209; test 215 | PASS |
| 4 | §7 pH crop rule 0-14, ordered, tolerance contains optimum; invalid/missing -> unknown | 490-518; test 215 | PASS |
| 5 | §7 salinity negative/min>max -> unknown | 388-397; test 243 | PASS |
| 6 | §7 no assumed salinity unit: missing/wrong unit -> unknown | 398-418; test 243 | PASS |
| 7 | §7 strict `<N dS/m`: max<N pass; max==N/min>N/straddle caution | 446-487; test 243 | PASS |
| 8 | §7/§14.4 pH/salinity pass requires local `source_ids`; crop source does not count | 239-248, 432-441; tests 161, 243 | PASS |
| 9 | §8 default `unknown`/enum; unknown access -> "Irrigation confirmation required" | 21, 66-71, 134-143; tests 329, 356 | PASS |
| 10 | §8 rainfed/irrigation partial; no demand-minus-rainfall | 144-163; tests 339, 347, 363 | PASS |
| 11 | §8 negative demand -> unknown invalid; 0 caution; None -> unknown missing | 119-131; test 378 | PASS |
| 12 | §5/§14.4 unknown never pass; shape/nulls/JSON; no crop-ID branches | 23, 544-579, 627-636; tests 293, 446 | PASS |

## Part B — provenance
- Crop rules/guidance come only from CSV (`ph_opt_*`, `ph_tol_*`, `salinity_ecocrop`, texture/drainage, `fao_crop_water_need_*_mm`, `local_phase_water_total_mm`, `irrigation_guidance`); local pH/salinity/texture/drainage values are caller-supplied. No invented thresholds, local soil, demand, or classifications.
- New code literals are generic pH 0-14/monotonicity guards, precedence, and unit labels; tests use `synthetic://`; real assertions (450/700/631 mm, `wide`) match CSV.
- No crop-ID/name branch exists (source scan; test 446). Real profiles remain `unknown` without local evidence.
- Residuals (non-favourable): FAO `min > max` is not validated (returns caution, not unknown); invalid negative demand keeps `missing_evidence=["crop_water_demand_evidence"]`. Neither can yield `pass`.

## Part C — verdict
**PASS**. All five E5-review findings are closed; re-ran `python -X utf8 -m unittest discover -s tests`: **136 tests, OK**; E5 **20 tests, OK** (shell output, matches builder).
Residual risk: inverted demand range and the invalid-demand missing-evidence label are semantically off; no favourable result or invented data. Data/ inventory claim not independently re-checked (read restriction).
