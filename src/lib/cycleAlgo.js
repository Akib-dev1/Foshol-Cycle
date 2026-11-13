export const ENGINE_DISTRICT = "rajshahi";
export const MAX_COMPARISONS = 3;
export const MIN_START_DATE = "0002-01-01";
export const MAX_START_DATE = "9990-12-31";

export const waterOptions = {
  unknown: "Water access unknown",
  rainfed: "Rainfed",
  irrigation_available: "Irrigation available",
};

export const rankingOptions = {
  fastest_completion: "Fastest completion",
  more_crop_diversity: "More crop-family diversity",
  closest_temperature_match: "Closest temperature match",
  least_dry_spell_exposure: "Less dry-spell exposure",
  least_heavy_rain_exposure: "Less heavy-rain exposure",
};

export function todayInDhaka() {
  return new Intl.DateTimeFormat("sv-SE", { timeZone: "Asia/Dhaka" }).format();
}

export function isCalendarDate(value) {
  if (typeof value !== "string" || !/^\d{4}-\d{2}-\d{2}$/.test(value) || value.startsWith("0000")) {
    return false;
  }
  const parsed = new Date(`${value}T00:00:00Z`);
  return Number.isFinite(parsed.getTime()) && parsed.toISOString().slice(0, 10) === value;
}

export function isPlanningDate(value) {
  return isCalendarDate(value) && value >= MIN_START_DATE && value <= MAX_START_DATE;
}

export function readScenario(query, defaultDate) {
  return {
    district_id: ENGINE_DISTRICT,
    start_date: typeof query.date === "string" ? query.date : defaultDate,
    first_crop_id: typeof query.crop === "string" && query.crop ? query.crop : null,
    water_access: typeof query.water === "string" && Object.hasOwn(waterOptions, query.water) ? query.water : "unknown",
    preference: typeof query.rank === "string" && Object.hasOwn(rankingOptions, query.rank) ? query.rank : "fastest_completion",
  };
}

export function readComparison(query) {
  const branchIds = Array.isArray(query.branch) ? query.branch : [query.branch];
  return [...new Set(branchIds.filter((id) => typeof id === "string" && id))].slice(0, MAX_COMPARISONS);
}

export function scenarioLink(path, scenario, branchIds) {
  const params = new URLSearchParams({
    date: scenario.start_date,
    crop: scenario.first_crop_id,
    water: scenario.water_access,
    rank: scenario.preference,
  });
  for (const id of branchIds) params.append("branch", id);
  return `${path}?${params}`;
}

export function rotationName(branch) {
  return branch.crops.map((crop) => crop.name_en).join(" → ");
}

export function dayRange(range) {
  if (range?.min == null && range?.max == null) return "Unknown";
  if (range.min == null) return `Up to ${range.max} days`;
  if (range.max == null) return `${range.min} days minimum`;
  if (range.min === range.max) return range.min === 1 ? "1 day" : `${range.min} days`;
  return `${range.min}–${range.max} days`;
}

const dateFormat = new Intl.DateTimeFormat("en-GB", {
  day: "numeric", month: "short", year: "numeric", timeZone: "UTC",
});

export function formatDate(date) {
  return isCalendarDate(date) ? dateFormat.format(new Date(`${date}T00:00:00Z`)) : "Unknown";
}

export function dateRange(range) {
  if (!range?.earliest) return "Unknown";
  const start = formatDate(range.earliest);
  return range.earliest === range.latest ? start : `${start} – ${formatDate(range.latest)}`;
}
