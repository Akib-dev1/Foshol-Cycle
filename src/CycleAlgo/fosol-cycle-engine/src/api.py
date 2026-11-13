"""Thin HTTP-facing wrapper for the explore engine (v1.md §14.3/§14.5)."""

from __future__ import annotations

from src.error_contract import build_error_response
from src.request_validation import RequestValidationError


def handle_explore(payload: object, *, explore_fn=None, **kwargs) -> tuple[int, dict]:
    """Map one explore call to ``(status_code, JSON body)``.

    The default engine is imported lazily so this module and its tests do not
    require ``src.explore`` to exist yet. Unexpected failures are deliberately
    replaced with a generic 500 body; exception text, tracebacks, credentials,
    and tokens are never returned.
    """
    try:
        if explore_fn is None:
            from src.explore import explore as explore_fn
        result = explore_fn(payload, **kwargs)
    except RequestValidationError as exc:
        return 400, build_error_response(exc)
    except Exception:
        return 500, _internal_error()
    return 200, result


def _internal_error() -> dict:
    return {
        "schema_version": "1",
        "error": {
            "code": "INTERNAL_ERROR",
            "message": "Internal server error.",
            "field": None,
        },
    }
