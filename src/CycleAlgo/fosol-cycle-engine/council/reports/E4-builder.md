# E4 — Builder report: shared calendar evaluator

Scope: §6.1 calendar eligibility and §17.1–17.5 only. No climate exposure,
soil/water, timeline, preparation, economics, or crop-specific logic was added.

## Files

- `src/calendar_evaluator.py` — new shared evaluator.
- `tests/test_calendar.py` — new tests (19 tests).
- `council/reports/E4-builder.md` — this report.

No file under `Data/` was modified. `Data/DataNEVERBEUSED/` was not read,
listed, or modified. `v1.md` was read only.

## API

```python
from src.calendar_evaluator import evaluate_calendar_fit

result = evaluate_calendar_fit(
    profile,              # dict from src.crop_profiles.load_crop_profiles
    start_date,           # datetime.date or ISO "YYYY-MM-DD"
    max_waiting_days=None # explicit policy only; None means not configured
)
```

Return shape:

```python
{
    "status": "pass" | "caution" | "unsupported" | "unknown",
    "code": "...",
    "reason": "...",
    "source_ids": ["source_planting_window", "source_local_calendar"],
    "details": {
        "planting_date": "2026-07-10",       # ISO
        "plant_now": True,
        "preferred_start": "2026-07-10",     # ISO, resolved year
        "preferred_end": "2026-07-24",       # ISO, resolved year
        "supported_late_end": None,          # ISO, resolved year, or None
        "next_window_start": None,           # ISO only for future-window results
        "waiting_days": None,
        "waiting_limit_days": None,
        "waiting_limit_status": "not_applicable",
        "window_start_year": 2026,           # audit aid for cross-year windows
        "date_precision": "DAY",
        "hard_deadline_validated": False,
        "window_basis": "...",
        "window_type": "...",
        "window_guard_readiness": "...",
        "algorithm_use_note": "...",
    },
}
```

`source_ids` is a list of the stable source field names actually present, in
the order `source_planting_window`, `source_local_calendar`.

`max_waiting_days` is validated as a non-negative integer or `None`. No
numeric default is supplied.

## Window resolution

1. Read the three MM-DD fields from the normalized profile, falling back to
   `profile["raw"]` for metadata (`planting_window_type`, `date_precision`,
   `window_basis`, `hard_deadline_validated`, `window_guard_readiness`,
   `algorithm_use_note`, and the two `source_*` fields).
2. Attach dates for candidate start years `Y-1`, `Y`, `Y+1`:
   - non-crossing: start and end in the same start year;
   - `window_crosses_year=true`: start in `S`, end and supported-late end in
     `S+1`.
3. A containing instance wins (preferred window or documented supported-late
   extension). Otherwise the nearest start is chosen among the current/next
   season and any window whose support ended in the proposed calendar year.
   A just-expired season stays outside support; a season that ended in an
   earlier year does not displace the upcoming window, and a year-end date can
   still reach an early-January window in the following year.
4. A boundary that does not exist in its attached year (for example `02-29` in
   a non-leap year) marks that instance missing. If the missing instance is
   selected, the result is `unknown` / `WINDOW_DATE_MISSING`; it is not skipped
   to a distant valid year.

No agronomic window, deadline, or waiting number is invented. Preferred ends
are never described as proven biological deadlines. `hard_deadline_validated`
is recorded but never used as a pass/fail rule.

The selection rule is deliberate: §17.3 requires a just-expired Aman date to be
`unsupported` rather than silently treated as next season's future option,
while a genuinely upcoming window (for example Boro in November) remains a
future option with its waiting days exposed.

## Status and code mapping

| Condition | Status | Code |
|---|---|---|
| Inside preferred, exact `DAY` precision | `pass` | `PREFERRED_WINDOW` |
| Inside preferred, approximate/non-`DAY` precision | `caution` | `PREFERRED_WINDOW_APPROXIMATE` |
| After preferred end, within `supported_late_end_mmdd` | `caution` | `LATE_WINDOW` |
| After preferred/late support | `unsupported` | `OUTSIDE_SUPPORTED_WINDOW` |
| Before next window, `max_waiting_days is None` | `unknown` | `FUTURE_WINDOW_WAIT_POLICY_UNKNOWN` |
| Before next window, waiting within limit | `caution` | `FUTURE_WINDOW_WITHIN_LIMIT` |
| Before next window, waiting exceeds limit | `unsupported` | `FUTURE_WINDOW_EXCEEDS_LIMIT` |
| Window is not Rajshahi-exact | `unknown` | `WINDOW_GEOGRAPHY_UNKNOWN` |
| Cross-year flag conflicts with start/end order | `unknown` | `WINDOW_DATA_INCONSISTENT` |
| Boundary MM-DD absent in the required year | `unknown` | `WINDOW_DATE_MISSING` |
| Missing preferred start | `unknown` | `WINDOW_START_MISSING` |
| Missing preferred end | `unknown` | `WINDOW_END_MISSING` |
| Missing `window_basis` | `unknown` | `WINDOW_BASIS_MISSING` |
| Missing `planting_window_type` | `unknown` | `WINDOW_TYPE_MISSING` |
| Missing/unusable `window_crosses_year` | `unknown` | `WINDOW_CROSS_YEAR_MISSING` |
| Missing `date_precision` inside preferred | `unknown` | `DATE_PRECISION_MISSING` |
| Malformed MM-DD text | `unknown` | `WINDOW_START_INVALID` / `WINDOW_END_INVALID` / `WINDOW_LATE_END_INVALID` |

`waiting_limit_status` is `unknown`, `within_limit`, `exceeds_limit`, or
`not_applicable` (non-future result). `plant_now` is false for future,
unsupported, and unknown results; true for preferred, approximate, and late
results.

## Test coverage

- §17.1 — Aman `2026-07-10` and `2026-07-24` both pass.
- §17.2 — Boro `2026-02-01` is `caution` / `LATE_WINDOW`.
- §17.3 — Aman `2026-08-01` is `unsupported` / `OUTSIDE_SUPPORTED_WINDOW`.
- §17.4 — Aman `2026-07-25` reason states no documented late window, not a
  biological impossibility, and not a proven deadline.
- §17.5 — Boro `2026-01-05` resolves to `2025-12-25..2026-01-10` with late end
  `2026-02-28`; Boro `2026-12-25` resolves to `2026-12-25..2027-01-10` with
  late end `2027-02-28`; synthetic `02-29..03-10` passes on `2028-02-29` and
  returns `WINDOW_DATE_MISSING` for 2027 dates.
- Future Aman `2026-06-01` returns `next_window_start=2026-07-10`,
  `waiting_days=39`, and unknown policy when no limit is configured. Aman
  `2026-01-01` is a future option for the 2026 window; Boro `2026-06-01` is
  outside the ended 2025-26 support, while Boro `2026-11-01` is a future
  option for `2026-12-25`. Synthetic within/exceeds limit cases are covered.
- Lentil is `caution` / `PREFERRED_WINDOW_APPROXIMATE`; Mung is `unknown` /
  `WINDOW_GEOGRAPHY_UNKNOWN` even inside its encoded dates; missing fields and
  inconsistent cross-year flags are `unknown`; every result is JSON
  serializable with `allow_nan=False`.
- A source scan asserts no crop ID appears in `src/`.

## Exact commands

From `Q:\CycleAlgo\fosol-cycle-engine` (Python 3.13.2):

```powershell
python -X utf8 -m unittest discover -s tests -p "test_calendar.py" -v
python -X utf8 -m unittest discover -s tests -v
```

Focused run:

```text
Ran 19 tests in 0.005s

OK
```

## Real full-suite output

Command:

```powershell
python -X utf8 -m unittest discover -s tests -v
```

Output:

```text
test_aman_after_support_is_not_a_normal_candidate (test_calendar.RealProfileCalendarTests.test_aman_after_support_is_not_a_normal_candidate) ... ok
test_aman_january_is_a_future_option (test_calendar.RealProfileCalendarTests.test_aman_january_is_a_future_option) ... ok
test_aman_preferred_window_passes_at_both_boundaries (test_calendar.RealProfileCalendarTests.test_aman_preferred_window_passes_at_both_boundaries) ... ok
test_boro_after_late_support_is_unsupported (test_calendar.RealProfileCalendarTests.test_boro_after_late_support_is_unsupported) ... ok
test_boro_before_december_window_is_future (test_calendar.RealProfileCalendarTests.test_boro_before_december_window_is_future) ... ok
test_boro_cross_year_windows_resolve_to_correct_years (test_calendar.RealProfileCalendarTests.test_boro_cross_year_windows_resolve_to_correct_years) ... ok
test_boro_documented_late_date_is_caution (test_calendar.RealProfileCalendarTests.test_boro_documented_late_date_is_caution) ... ok
test_future_aman_window_starts_2026_07_10 (test_calendar.RealProfileCalendarTests.test_future_aman_window_starts_2026_07_10) ... ok
test_lentil_approximate_window_is_caution (test_calendar.RealProfileCalendarTests.test_lentil_approximate_window_is_caution) ... ok
test_missing_late_window_is_not_a_biological_impossibility (test_calendar.RealProfileCalendarTests.test_missing_late_window_is_not_a_biological_impossibility) ... ok
test_mung_is_geography_unknown_even_inside_encoded_dates (test_calendar.RealProfileCalendarTests.test_mung_is_geography_unknown_even_inside_encoded_dates) ... ok
test_every_result_is_json_serializable_and_complete (test_calendar.ResultContractTests.test_every_result_is_json_serializable_and_complete) ... ok
test_no_crop_id_specific_branch_in_src (test_calendar.ResultContractTests.test_no_crop_id_specific_branch_in_src) ... ok
test_early_january_window_uses_next_year_candidate (test_calendar.SyntheticCalendarTests.test_early_january_window_uses_next_year_candidate) ... ok
test_future_window_limit_within_and_exceeds (test_calendar.SyntheticCalendarTests.test_future_window_limit_within_and_exceeds) ... ok
test_inconsistent_cross_year_flag_is_unknown (test_calendar.SyntheticCalendarTests.test_inconsistent_cross_year_flag_is_unknown) ... ok
test_invalid_inputs_are_rejected (test_calendar.SyntheticCalendarTests.test_invalid_inputs_are_rejected) ... ok
test_leap_day_window_accepts_leap_year_and_rejects_other_years (test_calendar.SyntheticCalendarTests.test_leap_day_window_accepts_leap_year_and_rejects_other_years) ... ok
test_missing_required_fields_are_specific_unknowns (test_calendar.SyntheticCalendarTests.test_missing_required_fields_are_specific_unknowns) ... ok
test_boro_window_crosses_year_with_parsed_bounds (test_crop_profiles.RealDatasetTests.test_boro_window_crosses_year_with_parsed_bounds) ... ok
test_duration_ranges_are_integers_in_order (test_crop_profiles.RealDatasetTests.test_duration_ranges_are_integers_in_order) ... ok
test_loads_exactly_eight_profiles (test_crop_profiles.RealDatasetTests.test_loads_exactly_eight_profiles) ... ok
test_names_and_variety_are_normalized (test_crop_profiles.RealDatasetTests.test_names_and_variety_are_normalized) ... ok
test_removed_crops_are_absent_from_ids_and_names (test_crop_profiles.RealDatasetTests.test_removed_crops_are_absent_from_ids_and_names) ... ok
test_requested_crop_ids_are_present (test_crop_profiles.RealDatasetTests.test_requested_crop_ids_are_present) ... ok
test_blank_value_is_none_and_missing (test_crop_profiles.ValidationTests.test_blank_value_is_none_and_missing) ... ok
test_duplicate_crop_id_raises_value_error (test_crop_profiles.ValidationTests.test_duplicate_crop_id_raises_value_error) ... ok
test_empty_csv_raises_value_error (test_crop_profiles.ValidationTests.test_empty_csv_raises_value_error) ... ok
test_header_only_csv_raises_value_error (test_crop_profiles.ValidationTests.test_header_only_csv_raises_value_error) ... ok
test_invalid_mmdd_is_none_and_unclear (test_crop_profiles.ValidationTests.test_invalid_mmdd_is_none_and_unclear) ... ok
test_leap_day_is_valid_but_february_30_is_not (test_crop_profiles.ValidationTests.test_leap_day_is_valid_but_february_30_is_not) ... ok
test_min_greater_than_max_clears_pair_and_flags_unclear (test_crop_profiles.ValidationTests.test_min_greater_than_max_clears_pair_and_flags_unclear) ... ok
test_raw_row_is_preserved (test_crop_profiles.ValidationTests.test_raw_row_is_preserved) ... ok
test_every_field_changes_the_key (test_environment.CacheKeyTests.test_every_field_changes_the_key) ... ok
test_key_is_stable_and_variable_order_is_irrelevant (test_environment.CacheKeyTests.test_key_is_stable_and_variable_order_is_irrelevant) ... ok
test_point_id_is_part_of_the_key (test_environment.CacheKeyTests.test_point_id_is_part_of_the_key) ... ok
test_corrupt_cache_is_a_miss (test_environment.EnvironmentCacheTests.test_corrupt_cache_is_a_miss) ... ok
test_invalid_key_and_non_finite_payload_are_rejected (test_environment.EnvironmentCacheTests.test_invalid_key_and_non_finite_payload_are_rejected) ... ok
test_non_finite_json_constants_are_a_miss (test_environment.EnvironmentCacheTests.test_non_finite_json_constants_are_a_miss) ... ok
test_put_and_get_round_trip (test_environment.EnvironmentCacheTests.test_put_and_get_round_trip) ... ok
test_auth_failure_hint_is_surfaced (test_environment.EnvironmentLoaderTests.test_auth_failure_hint_is_surfaced) ... ok
test_fresh_cache_avoids_network (test_environment.EnvironmentLoaderTests.test_fresh_cache_avoids_network) ... ok
test_fresh_cache_works_without_network (test_environment.EnvironmentLoaderTests.test_fresh_cache_works_without_network) ... ok
test_no_cache_and_failure_raises (test_environment.EnvironmentLoaderTests.test_no_cache_and_failure_raises) ... ok
test_non_finite_cache_is_refetched (test_environment.EnvironmentLoaderTests.test_non_finite_cache_is_refetched) ... ok
test_smap_cache_is_separated_by_point_id (test_environment.EnvironmentLoaderTests.test_smap_cache_is_separated_by_point_id) ... ok
test_smap_default_point_id_is_stable_coordinate_string (test_environment.EnvironmentLoaderTests.test_smap_default_point_id_is_stable_coordinate_string) ... ok
test_smap_loader_and_json_serialization (test_environment.EnvironmentLoaderTests.test_smap_loader_and_json_serialization) ... ok
test_stale_cache_is_used_with_explicit_warning (test_environment.EnvironmentLoaderTests.test_stale_cache_is_used_with_explicit_warning) ... ok
test_both_providers_failing_raises (test_environment.EnvironmentOrchestratorTests.test_both_providers_failing_raises) ... ok
test_both_providers_succeed (test_environment.EnvironmentOrchestratorTests.test_both_providers_succeed) ... ok
test_partial_result_when_one_provider_fails (test_environment.EnvironmentOrchestratorTests.test_partial_result_when_one_provider_fails) ... ok
test_422_is_not_retried (test_environment.PowerFetchTests.test_422_is_not_retried) ... ok
test_build_url_uses_documented_query (test_environment.PowerFetchTests.test_build_url_uses_documented_query) ... ok
test_retries_429_then_succeeds (test_environment.PowerFetchTests.test_retries_429_then_succeeds) ... ok
test_retries_5xx_then_succeeds (test_environment.PowerFetchTests.test_retries_5xx_then_succeeds) ... ok
test_retries_network_failure_then_succeeds (test_environment.PowerFetchTests.test_retries_network_failure_then_succeeds) ... ok
test_fill_value_is_none_not_zero (test_environment.PowerNormalizeTests.test_fill_value_is_none_not_zero) ... ok
test_malformed_responses_are_rejected (test_environment.PowerNormalizeTests.test_malformed_responses_are_rejected) ... ok
test_non_finite_values_become_none (test_environment.PowerNormalizeTests.test_non_finite_values_become_none) ... ok
test_real_fixture_is_normalized (test_environment.PowerNormalizeTests.test_real_fixture_is_normalized) ... ok
test_response_is_json_serializable (test_environment.PowerNormalizeTests.test_response_is_json_serializable) ... ok
test_full_orchestration_uses_the_results_csv (test_environment.SmapFetchTests.test_full_orchestration_uses_the_results_csv) ... ok
test_conflicting_duplicate_timestamp_is_rejected (test_environment.SmapParseTests.test_conflicting_duplicate_timestamp_is_rejected) ... ok
test_fill_and_empty_become_none_not_zero (test_environment.SmapParseTests.test_fill_and_empty_become_none_not_zero) ... ok
test_identical_duplicate_timestamp_is_deduplicated (test_environment.SmapParseTests.test_identical_duplicate_timestamp_is_deduplicated) ... ok
test_malformed_csv_is_rejected (test_environment.SmapParseTests.test_malformed_csv_is_rejected) ... ok
test_real_csv_is_parsed (test_environment.SmapParseTests.test_real_csv_is_parsed) ... ok
test_response_is_json_serializable (test_environment.SmapParseTests.test_response_is_json_serializable) ... ok
test_303_means_done (test_environment.SmapRequestTests.test_303_means_done) ... ok
test_403_reports_expired_or_invalid_token (test_environment.SmapRequestTests.test_403_reports_expired_or_invalid_token) ... ok
test_bundle_picks_results_csv (test_environment.SmapRequestTests.test_bundle_picks_results_csv) ... ok
test_bundle_without_results_csv_is_rejected (test_environment.SmapRequestTests.test_bundle_without_results_csv_is_rejected) ... ok
test_download_decodes_csv (test_environment.SmapRequestTests.test_download_decodes_csv) ... ok
test_error_status_raises (test_environment.SmapRequestTests.test_error_status_raises) ... ok
test_poll_queued_processing_done (test_environment.SmapRequestTests.test_poll_queued_processing_done) ... ok
test_submit_body_dates_and_coordinates_are_exact (test_environment.SmapRequestTests.test_submit_body_dates_and_coordinates_are_exact) ... ok
test_submit_defaults_point_id_to_coordinates (test_environment.SmapRequestTests.test_submit_defaults_point_id_to_coordinates) ... ok
test_timeout_is_bounded (test_environment.SmapRequestTests.test_timeout_is_bounded) ... ok
test_get_retries_5xx_then_succeeds (test_environment.SmapRetryTests.test_get_retries_5xx_then_succeeds) ... ok
test_post_500_is_not_retried (test_environment.SmapRetryTests.test_post_500_is_not_retried) ... ok
test_retry_budget_is_bounded (test_environment.SmapRetryTests.test_retry_budget_is_bounded) ... ok
test_submit_retries_429_then_succeeds (test_environment.SmapRetryTests.test_submit_retries_429_then_succeeds) ... ok
test_submit_retries_503_then_succeeds (test_environment.SmapRetryTests.test_submit_retries_503_then_succeeds) ... ok
test_missing_token_file_raises (test_environment.SmapTokenTests.test_missing_token_file_raises) ... ok
test_token_is_loaded_and_expiry_is_enforced (test_environment.SmapTokenTests.test_token_is_loaded_and_expiry_is_enforced) ... ok
test_token_path_comes_from_documented_env_var (test_environment.SmapTokenTests.test_token_path_comes_from_documented_env_var) ... ok
test_error_response_has_exact_documented_shape (test_request_validation.ErrorContractTests.test_error_response_has_exact_documented_shape) ... ok
test_invalid_request_maps_to_http_400 (test_request_validation.ErrorContractTests.test_invalid_request_maps_to_http_400) ... ok
test_unexpected_error_maps_to_http_500 (test_request_validation.ErrorContractTests.test_unexpected_error_maps_to_http_500) ... ok
test_whole_payload_error_has_null_field (test_request_validation.ErrorContractTests.test_whole_payload_error_has_null_field) ... ok
test_bad_date_message_matches_spec_example (test_request_validation.RequestValidationTests.test_bad_date_message_matches_spec_example) ... ok
test_bad_start_dates_are_rejected (test_request_validation.RequestValidationTests.test_bad_start_dates_are_rejected) ... ok
test_district_id_missing_blank_or_non_string (test_request_validation.RequestValidationTests.test_district_id_missing_blank_or_non_string) ... ok
test_every_allowed_enum_value_is_accepted (test_request_validation.RequestValidationTests.test_every_allowed_enum_value_is_accepted) ... ok
test_first_crop_id_must_be_null_or_a_known_id (test_request_validation.RequestValidationTests.test_first_crop_id_must_be_null_or_a_known_id) ... ok
test_first_crop_id_null_is_accepted (test_request_validation.RequestValidationTests.test_first_crop_id_null_is_accepted) ... ok
test_full_payload_round_trips (test_request_validation.RequestValidationTests.test_full_payload_round_trips) ... ok
test_lowest_upfront_cash_is_rejected_until_cash_flow_exists (test_request_validation.RequestValidationTests.test_lowest_upfront_cash_is_rejected_until_cash_flow_exists) ... ok
test_minimal_payload_applies_documented_defaults (test_request_validation.RequestValidationTests.test_minimal_payload_applies_documented_defaults) ... ok
test_payload_must_be_a_json_object (test_request_validation.RequestValidationTests.test_payload_must_be_a_json_object) ... ok
test_preference_rejects_every_invalid_value (test_request_validation.RequestValidationTests.test_preference_rejects_every_invalid_value) ... ok
test_real_calendar_dates_including_leap_day_are_accepted (test_request_validation.RequestValidationTests.test_real_calendar_dates_including_leap_day_are_accepted) ... ok
test_unknown_extra_keys_are_ignored (test_request_validation.RequestValidationTests.test_unknown_extra_keys_are_ignored) ... ok
test_water_access_rejects_every_invalid_value (test_request_validation.RequestValidationTests.test_water_access_rejects_every_invalid_value) ... ok

----------------------------------------------------------------------
Ran 105 tests in 0.103s

OK
```

## Open decisions left unchanged

- No maximum waiting value is established; callers must pass
  `max_waiting_days` explicitly or the future-window result stays `unknown`.
- `hard_deadline_validated` is `false` in the real crop CSV and is recorded,
  not converted into a deadline claim.
- Climate exposure, soil/water, timelines, economics, and the overall response
  envelope remain for later increments.
