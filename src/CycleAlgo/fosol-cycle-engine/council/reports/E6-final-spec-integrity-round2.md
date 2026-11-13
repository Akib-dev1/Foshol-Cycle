# E6 — FINAL spec+integrity audit round 2 (fixes 4–5)
Scope: `src/timeline.py`, `src/branch_expander.py`, `src/rotation.py`; E6 tests; `docs/TIMELINE.md`; fix4/fix5 + final reports; `v1.md` §5/§10.2–10.4/§11/§14.4/§17.6–8/§17.12.

## Part A — verification -> code/test -> verdict
| # | Rule | Code / test | Verdict |
|---|---|---|---|
| 1 | Option A: clipped latest -> waiting/total `max=null`, `latest_invalid=true`, earliest retained | `timeline.py:191-246`; `test_timeline.py:271-284` | PASS |
| 2 | `NEXT_PLANTING_LATEST_CLIPPED` and `latest_clipped=true` retained | `timeline.py:329-379`; `test_branch_expander.py:369-396` | PASS |
| 3 | Branch conditional; path-level null/missing propagation | `branch_expander.py:776-789,992-1008`; `test_branch_expander.py:398-429` | PASS |
| 4 | Invariant: non-null total min/max >= prep min/max | `test_branch_expander.py:342-367`; reviewer smoke 0 below | PASS |
| 5 | `_transition_ok` requires `next_planting.status=="pass"`; caution -> conditional | `branch_expander.py:992-1008`; `test_branch_expander.py:431-470` | PASS |
| 6 | Fix 1 next-season roll still holds | `test_branch_expander.py:224-312` | PASS |
| 7 | Fix 2 all-path family repeats still caution, not blocking | `test_rotation.py:38-60` | PASS |
| 8 | Fix 3 uniqueness still: same sequence/different windows = 2; duplicate IDs flagged | `test_branch_expander.py:101-166` | PASS |
| 9 | Duration range propagation; unresolved reference conditional; no nursery double count | `timeline.py:53-114`; `test_timeline.py:38-115` | PASS |
| 10 | Prep missing -> unknown/null, never zero; prep only caller/synthetic | `timeline.py:59-64,78-83`; `test_timeline.py:117-166` | PASS |
| 11 | Next planting = max(ready, window opening); latest plausible/earliest retained | `timeline.py:329-379`; `test_timeline.py:184-215` | PASS |
| 12 | Exactly 3 crops/2 transitions; rotation/legume/BNF scope | `branch_expander.py:138-229`; `rotation.py:25-95`; E6 tests | PASS |

## Part B — provenance
- Duration only profile `variety_duration_min/max_days` (CSV or labeled synthetic); prep only caller/synthetic; `max_waiting_days` only caller, default `None`; no numeric defaults or invented data; status codes implementation-defined.
- No crop-ID/name branch (source scan/test); `latest_invalid` is derived from dates/clip, not invented; `Data/` untouched. Reviewer smoke: no-prep **420 branches/15 exclusions/0 candidate/420 conditional**; prep 7–10 **419/16**, **30 total<prep -> 0**, **30 latest_invalid**, **78 caution / 0 pass**.
- Low: `docs/TIMELINE.md` still omits `FAMILY_REPEAT_IN_PATH`/`matched_positions`; rotation `source_ids` is a field label; nursery age lacks `seedling_age_*` source IDs.

## Part C — verdict
Fixes 1–5: **PASS**. **E6 milestone: PASS**; no blocking criteria remain. Low residuals only: docs omit `FAMILY_REPEAT_IN_PATH`/`matched_positions`; `_limit_error` lacks product-cutoff wording.
Full suite **187 OK**; E6 focused **20+8+23=51 OK**; reviewer mutation **7/7**. Counts match reviewer smoke. No code/test edits.
