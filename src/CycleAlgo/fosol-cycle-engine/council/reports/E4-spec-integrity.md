# E4 Gate — Spec + Integrity
Scope: `src/calendar_evaluator.py`, `tests/test_calendar.py`; spec §5/§6.1/§10.4/§17.1–5. Re-ran `python -X utf8 -m unittest discover -s tests`: 116 tests OK (30 E4 focused).
## Part A — Spec
| Spec rule | Code / test | Verdict |
|---|---|---|
| §5 vocabulary; unknown never passes | `_result` returns exactly pass/caution/unknown/unsupported; contract + missing-source/field tests `src/calendar_evaluator.py:433-468`, `tests/test_calendar.py:569-598`, `:381-397`, `:492-501` | PASS |
| §6.1.1 inside preferred | inclusive `proposed <= end` -> pass/`PREFERRED_WINDOW`; approximate -> caution `src/...:215-240`; Aman boundaries + lentil `tests/...:86-105`, `:307-317` | PASS |
| §6.1.2 late; optional late-bound fix | late only consulted after preferred end; absent/resolved/unresolved/inconsistent `src/...:245-287`, `:300-340`; Boro late + 02-29 bound `tests/...:107-115`, `:183-216` | PASS |
| Prior medium fix: late order/year | requires `late_end > preferred_end` and `< next start`, else `WINDOW_DATA_INCONSISTENT` `src/...:323-330`; 3 invalid cases `tests/...:420-460` | PASS |
| §6.1.3–4 outside/missing/geography; wording | outside -> unsupported, missing/geo -> unknown; reasons say not a proven biological deadline / not a biological impossibility `src/...:49-54`, `:140-151`, `:260-297`; tests `:117-131`, `:318-326`, `:477-501` | PASS |
| §6.1 future window; correct year; no silent distant season | `plant_now=False`, next start + wait; candidates Y-1/Y/Y+1 nearest `src/...:117`, `:172-204`, `:342-380`; tests `:150-181`, `:345-358` | PASS |
| §6.1 + §17.5 cross-year/leap | end year start+1 when crossing; 02-29 absent -> unknown, never distant leap `src/...:300-340`, `:388-407`; Boro/leap `tests/...:133-148`, `:183-243`, `:328-343` | PASS |
| §10.4 (E4 first-crop wait) configurable limit; no numeric default; basis | caller `max_waiting_days=None`; int >=0; unknown/within/exceeds; exclusion says product cutoff `src/...:30-45`, `:172-204`, `:478-485`; tests `:245-267`, `:360-379` | PASS |
| §17.1–4 minimum cases | preferred both boundaries, late conditional, beyond support, no impossibility wording `tests/...:86-131` | PASS |
## Part B — Provenance
| Item | Source |
|---|---|
| `max_waiting_days` default + validation | `None` default; non-negative int only (bool/float/negative rejected) — caller-supplied/implementation-defined; no numeric `max_waiting_days` constant in `src/` (grep) `src/...:33`, `:478-485` |
| Waiting arithmetic, statuses, defaults | `waiting_days = start - proposed`; `waiting_limit_status` not_applicable/unknown/within_limit/exceeds_limit; `plant_now=False`; detail fields default `None` — computed/implementation-defined `src/...:172-204`, `:410-431` |
| Year/leap/tie-break numbers | candidates Y-1,Y,Y+1; nearest-start and future tie-break; 02-29 nominal -> Mar 1; parse probe year 2024; Dec31/Jan1 policy — implementation-defined `src/...:117`, `:342-407`, `:505` |
| Late extension limits | `late_end > end` and `< next_start` — implementation validation of CSV-sourced late value; no invented date `src/...:323-330` |
| Status + code set (21) | statuses pass/caution/unknown/unsupported (§5; lowercase §14.4); late status absent/resolved/unresolved/inconsistent; codes PREFERRED_WINDOW, PREFERRED_WINDOW_APPROXIMATE, LATE_WINDOW, OUTSIDE_SUPPORTED_WINDOW, FUTURE_WINDOW_WAIT_POLICY_UNKNOWN, FUTURE_WINDOW_WITHIN_LIMIT, FUTURE_WINDOW_EXCEEDS_LIMIT, WINDOW_SOURCE_MISSING, WINDOW_START_MISSING, WINDOW_START_INVALID, WINDOW_END_MISSING, WINDOW_END_INVALID, WINDOW_BASIS_MISSING, WINDOW_TYPE_MISSING, WINDOW_CROSS_YEAR_MISSING, WINDOW_DATA_INCONSISTENT, WINDOW_DATE_MISSING, WINDOW_GEOGRAPHY_UNKNOWN, WINDOW_PRECISION_MISSING, WINDOW_LATE_END_INVALID, WINDOW_LATE_END_UNRESOLVED — spec-derived/implementation-defined `src/...` |
| Real window values + metadata | `Data/fosol_cycle_rajshahi_crop_dataset.csv` columns preferred_start/end_mmdd, supported_late_end_mmdd, window_crosses_year, date_precision, planting_window_type, hard_deadline_validated, source_* via loader/caller; MM-DD 2-digit; tokens DAY, NOT_RAJSHI_EXACT, LOCATION_TRANSFERABILITY, TRUE/FALSE; 8/8 profiles, e.g. Aman 07-10..07-24, Boro 12-25..01-10 + 02-28 `src/...:49-151`, `tests/...:86-148`, `:269-326` |
| Test-only numbers / synthetic labels | limits 39/38/0/54/53 explicit caller args; expected waits 39/190/54/24/1/5/353/31 from date arithmetic; synthetic profile labelled crop_id=synthetic, SYNTHETIC_*, synthetic:// `tests/...:45-76`, `:150-267`, `:345-379` |
## Part C — Verdict
- A — PASS: 9/9 spec rows pass; both prior medium fixes and the wording rule verified.
- B — PASS: every default/number/status/limit is sourced or labelled; no hardcoded `max_waiting_days`; window values come from the CSV; synthetic profiles are labelled.
- C — PASS: re-run 30/30 E4 and 116/116 full-suite tests OK; Reviewer round-2 PASS, 5/5 mutations killed.
