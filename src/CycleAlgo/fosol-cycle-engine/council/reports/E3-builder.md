# E3 — Environmental loading, caching, missing-value handling

> Round-2 fixes and the current 86-test output: `council/reports/E3-builder-round2.md`.

Status: complete. Implements spec §2, §6.2, §7, §9.3, §15, and §19 for the
POWER + SMAP data layer only. No calendar/evaluator (E4), crop logic, HTTP
wrapper, or response-envelope work was added.

No file in `Q:\CycleAlgo\Data\` was read or modified, and
`Data/DataNEVERBEUSED/` was not accessed. No credentials were added to code,
tests, fixtures, or docs.

## Files created

| File | Purpose |
|---|---|
| `src/power_api.py` | POWER daily point URL/fetch/retry + response normalizer |
| `src/smap_api.py` | AppEEARS token, task, bundle, CSV parse, point orchestration |
| `src/environment_cache.py` | Atomic JSON cache and canonical SHA-256 key |
| `src/environment.py` | POWER/SMAP cache-aware loaders and combined loader |
| `tests/test_environment.py` | 41 new `unittest` tests (73 total) |
| `tests/fixtures/power_daily_rajshahi_20250101_20250103.json` | Real live POWER response |
| `tests/fixtures/appeears_spl4smgp_rajshahi_20250101_20250103.csv` | Real smoke-test AppEEARS CSV |
| `tests/fixtures/power_daily_synthetic_missing.json` | Synthetic `-999`/null sample |
| `tests/fixtures/appeears_spl4smgp_synthetic_missing.csv` | Synthetic `-9999`/empty sample |
| `docs/ENVIRONMENTAL_DATA.md` | Endpoints, products, units, fill values, policy |
| `council/reports/E3-builder.md` | This report |

The POWER fixture was fetched live on 2026-11-06 for
24.3767 N / 88.6029 E, 2025-01-01 through 2025-01-03, with
`T2M,PRECTOTCORR,GWETTOP`, `community=AG`, `units=metric`,
`time-standard=LST`. Values were not edited.

## Public API

### `src/power_api.py`

```python
build_power_url(latitude, longitude, start_date, end_date, parameters, *,
                community="AG", units="metric", time_standard="LST") -> str
fetch_power_daily(latitude, longitude, start_date, end_date, parameters, *,
                  community="AG", units="metric", time_standard="LST",
                  timeout=30.0, max_retries=3, backoff_seconds=1.0,
                  sleep=time.sleep, opener=urllib.request.urlopen) -> dict
normalize_power_response(raw, retrieved_at=None) -> dict
```

- Retries only HTTP 429, HTTP 5xx, network, and timeout failures; bounded by
  `max_retries` with exponential backoff. HTTP 422 and other 4xx responses are
  raised immediately.
- `PowerApiError` carries `message`, `status_code`, and `code`.
- Normalized fields: `product`, `product_version`, `provider`, `variables`
  (`units`, `longname`), `observations` keyed ISO date,
  `observation_start`, `observation_end`, `fill_value`, `messages`,
  `spatial_resolution`, `temporal_resolution`, `retrieved_at`.
- `-999`, `null`, `NaN`, and infinities become `None`. They are never `0`.
- Missing/invalid header, metadata, parameter series, dates, or non-numeric
  observations raise `PowerApiError`.

### `src/smap_api.py`

```python
token_file_path(path=None) -> Path
load_token(path=None, *, now=None) -> str
submit_point_task(token, *, task_name, latitude, longitude, point_id,
                  start_date, end_date, timeout=60.0, opener=...) -> dict
wait_for_task(token, task_id, *, timeout_seconds=900.0, poll_seconds=10.0,
              request_timeout=60.0, sleep=time.sleep, clock=time.monotonic,
              opener=...) -> dict
get_bundle(token, task_id, *, timeout=60.0, opener=...) -> list[dict]
select_result_file(files) -> dict
download_result_csv(token, task_id, file_id, *, timeout=60.0, opener=...) -> str
parse_appeears_csv(csv_text, retrieved_at=None) -> dict
fetch_smap_point(latitude, longitude, start_date, end_date, *, point_id,
                 token=None, token_path=None, task_name=None,
                 task_timeout_seconds=900.0, poll_seconds=10.0,
                 request_timeout=60.0, sleep=time.sleep,
                 clock=time.monotonic, opener=...) -> dict
```

- Product: `SPL4SMGP.008`; layers `Geophysical_Data_sm_surface` and
  `Geophysical_Data_sm_rootzone`.
- The submitted body is exactly the documented `task_type="point"` body with
  `MM-DD-YYYY` dates, both layers, and one coordinate.
- `pending`, `queued`, and `processing` keep polling; `done` returns; HTTP 303
  is treated as done; `error`, unknown statuses, and the bounded timeout raise.
- Bundle selection uses the CSV whose name contains `results`; statistics and
  metadata files are not selected.
- Parsed fields: `product`, `product_version`, `provider`, `variables`
  (`units`, `layer`), sorted `observations` with ISO UTC `timestamp`,
  `observation_start`, `observation_end`, `point`, `missing_counts`,
  `fill_value`, `spatial_resolution`, `temporal_resolution`, `retrieved_at`.
- `-9999`, empty cells, and non-finite values become `None`.
- `load_token` reads `APPEARS_TOKEN_FILE` or the default parent-repo
  `appeears_token.txt`, rejects a known-expired token, and never echoes the
  token. HTTP 401/403 raises `AppEEarsAuthError` with:
  `AppEEARS token expired or invalid; run tools/appeears_login.py`.
- Typed errors: `AppEEarsError`, `AppEEarsAuthError`,
  `AppEEarsResponseError`.

### `src/environment_cache.py`

```python
build_cache_key(product, product_version, latitude, longitude,
                start_date, end_date, variables, settings) -> str
EnvironmentCache(cache_dir).get(key) -> dict | None
EnvironmentCache(cache_dir).put(key, payload) -> None
```

- Canonical JSON (sorted keys, compact separators), variables sorted; every
  input changes the key.
- Writes are atomic via a same-directory temporary file and `os.replace`.
- Corrupt/missing entries are cache misses. Non-finite JSON is rejected.
- Only 64-character hex SHA-256 keys are accepted, preventing path traversal.

### `src/environment.py`

```python
EnvironmentUnavailable(message, *, providers=())
load_power_environment(cache, *, latitude, longitude, start_date, end_date,
                       variables=("T2M","PRECTOTCORR","GWETTOP"),
                       cache_ttl_seconds=604800, allow_network=True,
                       fetcher=..., normalizer=..., now=...) -> dict
load_smap_environment(cache, *, latitude, longitude, start_date, end_date,
                      point_id, cache_ttl_seconds=604800,
                      allow_network=True, fetcher=..., token=None,
                      token_path=None, now=...) -> dict
load_environment(cache, *, latitude, longitude, start_date, end_date, point_id,
                 power_variables=..., power_ttl_seconds=604800,
                 smap_ttl_seconds=604800, allow_network=True,
                 power_loader=..., smap_loader=..., token=None,
                 token_path=None, now=...) -> dict
```

- Fresh cache returns immediately with no network call; `allow_network=False`
  still serves fresh cache.
- Fetch result is normalized then stored.
- Failed fetch with a stale cache returns it with:
  `{"code": "STALE_CACHE", "provider": "...", "cache_age_seconds": <number>,
  "retrieved_at": "...", "message": "..."}`.
- No cache and no network -> `EnvironmentUnavailable`; an auth failure includes
  the `tools/appeears_login.py` hint.
- Each loader result adds `warnings`, `request`, and
  `cache={hit, stale, age_seconds}` plus the normalized provider fields.
- `load_environment` returns `{"request", "sources": {"power", "smap"},
  "warnings"}`. One provider failure returns a partial result with
  `POWER_UNAVAILABLE` / `SMAP_UNAVAILABLE`; both failing raises.
- Missing observations are never zero-filled.

### Cache TTL

Both providers default to `604800` seconds (7 days). This is an explorer
freshness policy, not a provider SLA; callers can override it.

## Example

```python
from src.environment import load_environment
from src.environment_cache import EnvironmentCache

env = load_environment(
    EnvironmentCache("Q:/CycleAlgo/fosol-cycle-engine/.cache/environment"),
    latitude=24.3767,
    longitude=88.6029,
    start_date="2025-01-01",
    end_date="2025-01-03",
    point_id="rajshahi",
)
```

SMAP requires a token file created by `tools/appeears_login.py`; POWER needs
no credentials.

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
test_corrupt_cache_is_a_miss (test_environment.EnvironmentCacheTests.test_corrupt_cache_is_a_miss) ... ok
test_invalid_key_and_non_finite_payload_are_rejected (test_environment.EnvironmentCacheTests.test_invalid_key_and_non_finite_payload_are_rejected) ... ok
test_put_and_get_round_trip (test_environment.EnvironmentCacheTests.test_put_and_get_round_trip) ... ok
test_auth_failure_hint_is_surfaced (test_environment.EnvironmentLoaderTests.test_auth_failure_hint_is_surfaced) ... ok
test_fresh_cache_avoids_network (test_environment.EnvironmentLoaderTests.test_fresh_cache_avoids_network) ... ok
test_fresh_cache_works_without_network (test_environment.EnvironmentLoaderTests.test_fresh_cache_works_without_network) ... ok
test_no_cache_and_failure_raises (test_environment.EnvironmentLoaderTests.test_no_cache_and_failure_raises) ... ok
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
test_fill_and_empty_become_none_not_zero (test_environment.SmapParseTests.test_fill_and_empty_become_none_not_zero) ... ok
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
test_timeout_is_bounded (test_environment.SmapRequestTests.test_timeout_is_bounded) ... ok
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
Ran 73 tests in 0.062s

OK
```

## Live SMAP smoke summary (sanitized)

A new live AppEEARS point task was run through the implemented client on
2026-11-06 for Rajshahi (24.3767 N, 88.6029 E), 2025-01-01 through
2025-01-03. No token or authorization header is reproduced anywhere.

```text
task_name          fosol-e3-code-smoke-20261106-0925
submit_status      pending
task_id            b9f568a1-d5e8-4600-b2f8-814e1a6f8c35
status_transitions pending -> queued -> processing -> done
bundle_files       fosol-e3-code-smoke-20261106-0925-SPL4SMGP-008-results.csv
                   fosol-e3-code-smoke-20261106-0925-granule-list.txt
                   fosol-e3-code-smoke-20261106-0925-request.json
                   fosol-e3-code-smoke-20261106-0925-SPL4SMGP-008-metadata.xml
                   README.md
csv_columns        ID,Latitude,Longitude,Date,SMAP_Tile,
                   SPL4SMGP_008_Line_Y_9.00805km,
                   SPL4SMGP_008_Sample_X_9.00805km,
                   SPL4SMGP_008_Geophysical_Data_sm_rootzone,
                   SPL4SMGP_008_Geophysical_Data_sm_surface
parsed_product     SPL4SMGP 008
observations       24
observation_start  2025-01-01T01:30:00+00:00
observation_end    2025-01-03T22:30:00+00:00
missing_counts     {'sm_surface': 0, 'sm_rootzone': 0}
point              {'id': 'rajshahi', 'latitude': 24.3767, 'longitude': 88.6029}
```

The prior smoke CSV copied to
`tests/fixtures/appeears_spl4smgp_rajshahi_20250101_20250103.csv` is real and
unedited; the new run independently reproduced the same columns and shape.

## Test coverage map

- POWER normalization of the real fixture, units, version, resolution,
  observation dates, messages, and `retrieved_at`.
- POWER `-999`/null -> `None`, real `0.0` preserved, `NaN`/infinity -> `None`.
- POWER malformed responses (non-object, missing header/metadata/fill/range,
  bad date, non-numeric) raise `PowerApiError`.
- POWER retry on 429 then success; retry on 5xx then success; retry on network
  failure; 422 raises once with no sleep.
- AppEEARS submission URL, method, bearer header, exact body, MM-DD-YYYY dates,
  product/layers, and coordinates.
- Polling queues, processing, done; 303; task error; bounded timeout.
- 401/403 auth message, token-file load, expiry, missing file, env override.
- Bundle selection of the results CSV and rejection without one.
- Real CSV parse: 24 observations, sorted ISO timestamps, point, variables,
  units, fill value, missing counts.
- Synthetic CSV: `-9999` and empty -> `None`, not zero.
- Malformed CSV: empty, missing column, bad timestamp, non-numeric, empty ID.
- Cache round-trip, corrupt entry, path-traversal key rejection, non-finite
  payload rejection.
- Fresh cache avoids the fetcher; fresh cache works with network disabled;
  stale cache warning includes `cache_age_seconds`; no cache raises.
- Orchestrator partial success, both-success JSON serialization, both-failure
  raise, and auth-hint propagation.
- Cache keys are stable for variable order and change for every field.

## Decisions recorded

- POWER `header.start`/`header.end` are required; the normalizer does not
  invent an observation range from partial data.
- POWER metadata and observation parameter sets must match.
- Both SMAP layers are always requested and parsed; no QA layer is claimed.
- SMAP `select_result_file` requires a filename containing `results`; it does
  not silently use a statistics CSV.
- The 7-day TTL is an explorer cache policy, not a provider freshness claim.
- `retrieved_at` is process retrieval time; observation dates remain the
  provider's observation period.
- A cache write failure does not discard a successfully fetched response.

## Not implemented (out of scope)

- Calendar evaluator (E4), soil/water checks, branch expansion, historical
  seasonal replay, metrics, response envelope, HTTP wrapper.
- District aggregation: the SMAP query is a documented point, not a district
  average.
- Any moisture threshold or forecast interpretation.
