# Connect the frontend to Fosol-Cycle

Short version: the frontend talks to the engine over HTTP. **Do not import Python
code** from `src/` into the browser app. Call `POST /api/explore` and `GET /health`.

## Interactive request model

`POST /api/explore` is the interactive data source:

- `first_crop_id: null` returns crop options and the summary; `branches` is `[]`.
- Selecting a first crop returns that crop's generated three-crop paths.
- Changing `start_date`, `water_access`, or `preference` requires a new API request;
  the frontend must not change those in a saved response locally.
- Second/third crop selections can filter or group the returned paths. They are not
  separate API inputs today.
- Every returned path contains exactly three crops. There is no three-path total
  limit; the response is governed by the engine's normal branch count and any
  `max_branches` setting.
- `examples/featured_comparison.json` is optional fixed-scenario demonstration
  content. It does not recalculate with interactive controls and must not be used
  in place of `/api/explore`.

## 1. What to use

- Base URL: `http://127.0.0.1:8000`
- `POST /api/explore` — request JSON in, response JSON out.
- `GET /health` — readiness check.
- Planning dates must be between `0002-01-01` and `9990-12-31` inclusive;
  outside dates return HTTP 400 rather than overflowing calendar calculations.
- Large responses use gzip when the client accepts it. Browsers negotiate and
  decompress this automatically; the JSON fields are unchanged. Clients without
  gzip support still receive uncompressed JSON. Keep compression enabled through
  your deployment proxy; responses include `Vary: Accept-Encoding`.
- Default host/port: `127.0.0.1:8000`. Change with
  `--host` and `--port` when starting `src.server`; use the same host/port in the
  frontend base URL.
- CORS: the server allows **only** `http://localhost:<api-port>` and
  `http://127.0.0.1:<api-port>` (the port the API is running on). A separate frontend
  dev-server origin (for example `http://localhost:5173` while the API is on `8000`)
  is rejected with HTTP 403. Use a same-origin dev proxy (`/api` -> `127.0.0.1:8000`)
  or ask the engine owner to add the frontend origin to the allowlist. Do not edit the
  engine source yourself.

## 2. Which file is the engine

Entry point: `src/explore.py`, function
`explore(payload, *, profiles, config=None, environment=None, smap_context=None,
soil_evidence=None, preparation_lookup=None, duration_reference_verified=False,
duration_reference_verified_crop_ids=None, now=None)`. It returns the response dict;
it does not need the HTTP server. The evidence arguments are trusted host/server
inputs, never JSON request fields.

HTTP server: `src/server.py`; run `python -m src.server`.

| Role | Real path |
|---|---|
| Engine entry / envelope | `src/explore.py` |
| HTTP server / CORS | `src/server.py` |
| Crop profile loader | `src/crop_profiles.py` |
| Calendar evaluator | `src/calendar_evaluator.py` |
| Timeline / 3-crop expansion | `src/timeline.py`, `src/branch_expander.py` |
| Metrics / ranking | `src/branch_metrics.py` |
| Seasonal outlook (E7) | `src/outlook.py`, `src/outlook_indicators.py`, `src/seasonal_replay.py` |
| POWER API / cache loader | `src/power_api.py`, `src/environment.py`, `src/environment_cache.py` |
| Local POWER snapshot (offline checks only) | `src/local_power.py` |
| SMAP / AppEEARS | `src/smap_api.py` |
| Config / labels | `src/outlook_config.py`, `src/server.py` (`DEFAULT_CONFIG`) |
| Tests | `tests/` |
| Demo safety check | `scripts/demo_check.py` |
| Contract checker | `scripts/contract_check.py` |
| Examples | `examples/` |
| Docs | `docs/` |

## 3. Which Python

Tested with **Python 3.13.2**. Minimum: **Python 3.11**. Standard library only — no
`pip install` and no `requirements.txt`.

Check:

```text
python --version
```

- Windows: use `python` (or `py -3.11`).
- Linux/macOS: use `python3`.

Create/activate a venv (optional but recommended):

```bash
# Linux/macOS
python3 -m venv .venv
source .venv/bin/activate
```

```powershell
# Windows PowerShell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Run everything below from the `fosol-cycle-engine` directory.

## 4. Start the server

```powershell
python -X utf8 -m src.server --host 127.0.0.1 --port 8000
```

Ready when the terminal prints:

```text
Listening on http://127.0.0.1:8000
```

Health check (second terminal):

```powershell
curl.exe -s http://127.0.0.1:8000/health
```

Expected:

```json
{"status": "ok"}
```

Stop with `Ctrl+C`.

Run from any other directory (PowerShell):

```powershell
$env:PYTHONPATH = "C:\path\to\repo\fosol-cycle-engine"
python -m src.server --data-dir "C:\path\to\repo\Data" --host 127.0.0.1 --port 8000
```

The same works on Linux/macOS with `export PYTHONPATH=...`. `--data-dir` is optional
when the default sibling `Data/` exists; `PYTHONPATH` is required outside the engine
directory.

## 5. First request

Initial options (no first crop selected):

```powershell
curl.exe -s -X POST http://127.0.0.1:8000/api/explore `
  -H "Content-Type: application/json" `
  --data-binary "@examples/example_request_initial.json"
```

Matching saved response: `examples/example_response_initial.json`.
The initial response has `branches: []` and a summary of **0 candidate / 295
conditional / 56 exclusions** at the default 180-day initial wait.

First-crop-selected example:

```powershell
curl.exe -s -X POST http://127.0.0.1:8000/api/explore `
  -H "Content-Type: application/json" `
  --data-binary "@examples/example_request_first_crop_selected.json"
```

Matching saved response: `examples/example_response_first_crop_selected.json`.

Historical climate view:

```powershell
curl.exe -s -X POST http://127.0.0.1:8000/api/explore `
  -H "Content-Type: application/json" `
  --data-binary "@examples/example_request_climate.json"
```

Matching saved response: `examples/example_response_climate.json`. Climate preferences
are `closest_temperature_match`, `least_dry_spell_exposure`, and
`least_heavy_rain_exposure`; they use only common complete POWER seasons and keep
candidate/conditional groups separate.

Browser `fetch()` equivalent:

```js
const payload = {
  district_id: "rajshahi",
  start_date: "2026-11-06",
  first_crop_id: null,
  water_access: "unknown",
  preference: "fastest_completion"
};
const res = await fetch("http://127.0.0.1:8000/api/explore", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify(payload)
});
const data = await res.json();
```

Saved examples are **trimmed for handoff size** (`config.max_branches`): the main
`example_response.json` has 1 branch, the first-crop-selected sample has 10, and the
climate example has 5. A live Boro request returns **42** branches because the server
default does not cap `max_branches`. Compare status, counts, field shapes and contract
checks; do not expect byte-identical branch arrays.

A branch is a single three-crop sequence, not a verified repeating rotation.
Repeated cycles require separate evidence.

## 6. Where the data lives

`Data/` must be a sibling of `fosol-cycle-engine/`, i.e. at the repository root:

```text
<repo>/Data/
<repo>/fosol-cycle-engine/
```

The server reads:

| File / resource | Used by | Tracked? |
|---|---|---|
| `Data/fosol_cycle_rajshahi_crop_dataset.csv` | crop profiles | yes |
| NASA POWER daily point API | server environmental history | no (external) |
| `<repo>/.cache/power/*.json` | normalized POWER history cache | no (gitignored) |
| `fosol-cycle-engine/tests/fixtures/appeears_spl4smgp_rajshahi_20250101_20250103.csv` | cached SMAP in examples/demo_check | yes |

`Data/DataNEVERBEUSED/` is **never read**. Local `Data/NASA_RAJ_DATA_2000_2026.csv`
remains for offline demo snapshots; the development server does not use it.

At startup the server loads one POWER history (Rajshahi `24.3767/88.6029`,
`T2M,PRECTOTCORR,GWETTOP`, stable period 1991-01-01..2025-12-31) and reuses it
for every explore request. The stable end date lets an offline restart on a later
day reuse the same cache. A fresh cache avoids network calls. A failed refresh may
use a stale cache with `STALE_CACHE`; `data_sources` exposes observation dates,
retrieval time, and cache metadata. With no usable data, the outlook is explicitly
`unavailable` with `POWER_UNAVAILABLE`; there is no local-CSV fallback. The server’s
SMAP context remains `unavailable` with a warning (iteration 2).

If the crop CSV is missing, the server exits during startup with a Python traceback
naming the missing file. A POWER provider/cache failure does not exit; it returns an
explicit unavailable outlook. The cached SMAP sample is used only by
examples/demo_check as dated context, never as current conditions or a ranking input.

## 7. Do not touch

Do not edit or delete:

- `tools/appeears_login.py` and any token file (`token.txt`, `appeears_token.txt`);
- `Data/` (read-only; never `Data/DataNEVERBEUSED/`);
- `council/`;
- `tests/fixtures/`;
- engine source under `src/`.

Report bugs/change requests to the engine owner. Do not put tokens, passwords, or
cookies in the frontend, examples, docs, or commits.

## 8. Troubleshooting

1. **Port already in use** — `OSError: [WinError 10048]` / “Address already in use”.
   Start on another port (`--port 8001`) and update the frontend base URL and health
   URL.
2. **CORS error in the browser** — the API allowlist only contains API-port origins.
   Use a same-origin dev proxy (`/api` -> `http://127.0.0.1:8000`) or ask the engine
   owner to add the frontend origin. A 403 on `OPTIONS` is this allowlist.
3. **Wrong Python version** — `python --version` must be 3.11+. Use `python3` on
   Linux/macOS, `py -3.11` on Windows if `python` points elsewhere.
4. **Missing Data folder** — server traceback `FileNotFoundError` before “Listening”.
   Put `Data/` beside `fosol-cycle-engine/` or pass `--data-dir`.
5. **Server unreachable from the frontend dev server** — confirm the API is running,
   use the exact host/port, and check firewall/`localhost` vs `127.0.0.1`. If the
   browser blocks the response, it is the CORS allowlist in item 2, not a route 404.
