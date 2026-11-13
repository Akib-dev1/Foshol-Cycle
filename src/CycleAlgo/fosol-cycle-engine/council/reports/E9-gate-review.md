# E9 gate review (final)

**Verdict: PASS.**
Full suite: `Ran 310 tests in 8.631s`, `OK`. Demo: PASS.
Examples: 9/9 PASS (2 requests, 6 responses, 1 error).
Source unchanged since the 5/5 mutation run: `explore.py F4DD...6036`, `branch_metrics.py 45DA...DD81`, `calendar_evaluator.py 44A9...8BEF`, `test_explore.py 5DAF...3CFC`, `test_branch_expander.py FDC5...6EB5`, `demo_check.py 7179...4DE6`, `contract_check.py D73A...07ED`.
Verified: request limits `180`/`None` on initial/selected/unsupported/data_unavailable; ranking `initial_wait_days` matches branch values; climate checks and `current_season_climate_exposure` present in applicable responses; examples include request limit fields and ranking waits.
| mutation | failing test | clean restore (hash verified) |
|---|---|---|
| status partial -> ok | `test_demo_status_and_summary` | yes |
| economics null -> 0 | `test_economics_values_are_null_and_checker_rejects_zero` | yes |
| no-candidate message removed | `test_no_candidate_message_is_explicit` | yes |
| SMAP affects status/ranking | `test_smap_context_does_not_change_status_or_ranking` | yes |
| initial-wait 180 -> 179/181 | `test_initial_wait_boundary_is_exact` | yes |

5/5 killed; hashes restored.
No source/test/example edits or commits; pre-existing `branch_metrics.py`/`v1.md` diffs remain.
