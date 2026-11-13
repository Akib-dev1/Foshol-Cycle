# E6 — timeline/preparation/waiting/rotation/3-crop: code review

**Verdict: FAIL.** Full suite green and 5/5 chosen mutations killed, but §11 rotation and §10.3 next-window resolution have real defects.
Full `python -X utf8 -m unittest discover -s tests -v`: `Ran 176 tests in 0.521s`, `OK` (exit 0).
Focused E6 (`test_timeline.py`/`test_rotation.py`/`test_branch_expander.py`): `Ran 18/7/15 tests`, all `OK` (40 total).

## Adversarial matrix
Duration pairing/missing/transplant, prep `None` vs `0` vs synthetic range, next planting before/at/after window open, late-end clip vs exclude, waiting exact/partial/exceeds/`None`, 3 crops/2 transitions, blocked paths, deterministic IDs/order, JSON: PASS.
Real expansion: 295 branches, 56 exclusions, all conditional; JSON 12,174,010 bytes; no 4th crop; IDs unique and insertion-order independent.

## Mutation gate (5/5 killed; SHA-256 restored)
| mutation | failing E6 test |
|---|---|
| duration pairing | `test_harvest_range_propagates_both_duration_endpoints` |
| prep-unknown guard | `test_missing_preparation_is_unknown_not_zero` |
| waiting `<=` -> `<` | `test_waiting_limit_statuses_are_inclusive_and_distinguish_overlap` |
| 3-crop stop (4 nodes) | `test_every_branch_has_exactly_three_crops_and_two_transitions` |
| rotation/block (`blocking=True`) | `test_same_family_is_caution_not_rejection` |

Calendar-combine precedence (`caution`/`unknown` swap) survived: no E6 test mixes statuses; a direct mixed-status check returns the correct `unknown`/`unsupported`, so this is a test gap only.
SHA-256 restored and matching backup: timeline `667714939EE2C370D30FF65A01323DC594BD9530DD92330AF14ACCAE51956FA3`; rotation `113AFD09716ACBED6661C0A23CB70DB2A8D41B6180CC9F6F27A921BEF4F3AD12`; expander `66A9616DB57FB6A03EE2D52BA5ECC41C06E5148857633E863C2741454826F75D`.

## Bugs
1. **§11 rotation misses non-consecutive family repeats.** `evaluate_rotation(maize, lentil, [boro, lentil])` -> `pass`/`FAMILY_DIVERSIFIED`, `path_length=3`, families Poaceae->Fabaceae->Poaceae; 62/295 real branches repeat family at positions 1&3 and get `pass`. `_path_profiles` also dedupes by `crop_id`, so `boro->lentil->boro` reports `path_length=2` and omits the third crop. Code: `rotation.py:25-31,51,102-118`.
2. **§10.3/§10.5 valid next-season windows excluded.** `mustard->mung->boro`, `max_waiting=365`: mung harvest 2027-05-09..22; boro next window 2027-12-25..2028-01-10 (217-230 d <=365), yet E6 excludes `OUTSIDE_SUPPORTED_WINDOW` citing boro's ended 2026-27 window (late end 2027-02-28). The same `mustard->mung` prefix yields six other third crops; only boro is lost. E4's single-date unsupported is correct; `_resolve_window` treats it as terminal instead of resolving the next window. A resolved future option would expose the 217-230 d gap and apply the limit, so §6.1's "never silently advance" is satisfied. Code: `branch_expander.py:411-413`.
3. Low/test gap: calendar-combine precedence has no mixed-status regression test (mutation survived); code behavior is correct.

Demo_check: N/A until E8-E9. No permanent source/test edits; `Data/` not modified (real CSV only through `load_crop_profiles`/tests).
