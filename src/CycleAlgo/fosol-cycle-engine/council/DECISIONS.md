# Decisions

## decided-by: user

- Initial wait: 180 days, product relevance limit (not scientific), configurable,
  engine default stays `None`, boundary tests at 179/180/181.
  Quote: “Initial-wait limit: 180 days, labelled as a product relevance limit (not
  scientific), configurable, engine default stays None, boundary tests at
  179/180/181.”
- Completion range: realized fastest/slowest corners with both dates.
  Quote: “Completion range: realized fastest/slowest corners with dates (already built).”
- Ranking: only within the conditional group; no invented candidate group; economics
  unranked with `no_winner=true`.
  Quote: “Ranking only within the conditional group; no candidate group is invented;
  economics unranked, no_winner=true.”
- Current status: `partial` while evidence is missing, with the explicit state
  “No candidate branches - N conditional branches shown”; `ok` for current data is a bug.
  Quote: “Status is `partial` while evidence is missing, with the explicit state
  ‘No candidate branches - N conditional branches shown’. `ok` for the current data
  would be a bug.”
- Unknown serialization: `null`, never 0/NaN/empty string.
  Quote: “Unknown serializes as null, never 0/NaN/empty string.”
- SMAP: context display only; `environment_context` block; never status/ranking;
  missing/expired fetch is `unavailable` with a warning; no live token in tests.
  Quote: “SMAP: context display only. Add an `environment_context` block … A failed,
  expired or missing fetch is `unavailable` with a warning, never zero. SMAP stays out
  of E7 and out of all status/ranking logic.”
- §6.2 current-season climate: deferred; list in `docs/OPEN_DECISIONS.md` and response
  missing evidence.
  Quote: “Section 6.2 (current-season climate): deferred.”
- E8 economics: unavailable by design; no invented prices/costs; ranking metrics
  unranked. Quote: “economics unranked, no_winner=true.”
- E7 warnings: all OFF; wheat hidden; mustard held. (Earlier user decision, retained.)

## decided-by: agent | safe default

- `max_waiting_days` (between-crop) remains `None` for E9/demo; affects transition
  exclusion only; reverse by passing a configured value.
- SMAP uses the cached live-task fixture (`tests/fixtures/appeears_spl4smgp_...csv`);
  no live token. Reverse by refreshing `tools/appeears_login.py` and fetching live.
- §6.2 omitted from status; `climate` check is `unknown` with reason; reverse by
  implementing a sourced exposure rule.
- Initial request returns `branches: []` per §14.3; `branch_summary` aggregates all
  roots (295) and says available/select a first crop. Reverse by returning all root
  branches in the initial response.
- No-candidate message: “available; select a first crop” when branches are empty,
  “shown” when branches are present. Reverse by changing the message policy.
- Handoff examples trimmed: `example_response.json` 1 branch; 10-branch sample separate
  (`max_branches`). Reverse by regenerating without the cap (42 for Boro).
- E7 demo uses the local POWER B export `Data/NASA_RAJ_DATA_2000_2026.csv` normalized
  per E3; analysis 2000–2025; 1991–1999 excluded because the local precipitation is
  invalid (24×). Reverse by supplying valid 1991–1999 POWER and setting the analysis
  start year back to 1991.
- E7 shows per-season ranges only (T2M mean, PRECIP total, GWETTOP mean); no warning
  thresholds. Reverse by supplying sourced stage-specific thresholds and enabling the
  warning config.
- E7 outlook is `unavailable` when no normalized POWER environment is supplied.
  Reverse by injecting a POWER environment and attaching the outlook.
- SMAP context is omitted/unavailable when no cached context is supplied; reverse by
  supplying the cached fixture or a live normalized SMAP payload.
