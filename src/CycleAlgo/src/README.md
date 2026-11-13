# V1 — Component 1: Data foundation

`data_foundation.py` loads the crop research CSV and NASA POWER daily CSV using
only Python's standard library. It does not schedule rotations or recommend crops.

## Run

From the repository root:

```powershell
python -B src/data_foundation.py
python -B -m unittest discover -s src -p "test_*.py"
```

The first command prints a validation report and changes no files. Invalid input
returns exit code 1; structurally valid input with evidence gaps returns 0 and
`VALID_WITH_WARNINGS`. Read the warnings: successful loading is not agricultural
validation or permission to calculate with unresolved values.

Optional export to a **new** file (parent directory must already exist):

```powershell
python -B src/data_foundation.py --output src/data_foundation_v1.json
```

Existing files are never overwritten. Raw/research inputs and the existing JSON
files remain unchanged. Use `--crops PATH` or `--climate PATH` for another source.
The old converter in `scripts/jsonconverter.py` is not used by this component.

## Internal contract — not the frontend comparison contract

- `schema_version`: currently `1.0`.
- `crop_data.metadata`: source filename/hash and crop count.
- `crop_data.crops[crop_id]`: identity, establishment, planting window, duration,
  evidence, and the complete typed `research` row. Environmental requirements,
  water/irrigation guidance, rotation flags, yield context and all research caveats
  remain available in `research`; no source columns are discarded.
- `climate_data.metadata`: source hash, coordinates, units, time standard, coverage,
  missing observations, calendar-year row counts and precipitation status.
- `climate_data.daily[YYYY-MM-DD]`: actual daily weather, not MM-DD climatology.
- `validation_report`: status, record counts, and scoped warnings.

Blank research values and NASA missing observations become JSON `null`. Ranges
remain ranges. Duplicate identifiers/dates, malformed values, non-finite numbers,
reversed numeric ranges, invalid dates and unexpected climate units fail loading.
Annual row completeness does **not** mean all weather variables are complete;
downstream analysis must check coverage in its own exact period and variables.

### Reviewed duration interpretation

For the existing BRRI dhan28 row (140 days and the matching source), the duration
reference is `NURSERY_SOWING`, based on the paper's **Cultivated rice varieties**
section: growth duration is from nursery sowing to harvest.

Source: https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0250897

Other duration starting events remain `null` pending verification, including BR11.
The loader never infers a starting event from the establishment method. Existing
crop confidence labels are source data, not confidence in the resulting scenario.

### Rainfall quarantine

The exact larger NASA download currently in `Data/` is identified by SHA-256.
Its sampled precipitation values are 24x the NASA API values despite its mm/day
header. For that artifact only, `precipitation_mm` is null and the unmodified value
is kept in `precipitation_source_value`. No scaling correction is silently applied.

Verification samples, checked 2026-10-30 using LST and coordinates
24.3769 N, 88.6031 E:

| Date | NASA API mm/day | Affected CSV value |
|---|---:|---:|
| 2000-01-16 | 1.53 | 36.72 |
| 2000-01-24 | 2.56 | 61.44 |
| 2020-07-02 | 10.82 | 259.68 |
| 2020-07-04 | 11.22 | 269.28 |

API: https://power.larc.nasa.gov/api/temporal/daily/point?parameters=PRECTOTCORR&community=AG&longitude=88.6031&latitude=24.3769&start=20200701&end=20200707&format=JSON

For other artifacts `SOURCE_UNITS_ACCEPTED` means only that the supplied header
matches expected units, **not** that NASA independently verified every value.
Changing the affected file changes its hash: review any replacement before use.
Temperature and other variables in the quarantined artifact remain available.
