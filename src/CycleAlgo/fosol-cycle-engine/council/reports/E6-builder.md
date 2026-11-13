# E6 - Builder: timeline, preparation, waiting, rotation, 3-crop expansion

Files: `src/timeline.py` (`build_crop_timeline`, `calculate_next_planting`, `calculate_waiting`, `evaluate_waiting_limit`), `src/rotation.py` (`evaluate_rotation`), `src/branch_expander.py` (`expand_branches`), tests 18+7+15=40, `docs/TIMELINE.md`.

Formulas: harvest = planting endpoint + duration endpoint; ready = harvest + prep endpoint; next = max(ready, window start); waiting = next - ready; total = next - harvest. Ranges stay paired, never averaged; latest next dates clip at the supported-late end. Waiting min/max is sorted, so clipping cannot create a negative interval.

Evidence: duration unverified by default -> conditional / `DURATION_REFERENCE_UNRESOLVED`; transplanted crops never add seedling age (`NURSERY_AGE_NOT_ADDED`). Preparation only from caller lookup, never blank CSV turnaround; missing prep leaves prep/ready/waiting `None` with `PREPARATION_EVIDENCE_MISSING`, never 0. Limit is product policy: `not_configured`/`unknown`/`within`/`partial`/`exceeds`.

Rotation: same family -> `caution`/`SAME_FAMILY_REPEAT` (never blocking); different -> `pass`/`FAMILY_DIVERSIFIED`; legume presence is potential BNF only; CSV text advisory (`rule_machine_readable=false`, source `rotation_family_rule`). No third-to-first claim.

Real data smoke (`2026-11-06`, max_waiting 365): 295 branches, 56 exclusions, all conditional, first `boro_brri_dhan28 -> aman_br11 -> boro_brri_dhan28`, 3 crops / 2 transitions.

Command: `python -X utf8 -m unittest discover -s tests -q`
```text
Ran 176 tests in 0.493s

OK
```
New tests 40 (budget 35-50); no crop-specific branches; `Data/` untouched.





