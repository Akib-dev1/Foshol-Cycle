"""Small atomic JSON cache shared by the environmental loaders."""

from __future__ import annotations

import hashlib
import json
import math
import os
import re
import tempfile
from pathlib import Path

_KEY_RE = re.compile(r"^[0-9a-f]{64}$")


def build_cache_key(
    product: str,
    product_version: str,
    latitude: float,
    longitude: float,
    start_date: str,
    end_date: str,
    variables: list[str] | tuple[str, ...],
    settings: dict,
    point_id: str | None = None,
) -> str:
    """Return a SHA-256 over the canonical request description.

    ``variables`` is order-insensitive; ``settings`` is canonical JSON with
    sorted keys. Every input, including ``point_id``, affects the key.
    """
    payload = {
        "product": product,
        "product_version": product_version,
        "latitude": float(latitude),
        "longitude": float(longitude),
        "start_date": start_date,
        "end_date": end_date,
        "variables": sorted({str(name) for name in variables}),
        "settings": settings,
        "point_id": point_id,
    }
    canonical = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _reject_json_constant(value: str) -> None:
    raise ValueError(f"non-finite JSON constant: {value}")


def _finite_json_float(value: str) -> float:
    number = float(value)
    if not math.isfinite(number):
        raise ValueError(f"non-finite JSON number: {value}")
    return number



class EnvironmentCache:
    """A directory of atomic JSON files keyed by SHA-256."""

    def __init__(self, cache_dir: str | Path) -> None:
        self.cache_dir = Path(cache_dir)

    def _path(self, key: str) -> Path:
        if not isinstance(key, str) or _KEY_RE.fullmatch(key) is None:
            raise ValueError("cache key must be a 64-character hex SHA-256")
        return self.cache_dir / f"{key}.json"

    def get(self, key: str) -> dict | None:
        """Return a cached JSON object, or ``None`` if absent or corrupt."""
        path = self._path(key)
        try:
            payload = json.loads(
                path.read_text(encoding="utf-8"),
                parse_constant=_reject_json_constant,
                parse_float=_finite_json_float,
            )
        except (FileNotFoundError, UnicodeDecodeError, ValueError):
            return None
        except OSError:
            return None
        return payload if isinstance(payload, dict) else None

    def put(self, key: str, payload: dict) -> None:
        """Write ``payload`` atomically; non-finite JSON is rejected."""
        if not isinstance(payload, dict):
            raise ValueError("cache payload must be a JSON object")
        path = self._path(key)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        text = json.dumps(payload, ensure_ascii=False, allow_nan=False)

        descriptor, temporary = tempfile.mkstemp(
            dir=self.cache_dir, prefix=f"{key}-", suffix=".tmp"
        )
        try:
            with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
                handle.write(text)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary, path)
        except BaseException:
            try:
                os.unlink(temporary)
            except OSError:
                pass
            raise
