# E9–E11 — final spec + integrity audit
Scope: `src/explore.py`, `src/api.py`, `src/server.py`, `scripts/contract_check.py`, examples, docs, E9–E11 reports; `v1.md` §14.3–14.5/§12–13/§6.1/§10.4; `DECISIONS.md`, `QUESTIONS.md`.
## Part A — rule -> code/test -> verdict
| # | Rule | Code / test | Verdict |
|---|---|---|---|
| 1 | Request limits, assumptions 180 product policy, ranking `initial_wait_days`, branch IDs exist, 179/180/181 | `explore.py:64-170`; `branch_metrics.py:551-559`; `test_explore.py:188-199,255-263,370`; `test_branch_expander.py:321-377` | PASS |
| 2 | Every crop option and branch node has deferred `climate`; missing `current_season_climate_exposure`; docs/QUESTIONS/OPEN use same ID | `explore.py:37-45,325-334,638`; `test_explore.py:244-252,433-446`; docs verified | PASS |
| 3 | Economics unavailable null/scenarios empty; contract checker rejects zeroed unavailable values | `branch_metrics.py:245-338`; `contract_check.py:39-59`; mutation probe | PASS |
| 4 | Status precedence/current partial/no-candidate/null serialization/400/500/no stack | `explore.py:66-127,445-492`; `api.py:9-36`; `server.py:74-86`; demo/examples | PASS |
| 5 | SMAP context exact 9 km/3-hourly/SPL4SMGP.008; unavailable warning; no status/ranking effect; out of E7 | `explore.py:627-691`; demo SMAP equality; example | PASS |
| 6 | Four stale examples regenerated with request limits; populated examples have ranking initial/climate; empty unsupported/data examples have empty options by design; handoff line fixed; all prior findings resolved | regenerated examples; `FRONTEND_HANDOFF.md:205-207`; checker | PASS |
| 7 | Full suite 310; `demo_check` PASS; all 7 example contract checks PASS | real runs | PASS |
## Part B — provenance
- 180: user decision; 365/365: test-only smoke; 1991–2025: configured default; 9 km/3-hourly/SPL4SMGP.008: official docs; 64 KiB/8000/CORS: implementation-defined; counts/655..682: engine.
- Warning thresholds 30/15/50 are config-only, all OFF, no sourced local rule; keep off. No invented prices, yields, costs, endpoints, SMAP data, Data changes, or code/test edits.
## Part C — verdict
**PASS** E9–E11. Request/ranking initial wait, deferred climate ID, economics null/scenarios, status/error handling, SMAP context-only, regenerated examples, and docs all pass.
Full suite **310 OK**; `demo_check` **PASS**; 7/7 examples **PASS**. No blocking remaining items; warning thresholds remain config-only/off.
