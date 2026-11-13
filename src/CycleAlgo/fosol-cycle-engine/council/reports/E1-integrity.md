# E1 Integrity Audit — Crop-Profile Loader

Audited files:

- `src/crop_profiles.py`
- `tests/test_crop_profiles.py`
- `council/reports/E1-builder.md`

Source of truth: `Q:\CycleAlgo\v1.md`; real data:
`Q:\CycleAlgo\Data\fosol_cycle_rajshahi_crop_dataset.csv`.

**Verdict: PASS.** No fabricated crop data, prices, yields, thresholds, fallback
values, endpoints, or sources were found. The real CSV has exactly the 8 expected
rows, the tests match it, and the loader records missing/unparseable values as
`None` instead of filling them.

One non-data implementation constant is untraceable to the spec/CSV/user:
`_LEAP_YEAR = 2024`. It carries no crop or economic meaning and does not change
any loaded value; see “Unsourced items”.

## 1. Dataset facts independently verified

These were read directly from the CSV, not taken from the builder report.

| Check | Real file evidence | Result |
|---|---|---|
| Row count | 8 data rows | Matches `test_loads_exactly_eight_profiles` |
| Crop IDs | `aman_br11`, `boro_brri_dhan28`, `wheat_bari_gom33`, `mustard_binasarisha9`, `lentil_binamasur9`, `mung_bari_mung6_kharif1`, `maize_rabi_bari_hybrid13`, `potato_bari_alu41` | Exact match with `EXPECTED_CROP_IDS` |
| Boro cross-year | `window_crosses_year=TRUE`, `preferred_start_mmdd=12-25`, `preferred_end_mmdd=01-10`, `supported_late_end_mmdd=02-28` | Test expectations match |
| Aman names | `crop_name_en=T. Aman rice`, `crop_name_bn=আমন ধান`, `reference_variety=BR11` | Test expectations match |
| Removed crops | `tomato`, `cucumber`, `garlic` occur 0 times in the entire CSV | Test absence check is valid |
| Encoding | CSV starts with UTF-8 BOM | `utf-8-sig` is justified |
| Dataset version | `2026-10-20_research_build_v1` | Preserved in `raw`; not invented |
| All normalized values | 38 normalized fields compared value/type against the CSV: no mismatches | No invented or altered values |

Duration values in the real CSV:

| Crop ID | Variety duration (days) | Seedling age (days) | Turnaround (days) |
|---|---:|---:|---:|
| `aman_br11` | 145–145 | 30–30 | blank |
| `boro_brri_dhan28` | 140–140 | 35–45 | blank |
| `wheat_bari_gom33` | 108–112 | blank | blank |
| `mustard_binasarisha9` | 80–84 | blank | blank |
| `lentil_binamasur9` | 100–105 | blank | blank |
| `mung_bari_mung6_kharif1` | 55–58 | blank | blank |
| `maize_rabi_bari_hybrid13` | 140–145 | blank | blank |
| `potato_bari_alu41` | 90–95 | blank | blank |

The test checks duration types and ordering, not the exact numbers above; the
independent value/type comparison confirmed that every parsed duration equals
the CSV value.

Selected independent command output for the facts above:

```text
rows 8
has_BOM True
dataset_version ['2026-10-20_research_build_v1']
crop_ids ['aman_br11', 'boro_brri_dhan28', 'wheat_bari_gom33', 'mustard_binasarisha9', 'lentil_binamasur9', 'mung_bari_mung6_kharif1', 'maize_rabi_bari_hybrid13', 'potato_bari_alu41']

value/type mismatches: NONE
field count: 38
```

Data-file integrity:

```text
$ git -C Q:\CycleAlgo status --porcelain -- Data
(no output)
$ git -C Q:\CycleAlgo diff --exit-code -- Data/fosol_cycle_rajshahi_crop_dataset.csv
(no output; exit 0)
```

CSV last write: `2026-10-21 17:11:21`; E1 builder report last write:
`2026-11-06 01:13:15`. The data file predates the build.

## 2. Provenance table

### 2.1 Data-bearing field names

All profile field names come from the real CSV header. `name_en` and `name_bn`
are the only renamed fields; the mapping is explicit in `SOURCE_FIELDS`.
`crop_id`, `name_en`, `name_bn`, and reference variety are also named in spec
§14.4.

| Group | Fields introduced | Provenance |
|---|---|---|
| Identity | `crop_id` | CSV column `crop_id`; spec §14.2/§14.4 |
| Text | `name_en`, `name_bn` | CSV columns `crop_name_en`, `crop_name_bn`; spec §14.4 |
| Text | `scientific_name`, `family`, `season_profile`, `crop_role`, `reference_variety`, `establishment_method`, `duration_precision`, `decision_duration_source`, `irrigation_guidance`, `yield_basis`, `market_price_mode`, `rotation_family_rule`, `rotation_note` | Exact CSV header columns |
| Boolean | `is_legume_n_fixing`, `window_crosses_year` | Exact CSV header columns; values are `TRUE`/`FALSE` |
| Window | `preferred_start_mmdd`, `preferred_end_mmdd`, `supported_late_end_mmdd` | Exact CSV header columns; spec §6.1 for window semantics |
| Integer days | `variety_duration_min_days`, `variety_duration_max_days`, `seedling_age_min_days`, `seedling_age_max_days`, `turnaround_days_min`, `turnaround_days_max` | Exact CSV header columns; spec §10.1 |
| Numeric | `temp_opt_min_c`, `temp_opt_max_c`, `temp_tol_min_c`, `temp_tol_max_c`, `precip_opt_min_mm`, `precip_opt_max_mm`, `precip_tol_min_mm`, `precip_tol_max_mm`, `ph_opt_min`, `ph_opt_max`, `ph_tol_min`, `ph_tol_max` | Exact CSV header columns; spec §6.2/§7 |

Programmatic check: only `name_en` and `name_bn` are absent from the CSV header;
all other 36 normalized field names are present exactly. The two exceptions have
the explicit `SOURCE_FIELDS` mapping shown above.

### 2.2 Structural output keys

These names do not assert external facts; they are implementation-defined
container keys whose semantics are required by the spec.

| Key | Provenance / justification |
|---|---|
| `data_quality` | Implementation-defined; implements spec §5 (`UNKNOWN`, missing evidence) and §15 (missing values must not become observations) |
| `missing_fields` | Implementation-defined; distinguishes empty cells from invalid values |
| `unclear_fields` | Implementation-defined; records non-empty values that could not be parsed |
| `notes` | Implementation-defined; records factual normalization notes |
| `raw` | Implementation-defined; preserves the original CSV row, consistent with spec §2/§14.4 source-preservation requirements |

### 2.3 Numbers, constants, and other literals

| Literal | Location | Provenance / classification |
|---|---|---|
| `2024` | `src/crop_profiles.py:87` (`_LEAP_YEAR`) | **No spec/CSV/user source for the exact year.** Implementation constant used only to make `02-29` valid during MM-DD validation. Any leap year works; no crop value is stored or emitted. This is the sole unsourced non-data literal. |
| `2` (regex quantifier and group indexes) | `src/crop_profiles.py:86,118` | Implementation detail of MM-DD parsing; format is evidenced by CSV values such as `12-25` |
| `"\d{2}-\d{2}"` | `src/crop_profiles.py:86` | Implementation validation regex for the CSV’s MM-DD format |
| `"TRUE"` / `"FALSE"` | `src/crop_profiles.py:106-109` | CSV boolean values; verified in real rows |
| `"utf-8-sig"` | `src/crop_profiles.py:208` | Implementation encoding; real CSV has a UTF-8 BOM |
| `"r"`, `newline=""` | `src/crop_profiles.py:208` | Standard file-reading implementation |
| `"crop_id"` | `src/crop_profiles.py:216` | CSV column |
| Error strings: `"crop-profile CSV contains no rows"`, `"crop-profile row has an empty crop_id"`, `"duplicate crop_id: "` | `src/crop_profiles.py:212,218,220` | Implementation messages; no domain claim |
| Note format: `"/"`, `": min>max"` | `src/crop_profiles.py:191` | Implementation diagnostic text; no domain claim |
| `"data_quality"`, `"missing_fields"`, `"unclear_fields"`, `"notes"`, `"raw"` | `src/crop_profiles.py:193-198` | Structural keys; see §2.2 |
| Docstrings and comments | `src/crop_profiles.py` | Documentation; no values asserted beyond the code behavior |

No endpoints, URLs, API hosts, prices, yields, thresholds, or fallback constants
appear in the new code or tests.

### 2.4 Test literals

| Literal(s) | Provenance |
|---|---|
| `8` | Real CSV row count |
| `EXPECTED_CROP_IDS` (8 IDs) | Exact real CSV `crop_id` values |
| `"T. Aman rice"`, `"আমন ধান"`, `"BR11"` | Exact real CSV values for `aman_br11` |
| `"boro_brri_dhan28"`, `True`, `"12-25"`, `"01-10"` | Exact real CSV values for Boro |
| `"tomato"`, `"cucumber"`, `"garlic"` | Spec §2: these crops must not appear as evaluated options |
| `"mung_test"`, `"bad_range"`, `"valid_test"`, `"invalid_test"`, `"crop_x"`, `"Crop X"`, `"keep me"`, `"Duplicate"`, `"Mung"` | Synthetic test fixtures; not claimed to be real crop data |
| `120`, `100` | Synthetic min>max fixture; not a crop value |
| `13-40`, `02-30` | Synthetic invalid-date fixtures |
| `02-29`, `03-01`, `03-15` | Calendar-validity fixtures; `03-15` is not asserted as a real crop window |
| `"Data"`, `"fosol_cycle_rajshahi_crop_dataset.csv"` | Real repository path components; the passing real-data test confirms the path resolves |
| `2` (`parents[2]`) | Path depth from `tests/test_crop_profiles.py` to `Q:\CycleAlgo`; verified by the passing real-data test |
| `"crops.csv"`, `"utf-8"`, `" "` (join separator), `tempfile.TemporaryDirectory` | Temporary-file test scaffolding / string formatting |
| `"crop_id"`, `"crop_name_en"`, `"crop_name_bn"`, `"preferred_start_mmdd"`, `"preferred_end_mmdd"`, `"variety_duration_min_days"`, `"variety_duration_max_days"`, `"unknown_column"` | CSV column names used to build synthetic CSV headers; `"unknown_column"` is a deliberately unknown raw-preservation fixture |
| `"name_en"`, `"name_bn"`, `"reference_variety"`, `"data_quality"`, `"missing_fields"`, `"unclear_fields"`, `"notes"`, `"raw"`, `"window_crosses_year"`, `"variety_duration"`, `"seedling_age"` | Assertion keys / field prefixes matching the loader’s documented normalized output |
| `"__main__"` | Standard Python idiom |

## 3. Re-run of the exact builder command

Command, from `Q:\CycleAlgo\fosol-cycle-engine`:

```powershell
$env:PYTHONIOENCODING='utf-8'; python --version
$env:PYTHONIOENCODING='utf-8'; python -m unittest discover -s tests -v
```

Real output:

```text
Python 3.13.2
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

This matches the builder’s pasted output and its claims of 14 tests, Python
3.13.2, and a passing suite.

## 4. Silent missing-value fill check

Independent loader run against the real CSV:

```text
loaded: 8 csv rows: 8
errors: NONE

parsed rows:
aman_br11 | dur 145 145 | seed 30 30 | turn None None | cross False | missing 3
boro_brri_dhan28 | dur 140 140 | seed 35 45 | turn None None | cross True | missing 2
wheat_bari_gom33 | dur 108 112 | seed None None | turn None None | cross False | missing 4
mustard_binasarisha9 | dur 80 84 | seed None None | turn None None | cross False | missing 4
lentil_binamasur9 | dur 100 105 | seed None None | turn None None | cross False | missing 5
mung_bari_mung6_kharif1 | dur 55 58 | seed None None | turn None None | cross False | missing 5
maize_rabi_bari_hybrid13 | dur 140 145 | seed None None | turn None None | cross False | missing 5
potato_bari_alu41 | dur 90 95 | seed None None | turn None None | cross False | missing 5
```

Additional checks:

- Every `raw` row equals the corresponding CSV `DictReader` row exactly.
- Every empty CSV cell maps to `None` and appears in `missing_fields`.
- No real row produced an `unclear_fields` entry; all non-empty values parsed.
- No `0`, `NaN`, empty string, neutral score, or fallback value was substituted.
- The only generated `None` values are explicit missing/unparseable markers,
  recorded in `data_quality`.
- Invalid dates, invalid booleans, invalid integers, and invalid numbers all
  become `None` plus `unclear_fields`; they are not defaulted.
- A `min > max` pair clears both endpoints, flags both as unclear, and adds a
  note; the test covers this.

Code-path confirmation: `_clean()` returns `None` for blank cells;
`_normalize_row()` appends the field to `missing_fields` and continues;
`_parse_bool`, `_parse_mmdd`, `_parse_integer`, and `_parse_number` return
`None` on failure, and `_normalize_row()` records those in `unclear_fields`.
There is no crop-data fallback branch and no crop-ID-specific logic in `src/`.

## 5. Builder report claim audit

| Claim in `E1-builder.md` | Evidence | Result |
|---|---|---|
| Four files created, including empty `src/__init__.py` | Files exist; `src/__init__.py` is 0 bytes | Backed |
| `src/crop_profiles.py` is the shared loader | File exists; imported by tests | Backed |
| 14 `unittest` tests | Re-run output shows 14 tests | Backed |
| No `Data/` file modified | `git status --porcelain -- Data` and `git diff -- Data` are clean; CSV mtime predates the build | Backed externally; not pasted in the builder report |
| `DataNEVERBEUSED/` was not accessed | No reference in new code/tests; no contents were used in this audit | **Not independently provable** as a negative; no evidence of access or fabricated data |
| Reads with `utf-8-sig` | `src/crop_profiles.py:208`; real CSV has BOM | Backed |
| Keys by stripped `crop_id` | `_clean(row.get("crop_id"))`; duplicate/blank checks | Backed |
| Raises `ValueError` for empty/header-only, blank, duplicate IDs | Code and validation tests | Backed |
| Every profile has `crop_id`, normalized fields, `data_quality`, `raw` | Key inventory: 1 + 38 + 2 keys per profile | Backed |
| `raw` is the unmodified CSV row | All 8 `raw` rows equal their CSV rows | Backed |
| Normalized key list is accurate | `NORMALIZED_FIELDS` contains exactly the listed 38 fields | Backed |
| Boolean parsing is `TRUE`/`FALSE`, case-insensitive, otherwise unclear | `_parse_bool` and `_normalize_row`; no contradicting data | Backed by code |
| Window parsing validates against leap year 2024 | `_LEAP_YEAR = 2024`; tests `02-29`/`02-30` | Backed, with the unsourced-constant caveat |
| Integer and numeric field lists are accurate | All names match CSV columns | Backed |
| `data_quality` meanings are accurate | Code behavior and tests | Backed |
| `min > max` clears both, flags both, adds a note | Code lines 182-191; test | Backed |
| No defaults or invented values; no crop-specific branches | No fallback values; no crop IDs in `src/` | Backed for domain data |
| Python 3.13.2 and exact test command | Re-run | Backed |
| Pasted 14-test output | Re-run matches | Backed |
| “Verified against the real 8-row Rajshahi CSV” | 8 rows, exact IDs, Boro values, names, durations independently checked | Backed |

## 6. Unsourced items

### Data-bearing items

**None.** Every crop ID, crop name, variety name, window, duration, environmental
range, irrigation text, yield-basis text, market-price-mode text, rotation rule,
and legume flag in the code/tests traces to the CSV (or, for
`tomato`/`cucumber`/`garlic`, to spec §2’s prohibition). No prices, yields,
thresholds, sources, or fallback values were invented.

### Non-data items

| Item | Why it has no external source | Impact |
|---|---|---|
| `_LEAP_YEAR = 2024` | Spec §17.5/§9.2 require leap-year handling but do not name a year; the CSV does not contain 2024; the user gave no year. Any leap year would work. | None on crop values; only permits `02-29` during MM-DD validation. |
| `data_quality`, `missing_fields`, `unclear_fields`, `notes`, `raw` | Names were chosen by the implementation; the spec requires missing evidence/unknown handling but does not dictate these key names. | Structural only; tests and downstream code use them consistently. |
| Error-message strings and the `min>max` note | Implementation diagnostics. | No domain claim. |
| Synthetic test fixtures (`mung_test`, `bad_range`, `120`, `100`, `13-40`, `02-30`, etc.) | Deliberately synthetic test inputs, not presented as Rajshahi data. | No domain claim; they test parser behavior only. |

The builder’s “`DataNEVERBEUSED/` was not accessed” claim is a negative assertion
that cannot be proven from the repository. What can be confirmed: neither the
new source nor the tests contain any reference to `DataNEVERBEUSED`, and no
contents from that directory appear in the code, tests, or this report.

## 7. Verdict

**PASS.** E1’s data integrity is sound:

- The real CSV has 8 rows with the exact IDs the tests expect.
- Boro’s cross-year window and all duration values match the CSV.
- All 38 normalized field values/types match their CSV sources.
- The loader never silently fills a missing cell; it emits `None` plus an
  explicit `missing_fields`/`unclear_fields` record and preserves `raw`.
- No invented crop data, prices, yields, thresholds, endpoints, or fallbacks
  exist in the new code or tests.
- The 14-test suite passes under Python 3.13.2, matching the builder’s pasted
  output.

Only non-blocking note: `_LEAP_YEAR = 2024` is an implementation constant with
no external provenance. If the council interprets “anything with no source” as
applying to non-data constants as well, this is the single item to reclassify;
it does not affect any agricultural or economic value.

---

Auditor access note: no file under `DataNEVERBEUSED/` was opened or read, and no
file under `Data/` was modified. A repository metadata query (`git ls-files --
Data`) returned tracked path names, including that directory; no file contents
were accessed or used. No code or test was modified during this audit.
