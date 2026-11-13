# Testing Policy (amendment 2026-11-06)

Applies to every layer E1–E11 from now on. The goal is demo safety, not test count.

## 1. Every test justifies itself
One-line docstring: `Spec §X | Bug it catches: <specific bug>`.
If no other test catches that bug, do not write the test.

## 2. Always test
- Boundaries: just before / exactly / just after every limit.
- One normal case per spec rule.
- Missing/unknown in every distinct form: key absent, null, empty, -999, NaN, wrong type.
- One failure/invalid case per rule.
- Date edges: cross-year, leap day, year rollover during a duration.
- Spec safety rules: unknown never pass; missing economics never wins; blocked never revived;
  unsupported district never inherits Rajshahi; failed API never favorable; 3 crops / 2 transitions.
- Determinism: same request twice -> identical IDs, ranking, tie-breaks.

## 3. Vary only when the code path differs
Different missing shapes, date contexts, structurally different profiles (3–4 representative,
not all 8), enum branches, range vs single date.

## 4. Do not repeat
Same equivalence class; same crop logic per crop; same rule at a higher layer (test it at the
lowest owner); stdlib/field-existence/getters; line-by-line mirrors; near-identical cases
(collapse into one `subTest` table).

## 5. Budget per layer (exceeding needs a one-line reason in the report)
E1 8–12 · E2 12–18 · E3 12–20 · E4 40–60 · E5 15–25 · E6 35–50 · E7 20–30 ·
E8 25–40 · E9 12–20 · E10 8–12 · E11 8–12 · demo/E2E 10–15.

## 6. Break-it-on-purpose (replaces more tests)
At each milestone the Reviewer mutates 5 critical lines (boundary comparison, `<` vs `<=`,
missing default, status mapping, unit conversion), runs the suite, and confirms each mutation
fails at least one test. Restore the file and verify the hash/git diff afterward. A surviving
mutation gets ONE targeted test. Report a table: mutation | failing test.

## 7. Demo safety suite (E8–E9, rerun at every later milestone)
Golden Rajshahi scenarios (demo date, each first crop, each preference, each water access),
offline fixtures, invariant sweep (exactly 3 crops/2 transitions, earliest ≤ latest, no NaN/
negative durations, no blocked branch ranked, referenced IDs exist, valid JSON, no secrets),
and `python scripts/demo_check.py` printing PASS/FAIL. Offline/stale-cache run must return
`partial` or `data_unavailable` with warnings, never a crash and never a pass.

## 8. Gate
Per function: Builder code+tests -> Reviewer runs tests and checks the cited spec section;
PASS commits locally; FAIL = one fix + one recheck.
Per milestone: full suite + demo_check (when it exists); mutation check; Spec+Integrity table
(rule -> code, every default/number/endpoint sourced); Reviewer bug/edge pass; max 2 fix rounds;
Governor ticks CHECKLIST, updates STATE, commits/pushes to the council branch (never main,
never force-push), and reports in ≤6 lines: layer, test count, mutations, demo_check, commit, warnings.
All reports < 30 lines with real command output.
