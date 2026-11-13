# Fosol-Cycle: one worked Rajshahi comparison

## What this is

Fosol-Cycle is a Rajshahi crop-sequence explorer. The interactive product is
`POST /api/explore`; this page's three sequences are optional fixed-scenario
demonstration content, not a replacement for the API or a limit on the paths it
generates. They let a reader see what the evidence says, what it does not say, and
what a farmer or local adviser still has to confirm. This is not a recommendation,
a yield model, a forecast, or a field prescription.

The full artifact is [`examples/featured_comparison.json`](../examples/featured_comparison.json).
It is generated offline from the local NASA POWER API cache by
[`scripts/featured_comparison.py`](../scripts/featured_comparison.py). No second
scoring algorithm is used: displayed weather values come from the engine's branch
climate summaries and its ranking entry.

There is **no frontend in this repository**. The frontend handoff fields and the
disabled economics/irrigation-dependence controls are documented in
[`FRONTEND_HANDOFF.md`](FRONTEND_HANDOFF.md).

Only these three examples are featured. The engine also generated broader
conditional paths; the artifact records their counts under `exploratory_scope` and
does not present them as recommendations or as a full ranking.

## The three examples

All examples use the same request context: start **2026-11-06**, water access
**unknown**, the server's **180-day** initial-wait policy, no waiting limit, and
common complete POWER seasons.

| | Baseline | Alternative A | Alternative B |
|---|---|---|---|
| Sequence | Mustard → Boro → T. Aman | Mustard → Mung → T. Aman | Wheat → Mung → T. Aman |
| Why it is here | Locally documented Rajshahi pattern | BARC low-water/legume pattern documented outside Rajshahi | Documented Kushtia sequence explored under Rajshahi weather and reference profiles |
| Documentation status | Rajshahi regional survey | Khulna/Satkhira trial context; exploratory here | Kushtia sequence; Rajshahi applicability unverified |
| Initial wait | 0 days | 0 days | 9 days |
| Sequence duration | 382–405 days | 382–405 days | 367–396 days |
| Earliest / latest completion | 2027-12-02 / 2027-12-16 | 2027-12-02 / 2027-12-16 | 2027-12-02 / 2027-12-16 |
| Families / legume | Brassicaceae, Poaceae / no | Brassicaceae, Fabaceae, Poaceae / yes | Poaceae, Fabaceae / yes |
| Engine status | Conditional | Conditional | Conditional |

The baseline is a **regional pattern**, not a universal practice. The two
alternatives are candidate comparisons, not researched Rajshahi rotations. The
wheat example is a documented Kushtia sequence explored under Rajshahi weather and
the engine's reference crop profiles; local applicability is unverified. Related
Rajshahi evidence documents a Wheat–Mung–T. Aus pattern, but that is not a
validation of this sequence.

### Realized schedules

Each view uses two completion-optimized schedules. These are examples, not
weather-optimized schedules and not a worst-case bound.

| Example | Schedule | P1 | H1 | P2 | H2 | P3 | H3 | Days |
|---|---|---|---|---|---|---|---|---|
| Baseline | min | 2026-11-15 | 2027-02-03 | 2027-02-03 | 2027-06-23 | 2027-07-10 | 2027-12-02 | 382 |
| Baseline | max | 2026-11-06 | 2027-01-25 | 2027-01-25 | 2027-06-14 | 2027-07-24 | 2027-12-16 | 405 |
| Mustard–Mung–Aman | min | 2026-11-15 | 2027-02-03 | 2027-03-15 | 2027-05-09 | 2027-07-10 | 2027-12-02 | 382 |
| Mustard–Mung–Aman | max | 2026-11-06 | 2027-01-25 | 2027-03-15 | 2027-05-09 | 2027-07-24 | 2027-12-16 | 405 |
| Wheat–Mung–Aman | min | 2026-11-30 | 2027-03-18 | 2027-03-18 | 2027-05-12 | 2027-07-10 | 2027-12-02 | 367 |
| Wheat–Mung–Aman | max | 2026-11-15 | 2027-03-03 | 2027-03-15 | 2027-05-09 | 2027-07-24 | 2027-12-16 | 396 |

Window-only gaps between harvest and the next planting window:

| Example | P1→P2 | P2→P3 |
|---|---|---|
| Baseline | 0–34 days | 0–40 days |
| Mustard–Mung–Aman | 36–59 days | 49–76 days |
| Wheat–Mung–Aman | 0–22 days | 49–76 days |

These are **window gaps**, not field-ready waiting. Preparation time is unknown
for every crop, so `waiting_range` and `total_interval_range_days` are null.

## What NASA POWER shows

The two rain views use `PRECTOTCORR`; the temperature view uses `T2M`. Coverage is
independent, and units are checked independently: a missing/incompatible `T2M`
unit disables only the temperature view, while a rain-unit failure disables only
the rain views. If one view has no cross-example common period, it is returned
unavailable with null values and a reason, and only that view's control is
disabled; the other view remains valid. Every featured view in this run has
**34 common complete seasons, 1991–2024**. Missing days are excluded, never
zero-filled or joined across a gap.

| View | Baseline | Mustard–Mung–Aman | Wheat–Mung–Aman | Reading |
|---|---|---|---|---|
| Temperature distance | 0.0 °C | 0.0 °C | 0.0 °C | Exact three-way tie; seasonal medians are inside the general EcoCrop optimum. |
| Longest dry spell | 42.83 days | 38.5 days | 40.33 days | Median longest run below 1 mm/day; higher of the two schedules. |
| Heavy-rain frequency | 0.02684 | 0.02365 | 0.02376 | Heavy days (≥20 mm/day) per valid growing day; higher of the two schedules. |

The temperature tie is real. A 0 °C distance only means the seasonal median is
inside the published species-level optimum range; it does **not** establish
absence of heat stress or overall suitability.

The rain values are separate views. The temperature view does not decide the rain
views, and a lower rain value or less heat is not automatically better. **No
overall winner or composite score is produced.** The view value is the higher of
the two completion-optimized schedule values; it is not a worst-case bound.

Per-crop rainfall context below is from the `max_realization` schedule and is
descriptive, not an annual total or irrigation demand:

| Example | Crop | Median rainfall (mm) | IQR (mm) |
|---|---|---|---|
| Baseline | Mustard | 11.02 | 24.20 |
| Baseline | Boro | 315.95 | 175.84 |
| Baseline | T. Aman | 611.19 | 225.43 |
| Mustard–Mung–Aman | Mustard | 11.02 | 24.20 |
| Mustard–Mung–Aman | Mung | 102.89 | 62.87 |
| Mustard–Mung–Aman | T. Aman | 611.19 | 225.43 |
| Wheat–Mung–Aman | Wheat | 21.54 | 30.37 |
| Wheat–Mung–Aman | Mung | 102.89 | 62.87 |
| Wheat–Mung–Aman | T. Aman | 611.19 | 225.43 |

Do not add these crop-period totals into an annual saving or compare unequal
horizons as superiority. No irrigation demand is inferred.

## What changes from the baseline

- **Mustard–Mung–Aman:** Boro is replaced by mung. The family count rises from 2
  to 3 and a legume is present. Completion range is unchanged in this run, but the
  window gaps are longer. The BARC low-water result is from a saline-prone-area
  trial, not Rajshahi.
- **Wheat–Mung–Aman:** Mustard and Boro are replaced by wheat and mung. Initial
  wait becomes 9 days and completion shortens to 367–396 days. The family count
  stays at 2 because wheat and Aman are both Poaceae; a legume is present. This is
  a documented Kushtia sequence explored under Rajshahi weather and reference
  profiles; local applicability is unverified. Related Rajshahi evidence documents
  Wheat–Mung–T. Aus, but is not a validation of this sequence.

Family count and legume presence are context only. They do not promise fertilizer
savings, pest control, soil improvement, or higher income.

## Prerequisites and unknowns

| Item | What the engine shows |
|---|---|
| Soil | Unknown: no local pH, texture, drainage, or salinity measurement. Never an automatic pass. |
| Preparation | Unknown: preparation ranges are null; field-ready waiting is not calculated. |
| Drainage | Unknown: no field drainage or waterlogging evidence. Heavy-rain frequency is meteorological exposure, not flooding. |
| Irrigation | Context only and unranked. Per-crop guidance is visible; no comparable total or dependence score. |
| Economics | Unavailable: no sourced prices, costs, cash-flow schedule, or validated typical yields. |
| Labor/equipment/market | Unavailable or dynamic external; no equipment plan or farm-gate price. |

Specific things to confirm:

- **Baseline:** whether the regional pattern is actually used on this field and
  with which varieties; the engine's reference varieties differ from the survey.
  BARC's trial context reports high water use for this pattern, but the engine does
  not turn that into an irrigation-demand score.
- **Mustard–Mung–Aman:** whether the Khulna mung calendar transfers to this
  Rajshahi field. The crop data marks the exact mung window as
  medium-transferability; the low-water result is not Rajshahi-specific.
- **Wheat–Mung–Aman:** whether the documented Kushtia sequence and its local
  applicability transfer to this Rajshahi field. Related Rajshahi evidence uses
  Wheat–Mung–T. Aus; it is not a validation of this featured sequence.

Every example remains conditional. None is a candidate or a recommendation.

## Sources and limitations

| Source | Exact link | What it supports | Limitation |
|---|---|---|---|
| Rashid et al. (2018), *Cropping Systems and Land Use Pattern in Rajshahi Region* | https://www.banglajol.info/index.php/BRJ/article/view/38209 | Mustard–Boro–T. Aman was the 4th dominant Rajshahi pattern in a 2014–15 survey (21(2):237–254). | Region-level survey; not a field prescription or variety trial. |
| BARC ARMIS research summary 38215 | https://apps.barc.gov.bd/armis/home/research/detail/38215 | Directly documents Wheat–Mung–T. Aman in Kushtia, lists the Khulna pattern, and separately lists Rajshahi Wheat–Mung–T. Aus as related evidence; reports lowest water use for Mustard–Mung–T. Aman and highest for Mustard–Boro–T. Aman in the trial context. | Multi-location 2014–16 water trial; not a Rajshahi-only validation, yield model, or income study. The Kushtia sequence's local applicability here is unverified. |
| BAMIS Rajshahi calendars | https://www.bamis.gov.bd/en/calendar/1/44/2/ ; https://www.bamis.gov.bd/en/calendar/1/75/2/ ; https://www.bamis.gov.bd/en/calendar/1/74/2/ ; https://www.bamis.gov.bd/en/calendar/1/86/2/ ; https://www.bamis.gov.bd/en/calendar/1/9/2/ | Local calendar sources used by the crop dataset for mustard, Boro, Aman, mung, and wheat. | Calendar guidance, not field measurement; mung exact-window transferability is medium. |
| BINA / BWMRI / PLOS / Springer crop references | https://bina.gov.bd/pages/static-pages/6922dc58933eb65569e0fd70 ; https://bwmri.gov.bd/pages/static-pages/6922e0b6933eb65569e28480 ; https://journals.plos.org/climate/article?id=10.1371/journal.pclm.0000180 ; https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0250897 ; https://link.springer.com/article/10.1186/s40068-021-00239-z | Planting-window and variety references cited by the crop dataset. | Reference guidance; study geography and varieties must be checked against this field. |
| FAO EcoCrop mirror | https://github.com/OpenCLIM/ecocrop/blob/main/EcoCrop_DB.csv | Species entries and general temperature ranges used for the match. | A data mirror, not independent agronomic validation. |

Variety limits: the engine evaluates Binasarisha-9, BRRI dhan28, BR11, BARI
Mung-6, and BARI Gom-33. The BARC trial/nearby patterns list different materials
such as BARI Sarisha 14, BINAdhan 7, BARI Gom-28, and BRRI dhan 55/56. The engine's
reference varieties are not the trial's varieties, and none of these sources is a
variety trial for this field.

## Provenance: confirmed and not confirmed

**Confirmed:** the mirror contains the species entries used here: mustard
`Brassica juncea` 548, rice `Oryza sativa` 1574, mung `Vigna radiata` 2150, and
wheat `Triticum aestivum` 2114. The project compares the median daily T2M over the
realized growing period with the published optimum range; distance is 0 inside the
range.

**Not confirmed:** that these species-level ranges are Rajshahi variety- or
stage-specific thresholds; that a 0 °C distance means no heat stress; that the
mirror alone is independent agronomic validation; or that equal crop weighting is
duration-neutral. The seasonal-median match is a disclosed project convention.

## Data and offline behavior

The artifact uses the server's cached NASA POWER daily history:

- product/version: `NASA POWER Daily Point`, `v2.10.3`
- observation period: `1991-01-01..2025-12-31`
- retrieval time in this artifact: `2026-11-12T12:13:00+00:00`
- cache: hit, fresh; no network fetch during generation
- common seasons: 34, `1991..2024`

The cache path is `.cache/power/`. Generation calls `load_server_power` with
`allow_network=False`; an unavailable cache is an error, not a fallback to another
source. The local `2000–2025` POWER CSV used by `scripts/demo_check.py` is a
separate offline fixture and is not used for this comparison. A stale cache would
be marked stale with a warning; missing data would remain unavailable, not zero.

## Reproduce and check

```powershell
python scripts/featured_comparison.py
python -m unittest discover -s tests -q
python scripts/demo_check.py
python scripts/contract_check.py examples/example_response_climate.json
```

The normal unit suite does not need the gitignored NASA cache or network. The
real-cache integration check is explicit and separate:

```powershell
$env:FEATURED_POWER_INTEGRATION = "1"
python -m unittest discover -s tests -p "test_featured_comparison.py" -v
```

The generator measures its own end-to-end time. In the current cache it completed
in about 16 seconds while evaluating two first-crop groups and extracting all three
views.

## Glossary

- **Conditional:** inspectable path with missing field evidence; not a recommendation.
- **Common season:** a historical season with complete daily data for both schedules and every crop in the view.
- **T2M:** NASA POWER daily temperature at 2 m; required in Celsius.
- **PRECTOTCORR:** NASA POWER corrected daily precipitation; required in mm/day.
- **Dry day:** `PRECTOTCORR < 1 mm/day`.
- **Heavy day:** `PRECTOTCORR >= 20 mm/day` (R20mm adaptation).
- **Completion schedule:** a min- or max-realization example optimized for completion, not weather or a worst case.
- **Equal crop weighting:** each crop contributes equally to a branch weather value; a product convention, not duration neutrality.
- **Tie:** examples with exactly the same displayed value; ties are kept, not forced apart.
- **Window gap:** calendar gap to the next planting window; not field-ready waiting when preparation is unknown.

A three-crop sequence is **not** a verified repeatable rotation. Third-to-first
compatibility is not checked. Weather exposure is not overall agricultural
suitability.
