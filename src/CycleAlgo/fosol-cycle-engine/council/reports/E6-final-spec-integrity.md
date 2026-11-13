# E6 — FINAL spec + integrity audit: timeline/rotation/3-crop
Scope: `src/timeline.py`, `src/rotation.py`, `src/branch_expander.py`; E6 tests; `docs/TIMELINE.md`; E6 builder/fix/review reports; `v1.md` §5/§10/§11/§14.4/§17.6–8/§17.12.

## Part A — rule -> code/test -> verdict
| # | Rule | Code / test | Verdict |
|---|---|---|---|
| 1 | Duration min/max propagate; no averaging | `timeline.py:53-56`; `test_timeline.py:38-47` | PASS |
| 2 | Unresolved duration reference -> conditional | `timeline.py:96-114`; `test_timeline.py:108-115` | PASS |
| 3 | No nursery-age double count | `timeline.py:85-94,630-635`; `test_timeline.py:93-106` | PASS |
| 4 | Missing prep -> unknown/null, never zero | `timeline.py:59-64,78-83,106-114`; `test_timeline.py:117-124` | PASS |
| 5 | Next planting = max(ready, window opening) | `timeline.py:287-337`; `test_timeline.py:184-215` | PASS |
| 6 | Next-season window rolls forward within limit | `branch_expander.py:493-674`; `test_branch_expander.py:223-311` | PASS |
| 7 | Latest plausible label; earliest retained; clip exposed | `timeline.py:307-337`; `test_timeline.py:197-209` | PASS |
| 8 | Waiting partial vs complete; total = prep + waiting | `timeline.py:592-602`; `test_timeline.py:248-269` | **FAIL** — clip zeroes latest; total below prep; 11-day clip + limit 5 -> partial, not exceeds. |
| 9 | Exactly 3 crops / 2 transitions; no 3rd-to-first claim | `branch_expander.py:138-229`; `test_branch_expander.py:54-69` | PASS |
| 10 | Rotation all-path repeats caution, never block | `rotation.py:25-31,47-95`; `test_rotation.py:38-60` | PASS |
| 11 | Legume = potential BNF, not guaranteed N | `rotation.py:32-45,111-119`; `test_rotation.py:72-82` | PASS |
| 12 | §14.4 ordered crop/window branches; duplicate IDs fail | `branch_expander.py:249-310,932-974`; `test_branch_expander.py:100-165` | PASS (flagged, not raised) |

## Part B — provenance
- Duration only profile `variety_duration_min/max_days` (CSV or labeled synthetic); prep only caller/synthetic `preparation`/`preparation_lookup`; blank `turnaround_*` never read; `max_waiting_days` only caller, default `None`; no numeric defaults or invented data.
- Status codes are implementation-defined; no crop-ID/name branch (source scan/test); test prep 7/10 and soil 0/0 are `synthetic://`. Real-data smoke used read-only CSV; `Data/` untouched.
- Low: rotation `source_ids=["rotation_family_rule"]` is a field label, not a CSV source column; `nursery_age_days` is reported without `seedling_age_*` source IDs.

## Part C — verdict
Fixes 1–3: **PASS** (next-season roll, all-path rotation, uniqueness). **E6 milestone: FAIL.**
Remaining: (1) §10.4 `timeline.py:592-602` — reviewer smoke (prep 7–10) has 30 transitions with total < prep; example `aman->mustard->aman` t2 total {5,7} vs prep {7,10}, waiting {0,0}; regression test only asserts non-negative. (2) `_transition_ok` (`branch_expander.py:977-984`) ignores `next_planting.status`; 1 of 78 caution transitions passes, and a synthetic all-candidate branch is emitted; require `next_planting.status == "pass"`. (3) Low: docs omit `FAMILY_REPEAT_IN_PATH`/`matched_positions`.
Full suite **181 OK**; E6 focused **18+8+19=45 OK**; reviewer mutation **6/6**. No code/test edits.
