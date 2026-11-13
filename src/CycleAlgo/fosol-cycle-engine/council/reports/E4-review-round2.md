# E4 round-2 review — fixes + mutation check

**Verdict: PASS.** Both medium findings and the reported low cluster are fixed; 5/5 mutations killed; source restored byte-for-byte.

**Fix verification**
- Finding 1: `_build_candidate` separates `missing_preferred` from `late_status` (`src/calendar_evaluator.py:310-329`); preferred/future use only start/end (`:161-239`); unresolved post-preferred late returns `WINDOW_LATE_END_UNRESOLVED` (`:266-276`). Tests `tests/test_calendar.py:183-215` (Boro late=02-29: pass/future/unresolved/leap-late).
- Finding 2: late must be `late_end > end` and `< next_start`, else `WINDOW_DATA_INCONSISTENT` profile-wide (`:316-329`, `:119-126`). Tests `:420-460` (next-year, cross-year Dec, late-before-end).
- Low cluster: `WINDOW_SOURCE_MISSING` (`:49-55`; test `:492-501`); normalized-only MM-DD (`:57-61`, `:534-539`; test `:477-490`); `WINDOW_PRECISION_MISSING` (`:216-247`; test `:462-475`); dead late-missing path removed (`:78-82`; test `:536-552`); Dec31/Jan1 policy documented/pinned (`:10-13`, `:358-361`; test `:503-521`); boundary/limit/status tests `:217-305`.
- Full suite: `python -X utf8 -m unittest discover -s tests -v` -> `Ran 116 tests in 0.082s` / `OK`; focused E4 -> `Ran 30 tests in 0.006s` / `OK`.

**Mutation check** (backup `%TEMP%\opencode\e4_calendar_backup.py`; SHA-256 `44a9b003bf069726b869e135d79844415fc066a0c6bdad524dff1e33f6828bef`; all rc=1)
| mutation | failing test | restored hash OK |
|---|---|---|
| `if proposed <= end` -> `<` (`:215`) | `test_aman_preferred_window_passes_at_both_boundaries` | yes |
| `if proposed <= late_end` -> `<` (`:279`) | `test_boro_boundary_edges` | yes |
| cross-year `+1` -> `+0` (`:307`) | `test_boro_after_late_support_is_unsupported` | yes |
| `waiting_days <= limit` -> `<` (`:187`) | `test_waiting_limit_zero_and_boro_exact_boundary` | yes |
| `if not source_ids` -> `if False` (`:49`) | `test_missing_sources_is_unknown` | yes |

**Clean check:** source SHA-256 before/after `44a9...8bef`; backup SHA-256 same; `git diff --stat -- src/calendar_evaluator.py` empty (file untracked), `git status` shows `?? src/calendar_evaluator.py`; `git diff --no-index` source vs backup exit 0; focused 30/30 after restore. No mutation left; no test added.

**Residual low:** a loader-normalized invalid late (top-level `None`, `data_quality.unclear_fields`) is treated as absent, so a post-preferred date gives `OUTSIDE_SUPPORTED_WINDOW` rather than `WINDOW_LATE_END_INVALID`; no current profile has it.
No `DataNEVERBEUSED` access; no permanent source/test edits.
