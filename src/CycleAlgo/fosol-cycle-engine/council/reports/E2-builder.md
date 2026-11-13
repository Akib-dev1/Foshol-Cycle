# E2 — Request validation and error contract

Status: complete. Implements the §14.2 request rules and the §14.3
invalid-request error shape only. No evaluator, API calls, or successful
response envelope were added.

## Files created

- `src/request_validation.py` — validation and documented defaults.
- `src/error_contract.py` — error envelope and HTTP status mapping.
- `tests/test_request_validation.py` — 18 `unittest` tests.
- `council/reports/E2-builder.md` — this report.

No file in `Q:\CycleAlgo\Data\` was modified, and
`Data/DataNEVERBEUSED/` was not accessed. E1 files were not changed.

## Public API

```python
from src.error_contract import build_error_response, http_status_for_error
from src.request_validation import RequestValidationError, validate_explore_request

effective = validate_explore_request(payload, known_crop_ids)
```

### `RequestValidationError`

- `code == "INVALID_REQUEST"` (class attribute).
- `message: str`.
- `field: str | None`.
- Constructor: `RequestValidationError(message, field=None)`.

### `validate_explore_request(payload, known_crop_ids) -> dict`

Returns exactly these five keys, with defaults applied:

```python
{
    "district_id": ...,
    "start_date": ...,
    "first_crop_id": ...,
    "water_access": ...,
    "preference": ...,
}
```

| Field | Rule |
|---|---|
| `district_id` | Required key. Must be a string whose stripped content is non-empty. The accepted value is returned unchanged (no trimming). District support is **not** checked here; that remains E9. |
| `start_date` | Required key. Must be a string matching ASCII `YYYY-MM-DD` and a real calendar date. Returned unchanged as a string; no timezone conversion. |
| `first_crop_id` | Required key. `null`, or a string exactly present in `known_crop_ids`. Missing key, unknown IDs, and all other types are rejected. |
| `water_access` | Optional. If the key is absent, defaults to `"unknown"`. If present, must be exactly `rainfed`, `irrigation_available`, or `unknown`; `null`, numbers, booleans, and unknown strings are rejected. |
| `preference` | Optional. If the key is absent, defaults to `"fastest_completion"`. If present, must be exactly `fastest_completion`, `lowest_total_cost`, `least_irrigation_dependence`, `highest_net_return`, or `more_crop_diversity`. `lowest_upfront_cash` is not accepted until §12.4 cash-flow evidence exists. |

Error messages:

- `district_id is required.`
- `district_id must be a non-empty string.`
- `start_date is required.`
- `start_date must be a valid YYYY-MM-DD date.` (matches the §14.3 example)
- `first_crop_id is required.`
- `first_crop_id must be null or an existing crop ID.`
- `water_access must be one of: rainfed, irrigation_available, unknown.`
- `preference must be one of: fastest_completion, lowest_total_cost, least_irrigation_dependence, highest_net_return, more_crop_diversity.`
- `Request payload must be a JSON object.` (`field` is `null`; there is no field name)

Unknown extra keys are ignored and are not copied into the effective request.
No value is coerced or replaced by a default when it is present but invalid.

### `build_error_response(exc)`

Returns exactly:

```json
{
  "schema_version": "1",
  "error": {
    "code": "INVALID_REQUEST",
    "message": "start_date must be a valid YYYY-MM-DD date.",
    "field": "start_date"
  }
}
```

Always includes `code`, `message`, and `field`. For a non-object payload the
field is `null`. No stack trace or raw payload is returned.

### `http_status_for_error(exc)`

Returns `400` when `exc.code == "INVALID_REQUEST"`; other exceptions map to
`500` for the later HTTP wrapper. The function does not build a success
envelope or catch exceptions.

## Decisions recorded

- Dates use an ASCII-only regex before the calendar check, so `2026-1-6`,
  `06-11-2026`, Arabic-Indic digits, date-times, non-strings, and invalid
  calendar days are rejected. `2024-02-29` is accepted; `2026-02-29` is not.
- Only an **absent** optional enum key receives its default. A present `null`
  or empty string is rejected, following §14.2's "reject invalid enum values
  rather than silently substituting" rule.
- `district_id` whitespace-only values are rejected, but accepted values are
  not rewritten. The value is a stable ID for downstream lookup, not a display
  name, and district support is deferred.
- `first_crop_id` uses exact string membership in `known_crop_ids`; no
  trimming or case folding.
- Tests use synthetic IDs (`crop_one`, `crop_two`). They do not invent crop
  records or agronomic values and do not depend on the real CSV.

## Commands run

From `Q:\CycleAlgo\fosol-cycle-engine` (Python 3.13.2):

```powershell
$env:PYTHONIOENCODING='utf-8'; python -m unittest discover -s tests -v
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
Ran 32 tests in 0.016s

OK
```

## Test coverage map

- Defaults: minimal payload -> `water_access="unknown"`,
  `preference="fastest_completion"`.
- Full valid payload round-trips unchanged.
- All allowed water-access and preference values are accepted.
- Extra keys are ignored.
- `district_id`: missing, empty, whitespace-only, null, number, boolean, list.
- `start_date`: `2026-02-30`, `2026-1-6`, `06-11-2026`, `2026-13-01`,
  `2026-11-6`, date-time, empty, integer, null, boolean, missing; leap-day
  acceptance and non-leap rejection.
- `first_crop_id`: null and known IDs accepted; unknown, empty, padded,
  integer, boolean, list, and object rejected; missing rejected.
- Enums: every invalid water-access and preference value, including
  `lowest_upfront_cash`, null, wrong case, trailing space, and wrong types.
- Error contract: exact top-level and nested keys, `schema_version == "1"`,
  JSON serialization, `field == null` for a non-object payload, HTTP 400 for
  `INVALID_REQUEST`, and HTTP 500 for an unexpected exception.
