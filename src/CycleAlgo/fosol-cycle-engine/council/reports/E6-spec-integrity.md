# E6 — SPEC + INTEGRITY audit: timeline, preparation, waiting, rotation, 3-crop
Scope: `src/timeline.py`, `src/rotation.py`, `src/branch_expander.py`; `tests/test_timeline.py`, `test_rotation.py`, `test_branch_expander.py`; `docs/TIMELINE.md`; `council/reports/E6-builder.md`, `E6-review.md`; `v1.md` §5/§10/§11/§14.4/§17.6–8/§17.12.

## Part A — rule -> code/test -> verdict
| # | Rule | Code / test | Verdict |
|---|---|---|---|
| 1 | Duration min/max propagate, never averaged | `timeline.py:53-56`; `test_timeline.py:38-47` | PASS |
| 2 | Unresolved duration reference -> conditional | `timeline.py:96-114`; `test_timeline.py:108-115` | PASS (bool only; no type guard) |
| 3 | No nursery-age double count | `timeline.py:85-94,630-635`; `test_timeline.py:93-106` | PASS |
| 4 | Missing prep -> unknown/null, never zero | `timeline.py:59-64,78-83,106-114`; `test_timeline.py:117-124` | PASS |
| 5 | Next planting = max(ready, window opening) | `timeline.py:287-337`; `test_timeline.py:184-215` | PASS |
| 6 | Latest plausible label; earliest retained; clip exposed | `timeline.py:307-337`; `test_timeline.py:197-209` | PASS |
| 7 | §10.3/§10.5 resolve the next season, not a terminal current window | `branch_expander.py:411-413`; reviewer example `mustard->mung->boro` | **FAIL** — first `unsupported` returns immediately; boro's 2027-12-25..2028-01-10 window (217-230 d <=365) is excluded. |
| 8 | Waiting limit partial vs complete exclusion; product-cutoff label | `timeline.py:592-602,227-284`; `branch_expander.py:318-325`; `test_timeline.py:248-289` | **FAIL** — waiting clamps the clipped latest to 0; total (next-harvest) then falls below prep: synthetic prep 7-10 on real windows gives total {1,7} < prep {7,10}; a synthetic clipped earliest-only 11-day wait with limit 5 returns `partial`, not `exceeds`. |
| 9 | Exactly 3 crops/2 transitions; no 3rd-to-first claim | `branch_expander.py:138-220,677-719`; `test_branch_expander.py:38-53`; `TIMELINE.md:57-59` | PASS |
| 10 | Rotation same-family caution, not rejection; all path repeats | `rotation.py:25-31,51,102-118`; `test_rotation.py:27-34`; reviewer example | **PARTIAL** — consecutive same-family is caution/not blocking; 1&3 family repeats get `pass`, and `_path_profiles` dedupes by crop_id (`boro->lentil->boro` path_length=2). |
| 11 | Legume = potential BNF, not guaranteed N | `rotation.py:83-91`; `test_rotation.py:44-53` | PASS |
| 12 | Documented rules only; no invented sequence block | `rotation.py:19-24,70-99`; `test_rotation.py:55-72` | PASS (`source_ids` label weak) |
| 13 | Branch shape/deterministic IDs/nulls | `branch_expander.py:677-744,722-729`; `test_branch_expander.py:55-71,322-343` | PARTIAL — IDs deterministic, nulls/JSON OK; `_transition_ok` ignores `next_planting` caution; `metrics` deferred E8. |

## Part B — provenance
- Duration from profile `variety_duration_min_days/max_days` (CSV via loader or labeled synthetic); prep only caller `preparation`/`preparation_lookup`; blank `turnaround_*` never read in E6; no numeric prep default (`timeline.py:18,490-566`).
- `max_waiting_days` default `None`, non-negative int only; no numeric max constant in `src/`; statuses `not_configured/unknown/within/partial/exceeds`, basis `product_policy` (`timeline.py:26,227-284,620-627`; `branch_expander.py:40,815-822`).
- No crop-ID/name branch (source grep; `test_branch_expander.py:335-343`); test prep 7/10/0 and soil 0/0 are labeled `synthetic://`; residual: rotation `source_ids=["rotation_family_rule"]` is a field label, not a CSV source column, and `nursery_age_days` is reported without `seedling_age_*` in `source_ids`; CSV rows were not manually inspected (Data restriction).

## Part C — verdict
**FAIL**. Re-ran full suite: **176 tests OK**; E6 focused **18+7+15=40 OK**; builder smoke reproduced **295 branches/56 exclusions, all conditional, first boro->aman->boro, 3 crops/2 transitions**. `E6-review.md` independently FAILs §11 non-consecutive repeats and §10.3 next-season exclusion; this audit adds the waiting/total clamp. No code/test edits.
