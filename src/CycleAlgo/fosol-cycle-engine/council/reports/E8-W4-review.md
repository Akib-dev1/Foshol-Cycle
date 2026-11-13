# E8 W4 review - build_economics_metrics
Verdict: PASS. Bugs: none.
Full suite: `python -X utf8 -m unittest discover -s tests -v`
```text
Ran 253 tests in 1.252s
OK
```
Focused W4: `5 + 1 + 1 = 7 tests`, all OK.

Verified: `gross_revenue_bdt_per_ha`, `production_cost_bdt_per_ha`, `net_return_bdt_per_ha`, and `upfront_cash_bdt_per_ha` are all `unavailable` with `value_bdt_per_ha=None` and `unit="BDT/ha"`; no zero-filled economics. `scenarios=[]`; top-level reason is exactly `Economic estimate unavailable.`.
Reference yields are per-crop context (`status="static_reference_not_used"`) and gross remains null. Price evidence is `unavailable`, `market_price_mode="DYNAMIC_EXTERNAL"`, `price_value=None`, and per-crop entries carry no price value. Top-level `missing_evidence` is exactly `production_cost_evidence`, `farm_gate_price_evidence`, `validated_typical_yield_or_attainable_basis`, `cash_flow_schedule`. Malformed branch shape makes all four unavailable with `INVALID_BRANCH_SHAPE`; output is JSON-serializable; no crop-ID branches.

Mutation gate (5/5 killed):
| mutation | failing test | hash OK |
|---|---|---|
| gross from reference yields | `test_economics_metrics_are_unavailable_and_scenarios_empty` | yes |
| production cost -> 0 | `test_economics_metrics_are_unavailable_and_scenarios_empty` | yes |
| invented price value | `test_price_evidence_is_dynamic_external_without_value` | yes |
| invented scenario | `test_economics_metrics_are_unavailable_and_scenarios_empty` | yes |
| malformed-shape guard removed | `test_economics_malformed_branch_is_unavailable` | yes |

Restored SHA-256 `F180AFB1...`; no mutation remains.
E6 smoke (`2026-11-06`, max 365): 420 branches, 0 candidate / 420 conditional, 15 exclusions. No E6/E7 source changed; no permanent edits; no commits.
