"""Shared POWER + SMAP environmental loading with explicit cache freshness.

Missing values stay missing. A stale cache is only used with a
``STALE_CACHE`` warning; with no usable cache the provider is reported as
unavailable rather than replaced by an invented value.
"""

from __future__ import annotations

import datetime as dt
from collections.abc import Callable, Sequence

from src.environment_cache import EnvironmentCache, build_cache_key
from src.power_api import (
    COMMUNITY,
    POWER_PRODUCT_VERSION,
    PRODUCT as POWER_PRODUCT,
    TIME_STANDARD,
    UNITS as POWER_UNITS,
    PowerApiError,
    fetch_power_daily,
    normalize_power_response,
)
from src.smap_api import (
    AUTH_ERROR_MESSAGE,
    DEFAULT_LAYERS,
    PRODUCT as SMAP_PRODUCT,
    PRODUCT_VERSION as SMAP_PRODUCT_VERSION,
    AppEEarsAuthError,
    AppEEarsError,
    fetch_smap_point,
    resolve_point_id,
)

DEFAULT_POWER_VARIABLES = ("T2M", "PRECTOTCORR", "GWETTOP")

# Product freshness policy chosen for this explorer, not a provider SLA.
POWER_CACHE_TTL_SECONDS = 7 * 24 * 60 * 60
SMAP_CACHE_TTL_SECONDS = 7 * 24 * 60 * 60

_POWER_SETTINGS = {
    "community": COMMUNITY,
    "units": POWER_UNITS,
    "time_standard": TIME_STANDARD,
}
_PROVIDER_FAILURES = (PowerApiError, AppEEarsError, OSError, TimeoutError, ValueError)


class EnvironmentUnavailable(Exception):
    """No fresh or stale cached environment could be returned."""

    code = "ENVIRONMENT_UNAVAILABLE"

    def __init__(self, message: str, *, providers: Sequence[str] = ()) -> None:
        super().__init__(message)
        self.message = message
        self.providers = tuple(providers)


def _utc_now() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc)


def _as_utc(moment: dt.datetime) -> dt.datetime:
    return (
        moment.replace(tzinfo=dt.timezone.utc)
        if moment.tzinfo is None
        else moment
    )


def _cache_age_seconds(record: dict | None, now: Callable[[], dt.datetime]) -> float | None:
    if not isinstance(record, dict):
        return None
    retrieved_at = record.get("retrieved_at")
    if not isinstance(retrieved_at, str):
        return None
    try:
        retrieved = dt.datetime.fromisoformat(retrieved_at.replace("Z", "+00:00"))
    except ValueError:
        return None
    current = _as_utc(now())
    return max(0.0, (current - _as_utc(retrieved)).total_seconds())


def _stale_warning(provider: str, age_seconds: float, retrieved_at: object) -> dict:
    return {
        "code": "STALE_CACHE",
        "message": (
            f"{provider} data came from a stale cache and was not refreshed "
            "from the provider; freshness is not guaranteed."
        ),
        "provider": provider,
        "cache_age_seconds": age_seconds,
        "retrieved_at": retrieved_at,
    }


def _load_with_cache(
    cache: EnvironmentCache,
    *,
    key: str,
    provider: str,
    ttl_seconds: float,
    allow_network: bool,
    fetch: Callable[[], dict],
    now: Callable[[], dt.datetime],
) -> tuple[dict, list[dict], bool, float | None]:
    """Return ``(record, warnings, cache_hit, age_seconds)``."""
    cached = cache.get(key)
    age = _cache_age_seconds(cached, now)
    if cached is not None and age is not None and age <= ttl_seconds:
        return cached, [], True, age

    if allow_network:
        try:
            record = fetch()
        except _PROVIDER_FAILURES as exc:
            if cached is not None and age is not None:
                warning = _stale_warning(provider, age, cached.get("retrieved_at"))
                return cached, [warning], True, age
            hint = f" {AUTH_ERROR_MESSAGE}" if isinstance(exc, AppEEarsAuthError) else ""
            raise EnvironmentUnavailable(
                f"{provider} environmental data are unavailable and no usable "
                f"cache exists.{hint}",
                providers=(provider,),
            ) from exc
        try:
            cache.put(key, record)
        except OSError:
            pass  # a cache write failure must not discard a valid response
        return record, [], False, 0.0

    if cached is not None and age is not None:
        warning = _stale_warning(provider, age, cached.get("retrieved_at"))
        return cached, [warning], True, age
    raise EnvironmentUnavailable(
        f"{provider} environmental data are unavailable: network access is "
        "disabled and no usable cache exists.",
        providers=(provider,),
    )


def _finish(
    record: dict,
    *,
    warnings: list[dict],
    request: dict,
    cache_hit: bool,
    age_seconds: float | None,
) -> dict:
    result = dict(record)
    result["warnings"] = warnings
    result["request"] = request
    result["cache"] = {
        "hit": cache_hit,
        "stale": bool(warnings),
        "age_seconds": age_seconds,
    }
    return result


def load_power_environment(
    cache: EnvironmentCache,
    *,
    latitude: float,
    longitude: float,
    start_date: str,
    end_date: str,
    variables: Sequence[str] = DEFAULT_POWER_VARIABLES,
    cache_ttl_seconds: float = POWER_CACHE_TTL_SECONDS,
    allow_network: bool = True,
    fetcher: Callable[..., dict] = fetch_power_daily,
    normalizer: Callable[..., dict] = normalize_power_response,
    now: Callable[[], dt.datetime] = _utc_now,
) -> dict:
    """Load normalized POWER daily observations with cache semantics."""
    names = [str(name) for name in variables]
    if not names:
        raise ValueError("at least one POWER variable is required")

    key = build_cache_key(
        POWER_PRODUCT,
        POWER_PRODUCT_VERSION,
        latitude,
        longitude,
        start_date,
        end_date,
        names,
        _POWER_SETTINGS,
    )

    def fetch() -> dict:
        raw = fetcher(
            latitude,
            longitude,
            start_date,
            end_date,
            names,
            community=COMMUNITY,
            units=POWER_UNITS,
            time_standard=TIME_STANDARD,
        )
        return normalizer(raw)

    record, warnings, cache_hit, age = _load_with_cache(
        cache,
        key=key,
        provider="POWER",
        ttl_seconds=cache_ttl_seconds,
        allow_network=allow_network,
        fetch=fetch,
        now=now,
    )
    request = {
        "latitude": float(latitude),
        "longitude": float(longitude),
        "start_date": start_date,
        "end_date": end_date,
        "variables": names,
        "community": COMMUNITY,
        "units": POWER_UNITS,
        "time_standard": TIME_STANDARD,
    }
    return _finish(
        record,
        warnings=warnings,
        request=request,
        cache_hit=cache_hit,
        age_seconds=age,
    )


def load_smap_environment(
    cache: EnvironmentCache,
    *,
    latitude: float,
    longitude: float,
    start_date: str,
    end_date: str,
    point_id: str | None = None,
    cache_ttl_seconds: float = SMAP_CACHE_TTL_SECONDS,
    allow_network: bool = True,
    fetcher: Callable[..., dict] = fetch_smap_point,
    token: str | None = None,
    token_path: str | None = None,
    now: Callable[[], dt.datetime] = _utc_now,
) -> dict:
    """Load normalized SPL4SMGP.008 point observations with cache semantics."""
    resolved_point_id = resolve_point_id(point_id, latitude, longitude)
    values = list(DEFAULT_LAYERS)
    key = build_cache_key(
        SMAP_PRODUCT,
        SMAP_PRODUCT_VERSION,
        latitude,
        longitude,
        start_date,
        end_date,
        values,
        {},
        point_id=resolved_point_id,
    )

    def fetch() -> dict:
        return fetcher(
            latitude,
            longitude,
            start_date,
            end_date,
            point_id=resolved_point_id,
            token=token,
            token_path=token_path,
        )

    record, warnings, cache_hit, age = _load_with_cache(
        cache,
        key=key,
        provider="SMAP",
        ttl_seconds=cache_ttl_seconds,
        allow_network=allow_network,
        fetch=fetch,
        now=now,
    )
    request = {
        "latitude": float(latitude),
        "longitude": float(longitude),
        "start_date": start_date,
        "end_date": end_date,
        "point_id": resolved_point_id,
        "layers": values,
    }
    return _finish(
        record,
        warnings=warnings,
        request=request,
        cache_hit=cache_hit,
        age_seconds=age,
    )


def _unavailable_warning(code: str, provider: str, exc: EnvironmentUnavailable) -> dict:
    message = (
        f"{provider} environmental data are unavailable; {provider}-based "
        "checks must remain unknown."
    )
    if isinstance(exc.__cause__, AppEEarsAuthError):
        message = f"{message} {AUTH_ERROR_MESSAGE}"
    return {"code": code, "message": message, "provider": provider}


def load_environment(
    cache: EnvironmentCache,
    *,
    latitude: float,
    longitude: float,
    start_date: str,
    end_date: str,
    point_id: str | None = None,
    power_variables: Sequence[str] = DEFAULT_POWER_VARIABLES,
    power_ttl_seconds: float = POWER_CACHE_TTL_SECONDS,
    smap_ttl_seconds: float = SMAP_CACHE_TTL_SECONDS,
    allow_network: bool = True,
    power_loader: Callable[..., dict] = load_power_environment,
    smap_loader: Callable[..., dict] = load_smap_environment,
    token: str | None = None,
    token_path: str | None = None,
    now: Callable[[], dt.datetime] = _utc_now,
) -> dict:
    """Load both providers; one failure yields a partial result plus warning."""
    warnings: list[dict] = []
    resolved_point_id = resolve_point_id(point_id, latitude, longitude)

    power: dict | None = None
    power_failed = False
    try:
        power = power_loader(
            cache,
            latitude=latitude,
            longitude=longitude,
            start_date=start_date,
            end_date=end_date,
            variables=power_variables,
            cache_ttl_seconds=power_ttl_seconds,
            allow_network=allow_network,
            now=now,
        )
    except EnvironmentUnavailable as exc:
        power_failed = True
        warnings.append(_unavailable_warning("POWER_UNAVAILABLE", "POWER", exc))
    else:
        warnings.extend(power.get("warnings", []))

    smap: dict | None = None
    smap_failed = False
    try:
        smap = smap_loader(
            cache,
            latitude=latitude,
            longitude=longitude,
            start_date=start_date,
            end_date=end_date,
            point_id=resolved_point_id,
            cache_ttl_seconds=smap_ttl_seconds,
            allow_network=allow_network,
            token=token,
            token_path=token_path,
            now=now,
        )
    except EnvironmentUnavailable as exc:
        smap_failed = True
        warnings.append(_unavailable_warning("SMAP_UNAVAILABLE", "SMAP", exc))
    else:
        warnings.extend(smap.get("warnings", []))

    if power_failed and smap_failed:
        raise EnvironmentUnavailable(
            "Environmental data are unavailable from both POWER and SMAP.",
            providers=("POWER", "SMAP"),
        )

    request = {
        "latitude": float(latitude),
        "longitude": float(longitude),
        "start_date": start_date,
        "end_date": end_date,
        "point_id": resolved_point_id,
        "power_variables": [str(name) for name in power_variables],
        "smap_layers": list(DEFAULT_LAYERS),
    }
    return {
        "request": request,
        "sources": {"power": power, "smap": smap},
        "warnings": warnings,
    }
