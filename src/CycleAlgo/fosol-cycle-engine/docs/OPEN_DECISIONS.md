# Open decisions and current defaults

These are unresolved evidence/configuration decisions. They are intentionally
visible in responses; none is silently replaced by a favorable value.

| Decision | Current default | Impact on the product |
|---|---|---|
| §6.2 current-season climate exposure | Deferred. `climate` check is `unknown` with `CLIMATE_EXPOSURE_DEFERRED`; `current_season_climate_exposure` is missing. | No climate-driven candidate or rejection. Weather warnings are not current-season evidence. |
| Sourced preparation times | Missing. All crop-CSV `turnaround_days_*` cells are blank; `preparation_range`, `ready_range`, `waiting_range`, and `total_interval_range_days` are null. | Readiness is unknown, never zero. Next planting is window-only; the harvest-to-window gap is not field-ready waiting. |
| Duration reference stage | Unconfirmed. The CSV gives variety duration but not whether it starts at sowing or transplanting. `DURATION_REFERENCE_UNRESOLVED`; timing is conditional. | Timeline remains conditional; nursery age is shown but not added to duration. |
| Local soil/land evidence | Missing. No district BARC/SRDI pH, texture, drainage, or salinity evidence; soil checks are `unknown`. Crop-CSV EcoCrop text is guidance only. | No soil pass; branches remain conditional. SMAP is not used as a substitute. |
| Sourced water/comparability evidence | Missing. Water checks return caution/unknown; irrigation guidance and FAO/phase values are context only, not a comparable dependence measure. | `least_irrigation_dependence` is unranked; no irrigation total or score is calculated. |
| Sourced economics | Missing. No farm-gate prices, production costs, cash-flow schedule, or validated typical yields. All monetary metrics are `unavailable`/null; scenarios empty. | Cost, net-return, and upfront-cash preferences are unranked with `no_winner=true`; reference yields are context only. |
| Warning thresholds | Config-only and all OFF: wheat `T2M_MAX > 30 C` / `T2M_MIN < 15 C`, mustard `PRECTOTCORR > 50 mm/day`. Wheat hidden; the corrected mustard heavy-rain audit is 1/35 and remains held. | No active warning indicators or thresholds. Enabling them requires a sourced stage-specific rule. |
| SMAP outlook | Out of status/ranking and out of E7. If supplied, `environment_context` is context only; if missing/expired, unavailable with a warning. | No moisture threshold, no status change, no forecast. A missing token is not zero moisture. |
| `v1.md` | User work, uncommitted; source of truth for the spec. | Documentation/code changes must not commit or rewrite it; spec and implementation can drift until the user confirms. |

Trusted preparation, soil, and duration-reference evidence can be supplied only by
the server/host through `src.explore.explore` and `create_server`. It is never read
from the HTTP request, and missing fields remain unknown. No questionnaire or
user-supplied verification path exists.

## Iteration-2 climate views

- Temperature is an exploratory EcoCrop optimum-distance proxy, not a stage-specific
  damage or variety-suitability rule. Daily T2M becomes a per-season median; tolerance
  is context only. The actual FAO EcoCrop species entries are recorded; the
  seasonal-median matching convention is project-defined.
- Dry day is `PRECTOTCORR < 1 mm/day`; the metric is the longest consecutive run per
  crop period. Heavy rain is `PRECTOTCORR >= 20 mm/day`; ordering uses heavy days per
  valid growing day. Both are growing-period adaptations of meteorological indices,
  not annual Climdex outputs or crop-damage thresholds.
- `T2M` units must be Celsius and `PRECTOTCORR` units mm/day (documented equivalents
  accepted). Missing/incompatible temperature units do not disable rain views, and
  vice versa.
- Temperature and rain coverage are independent. Only common complete seasons for the
  selected view are compared. Missing rainfall is never zero-filled or joined across
  gaps.
- `min_realization` and `max_realization` are completion-optimized examples. Ordering
  uses the higher exposure of the two, not a worst-case bound.
- Three crop summaries are equally weighted as a disclosed product convention; there
  is no overall weighted climate score.

## Configured (not silently invented)

- Server initial-wait policy: **180 days**, product relevance cutoff, caller/engine
  configurable; engine default remains `None`.
- Transition waiting limit: **None** on the server; no numeric product maximum is
  claimed.
- Historical analysis period: engine default **1991–2025**, configurable. The
  development server uses the POWER API/cache for the stable period
  **1991-01-01..2025-12-31**; cross-year seasons needing 2026 observations are
  excluded. The offline `scripts/demo_check.py` snapshot uses local POWER
  **2000–2025** because 1991–1999 precipitation in the local export is invalid
  (24×); this is not the server path.
- Supported district: **Rajshahi only**; other valid district IDs return
  `unsupported_district` with no fabricated results.
- `lowest_upfront_cash` is rejected until a sourced cash-flow schedule exists.
