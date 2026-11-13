# E2 — Spec Audit: Request Validation and Error Contract

**Scope:** `src/request_validation.py`, `src/error_contract.py`, `tests/test_request_validation.py`, `council/reports/E2-builder.md`. E2 covers §14.2 request validation and the §14.3 invalid-request error contract; the HTTP `POST /api/explore` route (E10), the successful envelope (E9), and the evaluator (E4–E8) are downstream milestones.

**Source of truth:** `Q:\CycleAlgo\v1.md` (`../v1.md` from the engine root) §14.1, §14.2, §14.3, §12.4, §13; with §3 for the stable district-ID rule.

**Method:** Read-only source/test/report inspection against `v1.md`, a clean run of the full `unittest` suite, a direct probe of the validator and error helpers, and a read-only check against the eight real crop-profile IDs. No source or test file was changed by this audit; this audit added only this report. `Data/DataNEVERBEUSED/` was not read and its contents were not listed; no file under `Data/` was modified. `git status --short` showed no `Data/` path.

## Compliance table

| Spec section | Exact rule (quote the must / must not / never / default) | Enforced at file:line or test | PASS/FAIL |
|---|---|---|---|
| §14.2, one endpoint (`v1.md:507-512`) | "Use one endpoint initially: `POST /api/explore`" with "`Content-Type: application/json`". | No HTTP route exists in E2. The builder explicitly scopes HTTP out (`council/reports/E2-builder.md:3-5`), and the build order assigns the wrapper to E10 (`council/CHECKLIST.md:72`). The callable request entry point is `src/request_validation.py:40-47`. No competing or invented endpoint was added. | PASS (request contract only; route deferred to E10) |
| §14.2, JSON request fields (`v1.md:514-536`) | The initial request is `district_id`, `start_date`, `first_crop_id`, `water_access`, `preference`; `first_crop_id` is `null` for first-crop options. | The effective request is exactly those five keys, with no extra fields: `src/request_validation.py:106-112`; `tests/test_request_validation.py:39-60`. Unknown input keys are dropped, not copied: `tests/test_request_validation.py:77-84`. | PASS |
| §3/§14.2, `district_id` (`v1.md:89,532`) | "Required stable district ID. Do not use a translated display name as the key." | Required key; must be a string whose stripped content is non-empty; accepted value is returned unchanged: `src/request_validation.py:51-57,107`. Missing/blank/non-string cases are rejected: `tests/test_request_validation.py:86-99`. District support and stable-ID/display-name resolution are not checked here; any non-empty string passes unchanged. | PASS (presence/type; see Note 1) |
| §14.2, `start_date` (`v1.md:533`) | "Required valid `YYYY-MM-DD` calendar date, interpreted as a Bangladesh local agricultural date." | Required key; ASCII `YYYY-MM-DD` regex plus a real-calendar `datetime.date` check: `src/request_validation.py:26,59-73`. Malformed, impossible, datetime, numeric and non-string values are rejected; leap day is handled: `tests/test_request_validation.py:101-135`. Returned unchanged as a date-only string; no timezone conversion is performed, so downstream must interpret it as a Bangladesh local date rather than applying a UTC shift. | PASS |
| §14.2, `first_crop_id` (`v1.md:534`) | "`null` for first-crop options; otherwise an existing crop-profile ID." | Missing key is rejected (see Note 5); `null` is accepted; a non-null value must be an exact member of the supplied `known_crop_ids`: `src/request_validation.py:75-86`; tests `tests/test_request_validation.py:137-159`. Real-ID probe accepted `aman_br11` and rejected `tomato`, `AMAN_BR11`, and ` aman_br11`. | PASS |
| §14.2, crop re-evaluation (`v1.md:540`) | "The engine must re-evaluate a supplied crop ID under the request conditions. A frontend selection is not evidence that a crop passes the filters." | E2 only checks that the ID exists; it does not mark the crop as candidate/pass and does not treat selection as filter evidence: `src/request_validation.py:80-86`. The builder states no evaluator was added: `council/reports/E2-builder.md:3-5`. | PASS (E2 boundary; see Note 4) |
| §14.2, `water_access` (`v1.md:535`) | "`rainfed`, `irrigation_available`, or `unknown`; default `unknown`." | Exact allow-list: `src/request_validation.py:14`; absent-key default: `:23,88-95`. Defaults test: `tests/test_request_validation.py:39-52`; invalid values, including present `null` and wrong case, are rejected: `:161-177`. | PASS |
| §14.2, `preference` (`v1.md:536`) | "`fastest_completion`, `lowest_total_cost`, `least_irrigation_dependence`, `highest_net_return`, or `more_crop_diversity`. Default `fastest_completion`." | Exact allow-list: `src/request_validation.py:15-21`; absent-key default: `:24,97-104`. Defaults test: `tests/test_request_validation.py:39-52`; every allowed value is accepted: `:62-75`; invalid values are rejected: `:179-193`. | PASS |
| §14.2, invalid enums (`v1.md:538`) | "Reject invalid enum values rather than silently substituting a different preference." | A present invalid value raises `RequestValidationError`; defaults apply only when the key is absent: `src/request_validation.py:88-104`. Tests cover invalid water-access and preference values, including wrong case, trailing space, `null`, and wrong types: `tests/test_request_validation.py:161-199`. | PASS |
| §14.2 + §12.4, `lowest_upfront_cash` (`v1.md:538,399`) | "Add `lowest_upfront_cash` only when the cash-flow evidence and calculation described in Section 12.4 are implemented." / "Only display **Lowest upfront cash** when there is a sourced cash-flow schedule for expenses and receipts." | The enum excludes `lowest_upfront_cash`: `src/request_validation.py:15-21`. Explicit rejection test: `tests/test_request_validation.py:195-199`. No cash-flow/receipts implementation exists; a source/test grep for cash/upfront/receipt/finance finds only this validation test. | PASS |
| §13, preference controls (`v1.md:409-416`) | "Offer simple preference controls: **Fastest completion**. **Lowest estimated total cost**. **Least irrigation dependence**, where comparable evidence supports the distinction. **Highest estimated net return**. **More crop diversity**. **Lowest upfront cash**, only when cash-flow evidence exists." | The five implemented controls match the first five §13 items; `lowest_upfront_cash` is omitted: `src/request_validation.py:15-21`. Allowed-values test: `tests/test_request_validation.py:62-75`; rejection test: `:195-199`. | PASS |
| §14.3, error shape (`v1.md:572-583`) | "Error response shape: `{ "schema_version": "1", "error": { "code": "INVALID_REQUEST", "message": "...", "field": "start_date" } }`." | `build_error_response` returns exactly `schema_version` and `error{code,message,field}`: `src/error_contract.py:6-15`. Exact-shape test: `tests/test_request_validation.py:215-233`. Direct probe reproduced the shape and the spec's example message. | PASS |
| §14.3, HTTP 400 (`v1.md:570`) | "Use HTTP 400 for invalid input" | `http_status_for_error` returns 400 when the code is `INVALID_REQUEST`: `src/error_contract.py:18-22`; test `tests/test_request_validation.py:242-243`. | PASS |
| §14.3, HTTP 500 (`v1.md:570`) | "Use HTTP 500 for unexpected internal failures." | `http_status_for_error` returns 500 for other exceptions: `src/error_contract.py:20-22`; test `tests/test_request_validation.py:245-246`. The 500 response body is not built by E2; see Note 3. | PASS (status mapping; body deferred to E10) |
| §14.3, no secrets or stack traces (`v1.md:585`) | "Never return credentials, raw stack traces, or secret provider headers to the frontend." | The envelope contains only `code`, `message`, and `field`: `src/error_contract.py:8-15`; exact-key assertion: `tests/test_request_validation.py:228-232`. No provider, credential, or traceback code exists in E2. | PASS |
| §14.1, callable/JSON/no per-click file (`v1.md:499-503`) | "Implement the decision logic as a callable function accepting a request object and returning a result object. Keep HTTP handling as a thin wrapper..." and "Do not create a new JSON file on disk for every user click." | `validate_explore_request(payload, known_crop_ids)` is callable, returns a plain JSON-serializable dict: `src/request_validation.py:40-47,106-112`. Tests call it directly; the module performs no file I/O and writes no per-request JSON file. | PASS |
| §14.2/§14.3, no invented fields or endpoints (`v1.md:516-536,570-585`) | The request contract lists only the five documented fields; the error shape lists only the documented keys; "Use one endpoint initially." | Effective request has exactly five keys: `src/request_validation.py:106-112`; error has exactly two top-level and three nested keys: `src/error_contract.py:8-15`; no HTTP route or alternate endpoint exists: `council/reports/E2-builder.md:3-5`. | PASS |

## Verification performed

Full suite from `Q:\CycleAlgo\fosol-cycle-engine`:

```text
cmd /c "set PYTHONIOENCODING=utf-8&& python -m unittest discover -s tests 2>&1"
................................
----------------------------------------------------------------------
Ran 32 tests in 0.029s

OK
EXIT:0
```

The E2 module contributes 18 of the 32 tests (`tests/test_request_validation.py`: 14 request-validation tests and 4 error-contract tests).

Direct validator/error probe (read-only):

```text
effective: {"district_id": "rajshahi", "first_crop_id": null, "preference": "fastest_completion", "start_date": "2026-11-06", "water_access": "unknown"}
bad_date -> start_date | start_date must be a valid YYYY-MM-DD date.
bad_pref -> preference | preference must be one of: fastest_completion, lowest_total_cost, least_irrigation_dependence, highest_net_return, more_crop_diversity.
bad_crop -> first_crop_id | first_crop_id must be null or an existing crop ID.
bad_water -> water_access | water_access must be one of: rainfed, irrigation_available, unknown.
error_shape: {"error": {"code": "INVALID_REQUEST", "field": "start_date", "message": "start_date must be a valid YYYY-MM-DD date."}, "schema_version": "1"}
http400: 400 http500: 500
lowest_upfront_cash_in_enum: False
display_name_accepted: Rajshahi
generic_error_body: AttributeError
```

Real crop-profile integration probe: `load_crop_profiles` returned the eight expected IDs; the validator accepted `aman_br11` and rejected `tomato`, `AMAN_BR11`, and ` aman_br11`.

Additional API-edge probe: `validate_explore_request(..., known_crop_ids="crop_one")` accepted `first_crop_id="crop"` because string membership is substring membership (see Note 6).

## Non-blocking observations

1. **District ID canonicalization is not enforced in E2.** The validator accepts any non-empty string unchanged, including `"Rajshahi"`, `"রাজশাহী"`, and `" rajshahi "` (probe). This is consistent with leaving unknown districts for the `unsupported_district` outcome and avoids silently substituting Rajshahi, but E9 must resolve only stable IDs and must not map a translated display name to Rajshahi. The builder's statement that the value is "a stable ID for downstream lookup, not a display name" is a design assertion, not a runtime check (`council/reports/E2-builder.md:102-104`).
2. **The HTTP route is absent by design (E10).** E2 exercises the callable request contract, not `POST /api/explore`, JSON request parsing, or `Content-Type: application/json`. No alternate endpoint was invented. This is not an E2 defect, but the endpoint contract is not yet proven by an HTTP-level test.
3. **The 500 path has a status mapping but no safe 500 envelope.** `build_error_response(RuntimeError("boom"))` raises `AttributeError` because the function assumes `.code`, `.message`, and `.field` (`src/error_contract.py:11-13`). E10 must add a generic 500 error body with no stack trace and must not pass arbitrary exceptions to this invalid-request helper. This is the one place where a future wrapper could accidentally produce an unsafe 500 response.
4. **Crop re-evaluation is not implemented in E2.** `first_crop_id` is only checked for existence; E4–E8 must evaluate the supplied crop under the request conditions and must not treat the frontend selection as a filter pass. The builder correctly says no evaluator was added (`council/reports/E2-builder.md:3-5`), so this E2 PASS does not close §14.2's re-evaluation rule.
5. **Missing `first_crop_id` is a contract ambiguity; this audit reads explicit `null` as required.** §14.2 explicitly labels only `district_id` and `start_date` as "Required" (`v1.md:532-533`), while `first_crop_id` says "`null` for first-crop options; otherwise an existing crop-profile ID" (`v1.md:534`). The initial request example includes `"first_crop_id": null` (`v1.md:516-524`), and the builder documents the key as required (`council/reports/E2-builder.md:51`). I read the example as requiring the key with explicit `null`; a frontend that omits it will receive 400. If the intended contract is "absent means null", this is over-strict and should be relaxed in a later contract decision. This is an ambiguity, not a clear violation.
6. **Bare-string `known_crop_ids` weakens the `first_crop_id` check.** The parameter is typed `Collection[str]` (`src/request_validation.py:41`), and `str` is itself a `Collection[str]`; membership at `:80-82` then becomes substring matching. Example: `known_crop_ids="crop_one"` accepts `first_crop_id="crop"`, which is not an existing crop-profile ID. The documented/tested caller passes a set (`tests/test_request_validation.py:16`), so this is a latent API edge, not an observed E2 failure. Converting to a set or rejecting `str` would close it.
7. **Minor test-strength note.** `test_every_allowed_enum_value_is_accepted` iterates the module's own `WATER_ACCESS_VALUES` and `PREFERENCE_VALUES` tuples (`tests/test_request_validation.py:62-75`), so it would not catch a required value being accidentally removed from a tuple. The code currently matches §14.2 exactly; hard-coding the three water values and five preference values in the test would lock the contract independently.
8. **Unknown input keys are ignored** (`src/request_validation.py:45-46,106-112`; test `tests/test_request_validation.py:77-84`). The spec does not require rejecting unknown keys, and dropping them prevents invented fields from leaking, but a typo such as `prefernce` silently gets the default preference. This is a product-contract choice, not a spec violation.

## Verdict

**PASS** — E2 implements the §14.2 request shape, required fields, defaults, enum allow-lists, and `lowest_upfront_cash` rejection, plus the §14.3 invalid-request envelope with 400/500 status mapping and no credential/stack-trace fields. No blocking compliance defect was found within E2's stated scope.

This PASS does not close the downstream items in Notes 1–4: the HTTP `POST /api/explore` route (E10), district stable-ID/`unsupported_district` resolution (E9), crop re-evaluation (E4–E8), and a safe generic 500 response body (E10).
