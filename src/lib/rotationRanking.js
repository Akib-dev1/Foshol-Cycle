export const rankingDescriptions = {
  fastest_completion: "Shorter upper estimate first, measured from first planting to final harvest. Overlapping windows can finish in either order.",
  more_crop_diversity: "Rotations with more distinct crop families come first. Family count describes the sequence, not the condition of the soil.",
  closest_temperature_match: "Lower seasonal-median temperature distance from general EcoCrop guidance comes first. Zero is a match, not proof of no heat stress.",
  least_dry_spell_exposure: "Lower dry-spell exposure comes first: equal weighting of each crop's historical median longest run below 1 mm/day. This is not irrigation demand or drought damage.",
  least_heavy_rain_exposure: "Lower heavy-rain exposure comes first: equal weighting of each crop's frequency of days with at least 20 mm of rain. This is not a crop-damage or drainage rating.",
};

export function climateView(preference) {
  if (preference === "closest_temperature_match") return "temperature";
  if (["least_dry_spell_exposure", "least_heavy_rain_exposure"].includes(preference)) return "rain";
  return null;
}

export function rankingValue(value, preference) {
  if (!Number.isFinite(value)) return "Unavailable — no comparable data";
  if (preference === "more_crop_diversity") return `${value} crop ${value === 1 ? "family" : "families"}`;
  if (preference === "closest_temperature_match") return `${value.toLocaleString("en-GB", { maximumFractionDigits: 2 })} °C from guidance`;
  if (preference === "least_dry_spell_exposure") return `${value.toLocaleString("en-GB", { maximumFractionDigits: 2 })} dry-spell days`;
  if (preference === "least_heavy_rain_exposure") return `${value.toLocaleString("en-GB", { maximumFractionDigits: 5 })} heavy days / growing day`;
  return `Up to ${value} ${value === 1 ? "day" : "days"}`;
}

export function seasonLabel(years) {
  if (!years?.length) return "No common complete seasons";
  return `${years.length} complete ${years.length === 1 ? "season" : "seasons"} (${years[0]}${years.length > 1 ? `–${years.at(-1)}` : ""})`;
}

export function cropExposure(crop, preference) {
  if (preference === "closest_temperature_match") return crop?.temperature?.median_distance_c;
  if (preference === "least_dry_spell_exposure") return crop?.dry_spell?.median_longest_run_days;
  if (preference === "least_heavy_rain_exposure") return crop?.heavy_rain?.frequency;
  return null;
}

export function viewUnavailableReason(branches, preference) {
  const view = climateView(preference);
  if (!view || !branches.length) return null;
  if (branches.some((branch) => branch.metrics?.climate?.views?.[view]?.status === "ok")) return null;
  return branches.find((branch) => branch.metrics?.climate?.views?.[view]?.reason)
    ?.metrics.climate.views[view].reason ?? "No usable historical evidence for this view.";
}

export function rankGroup(group, branchesById) {
  const ranked = group.ranked.filter(({ branch_id }) => branchesById.has(branch_id));
  let rank = 0;
  return [
    ...ranked.map((entry, index) => {
      const value = entry.metric_value;
      if (!Number.isFinite(value)) return { ...entry, id: entry.branch_id, value: null, rank: null };
      if (value !== ranked[index - 1]?.metric_value) rank = index + 1;
      const tied = ranked[index - 1]?.metric_value === value || ranked[index + 1]?.metric_value === value;
      return { ...entry, id: entry.branch_id, value, rank, tied };
    }),
    ...group.unranked.filter(({ branch_id }) => branchesById.has(branch_id))
      .map((entry) => ({ ...entry, id: entry.branch_id, value: null, rank: null })),
  ];
}
