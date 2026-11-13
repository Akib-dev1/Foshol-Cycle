# E8 W3 review - resource metrics

**Verdict: PASS.** No blocking bugs. Full suite: `Ran 246 tests in 1.193s`, `OK`; focused W3: `Ran 6 tests`, `OK`.

## Checks
| Check | Result |
|---|---|
| Four keys; no combined score | PASS: exact `cash_cost`, `irrigation`, `labor`, `equipment`; no score/total key |
| Cash/labor/equipment unavailable/null | PASS: `value_bdt_per_ha=None`, `value=None`, evidence ids |
| No reference-yield use | PASS: source grep; reason states reference yields are not used |
| Irrigation context-only/unranked | PASS: `context_only`, `unranked`, per-crop context, node-first/profile fallback |
| No summed guide/volume | PASS: `total=None`, no dependence score |
| Malformed shape | PASS: all four unavailable with `INVALID_BRANCH_SHAPE` |
| JSON/no crop-ID branches | PASS: JSON test; known crop-ID scan clean |
| Low | `_resource_number` accepts negative/fill sentinels as unranked context; no score/sum effect |

## Mutations (5/5 killed)
| Mutation | Failing test |
|---|---|
| cash unavailable -> 0 | `test_cash_labor_and_equipment_are_unavailable` |
| labor unavailable -> 0 | `test_cash_labor_and_equipment_are_unavailable` |
| irrigation sum added | `test_irrigation_is_context_only_without_numeric_total` |
| combined score added | `test_resources_remain_four_separate_metrics` |
| malformed guard removed | `test_malformed_branch_makes_all_resources_unavailable` |

SHA-256 restored: `FB4802D9D4AACF0336CCCE3E0DC69A3093BECA417FD596A3CF204458B5335435`; no mutation remains.
E6 smoke: 420 branches, 0 candidate / 420 conditional, 15 exclusions; unchanged. No E6/E7 changes; no permanent edits; no commits.
