# E10/E11 combined review
Verdict: PASS. No blocking bugs.
Full suite: `python -X utf8 -m unittest discover -s tests -v`
```text
Ran 307 tests in 8.321s
OK
```
Focused: `test_api.py` 11 tests OK; `test_explore.py` 21 tests OK.
Real server (port 0, local only): `GET /health` -> `200 {"status":"ok"}`; `POST /api/explore` initial request -> `200 partial`, branches 0, summary 0 candidate / 295 conditional / 56 exclusions, warnings include POWER/SMAP unavailable.
`python -X utf8 scripts/demo_check.py` -> `PASS` (295/56 initial; selected boro 42; SMAP isolation; determinism).
Contract checker: all 9 example files PASS, including requests, invalid-input error, and SMAP context.
Verified docs: handoff has start/curl, request/response fields, null meaning, all UI states, comparison/timeline fields, must-nots; explainer has 0/295/56, 420/365/365, 655..682 and 5 Q&A; OPEN_DECISIONS lists §6.2, preparation/evidence, warning thresholds, SMAP outlook, v1.md; SETUP has clean-clone, Python 3.11+, stdlib-only, env names without secrets, Rajshahi-only.
API/server checks: 400/415/413/404/500 generic, no stack/token, health, strict localhost/127 CORS without wildcard, local profiles, demo config 180/None, no live providers.
E6/E9 smoke explicit 365/365: 420 branches, 0 candidate / 420 conditional, 15 exclusions.
No Data changes; no permanent edits; no commits.
