# E9 preflight — envelope, status, demo gate, initial wait

Date: 2026-11-07. Status: **waiting on the maximum initial-wait decision. No E9 code yet.**
E8 accepted: real fastest/slowest ranges; 655..682 for `b_82899e8d6941`.

## Initial wait audit

- `expand_branches(..., max_waiting_days=None)` is the engine default. There is **no
  approved product maximum**.
- The `365` used in the E6/E8 smoke was a **test parameter set by the council**, not a
  sourced product setting or user decision. It must not be presented as science.
- The branch crop-1 calendar carries `waiting_days` (e.g. 246) and
  `waiting_limit_days` (365) inside `checks.calendar.details`. There is no top-level
  branch `initial_wait_days` yet.
- E9 must surface `initial_wait_days` per branch/crop option, include
  `max_initial_wait_days` in `assumptions`/`request`, and show it in ranking entries so
  “fastest completion” cannot hide an 8-month start delay.
- E6 transitions already carry `preparation_range`, `waiting_range`,
  `total_interval_range_days` and `next_planting.timing_basis`. With preparation unknown,
  `waiting_range` is `null` and the next planting is window-only. The H1→P2 gap
  (e.g. 2027-12-16 → 2028-07-10, 206 days) is a **window-only gap**, not field-ready
  waiting. E9 must display it separately and not call it a waiting interval.

## E9 requirements

- `scripts/demo_check.py` must **exist and pass before the first E9 commit**: golden
  Rajshahi scenarios, each first crop/preference/water access, invariants (3 crops/2
  transitions, earliest ≤ latest, no NaN/empty, IDs exist, no blocked branch ranked),
  candidate/conditional state, null serialization, offline/stale-cache behavior.
- Current data status must be **`partial`** (0 candidate / 420 conditional, economics
  unavailable, evidence missing). `ok` is a bug.
- “No candidate branches — 420 conditional branches shown” must be in the response
  (`ranking`/`branch_summary`), not inferred by the frontend.
- Unknown values serialize as `null`; never 0, NaN, or empty string.
- Invalid input → HTTP 400 with the E2 error shape; unexpected internal error → 500
  generic body, no stack trace or credentials.
- E9 envelope: `schema_version`, `generated_at`, `request`, `status`, `district`,
  `assumptions`, `data_sources`, `crop_options`, `branches`, `ranking`, `warnings`;
  status precedence unsupported district → data unavailable → no supported options →
  partial → ok.

## v1.md check

`v1.md` currently ends at the **Core rule** line; no leftover council prompt is present.
It remains uncommitted user work and will not be committed until the user confirms.

## Decision needed

`max_initial_wait_days` for E9/demo: 365 (current smoke), 180, 90, or `None` (future
first crops shown as unknown/unranked). Engine default remains `None`.
