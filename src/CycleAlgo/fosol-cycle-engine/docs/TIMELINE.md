# Timeline, Preparation, Waiting, and Branches (E6)

Source: `v1.md` §10, §11, §17.6-8, §17.12. Code: `src/timeline.py`,
`src/rotation.py`, `src/branch_expander.py`. Tests: `tests/test_timeline.py`,
`tests/test_rotation.py`, `tests/test_branch_expander.py`.

## Duration stage is an assumption

The crop CSV records variety duration min/max but not whether the clock starts
at sowing or transplanting. `duration_reference_verified` defaults to `False`,
so known durations stay `conditional` / `DURATION_REFERENCE_UNRESOLVED`.
Aman and Boro are transplanted; their `seedling_age_*` values are reported but
never added to variety duration (`NURSERY_AGE_NOT_ADDED`, `nursery_age_added=false`).

Verification is per crop. A host/server may pass
`duration_reference_verified=True` with
`duration_reference_verified_crop_ids`; only those crop IDs receive
`duration.reference_verified=true`. Unknown IDs and IDs supplied without the
verification flag are rejected. The flag is not a request-payload field.

## Preparation is unknown until supplied

All eight `turnaround_days_min/max` cells are blank and
`turnaround_rule_status=VALIDATION_REQUIRED`. The engine never reads those
fields. `preparation` / `preparation_lookup` is the only source:
`{"min_days", "max_days", "source_ids"}`. `None` leaves preparation and
readiness `None` with `PREPARATION_EVIDENCE_MISSING`; it is never zero.
An explicit `0` is a valid immediate-readiness assumption.

## Formulas

```text
harvest earliest = planting earliest + duration_min
harvest latest   = planting latest   + duration_max
ready earliest   = harvest earliest  + prep_min
ready latest     = harvest latest    + prep_max
next earliest    = max(ready earliest, window start)
next latest      = max(ready latest,   window start)
waiting          = next planting - ready
total interval   = next planting - harvest
```

The next range is clipped at the documented supported-late end and the clip is
reported (`NEXT_PLANTING_LATEST_CLIPPED`). When the clip falls below the latest
ready/harvest endpoint, the latest realization is invalid: latest waiting/total
are null and `latest_invalid=true`; the earliest endpoint is kept only when its
own pairing is valid. When preparation is unknown, the next planting range is
the crop window only (`timing_basis=window_only_preparation_unknown`); the
engine does not claim the crop follows on time.

Completion realizations are built as one chain, not by pairing independent first
and third endpoints. Every reported `min_realization` and `max_realization` must
satisfy `planting1 <= harvest1 <= planting2 <= harvest2 <= planting3 <= harvest3`,
stay inside each crop’s planting/harvest and duration ranges, and obey a sourced
preparation minimum when present. If no valid chain exists, completion is
`unavailable` with `COMPLETION_RANGE_INVALID`; the old enumeration fallback is not
allowed to turn that into `ok`.

The iteration-2 climate views use those same `min_realization` and `max_realization`
as two identified example schedules. They optimize completion, not weather. The
ranking uses the higher exposure of the two and labels it as such; it is not a
worst-case bound over every possible schedule.

## Waiting limit is product policy

`max_waiting_days` has no default numeric value. `None` gives
`waiting_limit_status=not_configured`; `within` is inclusive, `partial` means
part of the range exceeds it or the latest waiting is unknown (`max=null`), and
`exceeds` excludes the path. The limit is a product relevance cutoff, not a
sourced agronomic maximum or a claim that longer fallow is unsafe.

## Rotation scope

Consecutive same-family repetition is `caution` / `SAME_FAMILY_REPEAT`; a repeat
at any non-consecutive position (e.g. 1 & 3) is `caution` /
`FAMILY_REPEAT_IN_PATH` with `matched_positions`. A family change is
`pass` / `FAMILY_DIVERSIFIED`. Neither is proof of disease control, soil-carbon
improvement, or nitrogen balance. Legume presence is potential BNF, not a
guaranteed nitrogen credit. The CSV text is advisory (`rule_machine_readable=false`)
and never blocks a branch. Only the two transitions inside the three-crop path
are evaluated: the third-to-first transition is outside v1 scope and is not
claimed as a validated repeatable rotation.

## Branch uniqueness

`expand_branches` adds `uniqueness`: `branch_count`, `branch_ids_unique`,
`duplicate_branch_ids`, `sequence_count`, `duplicate_sequences` (each with
`crop_ids`, `branch_ids`, `window_keys`) and the §14.4 rule. The same crop
sequence with different ordered windows is two branches; duplicate branch IDs
are a hard failure. Duplicate sequences are reported, never collapsed.
