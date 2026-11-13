# E4 — Builder round 2: calendar evaluator fixes

Scope: round-1 review findings 1–2 plus the requested hardening items 3–8.
Files changed:

- `src/calendar_evaluator.py`
- `tests/test_calendar.py`
- `council/reports/E4-builder-round2.md`

No crop-specific branches were added. No agronomic or waiting number was
invented. No file under `Data/` was modified; `Data/DataNEVERBEUSED/` was not
read, listed, or modified.

## 1. Optional late bound no longer invalidates preferred/future results

`_build_candidate` now keeps:

- `missing_preferred` — only `preferred_start_mmdd` / `preferred_end_mmdd`;
- `late_status` — `absent`, `resolved`, `unresolved`, or `inconsistent`.

The preferred and future branches never require the late bound:

- inside preferred -> `pass` / `PREFERRED_WINDOW` or approximate caution;
- before the next start -> the future-window result;
- after preferred start but missing preferred end -> `WINDOW_DATE_MISSING`.

Only dates after the preferred end consult the late bound. A late MM-DD that
does not exist in the attached end year (for example `02-29` outside a leap
year) now returns `unknown` / `WINDOW_LATE_END_UNRESOLVED` with a clear reason.
Missing preferred boundaries still return `unknown` / `WINDOW_DATE_MISSING`.

Tests added:

- real Boro with `supported_late_end_mmdd=02-29`:
  - `2026-01-05` -> `pass` / `PREFERRED_WINDOW`;
  - `2026-12-01` -> future option for `2026-12-25`;
  - `2026-02-01` -> `unknown` / `WINDOW_LATE_END_UNRESOLVED`;
  - `2028-02-01` -> `caution` / `LATE_WINDOW` with late end `2028-02-29`.
- future result with a valid start but a year-missing preferred end still
  returns the future option.

## 2. Late-bound order/year validation

The late end is attached to the preferred window's end year:
`end_year = start_year + 1` for cross-year windows, otherwise `start_year`.
A late bound is accepted only when both hold:

```text
late_end > preferred_end
late_end < next season's preferred start
```

The second check prevents a December late bound from overlapping the next
preferred window. Otherwise the result is `unknown` /
`WINDOW_DATA_INCONSISTENT` before any pass/caution. No next-year late extension
is inferred silently.

Tests added for the review's Repros A/B/C:

- non-cross `11-15..11-30` with late `01-15` -> inconsistent;
- cross-year `12-25..01-10` with late `12-30` -> inconsistent;
- non-cross `01-01..03-01` with late `02-01`, evaluated inside the preferred
  window -> inconsistent.

## 3. Missing `date_precision`

Missing precision now returns `unknown` / `WINDOW_PRECISION_MISSING` for
inside-preferred, late, and outside results, before any definitive caution or
unsupported status. Future-window results are unchanged. The old
`DATE_PRECISION_MISSING` code was removed.

Test added for inside, late, and outside dates with missing precision.

## 4. MM-DD authority

The three MM-DD window fields are read from the normalized top level only.
`raw` fallback is now limited to descriptive metadata and source IDs
(`window_basis`, `planting_window_type`, `date_precision`,
`hard_deadline_validated`, `window_guard_readiness`, `algorithm_use_note`,
`source_*`). `window_crosses_year` is also read from the normalized top level.

Test added: top-level `preferred_start_mmdd=None` with raw `"07-10"` returns
`WINDOW_START_MISSING`, and top-level `supported_late_end_mmdd=None` with raw
`"08-15"` is treated as no documented late window.

## 5. Missing sources

If neither `source_planting_window` nor `source_local_calendar` is present, the
evaluator returns `unknown` / `WINDOW_SOURCE_MISSING` before any pass/caution.
Test added with both sources absent.

## 6. Dead late-missing path removed

`WINDOW_LATE_END_MISSING` was removed. A present-but-invalid late text is
deferred: preferred/future results still work, while a post-preferred date
returns `unknown` / `WINDOW_LATE_END_INVALID`. Tests cover both sides.

## 7. Added review edge tests

- Boro `2025-02-28` -> `caution` / `LATE_WINDOW`.
- Boro `2026-03-01` -> `unsupported` / `OUTSIDE_SUPPORTED_WINDOW`.
- Boro `2025-12-24` -> future option for `2025-12-25`, waiting 1 day.
- Boro `2025-12-25` -> `pass` / `PREFERRED_WINDOW`.
- `max_waiting_days=0` on Aman `2026-06-01` -> `FUTURE_WINDOW_EXCEEDS_LIMIT`.
- Boro exact 54-day boundary: `54` -> within, `53` -> exceeds.
- Non-crossing December window `12-20..12-31`: `2026-12-31` -> pass;
  `2027-01-01` -> future option for `2027-12-20`, waiting 353 days.
- Status/code contract for every real crop at a preferred boundary, including
  approximate and geography-unknown outcomes.

## 8. Dec 31 / Jan 1 policy

The existing product policy is retained and now documented in the module
docstring, in `_select_candidate`, and pinned by the December-window test:

- on Dec 31 a December-ending window is still evaluated against its own season
  (pass if inside preferred or late support);
- on Jan 1 the season that ended in the previous calendar year is not revived;
  the next season becomes the future option.

This is a deliberate one-day discontinuity. It never turns a past date into a
pass; `plant_now` stays false on the future option.

## Commands and real output

From `Q:\CycleAlgo\fosol-cycle-engine` (Python 3.13.2):

```powershell
python -X utf8 -m unittest discover -s tests -p "test_calendar.py" -v
python -X utf8 -m unittest discover -s tests -v
```

Focused E4 result:

```text
Ran 30 tests in 0.006s

OK
```

Full suite command:

```powershell
python -X utf8 -m unittest discover -s tests -v
```

Real full-suite output:

```text
test_aman_after_support_is_not_a_normal_candidate (test_calendar.RealProfileCalendarTests.test_aman_after_support_is_not_a_normal_candidate) ... ok
test_aman_january_is_a_future_option (test_calendar.RealProfileCalendarTests.test_aman_january_is_a_future_option) ... ok
test_aman_preferred_window_passes_at_both_boundaries (test_calendar.RealProfileCalendarTests.test_aman_preferred_window_passes_at_both_boundaries) ... ok
test_boro_after_late_support_is_unsupported (test_calendar.RealProfileCalendarTests.test_boro_after_late_support_is_unsupported) ... ok
test_boro_before_december_window_is_future (test_calendar.RealProfileCalendarTests.test_boro_before_december_window_is_future) ... ok
test_boro_boundary_edges (test_calendar.RealProfileCalendarTests.test_boro_boundary_edges) ... ok
test_boro_cross_year_windows_resolve_to_correct_years (test_calendar.RealProfileCalendarTests.test_boro_cross_year_windows_resolve_to_correct_years) ... ok
test_boro_documented_late_date_is_caution (test_calendar.RealProfileCalendarTests.test_boro_documented_late_date_is_caution) ... ok
test_boro_late_leap_bound_keeps_preferred_and_future_results (test_calendar.RealProfileCalendarTests.test_boro_late_leap_bound_keeps_preferred_and_future_results) ... ok
test_future_aman_window_starts_2026_07_10 (test_calendar.RealProfileCalendarTests.test_future_aman_window_starts_2026_07_10) ... ok
test_lentil_approximate_window_is_caution (test_calendar.RealProfileCalendarTests.test_lentil_approximate_window_is_caution) ... ok
test_missing_late_window_is_not_a_biological_impossibility (test_calendar.RealProfileCalendarTests.test_missing_late_window_is_not_a_biological_impossibility) ... ok
test_mung_is_geography_unknown_even_inside_encoded_dates (test_calendar.RealProfileCalendarTests.test_mung_is_geography_unknown_even_inside_encoded_dates) ... ok
test_real_crop_status_contract_at_preferred_boundaries (test_calendar.RealProfileCalendarTests.test_real_crop_status_contract_at_preferred_boundaries) ... ok
test_waiting_limit_zero_and_boro_exact_boundary (test_calendar.RealProfileCalendarTests.test_waiting_limit_zero_and_boro_exact_boundary) ... ok
test_every_result_is_json_serializable_and_complete (test_calendar.ResultContractTests.test_every_result_is_json_serializable_and_complete) ... ok
test_no_crop_id_specific_branch_in_src (test_calendar.ResultContractTests.test_no_crop_id_specific_branch_in_src) ... ok
test_early_january_window_uses_next_year_candidate (test_calendar.SyntheticCalendarTests.test_early_january_window_uses_next_year_candidate) ... ok
test_future_result_does_not_need_preferred_end (test_calendar.SyntheticCalendarTests.test_future_result_does_not_need_preferred_end) ... ok
test_future_window_limit_within_and_exceeds (test_calendar.SyntheticCalendarTests.test_future_window_limit_within_and_exceeds) ... ok
test_inconsistent_cross_year_flag_is_unknown (test_calendar.SyntheticCalendarTests.test_inconsistent_cross_year_flag_is_unknown) ... ok
test_invalid_inputs_are_rejected (test_calendar.SyntheticCalendarTests.test_invalid_inputs_are_rejected) ... ok
test_invalid_late_text_does_not_break_preferred_or_future (test_calendar.SyntheticCalendarTests.test_invalid_late_text_does_not_break_preferred_or_future) ... ok
test_late_bound_order_is_validated (test_calendar.SyntheticCalendarTests.test_late_bound_order_is_validated) ... ok
test_leap_day_window_accepts_leap_year_and_rejects_other_years (test_calendar.SyntheticCalendarTests.test_leap_day_window_accepts_leap_year_and_rejects_other_years) ... ok
test_missing_precision_after_preferred_is_unknown (test_calendar.SyntheticCalendarTests.test_missing_precision_after_preferred_is_unknown) ... ok
test_missing_required_fields_are_specific_unknowns (test_calendar.SyntheticCalendarTests.test_missing_required_fields_are_specific_unknowns) ... ok
test_missing_sources_is_unknown (test_calendar.SyntheticCalendarTests.test_missing_sources_is_unknown) ... ok
test_mmdd_fields_use_normalized_top_level_only (test_calendar.SyntheticCalendarTests.test_mmdd_fields_use_normalized_top_level_only) ... ok
test_non_crossing_december_window_new_year_policy (test_calendar.SyntheticCalendarTests.test_non_crossing_december_window_new_year_policy) ... ok
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
Ran 116 tests in 0.083s

OK
```

## Notes

- `source_ids` remains a list of the stable source field names actually present.
- `WINDOW_PRECISION_MISSING` replaces the old `DATE_PRECISION_MISSING` code.
- `WINDOW_LATE_END_UNRESOLVED` is used only for a post-preferred date whose
  attached late bound is absent in that year.
- `WINDOW_DATA_INCONSISTENT` is used profile-wide when the late bound is not a
  valid extension (`late_end <= preferred_end` or `late_end >= next start`).
- The Dec 31/Jan 1 policy is deliberate and pinned; it never creates a
  `plant_now=True` result for a past date.
- Climate, soil/water, timelines, economics, and overall response aggregation
  remain out of E4 scope.
