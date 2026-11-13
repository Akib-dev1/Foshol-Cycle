# Environmental data — POWER and SMAP

Scope: E3 environmental loading only. These observations are context for
crop checks; they are not a forecast, a yield model, or a field measurement.

## NASA POWER daily point

| Item | Value |
|---|---|
| Provider | NASA POWER |
| Product label in results | `NASA POWER Daily Point` |
| API version | `v2.10.3` (read from `header.api.version`; verified 2026-11-06) |
| Endpoint | `GET https://power.larc.nasa.gov/api/temporal/daily/point` |
| Query | `start`, `end` (`YYYYMMDD`), `latitude`, `longitude`, `community=AG`, comma-separated `parameters`, `format=JSON`, `units=metric`, `time-standard=LST` |
| Response path | `properties.parameter.<NAME>.<YYYYMMDD>`, `parameters.<NAME>.units/longname`, `header.fill_value`, `header.api.version`, `header.sources`, `messages` |
| Temporal resolution | Daily |
| Spatial resolution | `0.5 x 0.625 degree lat/lon region (MERRA-2)` |
| Fill value | `-999` (`header.fill_value`) |

Variables used by default:

| Variable | Units | Meaning |
|---|---|---|
| `T2M` | `C` | Temperature at 2 Meters |
| `PRECTOTCORR` | `mm/day` | Precipitation Corrected |
| `GWETTOP` | `1` | Surface Soil Wetness |

`GWETTOP` is **MERRA-2 surface soil wetness**. It is **not SMAP**, is not root-zone
moisture, and must never be labelled as SMAP.

### Historical exposure views

Iteration 2 uses POWER `T2M` and `PRECTOTCORR` only, over complete seasons of the crop
periods in the two completion-optimized schedules. Temperature and rain coverage are
independent: temperature needs complete `T2M`, dry/heavy views need complete
`PRECTOTCORR`. Units are validated (`C` and `mm/day`, with documented equivalent
labels); missing or incompatible units disable only that view. Temperature is the
per-season median daily T2M compared with the crop profile’s EcoCrop optimum
(tolerance is context only). Dry spell is the longest run of daily
`PRECTOTCORR < 1 mm/day`; heavy rain is days `>=20 mm/day` divided by valid growing
days. These are growing-period adaptations of meteorological indices, not standard
annual Climdex outputs, crop-damage thresholds, or irrigation demand. Temperature
provenance uses the actual FAO EcoCrop species entries; the seasonal-median match is
our project convention. Verified entries: `Oryza sativa` 1574, `Triticum aestivum`
2114, `Brassica juncea` 548, `Lens culinaris` 7209, `Vigna radiata` 2150,
`Zea mays` 2175, `Solanum tuberosum` 1971, from
`https://github.com/OpenCLIM/ecocrop/blob/main/EcoCrop_DB.csv` (FAO EcoCrop
database mirror). These are species/crop-level general ranges, not variety- or
stage-specific thresholds. Rainfall totals and IQR are descriptive. Missing days exclude
a season and are never zero-filled. Equal crop weighting and the
higher-exposure-of-two-schedules rule are product conventions disclosed in the ranking.

### Temperature provenance: exactly what is confirmed

**Confirmed:** the mirror contains the cited species entries and their numbers
(for example mustard `Brassica juncea` 548, rice `Oryza sativa` 1574, mung
`Vigna radiata` 2150, wheat `Triticum aestivum` 2114). The project compares the
median daily T2M over the realized growing period with the published optimum
range; distance is 0 inside the range.

**Not confirmed:** that those species-level ranges are Rajshahi variety- or
stage-specific field meanings; that a 0 °C distance means no heat stress; or that
the mirror alone is independent agronomic validation. The seasonal-median rule is
a project-defined convention, not an EcoCrop field definition. Do not describe a
software check or a mirror match as agricultural validation.

The development server uses this API through `src/environment.py` and the
`.cache/power/` cache, not the local environmental CSV. It requests one history for
Rajshahi (`24.3767/88.6029`, three variables, stable period
1991-01-01..2025-12-31). The stable end date keeps the cache key reusable across
offline restarts. The documented limit is 20 parameters per single-point
submission; no date range split is required for this request. A stale cache is used
only with a `STALE_CACHE` warning, and no usable cache yields an unavailable
outlook, never a local-CSV fallback. Local POWER files remain for offline demo
snapshots.

### POWER failures

- `422`: validation failure, not retried.
- `429` and `5xx`: retried with exponential backoff, bounded by `max_retries`
  (default 3 additional attempts) and a finite per-attempt timeout (default 30 s).
- Network and timeout failures are retried under the same bound.
- Non-JSON, non-object, or structurally invalid responses raise `PowerApiError`.
- Fill values, JSON nulls, and non-finite numbers become `None`; they are never
  converted to `0`.

## NASA SMAP through AppEEARS

| Item | Value |
|---|---|
| Provider | `NASA SMAP via AppEEARS` |
| Product | `SPL4SMGP` version `008` |
| AppEEARS product ID | `SPL4SMGP.008` |
| Base API | `https://appeears.earthdatacloud.nasa.gov/api` |
| Task submission | `POST /task`, body with `task_type: "point"` |
| Task polling | `GET /task/{task_id}` |
| Bundle listing | `GET /bundle/{task_id}` |
| File download | `GET /bundle/{task_id}/{file_id}` |
| Temporal resolution | 3-hourly in the actual returned CSV (the daily catalog metadata is coarse) |
| Spatial resolution | 9 km EASE-Grid 2.0 |
| Units | `m^3/m^3` for both layers |
| Fill value | `-9999`; empty cells are also missing |

Layers:

| Layer | Result key |
|---|---|
| `Geophysical_Data_sm_surface` | `sm_surface` |
| `Geophysical_Data_sm_rootzone` | `sm_rootzone` |

The real results CSV has columns `ID,Latitude,Longitude,Date,SMAP_Tile,...`
and the two product columns named
`SPL4SMGP_008_Geophysical_Data_sm_rootzone` and
`SPL4SMGP_008_Geophysical_Data_sm_surface`. `Date` is
`YYYY-MM-DD HH:MM:SS UTC` and is normalized to ISO UTC timestamps, sorted.
**No separate QA layer was returned for these two layers; none is invented.**

### Credentials and token expiry

- Run `python tools/appeears_login.py` once to write the token file.
- Default path: `Q:\CycleAlgo\appeears_token.txt` (the parent of
  `fosol-cycle-engine`). Override with the `APPEARS_TOKEN_FILE` environment
  variable. The file is gitignored.
- A token is valid for about 48 hours. `load_token` raises
  `AppEEarsAuthError` when the stored `expiration` has passed.
- An HTTP 401/403 produces:
  `AppEEARS token expired or invalid; run tools/appeears_login.py`.
- The token value is never printed, logged, included in an error message, or
  exposed in a response.

### SMAP failures and retries

- GET requests (`task`, `bundle`, file download) retry HTTP 429, HTTP 5xx, and
  network/timeout failures with bounded exponential backoff.
- `POST /task` retries only HTTP 429 and 503, with a fresh bounded retry budget;
  other 5xx responses and network failures are not retried, to avoid submitting
  duplicate tasks on an ambiguous request.
- HTTP 401/403 is never retried and raises the token-refresh error above.
- Identical duplicate rows at the same timestamp are removed and counted in
  `duplicate_timestamps`. If the same timestamp has conflicting values,
  `AppEEarsResponseError` is raised instead of picking one.
- The bundle selection uses the CSV whose file name contains `results`, never a
  statistics or metadata file.

### Task statuses

Observed statuses are `pending`, `queued`, `processing`, `done`, and `error`.
`queued` is an observed status extension and is polled like the other
in-progress statuses. A `303` response also means done. Polling is bounded by
`timeout_seconds` (default 900 s) with an injectable clock and sleep function; an
`error` task or a timeout raises a typed `AppEEarsError`.

## Provider record (§2)

| Item | NASA POWER | NASA SMAP / AppEEARS |
|---|---|---|
| Product + version | `NASA POWER Daily Point`; API version `v2.10.3` from `header.api.version` (verified 2026-11-06) | `SPL4SMGP` version `008` (`SPL4SMGP.008`) |
| Endpoint / access mechanism | `GET https://power.larc.nasa.gov/api/temporal/daily/point` (daily point API) | AppEEARS API at `https://appeears.earthdatacloud.nasa.gov/api`: `POST /task`, `GET /task/{task_id}`, `GET /bundle/{task_id}`, `GET /bundle/{task_id}/{file_id}` |
| Authentication | None | NASA Earthdata Login; AppEEARS token from `POST /login`, valid about 48 h; token file is local and gitignored; **no secrets are stored in git** |
| Usage limits / 429 | HTTP `429 Too Many Requests` (official API docs). A third-party POWER client (`nasapower`) documents a 20-parameter cap for daily point requests; the official OpenAPI used here does not state it, and this engine requests only 3 parameters. Client retries 429/5xx/network with bounded backoff. | Numeric request quota is **not documented** in the reviewed sources. Client retries GET 429/5xx/network and POST `/task` 429/503 with bounded backoff; 401/403 raise the token-refresh error. |
| Variables and units | `T2M` °C; `PRECTOTCORR` mm/day; `GWETTOP` 1 (MERRA-2 surface soil wetness; **not SMAP**) | `sm_surface` and `sm_rootzone`, both `m^3/m^3` |
| Valid ranges | The daily point response does not supply variable valid ranges; **no range filtering is applied** | Depth: `sm_surface` 0–5 cm, `sm_rootzone` 0–100 cm. Valid value range 0–0.9 m^3/m^3; fill `-9999` |
| Missing-value convention | `header.fill_value` (`-999` verified); JSON nulls and non-finite numbers are also missing | `-9999`, empty cells, and non-finite numbers |
| Spatial resolution | `0.5 x 0.625 degree lat/lon region (MERRA-2)` | 9 km EASE-Grid 2.0 |
| Temporal resolution | Daily | 3-hourly in the actual returned CSV; the daily catalog metadata is coarse |
| Coverage | `1981-01-01 to present/NRT` (NASA POWER Daily docs; live `/configuration` returned start `1981-01-01T00:00:00`, end `2026-11-06T00:00:00`) | `2015-03-31 to present` (NSIDC `SPL4SMGP.008` product page) |
| Publication latency | `2–3 days meteorological; 5–7 days solar` (POWER Data FAQ) | Level-4 soil moisture is required within `7 days` (SMAP mission data products); this is the required product latency, not a measured mean |
| Quality flags / limitations | Only `fill_value` and `messages` are exposed by this point response; no separate QA flag is available | No separate QA layer was returned for the selected two layers; none is invented |
| Representative location and association | Rajshahi point 24.3767 N / 88.6029 E, the coordinates from the POWER CSV header; the result represents the POWER grid cell, **not a district average** | Same representative point; the AppEEARS point query represents that 9 km grid cell/point, **not a district average** |

POWER and SMAP do **not** share resolution, temporal step, coverage, or
observation dates. They are normalized and reported separately; no date or grid
is fabricated for a provider that lacks it. `GWETTOP` remains MERRA-2 surface
soil wetness, **not SMAP** (see the POWER section above).

Sources for this record: NASA POWER Daily docs, POWER Data FAQ, the official
POWER API/OpenAPI docs, the third-party `nasapower` client documentation, the
NSIDC `SPL4SMGP.008` product page, and the SMAP mission data-products
documentation.

The AppEEARS daily catalog metadata is coarse; the actual point-results CSV
returned in the smoke test is 3-hourly. `queued` is an observed task-status
extension, not a new terminal state.

## Normalized shapes

POWER (`normalize_power_response`):

```text
product, product_version, provider, variables{units,longname},
observations{ISO date: {variable: value|null}}, observation_start,
observation_end, fill_value, messages, spatial_resolution,
temporal_resolution, retrieved_at
```

SMAP (`parse_appeears_csv`):

```text
product, product_version, provider, variables{units,layer},
observations[{timestamp, sm_surface, sm_rootzone}], observation_start,
observation_end, point{id,latitude,longitude}, missing_counts,
duplicate_timestamps, fill_value, spatial_resolution, temporal_resolution,
retrieved_at
```

`retrieved_at` is when this process obtained the data. Observation dates are
the provider's observation period; the two must not be conflated.

## Cache policy

`EnvironmentCache` is a directory of JSON files with SHA-256 names. Writes are
atomic (temporary file + `os.replace`); a corrupt cache entry is treated as a
miss. Keys are canonical SHA-256 over:

```text
product, product_version, latitude, longitude, start_date, end_date,
sorted variables, settings, point_id
```

POWER settings are `community`, `units`, and `time_standard`; its `point_id` is
`null`. SMAP settings are empty because the product and layers are already in
the key; its `point_id` is the resolved AppEEARS coordinate id. When a caller
does not supply one, the stable default is `"<latitude>,<longitude>"`. Two point
labels at the same coordinates therefore do not share a cache entry.

Cache JSON is parsed strictly: `NaN`, `Infinity`, `-Infinity`, and float
overflow are rejected, and the entry is treated as a miss and refetched.

Default freshness TTL: **7 days** for both providers. This is an explorer
policy chosen to avoid refetching stable history, **not** a provider SLA or a
publication-latency claim. Callers may override it.

Loader behavior:

1. Fresh cache: return it and make no network request.
2. No fresh cache: fetch, validate/normalize, store, return.
3. Provider failure with a stale cache: return the stale record with a
   `STALE_CACHE` warning containing `cache_age_seconds`.
4. Provider failure with no usable cache: raise `EnvironmentUnavailable`.
5. `allow_network=False`: consult cache only; fresh returns silently, stale
   returns with `STALE_CACHE`, no cache raises.

`load_environment` combines both providers. If one fails, the result is partial
with `POWER_UNAVAILABLE` or `SMAP_UNAVAILABLE`; if both fail, it raises. Results
contain `request`, `sources` (`power` and `smap`), and `warnings`.

## Limitations

- POWER values are reanalysis/assimilation products at the stated grid
  resolution, not measurements at the user's field.
- SMAP values are 9 km gridded moisture values, not a district average and not
  a field measurement. Do not describe a point query as an area average.
- POWER and SMAP have different resolutions, temporal steps, latencies, and
  coverage. Do not imply their dates or grids are identical.
- Missing values remain `None`. A failed or missing observation must make the
  dependent check unknown; it must not become zero, a pass, or a favourable
  result.
- These data support historical and recent-context checks. They are **not a
  weather forecast** and cannot predict future moisture after a chosen crop.
- No crop-specific moisture threshold is validated here. Do not declare land
  ready, waterlogged, or unsuitable from an unvalidated SMAP threshold.
- No QA flag is available from the selected AppEEARS layers; do not invent one.

## Local CSV caveat

`Data/POWER_Point_Daily_19900101_20261023_024d38N_088d60E_LST.csv` contains
`PRECTOTCORR` values **24×** the live POWER API and the 2000–2026 local file.
`T2M`, `T2M_MAX`, `T2M_MIN`, `QV2M`, and `GWETTOP` match. The 1991–1999 rows exist
only in that file; if they are used for local analysis, divide `PRECTOTCORR` by 24
and record the correction. Production E7 uses the POWER API, which matches the
2000–2026 file. Do not use the 1990 file's `PRECTOTCORR` raw. See
`council/reports/E7-mustard-audit.md` for the live-API comparison.
