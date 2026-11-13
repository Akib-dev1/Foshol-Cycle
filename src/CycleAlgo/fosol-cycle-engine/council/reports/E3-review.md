# E3 — Environmental loading, caching, missing values: code review

**Reviewer:** Code Reviewer (Fosol-Cycle v1 council)
**Date:** 2026-11-06
**Scope:** `src/power_api.py`, `src/smap_api.py`, `src/environment_cache.py`,
`src/environment.py`, `tests/test_environment.py`, `tests/fixtures/*`,
`docs/ENVIRONMENTAL_DATA.md`, `council/reports/E3-builder.md`
**Spec context:** `../v1.md` §2, §7, §9.3, §15
**Environment:** Windows, Python 3.13.2, engine root `Q:\CycleAlgo\fosol-cycle-engine`

**Final status (round 2): PASS.** The round-1 FAIL and table below are historical;
the four blocking findings were fixed and re-verified. See “Round 2 — re-review”.

**Data safety:** `Data/DataNEVERBEUSED/` was not read, listed, or modified. No file
under `Data/` was modified by this review. The AppEEARS token file was never read;
all credential probes used dummy strings. No source or test file was changed; this
report is the only repo addition.

**Probe process note:** all reported probe results below use temporary files, fake
openers, and one loopback HTTP server. One early, throwaway cache probe (before its
cache key was corrected) made a single unauthenticated POWER request and received
HTTP 422. It did not use the AppEEARS token, did not touch AppEEARS, and stored no
provider data. The corrected probe and the unit suite are offline.

## Verdict

**FAIL — the happy path and the missing-value safety rules pass, but four
medium correctness/validation findings block E3 sign-off.**

The implementation correctly keeps missing values as `None`, does not zero-fill,
does not turn provider failure into a pass, warns on stale cache use, and does not
leak the token. The defects below are in cache identity, malformed CSV validation,
corrupt-cache validation, and AppEEARS retry behaviour; findings 1–4 can produce
misleading metadata, double-counted observations, a non-JSON response, or avoidable
provider unavailability. Findings 5–7 are low-severity hardening gaps. Re-run of
E3 is required after findings 1–4 are fixed; findings 5–7 are recommended before
E7 starts consuming this layer.

> **Round 2 update:** the builder fixed findings 1–4. The final re-review verdict is
> **PASS** with residual low findings; see “Round 2 — re-review” at the end. The
> round-1 FAIL below is retained as the historical review.

| Gate | Result |
|---|---|
| Unit tests | **PASS** — 73/73, 41 E3 tests, `OK`, exit 0 |
| POWER normalization | **PASS** — fill/null/non-finite -> `None`; `-998.999` retained; malformed shape rejected |
| POWER retries | **PASS** — 429/5xx/network/timeout bounded; 422 not retried |
| SMAP token/task flow | **PASS** — missing/expired token, 403, `queued`, `done`, `303`, unknown, `error`, bounded timeout |
| SMAP CSV | **PASS** on valid real/synthetic data; duplicate-timestamp validation gap (finding 2) |
| Cache key/freshness | **PASS** for single-writer and normal cache; **FAIL** for `point_id` identity (finding 1) and non-finite JSON (finding 3) |
| Cache concurrency | **PASS** for single-writer atomicity; low-severity `PermissionError` under same-key Windows writers (finding 5) |
| Orchestrator | **PASS** — POWER ok/SMAP fail, POWER fail/SMAP ok, both fail |
| Missing-value safety | **PASS** — no zero-fill, no failed-provider pass |
| Token secrecy | **PASS** — no token in output/errors/literals; token file ignored |
| No live network in unit suite | **PASS** — all provider calls inject an opener/fetcher |
| Date/time, sorting, bools | **PASS** with low bool-control gap (finding 7) |
| Overall | **FAIL** — findings 1–4 |

## Commands and real output

### 1. Full unit suite

From the engine root:

```powershell
cd Q:\CycleAlgo\fosol-cycle-engine
cmd /c "set PYTHONIOENCODING=utf-8&& python -X utf8 -m unittest discover -s tests -v 2>&1"
```

Real output:

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
Ran 73 tests in 0.069s

OK
```

Exit code check:

```powershell
cmd /c "set PYTHONIOENCODING=utf-8&& python -X utf8 -m unittest discover -s tests -v >nul 2>&1"; Write-Output "EXIT:$LASTEXITCODE"
```

```text
EXIT:0
```

### 2. Adversarial probes

Probe scripts were written under `%TEMP%\opencode\` outside the repo. They used
temporary cache directories and fake `opener`/`fetcher` callables; no provider call
was made by the final probe set.

```powershell
python -X utf8 "$env:TEMP\opencode\e3_probe.py"
python -X utf8 "$env:TEMP\opencode\e3_cache_concurrency.py"
python -X utf8 "$env:TEMP\opencode\e3_cache_nan.py"
python -X utf8 "$env:TEMP\opencode\e3_orch_auth.py"
python -X utf8 "$env:TEMP\opencode\e3_appeears_429.py"
python -X utf8 "$env:TEMP\opencode\e3_303_local.py"
python -X utf8 "$env:TEMP\opencode\e3_static_checks.py"
```

Real output (selected; long JSON payloads are abbreviated, and the repeated
`PermissionError` list in `cache_concurrent_put` is summarized as a count):

```text
=== POWER ===
power_429_then_200: RETURN ('v2.10.3', 2)
power_422_no_retry: RAISE PowerApiError code=POWER_API_ERROR status=422 msg='POWER API returned HTTP 422. bad range'
power_timeout_retries: RAISE PowerApiError code=POWER_NETWORK_ERROR status=None msg='POWER request failed: TimeoutError.'
power_network_error_retries: RAISE PowerApiError code=POWER_NETWORK_ERROR status=None msg='POWER request failed: URLError.'
power_malformed_json: RAISE PowerApiError code=POWER_API_ERROR status=None msg='POWER returned a response that is not JSON.'
power_non_object_json: RAISE PowerApiError code=POWER_API_ERROR status=None msg='POWER returned a non-object JSON response.'
power_missing_fill_value: RAISE PowerApiError code=POWER_API_ERROR status=None msg='POWER response has a non-numeric fill_value.'
power_fill_vs_valid_minus_999: RETURN {'minus_999': None, 'near': -998.999}
power_non_finite_observations: RETURN {'2025-01-01': None, '2025-01-02': None}
power_non_finite_fill: RAISE PowerApiError code=POWER_API_ERROR status=None msg='POWER response has a non-finite fill_value.'
power_url_encoding: RETURN ('start=20250101&end=20250103&latitude=-24.3767&longitude=-88.6029&community=AG&parameters=T2M%2CA+B%2CX%26Y&format=JSON&units=metric&time-standard=LST', {'start': ['20250101'], 'end': ['20250103'], 'latitude': ['-24.3767'], 'longitude': ['-88.6029'], 'community': ['AG'], 'parameters': ['T2M,A B,X&Y'], 'format': ['JSON'], 'units': ['metric'], 'time-standard': ['LST']})
power_bool_latitude: RAISE ValueError code=None status=None msg='latitude must be a finite number'
power_bool_max_retries: RETURN 'accepted, calls=2'
=== APPEEARS ===
token_missing: RAISE AppEEarsAuthError code=APPEEARS_AUTH status=None msg='AppEEARS token file not found; run tools/appeears_login.py'
token_expired: RAISE AppEEarsAuthError code=APPEEARS_AUTH status=None msg='AppEEARS token expired or invalid; run tools/appeears_login.py'
token_raw_not_json: RAISE AppEEarsAuthError code=APPEEARS_AUTH status=None msg='AppEEARS token file is unreadable; run tools/appeears_login.py'
token_malformed_expiration_accepted: RETURN True
appeears_403: RAISE AppEEarsAuthError code=APPEEARS_AUTH status=None msg='AppEEARS token expired or invalid; run tools/appeears_login.py'
appeears_202_location_without_body_task_id: RAISE AppEEarsResponseError code=APPEEARS_RESPONSE status=None msg='AppEEARS task response has no task_id.'
appeears_429_no_retry: RAISE AppEEarsResponseError code=APPEEARS_RESPONSE status=429 msg='AppEEARS returned HTTP 429.'
appeears_303_done: RETURN {'task_id': 'task-1', 'status': 'done'}
appeears_queued_done: RETURN ({'status': 'done'}, 4)
appeears_unknown_status: RAISE AppEEarsResponseError code=APPEEARS_TASK_STATUS status=None msg='AppEEARS task task-1 reported an unknown status.'
appeears_error_status: RAISE AppEEarsResponseError code=APPEEARS_TASK_ERROR status=None msg='AppEEARS task task-1 failed: bad task'
appeears_timeout: RAISE AppEEarsError code=APPEEARS_TIMEOUT status=None msg='AppEEARS task task-1 did not finish within the timeout.'
bundle_without_csv: RAISE AppEEarsResponseError code=APPEEARS_RESPONSE status=None msg='AppEEARS bundle contains no usable results CSV.'
bundle_invalid_entry: RAISE AppEEarsResponseError code=APPEEARS_RESPONSE status=None msg='AppEEARS bundle entry has no file_name.'
select_non_dict: RAISE AttributeError code=None status=None msg="'NoneType' object has no attribute 'get'"
download_url_encoding: RETURN ('ID,Latitude,Longitude,Date\n', 'https://appeears.earthdatacloud.nasa.gov/api/bundle/a%2Fb/c%20d')
=== CSV ===
csv_missing_column: RAISE AppEEarsResponseError code=APPEEARS_RESPONSE status=None msg='AppEEARS results CSV is missing the Geophysical_Data_sm_surface column.'
csv_blank_and_fill: RETURN {'synthetic': [{'timestamp': '2025-01-01T01:30:00+00:00', 'sm_surface': None, 'sm_rootzone': 0.2}, {'timestamp': '2025-01-01T04:30:00+00:00', 'sm_surface': None, 'sm_rootzone': None}, {'timestamp': '2025-01-01T07:30:00+00:00', 'sm_surface': 0.18, 'sm_rootzone': 0.24}]}
csv_nan: RETURN {'timestamp': '2025-01-01T01:30:00+00:00', 'sm_surface': None, 'sm_rootzone': 0.2432147}
csv_invalid_date: RAISE AppEEarsResponseError code=APPEEARS_RESPONSE status=None msg='AppEEARS results contain an invalid UTC timestamp.'
csv_duplicate_timestamp: RETURN (25, ['2025-01-01T01:30:00+00:00', '2025-01-01T01:30:00+00:00'])
csv_extra_column: RETURN {'timestamp': '2025-01-01T01:30:00+00:00', 'sm_surface': 0.1858516, 'sm_rootzone': 0.2432147}
csv_non_ascii_id: RETURN 'রাজশাহী'
csv_short_row: RETURN (25, {'timestamp': '2025-01-04T01:30:00+00:00', 'sm_surface': None, 'sm_rootzone': None})
csv_json_serializable: RETURN True
=== CACHE ===
cache_concurrent_put: value_type=dict value=79 errors=38 (all PermissionError) tmp_leftovers=[]
cache_corrupt_json: None
cache_point_id_reuse: first_point=A second_request=B second_point=A second_fetcher_calls=0
cache_stale: hit=True stale=True codes=['STALE_CACHE'] age=864000
cache_key_field_changes: distinct=9 expected=9
cache_atomic_replace_failure: raised=OSError old={'old': True}
=== ORCHESTRATOR ===
orch_power_ok_smap_fail: power=True smap=None warnings=['SMAP_UNAVAILABLE']
orch_power_fail_smap_ok: power=None smap=True warnings=['POWER_UNAVAILABLE']
orch_both_fail: RAISE providers=('POWER', 'SMAP')
=== TOKEN LEAK / TYPES ===
token_leak_in_errors: False
power_bool_value_rejected: YES
smap_bool_latitude_rejected: YES
```

Concurrency stress, same key versus distinct keys:

```text
same_key threads=2 errors=0 types=[] stray=0
same_key threads=4 errors=4 types=['PermissionError'] stray=0
same_key threads=8 errors=68 types=['PermissionError'] stray=0
distinct_keys threads=8 errors=0 types=[] stray=0
```

Corrupt cache with a non-finite JSON constant:

```text
cache.get: {'retrieved_at': '2026-11-06T12:00:00+00:00', 'observations': {'T2M': nan}}
loaded value: nan
json.dumps(allow_nan=False): ValueError: Out of range float values are not JSON compliant: nan
```

Both-provider failure with an auth cause:

```text
both_fail_message: Environmental data are unavailable from both POWER and SMAP.
contains_auth_hint: False
```

### 3. Token/secrecy and offline checks

```text
network_calls_without_opener: []
token_shaped_literals: []
```

`token_shaped_literals` scanned `src/*.py`, `tests/*.py`, `docs/*.md`,
`council/reports/*.md`, and `tools/*.py` for JWTs, long literal `Bearer` values,
and long `"token": "..."` assignments; it reported none. The token file itself was
not opened.

```powershell
git -C Q:\CycleAlgo check-ignore -v appeears_token.txt
git -C Q:\CycleAlgo ls-files | Select-String -Pattern 'token|appeears'
```

```text
.gitignore:2:/appeears_token.txt	appeears_token.txt
```

No token file is tracked. Non-blocking repo note: the root `.gitignore` that contains
this rule is itself untracked in the current working tree; it must be committed with
E3 or the ignore rule will not reach a fresh clone.

## Findings

### 1. Medium — SMAP cache key omits `point_id`, so a cached result can carry the wrong point identity

- **Files:** `src/environment.py:250-259` (key uses product, version, lat/lon,
  dates, layers, empty settings), `src/environment.py:281-288` (request stores
  `point_id`), `src/environment.py:289-295` (cached record returned unchanged).
- **Repro:** in a temp cache, call `load_smap_environment` twice with identical
  coordinates/dates but `point_id="A"` then `point_id="B"`. The first fake fetcher
  returns a normalized record with `point.id="A"`; the second fetcher counts calls.
- **Observed:**

  ```text
  cache_point_id_reuse: first_point=A second_request=B second_point=A second_fetcher_calls=0
  ```

- **Why it matters:** the observation values for identical coordinates are the same,
  but `sources.smap.point.id` is stale and does not match `request.point_id`. A
  consumer that displays or joins on `point.id` attributes the cached record to the
  wrong point label. `build_cache_key` has no `point_id` parameter, and the SMAP
  loader does not pass the id through its empty `settings` dict.
- **Fix direction:** include `point_id` in the SMAP cache key/settings, or overwrite
  the returned `point.id` with the requested id and document that coordinates alone
  key the data; add a two-call cache-identity test.

### 2. Medium — duplicate SMAP timestamps are accepted and returned

- **Files:** `src/smap_api.py:592-602` (append every row, then sort by timestamp;
  no uniqueness check), `src/smap_api.py:594-600` (missing counts also include
  duplicate rows).
- **Repro:** append the first real CSV data row again and parse it.
- **Observed:**

  ```text
  csv_duplicate_timestamp: RETURN (25, ['2025-01-01T01:30:00+00:00', '2025-01-01T01:30:00+00:00'])
  ```

- **Why it matters:** a duplicate 3-hourly row is counted twice in downstream
  averages, coverage, and missing-count calculations. The parser validates columns,
  dates, coordinates, and values, but not timestamp uniqueness. The real provider
  data has one row per timestamp, so this is a malformed-response path, not a normal
  fixture defect.
- **Fix direction:** reject duplicate timestamps with `AppEEarsResponseError`, or
  deduplicate with an explicit warning/count; add a duplicate-row test.

### 3. Medium — corrupt cache JSON containing `NaN`/`Infinity` is accepted as fresh, then breaks JSON serialization

- **Files:** `src/environment_cache.py:64-70` (`json.loads` defaults accept the
  non-standard constants; `get` only checks `dict`), `src/environment.py:111-112`
  (fresh cached record returned), `src/environment.py:127-130` (a cache-write
  `OSError` is swallowed; no cache-read payload validation is done).
- **Repro:** write a valid cache filename containing
  `{"retrieved_at":"2026-11-06T12:00:00+00:00","observations":{"T2M":NaN}}`, then
  load it through `load_power_environment` with a fetcher that fails.
- **Observed:**

  ```text
  cache.get: {'retrieved_at': '2026-11-06T12:00:00+00:00', 'observations': {'T2M': nan}}
  loaded value: nan
  json.dumps(allow_nan=False): ValueError: Out of range float values are not JSON compliant: nan
  ```

- **Why it matters:** `put` rejects non-finite payloads, but `get` does not. A
  corrupt/older cache entry bypasses the write-time guard and produces a loader
  result that cannot be serialized to the documented JSON response. This contradicts
  the builder's "corrupt cache entry is a miss" claim for this class of corruption.
- **Fix direction:** pass a rejecting `parse_constant` to `json.loads` (or validate
  all numeric leaves) in `EnvironmentCache.get`; add a `NaN`/`Infinity` cache test.

### 4. Medium — AppEEARS HTTP 429/5xx responses are not retried, unlike POWER

- **Files:** `src/smap_api.py:200-222` (`_open_bytes` raises immediately; no
  `max_retries`/backoff), `src/smap_api.py:225-272` (request helpers have no retry
  loop). POWER implements bounded retries at `src/power_api.py:196-223`.
- **Repro:** call `submit_point_task` with an opener returning HTTP 429 followed by a
  valid `{"status":"pending","task_id":"task-1"}` response.
- **Observed:**

  ```text
  type= AppEEarsResponseError status= 429 requests= 1
  ```

- **Why it matters:** §15 requires bounded retries and provider rate-limit handling.
  A transient AppEEARS 429/5xx makes SMAP unavailable for the request instead of
  retrying; the failure is safe (checks remain unknown), but the spec requirement is
  unmet and the UI loses a provider that would have recovered.
- **Fix direction:** apply the same bounded exponential backoff to AppEEARS 429/5xx
  (and optionally network/timeout), without retrying 401/403/other 4xx; add tests
  analogous to the POWER retry tests.

### 5. Low — concurrent same-key cache writes can raise `PermissionError` on Windows; the loader silently skips caching

- **Files:** `src/environment_cache.py:80-94` (`os.replace` at line 88),
  `src/environment.py:127-130` (`except OSError: pass` around `cache.put`).
- **Repro:** run 4 or 8 threads, each writing the same 64-hex key 50 times, then read
  the final file.
- **Observed:**

  ```text
  same_key threads=2 errors=0 types=[] stray=0
  same_key threads=4 errors=4 types=['PermissionError'] stray=0
  same_key threads=8 errors=68 types=['PermissionError'] stray=0
  distinct_keys threads=8 errors=0 types=[] stray=0
  ```

  The final cache file is valid and no `.tmp` files remain; single-writer atomic
  replacement and the old-file-preservation path pass.
- **Why it matters:** on Windows, concurrent requests refreshing the same key can
  lose their cache write. The loader still returns the valid fetched response, so
  this is not data corruption, but it causes repeated fetches/cache stampede and a
  direct `EnvironmentCache.put` caller sees an unexpected `OSError`.
- **Fix direction:** retry `os.replace` on Windows sharing violations with a short
  bounded backoff, or serialize writers per key with a lock; add a concurrent
  same-key test.

### 6. Low — a present-but-unparseable token `expiration` bypasses expiry rejection

- **Files:** `src/smap_api.py:171-177` (`_parse_timestamp` returns `None` on invalid
  text; `expiration is None` means no check), `src/smap_api.py:124-137`.
- **Repro:** write `{"token": "DUMMY", "expiration": "not-a-date"}` and call
  `load_token(..., now=T0)`.
- **Observed:**

  ```text
  token_malformed_expiration_accepted: RETURN True
  ```

- **Why it matters:** a malformed or missing expiry is treated as "unknown, therefore
  accept". An expired token is then rejected only by the provider's 403. This does
  not leak or invent data, but it weakens the documented "known expired token raises
  before any request" guarantee.
- **Fix direction:** if `expiration` is present but not parseable, raise
  `AppEEarsAuthError` (or re-login); keep the explicit-missing-expiry policy
  documented.

### 7. Low — boolean control parameters are accepted as integers

- **Files:** `src/power_api.py:175-180` (validates `max_retries`, `timeout`,
  `backoff_seconds` numerically but not `bool`), `src/smap_api.py:352-355` (same for
  `timeout_seconds`/`poll_seconds`), `src/environment.py:111`/`:170` (TTL floats not
  bool-checked).
- **Repro:** `fetch_power_daily(..., max_retries=True, ...)` with a 503 then a valid
  response.
- **Observed:**

  ```text
  power_bool_max_retries: RETURN 'accepted, calls=2'
  power_bool_latitude: RAISE ValueError code=None status=None msg='latitude must be a finite number'
  smap_bool_latitude_rejected: YES
  power_bool_value_rejected: YES
  ```

- **Why it matters:** data values and coordinates correctly reject `bool`, but a
  caller passing `True` for `max_retries` silently gets one retry instead of a type
  error. `timeout=True`/`cache_ttl_seconds=True` similarly mean 1 second. This is type
  hygiene, not a data-safety defect.
- **Fix direction:** reject `isinstance(value, bool)` for integer/float control
  parameters, as `_coordinate`/`_number` already do.

## Test coverage gaps

Round-1 state (historical). Round 2 added regression tests for findings 1–4:
`test_point_id_is_part_of_the_key`, `test_smap_cache_is_separated_by_point_id`,
`test_smap_default_point_id_is_stable_coordinate_string`,
`test_identical_duplicate_timestamp_is_deduplicated`,
`test_conflicting_duplicate_timestamp_is_rejected`,
`test_non_finite_json_constants_are_a_miss`, `test_non_finite_cache_is_refetched`,
and the `SmapRetryTests` matrix. Remaining probe-only behaviours are:

- Same-key concurrent cache writes (finding 5).
- Malformed token `expiration` (finding 6).
- Boolean control parameters (finding 7).
- `202` with `Location` but no body `task_id`, the both-fail auth-hint path, and the
  round-1 CSV short-row/out-of-range notes listed under other observations.

## Other observations (not counted as blocking findings)

- **202 without body `task_id` but with `Location`.** `submit_point_task` reads only
  the body and rejects `{"status":"pending"}` when the task id is in a `Location`
  header (`smap_api.py:328-330`). The live AppEEARS smoke from the builder returned
  `202 + {status, task_id}`, so this is conditional: if the provider contract can
  return Location-only 202, the client fails. No official evidence for that case was
  found in this review.
- **`select_result_file([None])`** raises `AttributeError` rather than a typed
  `AppEEarsResponseError` (`smap_api.py:450-460`). Normal `get_bundle` output is
  validated, so this only affects direct callers.
- **Both-provider failure loses the auth hint.** `load_environment` raises a new
  generic `EnvironmentUnavailable` at `environment.py:371-375`; the inner
  `AppEEARS token expired...` cause is discarded. Output:
  `both_fail_message: Environmental data are unavailable from both POWER and SMAP.`
  `contains_auth_hint: False`.
- **Truncated CSV row accepted as all-missing.** Appending a row with only
  `ID,Latitude,Longitude,Date` returns 25 observations, with the last both `None`.
  `smap_api.py:594-600` treats `DictReader`'s `None` for absent layer cells as a
  legitimate missing value. This is lenient; it may hide a truncated file.
- **303 redirect caveat.** A local-server probe showed real `urllib` follows a 303
  to a final `{"status":"done"}` and `wait_for_task` returns done. The direct
  `HTTPError(303)` unit test is not representative of the redirect path. If the
  provider's 303 `Location` targets a bundle/non-status document instead of a status
  JSON, the client would report an unknown status rather than done; this is an
  integration risk, not confirmed against the live API. Probe result:
  `303_followed_to_status_json: {'status': 'done'}`.
- **Out-of-range observations are not rejected.** Neither normalizer knows the
  requested date range, so a structurally valid response containing dates outside
  the requested range would be cached under the requested key. The evaluator's
  coverage logic (E7) must not assume every requested date is present.
- **Docs wording nit (round 2 fixed):** round 1 noted that
  `docs/ENVIRONMENTAL_DATA.md:82` said the token is never "returned", although
  `load_token` necessarily returns it to the caller. The round-2 docs now say it is
  never printed, logged, included in an error, or exposed in a response.

## What passed

- **POWER:** 429 then 200 succeeds on the second request; 422 raises once with
  `status_code=422` and no sleep; timeout/URL/network errors are bounded; malformed
  JSON, non-object JSON, missing `header`, missing `fill_value`, invalid dates, and
  non-numeric observations raise `PowerApiError`; `-999`/`null`/`NaN`/`Infinity`
  become `None`, `0.0` survives, `-998.999` survives, and non-finite fill metadata is
  rejected. A legitimate observation of exactly `-999` is indistinguishable from the
  documented sentinel and is correctly treated as missing; that is the provider
  contract, not a coercion bug. URL encoding round-trips spaces, `&`, commas, and
  negative coordinates.
- **SMAP request flow:** missing/expired token and 403 produce the documented auth
  message without the dummy token; raw non-JSON token files are rejected as
  documented; `pending`/`queued`/`processing` are polled, `done` and injected 303
  return, `error`/unknown status/timeout are typed; bundle selection excludes
  statistics, multiple results CSVs are rejected, bundle entries are validated, and
  download URLs percent-encode task/file ids.
- **SMAP CSV:** missing column, invalid date, and non-numeric values are rejected;
  blank, `-9999`, `nan`, and `inf` become `None`; extra columns and a non-ASCII point
  id are accepted; output is JSON-serializable; 24 real 3-hourly observations sort
  from `2025-01-01T01:30:00+00:00` to `2025-01-03T22:30:00+00:00`.
- **Cache:** fresh hit avoids the fetcher; `allow_network=False` serves fresh cache;
  stale cache after failure returns `STALE_CACHE` with age 864000 s; syntactically
  corrupt JSON is a miss; all key fields (including `point_id` in round 2) change the
  key; invalid keys and non-finite `put` payloads are rejected; a simulated
  `os.replace` failure leaves the old file intact; path traversal is blocked.
- **Orchestrator:** POWER ok/SMAP fail gives `smap=None` plus `SMAP_UNAVAILABLE`;
  POWER fail/SMAP ok gives `power=None` plus `POWER_UNAVAILABLE`; both fail raises
  with providers `("POWER", "SMAP")`; both ok is JSON-serializable.
- **Secrecy/offline:** no token-shaped literals found; no token in error strings;
  token file is ignored and not tracked; no test call to a provider function omits
  an injected opener; suite runtime 0.069 s. No mutable default arguments were found
  (`DEFAULT_POWER_VARIABLES` and `DEFAULT_LAYERS` are tuples).

---

# Round 2 — re-review

**Date:** 2026-11-06
**Changed files reviewed:** `src/environment_cache.py`, `src/smap_api.py`,
`src/environment.py`, `tests/test_environment.py`, `docs/ENVIRONMENTAL_DATA.md`,
`council/reports/E3-builder-round2.md`.
**Spec context:** `../v1.md` §15, with the round-1 cache/identity requirements.
**Data safety:** no `Data/` or `DataNEVERBEUSED/` access; no token file read; all
round-2 probes used temp files, fake openers, or a loopback HTTP server.

## Round-2 final verdict

**PASS — all four round-1 blocking findings are fixed, and no new blocking
regression was found. 86/86 tests pass.** The residual items are the round-1 low
findings (concurrent same-key cache writes, malformed token expiry, bool control
parameters) and several low-risk implementation notes (POST 503 idempotency,
retry time versus the task timeout, and the default-id/CSV-id assumption). None
changes missing-value safety or creates a known wrong observation in the normal
path.

| Round-1 finding | Round-2 status | Evidence |
|---|---|---|
| 1. SMAP cache key omitted `point_id` | **FIXED** | cache-key payload now includes `point_id`; A/B at same coordinates produce two fetches, two cache files, and correct point ids |
| 2. Duplicate SMAP timestamps accepted | **FIXED** | identical duplicates dedupe with `duplicate_timestamps=1`; conflicting duplicates raise; missing counts use unique observations |
| 3. `NaN`/`Infinity` cache JSON accepted | **FIXED** | strict parser returns a miss for all non-finite constants and float overflow; loader refetches |
| 4. AppEEARS 429/5xx not retried | **FIXED** | bounded GET retries for 429/5xx/network; POST retries 429/503; 403 remains immediate; backoff and budget tested |
| 5. Windows same-key concurrent cache writes | **UNCHANGED low** | `os.replace` still raises `PermissionError` under 4–8 same-key writers; loader swallows the write error |
| 6. Malformed token expiration accepted | **UNCHANGED low** | `_parse_timestamp` still returns `None` for malformed text; token accepted until provider 403 |
| 7. Bool control parameters | **PARTIALLY FIXED low** | SMAP retry budget/backoff now reject bool; POWER retry/timeout/backoff and TTL params still accept bool |

## Verification of the four fixes

### Finding 1 — SMAP cache identity now includes `point_id` — PASS

- **Code:** `src/environment_cache.py:16-50` adds keyword-only `point_id` and puts it
  in the canonical payload at line 41. `src/environment.py:250-262` resolves it,
  keys the SMAP entry, and `:284-291` returns it in `request`. `src/smap_api.py:116-129`
  defines `default_point_id`/`resolve_point_id`; `:352-372` uses the resolved id in
  the submit body; `:749-771` uses it for the full fetch task name/body.
- **Tests:** `tests/test_environment.py:741-745` (`test_point_id_is_part_of_the_key`),
  `:957-985` (`test_smap_cache_is_separated_by_point_id`), `:987-1021`
  (`test_smap_default_point_id_is_stable_coordinate_string`).
- **Targeted repro:**

  ```text
  cache_key_none_vs_a_b: RETURN (True, True)
  smap_point_id_cache: {'first': 'point-a', 'second': 'point-b', 'third': 'point-a', 'calls': ['point-a', 'point-b'], 'third_hit': True, 'files': 2}
  smap_default_point_id: 24.3767,88.6029 24.3767,88.6029 calls ['24.3767,88.6029'] hit True
  orchestrator_default_point_id: 24.3767,88.6029 ['24.3767,88.6029']
  ```

- **Result:** PASS. Two labels at the same coordinates no longer share a cache entry;
  the third A call is a hit and does not fetch again. `load_environment` resolves the
  same default once and passes it to the SMAP loader.

### Finding 2 — duplicate timestamps deduplicated/rejected — PASS

- **Code:** `src/smap_api.py:661-721` collects observations by ISO timestamp in
  `unique`; identical duplicates increment `duplicate_timestamps`; conflicting values
  raise `AppEEarsResponseError`; `missing_counts` is computed over unique observations
  at `:715-721`; output includes `duplicate_timestamps` at `:740`.
- **Tests:** `tests/test_environment.py:665-673` (identical duplicate -> 24, count 1,
  missing counts unchanged) and `:675-680` (conflicting duplicate rejected).
- **Targeted repro:**

  ```text
  dedupe_identical: RETURN (24, 1, {'sm_surface': 0, 'sm_rootzone': 0})
  dedupe_conflict: RAISE AppEEarsResponseError code=APPEEARS_RESPONSE status=None msg='AppEEARS results contain conflicting values for timestamp 2025-01-01T01:30:00+00:00.'
  dedupe_missing_counts: RETURN (3, 1, {'sm_surface': 2, 'sm_rootzone': 1})
  dedupe_triple: RETURN (24, 2)
  parse_json_serializable: RETURN True
  ```

- **Result:** PASS. Exact duplicates are counted and dropped; a conflicting duplicate
  is rejected rather than silently picking one; missing counts are not inflated by
  duplicate rows.

### Finding 3 — strict cache JSON — PASS

- **Code:** `src/environment_cache.py:53-61` defines rejecting
  `parse_constant`/`parse_float`; `:76-89` passes both to `json.loads` and treats any
  `ValueError` as a cache miss. `put` still rejects non-finite writes.
- **Tests:** `tests/test_environment.py:771-785` covers `NaN`, `Infinity`,
  `-Infinity`, and `1e999`; `:1023-1058` verifies a NaN-containing cache is a miss and
  the loader refetches the valid value.
- **Targeted repro:**

  ```text
  cache_strict NaN None
  cache_strict Infinity None
  cache_strict -Infinity None
  cache_strict 1e999 None
  cache_strict -1e999 None
  cache_strict 1e309 None
  cache_valid_float {'retrieved_at': 'x', 'value': 1.5}
  cache_nan_is_miss: None
  cache_nan_refetch: 1 15.21
  ```

- **Result:** PASS. Non-finite and overflowing cache numbers are misses; a valid
  finite float still round-trips; the loader refetches instead of returning `nan`.

### Finding 4 — AppEEARS bounded retries — PASS

- **Code:** `src/smap_api.py:218-224` defines retryable statuses (GET 429/5xx; POST
  429/503); `:227-277` implements bounded backoff and retry; `:280-321` and `:324-349`
  pass the budget through JSON/byte requests; `:352-405`, `:418-488`, `:491-539`,
  `:562-589`, and `:749-822` expose it through submit/poll/bundle/download/fetch.
  401/403 is checked before retry at `:259-260`; POST 500/network is not retried.
- **Tests:** `tests/test_environment.py:458-527` covers POST 429/503 success, GET 5xx
  success, bounded exhaustion (3 requests with `max_retries=2`), and POST 500 no retry.
- **Targeted repro:**

  ```text
  post_429_then_ok: RETURN ({'status': 'pending', 'task_id': 't1'}, 2)
  post_503_then_ok: RETURN ({'status': 'pending', 'task_id': 't1'}, 2)
  post_500_no_retry: RAISE AppEEarsResponseError code=APPEEARS_RESPONSE status=500 msg='AppEEARS returned HTTP 500.'
  post_network_no_retry: RAISE AppEEarsError code=APPEEARS_NETWORK_ERROR status=None msg='AppEEARS request failed: URLError.'
  post_403_no_retry: RAISE AppEEarsAuthError code=APPEEARS_AUTH status=None msg='AppEEARS token expired or invalid; run tools/appeears_login.py'
  get_500_then_ok: RETURN ([{'file_id': 'results', 'file_name': 'x-results.csv', 'file_type': 'csv'}], 2)
  get_429_then_ok: RETURN ([{'file_id': 'results', 'file_name': 'x-results.csv', 'file_type': 'csv'}], 2)
  get_network_then_ok: RETURN ([{'file_id': 'results', 'file_name': 'x-results.csv', 'file_type': 'csv'}], 2)
  get_403_no_retry: RAISE AppEEarsAuthError code=APPEEARS_AUTH status=None msg='AppEEARS token expired or invalid; run tools/appeears_login.py'
  get_429_budget: RETURN ('error', 429, 3)
  submit_bool_max_retries: RAISE ValueError code=None status=None msg='max_retries must be a non-negative integer'
  submit_bool_backoff: RAISE ValueError code=None status=None msg='backoff_seconds must be a non-negative finite number'
  submit_303_still_done: RETURN {'task_id': 't1', 'status': 'done'}
  ```

  Extra GET paths and backoff:

  ```text
  wait_500_then_done: RETURN ({'status': 'done'}, 2)
  wait_network_then_done: RETURN ({'status': 'done'}, 2)
  wait_403_no_retry: RAISE AppEEarsAuthError code=APPEEARS_AUTH status=None msg='AppEEARS token expired or invalid; run tools/appeears_login.py'
  download_500_then_ok: RETURN ('ID,Latitude\n', 2)
  download_network_then_ok: RETURN ('ID,Latitude\n', 2)
  download_403_no_retry: RAISE AppEEarsAuthError code=APPEEARS_AUTH status=None msg='AppEEARS token expired or invalid; run tools/appeears_login.py'
  post_backoff_sleeps: [1.0, 2.0] calls: 3
  ```

- **Result:** PASS. GET retries cover polling, bundle, and download; POST retries are
  limited to 429/503; POST 500/network and all 401/403 responses are immediate; the
  backoff sequence is `1, 2`; a bounded budget stops at 3 attempts; 303 still means
  done.

## Regression checks on changed paths

### Cache keys and cache behaviour

- `build_cache_key` with no `point_id` and with `point_id=None` is stable; changing
  `point_id` changes the key (`cache_key_none_vs_a_b: (True, True)`).
- SMAP A/B at identical coordinates produces two fetches, two files, and a third A
  hit (`smap_point_id_cache` above). The default id is stable
  (`24.3767,88.6029`) and cached (`smap_default_point_id` above).
- POWER keys still work after the key-schema change; a second POWER load is a cache
  hit with no fetch:

  ```text
  power_cache_after_key_change: 0 True 15.21
  ```

- `load_environment` still handles POWER failure/SMAP success, both failure, and the
  default point id:

  ```text
  power_fail_smap_ok: None p ['POWER_UNAVAILABLE']
  both_fail: ('POWER', 'SMAP')
  default_point_ok: 1.0,2.0 1.0,2.0
  ```

- Round-1 cache concurrency remains a low issue, unchanged by strict parsing:

  ```text
  same_key threads=2 errors=0 types=[] stray=0
  same_key threads=4 errors=6 types=['PermissionError'] stray=0
  same_key threads=8 errors=80 types=['PermissionError'] stray=0
  distinct_keys threads=8 errors=0 types=[] stray=0
  ```

### Dedupe and missing values

- Real CSV still yields 24 observations and `duplicate_timestamps == 0`; synthetic
  missing CSV still yields 3 observations and missing counts `2/1`.
- Identical duplicate: 24 unique observations, count 1, missing counts unchanged.
- Conflicting duplicate: typed `AppEEarsResponseError`.
- Triple duplicate: 24 unique, count 2.
- Output remains JSON-serializable, including the new `duplicate_timestamps` integer.

### Strict JSON

- `NaN`, `Infinity`, `-Infinity`, `1e999`, `-1e999`, and `1e309` are all cache misses.
- A valid finite value (`1.5`) still round-trips.
- A NaN-containing cache entry is a miss and the loader refetches valid data
  (`cache_nan_refetch: 1 15.21`).
- `put` still rejects non-finite payloads.

### Retry loops and POST/403 behaviour

- POST 429/503 retry; POST 500/network do not; POST 403 is immediate auth.
- GET 429/5xx/network retry; GET 403 is immediate auth. The same policy is verified
  for `wait_for_task` and `download_result_csv`, not only bundle fetches.
- Backoff is exponential (`[1.0, 2.0]`); budget exhaustion is bounded at
  `max_retries + 1` attempts.
- 303 still returns done.
- POST retry body is re-sent intact in a loopback test:
  `post_bodies_equal: True`, `post_body_count: 2`. This also exposes the remaining
  low risk that retrying a POST 503 can duplicate a task if the server created the
  task before returning 503.
- A dummy token never appears in the retry/auth error strings:
  `token_in_error: False`.

### Docs check

`docs/ENVIRONMENTAL_DATA.md` now has the §2 provider record at `:107-127` covering
product/version, endpoint/access, authentication, usage limits/429, variables/units,
valid ranges, missing conventions, spatial/temporal resolution, coverage, publication
latency, QA availability, and representative-location association. The SMAP failures
section at `:85-97` matches the implemented GET/POST retry policy and duplicate
handling; the task-status section at `:99-105` records `queued` as observed and 303 as
done; the cache policy at `:153-171` includes `point_id` and strict JSON; and the
token wording at `:82-83` no longer claims the token is never returned. No docs/code
contradiction was found in the changed sections.

### Offline/unit-test check

The full suite ran in 0.080 s with no provider opener/fetcher left un-injected. The
static AST scan reports one apparent hit in `SmapRetryTests._submit` because the call
uses `**params`; `params` explicitly includes `"opener": opener` at
`tests/test_environment.py:461-475`, so it is not a live call. All other direct
provider calls pass an explicit opener, and all loader tests pass a fetcher/normalizer.

## Commands and real output — round 2

```powershell
cd Q:\CycleAlgo\fosol-cycle-engine
cmd /c "set PYTHONIOENCODING=utf-8&& python -X utf8 -m unittest discover -s tests -v 2>&1"
```

Real output:

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
Ran 86 tests in 0.080s

OK
```

Exit code:

```text
EXIT:0
```

Targeted probe commands and full key output:

```powershell
python -X utf8 "$env:TEMP\opencode\e3_round2_probe.py"
python -X utf8 "$env:TEMP\opencode\e3_round2_extra.py"
python -X utf8 "$env:TEMP\opencode\e3_round2_orch.py"
python -X utf8 "$env:TEMP\opencode\e3_round2_local_post.py"
```

```text
=== POINT_ID / CACHE KEY ===
cache_key_none_vs_a_b: RETURN (True, True)
smap_point_id_cache: {'first': 'point-a', 'second': 'point-b', 'third': 'point-a', 'calls': ['point-a', 'point-b'], 'third_hit': True, 'files': 2}
smap_default_point_id: 24.3767,88.6029 24.3767,88.6029 calls ['24.3767,88.6029'] hit True
orchestrator_default_point_id: 24.3767,88.6029 ['24.3767,88.6029']
=== DUPLICATE TIMESTAMPS ===
dedupe_identical: RETURN (24, 1, {'sm_surface': 0, 'sm_rootzone': 0})
dedupe_conflict: RAISE AppEEarsResponseError code=APPEEARS_RESPONSE status=None msg='AppEEARS results contain conflicting values for timestamp 2025-01-01T01:30:00+00:00.'
dedupe_missing_counts: RETURN (3, 1, {'sm_surface': 2, 'sm_rootzone': 1})
dedupe_triple: RETURN (24, 2)
parse_json_serializable: RETURN True
=== STRICT CACHE JSON ===
cache_strict NaN None
cache_strict Infinity None
cache_strict -Infinity None
cache_strict 1e999 None
cache_strict -1e999 None
cache_strict 1e309 None
cache_valid_float {'retrieved_at': 'x', 'value': 1.5}
cache_nan_is_miss: None
cache_nan_refetch: 1 15.21
=== RETRIES ===
post_429_then_ok: RETURN ({'status': 'pending', 'task_id': 't1'}, 2)
post_503_then_ok: RETURN ({'status': 'pending', 'task_id': 't1'}, 2)
post_500_no_retry: RAISE AppEEarsResponseError code=APPEEARS_RESPONSE status=500 msg='AppEEARS returned HTTP 500.'
post_network_no_retry: RAISE AppEEarsError code=APPEEARS_NETWORK_ERROR status=None msg='AppEEARS request failed: URLError.'
post_403_no_retry: RAISE AppEEarsAuthError code=APPEEARS_AUTH status=None msg='AppEEARS token expired or invalid; run tools/appeears_login.py'
get_500_then_ok: RETURN ([{'file_id': 'results', 'file_name': 'x-results.csv', 'file_type': 'csv'}], 2)
get_429_then_ok: RETURN ([{'file_id': 'results', 'file_name': 'x-results.csv', 'file_type': 'csv'}], 2)
get_network_then_ok: RETURN ([{'file_id': 'results', 'file_name': 'x-results.csv', 'file_type': 'csv'}], 2)
get_403_no_retry: RAISE AppEEarsAuthError code=APPEEARS_AUTH status=None msg='AppEEARS token expired or invalid; run tools/appeears_login.py'
get_429_budget: RETURN ('error', 429, 3)
submit_bool_max_retries: RAISE ValueError code=None status=None msg='max_retries must be a non-negative integer'
submit_bool_backoff: RAISE ValueError code=None status=None msg='backoff_seconds must be a non-negative finite number'
submit_303_still_done: RETURN {'task_id': 't1', 'status': 'done'}
=== TOKEN LEAK ===
token_in_error: False
```

Extra probe output:

```text
wait_500_then_done: RETURN ({'status': 'done'}, 2)
wait_network_then_done: RETURN ({'status': 'done'}, 2)
wait_403_no_retry: RAISE AppEEarsAuthError code=APPEEARS_AUTH status=None msg='AppEEARS token expired or invalid; run tools/appeears_login.py'
download_500_then_ok: RETURN ('ID,Latitude\n', 2)
download_network_then_ok: RETURN ('ID,Latitude\n', 2)
download_403_no_retry: RAISE AppEEarsAuthError code=APPEEARS_AUTH status=None msg='AppEEARS token expired or invalid; run tools/appeears_login.py'
post_backoff_sleeps: [1.0, 2.0] calls: 3
power_cache_after_key_change: 0 True 15.21
fetch_default_point: 24.3767,88.6029 rajshahi task-default 4
post_bodies_equal: True
post_body_count: 2
```

## Residual findings and low risks

These do not reopen the four round-1 blocking findings:

1. **Low — concurrent same-key cache writes still raise `PermissionError` on
   Windows.** `src/environment_cache.py:99-108` still has a single `os.replace`
   without a Windows sharing-violation retry; `src/environment.py:128-131` swallows
   the `OSError`. The round-2 stress run shows 6 errors with 4 threads and 80 with 8
   threads; distinct keys have none. Final cache contents remain valid.
2. **Low — malformed token `expiration` is still accepted.** `src/smap_api.py:189-195`
   treats an unparseable expiration as `None` and proceeds; the provider 403 is the
   backstop. The round-1 repro is unchanged.
3. **Low — bool control parameters are only partially rejected.** SMAP
   `max_retries`/`backoff_seconds` now reject bools (`src/smap_api.py:238-250`), but
   the POWER retry/timeout/backoff arguments (`src/power_api.py:175-180`),
   `_request_json`/`_request_bytes` timeout, and cache TTL still accept bools.
4. **Low risk — POST 503 retry is not idempotent by construction.** The loopback
   probe shows the POST body is re-sent on the second attempt. If AppEEARS creates a
   task and then returns 503, the retry can create a duplicate task. The current
   policy retries 429 and 503; 429 is safe, 503 is the remaining ambiguity. No
   provider evidence of this behavior was found.
5. **Low — retry backoff is outside the task timeout clock.** `wait_for_task` checks
   `timeout_seconds` before each poll, but `_open_bytes` can spend up to its retry
   budget sleeping inside one request; total wall time can exceed the task timeout by
   the retry window. The per-request budget is bounded, so this is a soft bound.
6. **Other round-1 probes remain unchanged:** 202-with-`Location` without body
   `task_id` is still rejected; `select_result_file` still raises `AttributeError`
   for a non-dict direct input; both-provider failure still loses the auth hint;
   truncated CSV rows are still treated as all-missing; out-of-range dates are not
   rejected by the normalizers. The docs wording about token “returned” was fixed.
7. **Low — default-id fetches still take `point.id` from the CSV.** `fetch_smap_point`
   submits the resolved default id (`24.3767,88.6029`), but `parse_appeears_csv`
   returns the CSV's `ID` column. The fixture CSV was generated with `rajshahi`, so a
   fixture-based default fetch prints body id `24.3767,88.6029` but result
   `point.id == rajshahi`. This is only a fixture artifact if AppEEARS echoes the
   submitted id; the round-2 default-id test uses a synthetic fetcher that overwrites
   `point.id`, so the real default-id round trip is not covered. The default task
   name also becomes `fosol-24.3767,88.6029-...`; whether AppEEARS accepts commas in
   `task_name` is unverified. No live default-id task was submitted in this review.
8. **Repo hygiene note:** the root `.gitignore` containing `/appeears_token.txt`
   remains untracked at review time; commit it with E3 so the token-ignore rule
   survives a fresh clone.

## Final round-2 verdict

**PASS.** All four round-1 blocking findings are verified fixed with code, tests, and
independent probes. The full suite is 86/86 `OK` (exit 0), the changed retry paths
preserve 401/403 immediacy and do not leak the dummy token, and no new blocking
regression was found. Residual items are low-severity hardening/design notes; the
POST 503 idempotency risk should be documented or avoided if AppEEARS task creation
is not idempotent.

**Round 3: no code changes, PASS stands** — 86/86 tests OK (exit 0); `src/` and `tests/` SHA-256 values match the round-2 manifest; later edits are docs/report only.
