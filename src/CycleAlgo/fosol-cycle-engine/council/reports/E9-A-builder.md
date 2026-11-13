# E9 Stream A - explore envelope

Delivered `src/explore.py`, `src/local_power.py`, `tests/test_explore.py` (25 tests), `tests/test_local_power.py` (3 tests), both main example pairs, and regenerated the small-state examples. Request echoes effective limits; assumptions state the 180-day product-relevance limit; ranking entries include `initial_wait_days`.

Seasonal outlook: local POWER 2000-2026 is loaded by `src/local_power.py`; `build_seasonal_ranges` attaches 2000-2025 T2M/PRECTOTCORR/GWETTOP min/median/max, `thresholds_applied=false`, no warnings, and historical-only notes to each crop outlook. Server and demo pass local POWER; SMAP uses the cached real AppEEARS fixture (24 observations, 2025-01-01..03 UTC).

Handoff size: `example_response.json` and `example_response_smap_context.json` use `max_branches=1` and real SMAP context; `example_response_first_crop_selected.json` is the 10-branch sample; a live Boro run returns 42 branches. Singular/plural branch messages are covered.

Climate: every crop option and branch crop node now has `status="unknown"`, `code="CLIMATE_EXPOSURE_DEFERRED"`, `missing_evidence=["current_season_climate_exposure"]`, empty `source_ids`; missing-evidence IDs/docs/questions aligned.

Boundary: synthetic 180-day window gives 179 -> `no_supported_options`/`FUTURE_WINDOW_EXCEEDS_LIMIT`; 180/181 -> conditional branches. Kills the off-by-one and `<` versus `<=` mutations.
Economics: all five monetary values null, scenarios `[]`; contract checker rejects a zeroed unavailable value.

Examples/checker: all `examples/*.json` contract checks PASS; `demo_check.py` PASS with local POWER and cached real SMAP observations. Full suite: `Ran 314 tests in 7.682s`, `OK`.
E6 smoke 365/365: 420 branches, 0 candidate / 420 conditional, 15 exclusions; unchanged.
No existing E6/E7/W1-W5 behavior changed; no Data changes; no commits.
