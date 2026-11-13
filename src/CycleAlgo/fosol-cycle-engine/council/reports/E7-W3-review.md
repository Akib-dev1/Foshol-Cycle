# E7 W3 - build_outlook review (final)

**Verdict: PASS.** Both contract fixes are present; suite green; 2/2 mutations killed.

Full suite: `Ran 224 tests in 1.195s`, `OK` (exit 0). Focused W3: `Ran 8 tests in 0.002s`, `OK`.

## Contract checks
- Unavailable warning: `numerator=None`, `days_meeting=None`, `denominator=0`, status `unavailable`, text says "unavailable, not zero".
- Every indicator `source_ids` equals `[sources[0]["source_id"]]` = `["nasa_power_daily"]`.
- Schema keys, exact em-dash label, status ok/partial/unavailable, warnings default OFF/disabled omitted, enabled heat/low-temp/heavy-rain texts distinct, unusual source version `v9.9.9`/fill `-1234`/`missing_days=1`/`failed_requests=2`, absent `failed_requests` -> null, union caveat, JSON, no crop-ID branches: pass.

## Mutation gate (2/2 killed; hashes restored)
| mutation | failing test | hash OK |
|---|---|---|
| remove source_ids assignment | `test_source_ids_and_unavailable_counts_are_pinned` | yes |
| unavailable numerator 0 | `test_unavailable_without_observations` | yes |
Restored SHA-256 `F8A6...83ED` / `F3B4...AE0B`; no mutation remains.

E6 smoke: 420 branches, 0 candidate / 420 conditional, 15 exclusions all `WINDOW_GEOGRAPHY_UNKNOWN`.

Budget: E7 36 tests vs 20–30 (+6); builder's one-line reason (schema/status/source coverage) is documented but thin. Tests retained. No permanent edits; no commits.
