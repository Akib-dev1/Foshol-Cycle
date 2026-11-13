# E8 W2 - diversity metrics

Delivered `calculate_diversity_metrics(branch, profiles=None)` in `src/branch_metrics.py`; added 8 diversity tests in `tests/test_branch_metrics.py` (15 total there; full suite 240).

Shape: exactly 3 crops/2 transitions; malformed -> `status="unavailable"`, null metrics, `INVALID_BRANCH_SHAPE`.

Families: case/space-normalized unique `families`, `distinct_family_count`, `family_repeat_count=3-distinct` (product proxy); basis `crop_family_count_product_convention`; `diversity_note` says not a soil-health ranking.

Legume: `legume_present` any `is_legume_n_fixing` true, `legume_crop_ids`; note potential BNF only, not guaranteed N credit. Optional `profiles` fallback resolves family/legume by `crop_id`; crop-node values win. Missing/blank family or legume flag -> `status="unknown"` with `missing_evidence`; family metrics null when family missing; legume is not defaulted false.

JSON; no crop-specific branches. Real E6 branch containing lentil/mung gives `legume_present=True` with profiles and `unknown` without profiles; profile family fallback tested. No E6 change.

Full suite: `python -X utf8 -m unittest discover -s tests -q` -> `Ran 240 tests in 1.662s`, `OK`.
E6 smoke (`2026-11-06`, max 365): 420 branches, 0 candidate / 420 conditional, 15 exclusions; unchanged.

No commits; only `src/branch_metrics.py` and `tests/test_branch_metrics.py`.
