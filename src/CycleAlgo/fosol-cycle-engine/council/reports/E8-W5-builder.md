# E8 W5 - preference ranking

Delivered `rank_branches(branches, preference, profiles=None)` in `src/branch_metrics.py`; added 11 ranking tests in `tests/test_branch_metrics.py` (264 total suite).

Preferences validated against all six names; unknown raises `ValueError`. Candidate and conditional groups stay separate; any other branch status goes to `excluded` and is never revived. No weighted score.

Fastest completion ranks by `completion_days.max` ascending with branch_id tie-break; entries include completion range and reasons/cautions; top-two overlap adds a note; empty candidate group is noted. Diversity ranks by `distinct_family_count` descending with legume presence shown separately and product-convention wording. Cost, net return, upfront cash, and irrigation dependence are all unranked with reasons/missing evidence and `no_winner=true`; missing completion is unranked, not favorable.

Full suite: `python -X utf8 -m unittest discover -s tests -q` -> `Ran 264 tests in 1.446s`, `OK`.
Focused W5: `Ran 11 tests`, `OK`.
E6 smoke (`2026-11-06`, max 365): 420 branches, 0 candidate / 420 conditional, 15 exclusions; unchanged.

No E6/E7/W1-W4 behavior changed; JSON and no-crop-ID checks pass; no commits; only `src/branch_metrics.py` and `tests/test_branch_metrics.py`.
