# E1 — Crop-profile loader: code review

**Reviewer:** Code Reviewer (Fosol-Cycle v1 council)
**Date:** 2026-11-06
**Scope:** `src/crop_profiles.py`, `tests/test_crop_profiles.py`, `council/reports/E1-builder.md`
**Spec context:** `../v1.md` §2, §10.1, §11, §14.4
**Environment:** Windows, Python 3.13.2, engine root `Q:\CycleAlgo\fosol-cycle-engine`

**Data safety:** `Data/DataNEVERBEUSED/` was not read, listed, or modified. No file under
`Data/` was modified. All synthetic CSVs were created under `%TEMP%` outside the repo. No
source or test file was changed by this review; this report is the only repo addition.

## Verdict

**PASS — no blocking correctness defect found against E1's stated contract.**

| Gate | Result |
|---|---|
| Unit tests | **PASS** — 14/14 |
| Real 8-row Rajshahi CSV | **PASS** — 8 profiles, exact expected IDs |
| Normalization / `data_quality` | **PASS** — independent check found 0 mismatches |
| Raw preservation | **PASS** for the real 83-column CSV — all 8 `raw` rows equal source rows |
| Generic loader | **PASS** — no crop-id branches; no crop names in `src/` |
| Adversarial edges | **PASS** with low-severity caveats (findings 1–4) |
| Test coverage | Low-severity gaps (finding 5) |

Findings 1–5 are low-severity edge/hardening issues and do not affect the real dataset.
Finding 6 is a validation-scope gap for downstream evaluators, not a defect against E1's
parse/normalize contract. None changes the E1 result. No adversarial input caused an
unexpected crash; invalid inputs either produced `None` plus quality flags or the
documented `ValueError`.

## Commands and real output

### 1. Unit tests

From the engine root:

```powershell
cd Q:\CycleAlgo\fosol-cycle-engine
cmd /c "set PYTHONIOENCODING=utf-8&& python -m unittest discover -s tests -v 2>&1"
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

----------------------------------------------------------------------
Ran 14 tests in 0.017s

OK
```

A direct PowerShell pipeline reports a `NativeCommandError` because `unittest` writes
progress to stderr; the `cmd /c` invocation above is the clean run. Exit code check:

```powershell
cmd /c "set PYTHONIOENCODING=utf-8&& python -m unittest discover -s tests -v >nul 2>&1"; Write-Output "EXIT:$LASTEXITCODE"
```

```text
EXIT:0
```

### 2. Adversarial probes (temp files outside the repo)

Probe scripts were written to `%TEMP%\opencode\`; probe CSVs were written under
`%TEMP%\e1review_*`. Command:

```powershell
$env:PYTHONIOENCODING='utf-8'
python "$env:TEMP\opencode\e1_review_probe.py"
```

Excerpts from the real probe output (long `missing_fields` lists elided with `...`; the
probe scripts and CSVs are under `%TEMP%`):

```text
### header-only
status=ValueError
error: crop-profile CSV contains no rows

### truly empty
status=ValueError
error: crop-profile CSV contains no rows

### blank crop_id (empty cell)
status=ValueError
error: crop-profile row has an empty crop_id

### blank crop_id (spaces)
status=ValueError
error: crop-profile row has an empty crop_id

### duplicate crop_id exact
status=ValueError
error: duplicate crop_id: x

### duplicate crop_id after strip
status=ValueError
error: duplicate crop_id: x

### invalid mmdd 13-40
status=OK
{"crop_id": "x", ... "unclear": ["preferred_start_mmdd"], "notes": [], "values": {"preferred_start_mmdd": [null, "NoneType"]}}

### invalid mmdd 02-30
status=OK
{"crop_id": "x", ... "unclear": ["preferred_start_mmdd"], ...}

### invalid mmdd 2-3
status=OK
{"crop_id": "x", ... "unclear": ["preferred_start_mmdd"], ...}

### valid mmdd leap 02-29
status=OK
{"crop_id": "x", ... "unclear": [], "values": {"preferred_start_mmdd": ["02-29", "str"]}}

### bool mixed-case TRUE/FALSE
status=OK
{"crop_id": "x", ... "unclear": [], "values": {"is_legume_n_fixing": [true, "bool"], "window_crosses_year": [false, "bool"]}}

### bool yes/no
status=OK
{"crop_id": "x", ... "unclear": ["is_legume_n_fixing", "window_crosses_year"], "values": {"is_legume_n_fixing": [null, "NoneType"], "window_crosses_year": [null, "NoneType"]}}

### min>max int
status=OK
{"crop_id": "x", ... "unclear": ["variety_duration_min_days", "variety_duration_max_days"], "notes": ["variety_duration_min_days/variety_duration_max_days: min>max"], "values": {"variety_duration_min_days": [null, "NoneType"], "variety_duration_max_days": [null, "NoneType"]}}

### min==max allowed
status=OK
{"crop_id": "x", ... "unclear": [], "values": {"variety_duration_min_days": [100, "int"], "temp_opt_min_c": [20.0, "float"], "temp_opt_max_c": [20.0, "float"]}}

### numeric nan/inf
status=OK
{"crop_id": "x", ... "unclear": ["temp_opt_min_c", "temp_opt_max_c"], "values": {"temp_opt_min_c": [null, "NoneType"], "temp_opt_max_c": [null, "NoneType"]}}

### UTF-8 BOM
status=OK
{"crop_id": "x", ... "unclear": [], "values": {"name_en": ["Crop", "str"]}, "raw": {"crop_id": "x", "crop_name_en": "Crop"}}

### unknown extra columns
status=OK
{"crop_id": "x", ... "unclear": [], "values": {"name_en": ["Crop", "str"]}, "raw": {"crop_id": "x", "crop_name_en": "Crop", "weird_col": "keep me"}}

### whitespace around values
status=OK
{"crop_id": "x", ... "unclear": [], "values": {"name_en": ["Crop X", "str"]}, "raw": {"crop_id": "  x  ", "crop_name_en": "  Crop X  "}}
```

Additional probe results (second script):

```text
Arabic-Indic mmdd ٠٣-١٥: accepted as "٠٣-١٥", unclear=[]
fullwidth mmdd ０３-１５: accepted as "０３-１５", unclear=[]
duplicate crop_name_en columns: name_en="Second", raw has only "Second"; "First" lost
header case Crop_ID: ValueError "crop-profile row has an empty crop_id"
header with leading space: ValueError "crop-profile row has an empty crop_id"
tabs around values: name_en="Crop" (stripped), raw preserves tabs
reordered header, CRLF, quoted comma, quoted newline: all load correctly
```

Adversarial case summary:

| Case | Observed |
|---|---|
| Header-only CSV | `ValueError: crop-profile CSV contains no rows` |
| Truly empty CSV | same `ValueError` |
| Blank `crop_id` (empty or spaces) | `ValueError: crop-profile row has an empty crop_id` |
| Duplicate `crop_id` exact / after strip | `ValueError: duplicate crop_id: x` |
| Duplicate `crop_id` case variant (`x` / `X`) | both load — case-sensitive (observation) |
| Invalid `13-40`, `02-30`, `2-3`, `00-00` | `None` + `unclear_fields` |
| `02-29` | accepted as valid (leap year 2024) |
| Mixed-case `True` / `fAlSe` | `True` / `False` booleans, no unclear |
| `yes` / `no`, `1` / `0` | `None` + both in `unclear_fields` |
| Blank optional values | `None` + `missing_fields` |
| `min > max` (int or float) | both `None` + both unclear + note |
| `min == max` | accepted |
| `100.0`, `1e3`, `1_000` in integer fields | accepted as ints (finding 2) |
| Negative durations | accepted, no flag (finding 6) |
| `nan` / `inf` numeric | `None` + unclear |
| UTF-8 BOM | loads; BOM not in normalized values or `raw` |
| Unknown extra column | preserved in `raw`, not added to profile |
| Whitespace around values | stripped in normalized fields; preserved in `raw` |
| Ragged short row | missing fields; `raw` has `None` values |
| Ragged long row | extra values stored in `raw` under key `None` (finding 3) |
| Duplicate header name | earlier column lost from both normalized value and `raw` (finding 3) |
| Header with whitespace / different case | misleading `empty crop_id` error (finding 4) |
| CRLF, quoted comma, quoted newline, reordered header | load correctly |
| CSV with no `crop_id` column | `ValueError: crop-profile row has an empty crop_id` |

### 3. Real-dataset consistency checks

Command:

```powershell
$env:PYTHONIOENCODING='utf-8'
python "$env:TEMP\opencode\e1_review_probe3.py"
```

Real output:

```text
profiles: 8
consistency problems: 0
all normalized values match independent parsing
```

This check independently re-parsed every non-empty source cell for all 38 normalized
fields and compared it with the loader output. It also verified that no `min > max` pair
survived normalization. Zero mismatches.

Raw-row equality check on all 8 rows and all 83 columns:

```text
header columns: 83 unique: 83 rows: 8
raw equality problems: none
profile count: 8
```

For the real CSV, `raw` key order and values match `csv.DictReader` exactly for every
row. `data_quality.missing_fields` also matches the empty-cell set for every row/field
(0 mismatches); `unclear_fields` and `notes` are empty for all 8 profiles.

Real-data missing fields (from probe output):

| `crop_id` | `missing_fields` | `unclear_fields` | `notes` |
|---|---|---|---|
| `aman_br11` | `supported_late_end_mmdd`, `turnaround_days_min`, `turnaround_days_max` | none | none |
| `boro_brri_dhan28` | `turnaround_days_min`, `turnaround_days_max` | none | none |
| `wheat_bari_gom33` | `seedling_age_min_days`, `seedling_age_max_days`, `turnaround_days_min`, `turnaround_days_max` | none | none |
| `mustard_binasarisha9` | `seedling_age_min_days`, `seedling_age_max_days`, `turnaround_days_min`, `turnaround_days_max` | none | none |
| `lentil_binamasur9` | `supported_late_end_mmdd`, `seedling_age_min_days`, `seedling_age_max_days`, `turnaround_days_min`, `turnaround_days_max` | none | none |
| `mung_bari_mung6_kharif1` | `supported_late_end_mmdd`, `seedling_age_min_days`, `seedling_age_max_days`, `turnaround_days_min`, `turnaround_days_max` | none | none |
| `maize_rabi_bari_hybrid13` | `supported_late_end_mmdd`, `seedling_age_min_days`, `seedling_age_max_days`, `turnaround_days_min`, `turnaround_days_max` | none | none |
| `potato_bari_alu41` | `supported_late_end_mmdd`, `seedling_age_min_days`, `seedling_age_max_days`, `turnaround_days_min`, `turnaround_days_max` | none | none |

These are real source gaps, not loader defaults: the corresponding CSV cells are empty.
`turnaround_days_*` is absent for all eight crops, so E6 must treat preparation time as
unknown/conditional rather than zero.

A separate semantic sanity check found no non-positive duration, no pH outside 0–14, no
`window_crosses_year` mismatch against start/end order, and no supported late end before
the preferred end in the real CSV.

### 4. Generic-loader check

```powershell
$env:PYTHONIOENCODING='utf-8'
python "$env:TEMP\opencode\e1_review_probe2.py"
```

Real output (tail of the probe):

```text
aman absent
boro absent
wheat absent
mustard absent
lentil absent
mung absent
maize absent
potato absent
tomato absent
cucumber absent
garlic absent
```

A harness grep of `src/**/*.py` for the same crop names returned `No matches found`.
A grep for crop-id branching returned only the identity/duplicate checks:

```text
src/crop_profiles.py:217:        if crop_id is None:
src/crop_profiles.py:219:        if crop_id in profiles:
```

No crop-specific branch, no hard-coded crop list in the loader.

## Findings

### Numbered bug list

**1. Low — MM-DD validation accepts non-ASCII digits and returns them uncanonicalized.**
`src/crop_profiles.py:86` (`_MMDD_RE` uses `\d`) and `src/crop_profiles.py:113-123`
(`_parse_mmdd` returns the original `text`). Repro (temp CSV):

```csv
crop_id,preferred_start_mmdd
x,٠٣-١٥
```

Observed: `preferred_start_mmdd == '٠٣-١٥'`, `unclear_fields == []`. Standard downstream
parsing fails:

```text
datetime.datetime.strptime('2025-٠٣-١٥', '%Y-%m-%d')
ValueError: time data '2025-٠٣-١٥' does not match format '%Y-%m-%d'
```

The loader therefore emits a value it treats as valid MM-DD, but standard date parsing
rejects it; downstream would need Unicode-aware parsing. The real CSV is ASCII-only, so
this is non-blocking. Fix: use `re.ASCII`/`[0-9]` and return a canonical ASCII
`f"{month:02d}-{day:02d}"`.

**2. Low — integer fields are parsed through `float`, causing silent coercion and
large-value corruption.**
`src/crop_profiles.py:126-133` (`_parse_integer`). Repro:

```csv
crop_id,variety_duration_min_days
x,9007199254740993
```

Observed: `9007199254740992`, `unclear_fields == []`. Also accepted silently:
`1e3` → `1000`, `1_000` → `1000`, `100.0000000000000001` → `100`. The real durations are
small positive integers, so this is non-blocking, but the loader can change a source
value without flagging it. Fix: parse with `int` under a strict decimal-integer regex, or
use `Decimal` and reject non-integer syntax.

**3. Low — duplicate CSV header names lose the earlier column from both the normalized
value and `raw`; extra values beyond the header are stored under a `None` key.**
`src/crop_profiles.py:198` (`profile["raw"] = dict(row)`) and
`src/crop_profiles.py:209` (`csv.DictReader`). Repro:

```csv
crop_id,crop_name_en,crop_name_en
x,First,Second
```

Observed: `name_en == "Second"` and
`raw == {"crop_id": "x", "crop_name_en": "Second"}`; `"First"` is lost. For a ragged row:

```csv
crop_id,crop_name_en
x,Crop,EXTRA1,EXTRA2
```

Observed: `raw` contains a key `None` (rendered `"null"` in JSON) with
`["EXTRA1", "EXTRA2"]`, so the extra values have no column name. The real CSV has 83
unique headers, so there is no current impact. This limits the builder report's general
claim that "no source column is lost" for malformed headers; validate unique headers if
that is a hard guarantee.

**4. Low — header names are not stripped or case-normalized; failures are reported as an
empty `crop_id` rather than a missing-column error.**
`src/crop_profiles.py:208-218`. Repro:

```csv
 crop_id ,crop_name_en
x,Crop
```

Observed: `ValueError: crop-profile row has an empty crop_id`. The header `Crop_ID` gives
the same misleading error. The real header is clean, so this is non-blocking. Fix: strip
`reader.fieldnames` (and optionally compare case-insensitively) and raise an explicit
"missing crop_id column" error when the column is absent.

**5. Low (test gap) — the documented blank-`crop_id` rejection is not tested, and several
edge behaviors verified manually are untested.**
`tests/test_crop_profiles.py:95-163`. The code correctly rejects:

```csv
crop_id,crop_name_en
,Crop
```

with `ValueError: crop-profile row has an empty crop_id`, but no test covers it. Missing
coverage also includes mixed-case booleans, UTF-8 BOM, whitespace-trimmed `crop_id`,
duplicate-after-strip, and float `min > max`. Code behavior was verified in the probes;
add tests to prevent regressions.

**6. Low (validation gap / scope) — syntactically valid but agronomically or relationally
invalid values pass `data_quality` clean.**
`src/crop_profiles.py:126-191`; only syntax and `min > max` are checked. Repros:

```csv
crop_id,variety_duration_min_days,variety_duration_max_days
x,-10,-5
```

→ `-10`/`-5`, `unclear_fields == []`, `notes == []`.

```csv
crop_id,ph_opt_min,ph_opt_max
x,-2,20
```

→ `-2.0`/`20.0`, no flag.

```csv
crop_id,preferred_start_mmdd,preferred_end_mmdd,window_crosses_year
x,12-25,01-10,FALSE
```

→ `window_crosses_year == False`, start/end parsed, no flag.

```csv
crop_id,preferred_start_mmdd,preferred_end_mmdd,supported_late_end_mmdd
x,11-01,11-30,11-15
```

→ late end `11-15` before preferred end `11-30`, no flag.

These are hypothetical adversarial inputs; the real CSV has positive durations, in-range
pH, and consistent windows. E1's stated contract is parse/normalize, not agronomic
validation, so this is not counted as a blocker. If the council expects range/consistency
validation in E1, finding 6 becomes a defect; otherwise E4/E6 must guard before using these
values in timelines.

### Non-blocking observations

- **Leap-day output needs a leap year downstream.** `02-29` is accepted (validated against
  2024, `src/crop_profiles.py:87`, `:120`), but Python 3.13
  `datetime.strptime('02-29', '%m-%d')` uses the default year 1900 and fails; even
  `strptime('2025-02-29', '%Y-%m-%d')` fails. E4 must parse with an explicit leap year or
  handle Feb 29 explicitly. The builder test intentionally treats `02-29` as valid.
- **Some fields are intentionally normalized only in `raw`.** `date_precision`,
  `window_basis`, `planting_window_type`, `hard_deadline_validated`,
  `turnaround_rule_status`, `source_*`, `yield_reference_*`, and readiness flags are not
  in `NORMALIZED_FIELDS`; all 83 columns are preserved in `raw`. Downstream E4/E6/E8 must
  read `raw` or promote these fields, otherwise window-precision cautions, source IDs, and
  yield evidence can be lost. This is a handoff risk, not an E1 loader defect.
- **Duplicate `crop_id` detection is case-sensitive.** `x` and `X` both load. The spec does
  not state that IDs are case-insensitive, and the real dataset is lowercase; note only.
- **`data_quality.missing_fields` includes columns absent from the header as missing.**
  This matches the builder report's "empty/absent" definition and is accurate, but a
  minimal/partial CSV reports many missing fields.
- **No sentinel-value normalization.** The real CSV was scanned for `NA`, `N/A`, `NULL`,
  `NIL`, `NONE`, `-`, `--`, `?`, `UNKNOWN`, and `TBD` in normalized source columns; no hits.
  If future data uses such sentinels in text fields, they would be stored as text rather
  than `None`; numeric fields would be `unclear`. Add explicit sentinel handling only if
  the source format changes.

## Spec notes

- **§2 — data sources:** The loader reads only the path it is given; it does not touch
  NASA/SMAP or any other source. No removed crop (tomato, cucumber, garlic) is added; the
  real dataset has exactly the eight expected profiles. `DataNEVERBEUSED/` was untouched.
- **§10.1 — duration reference point:** `variety_duration_min_days` /
  `variety_duration_max_days` remain ranges (no averaging), and `duration_precision`,
  `decision_duration_source`, `establishment_method`, and `seedling_age_*` are exposed for
  the downstream conditional-timing decision. Missing values stay `None`.
- **§11 — rotation compatibility:** `family`, `is_legume_n_fixing`, `rotation_family_rule`,
  and `rotation_note` are normalized; the loader invents no sequence restriction or
  nitrogen-saving assumption.
- **§14.4 — unknown quantities:** Empty cells, unparseable values, and invalid `min > max`
  pairs become `None`, never `0`, `NaN`, or an invented neutral value. `raw` retains the
  source `source_*` columns for downstream `source_ids`.

## Files reviewed

- `src/crop_profiles.py` — 222 lines, read in full.
- `tests/test_crop_profiles.py` — 167 lines, read in full.
- `council/reports/E1-builder.md` — 87 lines, read in full.
- `../v1.md` §2, §10.1, §11, §14.4 — read.
