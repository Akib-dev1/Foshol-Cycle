# E8 W3 - resource metrics

Delivered `build_resource_metrics(branch, profiles=None)` in `src/branch_metrics.py`, plus 6 tests in
`tests/test_branch_metrics.py`. No E6/E7/W1/W2 behavior changed.

Output keeps `cash_cost`, `irrigation`, `labor`, and `equipment` as four separate objects; no combined
resource score. Cash is unavailable with `value_bdt_per_ha=None` and `production_cost_evidence`; no
reference yield is used. Labor and equipment are unavailable/null with `labor_evidence`/
`equipment_evidence`.

Irrigation is `status="context_only"` / `ranking_status="unranked"`, with per-crop `crop_id`,
`irrigation_guidance`, FAO water-need min/max, local phase total, and `water_ranking_readiness` from the
crop node or `profiles` fallback (node wins). No guidance is summed; `total=None` and no dependence score.
The reason states the guidance is not comparable.

Malformed branch shape makes all four unavailable with `INVALID_BRANCH_SHAPE`. Output is JSON-serializable
and has no crop-specific branches.

Full suite: `python -X utf8 -m unittest discover -s tests -v`
```text
Ran 246 tests in 1.476s
OK
```
Focused resource tests: `Ran 6 tests`, OK.
E6 smoke (`2026-11-06`, max 365): 420 branches, 0 candidate / 420 conditional, 15 exclusions
(`WINDOW_GEOGRAPHY_UNKNOWN`).

No commits.
