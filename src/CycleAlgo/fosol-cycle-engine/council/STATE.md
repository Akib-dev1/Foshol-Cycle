# Council State

Last updated: 2026-11-10 (E7 local-POWER outlook wired; final rerun)

## FINAL
- Algorithm complete for v1 scope. **310 tests**, `demo_check.py` PASS, 9/9 example
  contract checks PASS.
- Initial request: `partial`; 0 candidate / **295 conditional** / 56 exclusions;
  6 selectable first crops; Aman/Mung unsupported. Selected branch counts: Boro 42,
  Lentil 55, Maize 42, Mustard 54, Potato 54, Wheat 48.
- Fastest/diversity ranked within the conditional group; economics/irrigation unranked,
  `no_winner=true`; §17.16 N/A (no financial values).
- §6.2 current-season climate deferred; preparation/soil/economic evidence missing, so
  no candidate branches. Parked in `council/QUESTIONS.md` / `docs/OPEN_DECISIONS.md`.
- SMAP is context-only (`environment_context`), never status/ranking. `example_response.json`
  uses the real cached AppEEARS fixture: 24 observations, 2025-01-01T01:30Z..2025-01-03T22:30Z,
  SPL4SMGP.008 9 km/3-hourly; no token. E7 warnings all OFF.
- Waiting gaps (window-only, prep unknown): transitions n=590 min 0 / median 206 /
  max 282, >90 461, >180 340; branch totals n=295 min 0 / median 389 / max 546,
  >90 282, >180 237. No limit configured; report `E9-waiting-gaps.md`.
- Handoff examples: 1-branch `example_response.json`, 10-branch
  `example_response_first_crop_selected.json`, small states, contract checker 11/11.
- Docs: `docs/FRONTEND_HANDOFF.md`, `docs/EXPLAINER.md`, `docs/OPEN_DECISIONS.md`,
  `docs/SETUP.md`, `docs/CONTRACT.md`; examples in `examples/`.
- Server: `python -m src.server --port 8000`; `POST /api/explore`, `GET /health`.
- `v1.md` remains uncommitted; no leftover council prompt.
- E7 demo outlook wired from local POWER B (2000–2026), analysis 2000–2025, 26 seasons:
  T2M per-season mean, PRECTOTCORR per-season total, GWETTOP per-season mean
  (MERRA-2, not SMAP); min/median/max, `thresholds_applied=false`, warnings empty;
  1991–1999 excluded (local precipitation invalid 24×). All 3 crop outlooks in the
  1-branch example and 30/30 in the 10-branch example are `ok`.
- SMAP examples use the cached live-task sample: 24 observations, 2025-01-01..03 UTC;
  context-only, never current, never status/ranking.
- Inter-crop wait sensitivity (initial 180): 90 d 11 branches/5 first crops; 120 d 20/6;
  180 d 74/6; 240 d 135/6; no limit 295/6. No limit configured.
- `docs/CONNECT.md` added and linked from `README.md` and
  `docs/FRONTEND_HANDOFF.md`; SETUP corrected to local POWER 2000–2025 and server
  SMAP-context limitation.
- Fresh clone of `vv1` in a temp folder, new venv (`3.13.2`), server started from a
  different cwd (`PYTHONPATH` + `--data-dir`): health `{"status":"ok"}`, both POSTs
  `200 partial` (`0/295/56` initial; `42` selected), both live outputs contract-check
  PASS. Saved examples are trimmed (1/10 branches); docs explain the difference.
- Merge-ready checks: full suite 314, demo_check PASS, contract 11/11 PASS; `.gitignore`
  covers venv/cache/pyc/logs/tokens/local config; secret scan clean in diff and
  history; no tracked file >5 MB; Data tracked 7 files/1.05 MB.
- `main..vv1`: 51 commits, 177 files, +130,947/−1; `main` is an ancestor of `vv1`
  (fast-forward yes, no conflicts). `git status` only `M v1.md`.
- Tag: `v1-handoff` on `vv1`.
- Next: none unless sourced preparation/soil/water/economic evidence is supplied.

## Current
- E1–E5 PASS. Commits: `4711b3e`, `fc92802`, `68220d1`, `a528c26`, `8fdbd5d`.
- E3 live-verified POWER (v2.10.3, fill -999) and AppEEARS SMAP
  (`SPL4SMGP.008`, 3-hourly, 9 km, fill -9999).
- E6 fix 1 PASS: next-season windows roll forward within `max_waiting_days`.
  Smoke (`2026-11-06`, max 365): 295 -> 420 branches, 0 candidate / 420 conditional,
  exclusions 56 -> 15 (all `WINDOW_GEOGRAPHY_UNKNOWN`), Aman 0 -> 62.
  Reports `E6-fix1-builder.md`, `E6-fix1-review.md`. Commit `5f6cef0`.
- E6 fix 2 PASS: rotation compares all prior positions; 150 position-1/3 family-repeat
  branches now caution (was 81 pass / 69 caution), 0 `FAMILY_DIVERSIFIED`; total branches
  still 420, exclusions still 15. Reports `E6-fix2-builder.md`, `E6-fix2-review.md`.
- E6 fix 3 PASS: sequence/branch-ID uniqueness check added; 420 branches, 420 unique
  sequences/IDs, 0 duplicates; branches not collapsed. Reports `E6-fix3-builder.md`,
  `E6-fix3-review.md`.
- E6 fixes 4–5 PASS: Option A null-latest (waiting/total latest null, `latest_invalid`,
  earliest retained, `total >= prep` invariant) and `_transition_ok` requires
  `next_planting.status=="pass"`. 187 tests; reports `E6-fix4-*.md`, `E6-fix5-*.md`.
- E6 final gate PASS: 7/7 mutations killed; no-prep 420 branches / 15 exclusions /
  0 candidate / 420 conditional; boro 55; 150 position-1/3 repeats all caution;
  uniqueness 420/420. Prep 7–10: 419/16, total<prep 30 -> 0, 30 `latest_invalid`,
  78 caution / 0 pass. Reports `E6-final-review-round2.md`,
  `E6-final-spec-integrity-round2.md`.
- E6 wording fix PASS: `_limit_error` now states product relevance cutoff, not a
  scientifically safe maximum / biological impossibility; 188 tests; smoke 420/15.
- E7 W1 PASS: `map_schedule_to_seasons` maps E6 union spans to 1991–2025, 90%/100%
  coverage, cross-year/leap handling, `last_complete_data_date` parameter. 201 tests;
  6/6 mutations; E6 smoke 420/0/420/15.
- E7 mustard audit: raw 29/35 was a local CSV unit bug; 1990 file `PRECTOTCORR`
  is 24× the live API/2000 file. Corrected 1/35 (2023 season, 2024-01-21 70.23 mm/day).
  Wheat warnings 35/35 (weak), mustard 1/35 (weak). All warning flags default OFF;
  statistics only until stage-specific windows/evidence. Report `E7-mustard-audit.md`.
- E7 W2 PASS: temperature pooled stats (≥90%, linear IQR), precipitation per-season
  totals (100% days, mm), generic warning engine with per-indicator text, flags default
  OFF. 216 tests; 7/7 mutations; E6 smoke 420/0/420/15. Reports `E7-W2-*`.
- E7 W3 PASS: `build_outlook` schema, exact em-dash label, status ok/partial/unavailable,
  data-sourced version/fill/missing, indicator `source_ids`, union-span notes. 224 tests;
  8 W3; 2/2 contract mutations. E7 total 36 tests vs 20–30; extra cases cover schema,
  status, source refs, unavailable nulls (documented reason). Reports `E7-W3-*`.
- E7 final gate PASS: spec/integrity, 224 tests, E6 smoke 420/0/420/15. Warnings OFF
  (wheat 35/35 hidden; mustard corrected 1/35 held); no SMAP/soil/water/prep/duration
  added; E7 historical-only. Report `E7-final-spec-integrity.md`.
- E8 preflight guard PASS: `tests/test_local_power_data.py` locks the 24× 1990
  PRECTOTCORR and the 2026-09 stale-B drift; live fixture proves A/24 = API.
  225 tests; E6 smoke 420/0/420/15. Reports `E8-preflight-guard*.md`. Commit `2e01a65`.
- E8 preflight delivered (`council/reports/E8-preflight.md`): all economic inputs
  missing; defaults in use: completion+diversity only, economics unavailable,
  completion endpoints A, irrigation display-only.
- E8 W1 PASS: `calculate_completion_time` decision A, unavailable/null on missing,
  malformed, or reversed ranges; 232 tests; 5/5 mutations; E6 smoke 420/0/420/15.
  Reports `E8-W1-builder.md`, `E8-W1-review.md`.
- E8 W2 PASS: `calculate_diversity_metrics` family count/repeat proxy, legume
  presence with profile fallback; missing -> unknown/null; 240 tests; 5/5 mutations.
  Reports `E8-W2-builder.md`, `E8-W2-review.md`.
- E8 W3 PASS: `build_resource_metrics` keeps cash/irrigation/labor/equipment separate;
  cash/labor/equipment unavailable/null; irrigation context-only/unranked; no combined
  score or summed volume; 246 tests; 5/5 mutations. Reports `E8-W3-*`.
- E8 W4 PASS: `build_economics_metrics` all monetary metrics unavailable/null;
  reference yields context-only; no price/cost/cash-flow values; 253 tests; 5/5
  mutations. Reports `E8-W4-*`.
- E8 W5 PASS: `rank_branches` candidate/conditional groups separate, blocked excluded,
  fastest/diversity ranked, economics/irrigation unranked/no winner, missing metric
  unranked, deterministic ties; 264 tests; 5/5 mutations. Reports `E8-W5-*`.
- E8 completion revision PASS: corner form, both realizations, 300-seed property test,
  enumeration fallback with negative guard, min<=max all 420, no
  `COMPLETION_RANGE_INVALID` unranked, fastest 420/420 conditional. 271 tests; E6 smoke
  420/0/420/15. Reports `E8-W1-revision-*.md`.
- E8 final PASS: real fastest/slowest realization range (example 655..682 with dates),
  independent tightness all 420, 300-sample exact min/max, prep-known distinction
  (60..99 vs B 60..129), enumeration fallback, fastest 420/420; 274 tests; 49 E8
  (+9 for user-requested realization/tightness tests); §17.16 N/A.
  Report `E8-final-spec-integrity-realization.md`.
- E9 initial-wait split PASS: `max_initial_wait_days=180` configurable, default None;
  roots use initial only, transitions use max_waiting only; `initial_wait_days` per
  branch; boundary 179/180/181. 275 tests. Counts 420/295/358 as above.
  Reports `E9-initial-wait-builder.md`, `E9-initial-wait-review.md`.
- Policy: `council/TESTING_POLICY.md` (budgets, fault log, mutation check, <30-line reports,
  demo_check at E8–E9).

## Done
- Step 0 setup: dirs, checklist, state.
- E1 crop-profile loader: 14 tests. Commit `4711b3e`.
- E2 request validation + error contract: 18 new tests. Commit `fc92802`.
- E3 environmental loader: 54 new tests. Commit `68220d1`.
- E4 calendar evaluator: 30 new tests; compact gate 5/5 mutations. Commit `a528c26`.
- E5 soil/land + water: 20 new tests; 5/5 mutations. Commit `8fdbd5d`.
- E6 timeline/prep/waiting/rotation/3-crop expansion PASS: 187 tests total.
  Fixes: next-season roll, all-path rotation repeats, sequence uniqueness,
  Option A null-latest, candidate `next_planting` pass guard.
- E7 W1 season mapping PASS: 13 focused tests, 201 total; 6/6 mutations; E6 smoke
  unchanged. Reports `E7-W1-builder.md`, `E7-W1-review.md`.
- E7 W2 indicators PASS: 15 focused tests, 216 total; 7/7 mutations; E6 smoke unchanged.
  Reports `E7-W2-builder.md`, `E7-W2-review.md`.
- E7 W3 outlook assembler PASS: 8 focused tests, 224 total; contract mutations killed.
  Reports `E7-W3-builder.md`, `E7-W3-review.md`.
- E7 final PASS: 224 tests; E6 smoke unchanged; warnings OFF; E7 36 tests (+6 budget,
  documented). Next E8.
- Entry points:
  - `src/crop_profiles.py` -> `load_crop_profiles(path)`
  - `src/request_validation.py` -> `validate_explore_request(payload, known_crop_ids)`
  - `src/error_contract.py` -> `build_error_response(exc)`, `http_status_for_error(exc)`
  - `src/power_api.py` -> `fetch_power_daily`, `normalize_power_response`
  - `src/smap_api.py` -> `fetch_smap_point`, `parse_appeears_csv`
  - `src/environment.py` -> `load_environment`, `load_power_environment`, `load_smap_environment`
  - `src/environment_cache.py` -> `EnvironmentCache`, `build_cache_key`
  - `src/calendar_evaluator.py` -> `evaluate_calendar_fit`
  - `src/soil_water.py` -> `evaluate_soil_fit`, `evaluate_water_fit`, `evaluate_soil_water`
  - `src/timeline.py` -> `build_crop_timeline`, `calculate_next_planting`, `calculate_waiting`
  - `src/rotation.py` -> `evaluate_rotation`
  - `src/branch_expander.py` -> `expand_branches`

## Blocked / must ask user
- Preparation times: `turnaround_days_*` blank for all 8 crops -> timing unknown; no zero.
- Max waiting limit, local soil evidence, sequence restrictions, costs/yields/prices:
  remain `unknown`/`null`/"Economic estimate unavailable" unless supplied.
- Duration reference point preserved but unconfirmed.
- AppEEARS token expiry is operational (48h); code raises a clear rerun hint.
- **BLOCKED:** `max_initial_wait_days` for E9/demo not decided. Options: 365
  (current smoke, test-only), 180, 90, or None (future first crops unknown/unranked).
  Engine default remains None. Do not bake 365 into the product.
- E9 must build/run `scripts/demo_check.py` before any commit (hard gate).
- Candidate group is empty (0/420); present conditional branches with evidence reasons
  and an explicit “no candidate branches” state. Cause: prep unknown, soil unknown,
  water caution/unknown, duration reference unresolved on all 1260 crop nodes.
- §17.16 N/A until sourced economics; all monetary metrics unavailable by design.

## Standing notes
- `v1.md` is modified/uncommitted user work; source of truth, do not commit/revert.
- Never touch `Data/DataNEVERBEUSED/`; `Data/` read-only.
- Python 3.13.2, stdlib only; one shared evaluator; no crop-specific branches.
- `token.txt` and `appeears_token.txt` are gitignored, never printed.

## Gate log

| Item | Builder | Code Review | Spec Audit | Integrity | Verdict | Commit |
|---|---|---|---|---|---|---|
| E1 | PASS | PASS | PASS | PASS | PASS | 4711b3e |
| E2 | PASS | PASS | PASS | PASS | PASS | fc92802 |
| E3 | PASS | PASS | PASS | PASS | PASS | 68220d1 |
| E4 | PASS | PASS | PASS | PASS | PASS | a528c26 |
| E5 | PASS | PASS | PASS | PASS | PASS | 8fdbd5d |
| E6 fix 1 | PASS | PASS | PASS | PASS | PASS | 5f6cef0 |
| E6 fix 2 | PASS | PASS | PASS | PASS | PASS | f867dd5 |
| E6 fix 3 | PASS | PASS | PASS | PASS | PASS | 9b99cc1 |
| E6 final | PASS | PASS | PASS | PASS | PASS | 609cdf0 |
| E7 W1 | PASS | PASS | PASS | PASS | PASS | 8e2f0d3 |
| E7 W2 | PASS | PASS | PASS | PASS | PASS | 1fafb61 |
| E7 W3 | PASS | PASS | PASS | PASS | PASS | cff97bc |
| E7 final | PASS | PASS | PASS | PASS | PASS | d454b96 |
| E8 guard | PASS | PASS | PASS | PASS | PASS | 2e01a65 |
| E8 W1 | PASS | PASS | PASS | PASS | PASS | 7c45cbb |
| E8 W2 | PASS | PASS | PASS | PASS | PASS | 6495a4d |
| E8 W3 | PASS | PASS | PASS | PASS | PASS | 4b11246 |
| E8 W4 | PASS | PASS | PASS | PASS | PASS | cae196a |
| E8 W5 | PASS | PASS | PASS | PASS | PASS | 30927f7 |
| E8 W1 rev | PASS | PASS | PASS | PASS | PASS | d0a7e8d |
| E8 final | PASS | PASS | PASS | PASS | PASS | 1de054c |
| E9 initial wait | PASS | PASS | PASS | PASS | PASS | e887489 |
| E9 | PASS | PASS | PASS | PASS | PASS | 6af889f |
| E10/E11 | PASS | PASS | PASS | PASS | PASS | 6af889f (examples trim 8664601) |
