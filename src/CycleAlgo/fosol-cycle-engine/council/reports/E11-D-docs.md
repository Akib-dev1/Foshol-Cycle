# E11-D — docs, setup, small-state examples

Wrote `docs/FRONTEND_HANDOFF.md` (start/curl, request fields, response/null fields, UI states, comparison/timeline fields, must-nots), `docs/EXPLAINER.md` (295/56 initial, 420/365/365 smoke, 655..682, unavailable evidence, five reviewer Q&As), `docs/OPEN_DECISIONS.md`, and `docs/SETUP.md` (Python 3.11+, stdlib only, CSV path, server config, env names, Rajshahi limits, SMAP helper).
Added real-engine examples: unsupported district, no options (`2026-08-01`, initial limit 0), data unavailable (`profiles={}`), invalid input, and synthetic SMAP context (one-branch cap; status/ranking equal to unavailable). Main examples untouched.
Counts verified: initial **0 candidate / 295 conditional / 56 exclusions**; 365/365 **420 / 0 / 420 / 15**; selected boro **42 / 0 / 42 / 8**.
Server smoke: `GET /health` -> `{"status": "ok"}`; `POST /api/explore` -> 200 `partial`, 0 candidate / 295 conditional / 56 exclusions.
Contract checker (real output):
```text
PASS examples\example_response_unsupported_district.json
PASS examples\example_response_no_options.json
PASS examples\example_response_data_unavailable.json
PASS examples\example_error_invalid_input.json
PASS examples\example_response_smap_context.json
PASS examples\example_response_initial.json
PASS examples\example_response.json
```
No Data changes; no code/test edits; no commits. `scripts/demo_check.py` is absent, not run.
