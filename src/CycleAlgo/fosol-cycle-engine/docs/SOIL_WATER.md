# Soil/Land and Water Checks (E5)

Source: `v1.md` §7, §8. Code: `src/soil_water.py`. Tests: `tests/test_soil_water.py`.

## Local evidence reality

`Data/` contains no district-level pH, texture, drainage, or salinity file. All eight
crop profiles are `soil_ranking_readiness=PARTIAL_REQUIRE_LOCAL_BARC_SRDI_CHECK`.
Crop-CSV pH optimum/tolerance, EcoCrop texture/drainage/salinity text, and irrigation
guidance are **crop guidance, not local measurements**. The engine never invents a
district soil value.

## Soil rules (`evaluate_soil_fit`)

| Property | Local evidence | Result |
|---|---|---|
| pH | missing | `unknown` / `SOIL_PH_EVIDENCE_MISSING`, `missing_evidence=["district_soil_ph"]` |
| pH | outside 0–14 or min > max | `unknown` / `SOIL_PH_EVIDENCE_INVALID` |
| pH | local range + complete crop rule | wholly inside optimum `pass`; overlap/outside optimum/outside tolerance `caution`; wholly outside tolerance `unsupported` (bounds inclusive) |
| pH | crop rule missing | `unknown` / `SOIL_PH_CROP_RULE_MISSING` |
| pH | crop rule not 0–14 or tolerance does not contain optimum | `unknown` / `SOIL_PH_CROP_RULE_INVALID` |
| texture/drainage | missing | `unknown` / `*_EVIDENCE_MISSING` |
| texture/drainage | present | `unknown` / `*_MAPPING_UNVALIDATED` (v1 has no validated mapping) |
| salinity | missing | `unknown` / `SOIL_SALINITY_EVIDENCE_MISSING` |
| salinity | negative or min > max | `unknown` / `SOIL_SALINITY_EVIDENCE_INVALID` |
| salinity | unit missing or not `dS/m` | `unknown` / `SOIL_SALINITY_UNIT_MISSING` or `_UNIT_INVALID` |
| salinity | local max < N in crop `<N dS/m` | `pass` |
| salinity | local max == N, min > N, or range straddles N | `caution` (`*_AT_LOW_GUIDANCE`, `*_ABOVE_LOW_GUIDANCE`, `*_PARTIALLY_ABOVE_LOW_GUIDANCE`) |
| salinity | crop text unparsable | `unknown` / `SOIL_SALINITY_RULE_UNVALIDATED` |

Any local-evidence-based pH or salinity result needs at least one local `source_ids`
entry; otherwise it returns `unknown` / `SOIL_EVIDENCE_SOURCE_MISSING`. A crop-rule
source alone is not provenance for a local measurement.

Aggregate precedence: `unsupported` > `caution` > `unknown` > `pass`. Unknown never
becomes a pass.

## Moisture is context only

SMAP/POWER wetness is returned under `moisture_context` with
`used_for_status=false`. `threshold_validated` is true only when the profile's
`surface_wetness_threshold_validated` is explicitly true; every current crop says
`FALSE`. Wet or dry observations cannot change the soil status or declare land ready,
waterlogged, or unsuitable.

## Water rules (`evaluate_water_fit`)

`water_access`: `rainfed` / `irrigation_available` / `unknown` (default `unknown`);
invalid values raise `ValueError`.

| Situation | Result |
|---|---|
| no FAO range and no local phase total | `unknown` / `WATER_DEMAND_EVIDENCE_MISSING`, even with irrigation available (mustard, lentil, mung) |
| negative FAO range or local phase total | `unknown` / `WATER_DEMAND_EVIDENCE_INVALID` |
| demand `0` | still a present, cautious demand |
| demand present, access unknown | `caution` / `IRRIGATION_CONFIRMATION_REQUIRED`; "Irrigation confirmation required." |
| demand present, rainfed | `caution` / `RAINFED_GUIDANCE_REVIEW`; rainfall is not assumed sufficient |
| demand present, irrigation available | `caution` / `IRRIGATION_PARTIAL_CONFIRMATION`; amount, timing, reliability, cost unconfirmed |

Water fit never returns `pass`. The engine never subtracts rainfall from crop demand;
effective rainfall, evapotranspiration, soil storage, and management are not modeled.
`irrigation_demand_calculated` is always `false`, and `environment_used_for_status`
is always `false`.

`evaluate_soil_water` combines both checks with the same precedence.
