# FosholCycle — v2 engine integration

FosholCycle helps users explore three-crop sequences and compare timing, diversity, temperature match, dry spells, and heavy-rain exposure for the Rajshahi pilot. The Bangladesh map still displays clearly labeled sample climate data; it is not a live NASA map. This is an exploration prototype, not a farm prescription.

## Run the local pilot

In PowerShell, use the current CycleAlgo v2 implementation beside the FosholCycle repository and start its server. Use Python 3.11 or newer. Crop profiles come from the bundled crop CSV; production weather comes from NASA POWER API history/cache, not local environmental CSVs. [CycleAlgo connection guide](https://github.com/hosain-ahmed/CycleAlgo/blob/main/fosol-cycle-engine/docs/CONNECT.md)

```powershell
git clone https://github.com/hosain-ahmed/CycleAlgo.git
Set-Location .\CycleAlgo\fosol-cycle-engine
python -X utf8 -m src.server --host 127.0.0.1 --port 8000
```

In a second terminal, go to the FosholCycle repository and start Next.js.

```powershell
curl.exe -fsS http://127.0.0.1:8000/health
npm ci
$env:CYCLE_ALGO_BASE_URL = "http://127.0.0.1:8000"
npm run dev
```

If the sibling engine checkout already exists, check its local changes before updating it; do not clone over it or reset it. The extracted copy's local `v2` branch contains the updated engine. Its first startup may need network access to populate the gitignored POWER cache. Missing weather does not silently switch to a local CSV or fixed demo JSON.

Open [Explore Map](http://localhost:3000/explore), choose Rajshahi, and open Rotation Planner. For the documented scenario, set the start date to **2026-11-06**, keep water access unknown, and choose **Boro rice (BRRI dhan28)**. Select up to three sequences and open their historical conditions. The three-selection limit belongs to the comparison panel; the API returns all supported paths for the scenario, not three fixed examples.

Changing date, water, first crop, or comparison preference requests updated engine results. Temperature/rainfall views use the engine's ranked values, direction, common periods, and unavailable handling, never a second browser scoring algorithm. Legume presence remains descriptive. No overall winner, crop-damage rating, irrigation demand, or profit is inferred.

`CYCLE_ALGO_BASE_URL` is read by the Next.js server and defaults to `http://127.0.0.1:8000`. Update it if you change the Python port. The browser sends requests to the same-origin Next.js Route Handler, so no broad CORS change is needed. The handler requests uncompressed Python responses to avoid a reproduced Node gzip/HTTP-1.0 parser failure; Next.js or the deployment proxy handles browser-facing compression. Allow several seconds for real historical comparisons and keep loading states visible.

Planning inputs accept `0002-01-01` through `9990-12-31` (technical calendar limits, not weather coverage). The engine's JSON `schema_version` remains `"1"` despite the product name v2. Default NASA history is 1991–2025 at a representative Rajshahi point/grid, not a district average. Actual common seasons and cache status are rendered from the response. Full-coverage reference-window ranges are separate context and may differ from common-period realized-schedule comparisons.

## Checks

Run `npm test`, `npm run lint`, and `npm run build` in FosholCycle. Frontend tests use deterministic fixtures and do not need a running engine or network. Run the following from `fosol-cycle-engine` to verify the engine and its bundled contract examples.

```powershell
python -X utf8 -m unittest discover -s tests
python scripts/contract_check.py examples/example_response.json
python scripts/contract_check.py examples/example_error_invalid_input.json --error
```
