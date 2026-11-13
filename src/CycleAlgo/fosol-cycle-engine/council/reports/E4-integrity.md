# E4 — Integrity audit: calendar evaluator

Auditor: INTEGRITY AUDITOR (anti-hallucination), Fosol-Cycle v1 council
Date: 2026-11-06
Scope: `src/calendar_evaluator.py`, `tests/test_calendar.py`, `council/reports/E4-builder.md`
Primary sources: `Q:\CycleAlgo\v1.md` (§5, §6.1, §17, §19); `Q:\CycleAlgo\Data\fosol_cycle_rajshahi_crop_dataset.csv` (8 rows)
Code/tests modified by this audit: **none**.

## Verdict

**PASS.** Every real window value exercised by the evaluator traces to the crop CSV; every
synthetic value is explicitly marked synthetic; no agronomic deadline, late window, maximum
waiting number, or geographic applicability claim is invented. The §17.1–17.5 tests match the
builder report and the real fixture values, and the re-run full suite passes 105/105.

Residual notes are listed in “Unsourced or unverifiable items”; none changes the verdict.

## 1. Provenance method

- Real values were read directly from the CSV row identified by `crop_id`, using the exact
  header columns named below. No value was copied from the builder report.
- The evaluator was executed against the loaded profiles for every real-profile test date. The
  resolved dates/years in Table B are actual returned values, not restatements of test literals.
- Codes and reason strings were read from `src/calendar_evaluator.py`; provenance is assigned
  to the spec rule or to the profile field that supplies their variable parts.
- `source_ids` were checked against the CSV header and against every row’s non-empty source
  cells.
- `max_waiting_days` was checked by signature, source scan, and repository-wide grep.

## 2. Provenance tables

### A. Real crop window values (verbatim CSV)

All values in this table are from `Data/fosol_cycle_rajshahi_crop_dataset.csv`, row
`crop_id=<first column>`, columns `preferred_start_mmdd`, `preferred_end_mmdd`,
`supported_late_end_mmdd`, `window_crosses_year`, `planting_window_type`, `date_precision`,
`hard_deadline_validated`. An em dash means the CSV cell is empty, not an evaluator default.

| crop_id | start | end | late | crosses | window_type | precision | hard_deadline_validated |
|---|---|---|---|---|---|---|---|
| `aman_br11` | `07-10` | `07-24` | — | `FALSE` | `RECOMMENDED_RAJSHI_EXACT` | `DAY` | `FALSE` |
| `boro_brri_dhan28` | `12-25` | `01-10` | `02-28` | `TRUE` | `BRRI_RECOMMENDED_VARIETY_WINDOW_PLUS_NW_OBSERVED_LATE_BOUND` | `DAY` | `FALSE` |
| `wheat_bari_gom33` | `11-15` | `11-30` | `12-20` | `FALSE` | `RECOMMENDED_EXACT_WITH_SUPPORTED_EXTENSION` | `DAY` | `FALSE` |
| `mustard_binasarisha9` | `10-25` | `11-15` | `12-21` | `FALSE` | `RECOMMENDED_WEEK_APPROX_WITH_LATE_SOWING_SUPPORT` | `WEEK_APPROX` | `FALSE` |
| `lentil_binamasur9` | `10-25` | `11-14` | — | `FALSE` | `RECOMMENDED_WEEK_APPROX` | `WEEK_APPROX` | `FALSE` |
| `mung_bari_mung6_kharif1` | `03-15` | `03-25` | — | `FALSE` | `MODELLED_OPTIMUM_BANGLADESH_NOT_RAJSHI_EXACT` | `DAY_BUT_LOCATION_TRANSFERABILITY_MEDIUM` | `FALSE` |
| `maize_rabi_bari_hybrid13` | `10-15` | `11-15` | — | `FALSE` | `BAMIS_RECOMMENDED_EXACT_RABI` | `DAY` | `FALSE` |
| `potato_bari_alu41` | `11-01` | `11-07` | — | `FALSE` | `NORTHERN_BANGLADESH_OPTIMUM_WEEK_APPROX` | `WEEK_APPROX` | `FALSE` |

`source_ids` provenance: the evaluator’s `_SOURCE_FIELDS` is exactly
`("source_planting_window", "source_local_calendar")` (`src/calendar_evaluator.py:20`). Both are
real CSV columns, and both cells are non-empty in all 8 rows. The returned `source_ids` are the
stable field names, not the URLs; the builder report says this explicitly. Spot-check of the
rows actually used by real-profile tests:

| crop_id | `source_local_calendar` (CSV value) | `source_planting_window` (CSV value) |
|---|---|---|
| `aman_br11` | `https://www.bamis.gov.bd/en/calendar/1/74/2/` | `https://link.springer.com/article/10.1186/s40068-021-00239-z` |
| `boro_brri_dhan28` | `https://www.bamis.gov.bd/en/calendar/1/75/2/` | `https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0250897` |
| `lentil_binamasur9` | `https://www.bamis.gov.bd/en/calendar/1/58/2/` | `https://bina.gov.bd/pages/static-pages/6922df3b933eb65569e20bee` |
| `mung_bari_mung6_kharif1` | `https://www.bamis.gov.bd/en/calendar/1/86/2/` | `https://journals.plos.org/climate/article?id=10.1371/journal.pclm.0000180` |

### B. Resolved dates, years, statuses and waits (real profiles, actual returns)

Years are not stored in the CSV. They are computed by attaching the CSV MM-DD bounds to
candidate start years `Y-1`, `Y`, `Y+1` and selecting the containing/nearest instance
(`src/calendar_evaluator.py:102-106, 242-307`). The table records the actual resolved values.
All real-profile results have `source_ids = ["source_planting_window",
"source_local_calendar"]`; omitted from the table only for width.

| crop_id | proposed | resolved start | resolved end | late end | start year | status / code | waiting days | limit | limit status |
|---|---|---|---|---|---|---|---|---|---|
| `aman_br11` | `2026-07-10` | `2026-07-10` | `2026-07-24` | — | 2026 | pass / `PREFERRED_WINDOW` | — | — | `not_applicable` |
| `aman_br11` | `2026-07-24` | `2026-07-10` | `2026-07-24` | — | 2026 | pass / `PREFERRED_WINDOW` | — | — | `not_applicable` |
| `boro_brri_dhan28` | `2026-02-01` | `2025-12-25` | `2026-01-10` | `2026-02-28` | 2025 | caution / `LATE_WINDOW` | — | — | `not_applicable` |
| `aman_br11` | `2026-08-01` | `2026-07-10` | `2026-07-24` | — | 2026 | unsupported / `OUTSIDE_SUPPORTED_WINDOW` | — | — | `not_applicable` |
| `aman_br11` | `2026-07-25` | `2026-07-10` | `2026-07-24` | — | 2026 | unsupported / `OUTSIDE_SUPPORTED_WINDOW` | — | — | `not_applicable` |
| `boro_brri_dhan28` | `2026-01-05` | `2025-12-25` | `2026-01-10` | `2026-02-28` | 2025 | pass / `PREFERRED_WINDOW` | — | — | `not_applicable` |
| `boro_brri_dhan28` | `2026-12-25` | `2026-12-25` | `2027-01-10` | `2027-02-28` | 2026 | pass / `PREFERRED_WINDOW` | — | — | `not_applicable` |
| `aman_br11` | `2026-06-01` | `2026-07-10` | `2026-07-24` | — | 2026 | unknown / `FUTURE_WINDOW_WAIT_POLICY_UNKNOWN` | 39 | `None` | `unknown` |
| `aman_br11` | `2026-01-01` | `2026-07-10` | `2026-07-24` | — | 2026 | unknown / `FUTURE_WINDOW_WAIT_POLICY_UNKNOWN` | 190 | `None` | `unknown` |
| `boro_brri_dhan28` | `2026-06-01` | `2025-12-25` | `2026-01-10` | `2026-02-28` | 2025 | unsupported / `OUTSIDE_SUPPORTED_WINDOW` | — | — | `not_applicable` |
| `boro_brri_dhan28` | `2026-11-01` | `2026-12-25` | `2027-01-10` | `2027-02-28` | 2026 | unknown / `FUTURE_WINDOW_WAIT_POLICY_UNKNOWN` | 54 | `None` | `unknown` |
| `lentil_binamasur9` | `2026-10-30` | `2026-10-25` | `2026-11-14` | — | 2026 | caution / `PREFERRED_WINDOW_APPROXIMATE` | — | — | `not_applicable` |
| `mung_bari_mung6_kharif1` | `2026-03-20` | `2026-03-15` | `2026-03-25` | — | 2026 | unknown / `WINDOW_GEOGRAPHY_UNKNOWN` | — | — | `not_applicable` |

Arithmetic check of every nonzero wait: `2026-06-01 → 2026-07-10` = 39 days;
`2026-01-01 → 2026-07-10` = 190 days; `2026-11-01 → 2026-12-25` = 54 days. The synthetic
year-end case `2026-12-31 → 2027-01-05` = 5 days. No wait value comes from a constant.

### C. Status/code/reason provenance

Status vocabulary (`pass`, `caution`, `unknown`, `unsupported`) is the implementation form of
v1 §5 statuses (`v1.md:129-136`). Codes are implementation tokens; their conditions map to
v1 §6.1 (`v1.md:150-163`). Reason strings are assembled from the profile fields/computed dates
shown, plus the stated spec language. No reason string introduces an unsourced date, deadline,
waiting number, or new district; `this district` is the project’s Rajshahi scope.

| Code | Status | Reason content (template) | Provenance |
|---|---|---|---|
| `PREFERRED_WINDOW` | pass | inside documented preferred window (`start`..`end`); end is a sourced calendar boundary, not a proven biological deadline | CSV start/end (`calendar_evaluator.py:186-201`); v1 §6.1.1 and `v1.md:159` |
| `PREFERRED_WINDOW_APPROXIMATE` | caution | inside preferred window but boundary is approximate (`date_precision`), not exact; not a proven biological deadline | CSV `date_precision` (`:202-210`); v1 §6.1.1 and `v1.md:159` |
| `LATE_WINDOW` | caution | after preferred end but inside documented supported-late window (to `late_end`); late planting carries documented risk | CSV `supported_late_end_mmdd` and `window_basis` (`:212-220`); v1 §6.1.2 |
| `OUTSIDE_SUPPORTED_WINDOW` (no late) | unsupported | outside documented window; no documented late window; not a biological impossibility and preferred end not a proven deadline | CSV empty late cell (`:222-231`); v1 §6.1.3, `v1.md:144,159` |
| `OUTSIDE_SUPPORTED_WINDOW` (late) | unsupported | outside preferred window and beyond supported-late end; outside documented support; not a biological impossibility | CSV late bound (`:232-239`); v1 §6.1.3, `v1.md:159` |
| `FUTURE_WINDOW_WAIT_POLICY_UNKNOWN` | unknown | next documented preferred window starts `start` (`N` days later); no maximum waiting policy configured; future, not plant-now | computed next start + caller `None` (`:151-165`); v1 §6.1 (`v1.md:161`) and unresolved waiting limit (`v1.md:744`) |
| `FUTURE_WINDOW_WITHIN_LIMIT` | caution | next window starts `start` (`N` days); within configured maximum waiting limit of `L` days; future option | computed wait + caller limit (`:166-174`); v1 `v1.md:161` |
| `FUTURE_WINDOW_EXCEEDS_LIMIT` | unsupported | next window starts `start` (`N` days); exceeds explorer’s maximum waiting gap of `L`; product relevance cutoff, not biological impossibility | computed wait + caller limit (`:175-184`); v1 `v1.md:161,144` |
| `WINDOW_GEOGRAPHY_UNKNOWN` | unknown | window is not Rajshahi-exact (`window_type`, `date_precision`); cannot support a calendar pass for this district | CSV `planting_window_type` / `date_precision` markers (`:116-129`); v1 §6.1.4 |
| `WINDOW_DATA_INCONSISTENT` | unknown | `window_crosses_year` conflicts with preferred start/end order; cannot attach years safely | CSV `window_crosses_year` + start/end (`:86-100`); v1 `v1.md:163` |
| `WINDOW_DATE_MISSING` (no candidate) | unknown | no calendar-window instance could be attached to the proposed date | candidate construction/selection (`:131-137, 270-307`); v1 `v1.md:163` |
| `WINDOW_DATE_MISSING` (bad boundary) | unknown | boundary does not exist in the required year (e.g. `02-29` outside a leap year) | calendar arithmetic (`:138-145, 318-322`); v1 `v1.md:163` |
| `WINDOW_START_MISSING` / `WINDOW_END_MISSING` / `WINDOW_LATE_END_MISSING` / `WINDOW_BASIS_MISSING` / `WINDOW_TYPE_MISSING` / `WINDOW_CROSS_YEAR_MISSING` / `DATE_PRECISION_MISSING` | unknown | “The crop profile has no usable `<field>`; calendar fit is unknown rather than an automatic pass.” | missing field in profile (`:46-93, 333-353, 465-469`); v1 §6.1.4 and `v1.md:144` |
| `WINDOW_START_INVALID` / `WINDOW_END_INVALID` / `WINDOW_LATE_END_INVALID` | unknown | same “no usable `<field>`” reason; malformed MM-DD is treated as unusable | parser (`:411-431`); v1 §6.1.4 and `v1.md:144` |

`WINDOW_LATE_END_MISSING` is present in the parser call but currently unreachable: the late
branch only runs when `late_text is not None` (`:61-69`), and `_parse_window_field` returns the
“missing” code only for `None`. This is dead code, not an invented claim; the builder’s mapping
table does not list it.

### D. Waiting-limit values

| Value | Where it comes from | Provenance |
|---|---|---|
| `None` (default) | `max_waiting_days` default `None` | `src/calendar_evaluator.py:26`; “no numeric default supplied” in builder report |
| `None` (real-profile tests) | tests call the evaluator with no limit | `tests/test_calendar.py:88,107,117,124,133,141,150,160,168,175,184,194`; result `waiting_limit_days=None` |
| `39` / `38` (synthetic only) | explicit caller arguments in the synthetic limit test | `tests/test_calendar.py:238,247`; these are test policy values, not product defaults or crop data |
| `39`, `190`, `54`, `5` (waiting days) | date subtraction between proposed date and next window start | `calendar_evaluator.py:152`; arithmetic shown in §2B |

Repository-wide grep found no numeric `max_waiting_days` default or constant: the only
occurrences are the `None` signature/validation, the builder report, and the synthetic test
arguments above.

### E. Synthetic test profiles

`tests/test_calendar.py:44-75` builds profiles with:

- `crop_id = "synthetic"`;
- `planting_window_type = "SYNTHETIC_DAY_EXACT"`;
- `window_basis = "synthetic test window"`;
- `window_guard_readiness = "SYNTHETIC"`;
- `algorithm_use_note = "synthetic test only"`;
- source values `synthetic://planting` and `synthetic://calendar`.

Synthetic window values (`07-10..07-24`, `02-29..03-10`, `01-05..01-20`) are therefore clearly
test fixtures and are not presented as crop data. The leap-day window is explicitly
non-agronomic test input; its `02-29` boundary is a calendar edge case, not a crop deadline.

## 3. No invented agronomic deadline, late window, waiting maximum, or geography

- **Deadlines:** no endpoint is labelled a proven biological deadline. Every such reason says
  the opposite (`:197-207, 215-238`). `hard_deadline_validated` is never a pass/fail input; it
  only appears in `details` (`:346-348`).
- **Late windows:** the only late bound is `supported_late_end_mmdd` from the profile
  (`:44, 61-69, 252`). There is no fallback late window, no heuristic extension, and no
  late value for rows whose CSV cell is empty. Real late bounds are Boro `02-28`, Wheat
  `12-20`, Mustard `12-21`; all other rows are empty.
- **Maximum waiting:** no product maximum exists. `max_waiting_days` is `None` by default and
  is used only when the caller supplies an explicit non-negative integer (`:26, 38, 401-408`).
  When absent, a future window is `unknown`, not silently accepted or rejected.
- **Geography:** the only geographic gate is the explicit marker check
  (`NOT_RAJSHI_EXACT` in `planting_window_type`, or `LOCATION_TRANSFERABILITY` in
  `date_precision`) at `:116-129`. It adds no coordinates, districts, or new applicability
  claims. It correctly catches the Mung profile’s own
  `MODELLED_OPTIMUM_BANGLADESH_NOT_RAJSHI_EXACT` /
  `DAY_BUT_LOCATION_TRANSFERABILITY_MEDIUM` metadata.
- **Reasons:** every reason string is a template filled with the resolved dates, computed
  waiting days, caller limit, or profile metadata above. No reason contains a hardcoded
  agronomic number.

## 4. No crop-ID-specific branches in `src/`

- The builder’s test `test_no_crop_id_specific_branch_in_src` passes
  (`tests/test_calendar.py:341-347`), scanning all `src/*.py` for the eight real crop IDs.
- Independent broader scan for crop-name tokens (`aman`, `boro`, `brri`, `dhan`, `wheat`,
  `mustard`, `lentil`, `mung`, `maize`, `potato`, `sarisha`, `masur`) found **no matches** in
  `src/`. In `src/calendar_evaluator.py`, the only geographic references are `Rajshahi-exact`
  / `this district` inside the negative `WINDOW_GEOGRAPHY_UNKNOWN` reason; no crop-specific
  branch.
- Real crop IDs appear only in `tests/test_calendar.py` (`CROP_IDS`, `setUpClass`, individual
  tests), which the task explicitly permits.

## 5. §17.1–17.5 test claims vs tests and real fixtures

v1 §17 minimum cases 1–5 (`v1.md:697-703`):

| Spec case | Test | Real fixture basis | Actual result | Match |
|---|---|---|---|---|
| 17.1 preferred passes at both boundaries | `test_aman_preferred_window_passes_at_both_boundaries` | Aman CSV `07-10..07-24` | `2026-07-10` pass, `2026-07-24` pass; both `PREFERRED_WINDOW` | Yes |
| 17.2 documented late date becomes conditional | `test_boro_documented_late_date_is_caution` | Boro CSV late `02-28`, cross-year window | `2026-02-01` caution / `LATE_WINDOW`; resolved `2025-12-25..2026-01-10`, late `2026-02-28` | Yes |
| 17.3 beyond support is not a normal candidate | `test_aman_after_support_is_not_a_normal_candidate` | Aman has no late bound | `2026-08-01` unsupported / `OUTSIDE_SUPPORTED_WINDOW`, `plant_now=false` | Yes |
| 17.4 missing late support is not biological impossibility | `test_missing_late_window_is_not_a_biological_impossibility` | Aman CSV late cell empty | `2026-07-25` unsupported; reason contains “no documented late window”, “not a biological impossibility”, “not a proven deadline” | Yes |
| 17.5 cross-year and leap-year resolve correctly | `test_boro_cross_year_windows_resolve_to_correct_years`; `test_leap_day_window_accepts_leap_year_and_rejects_other_years` | Boro CSV `12-25..01-10`, late `02-28`, `TRUE`; synthetic `02-29..03-10` | Boro `2026-01-05` → `2025-12-25..2026-01-10`, late `2026-02-28`; Boro `2026-12-25` → `2026-12-25..2027-01-10`, late `2027-02-28`; synthetic `2028-02-29` pass; `2027-02-28` and `2027-03-01` `WINDOW_DATE_MISSING` | Yes |

Additional checked claims: Aman `2026-06-01` → next `2026-07-10`, 39 days, limit unknown;
Aman `2026-01-01` → 190 days; Boro `2026-06-01` unsupported; Boro `2026-11-01` → next
`2026-12-25`, 54 days; Lentil `2026-10-30` caution / `PREFERRED_WINDOW_APPROXIMATE`; Mung
`2026-03-20` unknown / `WINDOW_GEOGRAPHY_UNKNOWN`. All match the builder report.

## 6. Re-run output

Focused run:

```powershell
python -X utf8 -m unittest discover -s tests -p "test_calendar.py" -v
```

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
Ran 19 tests in 0.006s

OK
```

Full run:

```powershell
python -X utf8 -m unittest discover -s tests -v
```

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
Ran 105 tests in 0.096s

OK
```

Comparison with `council/reports/E4-builder.md`:

- Focused: builder says 19 tests, `OK`; re-run is 19 tests, `OK`. Test names/order match.
  Elapsed time differs only by run noise (`0.005s` in the report vs `0.006s` here).
- Full: builder says 105 tests, `OK`; re-run is 105 tests, `OK`. A programmatic comparison of
  the 105 test names extracted from the builder report and this run found identical order, with
  no missing or extra test. Elapsed time differs (`0.103s` in the report vs `0.096s` here),
  which is expected timing variance and not a content discrepancy.
- Python version is 3.13.2, matching the builder report.

## 7. `source_ids` and `hard_deadline_validated`

- `source_ids` = list of the two stable CSV column names actually present, in the order
  `source_planting_window`, `source_local_calendar` (`src/calendar_evaluator.py:20, 39`). The
  CSV header contains both names once; all 8 rows have non-empty values. The Aman test asserts
  the exact list (`tests/test_calendar.py:101-104`). This is a trace to real source fields, not
  invented URLs. Caveat: consumers receive field names, not URL values; the builder report
  accurately says “stable source field names”, so this is not misrepresented.
- `hard_deadline_validated` is `FALSE` in all 8 real CSV rows. The evaluator parses it into
  `details["hard_deadline_validated"]` (`src/calendar_evaluator.py:346-348`), and the Aman test
  asserts `False` (`tests/test_calendar.py:98-100`). A source scan shows no branch on this
  field. The builder report’s statement that it is “recorded but never used as a pass/fail
  rule” is accurate. The value is not presented as a validated deadline.

## 8. Unsourced or unverifiable items

1. **Historical read-access claim.** The builder report says `Data/DataNEVERBEUSED/` was not
   read/listed/modified. Current git status shows no `Data/` modifications, but historical
   read access cannot be proven from the workspace. The auditor did not open or use any file
   contents under that directory. Process note: a `git ls-files -- Data` tracking query and a
   top-level `Data` directory listing inadvertently exposed path/directory names under
   `DataNEVERBEUSED`; no contents were read, and no value in this report derives from them.
2. **Elapsed times.** Builder report timings (`0.103s`, `0.005s`) differ from this re-run
   (`0.096s`, `0.006s`). Test counts, names, and `OK` results match; timing is not evidence of a
   discrepancy.
3. **Unreachable `WINDOW_LATE_END_MISSING`.** The code path is dead because the late parser is
   only called when the text is non-`None`. Not a false claim or a data fabrication, but it is
   code that cannot currently produce its documented code.
4. **Marker-based geography gate.** The gate catches explicit `NOT_RAJSHI_EXACT` /
   `LOCATION_TRANSFERABILITY` markers. It does not independently validate every profile’s
   geography; for example, the potato profile’s `NORTHERN_BANGLADESH_OPTIMUM_WEEK_APPROX`
   returns caution via `WEEK_APPROX`, not `WINDOW_GEOGRAPHY_UNKNOWN`. This is a documented
   limitation of the marker approach, not an invented geographic claim; the builder report does
   not claim full geographic validation.
5. **Status token case.** v1 shows `PASS/CAUTION/UNKNOWN/UNSUPPORTED`; the evaluator returns
   lowercase tokens. The mapping is one-to-one and the builder report documents the lowercase
   API tokens. No semantic mismatch.

## 9. Verdict

**PASS.** No fabricated crop window, late bound, year, status, waiting maximum, or geographic
claim was found. Real values trace to the CSV; synthetic fixtures are clearly synthetic; the
§17.1–17.5 claims match the tests and actual returned values; the full suite re-runs clean.
The residual items above are transparency/design notes, not integrity failures.
