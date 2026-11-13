# E8 — FINAL spec + integrity re-audit: real realizations
Scope: `src/branch_metrics.py`, `tests/test_branch_metrics.py`, E8 realization reports, prior E8 reports; `v1.md` §12.1–12.5/§13/§14.4/§17.14–17.

## Part A — rule -> code/test -> verdict
| # | Rule | Code / test | Verdict |
|---|---|---|---|
| 1 | Actual fastest/slowest P1/H1/P2/H2/P3/H3; example `b_82899e8d6941` 655..682 (fast P1 2027-07-24/H3 2029-05-09; slow P1 2027-07-10/H3 2029-05-22); 0 invalid/unranked | `branch_metrics.py:29-114,295-336`; `test_branch_metrics.py:490-566` | PASS |
| 2 | Independent tightness all 420; 300-sample exact min/max; prep-known real 60..99 vs widest 60..129; infeasible fallback; negative/reversed unavailable | `test_branch_metrics.py:568-704`; code 378-426 | PASS |
| 3 | Candidate 0 / conditional 420 cause is evidence: 1260/1260 nodes prep unknown, soil unknown, water caution/unknown, duration reference unresolved | Live probe; E6 checks | PASS |
| 4 | Fastest ranks 420/420 conditional by max, 0 unranked, candidate 0, overlap note | `branch_metrics.py:341-540`; `test_branch_metrics.py:992-1005` | PASS |
| 5 | Diversity/economics/irrigation unchanged | `test_branch_metrics.py:456-1012`; live probe | PASS |
| 6 | §17.14 blocked branches not revived | `test_branch_metrics.py:907-925`; code | PASS |
| 7 | §17.15 missing economics cannot win; no winner | `test_branch_metrics.py:901-923,1006-1012`; live probe | PASS |
| 8 | §17.17 honest insufficient/empty result; no forced winner | `branch_metrics.py:479-539`; tests | PASS |
| 9 | §17.16 financial units/transition costs | No financial values or conversion code | **N/A — not ticked** |
| 10 | No invented prices/yields/costs; no crop-ID branches; no E6/E7 changes | Source scan; tests; E6 smoke | PASS |
| 11 | E6 smoke 420/0/420/15 | Live probe `2026-11-06`, max 365 | PASS |
| 12 | Full suite 274; E8 49 vs 25–40 (+9) justified by tightness/property/fallback tests | `test_branch_metrics.py`; realization reports | PASS (budget justified) |

## Part B — provenance
- Completion comes from E6 `planting_range`/`harvest_range`/`duration`/transition prep+windows; actual fastest/slowest schedules; no annualization or invented timing.
- Conditional 420 is evidence-driven, not a metric bug: all evaluated crop nodes lack prep, soil, water confirmation, and duration-reference resolution.
- Low: `_resource_number` accepts negative/fill irrigation context; `yield_reference_context` omits `source_yield`; §12.4 financing wording generic. §17.16 is N/A.

## Part C — verdict
**PASS** for E8 realization re-audit. Corner realization tightness, rankings, conditional-cause evidence, and §17.14/15/17 all pass; §17.16 remains N/A.
Verified: example 655..682; 420/420 tight; fastest 420/420; E6 420/0/420/15; full suite 274; E8 49. Budget +9 justified.
Remaining low: negative/fill irrigation context; missing reference-yield source; generic financing wording; branch attachment/demo check deferred E9. No code/test edits.
