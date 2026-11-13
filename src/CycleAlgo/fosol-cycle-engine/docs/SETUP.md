# Setup

## Clean clone

1. Clone the repository containing `CycleAlgo` (replace the URL with the project
   remote), or copy the folder, then:

   ```powershell
   git clone <repository-url> CycleAlgo
   cd CycleAlgo\fosol-cycle-engine
   ```

2. Check Python:

   ```powershell
   python --version
   ```

   Python **3.11 or newer** is required. The implementation uses only the standard
   library; there is no `pip install` step and no package manifest to install.

3. Confirm the crop CSV exists at the default path:

   ```text
   Q:\CycleAlgo\Data\fosol_cycle_rajshahi_crop_dataset.csv
   ```

   From the engine directory this is `..\Data\fosol_cycle_rajshahi_crop_dataset.csv`.
   The server uses this parent-`Data` directory by default; use `--data-dir` for a
   different read-only location.

## Run checks

```powershell
python -X utf8 -m unittest discover -s tests
python scripts/contract_check.py examples/example_response.json
python scripts/contract_check.py examples/example_error_invalid_input.json --error
python scripts/featured_comparison.py
```

The contract checker must print `PASS` for the bundled examples. Normal unit tests
do not need the gitignored POWER cache or network; the real-cache integration check
is opt-in:

```powershell
$env:FEATURED_POWER_INTEGRATION = "1"
python -m unittest discover -s tests -p "test_featured_comparison.py" -v
```

The featured comparison generator uses only the local POWER API cache with
`allow_network=False`; it writes `examples/featured_comparison.json`. The local
POWER CSV used by `demo_check.py` is a separate offline fixture.

## Start the API

```powershell
python -X utf8 -m src.server --host 127.0.0.1 --port 8000
```

Health and an initial request:

```powershell
curl.exe -s http://127.0.0.1:8000/health
curl.exe -s -X POST http://127.0.0.1:8000/api/explore `
  -H "Content-Type: application/json" `
  --data-binary "@examples/example_request_initial.json"
```

The server loads local crop profiles and one cached NASA POWER API history. It no
longer uses the local environmental CSV. At startup it requests Rajshahi
`24.3767 N / 88.6029 E`, variables `T2M`, `PRECTOTCORR`, and `GWETTOP`, for
the stable complete comparison period **1991-01-01..2025-12-31**. The full history
is cached under the gitignored `<repo>/.cache/power/` and reused; it is not refetched
for each explore request, and the stable date allows an offline restart on a later
day to reuse the same cache. The documented POWER limit is 20 parameters per point
request, so the three-variable request is not split.

A fresh cache is used without a provider call. A failed refresh may return a stale
cache with `STALE_CACHE`; the response’s `data_sources` entry for
`nasa_power_daily` exposes observation dates, retrieval time, and cache metadata.
If no usable cache exists, the outlook is explicitly `unavailable` with
`POWER_UNAVAILABLE`; the server does not fall back to the local CSV. SMAP remains
unavailable in the server and is iteration 2 work.

Server configuration defaults:

- initial-wait policy: 180 days (`max_initial_wait_days`);
- transition waiting limit: `None` (`max_waiting_days`);
- historical analysis: 1991–2025 (POWER API through 2025-12-31; cross-year
  seasons that need 2026 observations are excluded rather than treated as
  complete);
- no credentials required for POWER; SMAP tokens are not loaded.

## Environment variables (names only; never commit values)

| Variable | Used by | Purpose |
|---|---|---|
| `APPEARS_TOKEN_FILE` | `src.smap_api` | Optional path override for the local AppEEARS token file. |
| `EARTHDATA_USERNAME` | `tools/appeears_login.py` | Optional Earthdata username for the interactive token helper. |
| `EARTHDATA_PASSWORD` | `tools/appeears_login.py` | Optional Earthdata password for the helper; prefer the hidden prompt. |

SMAP token helper:

```powershell
python tools/appeears_login.py
```

It writes a gitignored token file (by default `Q:\CycleAlgo\appeears_token.txt`) and
never prints the password. Tokens expire after roughly 48 hours; rerun the helper.
Do not put tokens, passwords, or cookies in examples, docs, or commits.

## Supported district and data limitations

- Only **Rajshahi** is evaluated. `district_id: "dhaka"` is valid input but returns
  `unsupported_district`; it never inherits Rajshahi results.
- No local preparation, district soil, or sourced economic evidence is present.
  Preparation/waiting/readiness are null, soil is unknown, and economics are
  unavailable; see `docs/OPEN_DECISIONS.md`.
- §6.2 current-season climate is deferred; the `climate` check is unknown.
- POWER and SMAP are historical/context data, not forecasts. SMAP is context only
  and never changes status or ranking.
- Warnings are config-only and OFF; wheat hidden, mustard held at the audited 1/35.
- The local 1990 POWER CSV has a documented 24× `PRECTOTCORR` scale issue. The
  development server uses the POWER API/cache; local POWER files remain only for
  offline `scripts/demo_check.py` snapshots. Do not copy raw 1990 precipitation into
  analysis.

## Documentation map

- `docs/CONTRACT.md` — frozen request/response schema.
- `docs/FRONTEND_HANDOFF.md` — UI/field guidance and exact server examples.
- `docs/EXPLAINER.md` — counts, example, unavailable evidence, reviewer questions.
- `docs/OPEN_DECISIONS.md` — unresolved evidence/configuration decisions.
- `docs/ENVIRONMENTAL_DATA.md`, `docs/SOIL_WATER.md`, `docs/TIMELINE.md` — E3/E5/E6.
