# E2 — Request validation and error contract: code review

**Reviewer:** Code Reviewer (Fosol-Cycle v1 council)
**Date:** 2026-11-06
**Scope:** `src/request_validation.py`, `src/error_contract.py`, `tests/test_request_validation.py`, `council/reports/E2-builder.md`
**Spec context:** `../v1.md` §14.2, §14.3
**Environment:** Windows, Python 3.13.2, engine root `Q:\CycleAlgo\fosol-cycle-engine`

**Data safety:** `Data/DataNEVERBEUSED/` was not read, listed, or modified. No file under
`Data/` was modified. All probe scripts were written under `%TEMP%\opencode\` outside the
repo. No source or test file was changed by this review; this report is the only repo
addition.

## Verdict

**PASS — no blocking correctness defect found against E2's stated contract.**

| Gate | Result |
|---|---|
| Unit tests | **PASS** — 32/32 total; 18/18 E2 tests |
| Payload shape | **PASS** — non-object payloads rejected with `field: null` |
| Required fields | **PASS** — missing `district_id` / `start_date` / `first_crop_id` report their own fields |
| `district_id` | **PASS** for blank/type checks; padded value observation in finding 4 |
| `start_date` | **PASS** — regex + real-calendar check; no off-by-one or leap-year defect found |
| `first_crop_id` | **PASS** for null/known/unknown/type checks; bare-string `known_crop_ids` caveat in finding 1 |
| Optional enums | **PASS** — defaults only when absent; present invalid values rejected, never substituted |
| Extra keys | **PASS** per documented policy; typo risk noted below |
| Error envelope | **PASS** — exact documented shape; uses the exception's `message` and `field` |
| HTTP mapping | **PASS** — `INVALID_REQUEST` -> 400; other exceptions -> 500 |
| Bool-is-int / mutable defaults | **PASS** — no boolean accepted where a string is required; no mutable default arguments |
| Test coverage | **PASS** with low-severity gaps (finding 5) |

Findings 1–5 are low-severity hardening, ambiguity, or test-gap issues. None changes the
E2 result for the documented contract. No adversarial input caused an unexpected crash in
the validator, and every present-but-invalid value was rejected rather than defaulted.

## Commands and real output

### 1. Unit tests

From the engine root:

```powershell
cd Q:\CycleAlgo\fosol-cycle-engine
python -X utf8 -m unittest discover -s tests -v
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

### 2. Adversarial probes (temp script outside the repo)

Probe command:

```powershell
python -X utf8 "$env:TEMP\opencode\e2_probe.py"
```

The probe made 116 assertions covering payload shape, missing keys, every requested type
and enum edge, date boundaries, error fields, the error envelope, HTTP mapping, and
signatures. Real excerpt (long JSON details kept as printed):

```text
PASS | payload None                                           | REJECT | {"code": "INVALID_REQUEST", "field": null, "message": "Request payload must be a JSON object."}
PASS | payload list                                           | REJECT | {"code": "INVALID_REQUEST", "field": null, "message": "Request payload must be a JSON object."}
PASS | payload string                                         | REJECT | {"code": "INVALID_REQUEST", "field": null, "message": "Request payload must be a JSON object."}
PASS | missing district_id                                    | REJECT | {"code": "INVALID_REQUEST", "field": "district_id", "message": "district_id is required."}
PASS | missing start_date                                     | REJECT | {"code": "INVALID_REQUEST", "field": "start_date", "message": "start_date is required."}
PASS | missing first_crop_id                                  | REJECT | {"code": "INVALID_REQUEST", "field": "first_crop_id", "message": "first_crop_id is required."}
PASS | district_id spaces only                                | REJECT | {"code": "INVALID_REQUEST", "field": "district_id", "message": "district_id must be a non-empty string."}
PASS | district_id True                                       | REJECT | {"code": "INVALID_REQUEST", "field": "district_id", "message": "district_id must be a non-empty string."}
PASS | district_id 1                                          | REJECT | {"code": "INVALID_REQUEST", "field": "district_id", "message": "district_id must be a non-empty string."}
PASS | start_date '2026-13-01'                                | REJECT | {"code": "INVALID_REQUEST", "field": "start_date", "message": "start_date must be a valid YYYY-MM-DD date."}
PASS | start_date '0000-01-01'                                | REJECT | {"code": "INVALID_REQUEST", "field": "start_date", "message": "start_date must be a valid YYYY-MM-DD date."}
PASS | start_date '2026-02-29'                                | REJECT | {"code": "INVALID_REQUEST", "field": "start_date", "message": "start_date must be a valid YYYY-MM-DD date."}
PASS | start_date '2026-02-30'                                | REJECT | {"code": "INVALID_REQUEST", "field": "start_date", "message": "start_date must be a valid YYYY-MM-DD date."}
PASS | start_date '2026-1-6'                                  | REJECT | {"code": "INVALID_REQUEST", "field": "start_date", "message": "start_date must be a valid YYYY-MM-DD date."}
PASS | start_date '2026-11-06 '                               | REJECT | {"code": "INVALID_REQUEST", "field": "start_date", "message": "start_date must be a valid YYYY-MM-DD date."}
PASS | start_date ' 2026-11-06'                               | REJECT | {"code": "INVALID_REQUEST", "field": "start_date", "message": "start_date must be a valid YYYY-MM-DD date."}
PASS | start_date '2026-11-06\n'                              | REJECT | {"code": "INVALID_REQUEST", "field": "start_date", "message": "start_date must be a valid YYYY-MM-DD date."}
PASS | start_date '２０２６-１１-０６'                                | REJECT | {"code": "INVALID_REQUEST", "field": "start_date", "message": "start_date must be a valid YYYY-MM-DD date."}
PASS | start_date valid '2024-02-29'                          | ACCEPT | {"district_id": "rajshahi", "first_crop_id": null, "preference": "fastest_completion", "start_date": "2024-02-29", "water_access": "unknown"}
PASS | start_date valid '2000-02-29'                          | ACCEPT | {"district_id": "rajshahi", "first_crop_id": null, "preference": "fastest_completion", "start_date": "2000-02-29", "water_access": "unknown"}
PASS | start_date '1900-02-29'                                | REJECT | {"code": "INVALID_REQUEST", "field": "start_date", "message": "start_date must be a valid YYYY-MM-DD date."}
PASS | first_crop_id int 7                                    | REJECT | {"code": "INVALID_REQUEST", "field": "first_crop_id", "message": "first_crop_id must be null or an existing crop ID."}
PASS | first_crop_id True                                     | REJECT | {"code": "INVALID_REQUEST", "field": "first_crop_id", "message": "first_crop_id must be null or an existing crop ID."}
PASS | first_crop_id empty string                             | REJECT | {"code": "INVALID_REQUEST", "field": "first_crop_id", "message": "first_crop_id must be null or an existing crop ID."}
PASS | first_crop_id unknown                                  | REJECT | {"code": "INVALID_REQUEST", "field": "first_crop_id", "message": "first_crop_id must be null or an existing crop ID."}
PASS | first_crop_id padded known                             | REJECT | {"code": "INVALID_REQUEST", "field": "first_crop_id", "message": "first_crop_id must be null or an existing crop ID."}
PASS | water_access 'RAINFED'                                 | REJECT | {"code": "INVALID_REQUEST", "field": "water_access", "message": "water_access must be one of: rainfed, irrigation_available, unknown."}
PASS | water_access 'unknown '                                | REJECT | {"code": "INVALID_REQUEST", "field": "water_access", "message": "water_access must be one of: rainfed, irrigation_available, unknown."}
PASS | water_access True                                      | REJECT | {"code": "INVALID_REQUEST", "field": "water_access", "message": "water_access must be one of: rainfed, irrigation_available, unknown."}
PASS | preference 'FASTEST_COMPLETION'                        | REJECT | {"code": "INVALID_REQUEST", "field": "preference", "message": "preference must be one of: fastest_completion, lowest_total_cost, least_irrigation_dependence, highest_net_return, more_crop_diversity."}
PASS | preference 'lowest_upfront_cash'                       | REJECT | {"code": "INVALID_REQUEST", "field": "preference", "message": "preference must be one of: fastest_completion, lowest_total_cost, least_irrigation_dependence, highest_net_return, more_crop_diversity."}
PASS | preference True                                        | REJECT | {"code": "INVALID_REQUEST", "field": "preference", "message": "preference must be one of: fastest_completion, lowest_total_cost, least_irrigation_dependence, highest_net_return, more_crop_diversity."}
OBSERVE defaults: {"district_id": "rajshahi", "first_crop_id": null, "preference": "fastest_completion", "start_date": "2026-11-06", "water_access": "unknown"}
PASS | defaults applied without substitution
PASS | extra keys ignored                                     | ACCEPT | {"district_id": "rajshahi", "first_crop_id": null, "preference": "fastest_completion", "start_date": "2026-11-06", "water_access": "unknown"}
PASS | extra keys not copied into effective request
PASS | error response exact documented shape: {"error": {"code": "INVALID_REQUEST", "field": "start_date", "message": "start_date must be a valid YYYY-MM-DD date."}, "schema_version": "1"}
PASS | build_error_response uses exception field/message
PASS | whole-payload error field is null: {"error": {"code": "INVALID_REQUEST", "field": null, "message": "Request payload must be a JSON object."}, "schema_version": "1"}
PASS | error envelope has exact keys and is JSON serializable
OBSERVE build_error_response(RuntimeError): CRASH AttributeError: 'RuntimeError' object has no attribute 'code'
PASS | http_status_for_error RequestValidationError -> 400
PASS | http_status_for_error RuntimeError -> 500
PASS | http_status_for_error ValueError -> 500
PASS | http_status_for_error arbitrary code=INVALID_REQUEST -> 400
PASS | http_status_for_error arbitrary code=OTHER -> 500
PASS | http_status_for_error no code attribute -> 500
PASS | validate_explore_request signature (payload: 'object', known_crop_ids: 'Collection[str]') -> 'dict' has no mutable defaults
PASS | build_error_response signature (exc: 'Exception') -> 'dict' has no mutable defaults
PASS | http_status_for_error signature (exc: 'Exception') -> 'int' has no mutable defaults

SUMMARY: 116/116 checks passed; 0 failed
```

Additional probe results (real output):

```text
PASS | district_id padded ' rajshahi '                        | ACCEPT | {"district_id": " rajshahi ", "first_crop_id": null, "preference": "fastest_completion", "start_date": "2026-11-06", "water_access": "unknown"}
PASS | known_crop_ids='crop_one', first_crop_id='crop'        | ACCEPT | {"district_id": "rajshahi", "first_crop_id": "crop", "preference": "fastest_completion", "start_date": "2026-11-06", "water_access": "unknown"}
PASS | start_date valid '0001-01-01'                          | ACCEPT | {"district_id": "rajshahi", "first_crop_id": null, "preference": "fastest_completion", "start_date": "0001-01-01", "water_access": "unknown"}
PASS | start_date valid '9999-12-31'                          | ACCEPT | {"district_id": "rajshahi", "first_crop_id": null, "preference": "fastest_completion", "start_date": "9999-12-31", "water_access": "unknown"}
```

Input-preservation / exception-shape probe:

```text
input unchanged: True
effective keys: ['district_id', 'first_crop_id', 'preference', 'start_date', 'water_access']
exception str/args: custom ('custom',)
set known crop accepted: crop_one
list known crop accepted: crop_one
dict_keys known crop accepted: crop_one
frozenset known crop accepted: crop_one
dict_keys JSON: {"district_id": "rajshahi", "first_crop_id": null, "preference": "highest_net_return", "start_date": "2026-11-06", "water_access": "rainfed"}
```

### 3. Probe coverage summary

| Probe group | Cases | Observed result |
|---|---|---|
| Payload `None`, list, string, number, boolean | 5 | All rejected; `field == null` |
| Missing `district_id` / `start_date` / `first_crop_id` | 3 | Correct field and required message each |
| `district_id` empty, whitespace-only, `None`, bool, int, list, dict | 8 | All rejected with `district_id` |
| `start_date` invalid (`2026-13-01`, `0000-01-01`, `2026-02-29`, `2026-02-30`, `2026-1-6`, date-time, padded, Unicode digits, non-string) | 28 | All rejected with `start_date`; message matches §14.3 |
| `start_date` valid (`2024-02-29`, `2000-02-29`, `2026-01-01`, `2026-12-31`, `0001-01-01`, `9999-12-31`) | 6 | All accepted unchanged |
| `first_crop_id` int, bool, empty, whitespace, unknown, padded, list, dict | 11 | All rejected with `first_crop_id` |
| `first_crop_id` `null`, known ID | 2 | Accepted; known ID returned unchanged |
| `water_access` invalid (wrong case, `None`, numbers, bools, list, dict, padded) | 14 | All rejected; no default substitution |
| `preference` invalid (wrong case, `None`, numbers, bools, list, dict, `lowest_upfront_cash`) | 13 | All rejected; no default substitution |
| Every allowed enum value | 8 | All accepted |
| Extra keys | 1 | Ignored and not copied into the effective request |
| Error envelope | 4 | Exact keys, exact documented values, custom exception message/field used, payload error `field == null`, JSON serializable |
| HTTP mapping | 6 | `INVALID_REQUEST` -> 400; all others -> 500 |
| Signatures | 3 | No mutable default arguments |
| Input mutation | 1 | Input dict unchanged |

## Findings

### Numbered bug list

**1. Low — `known_crop_ids: Collection[str]` permits a bare string, turning exact crop-ID membership into substring membership.**
`src/request_validation.py:41` (`known_crop_ids: Collection[str]`) and `:80-82`
(`first_crop_id not in known_crop_ids`). `str` is itself a `Collection[str]`, so this call
is type-valid but wrong:

```python
validate_explore_request(
    {"district_id": "rajshahi", "start_date": "2026-11-06", "first_crop_id": "crop"},
    "crop_one",
)
```

Observed:

```text
ACCEPT | first_crop_id="crop"
```

`"crop"` is not an existing crop-profile ID, but `"crop" in "crop_one"` is true. This
violates §14.2's "otherwise an existing crop-profile ID" if a caller passes a bare string.
No current caller does this; the E1 loader returns a `dict[str, dict]`, and E9 should pass
`set(...)`/`dict.keys()`. This is a latent API hazard, not an observed E2 failure. Fix by
narrowing the type to `AbstractSet[str]`/`Mapping[str, object]`, or guard
`isinstance(known_crop_ids, str)` before membership.

**2. Low (integration hazard) — `build_error_response` is annotated `Exception` but only works for `RequestValidationError`.**
`src/error_contract.py:6-14`. The function reads `exc.code`, `exc.message`, and `exc.field`,
which only `RequestValidationError` supplies. Repro:

```python
build_error_response(RuntimeError("boom"))
```

Observed:

```text
AttributeError: 'RuntimeError' object has no attribute 'code'
```

`http_status_for_error(RuntimeError("boom"))` returns 500 for the same object
(`src/error_contract.py:18-22`). If E10 pairs the two helpers in one `except Exception`
path, the 500 path crashes rather than returning an error envelope. E2's module docstring
scopes `build_error_response` to request-validation failures, so this is not a §14.2/§14.3
failure for E2's current use; resolve it before E10 (narrow the annotation/name, or add a
separate safe internal-error builder). Do not let it return a traceback or raw payload.

**3. Low (contract ambiguity) — missing `first_crop_id` is rejected, but §14.2 only explicitly labels `district_id` and `start_date` as required.**
`src/request_validation.py:75-78`. Repro:

```python
payload = {"district_id": "rajshahi", "start_date": "2026-11-06"}
validate_explore_request(payload, {"crop_one"})
```

Observed:

```text
REJECT | {"code": "INVALID_REQUEST", "field": "first_crop_id", "message": "first_crop_id is required."}
```

The sample request includes `"first_crop_id": null`, and the builder report explicitly
documents the field as required, so this is defensible. If the frontend treats omission as
equivalent to `null` for first-crop options, it will receive 400. Confirm with the Spec
Auditor; if omission is allowed, default to `None` and keep the explicit `null` path.

**4. Low — padded `district_id` is accepted and returned unchanged.**
`src/request_validation.py:54` (strip check) and `:107` (return original value). Repro:

```python
validate_explore_request(
    {"district_id": " rajshahi ", "start_date": "2026-11-06", "first_crop_id": None},
    {"crop_one"},
)
```

Observed:

```text
ACCEPT | district_id=" rajshahi "
```

Whitespace-only IDs are correctly rejected, but surrounding whitespace on a valid ID
survives. If E9 performs exact district lookup, a client typo becomes
`unsupported_district` (HTTP 200) rather than an invalid request (HTTP 400). The builder
report deliberately documents "accepted unchanged (no trimming)" because the ID is a
stable key, so this is a policy risk rather than a clear spec violation. Decide whether to
reject surrounding whitespace or normalize it before E9.

**5. Low (test gap) — several edge behaviors verified by probes are not covered by the suite.**
`tests/test_request_validation.py`. Missing coverage includes:

- `start_date` `"0000-01-01"`, leading/trailing spaces, `"\n"` suffix
  (`tests/test_request_validation.py:101-115`);
- padded `district_id` `" rajshahi "` (`:86-99`);
- `False` in the bool/int rejection cases for `first_crop_id`, `water_access`, and
  `preference` (`:141-199`);
- custom `RequestValidationError("message", "field")` passed to
  `build_error_response` (`:207-233`);
- `ValueError`/no-`code` exceptions in `http_status_for_error` (`:242-246`).

`test_every_allowed_enum_value_is_accepted` (`:62-75`) iterates the module's own
`WATER_ACCESS_VALUES` and `PREFERENCE_VALUES` tuples. It therefore cannot catch an
accidental removal of a required enum value from the allow-list; a hard-coded copy of the
§14.2 values in the test would lock the contract independently. All of the other listed
behaviors were verified manually and passed. Add tests if the behaviors are intended, so
the next refactor does not regress them.

### Non-blocking observations

- **Unknown-key tolerance can silently apply a default to a misspelled key.** Unknown
  extra keys are ignored as documented (`src/request_validation.py:106-112`;
  `tests/test_request_validation.py:77-84`). A client sending
  `{"prefernce": "lowest_total_cost", "water_acess": "rainfed"}` gets the documented
  defaults instead of an error:

  ```text
  {"district_id": "rajshahi", "first_crop_id": null, "preference": "fastest_completion",
   "start_date": "2026-11-06", "water_access": "unknown"}
  ```

  This is not an invalid *value* of `preference`/`water_access`, so it does not violate
  §14.2's reject-invalid-enum rule as written; §14.2 does not require rejecting unknown
  keys. It is a frontend-typo risk. If strictness is preferred, reject unknown keys or at
  least warn; otherwise keep the current forward-compatible policy and document it for
  the frontend.

- **No `start_date` year range.** `0001-01-01` and `9999-12-31` are accepted because they
  are valid proleptic Gregorian dates. §14.2 only requires a valid calendar date, so this
  is correct for E2. E4/E6 date arithmetic must handle the boundaries; do not let an
  extreme date overflow a later `date` calculation.

- **`RequestValidationError` carries the expected attributes.** `str(exc) == message` and
  `exc.args == (message,)`; `build_error_response` uses the instance's `message` and
  `field`, not hard-coded values. The non-object payload case returns `field: null`.

- **`http_status_for_error` duck-types on `code`.** An unrelated exception whose `code`
  attribute is `"INVALID_REQUEST"` maps to 400; one without a `code` maps to 500. This is
  consistent with the function's simple contract and did not misclassify any probed
  exception.

- **Input is not mutated.** A full payload with an extra key was deep-copied before
  validation; the effective request contains exactly the five documented keys and the
  input object was unchanged.

## Spec notes

- **§14.2 request rules:** `district_id` and `start_date` are required; `first_crop_id` is
  `null` or an existing crop ID; `water_access` and `preference` default only when absent;
  all documented enum values are accepted; `lowest_upfront_cash` is correctly absent until
  §12.4 cash-flow evidence exists. Present-but-invalid values raise
  `RequestValidationError`; no present invalid enum is silently replaced.
- **§14.2 district support:** E2 does not claim to know supported districts. A well-formed
  ID is accepted regardless of local evidence; E9 owns `unsupported_district`. The padded
  ID observation (finding 4) is therefore a handoff/ID-canonicalization question, not a
  missing district check.
- **§14.3 error envelope:** `build_error_response` returns exactly
  `{"schema_version": "1", "error": {"code": "INVALID_REQUEST", "message": ...,
  "field": ...}}`; the `start_date` message matches the spec example exactly; the
  whole-payload error uses `field: null`; the dict is JSON-serializable; no stack trace,
  raw payload, credential, or provider header is included.
- **§14.3 HTTP status:** `http_status_for_error` returns 400 for `INVALID_REQUEST` and 500
  for unexpected exceptions, matching the spec's "400 for invalid input and 500 for
  unexpected internal failures." E2 does not build the successful response envelope; that
  remains E9/E10 work.
- **Date correctness:** The regex is ASCII-only (`[0-9]`) and `fullmatch`-anchored, then
  `datetime.date` performs the real calendar check. `2024-02-29` and `2000-02-29` are
  accepted; `1900-02-29`, `2023-02-29`, `2026-02-29`, `2026-02-30`, `2026-04-31`,
  `2026-13-01`, `0000-01-01`, and `10000-01-01` are rejected. No off-by-one was found.

## Files reviewed

- `src/request_validation.py` — 112 lines, read in full.
- `src/error_contract.py` — 22 lines, read in full.
- `tests/test_request_validation.py` — 250 lines, read in full.
- `council/reports/E2-builder.md` — 177 lines, read in full.
- `../v1.md` §14.2 and §14.3 — read in full.
