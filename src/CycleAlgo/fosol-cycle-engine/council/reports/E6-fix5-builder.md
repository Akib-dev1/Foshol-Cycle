# E6 fix 5 - caution next-planting transitions cannot be candidates

Defect: `_transition_ok` checked calendar/waiting/latest_invalid/null but omitted `next_planting.status`, so a caution transition could yield a candidate branch.

Failing TDD before fix (`test_caution_next_planting_transition_is_conditional`): `AssertionError: True is not false`; `Ran 1 test in 0.001s`, `FAILED (failures=1)`. Control all-pass transition -> candidate passed.

Fix (`src/branch_expander.py`): `_transition_ok` now returns false unless `transition["next_planting"]["status"] == "pass"`, before the existing calendar/waiting/latest_invalid/null checks. Added the synthetic caution test and control; existing latest-invalid test fixture now supplies `next_planting.status="pass"`; fix4 null-latest behavior unchanged.

Full suite: `python -X utf8 -m unittest discover -s tests -v` -> `Ran 187 tests in 0.961s`, `OK`; focused E6 20+8+23=51 OK.

Smoke (`2026-11-06`, max 365):
- No prep: 420 branches, 15 exclusions, 0 candidate/420 conditional; 0 caution transitions (all 840 `next_planting.status="unknown"`), 0 pass `_transition_ok`; unchanged.
- Prep 7-10 (source of the 78): 419 branches, 16 exclusions, 0 candidate/419 conditional; 78 `next_planting.status="caution"` transitions, 0 now pass `_transition_ok`; 376 pass-status transitions still pass. The 419/16 and 78 are the fix4 baseline; no count change from fix5.

No branch count/status/exclusion change. Test count 186 -> 187 (+1). No commits; only `src/branch_expander.py` and `tests/test_branch_expander.py`.
