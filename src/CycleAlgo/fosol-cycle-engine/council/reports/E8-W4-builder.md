# E8 W4 - economics unavailable

Delivered `build_economics_metrics(branch, profiles=None)` in `src/branch_metrics.py`. All monetary metrics are explicitly unavailable with `value_bdt_per_ha=None` and `unit="BDT/ha"`: `gross_revenue_bdt_per_ha`, `production_cost_bdt_per_ha`, `net_return_bdt_per_ha`, `upfront_cash_bdt_per_ha`. `scenarios=[]`; top-level `reason="Economic estimate unavailable."`.

`yield_reference_context` is per crop with `yield_reference_low_t_ha`, `yield_reference_high_t_ha`, `yield_basis`, and `status="static_reference_not_used"`; it is never used to compute revenue. `price_evidence` reports `market_price_mode` and `source_barc_zoning` with `status="unavailable"`, `price_value=None`, and no per-crop price value. `missing_evidence` is exactly `production_cost_evidence`, `farm_gate_price_evidence`, `validated_typical_yield_or_attainable_basis`, `cash_flow_schedule`; no cost/price/yield component is invented. Malformed branches return all-unavailable metrics with `INVALID_BRANCH_SHAPE` and no crash. `profiles` is an optional fallback; crop-node values win. JSON-serializable; no crop-specific branches.

Tests: `tests/test_branch_metrics.py`, 7 new docstring tests covering null/unavailable metrics, context-only yields, dynamic-external price evidence with no value, exact missing IDs, empty scenarios, malformed shape, JSON, and no crop-ID branches.

Full suite: `python -X utf8 -m unittest discover -s tests -v`
```text
Ran 253 tests in 1.516s

OK
```
Focused W4: `Ran 7 tests in 0.001s`, `OK`. Test count 246 -> 253 (+7).

E6 smoke (`2026-11-06`, max 365): 420 branches, 0 candidate / 420 conditional, 15 exclusions all `WINDOW_GEOGRAPHY_UNKNOWN`; unchanged. No E6/E7/W1/W2/W3 behavior changed.

No commits; only `src/branch_metrics.py`, `tests/test_branch_metrics.py`, and this report.
