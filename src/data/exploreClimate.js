import { rajshahiPreview } from "./homePreview";

export function getExploreClimate(district, latitude, longitude) {
  // District IDs keep sample values stable when the pin moves within a district.
  const seed = [...district.id].reduce((hash, character) => Math.imul(hash, 31) + character.charCodeAt(0), 0) >>> 0;
  const metrics = district.name === "Rajshahi"
    ? {
        averageTemperatureC: rajshahiPreview.averageTemperature,
        annualRainfallMm: rajshahiPreview.monthlyRainfall.reduce((total, { millimeters }) => total + millimeters, 0),
        soilMoistureM3M3: 0.24,
        vegetationNdvi: 0.62,
      }
    : {
        averageTemperatureC: (242 + seed % 39) / 10,
        annualRainfallMm: 1320 + seed % 231 * 10,
        soilMoistureM3M3: (19 + seed % 19) / 100,
        vegetationNdvi: (48 + seed % 30) / 100,
      };

  return {
    districtId: district.id,
    districtName: district.name,
    latitude,
    longitude,
    metrics,
    source: "demo",
  };
}
