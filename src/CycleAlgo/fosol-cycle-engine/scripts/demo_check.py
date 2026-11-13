#!/usr/bin/env python3
"""Offline E9 demo check: contract, counts, SMAP isolation, determinism."""

from __future__ import annotations

import datetime as dt
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from contract_check import validate_response
from src.branch_metrics import rank_branches
from src.crop_profiles import load_crop_profiles
from src.explore import explore
from src.local_power import load_local_power
from src.request_validation import RequestValidationError
from src.smap_api import parse_appeears_csv

DATA = ROOT.parent / "Data" / "fosol_cycle_rajshahi_crop_dataset.csv"
LOCAL_POWER = load_local_power(DATA.parent / "NASA_RAJ_DATA_2000_2026.csv")
SMAP_FIXTURE = (
    ROOT
    / "tests"
    / "fixtures"
    / "appeears_spl4smgp_rajshahi_20250101_20250103.csv"
)
CONFIG = {
    "max_initial_wait_days": 180,
    "max_waiting_days": None,
    "analysis_start_year": 2000,
    "analysis_end_year": 2025,
    "max_branches": None,
}
NOW = dt.datetime(2026, 11, 9, 0, 0, tzinfo=dt.timezone.utc)
START = "2026-11-06"
PROFILES = None


def _real_smap_context() -> dict:
    context = parse_appeears_csv(
        SMAP_FIXTURE.read_text(encoding="utf-8"),
        retrieved_at="2026-11-09T12:00:00+00:00",
    )
    context["product"] = "SPL4SMGP.008"
    return context


SMAP_AVAILABLE = _real_smap_context()
SMAP_UNAVAILABLE = {
    **SMAP_AVAILABLE,
    "status": "unavailable",
    "observations": [],
    "warnings": [
        {
            "code": "SMAP_CONTEXT_UNAVAILABLE",
            "message": "SMAP context fetch failed.",
        }
    ],
}
SMAP_EXPIRED = {
    **SMAP_AVAILABLE,
    "status": "expired",
    "observations": [],
    "warnings": [],
}


class DemoFailure(Exception):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise DemoFailure(message)


def payload(
    first_crop_id=None,
    preference="fastest_completion",
    water_access="unknown",
) -> dict:
    return {
        "district_id": "rajshahi",
        "start_date": START,
        "first_crop_id": first_crop_id,
        "water_access": water_access,
        "preference": preference,
    }


RESPONSES: list[tuple[str, dict]] = []


def run(
    first_crop_id=None,
    preference="fastest_completion",
    water_access="unknown",
    *,
    environment=None,
    smap_context=None,
    config=None,
    label=None,
) -> dict:
    response = explore(
        payload(first_crop_id, preference, water_access),
        profiles=PROFILES,
        config=config or CONFIG,
        environment=environment,
        smap_context=smap_context,
        now=NOW,
    )
    errors = validate_response(response)
    require(not errors, f"{label or first_crop_id or 'initial'} contract: {errors[:3]}")
    RESPONSES.append((label or str(first_crop_id or "initial"), response))
    return response


def _walk(value, source_ids: set[str]) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if key == "source_ids" and isinstance(item, list):
                source_ids.update(
                    entry for entry in item if isinstance(entry, str) and entry
                )
            else:
                _walk(item, source_ids)
    elif isinstance(value, list):
        for item in value:
            _walk(item, source_ids)


def _has_empty_string(value) -> bool:
    if isinstance(value, str):
        return value == ""
    if isinstance(value, dict):
        return any(_has_empty_string(item) for item in value.values())
    if isinstance(value, list):
        return any(_has_empty_string(item) for item in value)
    return False


def _has_nonfinite(value) -> bool:
    if isinstance(value, float):
        return not math.isfinite(value)
    if isinstance(value, dict):
        return any(_has_nonfinite(item) for item in value.values())
    if isinstance(value, list):
        return any(_has_nonfinite(item) for item in value)
    return False


def _check_ranges(value) -> None:
    if isinstance(value, dict):
        if "earliest" in value and "latest" in value:
            earliest = value["earliest"]
            latest = value["latest"]
            if isinstance(earliest, str) and isinstance(latest, str):
                require(
                    earliest <= latest,
                    f"invalid range {earliest!r}..{latest!r}",
                )
        for item in value.values():
            _check_ranges(item)
    elif isinstance(value, list):
        for item in value:
            _check_ranges(item)


def check_invariants() -> None:
    for label, response in RESPONSES:
        require(not _has_empty_string(response), f"{label}: empty string present")
        require(not _has_nonfinite(response), f"{label}: non-finite number present")
        try:
            json.dumps(response, allow_nan=False)
        except ValueError as exc:
            raise DemoFailure(f"{label}: not strict JSON: {exc}") from exc

        branch_ids = [branch.get("branch_id") for branch in response["branches"]]
        require(
            len(branch_ids) == len(set(branch_ids)),
            f"{label}: duplicate branch IDs",
        )
        source_catalog = {
            source.get("source_id") for source in response["data_sources"]
        }
        referenced: set[str] = set()
        _walk(response, referenced)
        missing_sources = sorted(referenced - source_catalog)
        require(
            not missing_sources,
            f"{label}: source_ids not in data_sources: {missing_sources[:3]}",
        )

        for branch in response["branches"]:
            require(
                len(branch["crops"]) == 3 and len(branch["transitions"]) == 2,
                f"{label}: branch is not exactly 3 crops/2 transitions",
            )
            require(
                branch["status"] in ("candidate", "conditional"),
                f"{label}: blocked branch in branches",
            )
            _check_ranges(branch)
            completion = branch["metrics"]["completion"]
            if completion["status"] == "ok":
                for realization_name in (
                    "min_realization",
                    "max_realization",
                ):
                    realization = completion[realization_name]
                    dates = [
                        realization[key]
                        for key in ("p1", "h1", "p2", "h2", "p3", "h3")
                    ]
                    require(
                        dates == sorted(dates),
                        f"{label}: non-chronological {realization_name}",
                    )

        ranking = response["ranking"]["groups"]
        for group_name in ("candidate", "conditional"):
            for entry in ranking[group_name]["ranked"] + ranking[group_name][
                "unranked"
            ]:
                require(
                    entry.get("branch_id") in branch_ids,
                    f"{label}: ranking references unknown branch",
                )
                require(
                    entry.get("status") in ("candidate", "conditional"),
                    f"{label}: blocked/unsupported branch in ranking",
                )


def main() -> int:
    global PROFILES
    try:
        PROFILES = load_crop_profiles(DATA)
        initial = run(label="initial")
        require(initial["status"] == "partial", "initial status is not partial")
        require(initial["branches"] == [], "initial response returned branches")
        summary = initial["branch_summary"]
        require(summary["candidate_count"] == 0, "initial candidate count")
        require(summary["conditional_count"] == 295, "initial conditional count")
        require(summary["excluded_count"] == 56, "initial exclusion count")
        require(
            "295 conditional branches available; select a first crop"
            in summary["message"],
            "initial summary message",
        )
        options = {option["crop_id"]: option for option in initial["crop_options"]}
        require(len(options) == 8, "crop option count")
        require(options["aman_br11"]["status"] == "unsupported", "Aman status")
        require(
            options["mung_bari_mung6_kharif1"]["status"] == "unsupported",
            "Mung status",
        )
        conditional_ids = [
            crop_id
            for crop_id, option in options.items()
            if option["status"] == "conditional"
        ]
        require(len(conditional_ids) == 6, "conditional crop option count")
        for crop_id in conditional_ids:
            wait = options[crop_id]["initial_wait_days"]
            require(
                isinstance(wait, int) and 0 <= wait <= 180,
                f"{crop_id}: initial wait {wait}",
            )

        selected_counts = {}
        for crop_id in conditional_ids:
            selected = run(crop_id, label=f"selected:{crop_id}")
            branches = selected["branches"]
            require(branches, f"{crop_id}: no branches")
            require(selected["status"] == "partial", f"{crop_id}: status")
            summary = selected["branch_summary"]
            require(summary["candidate_count"] == 0, f"{crop_id}: candidates")
            require(
                summary["conditional_count"] == len(branches),
                f"{crop_id}: conditional count",
            )
            require(
                summary["message"]
                == f"No candidate branches - {len(branches)} conditional branches shown.",
                f"{crop_id}: shown message",
            )
            for branch in branches:
                require(
                    len(branch["crops"]) == 3
                    and len(branch["transitions"]) == 2,
                    f"{crop_id}: branch shape",
                )
                require(
                    branch["initial_wait_days"] <= 180,
                    f"{crop_id}: branch initial wait",
                )
            selected_counts[crop_id] = len(branches)

        boro = run("boro_brri_dhan28", label="boro")
        boro_branches = boro["branches"]
        power_config = {**CONFIG, "max_branches": 1}
        local_power = run(
            "boro_brri_dhan28",
            environment=LOCAL_POWER,
            config=power_config,
            label="boro:local-power",
        )
        no_environment = run(
            "boro_brri_dhan28",
            environment=None,
            config=power_config,
            label="boro:no-environment",
        )
        require(
            no_environment["status"] == local_power["status"],
            "local POWER changed status",
        )
        require(
            json.dumps(no_environment["ranking"], sort_keys=True)
            == json.dumps(local_power["ranking"], sort_keys=True),
            "local POWER changed ranking",
        )
        for branch in local_power["branches"]:
            for crop in branch["crops"]:
                outlook = crop["outlook"]
                require(
                    outlook["status"] in ("ok", "partial"),
                    "local POWER outlook status",
                )
                ranges = outlook["seasonal_ranges"]
                require(
                    ranges["status"] in ("ok", "partial"),
                    "seasonal ranges status",
                )
                require(
                    ranges["analysis_period"]
                    == {"start_year": 2000, "end_year": 2025},
                    "seasonal ranges coverage years",
                )
                require(
                    [item["variable"] for item in ranges["indicators"]]
                    == ["T2M", "PRECTOTCORR", "GWETTOP"],
                    "seasonal range indicators",
                )
                for indicator in ranges["indicators"]:
                    require(
                        indicator["min"] <= indicator["median"] <= indicator["max"],
                        "seasonal range ordering",
                    )
                require(
                    ranges["thresholds_applied"] is False,
                    "seasonal thresholds applied",
                )
                require(ranges["warnings"] == [], "seasonal warnings")
        boro_ids = {branch["branch_id"] for branch in boro_branches}
        allowed = (
            "fastest_completion",
            "lowest_total_cost",
            "least_irrigation_dependence",
            "highest_net_return",
            "more_crop_diversity",
            "closest_temperature_match",
            "least_dry_spell_exposure",
            "least_heavy_rain_exposure",
        )
        for preference in allowed:
            result = run(
                "boro_brri_dhan28", preference, label=f"preference:{preference}"
            )
            groups = result["ranking"]["groups"]
            require(groups["candidate"]["count"] == 0, f"{preference}: candidates")
            conditional = groups["conditional"]
            if preference in ("fastest_completion", "more_crop_diversity"):
                require(
                    len(conditional["ranked"]) == len(boro_branches),
                    f"{preference}: not all branches ranked",
                )
                require(conditional["unranked"] == [], f"{preference}: unranked")
                require(not result["ranking"]["no_winner"], f"{preference}: no_winner")
            else:
                require(
                    conditional["ranked"] == [],
                    f"{preference}: ranked economics/irrigation",
                )
                require(
                    len(conditional["unranked"]) == len(boro_branches),
                    f"{preference}: not all branches unranked",
                )
                require(result["ranking"]["no_winner"], f"{preference}: winner")
            for entry in groups["conditional"]["ranked"] + groups["conditional"][
                "unranked"
            ]:
                require(
                    entry["branch_id"] in boro_ids,
                    f"{preference}: unknown branch ID",
                )

        climate_config = {**CONFIG, "max_branches": 3}
        for preference in (
            "closest_temperature_match",
            "least_dry_spell_exposure",
            "least_heavy_rain_exposure",
        ):
            result = run(
                "boro_brri_dhan28",
                preference,
                environment=LOCAL_POWER,
                config=climate_config,
                label=f"climate:{preference}",
            )
            conditional = result["ranking"]["groups"]["conditional"]
            require(
                len(conditional["ranked"]) == len(result["branches"]),
                f"{preference}: climate branches not ranked",
            )
            require(
                result["ranking"]["climate"]["common_season_counts"][
                    "conditional"
                ]
                > 0,
                f"{preference}: no common climate seasons",
            )

        try:
            run(
                "boro_brri_dhan28",
                "lowest_upfront_cash",
                label="preference:lowest_upfront_cash",
            )
        except RequestValidationError:
            pass
        else:
            raise DemoFailure("lowest_upfront_cash should be rejected by the contract")
        upfront = rank_branches(
            boro_branches, "lowest_upfront_cash", PROFILES
        )
        require(upfront["no_winner"], "upfront: no_winner")
        require(
            upfront["groups"]["conditional"]["ranked"] == [],
            "upfront: ranked branches",
        )
        require(
            len(upfront["groups"]["conditional"]["unranked"]) == len(boro_branches),
            "upfront: not all branches unranked",
        )

        for water in ("rainfed", "irrigation_available", "unknown"):
            result = run(
                "boro_brri_dhan28",
                water_access=water,
                label=f"water:{water}",
            )
            require(result["status"] == "partial", f"{water}: status")

        unavailable_smap = run(
            "boro_brri_dhan28",
            smap_context=SMAP_UNAVAILABLE,
            label="smap:unavailable",
        )
        available_smap = run(
            "boro_brri_dhan28",
            smap_context=SMAP_AVAILABLE,
            label="smap:available",
        )
        require(
            unavailable_smap["status"] == available_smap["status"],
            "SMAP changed status",
        )
        require(
            [b["branch_id"] for b in unavailable_smap["branches"]]
            == [b["branch_id"] for b in available_smap["branches"]],
            "SMAP changed branch IDs",
        )
        require(
            [b["status"] for b in unavailable_smap["branches"]]
            == [b["status"] for b in available_smap["branches"]],
            "SMAP changed branch status",
        )
        require(
            json.dumps(unavailable_smap["ranking"], sort_keys=True)
            == json.dumps(available_smap["ranking"], sort_keys=True),
            "SMAP changed ranking",
        )
        require(
            unavailable_smap["environment_context"]["status"] == "unavailable",
            "SMAP unavailable context status",
        )
        require(
            available_smap["environment_context"]["status"] == "available",
            "SMAP available context status",
        )
        available_context = available_smap["environment_context"]
        require(
            available_context["product"] == "SPL4SMGP.008",
            "SMAP context product",
        )
        require(
            available_context["resolution"] == "9 km EASE-Grid 2.0",
            "SMAP context resolution",
        )
        require(
            available_context["temporal_resolution"] == "3-hourly",
            "SMAP context temporal resolution",
        )
        require(
            available_context["label"]
            == "Context only - no effect on status or ranking",
            "SMAP context label",
        )
        observations = available_context["observations"]
        require(len(observations) == 24, "SMAP observation count")
        require(
            observations[0]["timestamp"].startswith("2025-01-01T")
            and observations[-1]["timestamp"].startswith("2025-01-03T"),
            "SMAP observation dates",
        )
        require(
            all(
                observation.get("sm_surface") is not None
                and observation.get("sm_rootzone") is not None
                for observation in observations
            ),
            "SMAP real observation values",
        )
        for key in ("status", "district", "request", "crop_options", "branches", "branch_summary", "ranking", "data_sources"):
            require(
                unavailable_smap[key] == available_smap[key],
                f"SMAP changed {key}",
            )
        differing = {
            key
            for key in unavailable_smap
            if unavailable_smap[key] != available_smap[key]
        }
        require(
            differing
            <= {"environment_context", "assumptions", "warnings", "missing_evidence"},
            f"SMAP changed unexpected blocks: {differing}",
        )

        for name, smap in (("unavailable", SMAP_UNAVAILABLE), ("expired", SMAP_EXPIRED)):
            offline = run(
                "boro_brri_dhan28",
                environment=None,
                smap_context=smap,
                label=f"offline:{name}",
            )
            require(offline["status"] == "partial", f"offline {name}: status")
            require(offline["warnings"], f"offline {name}: warning")
            context = offline["environment_context"]
            require(context["status"] == "unavailable", f"offline {name}: context")
            require(context["observations"] == [], f"offline {name}: moisture")
            require(
                "sm_surface" not in json.dumps(context)
                and "sm_rootzone" not in json.dumps(context),
                f"offline {name}: zero-filled moisture",
            )

        first = run("boro_brri_dhan28", label="determinism:1")
        second = run("boro_brri_dhan28", label="determinism:2")
        require(
            json.dumps(first, sort_keys=True) == json.dumps(second, sort_keys=True),
            "repeated request is not deterministic",
        )

        check_invariants()

        print(f"profiles: {len(PROFILES)}")
        initial_summary = initial["branch_summary"]
        print(
            "initial: status=partial branches=0 "
            f"candidate={initial_summary['candidate_count']} "
            f"conditional={initial_summary['conditional_count']} "
            f"exclusions={initial_summary['excluded_count']} "
            f"options={len(options)}"
        )
        print("initial waits: 6 conditional <=180; Aman/Mung unsupported")
        print(
            "selected: "
            + " ".join(f"{crop_id}={count}" for crop_id, count in selected_counts.items())
        )
        print(
            "preferences: fastest/diversity/climate ranked; "
            "cost/net/irrigation/upfront unranked/no_winner"
        )
        print("water: rainfed/irrigation_available/unknown -> partial")
        print(
            "smap: status/branch IDs/status/ranking identical; "
            "context available/unavailable; "
            f"observations={len(available_context['observations'])} "
            f"{available_context['observation_start']}..{available_context['observation_end']}"
        )
        print("offline: unavailable/expired SMAP -> partial with warning; no moisture zero-fill")
        print("determinism: identical")
        print("PASS")
        return 0
    except DemoFailure as exc:
        print(f"FAIL: {exc}")
        return 1
    except Exception as exc:  # noqa: BLE001 - demo command reports failure
        print(f"FAIL: {type(exc).__name__}: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
