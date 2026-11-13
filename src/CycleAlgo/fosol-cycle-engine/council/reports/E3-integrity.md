# E3 Integrity Audit — POWER + AppEEARS/SMAP environmental loading

- Audit date: 2026-11-06
- Auditor: Integrity Auditor (anti-hallucination)
- Scope: `src/power_api.py`, `src/smap_api.py`, `src/environment_cache.py`,
  `src/environment.py`, `tests/test_environment.py`, `tests/fixtures/*`,
  `docs/ENVIRONMENTAL_DATA.md`, `council/reports/E3-builder.md`,
  `council/reports/E3-builder-round2.md`
- Source of truth: `Q:\CycleAlgo\v1.md` §2 (lines 63–67), §3 (line 91),
  §15 (lines 643–657); NASA POWER OpenAPI/Daily docs and Data FAQ; AppEEARS API
  docs and product metadata; NSIDC SPL4SMGP.008 page and latency FAQ; live
  provider responses.
- Code and tests were **not modified** by this audit. `Data/` and
  `Data/DataNEVERBEUSED/` were not read, listed, or modified.

## Verdict

**Round 3 final verdict: PASS.** Round 2's documentation-only failure is
resolved: the four false coverage/latency cells now carry sourced values, the
usage-limit statements are sourced or explicitly labelled, and no
code/test/secret regression was found. See §10.

### Round 1 verdict (historical)

**PASS, with non-blocking provenance notes.**

Every endpoint, product/version, layer, parameter, unit, fill value,
resolution, and status string used by the implementation is either directly
sourced from official NASA documentation/live metadata or is clearly labelled
as an implementation default. POWER `GWETTOP` is correctly labelled as
MERRA-2 surface soil wetness and is **not** presented as SMAP. The POWER JSON
fixture matches a fresh live API response and the live POWER CSV. The AppEEARS
CSV fixture is byte-identical to the results CSV in both live task bundles.
The live smoke tasks are `done` with the reported parameters. The full suite
passes 73/73, with exactly the 41 E3 tests claimed. No token or credential is
tracked or embedded in code, tests, fixtures, docs, or reports.

The notes in §6 are labeling/robustness issues, not fabricated provider claims.

## Artifacts audited

| Artifact | SHA-256 |
|---|---|
| `src/power_api.py` | `AAE4695157B39033B749C13D07FA60EFCFA07B8226DBCEF058F5AB9DCBBE5782` |
| `src/smap_api.py` | `ADA1AD647075455D2C1D515D7D56443F250A5A57F8DA96CC149D81FF6794C78F` |
| `src/environment_cache.py` | `EF0803A742752326EA7A8524100CF0BADD2FABE6D25A0EEDD5C11C43868BA9CD` |
| `src/environment.py` | `0CB38015007523BFC45D5888F36A859693DAA3DA49BC30A1777C056B2D6F58B4` |
| `tests/test_environment.py` | `892E53656492265A3F9B07D1907514DA2EC8F3AAE4EB2EEC53313EB7605892B1` |
| `docs/ENVIRONMENTAL_DATA.md` | `DE27A2020C267208F531984320DF581E1380ADAF19EE5576FB1CB262E5B51308` |
| `council/reports/E3-builder.md` | `47FB3E0B691CCEA305201E7559509C778450F6654AC3F1317482BB422CDFF912` |
| `Q:\CycleAlgo\v1.md` (working tree) | `1B1C313664A902BE7B942B13F5B287EA21EF1B7FD5F97EF81EF472D1F118875D` |
| `tests/fixtures/power_daily_rajshahi_20250101_20250103.json` | `FAD052B90B0F4DE8C9CFEAA175EBB7564844EF1AF67D7CE56FD27F1911BCC224` |
| `tests/fixtures/appeears_spl4smgp_rajshahi_20250101_20250103.csv` | `3E029434AF96FD07F8B94329BEEC839F9E9F76B62CFAD66CA8F8C83DABAA48B8` |
| `tests/fixtures/power_daily_synthetic_missing.json` | `B95D85C27CBCEA6EB82637731E90FBBBCB05C13A2A5687C41CA2FD4E6DB590F0` |
| `tests/fixtures/appeears_spl4smgp_synthetic_missing.csv` | `5ED38F502723EA6D8BDE7DB287ADEF1399690206607943A4020E1C9E8E72512F` |

## 1. Provenance table

### 1.1 NASA POWER daily point

| Item | Implemented value | Source / evidence | Result |
|---|---|---|---|
| Endpoint | `GET https://power.larc.nasa.gov/api/temporal/daily/point` | POWER OpenAPI `paths./api/temporal/daily/point`; live request succeeded | Exact |
| Query parameters | `start`, `end` (`YYYYMMDD`), `latitude`, `longitude`, `community`, `parameters`, `format=JSON`, `units`, `time-standard` | POWER OpenAPI parameter list; live request succeeded | Exact, optional POWER params omitted |
| Product/API version | `v2.10.3` | OpenAPI `info.version`; `GET /api/temporal/daily/configuration` returns `v2.10.3`; live fixture `header.api.version` is `v2.10.3` | Exact |
| Community | `AG` | OpenAPI examples/configuration; live configuration lists `["RE","SB","AG"]`; live request with `AG` succeeded | Exact. OpenAPI schema enum text lists lowercase `ag`; API accepts `AG` |
| Units | `metric` | OpenAPI default; live response units match | Exact |
| Time standard | `LST` | OpenAPI default; POWER Daily docs say Daily defaults to LST | Exact |
| Product label in results | `NASA POWER Daily Point` | Internal normalized label, not a provider title. Provider response title is `NASA/POWER Source Native Resolution Daily Data` | Clearly labelled internal; not presented as NASA's product name |
| `T2M` | `C`, `Temperature at 2 Meters` | Live fixture/live API `parameters.T2M`; live CSV header | Exact |
| `PRECTOTCORR` | `mm/day`, `Precipitation Corrected` | Live fixture/live API `parameters.PRECTOTCORR`; live CSV header | Exact |
| `GWETTOP` | `1`, `Surface Soil Wetness` | Live fixture/live API `parameters.GWETTOP`; live CSV header | Exact. **MERRA-2 surface soil wetness, not SMAP** (v1.md line 65; docs lines 28–29) |
| Default variables | `T2M`, `PRECTOTCORR`, `GWETTOP` | `src/environment.py` line 34; docs lines 20–26 | Exact |
| Fill value | `-999` | POWER OpenAPI example/header; live fixture `header.fill_value = -999.0`; live CSV header says missing value `-999` | Exact |
| Spatial resolution | `0.5 x 0.625 degree lat/lon region (MERRA-2)` | Live CSV header: `Average for 0.5 x 0.625 degree lat/lon region`; MERRA-2 native grid is 0.5° x 0.625° | Exact. POWER Daily docs also contain generic `0.5 x 0.5` regional wording; the live response is authoritative |
| Temporal resolution | `daily` | Endpoint/OpenAPI title; live response dates are daily | Exact |
| Retry policy | HTTP 429 and all 5xx retried; other 4xx (notably 422) not retried | POWER OpenAPI response codes 422/429/500/503; implementation | Consistent |
| Defaults | 30 s timeout, 3 additional attempts, 1 s backoff | Implementation only | Implementation policy, not a NASA claim |

### 1.2 AppEEARS / SPL4SMGP.008

| Item | Implemented value | Source / evidence | Result |
|---|---|---|---|
| Base API | `https://appeears.earthdatacloud.nasa.gov/api` | AppEEARS API documentation | Exact |
| Token acquisition helper | `POST /login` with Basic Earthdata credentials; not used by runtime loaders | AppEEARS API docs, Login section; `tools/appeears_login.py` | Exact for the helper |
| Task submission | `POST /task` | AppEEARS API docs, Tasks section | Exact |
| Task polling | `GET /task/{task_id}` | AppEEARS API docs | Exact |
| Bundle listing | `GET /bundle/{task_id}` | AppEEARS API docs | Exact |
| File download | `GET /bundle/{task_id}/{file_id}` | AppEEARS API docs | Exact |
| Product | `SPL4SMGP` version `008`; ID `SPL4SMGP.008` | AppEEARS `/api/product` entry: `ProductAndVersion: SPL4SMGP.008`, `Version: 008`; `/api/product/SPL4SMGP.008` layer metadata | Exact |
| Product title | SMAP L4 Global 3-hourly 9 km EASE-Grid Surface and Root Zone Soil Moisture Geophysical Data, Version 8 | NSIDC dataset page `https://nsidc.org/data/spl4smgp/versions/8`; DOI `10.5067/T5RUATAQREF8` | Exact |
| Spatial resolution | 9 km EASE-Grid 2.0 | NSIDC: `Spatial Resolution: 9 km`, `EASE-Grid 2.0`, EPSG:6933; AppEEARS catalog `Resolution: 9000m` | Exact |
| Temporal resolution | 3-hourly | NSIDC: `Temporal Resolution: 3 hour`; real CSV has 8 observations/day at 01:30, 04:30, …, 22:30 UTC | Exact for the data. AppEEARS catalog field says `TemporalGranularity: Daily`; see note 1 |
| Surface layer | `Geophysical_Data_sm_surface` = `Top layer soil moisture (0-5 cm)` | AppEEARS product metadata | Exact |
| Root-zone layer | `Geophysical_Data_sm_rootzone` = `Root zone soil moisture (0-100 cm)` | AppEEARS product metadata | Exact |
| Default layers | Both surface and root-zone layers, always requested | `src/smap_api.py` lines 34–38; docs lines 58–63; tests | Exact |
| Units | `m^3/m^3` for both layers | AppEEARS product metadata | Exact |
| Fill value | `-9999` | AppEEARS product metadata `FillValue: -9999.0`; real CSV/synthetic fixture | Exact |
| Valid range | `0.0` to `0.9` (`0.8999999762`) | AppEEARS product metadata | Consistent; not asserted as a crop threshold |
| QA layer | None selected/returned; no QA flag invented | AppEEARS product metadata: `QualityLayers: ""`, `IsQA: false` for both layers; docs line 70 | Exact |
| Task body | `task_type: "point"`, `MM-DD-YYYY` dates, both product layers, one coordinate with id/lat/lon | AppEEARS API docs; live task `params`; tests | Exact |
| Status strings | Wait on `pending`, `queued`, `processing`; finish on `done`; fail on `error`; HTTP 303 also means done | AppEEARS docs status table lists `pending`, `processing`, `done`, `error`; `queued` is not in the docs table but the builder reports observing it; code also handles it | Documented plus one observed extension; final `done` independently verified |
| Bundle download redirect | Follows the documented 302 to the S3 URL | AppEEARS API docs line 1398 | Consistent |
| Auth lifetime | Token ~48 hours; HTTP 403 on expiry | AppEEARS API docs line 277 | Exact; code also handles 401 defensively |
| Token storage | Gitignored local JSON; default `Q:\CycleAlgo\appeears_token.txt`; `APPEARS_TOKEN_FILE` override | Docs; `tools/appeears_login.py`; `git check-ignore` | Exact |
| Defaults | 60 s request timeout, 900 s task timeout, 10 s poll | Implementation only | Implementation policy, not a NASA claim |

### 1.3 Cache and freshness policy

| Item | Implemented value | Source / evidence | Result |
|---|---|---|---|
| Cache key | SHA-256 over product, product version, lat, lon, start/end, sorted variables, settings | v1.md §15 lines 645–648; implementation/docs | Exact to spec fields |
| POWER settings in key | community, units, time standard | Implementation/docs | Exact |
| SMAP settings in key | empty; product/version/layers already keyed | Implementation/docs | Exact |
| Default TTL | `604800` s / 7 days for both providers | `src/environment.py` lines 36–38; docs lines 130–132; builder lines 148–151 | **Explicitly labelled explorer policy, not a provider SLA** |
| Stale cache | Returned only with `STALE_CACHE` warning and age | v1.md §15 line 653; implementation/docs | Exact |
| No cache/no network | `EnvironmentUnavailable`; dependent checks stay unknown | v1.md §15 lines 653–654; implementation/docs | Exact |
| Partial provider failure | One provider failure yields partial result + `POWER_UNAVAILABLE`/`SMAP_UNAVAILABLE`; both fail raises | v1.md §15 line 657; implementation/docs | Exact |
| Missing values | Fill/null/empty/non-finite become `None`, never `0` | v1.md §15 lines 651–654; implementation/docs/tests | Exact |
| `retrieved_at` vs observation dates | Separate fields; observation dates remain provider dates | v1.md §15 line 648; implementation/docs | Exact |

## 2. Fixture verification

### 2.1 POWER JSON is a real live response

Fresh request on 2026-11-06 to the same documented endpoint with the same
parameters returned:

```text
live_url_path /api/temporal/daily/point
target_values_match True
```

`target_values_match` compares `properties`, `parameters`, `messages`, and
`header.{api,sources,fill_value,time_standard,start,end}` against the fixture.
The volatile `times` field was intentionally excluded. The live POWER CSV
returned the same three observation rows:

```text
YEAR,DOY,T2M,PRECTOTCORR,GWETTOP
2025,1,15.21,0.0,0.7
2025,2,14.87,0.0,0.7
2025,3,15.61,0.0,0.7
```

The CSV header also states `missing ... -999` and `Average for 0.5 x 0.625
degree lat/lon region`. Fixture values and units match the live JSON and CSV.
No observation value was hand-edited.

### 2.2 AppEEARS CSV is the real smoke result

The fixture is 2,311 bytes, 24 data rows, SHA-256
`3E029434AF96FD07F8B94329BEEC839F9E9F76B62CFAD66CA8F8C83DABAA48B8`.
Both live task bundles contain a results CSV with the same size, row count,
and SHA-256:

```text
b9f568a1-d5e8-4600-b2f8-814e1a6f8c35
  results.csv  file_size=2311
  sha256=3e029434af96fd07f8b94329beec839f9e9f76b62cfad66ca8f8c83dabaa48b8
  identical_to_fixture=True

e618d2cd-613d-455a-9c6c-cd3e296fa90e
  results.csv  file_size=2311
  sha256=3e029434af96fd07f8b94329beec839f9e9f76b62cfad66ca8f8c83dabaa48b8
  identical_to_fixture=True
```

The first line is the exact nine-column header reported by the builder; the
last line is `2025-01-03 22:30:00 UTC,...,0.2410727,0.1818904`. The bundle
metadata itself reports the same SHA-256 for the results CSV. This proves the
fixture is byte-identical to the provider's current output, not a hand-edited
sample.

### 2.3 Synthetic fixtures are clearly labelled

- `power_daily_synthetic_missing.json` has an in-file header title:
  `Synthetic POWER-shaped fixture with documented missing sentinels`.
- `appeears_spl4smgp_synthetic_missing.csv` is labelled `synthetic` in its
  filename; the builder report table and tests label it synthetic.
- Tests use these only for `-999`/`-9999`/empty/null handling and never present
  them as observed NASA values.

Non-blocking: the synthetic CSV has no in-file "synthetic" marker; the
filename and report/test labels are the only markers.

## 3. Live smoke verification

Token-use note: the token was used only for read-only `GET /task/{id}` and
`GET /bundle/{id}` / results-file reads for the two named completed tasks. No
task was submitted, deleted, or modified. The token value was not printed.
Task `GET /task/{task_id}` returned HTTP 200 with the following sanitized
payloads:

```text
=== b9f568a1-d5e8-4600-b2f8-814e1a6f8c35 ===
task_name: 'fosol-e3-code-smoke-20261106-0925'
status: 'done'
task_type: 'point'
api_version: 'v1'
created: '2026-11-06T03:33:55.669333'
updated: '2026-11-06T03:42:52.452617'
completed: '2026-11-06T03:42:52.432146'
error: None
params: {"coordinates": [{"id": "rajshahi", "latitude": 24.3767, "longitude": 88.6029}], "dates": [{"endDate": "01-03-2025", "startDate": "01-01-2025"}], "layers": [{"layer": "Geophysical_Data_sm_surface", "product": "SPL4SMGP.008"}, {"layer": "Geophysical_Data_sm_rootzone", "product": "SPL4SMGP.008"}]}

=== e618d2cd-613d-455a-9c6c-cd3e296fa90e ===
task_name: 'fosol-e3-smoke-20261106'
status: 'done'
task_type: 'point'
api_version: 'v1'
created: '2026-11-06T03:13:26.075097'
updated: '2026-11-06T03:15:48.762392'
completed: '2026-11-06T03:15:48.745718'
error: None
params: {"coordinates": [{"id": "rajshahi", "latitude": 24.3767, "longitude": 88.6029}], "dates": [{"endDate": "01-03-2025", "startDate": "01-01-2025"}], "layers": [{"layer": "Geophysical_Data_sm_surface", "product": "SPL4SMGP.008"}, {"layer": "Geophysical_Data_sm_rootzone", "product": "SPL4SMGP.008"}]}
```

The new task `b9f…` bundle contains exactly the files the builder listed:

```text
fosol-e3-code-smoke-20261106-0925-SPL4SMGP-008-results.csv
fosol-e3-code-smoke-20261106-0925-granule-list.txt
fosol-e3-code-smoke-20261106-0925-request.json
fosol-e3-code-smoke-20261106-0925-SPL4SMGP-008-metadata.xml
README.md
```

The earlier task `e618…` has the same five-file shape with the
`fosol-e3-smoke-20261106` prefix. Its results CSV is byte-identical to the
fixture (see §2.2).

The builder's exact transition claim
`pending -> queued -> processing -> done` cannot be replayed after the fact
because the task endpoint exposes only the final state/history summary. The
final state `done`, the timestamps, and all task parameters are independently
confirmed. This is an unverifiable historical detail, not a contradiction.

## 4. Test re-run

Command:

```powershell
python -X utf8 -m unittest discover -s tests -v
```

Fresh output tail:

```text
----------------------------------------------------------------------
Ran 73 tests in 0.063s

OK
```

- Process return code: `0`.
- E3 test methods: **41** (AST count).
- Total tests: **73**.
- The set of 73 test names is exactly the set pasted in
  `council/reports/E3-builder.md`; no missing or extra tests.
- Builder runtime was `0.062 s`; fresh runs were `0.058–0.072 s`. This is
  normal timing variance, not a discrepancy.
- No skips, failures, or errors.

## 5. Secrets and repository state

Token/secret scan:

```text
token_occurrences_in_repo_files 0
paths []
```

`git check-ignore`:

```text
.gitignore:1:/token.txt	token.txt
.gitignore:2:/appeears_token.txt	appeears_token.txt
```

`git ls-files` contains no token, secret, credential, or `.env` path. History
contains no such path either. The test values `test-token-never-real` and
`dummy-token-value` are obvious placeholders, not credentials.

`git status --short` at audit time:

```text
 M fosol-cycle-engine/council/STATE.md
 M v1.md
?? .gitignore
?? fosol-cycle-engine/council/reports/E3-builder.md
?? fosol-cycle-engine/docs/
?? fosol-cycle-engine/src/environment.py
?? fosol-cycle-engine/src/environment_cache.py
?? fosol-cycle-engine/src/power_api.py
?? fosol-cycle-engine/src/smap_api.py
?? fosol-cycle-engine/tests/fixtures/
?? fosol-cycle-engine/tests/test_environment.py
?? fosol-cycle-engine/tools/
```

No token file is staged or tracked. The only files this audit adds are this
report; code, tests, fixtures, and docs were not modified.

Non-blocking: the root `.gitignore` is itself untracked in this working tree.
It must be committed with the E3 work so the token-ignore rule stays in
version control.

## 6. Unsourced, mislabeled, or unverifiable items

1. **AppEEARS catalog temporal label differs from the product.** The official
   AppEEARS `/api/product` entry for `SPL4SMGP.008` says
   `TemporalGranularity: "Daily"`. NSIDC, the product title, and the real CSV
   (8 observations/day) say 3-hourly. The implementation and docs correctly
   use 3-hourly; the AppEEARS catalog field is the outlier. No code change is
   required, but this discrepancy should be kept in mind when citing AppEEARS
   catalog metadata.

2. **`queued` is not in the AppEEARS public status table.** The docs list
   `pending`, `processing`, `done`, and `error`. The builder reports observing
   `queued`, and the code waits on it. The docs label the five statuses as
   "observed", which is accurate. The final `done` state is independently
   verified; the transition sequence is not.

3. **The builder's exact transition sequence is not post-hoc provable.** The
   task API confirms final status, timestamps, and parameters, but not the
   historical `pending -> queued -> processing -> done` sequence.

4. **POWER's public Daily docs contain a generic `0.5 x 0.5` regional-grid
   sentence.** The actual live CSV response and MERRA-2 native grid are
   `0.5 x 0.625`; the implementation uses the live response's wording. This is
   a docs-wording inconsistency, not a code error.

5. **The POWER cache key uses the constant `POWER_PRODUCT_VERSION =
   "v2.10.3"`**, while the normalizer reads the actual version from
   `header.api.version`. If NASA bumps the API/product version, old cache
   entries could be keyed under the old constant. This is a robustness risk,
   not a provenance error.

6. **The 7-day TTL is an explorer policy, not a product-specific freshness
   schedule.** It is explicitly labelled as such in both code and docs. For
   recent/reprocessed SMAP or POWER dates, a 7-day cache can be stale; callers
   can override the TTL.

7. **The builder's "no Data/ access" claim is procedural and cannot be
   independently verified from the repository.** No code, test, doc, or
   report path references `Data/` except the builder's statement itself. The
   audit likewise did not access `Data/` or `DataNEVERBEUSED/`.

8. **Token file permissions are OS-default.** On a multi-user Unix host,
   `tools/appeears_login.py` should ideally write the token file with mode
   `0600`. This is outside the tracked-secret finding; the file is gitignored
   and untracked.

## 7. Sources checked

- NASA POWER OpenAPI:
  `https://power.larc.nasa.gov/api/temporal/daily/openapi.json`
- NASA POWER Daily API docs:
  `https://power.larc.nasa.gov/docs/services/api/temporal/daily/`
- NASA POWER daily configuration:
  `https://power.larc.nasa.gov/api/temporal/daily/configuration`
- NASA POWER Data FAQ (latency):
  `https://power.larc.nasa.gov/docs/faqs/data/`
- Third-party nasapower `get_power` reference (20-parameter note):
  `https://docs.ropensci.org/nasapower/reference/get_power.html`
- NASA Earthdata MERRA-2 project page (0.5° x 0.625° native grid):
  `https://www.earthdata.nasa.gov/data/projects/merra-2`
- AppEEARS API documentation:
  `https://appeears.earthdatacloud.nasa.gov/api/`
- AppEEARS product list:
  `https://appeears.earthdatacloud.nasa.gov/api/product`
- AppEEARS `SPL4SMGP.008` layer metadata:
  `https://appeears.earthdatacloud.nasa.gov/api/product/SPL4SMGP.008`
- NSIDC SPL4SMGP.008 product page:
  `https://nsidc.org/data/spl4smgp/versions/8`
- NSIDC SMAP latency FAQ:
  `https://nsidc.org/data/user-resources/help-center/what-are-latencies-smap-radiometer-data-sets`
- NASA SMAP data products / latency requirements:
  `https://smap.jpl.nasa.gov/data/`
- Live POWER JSON/CSV responses for
  `24.3767, 88.6029`, `2025-01-01`–`2025-01-03`
- Live AppEEARS tasks/bundles `b9f568a1-d5e8-4600-b2f8-814e1a6f8c35` and
  `e618d2cd-613d-455a-9c6c-cd3e296fa90e`

## 8. Round 1 final verdict (historical)

**PASS.** The E3 implementation is provenance-consistent with `v1.md` and the
official NASA sources. The real fixtures are real, the live smoke tasks are
verifiably `done` with the reported parameters, the AppEEARS fixture is
byte-identical to the provider bundle, the full test suite passes 73/73, and
no secret is tracked or embedded. The notes in §6 are non-blocking.

## 9. Round 2 — post-fix re-audit (2026-11-06)

Scope: only the changed/new content: SMAP cache `point_id`, duplicate-timestamp
handling, strict cache JSON, AppEEARS retry logic,
`docs/ENVIRONMENTAL_DATA.md` provider record, the new tests, and
`council/reports/E3-builder-round2.md`. Code and tests were **not modified** by
this audit. `Data/` and `Data/DataNEVERBEUSED/` were not read, listed, or
modified.

### 9.1 Changed artifacts

| Artifact | SHA-256 |
|---|---|
| `src/smap_api.py` | `148AF34E9824A518705F25A329F9B7CA5EA2D5FA063ACE1CBC62540519B3F614` |
| `src/environment_cache.py` | `6E32A48AB2A37DBDEFFA308EE19D4E21F21973D4F667E370CCEA002CFFDB24EF` |
| `src/environment.py` | `CB8427CA500C8EEC6392378C1FECDA72138DC2AB75B277DFE859CDBB84BB05EA` |
| `tests/test_environment.py` | `7E45D65839088F62D5D3B9DB07D6B89854458D925FD162F3E16CF668738CD240` |
| `docs/ENVIRONMENTAL_DATA.md` | `AEF05ED5652CF62EC7BAE7E501F6B5383E2685941AD07527AAC4E7473A6B7B51` |
| `council/reports/E3-builder-round2.md` | `D7EE7633F201F9C861BAC3B2BCD57D84401CB5C5896F8F83A1670CEA54FAE7AF` |

### 9.2 Changed behavior verification

| Change | Implementation evidence | Result |
|---|---|---|
| SMAP cache identity includes `point_id` | `build_cache_key` adds `point_id` (`src/environment_cache.py:16-50`); `load_smap_environment` resolves it once and passes it to the key/fetcher/request (`src/environment.py:234-298`); `load_environment` resolves once and passes the resolved id (`src/environment.py:311-389`). Tests: `test_point_id_is_part_of_the_key`, `test_smap_cache_is_separated_by_point_id`, `test_smap_default_point_id_is_stable_coordinate_string`, `test_submit_defaults_point_id_to_coordinates`. | **Pass.** Two labels at identical coordinates produce separate entries and fetches; the same label reuses the cache. POWER keeps `point_id=null`. |
| Duplicate SMAP timestamps | `parse_appeears_csv` keys rows by ISO timestamp; identical duplicate rows increment `duplicate_timestamps`; conflicting values for the same timestamp raise `AppEEarsResponseError`; `missing_counts` is computed over unique rows (`src/smap_api.py:628-746`). Tests: `test_identical_duplicate_timestamp_is_deduplicated`, `test_conflicting_duplicate_timestamp_is_rejected`, real-CSV `duplicate_timestamps == 0`. | **Pass.** This is a client parsing policy, not an AppEEARS provider claim; the docs correctly present it as client behavior. |
| Strict cache JSON | `EnvironmentCache.get` uses `parse_constant` to reject `NaN`/`Infinity`/`-Infinity` and `parse_float` to reject float overflow; `ValueError` is a cache miss (`src/environment_cache.py:53-89`). Writes still use `allow_nan=False`. Tests: `test_non_finite_json_constants_are_a_miss` and `test_non_finite_cache_is_refetched`. | **Pass.** Corrupt/non-finite entries are refetched, not served. |
| AppEEARS bounded retries | `_retryable_http` retries GET 429/5xx and POST 429/503 only (`src/smap_api.py:218-224`); GET network/timeout failures retry, POST network failures do not; 401/403 remain immediate auth errors (`src/smap_api.py:227-277`). Public functions expose `max_retries`, `backoff_seconds`, and `sleep`. Tests: `SmapRetryTests` (429, 503, GET 500, bounded budget, POST 500 no-retry). | **Pass.** AppEEARS documents 429/500/503; retrying POST 429/503 and not retrying other POST 5xx/network failures is a deliberate client policy. |
| Docs provider record | `docs/ENVIRONMENTAL_DATA.md:107-127` adds the §2 table. Most rows are sourced correctly, but coverage and publication latency contain false "not documented" claims. | **Fail (documentation-only).** See §9.4. |
| New tests / report | `tests/test_environment.py` has 54 E3 test methods: 41 pre-round + 13 new. Full suite: 86 tests. The builder report's 86 test names match the fresh run exactly. | **Pass.** See §9.5. |

### 9.3 New defaults and status strings

| Item | Value | Source / label | Result |
|---|---|---|---|
| `queued` task status | Polled like `pending`/`processing` | AppEEARS docs list `pending`, `processing`, `done`, `error`; `queued` is not in that table. Builder observed it; docs labels it an "observed status extension." | **Pass as labeled observed extension** |
| `DEFAULT_MAX_RETRIES` | `3` additional attempts | Implementation policy; not a NASA/AppEEARS claim. Docs says "bounded" but does not state the numeric default. | **Pass, non-blocking labeling gap** |
| `DEFAULT_BACKOFF_SECONDS` | `1.0` s, exponential | Implementation policy; not a NASA/AppEEARS claim. Docs says "bounded backoff" but does not state the numeric default. | **Pass, non-blocking labeling gap** |
| Default `point_id` | `"<latitude>,<longitude>"` | Implementation identifier convention, not an AppEEARS-assigned id. Docs calls it the "stable default"; it is not presented as a provider id. | **Pass as client convention** |
| `duplicate_timestamps` | Count of identical duplicate rows dropped | Client parsing rule, not an AppEEARS field. Docs describes the rule. | **Pass as client rule** |
| Strict cache JSON | Reject `NaN`/`Infinity`/`-Infinity`/overflow | Client cache policy, not a provider claim. Docs describes it. | **Pass as client policy** |
| POST retry set | 429 and 503 only | Client policy. AppEEARS documents 429/500/503; 503 is described as temporary maintenance. No provider guarantee that a retried POST cannot duplicate a task is claimed. | **Pass as client policy** |

No invented NASA/AppEEARS numeric claim was found in the changed code or
tests. The only provenance failure is the provider-record documentation.

### 9.4 Finding: false coverage and latency claims in the provider record

`docs/ENVIRONMENTAL_DATA.md` lines 120–121 currently say:

```text
| Coverage | Exact temporal coverage is **not documented** in the reviewed sources | Exact temporal coverage is **not documented** in the reviewed sources |
| Publication latency | **Not documented** in the reviewed sources | **Not documented** in the reviewed sources |
```

Official sources document all four cells:

| Cell | Official evidence | Correct value |
|---|---|---|
| POWER coverage | POWER Daily docs: "Daily UTC and LST time standards data are available from 1981/01/01 to Near Real Time (NRT)"; live `/configuration` returns `start: 1981-01-01T00:00:00`, `end: 2026-11-06T00:00:00` | `1981-01-01 to present/NRT` |
| SMAP coverage | NSIDC SPL4SMGP.008 page: "Temporal Coverage: 31 March 2015 to present"; AppEEARS product list: `TemporalExtentStart: 2015-03-31`, `TemporalExtentEnd: Present` | `2015-03-31 to present` |
| POWER latency | POWER Data FAQ: "POWER Data Archive has a latency of 2–3 days for meteorological parameters and 5–7 days for solar parameters" | `2–3 days meteorological; 5–7 days solar` |
| SMAP latency | NSIDC SMAP latency FAQ: SPL4SMGP required `7 days 00:00:00`; actual mean `2 days 15:53:00` | `required 7 days; actual mean 2 d 15:53` |

These are not unknown values. `v1.md` §2 lines 75–83 explicitly requires
coverage and publication latency in the provider record. The hedge "in the
reviewed sources" does not make the row correct for a §2 provider record; if a
source was not reviewed, the honest label is "not reviewed/unknown," not
"not documented." This is a documentation-integrity failure even though the
code and tests are correct.

Required correction (docs only; not applied by this audit): replace the four
cells with the sourced values above, or explicitly mark them
"not reviewed/unknown" with the reason. The rest of the provider-record table
(endpoints, auth, 429/500/503, units, missing values, resolutions, QA) is
consistent with the official sources.

### 9.5 Full-suite re-run

Command:

```powershell
python -X utf8 -m unittest discover -s tests -v
```

Fresh output tail:

```text
----------------------------------------------------------------------
Ran 86 tests in 0.081s

OK
```

- Process return code: `0`.
- `ok_count`: **86**; no skips/failures/errors.
- E3 test methods: **54** (41 pre-round + 13 new).
- The complete set of 86 test names matches the set pasted in
  `council/reports/E3-builder-round2.md`; no missing or extra tests.
- Builder runtime was `0.079 s`; the fresh run was `0.081 s`. Normal timing
  variance.
- No live network calls: the tests inject openers/fetchers; the only URL
  literal in the tests is `https://example.invalid` inside a synthetic
  `HTTPError`. The suite completed offline.

### 9.6 Secrets and repository state

```text
token_occurrences_in_repo_files 0
paths []
```

```text
.gitignore:1:/token.txt	token.txt
.gitignore:2:/appeears_token.txt	appeears_token.txt
```

- No token, secret, credential, or `.env` path is tracked (`git ls-files`).
- No token value occurs in the changed/new code, tests, docs, or reports.
- The token files remain ignored; no token was printed.
- `git status --short` shows only the expected untracked E3 artifacts; no token
  file is staged or tracked.
- Non-blocking: the root `.gitignore` is still untracked in this working tree
  and must be committed with the E3 work.

### 9.7 Round 2 verdict (historical)

**FAIL (documentation-only).**

The round-2 code changes pass: `point_id` cache separation, duplicate-timestamp
handling, strict cache JSON, and AppEEARS retry logic are implemented and
tested; the full suite passes 86/86; no token or secret was added. The
`queued` status is correctly labeled as an observed extension, and the
implementation-defined defaults are not presented as NASA claims.

The provider record fails provenance because four official coverage/latency
values are mislabeled as "not documented." Correct the docs as specified in
§9.4; no code or test change is required. After that correction, the expected
verdict is PASS.

## 10. Round 3 — docs-only re-audit (2026-11-06)

Scope: the corrected `docs/ENVIRONMENTAL_DATA.md` provider record only. Code and
tests were not modified by this audit; their hashes are unchanged from §9.1.
`Data/` and `Data/DataNEVERBEUSED/` were not read, listed, or modified.

### 10.1 Changed artifact

| Artifact | SHA-256 |
|---|---|
| `docs/ENVIRONMENTAL_DATA.md` | `AC0DF9655FCDCEC056AAAF8846A3206DB0ABF823B3E91B71DA4571D220252E0F` |

### 10.2 The four false “not documented” claims are resolved

| Provider record row | Current text | Official source | Result |
|---|---|---|---|
| POWER coverage | `1981-01-01 to present/NRT`; live `/configuration` start/end included | POWER Daily docs: daily UTC/LST data from `1981/01/01` to NRT; live `/configuration` returned `start 1981-01-01T00:00:00`, `end 2026-11-06T00:00:00` | **Resolved** |
| SMAP coverage | `2015-03-31 to present` | NSIDC `SPL4SMGP.008` page: temporal coverage `31 March 2015 to present`; AppEEARS product list: `TemporalExtentStart 2015-03-31`, `TemporalExtentEnd Present` | **Resolved** |
| POWER publication latency | `2–3 days meteorological; 5–7 days solar` | POWER Data FAQ: “POWER Data Archive has a latency of 2–3 days for meteorological parameters and 5–7 days for solar parameters” | **Resolved** |
| SMAP publication latency | Level-4 soil moisture required within `7 days`; explicitly the required product latency, not a measured mean | NASA SMAP data-products page: Level 4 products “within 7 days for soil moisture”; NSIDC latency FAQ: SPL4SMGP required `7 days 00:00:00` | **Resolved** |

The current table no longer contains the Round 2 false claims. The only
remaining “not documented” statement is the AppEEARS numeric request quota,
which this audit also could not find in the AppEEARS API docs; it is correctly
scoped as an unknown.

### 10.3 Usage-limit rows

- POWER `429 Too Many Requests` is sourced to the official POWER API/OpenAPI
  docs; the OpenAPI lists a 429 response. **Pass.**
- The `20`-parameter cap note is explicitly labelled third-party (`nasapower`).
  This is accurate: the nasapower `get_power` reference documents a maximum of
  twenty `pars` for daily/monthly/climatology point requests. **Pass.**
  Non-blocking: the official POWER Daily docs also state a maximum of 20
  parameters for a single point, so the row could cite that official source too;
  the current wording does not claim the cap is third-party-only.
- AppEEARS numeric request quota: no numeric quota was found in the reviewed
  AppEEARS API documentation; “not documented in the reviewed sources” is
  acceptable. **Pass as unknown.**
- Client retry behavior (`429`/`5xx`/network for GET; `429`/`503` for POST;
  401/403 immediate) is explicitly described as client behavior, not a provider
  guarantee. **Pass.**

### 10.4 Every added fact is sourced or labelled

| Added fact | Source / label | Result |
|---|---|---|
| POWER coverage `1981-01-01` / NRT | POWER Daily docs; live `/configuration` | Sourced |
| POWER latency `2–3 d` met / `5–7 d` solar | POWER Data FAQ | Sourced |
| POWER `429` | Official POWER API/OpenAPI docs | Sourced |
| `nasapower` 20-parameter cap | Third-party `nasapower` reference; explicitly labelled third-party | Sourced and labelled |
| SMAP coverage `2015-03-31` to present | NSIDC product page; AppEEARS product metadata | Sourced |
| SMAP required latency `7 days` | NASA SMAP data-products page; NSIDC latency FAQ | Sourced |
| SMAP “required, not measured mean” qualification | The cited SMAP latency requirement is a requirement; no measured mean is claimed | Correctly qualified |
| AppEEARS numeric quota unknown | Not found in reviewed AppEEARS docs | Labelled unknown |

No invented coverage date, latency value, quota, or provider claim was found in
the corrected provider record.

### 10.5 Test re-run

Command:

```powershell
python -X utf8 -m unittest discover -s tests -v
```

Fresh output tail:

```text
----------------------------------------------------------------------
Ran 86 tests in 0.078s

OK
```

- Process return code: `0`.
- `ok_count`: **86**; no skips/failures/errors.
- E3 test methods: **54** (41 pre-Round-2 + 13 Round-2 tests).
- Code/test hashes are unchanged from Round 2; the docs-only correction did
  not alter execution.
- Builder Round 2 reported `0.079 s`; this run was `0.078 s`. Normal timing
  variance.

### 10.6 Secrets

```text
token_occurrences_in_repo_files 0
paths []
```

```text
.gitignore:1:/token.txt	token.txt
.gitignore:2:/appeears_token.txt	appeears_token.txt
```

No token, secret, credential, or `.env` path is tracked. The token files remain
ignored and were not printed. Non-blocking repo-state note: the root
`.gitignore` is still untracked in this working tree and should be committed
with the E3 work.

### 10.7 Round 3 verdict

**PASS.**

The four documentation-integrity failures from Round 2 are corrected with
official sources. The usage-limit rows are either sourced or explicitly
labelled as third-party/unknown, and no invented claim remains. The full suite
passes 86/86, code/tests are unchanged from Round 2, and no token or secret was
added or exposed.

Non-blocking notes only: the official POWER Daily docs also state the
20-parameter cap (the current third-party attribution is accurate but could be
strengthened), and the root `.gitignore` remains untracked. Neither affects the
provenance verdict.
