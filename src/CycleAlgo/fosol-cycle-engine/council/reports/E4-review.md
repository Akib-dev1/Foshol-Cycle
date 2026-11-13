# E4 — Shared calendar evaluator: code review

**Reviewer:** Code Reviewer (Fosol-Cycle v1 council)
**Date:** 2026-11-06
**Scope:** `src/calendar_evaluator.py`, `tests/test_calendar.py`,
`council/reports/E4-builder.md`
**Spec context:** `../v1.md` §5, §6.1, §10.4, §17.1–17.5; §14.4 for the
lowercase machine-status rule.
**Environment:** Windows, Python 3.13.2, engine root
`Q:\CycleAlgo\fosol-cycle-engine`.

**Data safety:** `Data/DataNEVERBEUSED/` was not read, listed, or modified. No
file under `Data/` was modified. The real crop CSV was read only through
`src.crop_profiles.load_crop_profiles` for the allowed window metadata. No
source or test file was changed by this review; this report is the only repo
addition. `git status --short` shows no modified `src/` or `tests/` file; the
E4 source/test files are untracked builder work and `v1.md` is the pre-existing
user modification.

## Verdict

**FAIL — the current eight profiles pass every §17.1–17.5 case and the real
Boro/Aman year attachment is correct, but two medium correctness/validation
defects remain in the shared evaluator.**

1. A missing **optional** late bound is treated as fatal before the preferred
   window is evaluated. A leap-only late bound (`02-29`) therefore turns a
   valid preferred-window date into `unknown` for every non-leap season.
2. The late bound's year/order is never validated. A plausible next-year late
   support is silently lost, while an out-of-order cross-year late bound can
   create an eleven-month `LATE_WINDOW` with `plant_now=True` in June.

Neither defect is triggered by the eight current profiles (all late ends are
`02-28`, `12-20`, or `12-21`), so the required §17 cases still pass. They are
blocking for the shared evaluator because they can produce a false unknown on a
valid preferred window and a false favourable `plant_now` result on
inconsistent data. Findings 3–8 are low-severity hardening/wording/test gaps.

| Gate | Result |
|---|---|
| Focused E4 suite | **PASS** — 19/19, `OK`, exit 0 |
| Full suite | **PASS** — 105/105, `OK`, exit 0 |
| §17.1 preferred boundaries | **PASS** — Aman 2026-07-10 and 2026-07-24 both pass |
| §17.2 documented late date | **PASS** — Boro 2026-02-01 caution/LATE_WINDOW |
| §17.3 beyond support | **PASS** — Aman 2026-08-01 unsupported, plant_now false |
| §17.4 missing late support wording | **PASS** — no biological-impossibility/deadline claim |
| §17.5 cross-year/leap (covered cases) | **PASS** — Boro years correct; 02-29 start correct |
| §17.5 late-bound leap case (synthetic Boro edit) | **FAIL** — 02-29 late bound invalidates the season (Finding 1) |
| Status/code mapping | **PASS** — matches the builder table; no unexpected codes |
| `plant_now` | **PASS** on normal paths; **FAIL** for out-of-order late bound (Finding 2) |
| `source_ids` | **PASS** order/presence on real profiles; empty-source pass note (Finding 6) |
| No crop-ID branches | **PASS** — source scan finds none |
| JSON contract | **PASS** — 1120 rows, `allow_nan=False` |
| Season scan | **PASS** — no skipped/duplicated seasons; inclusive ends correct |
| Tests use real CSV windows / label synthetic | **PASS** — real classes load the CSV; synthetic IDs/metadata are labelled |
| Overall | **FAIL** — Findings 1–2 |

## Commands and real output

All commands were run with Python 3.13.2 from the engine root (probe scripts
were invoked by absolute temp path). Probe scripts live under
`%TEMP%\opencode\` outside the repo.

### 1. Focused E4 suite

```powershell
python -X utf8 -m unittest discover -s tests -p "test_calendar.py" -v
```

Real output:

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

----------------------------------------------------------------------
Ran 19 tests in 0.007s

OK
```

Exit code: `0`.

### 2. Full suite

```powershell
python -X utf8 -m unittest discover -s tests -v
```

Real output (all 105 tests; the E4 block is the first 19 lines):

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
Ran 105 tests in 0.099s

OK
```

Exit code: `0`.

### 3. Adversarial probe matrix

```powershell
python -X utf8 "$env:TEMP\opencode\e4_review_probe.py"
```

The matrix asserts 92 expected rows across the preferred, late, outside,
future, limit, cross-year, leap, missing-field, invalid-input, and contract
paths. Real summary:

```text
Total rows: 92  Failures: 0
```

`Failures: 0` means every row matched the documented mapping. One probe
expectation was corrected before the final run: Aman `2025-12-31` is
`unsupported`, not future, because the nearest-start rule keeps the 2025 season
as context; that policy discontinuity is Finding 3, not a matrix failure.

Key rows (real output; `lim` is `max_waiting_days`):

```text
Aman boundary  aman                     2026-07-09   None unknown     FUTURE_WINDOW_WAIT_POLICY_UNKNOWN OK
Aman boundary  aman                     2026-07-10   None pass        PREFERRED_WINDOW                 OK
Aman boundary  aman                     2026-07-24   None pass        PREFERRED_WINDOW                 OK
Aman boundary  aman                     2026-07-25   None unsupported OUTSIDE_SUPPORTED_WINDOW         OK
Boro cross-year boro                    2024-12-24   None unknown     FUTURE_WINDOW_WAIT_POLICY_UNKNOWN OK
Boro cross-year boro                    2024-12-25   None pass        PREFERRED_WINDOW                 OK
Boro cross-year boro                    2025-01-10   None pass        PREFERRED_WINDOW                 OK
Boro cross-year boro                    2025-01-11   None caution     LATE_WINDOW                      OK
Boro cross-year boro                    2025-02-28   None caution     LATE_WINDOW                      OK
Boro cross-year boro                    2025-03-01   None unsupported OUTSIDE_SUPPORTED_WINDOW         OK
Boro cross-year boro                    2026-01-10   None pass        PREFERRED_WINDOW                 OK
Boro cross-year boro                    2026-01-11   None caution     LATE_WINDOW                      OK
Boro cross-year boro                    2026-02-28   None caution     LATE_WINDOW                      OK
Boro cross-year boro                    2026-03-01   None unsupported OUTSIDE_SUPPORTED_WINDOW         OK
Boro cross-year boro                    2027-12-24   None unknown     FUTURE_WINDOW_WAIT_POLICY_UNKNOWN OK
Boro cross-year boro                    2027-12-25   None pass        PREFERRED_WINDOW                 OK
Boro cross-year boro                    2028-01-10   None pass        PREFERRED_WINDOW                 OK
Boro cross-year boro                    2028-02-28   None caution     LATE_WINDOW                      OK
Boro cross-year boro                    2028-02-29   None unsupported OUTSIDE_SUPPORTED_WINDOW         OK
Boro cross-year boro                    2028-03-01   None unsupported OUTSIDE_SUPPORTED_WINDOW         OK
Leap window    02-29..03-10             2027-02-28   None unknown     WINDOW_DATE_MISSING              OK
Leap window    02-29..03-10             2027-03-01   None unknown     WINDOW_DATE_MISSING              OK
Leap window    02-29..03-10             2028-02-28   None unknown     FUTURE_WINDOW_WAIT_POLICY_UNKNOWN OK
Leap window    02-29..03-10             2028-02-29   None pass        PREFERRED_WINDOW                 OK
Leap window    02-29..03-10             2028-03-10   None pass        PREFERRED_WINDOW                 OK
Leap window    02-29..03-10             2028-03-11   None unsupported OUTSIDE_SUPPORTED_WINDOW         OK
Jan window     01-05..01-20             2025-12-31   None unknown     FUTURE_WINDOW_WAIT_POLICY_UNKNOWN OK
Jan window     01-05..01-20             2026-01-01   None unknown     FUTURE_WINDOW_WAIT_POLICY_UNKNOWN OK
Jan window     01-05..01-20             2026-01-05   None pass        PREFERRED_WINDOW                 OK
Jan window     01-05..01-20             2026-01-20   None pass        PREFERRED_WINDOW                 OK
Jan window     01-05..01-20             2026-01-21   None unsupported OUTSIDE_SUPPORTED_WINDOW         OK
Jan window     01-05..01-20             2026-12-31   None unknown     FUTURE_WINDOW_WAIT_POLICY_UNKNOWN OK
Limit          0                        2026-06-01      0 unsupported FUTURE_WINDOW_EXCEEDS_LIMIT      OK
Limit          39 exact                 2026-06-01     39 caution     FUTURE_WINDOW_WITHIN_LIMIT       OK
Limit          38 one over              2026-06-01     38 unsupported FUTURE_WINDOW_EXCEEDS_LIMIT      OK
Limit          Boro 54 exact            2026-11-01     54 caution     FUTURE_WINDOW_WITHIN_LIMIT       OK
Limit          Boro 53 over             2026-11-01     53 unsupported FUTURE_WINDOW_EXCEEDS_LIMIT      OK
Contract       1120 rows                -               - OK          -                                OK
```

The contract row iterated all 8 real profiles over 140 dates (1120 results):
every result had exactly the five documented top-level keys, a valid status, a
non-empty code/reason, `source_ids`, all required detail keys, correct
`plant_now`/status consistency, and `json.dumps(..., allow_nan=False)` success.

### 4. Leap/late repro (Finding 1)

```powershell
python -X utf8 "$env:TEMP\opencode\e4_leap_late.py"
```

Real output:

```text
2025-12-24 -> unknown     WINDOW_DATE_MISSING              start=2025-12-25 end=2026-01-10 late=None year=2025 next=None
2026-01-05 -> unknown     WINDOW_DATE_MISSING              start=2025-12-25 end=2026-01-10 late=None year=2025 next=None
2026-01-10 -> unknown     WINDOW_DATE_MISSING              start=2025-12-25 end=2026-01-10 late=None year=2025 next=None
2026-01-11 -> unknown     WINDOW_DATE_MISSING              start=2025-12-25 end=2026-01-10 late=None year=2025 next=None
2026-02-28 -> unknown     WINDOW_DATE_MISSING              start=2025-12-25 end=2026-01-10 late=None year=2025 next=None
2026-03-01 -> unknown     WINDOW_DATE_MISSING              start=2025-12-25 end=2026-01-10 late=None year=2025 next=None
2026-12-01 -> unknown     WINDOW_DATE_MISSING              start=2026-12-25 end=2027-01-10 late=None year=2026 next=None
2026-12-25 -> unknown     WINDOW_DATE_MISSING              start=2026-12-25 end=2027-01-10 late=None year=2026 next=None

reason: The window boundary supported_late_end_mmdd does not exist in the year required for 2026-01-05 (for example 02-29 outside a leap year); the window cannot be attached.
control 02-28 2026-01-05 -> pass PREFERRED_WINDOW
control 02-28 2026-12-01 -> unknown FUTURE_WINDOW_WAIT_POLICY_UNKNOWN
```

The profile is the real `boro_brri_dhan28` with only
`supported_late_end_mmdd` changed to `02-29` in both the normalized field and
`raw`. The preferred window `2025-12-25..2026-01-10` is fully valid;
`2026-01-05` is inside it, yet the result is `unknown` because the optional
late bound is absent in non-leap 2026.

## Probe results by requested area

### Boundary dates and inclusive ends

- Aman `2026-07-09` future (1 day); `2026-07-10` pass; `2026-07-24` pass;
  `2026-07-25`/`2026-07-26` unsupported. Both preferred ends are inclusive.
- Boro `2024-12-24` future; `2024-12-25` pass; `2025-01-10` pass;
  `2025-01-11` late; `2025-02-28` late; `2025-03-01` unsupported. Same for
  the 2025-26, 2026-27, and 2027-28 seasons.
- Leaps: `2024-02-29` pass; `2024-03-10` pass; `2024-03-11` unsupported;
  `2028-02-29` pass; `2028-03-10` pass; `2028-03-11` unsupported.
- Early-January synthetic window: `2026-01-04` future; `2026-01-05` pass;
  `2026-01-20` pass; `2026-01-21` unsupported; `2026-12-31` future for
  `2027-01-05`.

### Cross-year Boro around Dec/Jan/Feb/Mar

The daily scan (2023-01-01 + 2200 days) produced these supported runs:

```text
Boro: 7 season runs
  2023-01-01 .. 2023-02-28 start_year=2022 days=59
  2023-12-25 .. 2024-02-28 start_year=2023 days=66
  2024-12-25 .. 2025-02-28 start_year=2024 days=66
  2025-12-25 .. 2026-02-28 start_year=2025 days=66
  2026-12-25 .. 2027-02-28 start_year=2026 days=66
  2027-12-25 .. 2028-02-28 start_year=2027 days=66
  2028-12-25 .. 2029-01-08 start_year=2028 days=15
```

The first run is partial because the scan starts mid-season; the last is
truncated by the scan range. Every complete season is 66 consecutive supported
days (17 preferred + 49 late), with the correct start year and no skipped or
duplicated season.

### Non-cross-year Aman across the year

```text
Aman: 3 season runs
  2025-07-10 .. 2025-07-24 start_year=2025 days=15
  2026-07-10 .. 2026-07-24 start_year=2026 days=15
  2027-07-10 .. 2027-07-24 start_year=2027 days=15
```

No duplicate or skipped Aman season.

### Leap 2028-02-29 vs 2027-02-29

- `2028-02-29` is accepted as a real date; a `02-29..03-10` window passes on it.
- `2027-02-29` is rejected by `_coerce_date` with
  `ValueError: start_date must be an ISO date (YYYY-MM-DD): '2027-02-29'`.
- A `02-29` preferred **start** in 2027 returns `WINDOW_DATE_MISSING` for
  2027-02-28, 2027-03-01, 2027-03-10, and 2027-03-11.
- A `02-29` preferred **late end** in a non-leap year fails the whole season;
  see Finding 1.

### `window_crosses_year` inconsistency

Rejected as `unknown` / `WINDOW_DATA_INCONSISTENT` for same-year data with
`True`, cross-year data with `False`, and same-day data with `True`.

### Missing / empty / invalid fields

- Missing or blank start/end/basis/type/cross-year/date-precision return the
  specific `WINDOW_*_MISSING` / `DATE_PRECISION_MISSING` codes.
- Blank `supported_late_end_mmdd` is treated as "no documented late window"
  and produces `OUTSIDE_SUPPORTED_WINDOW`; this matches the Aman §17.4 case.
- Invalid late text (`02-30`, `13-01`) returns `WINDOW_LATE_END_INVALID`.
- Invalid preferred MM-DD text returns `WINDOW_START_INVALID` /
  `WINDOW_END_INVALID`.
- A loader-normalized invalid MM-DD (top-level `None`, `raw` still `02-30`)
  returns `WINDOW_START_INVALID` because `_text` falls back to `raw`; see
  Finding 5.

### `max_waiting_days`

- `None` -> `FUTURE_WINDOW_WAIT_POLICY_UNKNOWN`.
- `0` with a 1-day wait -> `FUTURE_WINDOW_EXCEEDS_LIMIT`.
- `1` with a 1-day wait -> `FUTURE_WINDOW_WITHIN_LIMIT`.
- `39` with a 39-day wait -> within; `38` -> exceeds.
- Boro `54` with a 54-day wait -> within; `53` -> exceeds.
- Negative -> `ValueError`; float and bool -> `TypeError`.
- Exact-boundary behaviour is inclusive, consistent with §10.4's maximum
  waiting interval.

### JSON and contract

All 1120 real-profile rows serialized with `allow_nan=False`; exact top-level
key set `{status, code, reason, source_ids, details}`; all required detail
keys present; ISO dates/`None`/ints/bools only. No `dt.date` leaked.

## Findings

### 1. Medium — a missing optional late bound invalidates valid preferred/future results

**Files:** `src/calendar_evaluator.py:253-259` (late bound added to the same
`missing` list), `:138-145` (missing check returns unknown), `:151-184`
(future branch), `:186-210` (preferred branch), `:212-239` (late/outside
branches).

**Repro (real Boro profile, only the late field changed to `02-29`):**

```python
import copy
from src.crop_profiles import load_crop_profiles
from src.calendar_evaluator import evaluate_calendar_fit

p = load_crop_profiles(r"Q:\CycleAlgo\Data\fosol_cycle_rajshahi_crop_dataset.csv")
boro = copy.deepcopy(p["boro_brri_dhan28"])
boro["supported_late_end_mmdd"] = "02-29"
boro["raw"]["supported_late_end_mmdd"] = "02-29"
evaluate_calendar_fit(boro, "2026-01-05")
```

**Observed:** `unknown` / `WINDOW_DATE_MISSING`; reason says the window cannot
be attached. **Expected:** `pass` / `PREFERRED_WINDOW`, because
`2026-01-05` is inside the valid preferred window
`2025-12-25..2026-01-10`; the absent late bound is optional and irrelevant to a
preferred-window date. The same profile returns `pass` in a leap season, so the
result changes by year only because of the optional late bound.

**Why it matters:** a plausible data edit (`02-29` as "end of February") makes
every non-leap season unknown, including valid preferred windows and future
options. `WINDOW_DATE_MISSING` is safe (not a false pass), but it hides the
correct §6.1 outcome and contradicts §17.1/§17.5 for a valid window.

**Fix direction:** separate `missing_preferred` (start/end) from
`missing_late`. Return the preferred result when `start`/`end` are valid and
`proposed` is inside the preferred window; return the future result when
`proposed < start` even if the end/late bound is missing; use the missing late
bound only for dates after the preferred end, where the late extension
actually matters. Add a `02-29` late-end test.

### 2. Medium — late-bound year/order is not validated; a false `LATE_WINDOW` is possible

**Files:** `src/calendar_evaluator.py:252` (`late_end` always attached to
`end_year`), `:310-315` (`_support_end` silently ignores a late end before the
preferred end), `:212-220` (late branch), `:242-267` (candidate construction).

**Repro A — next-year late support silently lost:**

```python
profile = {
    "preferred_start_mmdd": "11-15",
    "preferred_end_mmdd": "11-30",
    "supported_late_end_mmdd": "01-15",
    "window_crosses_year": False,
    # ... metadata as in a loader profile ...
}
evaluate_calendar_fit(profile, "2027-01-05")
```

**Observed:** `unknown` / `FUTURE_WINDOW_WAIT_POLICY_UNKNOWN` for
`2027-11-15` (314 days), with `supported_late_end=2027-01-15` — a date
*before* the preferred start. **Expected:** `caution` / `LATE_WINDOW` for the
2026 season's late support through `2027-01-15`, or `unknown` /
`WINDOW_DATA_INCONSISTENT` if that shape is not supported.

**Repro B — out-of-order cross-year late bound creates an 11-month late
window:**

```python
profile = {
    "preferred_start_mmdd": "12-25",
    "preferred_end_mmdd": "01-10",
    "supported_late_end_mmdd": "12-30",
    "window_crosses_year": True,
    # ... metadata ...
}
evaluate_calendar_fit(profile, "2026-06-01")
```

**Observed:** `caution` / `LATE_WINDOW`, `plant_now=True`, with
`preferred_end=2026-01-10` and `supported_late_end=2026-12-30`; the reason
claims June 1 is inside the supported-late window. **Expected:**
`unknown` / `WINDOW_DATA_INCONSISTENT` (or no late support). A late bound
`12-30` for a January end cannot mean December of the same end year.

**Repro C — late before preferred end is accepted and reported:**

```python
profile = {
    "preferred_start_mmdd": "01-01",
    "preferred_end_mmdd": "03-01",
    "supported_late_end_mmdd": "02-01",
    "window_crosses_year": False,
    # ... metadata ...
}
```

**Observed:** `2026-02-15` -> `pass` with
`supported_late_end=2026-02-01` (before the preferred end); `2026-03-02` ->
`unsupported`, late bound ignored. **Expected:** `unknown` /
`WINDOW_DATA_INCONSISTENT` for an out-of-order late bound.

**Why it matters:** a malformed late row can produce a false favourable
`plant_now=True` result (Repro B), and a plausible next-year late support is
silently dropped (Repro A). The current eight profiles do not trigger it, but
the loader does not validate late-bound order either, so the evaluator is the
last line of defence. The spec auditor's Note 2 already flagged the
late-end-only cross-year shape as a non-blocking hardening item; this review
confirms it with a concrete wrong result and adds the out-of-order variants.

**Fix direction:** after attaching the late bound, require
`late_end > preferred_end` (and `late_end > preferred_start`); otherwise
return `WINDOW_DATA_INCONSISTENT`. If a next-year late extension is a supported
shape, add an explicit late-cross-year rule/field and attach it to
`end_year + 1` when the month/day is before the preferred end; do not infer it
silently. Add tests for Repro A/B/C.

### 3. Low — the calendar-year candidate boundary flips a just-ended season into next season's future option

**Files:** `src/calendar_evaluator.py:285-307` (`considered` keeps
`start_year` in `(Y, Y+1)` and windows whose support ended in `Y`; nearest
start breaks the tie).

**Repro (real profiles):**

```text
Aman     2026-12-31 -> unsupported OUTSIDE_SUPPORTED_WINDOW         next=None wait=None
Aman     2027-01-01 -> unknown     FUTURE_WINDOW_WAIT_POLICY_UNKNOWN next=2027-07-10 wait=190
potato   2026-12-31 -> unsupported OUTSIDE_SUPPORTED_WINDOW         next=None wait=None
potato   2027-01-01 -> unknown     FUTURE_WINDOW_WAIT_POLICY_UNKNOWN next=2027-11-01 wait=304
wheat    2026-12-31 -> unsupported OUTSIDE_SUPPORTED_WINDOW         next=None wait=None
wheat    2027-01-01 -> unknown     FUTURE_WINDOW_WAIT_POLICY_UNKNOWN next=2027-11-15 wait=318
mustard  2026-12-31 -> unsupported OUTSIDE_SUPPORTED_WINDOW         next=None wait=None
mustard  2027-01-01 -> unknown     FUTURE_WINDOW_WAIT_POLICY_UNKNOWN next=2027-10-25 wait=297
```

The Dec 31 result suppresses the next season's future option; Jan 1 exposes
it. For a window ending `12-31`, a proposed `01-01` jumps 353 days to the next
season instead of reporting the season that ended yesterday:

```text
Dec20-31 2026-12-31 -> pass PREFERRED_WINDOW
Dec20-31 2027-01-01 -> unknown FUTURE_WINDOW_WAIT_POLICY_UNKNOWN next=2027-12-20 wait=353
```

**Why it matters:** this is a one-day product discontinuity, not a false pass:
`plant_now` stays false and the future date/wait are explicit. It follows the
builder's stated "season that ended in an earlier year does not displace the
upcoming window" rule, so it is a product-policy question rather than a clear
spec violation. The spec auditor's Note 5 records the same behaviour. The UI
should not be surprised that a future option appears/disappears at New Year.

**Fix direction (optional):** define "just expired" by proximity to the
previous support end, not by calendar year, or always expose the nearest future
window when the current season is outside support. Do not change the deliberate
§17.3 just-expired behaviour without product sign-off.

### 4. Low — missing `date_precision` after the preferred window returns a definitive `unsupported`

**Files:** `src/calendar_evaluator.py:186-193` (precision checked only inside
preferred), `:212-239` (late/outside branches do not re-check).

**Repro:** Aman profile with `date_precision=None`, proposed `2026-08-01` ->
`unsupported` / `OUTSIDE_SUPPORTED_WINDOW`, despite §6.1 item 4 ("Missing ...
window evidence: unknown") and §5 ("unknown values never become an automatic
pass"). A late date with missing precision returns `caution` / `LATE_WINDOW`
(conservative), but an outside date is asserted as definitive.

**Why it matters:** current profiles all carry a concrete `date_precision`, so
this is latent. If a boundary is `WEEK_APPROX` or unknown, the exact outside
cutoff is not known; a date just after the window could still be inside the
approximate boundary.

**Fix direction:** require usable precision for late/outside results, or
downgrade an outside result with missing precision to `unknown` (or
`PREFERRED_WINDOW_APPROXIMATE`-style caution where appropriate). Add an
outside/late missing-precision test.

### 5. Low — MM-DD fields fall back to `raw`, contrary to the builder report

**Files:** `src/calendar_evaluator.py:447-454` (`_field_value` falls back to
`raw` for every field), `:457-462` (`_text`), `:42-59` (MM-DD reads);
`council/reports/E4-builder.md:64-67` says only metadata falls back to `raw`.

**Repro:**

```python
profile = {**synthetic, "preferred_start_mmdd": None,
           "raw": {**synthetic_raw, "preferred_start_mmdd": "07-10"}}
evaluate_calendar_fit(profile, "2026-07-10")   # pass/PREFERRED_WINDOW
```

**Observed:** pass, using the `raw` value. For a loader profile, an invalid
cell becomes top-level `None` but `raw` keeps the invalid text, so the result
is `WINDOW_START_INVALID` rather than `WINDOW_START_MISSING` — which is
arguably a better diagnostic, but it is not the documented contract.

**Why it matters:** the normalized profile is supposed to be authoritative. A
caller that deliberately clears a field (or a future loader change) can be
overridden by stale `raw` text. The current real data is unaffected.

**Fix direction:** use `_field_value` only for the metadata fields, and read the
three MM-DD fields from the normalized top level only; or document the
fallback for MM-DD and add a test.

### 6. Low — a profile with no source references still passes

**Files:** `src/calendar_evaluator.py:39` (`source_ids` is just the non-empty
source fields), `:356-365` (`_result` emits it without validation).

**Repro:** both `source_planting_window` and `source_local_calendar` empty ->
`pass` / `PREFERRED_WINDOW`, `source_ids=[]`.

**Why it matters:** §6.1 describes "sourced windows"; §5 says missing required
evidence is `unknown`. A pass with no evidence reference is favourable. All
eight real profiles carry both sources, so this is latent.

**Fix direction:** add a `WINDOW_SOURCE_MISSING` unknown (or require at least
one source id before pass/caution), and add a no-source test.

### 7. Informational — `WINDOW_LATE_END_MISSING` is unreachable

**Files:** `src/calendar_evaluator.py:61-69` (late block guarded by
`late_text is not None`), `:411-419` (`_parse_window_field` returns the
missing code only when `text is None`).

Because the block is skipped when `late_text` is `None`, the
`WINDOW_LATE_END_MISSING` argument can never be returned. This is dead code,
not a wrong result. Either remove it or use it for a distinct "late field
present but empty" policy.

### 8. Low — test coverage gaps around the failing edges

**Files:** `tests/test_calendar.py`.

The suite covers the required minimum well, but it does not cover the cases
that expose Findings 1–6:

- `02-29` as `supported_late_end_mmdd` (Finding 1). `test_leap_day...`
  (`:203-218`) only uses `02-29` as the preferred start.
- A late bound in the next calendar year, a late bound before the preferred
  end, and a cross-year late bound in December (Finding 2).
- Boro `2025-02-28`/`2026-03-01` (late end inclusive/outside); the late test
  uses only `2026-02-01` (`:106-114`).
- Boro `2025-12-24`/`2025-12-25` (day before/start); the future test uses
  `2026-11-01` (`:174-180`).
- `max_waiting_days=0` and the exact Boro 54-day boundary; the limit test uses
  Aman 39/38 only (`:235-254`).
- A non-crossing December window evaluated on Dec 31 vs Jan 1 (Finding 3).
- Missing sources and missing `date_precision` after the preferred window
  (Findings 4/6).
- A contract test that asserts the `status`/`code` for each real crop at its
  boundaries, not only key presence/JSON (`:310-339`).

Adding one focused test per bullet would have caught Findings 1–2 and pins the
Finding 3 policy.

## What passed

- **§17.1:** Aman `2026-07-10` and `2026-07-24` both `pass` /
  `PREFERRED_WINDOW`, `plant_now=True`, correct resolved dates and
  `source_ids` order.
- **§17.2:** Boro `2026-02-01` `caution` / `LATE_WINDOW`, `plant_now=True`,
  dates `2025-12-25..2026-01-10`, late `2026-02-28`, `window_start_year=2025`.
- **§17.3:** Aman `2026-08-01` `unsupported` /
  `OUTSIDE_SUPPORTED_WINDOW`, `plant_now=False`, no next-window claim.
- **§17.4:** Aman `2026-07-25` reason says "No documented late window",
  "not a biological impossibility", and "not a proven deadline".
- **§17.5 (covered cases):** Boro Jan 2026 -> 2025 start year; Boro Dec 2026
  -> 2026 start year; Boro late Feb 2028 -> 2027 start year; leap
  `02-29..03-10` passes on `2028-02-29` and returns `WINDOW_DATE_MISSING` for
  the 2027 dates.
- **Status/code mapping:** every table row observed exactly once; no unexpected
  status/code pair. Lowercase statuses match §14.4.
- **`plant_now`:** false for future, outside, unknown, geography, date-missing,
  precision-missing, and missing-field paths; true only for preferred,
  approximate preferred, and late results (except Finding 2B, where the wrong
  late window is selected).
- **Reasons:** all paths explain the outcome; preferred/late/outside reasons
  explicitly avoid calling the preferred end a proven biological deadline;
  the future/limit reason calls the limit a product-relevance cutoff.
- **`source_ids`:** real profiles return
  `["source_planting_window", "source_local_calendar"]` in the documented
  order; one-source profiles return just that field.
- **No crop-ID branches:** `tests/test_calendar.py:341-347` scans `src/*.py`
  for all eight IDs and finds none.
- **JSON:** 1120 real-profile results serialize with `allow_nan=False`; all
  dates are ISO strings; no zero substitution for unknown quantities.
- **Season scan:** Aman has exactly one 15-day run per July; Boro has exactly
  one 66-day run per season (17 preferred + 49 late) with the correct start
  year; no skipped or duplicated season.
- **Inclusive ends:** preferred start/end and late end are inclusive; the day
  after is outside; waiting limits are inclusive at the exact maximum.
- **Tests use real CSV windows:** `RealProfileCalendarTests` and
  `ResultContractTests` load
  `Data/fosol_cycle_rajshahi_crop_dataset.csv`; synthetic profiles use
  `crop_id="synthetic"`, `SYNTHETIC_*` type/readiness, and `synthetic://`
  sources, so synthetic data is clearly labelled.

## Non-blocking observations

- `_coerce_date` accepts Python's extended ISO forms (`20260710` and
  `2026-W28-5`) through `date.fromisoformat`, although the docstring says
  `YYYY-MM-DD`. The E2 request validator rejects these before the evaluator is
  called, so this is a direct-call leniency, not an HTTP-contract breach.
- `_parse_mmdd` validates syntactically valid leap-year dates but does not
  enforce a late bound after the preferred end; that is Finding 2.
- The `WINDOW_DATE_MISSING` reason says "the window cannot be attached" even
  when only the optional late bound is missing and the preferred window is
  attached; Finding 1.
- The geographic check is a token match on `NOT_RAJSHI_EXACT` /
  `LOCATION_TRANSFERABILITY` (spelling matches the current data). A future
  profile with `NOT_RAJSHAHI_EXACT` or another scope phrase would not be
  caught. This is the spec auditor's Note 3; no current impact.
- The waiting-limit basis is stated on the exclusion path ("product relevance
  cutoff") but not in `details` or on the within-limit path; this is the spec
  auditor's Note 4. The only implemented policy is a product cutoff, so no
  scientific-maximum claim is made.
- Overall candidate/conditional aggregation and range-level partial exclusion
  remain E9/E6 responsibilities; E4 correctly exposes the per-date
  `waiting_limit_status` they need.

## Final verdict

**FAIL** — Findings 1 and 2 are medium correctness/validation defects in the
shared evaluator. The current eight profiles pass §17.1–17.5 and the real
Boro/Aman year attachment is correct, so this is not a regression in the
current dataset; it is a latent shared-component defect that can produce a
false unknown on a valid preferred window (Finding 1) and a false
`plant_now=True` late result on inconsistent data (Finding 2B). Re-review is
required after those two are fixed and tests are added. Findings 3–8 are
low/informational and may be accepted as hardening.
