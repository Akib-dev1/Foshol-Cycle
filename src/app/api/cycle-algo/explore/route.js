const MAX_REQUEST_BYTES = 64 * 1024;
const TIMEOUT_MS = 45_000;
const statuses = new Set(["ok", "partial", "no_supported_options", "unsupported_district", "data_unavailable"]);

function errorResponse(status, code, message) {
  return Response.json({ schema_version: "1", error: { code, message, field: null } }, { status });
}

function isRankingGroup(group) {
  return Array.isArray(group?.ranked) && Array.isArray(group?.unranked) &&
    [...group.ranked, ...group.unranked].every((entry) => typeof entry?.branch_id === "string");
}

function isExploreResponse(data) {
  return statuses.has(data.status) && data.request && data.district && data.branch_summary &&
    Array.isArray(data.crop_options) && data.crop_options.every((crop) => typeof crop?.crop_id === "string") &&
    Array.isArray(data.branches) && data.branches.every((branch) =>
      typeof branch?.branch_id === "string" && Array.isArray(branch.crops) && branch.crops.length === 3 &&
      branch.crops.every((crop) => typeof crop?.name_en === "string") &&
      Array.isArray(branch.transitions) && branch.transitions.length === 2 && branch.transitions.every(Boolean)) &&
    isRankingGroup(data.ranking?.groups?.candidate) && isRankingGroup(data.ranking?.groups?.conditional);
}

export async function POST(request) {
  const contentType = request.headers.get("content-type")?.split(";")[0].trim().toLowerCase();
  if (contentType !== "application/json") {
    return errorResponse(415, "INVALID_REQUEST", "Send the scenario as JSON.");
  }

  let body;
  try {
    if (Number(request.headers.get("content-length")) > MAX_REQUEST_BYTES) {
      return errorResponse(413, "INVALID_REQUEST", "The scenario request is too large.");
    }
    body = await request.text();
    if (Buffer.byteLength(body) > MAX_REQUEST_BYTES) {
      return errorResponse(413, "INVALID_REQUEST", "The scenario request is too large.");
    }
    const payload = JSON.parse(body);
    if (!payload || typeof payload !== "object" || Array.isArray(payload)) {
      return errorResponse(400, "INVALID_REQUEST", "Send the scenario as a JSON object.");
    }
  } catch {
    return errorResponse(400, "INVALID_REQUEST", "The scenario request is not valid JSON.");
  }

  let endpoint;
  try {
    endpoint = new URL("/api/explore", process.env.CYCLE_ALGO_BASE_URL ?? "http://127.0.0.1:8000");
    if (endpoint.protocol !== "http:" && endpoint.protocol !== "https:") throw new Error();
  } catch {
    return errorResponse(503, "ENGINE_UNREACHABLE", "Check the CycleAlgo server address and retry.");
  }

  const timeout = AbortSignal.timeout(TIMEOUT_MS);
  const signal = AbortSignal.any([timeout, request.signal]);
  let upstream;
  let data;
  try {
    upstream = await fetch(endpoint, {
      method: "POST",
      // Avoid Node's gzip/HTTP-1.0 parser failure; Next.js handles browser compression.
      headers: { "Content-Type": "application/json", Accept: "application/json", "Accept-Encoding": "identity" },
      body,
      signal,
      cache: "no-store",
      redirect: "manual",
    });
    data = await upstream.json();
  } catch {
    if (timeout.aborted) return errorResponse(504, "ENGINE_TIMEOUT", "CycleAlgo took too long to respond. Try again.");
    if (!upstream) return errorResponse(503, "ENGINE_UNREACHABLE", "Start the CycleAlgo server and retry.");
  }

  if (data?.schema_version === "1") {
    if (upstream.status === 200 && isExploreResponse(data)) return Response.json(data);
    if (upstream.status >= 400 && typeof data.error?.code === "string" && typeof data.error?.message === "string") {
      return Response.json(data, { status: upstream.status });
    }
  }
  return errorResponse(502, "ENGINE_INVALID_RESPONSE", "CycleAlgo returned an unexpected response. Check the engine version and retry.");
}
