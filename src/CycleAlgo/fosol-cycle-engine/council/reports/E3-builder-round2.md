# E3 — Builder round 2 (review/spec fixes)

## Addendum — docs-only provider-record correction

After the round-2 code fixes, the remaining review failures were documentation
only. `docs/ENVIRONMENTAL_DATA.md` now records the verified provider facts:

- POWER coverage `1981-01-01 to present/NRT` (NASA POWER Daily docs; live
  `/configuration` start `1981-01-01T00:00:00`, end `2026-11-06T00:00:00`).
- POWER latency `2–3 days meteorological; 5–7 days solar` (POWER Data FAQ).
- POWER usage limit HTTP `429 Too Many Requests` (official API docs), plus the
  third-party `nasapower` note about a 20-parameter daily-point cap; the
  official OpenAPI used here does not state the cap and this engine requests
  only 3 parameters.
- SMAP/AppEEARS coverage `2015-03-31 to present` (NSIDC `SPL4SMGP.008` product
  page).
- SMAP latency: Level-4 soil moisture required within `7 days` (SMAP mission
  data products); no measured mean latency is claimed.

The record also keeps the existing resolutions, variables, fill values, auth,
quality, and point/grid association rows; explicitly labels `GWETTOP` as
MERRA-2 surface soil wetness, **not SMAP**; and states that POWER and SMAP do
not share resolution, temporal step, coverage, or dates.

No code or test files changed in this addendum. Real command output after the
docs-only edit:

```powershell
python -X utf8 -m unittest discover -s tests -v
```

```text
----------------------------------------------------------------------
Ran 86 tests in 0.087s

OK
```

The full 86-test listing below is from the preceding identical round-2 run;
the summary above is the post-docs-only re-run.

Status: round-2 fixes complete. Only the six requested items were addressed:

1. SMAP cache identity now includes `point_id`.
2. Duplicate SMAP timestamps are deduplicated or rejected on conflict.
3. Cache JSON is parsed strictly and non-finite values are treated as a miss.
4. AppEEARS HTTP requests have bounded retries.
5. Docs now contain the §2 provider record.
6. Docs record the actual 3-hourly AppEEARS granularity and the `queued`
   observed status extension.

No file under `Q:\CycleAlgo\Data\` or `Data/DataNEVERBEUSED/` was read or
modified. The AppEEARS token was never printed, logged, or committed. The unit
suite makes no live network calls.

## 1. SMAP cache key includes `point_id`

Changed:

- `src/environment_cache.py`: `build_cache_key(..., *, point_id=None)` adds
  `point_id` to the canonical payload. POWER leaves it `None`; SMAP supplies
  the resolved AppEEARS coordinate id.
- `src/smap_api.py`: added `default_point_id(latitude, longitude)` and
  `resolve_point_id(point_id, latitude, longitude)`. The default is the stable
  `"<latitude>,<longitude>"` string.
- `src/smap_api.py`: `submit_point_task` and `fetch_smap_point` accept
  `point_id=None` and use the same resolved id in the task body.
- `src/environment.py`: `load_smap_environment` and `load_environment` accept
  `point_id=None`, resolve it once, put it in the cache key, the request, and
  the fetcher call.

Tests added:

- `CacheKeyTests.test_point_id_is_part_of_the_key`
- `CacheKeyTests.test_every_field_changes_the_key` (adds `point_id`)
- `SmapRequestTests.test_submit_defaults_point_id_to_coordinates`
- `EnvironmentLoaderTests.test_smap_cache_is_separated_by_point_id` — two IDs
  at the same coordinates make two fetches and cache entries.
- `EnvironmentLoaderTests.test_smap_default_point_id_is_stable_coordinate_string`

## 2. Duplicate SMAP timestamps

Changed `src/smap_api.py::parse_appeears_csv`:

- Rows are collected by ISO timestamp.
- An identical duplicate row is dropped and counted in `duplicate_timestamps`.
- A duplicate timestamp with different layer values raises
  `AppEEarsResponseError`.
- `missing_counts` is computed over unique observations only.
- Parsed output now includes `duplicate_timestamps`.

Tests added:

- `SmapParseTests.test_identical_duplicate_timestamp_is_deduplicated`
  (24 unique observations, count 1, missing counts unchanged)
- `SmapParseTests.test_conflicting_duplicate_timestamp_is_rejected`
- The real-CSV test now asserts `duplicate_timestamps == 0`.

## 3. Strict cache JSON

Changed `src/environment_cache.py`:

- `json.loads` uses `parse_constant` to reject `NaN`, `Infinity`, and
  `-Infinity`, and `parse_float` to reject float overflow such as `1e999`.
- Invalid/corrupt entries are returned as `None` (a cache miss), so the loader
  refetches.
- Writes already use `allow_nan=False`.

Tests added:

- `EnvironmentCacheTests.test_non_finite_json_constants_are_a_miss` covers all
  four constants.
- `EnvironmentLoaderTests.test_non_finite_cache_is_refetched` writes a fresh
  cache entry containing `NaN`, verifies it is a miss, and verifies the loader
  calls the fetcher again and returns the valid value.

## 4. AppEEARS bounded retries

Changed `src/smap_api.py`:

- `_open_bytes` now has a bounded retry loop with exponential backoff.
- GET requests retry HTTP 429, all HTTP 5xx, and network/timeout failures.
- `POST /task` retries only HTTP 429 and 503; other 5xx and network failures are
  not retried, avoiding duplicate task submission on an ambiguous request.
- HTTP 401/403 remains an immediate `AppEEarsAuthError` with the documented
  token-refresh message.
- `submit_point_task`, `wait_for_task`, `get_bundle`, `download_result_csv`,
  and `fetch_smap_point` expose the retry budget/backoff/sleep parameters.

Tests added:

- `SmapRetryTests.test_submit_retries_429_then_succeeds`
- `SmapRetryTests.test_submit_retries_503_then_succeeds`
- `SmapRetryTests.test_get_retries_5xx_then_succeeds`
- `SmapRetryTests.test_retry_budget_is_bounded` (3 attempts with
  `max_retries=2`, then raises)
- `SmapRetryTests.test_post_500_is_not_retried`

## 5–6. Documentation

`docs/ENVIRONMENTAL_DATA.md` now has a `## Provider record (§2)` table with
both providers covering product/version, endpoint/access, authentication,
usage limits/429, variables/units, valid ranges, missing conventions, spatial
and temporal resolution, coverage, publication latency, quality flags, and the
representative-location association for Rajshahi 24.3767/88.6029. Results are
explicitly marked as grid-cell/point values, not district averages.

The table and notes record that AppEEARS actually returns 3-hourly data even
though the daily catalog metadata is coarse, and that `queued` is an observed
status extension. The SMAP failures section now documents the retry policy and
duplicate-timestamp behavior. The cache section documents `point_id` and strict
JSON parsing. The token wording no longer says the token is "returned"; it is
never printed, logged, exposed in a response, or included in an error message.

## Files changed in round 2

- `src/environment_cache.py`
- `src/smap_api.py`
- `src/environment.py`
- `tests/test_environment.py`
- `docs/ENVIRONMENTAL_DATA.md`
- `council/reports/E3-builder-round2.md`

## Commands run

From `Q:\CycleAlgo\fosol-cycle-engine` (Python 3.13.2):

```powershell
python -X utf8 -m unittest discover -s tests -v
```

## Real command output

```text
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
Ran 86 tests in 0.079s

OK
```

## Coverage summary

- 73 pre-round tests + 13 new tests = **86 total**, all passing.
- New tests cover point-id cache separation/defaults, duplicate dedupe/conflict,
  strict non-finite cache handling and refetch, AppEEARS 429/503/5xx retries,
  bounded retry exhaustion, and POST 500 non-retry.
- Test suite remains offline: every provider call injects an opener or fetcher.
