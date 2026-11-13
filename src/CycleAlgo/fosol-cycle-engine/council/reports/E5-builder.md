# E5 — Builder: soil/land + water checks (round-1 fixes)

Files: `src/soil_water.py` (`evaluate_soil_fit`, `evaluate_water_fit`,
`evaluate_soil_water`), `tests/test_soil_water.py` (20 tests, budget 15–25, round-1
subTests added to existing methods), `docs/SOIL_WATER.md`.

Round 1 fixes:
- Salinity evidence: numeric, non-negative, `min <= max`, and explicit `unit == "dS/m"`;
  negative/range -> `SOIL_SALINITY_EVIDENCE_INVALID`; missing/wrong unit -> unit codes.
- Strict crop rule `low (<N dS/m)`: `max < N` -> `pass`; `max == N`, `min > N`, and
  straddle -> `caution`.
- pH local evidence: 0–14 and `min <= max`; otherwise `SOIL_PH_EVIDENCE_INVALID` (not
  unsupported). pH crop rule must be 0–14, ordered, and contain the optimum; otherwise
  `SOIL_PH_CROP_RULE_INVALID`.
- Local pH/salinity results need local `source_ids`; otherwise
  `SOIL_EVIDENCE_SOURCE_MISSING`. Crop-rule provenance does not count.
- Negative water demand -> `WATER_DEMAND_EVIDENCE_INVALID`; `0` stays a present
  cautious demand; `None`/empty stays missing.

Defaults unchanged: no local soil file, so real crops remain `unknown`; water demand
present never passes; SMAP moisture is context only; no crop-ID branches; `Data/` untouched.

Command: `python -X utf8 -m unittest discover -s tests -v`
```text
Ran 136 tests in 0.117s

OK
```
