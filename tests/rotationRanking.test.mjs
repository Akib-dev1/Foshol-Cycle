import assert from "node:assert/strict";
import test from "node:test";
import {
  climateView, cropExposure, rankGroup, rankingValue, seasonLabel, viewUnavailableReason,
} from "../src/lib/rotationRanking.js";
import {
  isCalendarDate, isPlanningDate, MAX_START_DATE, MIN_START_DATE,
  rankingOptions, readComparison, readScenario, scenarioLink,
} from "../src/lib/cycleAlgo.js";
import { weatherResponse } from "./fixtures.mjs";

test("engine ordering, exact zero ties, and unranked status survive unchanged", () => {
  const data = weatherResponse();
  const branches = new Map(data.branches.map((branch) => [branch.branch_id, branch]));
  const result = rankGroup(data.ranking.groups.conditional, branches);
  assert.deepEqual(result.map(({ id }) => id), ["z", "a", "b", "unknown"]);
  assert.deepEqual(result.map(({ value }) => value), [0, 0, 5, null]);
  assert.deepEqual(result.map(({ rank }) => rank), [1, 1, 3, null]);
  assert.equal(result[0].tied, true);
  assert.equal(result[1].tied, true);
  assert.equal(result[2].tied, false);
  assert.equal(result[3].reason, "CLIMATE_EVIDENCE_MISSING");
  // The branch-wide score is 999; common-period engine ranking is deliberately different.
  assert.notEqual(result[0].value, branches.get("z").metrics.climate.summary.min_realization.dry_spell_days);
});

test("diversity also uses engine values rather than browser recalculation", () => {
  const data = weatherResponse("more_crop_diversity");
  const branches = new Map(data.branches.map((branch) => [branch.branch_id, branch]));
  assert.equal(rankGroup(data.ranking.groups.conditional, branches)[0].value, 0);
});

test("entries for absent branches are not rendered", () => {
  const data = weatherResponse();
  assert.deepEqual(rankGroup(data.ranking.groups.conditional, new Map()), []);
});

test("weather values use their own units and never zero-fill unavailable values", () => {
  assert.equal(rankingValue(0, "closest_temperature_match"), "0 °C from guidance");
  assert.equal(rankingValue(27.666666, "least_dry_spell_exposure"), "27.67 dry-spell days");
  assert.equal(rankingValue(0.02684, "least_heavy_rain_exposure"), "0.02684 heavy days / growing day");
  assert.match(rankingValue(null, "least_dry_spell_exposure"), /Unavailable/);
  assert.match(rankingValue(NaN, "closest_temperature_match"), /Unavailable/);
  assert.equal(rankingValue(3, "more_crop_diversity"), "3 crop families");
});

test("per-crop detail reads only the active view, not an unrelated measure", () => {
  const crop = { temperature: { median_distance_c: 0 }, dry_spell: { median_longest_run_days: 12 }, heavy_rain: { frequency: 0.2 } };
  assert.equal(cropExposure(crop, "closest_temperature_match"), 0);
  assert.equal(cropExposure(crop, "least_dry_spell_exposure"), 12);
  assert.equal(cropExposure(crop, "least_heavy_rain_exposure"), 0.2);
  assert.equal(cropExposure({}, "least_dry_spell_exposure"), undefined);
});

test("missing temperature does not disable rainfall views", () => {
  const { branches } = weatherResponse();
  assert.equal(climateView("closest_temperature_match"), "temperature");
  assert.equal(climateView("least_heavy_rain_exposure"), "rain");
  assert.equal(climateView("fastest_completion"), null);
  assert.equal(viewUnavailableReason(branches, "closest_temperature_match"), "T2M units unavailable");
  assert.equal(viewUnavailableReason(branches, "least_dry_spell_exposure"), null);
  assert.equal(viewUnavailableReason(branches, "least_heavy_rain_exposure"), null);
  assert.equal(viewUnavailableReason(branches, "fastest_completion"), null);
});

test("missing rain does not disable valid temperature and missing data has a reason", () => {
  const branches = [{ metrics: { climate: { views: { temperature: { status: "ok" }, rain: { status: "unavailable", reason: "Rain units incompatible" } } } } }];
  assert.equal(viewUnavailableReason(branches, "closest_temperature_match"), null);
  assert.equal(viewUnavailableReason(branches, "least_dry_spell_exposure"), "Rain units incompatible");
  assert.match(viewUnavailableReason([{}], "least_heavy_rain_exposure"), /No usable/);
});

test("shared-season labels use actual counts, including non-consecutive years", () => {
  assert.equal(seasonLabel([1991, 1993]), "2 complete seasons (1991–1993)");
  assert.equal(seasonLabel([1991]), "1 complete season (1991)");
  assert.equal(seasonLabel([]), "No common complete seasons");
});

test("planning bounds do not restrict display of later valid harvest dates", () => {
  assert.equal(isPlanningDate(MIN_START_DATE), true);
  assert.equal(isPlanningDate(MAX_START_DATE), true);
  assert.equal(isPlanningDate("0001-01-01"), false);
  assert.equal(isPlanningDate("9991-01-01"), false);
  assert.equal(isPlanningDate("2026-02-30"), false);
  assert.equal(isPlanningDate("2028-02-29"), true);
  assert.equal(isCalendarDate("9991-01-01"), true);
});

test("all engine-backed preferences survive shared links and none send a legume score", () => {
  assert.equal(Object.hasOwn(rankingOptions, "legume_presence"), false);
  for (const preference of Object.keys(rankingOptions)) {
    const scenario = readScenario({ date: "2026-11-06", crop: "boro_brri_dhan28", water: "rainfed", rank: preference }, "2026-11-07");
    const url = new URL(scenarioLink("/risk-uncertainty", scenario, ["z", "a"]), "http://localhost");
    const restored = readScenario(Object.fromEntries(url.searchParams), "2026-11-07");
    assert.deepEqual(restored, scenario);
    assert.deepEqual(readComparison({ branch: url.searchParams.getAll("branch") }), ["z", "a"]);
  }
});
