# E4 fault log
Scope: E4 calendar evaluator. No code/test changes; no `Data/` access.
| Fault | Smallest test now catching it | Code guard |
|---|---|---|
| Medium 1 — optional late bound invalidated preferred/future | `test_boro_late_leap_bound_keeps_preferred_and_future_results` (L183) | Preferred/future branches precede late; unresolved only post-preferred `:266-275` |
| Medium 2 — late order/year unvalidated | `test_late_bound_order_is_validated` (L420) | Inconsistent check `:119-126`; attach/order `:316-329` |
| Low 4 — missing precision after preferred | `test_missing_precision_after_preferred_is_unknown` (L462) | `:215-219`, `:241-246` |
| Low 5 — MM-DD raw fallback | `test_mmdd_fields_use_normalized_top_level_only` (L477) | `_normalized_text` `:534-539`; reads `:59-61` |
| Low 6 — no-source pass | `test_missing_sources_is_unknown` (L492) | Source gate `:49-55` |
| Low 7 — unreachable late-missing path | No dedicated behavior test; grep verifies no `WINDOW_LATE_END_MISSING` (`test_invalid_late_text_does_not_break_preferred_or_future`, L536, covers replacement policy) | Invalid late deferred `:78-82`, `:253-255` |
| Low 3 — Dec31/Jan1 discontinuity | `test_non_crossing_december_window_new_year_policy` (L503) | Season selection `:356-375` |
| Low 8 — coverage gaps | Tests L183/217/245/420/462/477/492/503/536 | Test-only; no code guard |
## Test grouping (30 total)
- §17.1 preferred both boundaries: 1 (L86)
- §17.2 documented late: 1 (L107)
- §17.3 outside support: 2 (L117, L168)
- §17.4 no-late wording: 1 (L124)
- §17.5 cross-year/leap: 2 (L133, L328)
- §6.1 preferred approximate/geography: 2 (L307, L318)
- §6.1 future + §10.4 waiting: 6 (L150, L160, L175, L245, L345, L360)
- §6.1 late/optional/data integrity/season: 7 (L183, L217, L399, L420, L503, L523, L536)
- §6.1 missing evidence/authority: 4 (L381, L462, L477, L492)
- §5/§14.4 contract/JSON/API/no-crop: 4 (L269, L554, L569, L600)
Verdict: 30 tests vs 40–60 budget; no trimming required.
Clear duplicate clusters: missing-precision L381/L462; waiting-limit L245/L360; preferred-boundary L86/L269. Proposed parametrized merges, not applied.
Suite: `python -X utf8 -m unittest discover -s tests -v` -> Ran 116 tests in 0.086s, OK.
