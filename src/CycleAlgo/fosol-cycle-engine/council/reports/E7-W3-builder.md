# E7 W3 - build_outlook output assembler
Delivered `src/outlook.py` (`build_outlook`) and `tests/test_outlook.py` (8 tests). No E6/W1 math changed.
`build_outlook` calls W1 for T2M (`stats_min_90`), PRECTOTCORR (`warnings_100`), and each enabled warning variable (`warnings_100`), then W2 for statistics and warnings. Output includes the exact em-dash label, crop ID, status, union-span period, coverage rules, season coverage, indicators, missing metadata, one POWER source, and notes. Disabled warnings are omitted entirely.
Status: `ok` = every requested indicator `ok`; `partial` = any partial/unavailable mix or excluded season; `unavailable` = all indicators unavailable. Unavailable warnings now return `numerator=None`, `days_meeting=None`, `denominator=0`, status `unavailable`, text "unavailable, not zero".
Every indicator now carries `source_ids=[sources[0]["source_id"]]` (`nasa_power_daily`); no invented source id. Environment metadata is authoritative: source `version`, `provider`, `product`, `retrieved_at`, `fill_value`, and `failed_requests` come from the payload (`failed_requests` stays null if absent). Fill values are counted as missing and sanitized to `None` before W1/W2. `missing_days` counts invalid values across all mapped seasons and variables used.
Tests cover stats-only default, heat, low-temperature/heavy-rain distinct text, unavailable (None counts), partial, unusual source metadata (`v9.9.9`, fill `-1234`, one missing day), indicator source refs, union-span/leap notes, JSON, and no crop-ID branches. Synthetic observations only; no 1990 CSV.
Full suite: `python -X utf8 -m unittest discover -s tests -v`
```text
Ran 224 tests in 1.109s
OK
```
Focused W3: `Ran 8 tests`, OK. E7 total is 36 tests, 6 above the 20-30 budget; W3 schema/status/source coverage required the extra cases.
E6 smoke (`2026-11-06`, max 365): 420 branches, 0 candidate / 420 conditional, 15 exclusions (`WINDOW_GEOGRAPHY_UNKNOWN`).
No commits.
