# Inter-crop wait sensitivity (initial wait 180)

Basis: `expand_branches(profiles, "2026-11-06", max_initial_wait_days=180,
max_waiting_days=L)`. Counts are for the engine's `max_waiting_days` parameter; no
product limit is set. Prep is unknown, so transition survival is conservative.

| max inter-crop wait | branches | first crops | first-crop IDs |
|---:|---:|---:|---|
| 90 d | 11 | 5 | Boro, Lentil, Mustard, Potato, Wheat |
| 120 d | 20 | 6 | + Maize |
| 180 d | 74 | 6 | + Maize |
| 240 d | 135 | 6 | + Maize |
| None | 295 | 6 | + Maize |

No maximum is configured. The UI may offer a 90/120/180/240 filter; the engine value
is configurable and should be labelled as a product relevance cutoff.
