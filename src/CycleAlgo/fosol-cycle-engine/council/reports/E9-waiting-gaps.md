# E9 inter-crop waiting gaps (295 branches)

Basis: `expand_branches(profiles, "2026-11-06", max_initial_wait_days=180,
max_waiting_days=None)`, 295 branches. Preparation/readiness is unknown, so these
are **window-only gaps**: `max(0, next_planting.earliest - previous_harvest.latest)`.
They are not field-ready waiting intervals. Raw overlaps below zero were clamped to 0
(raw min -25); a negative wait is not meaningful. No maximum is configured.

| Population | n | min | median | max | >90 d | >180 d |
|---|---:|---:|---:|---:|---:|---:|
| Transition gaps (2 per branch) | 590 | 0 | 206 | 282 | 461 | 340 |
| Branch total gap (2 transitions) | 295 | 0 | 389 | 546 | 282 | 237 |

The example branch H1 2027-12-16 → P2 2028-07-10 is 206 days, the transition median.
No waiting limit was set; this is for the user to decide.
