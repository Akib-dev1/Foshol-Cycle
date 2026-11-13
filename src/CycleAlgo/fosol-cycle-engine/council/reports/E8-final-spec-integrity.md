# E8 — FINAL spec + integrity audit: branch metrics
Scope: `src/branch_metrics.py`, `tests/test_branch_metrics.py`, E8 preflight/W1–W5 reports; `v1.md` §12.1–12.5/§13/§14.4/§17.14–17.

## Part A — rule -> code/test -> verdict
| # | Rule | Code / test | Verdict |
|---|---|---|---|
| 1 | Completion decision A endpoints; missing/reversed -> unavailable/null; rank latest; overlap note | `branch_metrics.py:29-94`; `test_branch_metrics.py:154-279` | PASS |
| 2 | Diversity family count/repeat proxy; legume via profiles; missing -> unknown/null; no soil-health claim | `branch_metrics.py:97-174`; `test_branch_metrics.py:281-420` | PASS |
| 3 | Resources separate cash/irrigation/labor/equipment; no combined score; cash/labor/equipment unavailable; irrigation context-only/unranked/no sum | `branch_metrics.py:177-242`; `test_branch_metrics.py:531-645` | PASS |
| 4 | Economics all unavailable/null; reference yields context-only; no price/cost/cash-flow values; scenarios empty; §17.15 | `branch_metrics.py:245-338`; `test_branch_metrics.py:422-528` | PASS |
| 5 | §12.4/§12.5 upfront cash only when sourced; total return/completion together; no financial estimates | `branch_metrics.py:245-338`; `test_branch_metrics.py:465-487` | PASS (low wording) |
| 6 | Ranking candidate/conditional separate; blocked excluded; missing metric unranked; ties/overlap; no forced winner; §17.14/15/17 | `branch_metrics.py:341-540`; `test_branch_metrics.py:648-841` | PASS |
| 7 | §17.16 financial units/transition costs | No financial values or conversion code; economics all null | **N/A — not ticked** |
| 8 | No invented prices/yields/costs; no crop-ID branches; no E6/E7 changes | Source scan; `test_branch_metrics.py:518-528`; E6 smoke | PASS |
| 9 | Real 420 branches: candidate 0; conditional fastest/diversity ranked; economics/irrigation no winner | Live probe; `test_branch_metrics.py:817-834` | PASS |
| 10 | E6 regression smoke 420/0/420/15 | Live probe `2026-11-06`, max 365 | PASS |
| 11 | Full suite 264; E8 tests 39 (7+8+6+7+11) within 25–40 | `test_branch_metrics.py` | PASS |
| 12 | `scripts/demo_check.py` deferred E9 | No script present; E9 envelope/API pending | N/A — deferred |

## Part B — provenance
- Completion uses E6 `planting_range`/`harvest_range`; diversity uses `family`/`is_legume_n_fixing` with profile fallback; no computed values are invented.
- Economics reads reference yields/price modes as context only and emits null monetary values, empty scenarios, and explicit missing IDs; resources emit no combined score or irrigation total.
- Low: `_resource_number` accepts negative/fill sentinels as irrigation context; `yield_reference_context` omits `source_yield`; §12.4 financing wording is generic. No financial values exist; §17.16 is N/A.
- Demo check remains E9; metrics are library-level, not yet attached to branch output.

## Part C — verdict
**PASS** for E8 spec/integrity; **§17.16 N/A** (no financial values, not ticked). Full suite **264 OK**; E8 **39 OK**; E6 smoke **420/0/420/15**.
Real 420: candidate 0; fastest **363 ranked / 57 unranked**; diversity **420 ranked**; economics and irrigation **420 unranked / no winner**.
Remaining low: negative/fill irrigation context; missing reference-yield source; generic financing wording; branch attachment/demo_check deferred E9. No code/test edits.
