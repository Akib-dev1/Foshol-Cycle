# E10 Stream C - thin HTTP wrapper
Delivered `src/api.py`, `src/server.py`, `tests/test_api.py` (11 tests). No Data/live provider changes.
`handle_explore(payload, *, explore_fn=None, **kwargs)` lazily imports `src.explore.explore`; RequestValidationError -> 400 error envelope, unexpected exception -> exact generic 500 (`INTERNAL_ERROR`, no stack/token/exception text), success -> 200 unchanged.
`src/server.py` uses `ThreadingHTTPServer`: `POST /api/explore` (JSON, 64 KiB max, content-type), `GET /health`, `OPTIONS` preflight, 404 otherwise. CORS allows only `http://localhost:<actual-port>` and `http://127.0.0.1:<actual-port>`; no wildcard. It loads the local crop CSV and passes profiles plus default config `max_initial_wait_days=180`, `max_waiting_days=None`, `start_year=1991`, `end_year=2025`; no SMAP/POWER calls. Start with `python -m src.server --port 8000`; `--host`/`--data-dir` are configurable.
Tests cover 400, generic 500/no secrets, 200 fake engine, health, allowed/rejected CORS, 404, malformed JSON, invalid payload, content-type, body-size, and a real port-0 request/health check.
Full suite: `python -X utf8 -m unittest discover -s tests -v`
```text
Ran 286 tests in 6.770s
OK
```
E6/E9 smoke explicit 365/365: 420 branches, 0 candidate / 420 conditional, 15 exclusions.
No commits.
