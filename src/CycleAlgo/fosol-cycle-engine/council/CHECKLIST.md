# Council Checklist — Fosol-Cycle v1 Engine

Source of truth: `../v1.md`. Governor ticks a box only after Builder, Code Reviewer,
Spec Auditor, and Integrity Auditor all report PASS for the item that proves it.

## A. Spec §17 — minimum automated cases (17)

- [ ] 17.1 Preferred planting window passes at both boundaries.
- [ ] 17.2 A documented late planting date becomes conditional.
- [ ] 17.3 A date beyond documented support is not presented as a normal candidate.
- [ ] 17.4 Missing late-window support is not treated as a biological impossibility claim.
- [ ] 17.5 Cross-year windows and leap-year dates resolve correctly.
- [ ] 17.6 Duration ranges propagate rather than collapsing silently to an average.
- [ ] 17.7 Missing preparation evidence makes timing conditional/unknown.
- [ ] 17.8 Waiting limits distinguish partial range overlap from complete exclusion.
- [ ] 17.9 Missing soil or irrigation evidence does not automatically pass or reject a crop.
- [ ] 17.10 API missing values, poor quality, and failed requests cannot create favorable results.
- [x] 17.11 Incomplete historical crop periods are excluded according to the declared coverage rule.
- [ ] 17.12 A branch stops at exactly three crops.
- [ ] 17.13 Unsupported districts do not inherit Rajshahi results.
- [x] 17.14 Preference changes cannot revive blocked branches.
- [x] 17.15 Missing economic inputs cannot win cost or return rankings.
- [ ] 17.16 Financial units are converted correctly and transition costs are counted once.
      N/A until sourced economics; all monetary metrics are unavailable by design.
- [x] 17.17 No supported path returns an honest empty/insufficient-evidence result.

## B. Spec §14.6 — required handoff artifacts (7)

- [x] 14.6.1 Runnable algorithm code with a short command showing how to execute it.
- [x] 14.6.2 Documented callable entry point and the HTTP endpoint if hosted separately.
- [x] 14.6.3 Finalized JSON request/response contract, every nested field documented.
- [x] 14.6.4 `example_request.json` and matching complete, schema-consistent `example_response.json`
      from the implemented algorithm, including all three crops when a first crop is selected.
- [x] 14.6.5 Small saved examples for initial options, conditional branches/missing economics,
      no supported paths, unsupported district, and invalid input.
- [x] 14.6.6 Runnable checks proving valid JSON, consistent required keys/statuses, existing
      branch/source ID references, and full paths with exactly three crops and two transitions.
- [x] 14.6.7 Setup/environment instructions naming required credentials without secrets,
      supported districts, data limitations, and API startup configuration.

## C. Spec §20 — acceptance criteria (8)

- [x] 20.1 Select Rajshahi from the Bangladesh map or district list.
      (Algorithm side only: `district_id=rajshahi` is accepted and supported; map UI out of scope.)
- [x] 20.2 Understand the planting-date assumption and environmental data freshness.
- [x] 20.3 See why first crops are candidates, conditional, or outside support.
- [x] 20.4 Choose a first crop and explore two subsequent crops with actual timeline ranges.
- [x] 20.5 See preparation, waiting, and excluded-path explanations.
- [x] 20.6 Compare complete branches by supported time/resource/economic/diversity metrics.
- [x] 20.7 Select a preference and understand why a branch is highlighted.
- [x] 20.8 Identify missing evidence and distinguish historical outlooks from forecasts or guarantees.

## D. Mission Definition of Done extras

- [x] D.1 Contract check: responses serialize as valid JSON; referenced branch/source IDs exist;
      every full path has exactly three crops and two transitions.
- [x] D.2 `docs/OPEN_DECISIONS.md` lists unresolved §19 decisions; results surface them as
      missing evidence, not silent defaults.
- [x] D.3 Final Integrity Auditor report with zero unsourced numbers, strings, endpoints, or defaults.
- [x] D.4 Full test suite passes, with real command output pasted in the gate report.

## E. Build-order milestones (spec §18 + mission Step 1)

- [x] E1 Crop-profile loader and normalizer (no guessed fields).
- [x] E2 Request validation and error contract (§14.2, §14.3).
- [x] E3 Environmental loading, caching, missing-value handling (§15).
- [x] E4 Calendar evaluator (§6.1, §17.1–5).
- [x] E5 Soil/land and water checks (§7, §8).
- [x] E6 Timeline, preparation, waiting, 3-crop expansion (§10, §11).
- [x] E7 Historical seasonal replay with coverage rules (§9).
- [x] E8 Metrics, economics, rankings, preferences (§12, §13).
- [x] E9 Response envelope, status precedence, warnings (§14.3, §14.4).
      Initial wait 180 decided; demo_check.py passed before commit.
- [x] E10 Thin HTTP wrapper `POST /api/explore`.
- [x] E11 Handoff artifacts and docs (§14.6).

## F. Testing-policy amendment (2026-11-06)

- [x] Policy recorded in `council/TESTING_POLICY.md`; reports now < 30 lines.
- [x] E4 fault log + test grouping produced; no test deleted before the mutation check.
- [x] E4 mutation check: 5 critical lines, each mutation caught, code restored (hash verified).
- [x] E5–E11 follow the per-function light gate and per-milestone full gate.
- [x] E8–E9 demo safety suite + `scripts/demo_check.py`; rerun at every later milestone.
      **E9 hard gate: build and run before any E9 commit; do not defer again.**
- [ ] E1–E3 budget overage reviewed (E1 14 vs 8–12; E3 54 vs 12–20) — deferred, not blocking.
