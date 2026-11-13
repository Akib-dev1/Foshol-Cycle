# E7 W2 - statistics + warning flags

Delivered `src/outlook_config.py` and `src/outlook_indicators.py`, plus `tests/test_outlook_indicators.py` (15 tests). No E6/W1 source changed.

Temperature: pooled daily T2M over W1 `evaluated_seasons` (`stats_min_90`); sample = valid days + seasons; median/IQR/min/max; Q1/Q3 use documented linear interpolation. Precipitation: per-season totals from W1 `warnings_100` seasons; sample = seasons; median/IQR/min/max across totals; unit mm. Statuses ok/partial/unavailable; partial records excluded/skipped seasons in notes and coverage; temperature coverage now includes an `excluded_seasons` count.

Warnings: generic `calculate_warning_indicator`; all three config flags default OFF. Enabled thresholds are T2M_MAX > 30.0 C (heat), T2M_MIN < 15.0 C (low-temperature), PRECTOTCORR > 50.0 mm/day (heavy rain); per-indicator text/source text. Numerator counts seasons with at least one day; `days_meeting` counts days. Coverage is `warnings_100`; Y=0 -> unavailable, never zero risk. Disabled returns status `disabled` with no X/Y.

`OUTLOOK_LABEL` is exactly "Seasonal outlook — based on historical conditions, not a weather forecast."; exact-string test. `weather_risk_threshold_text` is the exact §6.2 caution/hard-rejection phrase. No crop-ID branches; generic definitions. Source version/fill/missing counts are not hardcoded; W3 assembly handles metadata.

Tests: 15 synthetic-only outlook tests (15/15 OK); direct incomplete-season tests exercise W2 guards; the `valid_days != days` -> `< days-1` mutation is killed by both precip and warning tests; source SHA restored (`B0DD8A64…FBA94`). No 1990 CSV or raw PRECTOTCORR. Full suite:
`python -X utf8 -m unittest discover -s tests -q` -> `Ran 216 tests in 1.068s`, `OK`.

E6 smoke (`2026-11-06`, max 365): 420 branches, 0 candidate / 420 conditional, 15 exclusions (`WINDOW_GEOGRAPHY_UNKNOWN`), unchanged.

No commits.
