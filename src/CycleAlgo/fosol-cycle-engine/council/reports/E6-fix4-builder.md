# E6 fix 4 - waiting/total pairing for clipped latest

Defect: §10.4. A clipped latest next planting was paired with the latest ready/harvest, so total could fall below prep (30 transitions, e.g. `aman->mustard` t2 total {5,7} vs prep {7,10}). Failing before fix (`test_preparation_interval_is_lower_bound_for_total`): `AssertionError: 30 != 0`; clipped test also raised `KeyError: 'latest_invalid'`.

Fix: `calculate_waiting(..., latest_invalid=False)` auto-detects a clipped latest; returns waiting/total `{min:<int>,max:null}` and `latest_invalid=true`, keeping only a valid earliest pairing. `evaluate_waiting_limit` accepts `max=null`: min>limit -> `exceeds`, min<=limit -> `partial`. `_transition` exposes `latest_invalid`, adds caution/missing `latest_waiting_total`, keeps `NEXT_PLANTING_LATEST_CLIPPED`/`latest_clipped=true`. `_transition_ok` rejects `latest_invalid` or null waiting/total max; synthetic latest-invalid branch is conditional. `docs/TIMELINE.md` updated.

Full suite: `python -X utf8 -m unittest discover -s tests -v`
```text
Ran 186 tests in 0.980s

OK
```
Focused E6: `test_timeline` 20, `test_rotation` 8, `test_branch_expander` 22 = 50, all OK. Test count 181 -> 186 (+5: 2 timeline, 3 branch).

Smoke (`2026-11-06`, max 365):
- No prep: 420 branches, 15 exclusions, 0 candidate/420 conditional; unchanged.
- Prep 7-10: prior 30 total<prep -> **0**; 419 branches/16 exclusions unchanged (no branch/exclusion change); 30 `latest_invalid` transitions; 78 `next_planting.caution` transitions, 0 pass `_transition_ok`; 0 candidate; uniqueness 419/419.
- Clipped example `aman->mustard` t2: prep {7,10}, waiting {0,null}, total {7,null}, `latest_invalid=true`, `NEXT_PLANTING_LATEST_CLIPPED`, `latest_clipped=true`; total min 7 >= prep min 7.

No count change beyond test count and 30 bad -> 30 null-latest; no candidate/exclusion change. No commits; only `src/timeline.py`, `src/branch_expander.py`, both E6 test files, and `docs/TIMELINE.md`.
