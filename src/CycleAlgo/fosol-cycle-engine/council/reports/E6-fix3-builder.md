# E6 fix 3 - crop-sequence uniqueness

Rule decision (v1.md:602, §14.4): a deterministic `branch_id` is "unique for the selected request and ordered crop/window choices." The same crop sequence with different ordered windows is TWO branches with distinct branch_ids, not one; duplicate crop sequences are reported without collapsing them; duplicate branch_ids are a hard failure.

Failing TDD before fix: `KeyError: 'uniqueness'`; `Ran 1 test in 0.049s`, `FAILED (errors=1)`. Synthetic `check_branch_uniqueness` tests also failed with `AttributeError` before implementation.

Fix (`src/branch_expander.py`):
- Added `check_branch_uniqueness(branches)` with `branch_count`, `branch_ids_unique`, `duplicate_branch_ids`, `sequence_count`, `duplicate_sequences` (each `crop_ids`, `branch_ids`, `window_keys`), and `rule`.
- Added `uniqueness` to `expand_branches` output after the branch cap; no branch collapse/dedupe.
- Added 3 tests (contract key/counts, same sequence/different windows, duplicate branch_id) and a short `docs/TIMELINE.md` uniqueness note.

Full suite: `python -X utf8 -m unittest discover -s tests -v` -> `Ran 181 tests in 0.837s`, `OK`; focused E6 18+8+19=45 OK.

Smoke (`2026-11-06`, max 365): 420 branches, 15 exclusions (all `WINDOW_GEOGRAPHY_UNKNOWN`), 0 candidate/420 conditional.
Uniqueness: 420/420 unique branch_ids and sequences; `branch_count=420`, `sequence_count=420`, `branch_ids_unique=true`, `duplicate_branch_ids=[]`, `duplicate_sequences=[]`. Old: no check; new: pass.

No count/status/exclusion change; test count 178 -> 181 (+3). No commits; only `src/branch_expander.py`, `tests/test_branch_expander.py`, short `docs/TIMELINE.md` note.
