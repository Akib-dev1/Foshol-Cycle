# E6 fix 2 - rotation family repeats

Defect: §11. `evaluate_rotation` compared only the immediate previous family and `_path_profiles` deduped by crop_id, so `boro->lentil->boro` returned `pass`/`FAMILY_DIVERSIFIED`, `path_length=2`, missing the position-1 repeat.

Failing test before fix (`test_non_consecutive_family_repeat_is_caution`):
```text
AssertionError: 'pass' != 'caution'
Ran 1 test in 0.001s
FAILED (failures=1)
```

Fix: path = ordered prior profiles + current (duplicates preserved); `path_length`/`path_crop_ids` are positions; current family compared with all prior families. Immediate repeat -> `SAME_FAMILY_REPEAT`; non-consecutive -> `FAMILY_REPEAT_IN_PATH`; `matched_positions` lists prior matches + current position. Repeats stay cautions (`blocking=false`, no machine-readable rule); legume presence spans the whole path with unique IDs; advisory text unchanged; any missing current/prior family -> `unknown`. Tests now pass prior-only paths; new test covers boro/lentil/boro and maize/lentil/boro; path test asserts duplicate positions.

Full suite: `python -X utf8 -m unittest discover -s tests -v`
```text
Ran 178 tests in 0.820s

OK
```
Focused E6: `test_timeline` 18, `test_rotation` 8, `test_branch_expander` 16 = 42, all OK.

Smoke (`2026-11-06`, max 365): 420 branches, 15 exclusions, 0 candidate / 420 conditional; unchanged. Position-1/3 family repeats: 150 branches. Old rotation: 81 `pass`/`FAMILY_DIVERSIFIED`, 69 `caution`/`SAME_FAMILY_REPEAT`; new: 0 pass, 150 caution (81 `FAMILY_REPEAT_IN_PATH`, 69 `SAME_FAMILY_REPEAT`). Old path lengths 84x3 / 66x2; new 150x3. All 840 rotation checks: old 540 `FAMILY_DIVERSIFIED` / 300 `SAME_FAMILY_REPEAT` -> new 459 / 300 / 81 `FAMILY_REPEAT_IN_PATH`; the 81 moved are exactly the non-consecutive repeats. E6-review's 62/295 -> 150/420; the +88 is fix 1's +125 branches, not this fix. No repeat branch reports `FAMILY_DIVERSIFIED`; no branch excluded.

Only `src/rotation.py` and `tests/test_rotation.py` changed; fix 1 untouched. No commits.
