import assert from "node:assert/strict";
import test from "node:test";
import { POST } from "../src/app/api/cycle-algo/explore/route.js";
import { weatherResponse } from "./fixtures.mjs";

function request(payload, headers = { "Content-Type": "application/json" }) {
  return new Request("http://localhost/api/cycle-algo/explore", {
    method: "POST", headers, body: typeof payload === "string" ? payload : JSON.stringify(payload),
  });
}

test("proxy forwards every selected view and keeps all paths and evidence", async (t) => {
  const views = ["fastest_completion", "more_crop_diversity", "closest_temperature_match", "least_dry_spell_exposure", "least_heavy_rain_exposure"];
  for (const preference of views) {
    const data = weatherResponse(preference);
    let calls = 0;
    t.mock.method(globalThis, "fetch", async (url, options) => {
      calls++;
      assert.equal(url.pathname, "/api/explore");
      assert.deepEqual(JSON.parse(options.body), data.request);
      assert.equal(options.headers["Accept-Encoding"], "identity");
      assert.equal(options.cache, "no-store");
      assert.ok(options.signal instanceof AbortSignal);
      return Response.json(data);
    });
    const response = await POST(request(data.request));
    assert.equal(response.status, 200);
    assert.deepEqual(await response.json(), data);
    assert.equal(calls, 1);
    t.mock.restoreAll();
  }
});

test("initial discovery remains successful with an empty branches array", async (t) => {
  const data = weatherResponse();
  data.request.first_crop_id = null;
  data.branches = [];
  data.ranking.groups.conditional = { ranked: [], unranked: [] };
  t.mock.method(globalThis, "fetch", async () => Response.json(data));
  const response = await POST(request(data.request));
  assert.equal(response.status, 200);
  assert.deepEqual((await response.json()).branches, []);
});

test("engine date errors preserve status, message, and field", async (t) => {
  const error = { schema_version: "1", error: { code: "INVALID_REQUEST", message: "Date outside planning range", field: "start_date" } };
  t.mock.method(globalThis, "fetch", async () => Response.json(error, { status: 400 }));
  const response = await POST(request({ start_date: "9999-12-31" }));
  assert.equal(response.status, 400);
  assert.deepEqual(await response.json(), error);
});

test("unreachable engine returns a retryable error, never mock results", async (t) => {
  t.mock.method(globalThis, "fetch", async () => { throw new Error("private server detail"); });
  const response = await POST(request(weatherResponse().request));
  assert.equal(response.status, 503);
  const data = await response.json();
  assert.equal(data.error.code, "ENGINE_UNREACHABLE");
  assert.equal(data.branches, undefined);
  assert.doesNotMatch(JSON.stringify(data), /private server detail/);
});

test("malformed upstream JSON or shape returns 502", async (t) => {
  for (const body of ["not json", JSON.stringify({ schema_version: "1", status: "ok" })]) {
    t.mock.method(globalThis, "fetch", async () => new Response(body));
    const response = await POST(request(weatherResponse().request));
    assert.equal(response.status, 502);
    t.mock.restoreAll();
  }
});

test("invalid, oversized, and non-JSON requests never contact the engine", async (t) => {
  let calls = 0;
  t.mock.method(globalThis, "fetch", async () => { calls++; throw new Error("Unexpected fetch"); });
  assert.equal((await POST(request("{"))).status, 400);
  assert.equal((await POST(request("[]"))).status, 400);
  assert.equal((await POST(request("x".repeat(65537)))).status, 413);
  assert.equal((await POST(request("{}", { "Content-Type": "text/plain" }))).status, 415);
  assert.equal(calls, 0);
});
