# E8 preflight — metrics, economics, rankings, preferences

Date: 2026-11-07. Status: **awaiting user decisions; no E8 code written.**
E7 accepted. E8 guard PASS (`2e01a65`, 225 tests, E6 smoke 420/0/420/15).
W4 `attach_branch_outlook` is **deferred, not dropped**; `build_outlook` exists,
no branch attachment. E9 can wire it; E8 does not require it.

## Requirements (v1.md)

- §12.1 completion = third harvest − first planting; show a range; rank by a stated
  convention such as latest completion; disclose overlapping ranges.
- §12.2 keep cash cost, irrigation dependence, labor, equipment separate; no combined
  score; do not sum qualitative irrigation as volume.
- §12.3 BDT/ha; gross = yield × farm-gate price; net = gross − production cost; branch
  sums; transition costs once; record yield/price/cost sources and conditions; missing
  essential input -> **Economic estimate unavailable**; partial costs cannot win.
- §12.4 upfront cash only with a sourced cash-flow schedule; otherwise total cost and
  "financing needs have not been modeled".
- §12.5 show total return and completion time together; no annualization in v1.
- §13 preferences: fastest completion, lowest total cost, least irrigation dependence
  (only with comparable evidence), highest net return, more diversity, lowest upfront
  cash (only with cash flow). No weighted score.
- §13 rules: blocking constraints win; candidate and conditional in separate groups;
  missing metric -> unranked, not favorable; ties/overlaps visible; explain the
  highlighted path and trade-offs; never force a winner.
- §14.4 metrics: completion days, production cost, net return, irrigation evidence,
  labor/equipment evidence, distinct family count, legume presence; unavailable
  metrics unranked; units/basis required.
- Gate: §17.14 blocked branches cannot be revived; §17.15 missing economics cannot
  win cost/return rankings; §17.16 units and transition costs once; §17.17 honest
  empty/insufficient-evidence result.
- §19 open: which comparable management, cost, yield, and farm-gate price evidence
  can support rankings?

## Inputs in repo

| Input | Fields | Exists? |
|---|---|---|
| Yields | `yield_reference_low_t_ha`, `yield_reference_high_t_ha`, `yield_basis`, `source_yield`, `income_ranking_readiness` | Static references only; all `PARTIAL_STATIC_YIELD_ONLY`. |
| Prices | `market_price_mode`, `barc_zoning_required`, `source_barc_zoning` | No price values; all `DYNAMIC_EXTERNAL`; only a BARC zoning URL. |
| Production costs | — | Missing. |
| Labor / equipment | — | Missing. |
| Cash-flow schedule | — | Missing. |
| Irrigation context | `irrigation_guidance`, `fao_crop_water_need_min_mm`, `fao_crop_water_need_max_mm`, `local_phase_water_total_mm`, `local_water_metric_note`, `water_ranking_readiness` | Qualitative/context only; no comparable dependence classification. |
| Completion time | E6 `planting_range`, `harvest_range`, `transitions`, `waiting_range`, `total_interval_range_days` | Yes. |
| Diversity | `family`, `is_legume_n_fixing`, `rotation_family_rule`, `rotation_note` | Yes. |
| Branch status/reasons | E6 `status`, `checks`, `reasons`, `cautions`, `missing_evidence` | Yes. |

Yield references: Aman 5.0–5.5; Boro 6.0–6.0; Wheat 4.8–5.5; Mustard 1.6–2.0;
Lentil 2.25–2.4; Mung 1.5–1.6; Maize 8.1–11.1 (drought 8.1–8.5 vs normal irrigation
10.0–11.1); Potato 38–54. `yield_basis` records study/attainable/potential, not
validated farm profit.

## Decisions needed

1. **Economics:** A (recommended) completion + diversity only; all economic/resource
   metrics `unavailable` with reasons. B: user supplies sourced prices/costs/cash-flow/
   typical yields before E8. C: reference yields alone — still unavailable because
   prices/costs missing.
2. **Completion range endpoints:** A (recommended) `[H3.earliest − P1.earliest,
   H3.latest − P1.latest]`, rank by latest; B widest corner span (pairs unrelated
   endpoints); C enumerate realizations.
3. **Irrigation ranking:** A display qualitative guidance only, no rank; B user supplies
   comparable dependence classification; C text heuristic (not comparable).
4. If B economics: yield scenario (maize drought vs normal), price source/date/grade,
   cost/cash-flow components.
5. Labor/equipment/upfront cash unavailable unless supplied.
6. No annualization (v1).
7. Diversity: distinct family count; legume presence separate; no soil-health claim.

Current E6 smoke: **0 candidate / 420 conditional / 15 exclusions**, so the candidate
ranking group is empty; conditional branches must be ranked only within their group.

## Proposed split

1. W1 `calculate_completion_time(branch)` — range + latest convention + overlaps.
2. W2 `calculate_diversity_metrics(branch)` — family count + legume + reasons.
3. W3 `build_resource_metrics(branch)` — separate cash/irrigation/labor/equipment.
4. W4 `build_economics_metrics(...)` — unavailable with reasons; interface for sourced data.
5. W5 `rank_branches(branches, preference)` — candidate/conditional groups, missing
   unranked, ties/overlaps, reasons, no forced winner.

Each function: failing-then-passing tests, mutation check, code/spec check, E6 smoke
420/0/420/15 after every commit, commit/push.
