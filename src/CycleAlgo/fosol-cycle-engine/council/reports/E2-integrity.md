# E2 Integrity Audit — Request Validation and Error Contract

- Audit date: 2026-11-06
- Auditor: Integrity Auditor (anti-hallucination)
- Scope: `src/request_validation.py`, `src/error_contract.py`,
  `tests/test_request_validation.py`, `council/reports/E2-builder.md`
- Source of truth: `Q:\CycleAlgo\v1.md` §14.2 (lines 505–540), §14.3
  (lines 542–585); §12.4 (lines 395–399, 416) for the `lowest_upfront_cash`
  condition.
- Code and tests were **not modified** by this audit.

## Verdict

**PASS.** The accepted enums, defaults, field names, `schema_version`, error
code, error-envelope keys, and HTTP statuses match §14.2/§14.3.
`lowest_upfront_cash` is correctly absent from the accepted enum and is
explicitly rejected. The full suite passes 32/32 on a fresh run, and the
builder's pasted output matches the re-run except for normal timing variance
(0.016 s vs 0.017 s). No secrets, credentials, stack traces, invented
endpoints, invented request fields, invented defaults, or fake agronomic data
were found.

Non-blocking provenance notes are in §6. They are labeling/robustness issues,
not fabricated specification claims.

## Artifacts audited

| Artifact | SHA-256 |
|---|---|
| `src/request_validation.py` | `8C443662945A17F51DEC8AF3F46E34EA9991A2A12E7412CDAC828FB3712AC2D3` |
| `src/error_contract.py` | `C05E5EC5E2C6CF35BAE29DEB93DC04770D5D8E6CBEE15EC592B5ECB13A801C7D` |
| `tests/test_request_validation.py` | `F2030698CD227BD355FA50033582B0E5FE5A282EEBADA36CE29A6A6C8120410E` |
| `council/reports/E2-builder.md` | `909AA2052764B1D26BBD193764A8A7BC4B95F133D81E554EC5456DA311065487` |
| `Q:\CycleAlgo\v1.md` (source of truth, working tree) | `1B1C313664A902BE7B942B13F5B287EA21EF1B7FD5F97EF81EF472D1F118875D` |

Method: line-by-line comparison against §14.2/§14.3; exhaustive AST extraction
of string/number/bool/`None` constants from the three Python files; enum and
default comparison; fresh `unittest` discovery run; unified diff of the
builder's pasted output against the fresh output; grep for secret patterns,
tracebacks, endpoint strings, and `DataNEVERBEUSED` references; `git status`
for repository modifications.

## 1. Provenance table

### 1.1 Spec-derived literals

| Literal | Location | Spec provenance | Result |
|---|---|---|---|
| `rainfed`, `irrigation_available`, `unknown` | `src/request_validation.py:14` | §14.2 line 535 | Exact values; same order as spec |
| `fastest_completion`, `lowest_total_cost`, `least_irrigation_dependence`, `highest_net_return`, `more_crop_diversity` | `src/request_validation.py:16-20` | §14.2 line 536 | Exact values; same order as spec |
| `unknown` (water default) | `src/request_validation.py:23` | §14.2 line 535 | Exact |
| `fastest_completion` (preference default) | `src/request_validation.py:24` | §14.2 line 536 | Exact |
| `district_id`, `start_date`, `first_crop_id`, `water_access`, `preference` | `src/request_validation.py:51-111` | §14.2 example lines 517–523; field table lines 530–536 | Exact field names; no extras |
| `INVALID_REQUEST` | `src/request_validation.py:32`; `src/error_contract.py:20` | §14.3 line 578 | Exact error code |
| `schema_version` | `src/error_contract.py:9` | §14.3 lines 548, 576 | Exact key |
| `"1"` | `src/error_contract.py:9` | §14.3 lines 548, 576 | Exact initial schema version |
| `error`, `code`, `message`, `field` | `src/error_contract.py:10-13` | §14.3 lines 577–581 | Exact nested envelope shape |
| `start_date must be a valid YYYY-MM-DD date.` | `src/request_validation.py:64,72` | §14.3 line 579 | Exact spec example message |
| `400` | `src/error_contract.py:21` | §14.3 line 570 | Invalid input status |
| `500` | `src/error_contract.py:22` | §14.3 line 570 | Unexpected internal failure status |
| `lowest_upfront_cash` (tested as rejected) | `tests/test_request_validation.py:186,196,198` | §14.2 line 538; §12.4 lines 395–399, 416 | Conditional value; correctly **not** accepted because no cash-flow evidence/calculation exists in the project |
| `rajshahi` | `tests/test_request_validation.py:21,44` | §14.2 line 518 example | Spec example value; not fabricated data |
| `2026-11-06` | `tests/test_request_validation.py:22,45` | §14.2 line 519 example | Spec example value; not fabricated data |
| `2024-02-29`, `2026-02-29` | `tests/test_request_validation.py:132,135` | §14.2 line 533; §17.5 line 703 | Calendar-validity fixtures: leap day accepted, non-leap Feb 29 rejected |

### 1.2 Implementation-defined literals and rules

These have no exact spec text. They are implementation choices, not fabricated
domain claims.

| Item | Location | Classification and note |
|---|---|---|
| ASCII date regex `[0-9]{4}-[0-9]{2}-[0-9]{2}` | `src/request_validation.py:26` | Implementation enforcement of “valid `YYYY-MM-DD`”; stricter than a permissive parser but not contradictory. Also rejects non-ASCII digits and date-times. |
| `first_crop_id` is a **required key** | `src/request_validation.py:75-78` | Spec-implicit, not literal. The §14.2 example always includes the key with `null`, and the field is described, but the table does not use the word “Required” (unlike `district_id`/`start_date`). See §6.1. |
| `district_id` must be a non-empty string; whitespace-only is rejected; accepted value is not trimmed | `src/request_validation.py:54-57,107` | Spec says “required stable district ID”; blank/type handling is implementation-defined. See §6.2. |
| Exact membership of `first_crop_id` in `known_crop_ids`; no trim or case-folding | `src/request_validation.py:80-86` | Implements “existing crop-profile ID”; the exact matching policy is implementation-defined and disclosed in the builder report. |
| Defaults apply only when the optional key is **absent**; present `null`/empty string is rejected | `src/request_validation.py:88,97` | Implementation interpretation of “default”. Defensible because `null`/`""` are not enum values, but the spec does not state the null case explicitly. |
| Unknown extra keys are ignored and not copied | `src/request_validation.py:45-46,106-112` | Spec silent. Policy choice; see §6.3 for typo risk. |
| `Request payload must be a JSON object.` | `src/request_validation.py:49` | Implementation diagnostic; no domain claim. |
| `district_id is required.` | `src/request_validation.py:52` | Implementation diagnostic. |
| `district_id must be a non-empty string.` | `src/request_validation.py:56` | Implementation diagnostic. |
| `start_date is required.` | `src/request_validation.py:60` | Implementation diagnostic. |
| `first_crop_id is required.` | `src/request_validation.py:77` | Implementation diagnostic for the spec-implicit required key. |
| `first_crop_id must be null or an existing crop ID.` | `src/request_validation.py:84` | Implementation diagnostic; requirement itself is §14.2. |
| `water_access must be one of: rainfed, irrigation_available, unknown.` | `src/request_validation.py:91-93` | Implementation diagnostic; enum values are spec-derived. |
| `preference must be one of: fastest_completion, lowest_total_cost, least_irrigation_dependence, highest_net_return, more_crop_diversity.` | `src/request_validation.py:100-102` | Implementation diagnostic; enum values are spec-derived. |
| `field` is always present; it is `null` for a whole-payload error | `src/error_contract.py:13`; `src/request_validation.py:49` | Spec example shows `field` for a field-level error; whole-payload/null behavior is implementation-defined. |
| Any exception whose `code` is not `INVALID_REQUEST` maps to `500` | `src/error_contract.py:20-22` | Implementation mapping of §14.3's “HTTP 500 for unexpected internal failures”. |
| `RequestValidationError(message, field=None)`, `build_error_response(exc)`, `http_status_for_error(exc)` | `src/request_validation.py:29-37`; `src/error_contract.py:6,18` | Implementation API; no domain claim. `build_error_response` expects the validation-error attributes (`.code`, `.message`, `.field`). |
| Date slice indexes `0:4`, `5:7`, `8:10` | `src/request_validation.py:68` | Implementation detail of ISO-date parsing. |

### 1.3 Test-only literals

The AST inventory of `tests/test_request_validation.py` contains no product
constants beyond the contract values above. Every remaining literal is a test
fixture, an invalid input, or an assertion restating the contract.

| Group | Literals |
|---|---|
| Synthetic known crop IDs | `crop_one`, `crop_two` — explicitly synthetic, not real crop records |
| Default valid payload | `district_id="rajshahi"`, `start_date="2026-11-06"`, `first_crop_id=None` |
| Invalid `district_id` | missing key, `""`, `"   "`, `None`, `7`, `True`, `["rajshahi"]` |
| Invalid `start_date` | missing key, `"2026-02-30"`, `"2026-1-6"`, `"06-11-2026"`, `"2026-13-01"`, `"2026-11-6"`, `"2026-11-06T00:00:00"`, `""`, `20261106`, `None`, `True` |
| Valid/invalid leap dates | `"2024-02-29"` accepted; `"2026-02-29"` rejected |
| Valid/invalid `first_crop_id` | `None`, `"crop_one"` accepted; missing key, `"crop_unknown"`, `""`, `" crop_one"`, `7`, `True`, `["crop_one"]`, `{"id": "crop_one"}` rejected |
| Invalid `water_access` | `None`, `""`, `"not_sure"`, `"irrigation"`, `"RAINFED"`, `"unknown "`, `0`, `True`, `[]`, `{"value": "unknown"}` |
| Invalid `preference` | `None`, `""`, `"cheapest"`, `"FASTEST_COMPLETION"`, `"fastest completion"`, `"lowest_upfront_cash"`, `0`, `True`, `[]`, `{"value": "fastest_completion"}` |
| Invalid whole payloads | `None`, `[]`, `"request"`, `7`, `True` |
| Extra-key fixtures | `unknown_key="ignored"`, `another_unknown=123` |
| Generic exception message | `"boom"` |
| Assertion-only values | `"INVALID_REQUEST"`, `"1"`, `"schema_version"`, `"error"`, `"code"`, `"message"`, `"field"`, `"district_id"`, `"start_date"`, `"first_crop_id"`, `"water_access"`, `"preference"`, `"unknown"`, `"fastest_completion"`, `"irrigation_available"`, `"more_crop_diversity"`, `"crop_one"`, `"rajshahi"`, `"2026-11-06"`, `"2024-02-29"`, `"2026-02-30"`, `"start_date is required."`, `"first_crop_id is required."`, `"start_date must be a valid YYYY-MM-DD date."` |
| Python idiom | `"__main__"` |

No price, yield, duration, area, temperature, rainfall, soil value, or real
crop record appears in the E2 source or tests.

### 1.4 Endpoint / field / default inventiveness check

| Category | Finding |
|---|---|
| Invented endpoint | **None.** No `POST /api/explore`, URL, route, server, or HTTP client appears in the new code, tests, or builder report. E2 correctly leaves the HTTP wrapper to E10. |
| Invented request field | **None.** The effective request is exactly the five §14.2 fields. |
| Invented default | **None.** Only `water_access="unknown"` and `preference="fastest_completion"`, both §14.2. |
| Invented success-envelope field | **None.** No success envelope was added; E9 owns it. |
| Invented error code | **None.** Only `INVALID_REQUEST`, the §14.3 example code. No invented `INTERNAL_ERROR` or similar. |
| Invented status vocabulary | **None.** No success `status` enum was added; that is E9 scope. |
| Invented district/crop/agronomic data | **None.** `rajshahi` and `2026-11-06` are the §14.2 example values; crop IDs are explicitly synthetic test fixtures. |

## 2. Enum and default verification against §14.2

| Check | Spec §14.2 | Code | Result |
|---|---|---|---|
| Allowed `water_access` | `rainfed`, `irrigation_available`, `unknown` | `WATER_ACCESS_VALUES` exactly those three | **PASS** |
| `water_access` default | `unknown` | `DEFAULT_WATER_ACCESS = "unknown"` | **PASS** |
| Allowed `preference` | `fastest_completion`, `lowest_total_cost`, `least_irrigation_dependence`, `highest_net_return`, `more_crop_diversity` | `PREFERENCE_VALUES` exactly those five | **PASS** |
| `preference` default | `fastest_completion` | `DEFAULT_PREFERENCE = "fastest_completion"` | **PASS** |
| `lowest_upfront_cash` | Only add when §12.4 cash-flow evidence/calculation is implemented | Not in `PREFERENCE_VALUES`; test asserts rejection | **PASS** — correctly rejected |
| Invalid enum handling | Reject rather than substitute a different preference | Raises `RequestValidationError`; never rewrites a present value | **PASS** |
| `first_crop_id` values | `null` for first-crop options; otherwise an existing crop-profile ID | `None` accepted; strings must be exactly in `known_crop_ids` | **PASS** (key required by implementation; see §6.1) |
| `start_date` | Required valid `YYYY-MM-DD` calendar date | Required; ASCII regex plus `datetime.date` calendar check | **PASS** |
| `district_id` | Required stable district ID; no translated display name | Required non-empty string; support check deferred to E9 | **PASS** (blank/whitespace policy is implementation-defined; see §6.2) |
| Error envelope | `schema_version="1"`, `error.code`, `error.message`, `error.field` | Exact same four keys/values | **PASS** |
| HTTP mapping | 400 invalid input; 500 unexpected internal failure | 400 for `INVALID_REQUEST`; 500 otherwise | **PASS** |

The two optional enum keys are compared with exact string equality; the tests
exercise every allowed value and reject `null`, empty strings, wrong case,
trailing spaces, non-string types, and unknown values.

## 3. Re-run output

Command, from `Q:\CycleAlgo\fosol-cycle-engine`:

```powershell
python -X utf8 -m unittest discover -s tests -v
```

Fresh result (exit code 0):

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
Ran 32 tests in 0.017s

OK
```

Scoped E2 run:

```powershell
python -X utf8 -m unittest discover -s tests -p "test_request_validation.py" -v
```

```text
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
Ran 18 tests in 0.002s

OK
```

Comparison with `E2-builder.md`: a unified diff of the builder's pasted
`text` block against the fresh output differs only in the runtime line
(`Ran 32 tests in 0.016s` vs `0.017s`). Every test name, order, and `ok`
result is identical.

## 4. Builder report claim audit

| Claim in `E2-builder.md` | Evidence | Result |
|---|---|---|
| Implements §14.2/§14.3 only; no evaluator/API/success envelope | File contents; no imports beyond stdlib; no endpoint or success-envelope code | Backed |
| Four files created | All four exist; all four are untracked additions | Backed |
| 18 `unittest` tests in the E2 file | Scoped discovery: `Ran 18 tests` | Backed |
| 32 total tests, `OK` | Fresh full discovery: `Ran 32 tests`, `OK` | Backed |
| Python 3.13.2 | `python --version` → `Python 3.13.2` | Backed |
| `RequestValidationError` has `code`, `message`, `field`; constructor `(message, field=None)` | `src/request_validation.py:29-37` | Backed |
| Returns exactly five keys with defaults applied | `src/request_validation.py:106-112`; default test | Backed |
| `district_id`: required, non-empty string, returned unchanged, support deferred | `src/request_validation.py:51-57,107`; tests | Backed by code/tests |
| `start_date`: required, ASCII `YYYY-MM-DD`, real calendar date, returned unchanged | `src/request_validation.py:59-73,108`; tests | Backed |
| `first_crop_id`: required, `null` or exact known ID, other types rejected | `src/request_validation.py:75-86`; tests | Backed; “required” is spec-implicit (see §6.1) |
| `water_access`: absent → `unknown`; present must be one of three values | `src/request_validation.py:88-95`; tests | Backed |
| `preference`: absent → `fastest_completion`; five allowed values; `lowest_upfront_cash` rejected | `src/request_validation.py:97-104`; tests | Backed |
| All nine listed error messages are exact | Direct comparison with `src/request_validation.py:49-102` | Backed |
| Unknown extra keys ignored and not copied | `src/request_validation.py:106-112`; test | Backed |
| No coercion or default substitution for present-invalid values | Code raises before returning; tests | Backed |
| `build_error_response` exact shape, always `code`/`message`/`field`, `null` field for non-object, no stack trace/raw payload | `src/error_contract.py:6-15`; tests | Backed |
| `http_status_for_error`: 400 for `INVALID_REQUEST`, 500 otherwise | `src/error_contract.py:18-22`; tests | Backed |
| ASCII-only regex rejects date-times, non-strings, invalid calendar days; leap day accepted | `src/request_validation.py:26,62-73`; tests for all except Arabic-Indic digits | Backed by code; Arabic-Indic case not directly tested (see §6.6) |
| Only absent optional keys receive defaults | `payload.get(...)` with invalid-value raises; tests | Backed by code/tests |
| `district_id` whitespace-only rejected, accepted value not rewritten | `src/request_validation.py:54,107`; blank test | Backed by code/tests |
| `first_crop_id` exact membership, no trimming/case folding | `src/request_validation.py:80-81`; padded test | Backed |
| Tests use synthetic IDs (`crop_one`, `crop_two`), no invented crop records/agronomic values | Test file; no real crop IDs or agronomic fields | Backed |
| No file in `Q:\CycleAlgo\Data\` modified | `git status --porcelain -- Data` and `git diff --stat -- Data` are empty | Backed externally; not pasted in the builder report |
| `Data/DataNEVERBEUSED/` was not accessed | No reference in new code/tests; no contents used in this audit | **Not independently provable** as a negative; no evidence of access or fabricated data (see §6.7) |
| E1 files were not changed | `git status` shows no modifications to `src/crop_profiles.py` or `tests/test_crop_profiles.py` | Backed |

## 5. Secrets, credentials, stack traces, and fake data

| Check | Result |
|---|---|
| API keys, secrets, tokens, passwords, credentials, bearer strings, private keys | **No matches** in `src/request_validation.py`, `src/error_contract.py`, or `tests/test_request_validation.py` (case-insensitive grep for key/secret/token/password/credential/bearer/`sk-`/`ghp_`/`AKIA`/PEM headers) |
| Stack traces / `traceback` printing | **None.** No `traceback` import, no traceback formatting, no exception `repr` returned to callers |
| Raw payload echoed in errors | **None.** Messages are static; only the field name is returned |
| Network calls / file reads / environment access | **None.** Imports are `datetime`, `re`, `collections.abc.Collection`, and stdlib test modules only |
| Invented agronomic values | **None.** No crop durations, prices, yields, soil values, or district datasets were added |
| Fake data mislabeled as real | **None.** `crop_one`/`crop_two` are disclosed synthetic fixtures; `rajshahi`/`2026-11-06` are the spec example values |
| Credentials in the builder report | **None.** The report contains no secrets or provider headers |

One latent robustness note, not a security leak: `build_error_response(exc)`
reads `.code`, `.message`, and `.field` directly, so passing a generic
`RuntimeError` raises `AttributeError`. Its docstring scopes it to
request-validation failures, and the HTTP wrapper can use
`http_status_for_error` for generic exceptions. See §6.8.

## 6. Unsourced / non-blocking items

### 6.1 `first_crop_id` is labeled “Required” without a literal spec “Required”

`E2-builder.md` says `first_crop_id` is a “Required key.” §14.2’s field table
does not use the word “Required” for `first_crop_id` (it does for
`district_id` and `start_date`); it says `null` for first-crop options and an
existing crop-profile ID otherwise. The request example always includes the
key, so requiring it is a defensible reading of the documented request shape,
not a contradiction. **Classification: spec-implicit / implementation-defined.** Recommend the report say “required by this implementation, consistent
with the §14.2 example” rather than implying an explicit spec rule.

### 6.2 `district_id` blank handling and non-trimming are implementation-defined

§14.2 requires a stable district ID and forbids translated display names as
keys. It does not define whitespace or type handling. The code rejects
whitespace-only values but accepts `" rajshahi "` unchanged. This is disclosed
in the builder report and does not invent a district. **Risk:** a padded ID can
pass validation and then fail a downstream exact lookup; downstream code should
either reject or normalize padded IDs. Confirmed by direct call: `' rajshahi '`
passes and is returned unchanged. Non-blocking for E2.

### 6.3 Unknown extra keys are ignored

The spec does not say whether unknown request keys must be rejected. Ignoring
them is a safe forward-compatibility choice, but a typo in an optional key
(for example `preferance`) silently falls back to the default instead of
alerting the client. This is an implementation policy, not a spec claim.
Confirmed by direct call: a misspelled `preferance` key is ignored and the
effective request receives the `fastest_completion` default. If strictness is
desired later, reject unknown keys at the HTTP boundary.

### 6.4 Error-message text beyond the spec example is implementation-defined

Only `start_date must be a valid YYYY-MM-DD date.` is copied from §14.3. The
other eight messages are implementation diagnostics. §14.3 fixes the
`code`/`message`/`field` shape, not the prose for every failure. The builder
report does not claim otherwise, but the messages should not be treated as
spec-mandated strings by downstream tests.

### 6.5 `field: null` for a whole-payload error is implementation-defined

The §14.3 example shows `field` for a field-level failure. The spec does not
define the whole-payload case. Always including `field` (with `null` when no
field applies) preserves the documented shape and is a reasonable choice, but
it is not a literal spec rule.

### 6.6 Arabic-Indic digit rejection is code-backed, not test-backed

The builder report says the ASCII-only regex rejects Arabic-Indic digits. The
regex `[0-9]` does reject them, but the test list contains no Arabic-Indic
input. The claim is true by code inspection; it is simply not exercised by the
pasted output. Add one fixture if the council requires every stated behavior
to have a test.

### 6.7 `DataNEVERBEUSED/` non-access cannot be proven from artifacts

The builder’s negative claim is not independently provable. What was verified:
no reference to `DataNEVERBEUSED` exists in the new code, tests, or report;
`git status --porcelain -- Data` and `git diff --stat -- Data` are empty; and
this audit did not open or read anything under that directory.

### 6.8 `build_error_response` is not generic

The function assumes validation-error attributes. This is consistent with its
docstring and with E2’s scope (invalid-request error shape), and the spec does
not define a 500 response body. If the later HTTP wrapper calls it for
unexpected exceptions, it should build a separate generic error or guard the
attributes. Confirmed by direct call: `build_error_response(RuntimeError("boom"))`
raises `AttributeError: 'RuntimeError' object has no attribute 'code'`.
Non-blocking for E2, but worth fixing when E10 lands.

### 6.9 No success envelope, status enum, or HTTP endpoint

These are absent by design: E2 covers request validation and the invalid-request
error contract; E9 owns the success envelope/status precedence and E10 owns the
thin HTTP wrapper. Their absence is not an E2 gap and the builder report states
it correctly.

### 6.10 The audited §14.2/§14.3 text is an uncommitted working-tree addition

`git diff --numstat -- v1.md` shows `149 0 v1.md`, and the diff adds the entire
§14.1–§14.6 block (including §14.2/§14.3). The committed `v1.md` at `4711b3e`
does not contain those sections. This audit used the working-tree text because
the task names it as the source of truth, and the E2 code matches that text
exactly. Non-blocking for E2, but the council should commit the specification so
future gates compare against a stable reference.

## 7. Final verdict

**PASS.**

- Enum values and defaults match §14.2 exactly.
- `lowest_upfront_cash` is not accepted; the test explicitly verifies rejection.
- The error envelope matches §14.3’s `schema_version`, `error.code`,
  `error.message`, and `error.field` shape; HTTP 400/500 mapping is correct.
- The fresh full-suite run passes 32/32; the scoped E2 run passes 18/18.
- The builder’s pasted output is genuine, with only timing variance.
- No secrets, credentials, stack traces, invented endpoints, invented request
  fields, invented defaults, or fake agronomic data were found.
- The only provenance caveats are the non-blocking labeling/robustness/
  repository-hygiene items in §6; none fabricates a spec rule or domain value.

---

Auditor access note: no file under `Q:\CycleAlgo\Data\DataNEVERBEUSED\` was
opened, listed, or read; no file under `Q:\CycleAlgo\Data\` was modified. No
code or test was modified during this audit; only this report was created.
