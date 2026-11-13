# E1 — Crop-profile loader and normalizer

Status: complete. Verified against the real 8-row Rajshahi CSV.

## Files created

- `src/__init__.py` — package marker (empty).
- `src/crop_profiles.py` — shared loader/normalizer.
- `tests/test_crop_profiles.py` — 14 `unittest` tests.
- `council/reports/E1-builder.md` — this report.

No file in `Q:\CycleAlgo\Data\` was modified, and `DataNEVERBEUSED/` was not accessed.

## Public API

```python
from src.crop_profiles import load_crop_profiles

profiles: dict[str, dict] = load_crop_profiles("path/to/crop_dataset.csv")
```

- Reads with `utf-8-sig`, keys by stripped `crop_id`.
- Raises `ValueError` for an empty/header-only CSV, a blank `crop_id`, or a duplicate `crop_id`.
- Every profile has `crop_id`, the normalized fields below, `data_quality`, and `raw`.
- `raw` is the unmodified CSV row, so no source column is lost.

Normalized keys:

- Text: `name_en`, `name_bn` (from `crop_name_en`, `crop_name_bn`), `scientific_name`,
  `family`, `season_profile`, `crop_role`, `reference_variety`,
  `establishment_method`, `duration_precision`, `decision_duration_source`,
  `irrigation_guidance`, `yield_basis`, `market_price_mode`,
  `rotation_family_rule`, `rotation_note`.
- Boolean: `is_legume_n_fixing`, `window_crosses_year` (`TRUE`/`FALSE`,
  case-insensitive; any other non-empty value -> `None` + unclear).
- Window: `preferred_start_mmdd`, `preferred_end_mmdd`,
  `supported_late_end_mmdd` (validated against leap year 2024; invalid -> `None`
  + unclear).
- Integer days: `variety_duration_min_days`, `variety_duration_max_days`,
  `seedling_age_min_days`, `seedling_age_max_days`, `turnaround_days_min`,
  `turnaround_days_max`.
- Numeric: `temp_opt_min_c`, `temp_opt_max_c`, `temp_tol_min_c`,
  `temp_tol_max_c`, `precip_opt_min_mm`, `precip_opt_max_mm`,
  `precip_tol_min_mm`, `precip_tol_max_mm`, `ph_opt_min`, `ph_opt_max`,
  `ph_tol_min`, `ph_tol_max`.

`data_quality`:

- `missing_fields` — normalized fields whose source cell was empty/absent.
- `unclear_fields` — non-empty values that could not be parsed or validated.
- `notes` — short factual notes, e.g. `variety_duration_min_days/variety_duration_max_days: min>max`.

If a min/max pair has `min > max`, both fields are set to `None`, both are
listed in `unclear_fields`, and a note is added. No defaults or invented values
are applied. There are no crop-specific branches.

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

----------------------------------------------------------------------
Ran 14 tests in 0.016s

OK
```
