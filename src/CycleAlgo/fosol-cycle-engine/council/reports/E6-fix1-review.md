# E6 fix 1 — next-season window roll: code review

**Verdict: PASS.** Roll works at the specified boundaries; no permanent edits; no commits; hashes restored.
Full `python -X utf8 -m unittest discover -s tests -v`: `Ran 177 tests in 0.856s`, `OK` (exit 0).
Focused E6: `test_timeline` 18, `test_rotation` 7, `test_branch_expander` 16 — all `OK` (41 total).

## Fix / rollback
Diff is limited to `_roll_root_window`, `_resolve_window`, `_resolve_future_window`, `_next_season_start`, `_future_calendar`, plus the new test. Forcing `_next_season_start` to return None makes the new test fail (`FAIL: test_next_season_windows_roll_forward_within_limit`, `Ran 16 tests`, `FAILED`); restored SHA-256 `0D3015...940F2` matches backup.

## Boundaries (independent)
Aman root 2026-11-06: 246 d -> included, 2027-07-10..24, `caution`/`FUTURE_WINDOW_WITHIN_LIMIT`, `plant_now=false`, wait 246/246 `within_limit`; 245 -> excluded `FUTURE_WINDOW_EXCEEDS_LIMIT`.
`mustard->mung->boro`: 365 -> present, third 2027-12-25..2028-01-10; 230 -> present; 229 -> absent `FUTURE_WINDOW_EXCEEDS_LIMIT` (230 d). `max_waiting_days=None`: 205 branches, 0 Aman roots, no rolled calendar.
Boundary tests verified: `test_next_season_windows_roll_forward_within_limit` asserts Aman 246 in / 245 out, `mustard->mung->boro` 230 in / 229 out, and `max_waiting_days=None` Aman count 0; all pass.

## Spec check
§6.1: "A future-window crop is not a plant-now option"; "Never advance to a distant future season silently" -> PASS: rolled root/transition is caution, `plant_now=false`, wait exposed.
§10.3: "Earliest next planting = max(earliest ready, window opening)" / latest -> PASS: `calculate_next_planting` still applies max; rolled range is the window.
§10.4: "Apply a configurable maximum waiting interval"; "Every limit must state its basis: ... product relevance limit" -> PASS for the specified boundaries; partial-range guard behavior not re-reviewed (defect 1 only). Low: `_limit_error` says "explorer's maximum waiting gap" but omits E4's explicit "not a biological impossibility" sentence.
§10.5: "Include actual dates and gaps even when the sequence crosses calendar years" -> PASS: 2027-12-25..2028-01-10 path included at 365.

## Smoke (2026-11-06, max 365)
295 -> 420 branches; exclusions 56 -> 15 (all `WINDOW_GEOGRAPHY_UNKNOWN`); Aman roots 0 -> 62; first crops old boro42/lentil55/maize42/mustard54/potato54/wheat48 -> aman62/boro55/lentil62/maize55/mustard62/potato62/wheat62; second counts and boro positions 42/19/25 -> 55/49/54 match. Builder "boro any 86->158" is position occurrences; unique branches containing boro are 81->138 — report wording only.

## Findings
1. Low: `_limit_error` reason omits the explicit product-cutoff/non-biological sentence; no biological claim is made.
2. Low: builder "boro any" mislabels occurrences as unique branches (81->138).
No blocking defect. Demo_check: N/A until E8-E9.
