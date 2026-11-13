# E7 — FINAL spec + integrity audit: seasonal outlook
Scope: `src/seasonal_replay.py`, `src/outlook_config.py`, `src/outlook_indicators.py`, `src/outlook.py`, E7 tests, `docs/ENVIRONMENTAL_DATA.md`, E7-W1/2/3 + mustard reports; `v1.md` §9.1–9.3/§17.11/§14.4/§6.2/§19.

## Part A — rule -> code/test -> verdict
| # | Rule | Code / test | Verdict |
|---|---|---|---|
| 1 | Period 1991–2025 configurable; complete years; `last_complete_data_date`; no hard 2026; 2025→2026 included | `seasonal_replay.py:17-160`; `test_seasonal_replay.py:36-97` | PASS |
| 2 | Stats ≥90% / warnings 100%; missing/None/fill invalid; never favorable | `seasonal_replay.py:202-212`; `test_seasonal_replay.py:153-234`; W2 guards | PASS |
| 3 | Temp stats pooled T2M; sample fields; linear IQR | `outlook_indicators.py:13-82`; `test_outlook_indicators.py:80-150` | PASS |
| 4 | Precip stats per-season totals in mm with 100% days; sample fields | `outlook_indicators.py:85-173`; `test_outlook_indicators.py:152-224` | PASS |
| 5 | Warnings default OFF; wheat hidden; mustard held (audited 1/35) | `outlook_config.py:15-55`; `outlook.py:50-54,96-110`; `test_outlook.py:74-115`; mustard audit | PASS |
| 6 | Per-indicator text; Y=0 unavailable/null, never zero risk; no drought/dry-spell | `outlook_indicators.py:176-285`; `test_outlook_indicators.py:226-388` | PASS |
| 7 | Exact em-dash label; union-span caveat; leap-day notes; status ok/partial/unavailable | `outlook_config.py:5-7`; `outlook.py:175-195`; `seasonal_replay.py:55-59,122-135`; tests | PASS |
| 8 | Indicator `source_ids`; source version/product/provider/fill/missing from environment | `outlook.py:108-173`; `test_outlook.py:200-296` | PASS |
| 9 | Historical-only; no SMAP/soil/water/prep/duration; no current-season exposure | source scan; `outlook.py`/`seasonal_replay.py` imports | PASS |
| 10 | No crop-ID branches | `test_outlook.py:315-318`; `test_seasonal_replay.py:264-267`; `test_outlook_indicators.py:432-436` | PASS |
| 11 | E6 regression smoke | 420 branches / 15 exclusions / 0 candidate / 420 conditional | PASS |
| 12 | Test budget 36 vs 20–30; documented reason | `E7-W3-builder.md:12`; W3 review: documented but thin | PASS (thin) |

## Part B — provenance
- Period 1991–2025 and 90/100 coverage are configurable product defaults, not provider metadata; `last_complete_data_date` is caller-supplied; no hard 2026 cutoff.
- Warning thresholds 30/15/50 are config-only, all flags OFF; the 50 mm mustard audit gives corrected 1/35; wheat hidden; `weather_risk_threshold_text` is the exact §6.2 rule. Enabling any threshold requires a sourced local rule.
- Source version/product/provider/fill/missing come from `environment`; `_SOURCE_ID="nasa_power_daily"` is a fixed implementation label. No SMAP, soil, water, preparation, or duration data; no crop-ID branches.
- Low: E7 contract is documented in reports/tests, not added to `docs/ENVIRONMENTAL_DATA.md` (which remains E3-scoped).

## Part C — verdict
**PASS** for E7 spec/integrity. Full suite **224 OK**; E7 focused **13+15+8=36 OK**; E6 smoke **420/0/420/15** (15 exclusions all `WINDOW_GEOGRAPHY_UNKNOWN`; 3 crops/2 transitions).
Remaining low: budget 36 vs 20–30 (+6) reason thin but tests distinct; warning thresholds unsourced but all OFF; E7 contract absent from ENVIRONMENTAL_DATA.md. No code/test edits.
