import assert from "node:assert/strict";
import test from "node:test";
import { dayRange, formatDate, readComparison, readScenario, scenarioLink } from "../src/lib/cycleAlgo.js";
import { translateEngineMessage } from "../src/lib/cycleEngineCopy.js";
import { cycleLocales, readCycleLanguage } from "../src/lib/cycleLocale.js";
import { rankingValue, seasonLabel } from "../src/lib/rotationRanking.js";

const { bn, en } = cycleLocales;

test("shared analysis links carry the display language without changing the request", () => {
  assert.equal(readCycleLanguage(undefined), "bn");
  assert.equal(readCycleLanguage("fr"), "bn");
  assert.equal(readCycleLanguage("en"), "en");
  const scenario = readScenario({ crop: "boro_brri_dhan28", rank: "least_heavy_rain_exposure" }, "2026-11-06");
  const url = new URL(scenarioLink("/risk-uncertainty", scenario, ["a", "b"], "en"), "https://example.test");
  const query = { ...Object.fromEntries(url.searchParams), branch: url.searchParams.getAll("branch") };
  assert.equal(query.lang, "en");
  assert.deepEqual(readScenario(query, ""), scenario);
  assert.deepEqual(readComparison(query), ["a", "b"]);
});

test("Bangla results preserve precision, units, zero, and unavailable values", () => {
  assert.equal(dayRange({ min: 0, max: 0 }, bn), "০ দিন");
  assert.equal(dayRange(null, bn), "জানা নেই");
  assert.equal(formatDate("2026-11-06", bn), "৬ নভেম্বর, ২০২৬");
  assert.equal(rankingValue(0.123456, "least_heavy_rain_exposure", bn), "০.১২৩৪৬ ভারী বৃষ্টির দিন / চাষের দিন");
  assert.equal(rankingValue(0, "closest_temperature_match", bn), "নির্দেশনা থেকে ০ °C পার্থক্য");
  assert.equal(rankingValue(null, "closest_temperature_match", bn), "তুলনাযোগ্য তথ্য নেই");
  assert.equal(seasonLabel([1991, 1993], bn), "২টি সম্পূর্ণ মৌসুম (১৯৯১–১৯৯৩)");
});

test("crop names use the engine label, then the glossary, then the tagged original", () => {
  const boro = { crop_id: "boro_brri_dhan28", name_en: "Boro rice" };
  assert.deepEqual(bn.cropName({ ...boro, name_bn: " বোরো " }), { text: "বোরো", lang: "bn" });
  assert.deepEqual(bn.cropName(boro), { text: "বোরো ধান", lang: "bn" });
  assert.deepEqual(en.cropName(boro), { text: "Boro rice", lang: "en" });
  assert.deepEqual(bn.cropName({ crop_id: "future_crop", name_en: "Future crop" }), { text: "Future crop", lang: "en" });
});

test("engine notices localize known codes and preserve a path for unknown originals", () => {
  const message = "No candidate branches - 10 conditional branches shown.";
  assert.match(translateEngineMessage(message, "NO_CANDIDATE_BRANCHES", bn), /১০টি/);
  assert.match(translateEngineMessage("Timeout", "ENGINE_TIMEOUT", bn), /আবার চেষ্টা করুন/);
  assert.match(translateEngineMessage("TEMPERATURE_UNITS_UNAVAILABLE: UNITS_INCOMPATIBLE for T2M.", undefined, bn), /একক সামঞ্জস্যপূর্ণ নয়/);
  assert.equal(translateEngineMessage("An unknown warning.", "NEW_WARNING", bn), null);
  assert.equal(translateEngineMessage(message, undefined, en), null);
});
