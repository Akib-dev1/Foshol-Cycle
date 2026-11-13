"""Build the §14.3 error response for request-validation failures."""

from __future__ import annotations


def build_error_response(exc: Exception) -> dict:
    """Return exactly the documented error envelope for ``exc``."""
    return {
        "schema_version": "1",
        "error": {
            "code": exc.code,
            "message": exc.message,
            "field": exc.field,
        },
    }


def http_status_for_error(exc: Exception) -> int:
    """Invalid input is 400; any other error is an internal failure (500)."""
    if getattr(exc, "code", None) == "INVALID_REQUEST":
        return 400
    return 500
