export function weatherResponse(preference = "least_dry_spell_exposure") {
  const branches = ["z", "a", "b", "unknown"].map((id) => ({
    branch_id: id,
    status: "conditional",
    crops: [1, 2, 3].map((position) => ({ crop_id: `crop_${position}`, name_en: `Crop ${position}`, position })),
    transitions: [{}, {}],
    metrics: {
      diversity: { distinct_family_count: 99 },
      climate: {
        views: {
          temperature: { status: "unavailable", reason: "T2M units unavailable" },
          rain: { status: "ok" },
        },
        summary: { min_realization: { dry_spell_days: 999 } },
      },
    },
  }));
  return {
    schema_version: "1",
    status: "partial",
    district: { district_id: "rajshahi" },
    request: {
      district_id: "rajshahi", start_date: "2026-11-06", first_crop_id: "crop_1",
      water_access: "unknown", preference,
    },
    crop_options: [{ crop_id: "crop_1", name_en: "Crop 1", shown: true }],
    branches,
    branch_summary: { conditional_count: 4 },
    ranking: {
      preference,
      direction: "ascending",
      groups: {
        candidate: { ranked: [], unranked: [] },
        conditional: {
          ranked: [
            { branch_id: "z", metric_value: 0, common_seasons: [1991, 1993] },
            { branch_id: "a", metric_value: 0, common_seasons: [1991, 1993] },
            { branch_id: "b", metric_value: 5, common_seasons: [1991, 1993] },
          ],
          unranked: [{ branch_id: "unknown", metric_value: null, reason: "CLIMATE_EVIDENCE_MISSING" }],
        },
      },
    },
  };
}
