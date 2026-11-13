# E6 fix 3 review - sequence uniqueness
Verdict: PASS. Bugs: none found in the requested uniqueness contract.
Rule (v1.md §14.4): "A deterministic `branch_id`, unique for the selected request and ordered crop/window choices."
Contract checks (`check_branch_uniqueness`):
- Same sequence, different windows: `branch_count=2`, `branch_ids_unique=true`, `sequence_count=1`, one `duplicate_sequences` entry with two distinct `window_keys`; not collapsed.
- Duplicate `branch_id`: `branch_ids_unique=false`, `duplicate_branch_ids=["b_000000000001"]`, one duplicate sequence report.
- Real output: 420 branches, 420 unique branch IDs, 420 unique sequences, 0 duplicate sequences; `uniqueness` is present after the cap and its rule text matches the quote.
Focused E6: 18 + 8 + 19 = 45 tests, OK. New uniqueness tests: 3/3 OK.
Full suite: `python -X utf8 -m unittest discover -s tests -v`
```text
Ran 181 tests in 1.041s
OK
```
Mutation proof (temporary only):
- Before SHA-256: `9DA45C5D58BC3EE3D91A63590DE2F862100FE6A68B349B318F6C7C31962D07CC`
- Disabled duplicate detection -> 2/3 new tests failed:
```text
AssertionError: 0 != 1
AssertionError: True is not false
Ran 3 tests in 0.050s
FAILED (failures=2)
```
- Restored SHA-256 matches `9DA45C5D...`; full suite reran OK; no mutation remains.
Smoke (`2026-11-06`, max 365): 420 branches, 15 exclusions (all `WINDOW_GEOGRAPHY_UNKNOWN`), 0 candidate / 420 conditional. No count/status/exclusion change.
Docs note matches: same sequence with different windows is two branches; duplicate IDs are a hard failure; duplicate sequences are reported, never collapsed.
No commits; only this review report added.
