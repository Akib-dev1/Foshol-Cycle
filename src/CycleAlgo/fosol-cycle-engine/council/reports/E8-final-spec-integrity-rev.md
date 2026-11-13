# E8 — FINAL spec + integrity re-audit: corner completion
Scope: `src/branch_metrics.py`, `tests/test_branch_metrics.py`, E8-W1 revision reports, prior E8 reports; `v1.md` §12.1–12.5/§13/§14.4/§17.14–17.

## Part A — rule -> code/test -> verdict
| # | Rule | Code / test | Verdict |
|---|---|---|---|
| 1 | Corner form `min=H3.e−P1.l` / `max=H3.l−P1.e`; both realization dates; min<=max 420; 0 invalid/unranked; 57 old inversions valid; example 655..682 | `branch_metrics.py:29-62`; `test_branch_metrics.py:169-380` | PASS |
| 2 | 300 fixed-seed samples within range; no fallback on real branches; enumeration matches corner; old guard only never-fire assertion | `test_branch_metrics.py:382-447` | PASS |
| 3 | Enumeration fallback handles negative/reversed as unavailable | `branch_metrics.py:65-102`; `test_branch_metrics.py:323-341` | PASS — negative -> `COMPLETION_RANGE_INVALID`/null |
| 4 | Fastest ranks 420/420 conditional by max, 0 unranked, candidate 0, overlap note | `branch_metrics.py:341-540`; `test_branch_metrics.py:992-1005` | PASS |
| 5 | Diversity/economics/irrigation unchanged | `test_branch_metrics.py:456-1012`; live probe | PASS |
| 6 | §17.14 blocked branches not revived | `test_branch_metrics.py:907-925`; code | PASS |
| 7 | §17.15 missing economics cannot win; no winner | `test_branch_metrics.py:901-923,1006-1012`; live probe | PASS |
| 8 | §17.17 honest insufficient/empty result; no forced winner | `branch_metrics.py:479-539`; tests | PASS |
| 9 | §17.16 financial units/transition costs | No financial values or conversion code | **N/A — not ticked** |
| 10 | No invented prices/yields/costs; no crop-ID branches; no E6/E7 changes | Source scan; tests; E6 smoke | PASS |
| 11 | E6 smoke 420/0/420/15 | Live probe `2026-11-06`, max 365 | PASS |
| 12 | Full suite 271; E8 46 vs 25–40 (+6) justified by required negative-enumeration regression plus property/fallback/negative tests | `test_branch_metrics.py`; revision reports | PASS (budget justified) |

## Part B — provenance
- Completion is from E6 `planting_range`/`harvest_range`; corner endpoints and realization dates; `ranking_value_days=max`; no annualization or invented duration.
- Diversity/resources/economics remain profile/CSV context only; no monetary values; reference yields are not used for revenue. No crop-ID branches; no E6/E7 source changes.
- Low: `_resource_number` accepts negative/fill irrigation context; `yield_reference_context` omits `source_yield`; §12.4 financing wording generic. §17.16 is N/A.

## Part C — verdict
**PASS** for E8 re-audit. The negative-enumeration blocker is fixed: `enumerate_completion_range` now returns `unavailable`/null with `COMPLETION_RANGE_INVALID`; the new regression test passes.
Verified: 420/420 min<=max; 0 `COMPLETION_RANGE_INVALID`/unranked; example `b_82899e8d6941` 655..682; fastest 420/420 conditional, 0 unranked; E6 420/0/420/15; full suite 271; E8 46. Budget +6 justified.
Remaining low: negative/fill irrigation context; missing reference-yield source; generic financing wording; branch attachment/demo check deferred E9. §17.16 remains N/A. No code/test edits.
