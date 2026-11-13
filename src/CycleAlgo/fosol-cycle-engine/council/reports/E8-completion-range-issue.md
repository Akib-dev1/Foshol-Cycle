# E8 completion-range caveat — decision A

Status: E8 W1–W5 code and tests PASS; final spec/integrity PASS; **E8 not ticked**
because decision A produces invalid ranges for 57/420 branches.

## Observation

- Real smoke: 420 branches, 0 candidate / 420 conditional, 15 exclusions.
- `rank_branches(..., "fastest_completion")`: **363 ranked / 57 unranked** in the
  conditional group.
- All 57 unranked reasons: `COMPLETION_RANGE_INVALID`.
- Example `b_82899e8d6941`:
  - first planting `2027-07-10..2027-07-24`
  - third harvest `2029-05-09..2029-05-22`
  - A: min = 2029-05-09 − 2027-07-10 = **669 days**
  - A: max = 2029-05-22 − 2027-07-24 = **668 days** → max < min.

## Cause

E6 ranges are not monotonic one-for-one: the latest planting does not always pair
with the latest harvest interval in a way that preserves the same duration. Decision A
pairs earliest–earliest and latest–latest, so it can reverse. W1 correctly returns
unavailable/null rather than swapping or inventing a value; W5 leaves those branches
unranked with the reason visible.

## Options

1. **Keep A, leave 57 unranked (recommended for safety).** No unrelated endpoint
   pairing; fastest still ranks 363/420. The spec allows unranked missing/invalid
   metrics. E8 can pass with this caveat documented.
2. **Widest corner span B:** `[H3.earliest − P1.latest, H3.latest − P1.earliest]`
   (example 655–682). Always valid, conservative, but pairs different realizations;
   label `range_basis="widest_corner_span"`.
3. **Sort A’s two day values:** `[min(669,668), max(...)] = [668,669]`; keep dates
   separate and label `range_basis="endpoint_pairing_sorted"`. Valid range, but
   earliest/latest dates no longer align with min/max days.
4. **Enumerate realizations:** more code; E6 does not currently expose every
   planting/duration/gap combination.

No code changes pending the decision. E8 final audit: `E8-final-spec-integrity.md`.
