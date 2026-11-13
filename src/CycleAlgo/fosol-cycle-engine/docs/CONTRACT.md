# Explore contract (frozen)

Entry point: `src.explore.explore(payload, *, profiles, config=None, environment=None,
smap_context=None, now=None) -> dict`. HTTP wrapper: `src.api.handle_explore(payload, ...)
-> (status_code, body)`; server `POST /api/explore`, `GET /health`.

The iteration-3 file `examples/featured_comparison.json` is a handoff artifact, not
an explore response. Do not validate it with `scripts/contract_check.py`; its
featured fields are checked by `tests/test_featured_comparison.py`, with the real
cache comparison available through the explicit `FEATURED_POWER_INTEGRATION=1`
integration test.

## Request

```json
{
  "district_id": "rajshahi",
  "start_date": "2026-11-06",
  "first_crop_id": null,
  "water_access": "unknown",
  "preference": "fastest_completion",
  "max_initial_wait_days": 180,
  "max_waiting_days": null
}
```

`request` echoes the effective request, including the caller/engine
`max_initial_wait_days` and `max_waiting_days` policy values (null when unset).

`district_id` required stable ID (only `rajshahi` supported). `start_date` required
`YYYY-MM-DD`, between `0002-01-01` and `9990-12-31` inclusive. These technical
limits leave room for the previous calendar year and multi-year three-crop
schedules; they do not describe weather-data coverage. Outside dates return HTTP
400 with field `start_date`. `first_crop_id` null or a crop-profile ID. `water_access` in
`rainfed|irrigation_available|unknown` (default unknown). `preference` in
`fastest_completion|lowest_total_cost|least_irrigation_dependence|highest_net_return|
more_crop_diversity|closest_temperature_match|least_dry_spell_exposure|
least_heavy_rain_exposure` (default fastest_completion; `lowest_upfront_cash` rejected
until cash-flow evidence exists).

## Success envelope

```json
{
  "schema_version": "1",
  "generated_at": "UTC ISO",
  "request": {"district_id": "...", "start_date": "...", "first_crop_id": null,
              "water_access": "...", "preference": "..."},
  "status": "ok|partial|no_supported_options|unsupported_district|data_unavailable",
  "district": {"district_id": "rajshahi", "display_name": "Rajshahi",
               "supported": true, "geographic_scope": "representative point/grid"},
  "assumptions": [{"code": "...", "message": "..."}],
  "data_sources": [{"source_id": "...", "provider": "...", "product": "...",
                    "version": "...", "coverage": "...", "retrieved_at": null}],
  "crop_options": [{"crop_id": "...", "name_en": "...", "name_bn": "...",
                    "reference_variety": "...", "status": "candidate|conditional|unsupported",
                    "initial_wait_days": 0, "shown": true,
                    "checks": {"calendar": {...}, "climate": {...}, "soil": {...},
                               "water": {...}, "rotation": null},
                    "reasons": [], "missing_evidence": [], "source_ids": []}],
  "branches": [{"branch_id": "b_...", "status": "candidate|conditional",
                "initial_wait_days": 0, "crops": [3 nodes], "transitions": [2],
                "metrics": {"completion": {...}, "resources": {...},
                            "economics": {...}, "diversity": {...},
                            "climate": {"status": "ok|partial|unavailable",
                                        "definitions": {...},
                                        "unit_validation": {...},
                                        "views": {...},
                                        "temperature_provenance": {...},
                                        "per_schedule": {...},
                                        "summary": {...}}},
                "outlook": {"status": "ok|partial|unavailable", "label": "...",
                            "indicators": []},
                "reasons": [], "cautions": [], "missing_evidence": [], "source_ids": []}],
  "branch_summary": {"candidate_count": 0, "conditional_count": 0,
                     "no_candidate_branches": true,
                     "message": "No candidate branches - N conditional branches shown"},
  "ranking": {"preference": "...", "metric": "...", "direction": "asc|desc",
              "groups": {"candidate": {"count": 0, "ranked": [], "unranked": []},
                         "conditional": {"count": 0, "ranked": [], "unranked": []}},
              "method": "...", "notes": [], "no_winner": true,
              "climate": {"definitions": {...}, "common_seasons": {...},
                          "common_season_counts": {...}, "top_ties": {...},
                          "equal_crop_weighting": true,
                          "ordering_basis": "...", "no_overall_score": true}},
  "environment_context": {"status": "available|unavailable",
                          "product": "SPL4SMGP.008", "provider": "NASA SMAP via AppEEARS",
                          "resolution": "9 km EASE-Grid 2.0",
                          "temporal_resolution": "3-hourly",
                          "observations": [], "observation_start": null,
                          "observation_end": null, "retrieved_at": null,
                          "label": "Context only - no effect on status or ranking",
                          "warnings": []},
  "missing_evidence": [],
  "warnings": [{"code": "...", "message": "..."}]
}
```

- Date ranges `{"earliest","latest"}`; numeric ranges `{"min","max"}`.
- Unknown quantities `null`; never 0/NaN/empty string.
- `ranking` references branch IDs only; candidate and conditional groups separate.
- `environment_context` never changes status, checks, or ranking.
- Climate preferences rank only common complete seasons; entries expose both
  completion-optimized `min_realization`/`max_realization` values and use the higher
  exposure for ordering (not a worst-case bound). Missing evidence is unranked.
  Climate views have no overall weighted score.
- Errors: HTTP 400 `{"schema_version":"1","error":{"code":"INVALID_REQUEST",
  "message":"...","field":"..."}}`; HTTP 500 generic
  `{"schema_version":"1","error":{"code":"INTERNAL_ERROR",
  "message":"Internal server error.","field":null}}`; no stack/credentials.
