import { formatDate, rankingOptions, rotationName } from "@/lib/cycleAlgo";
import { climateView, cropExposure, rankingDescriptions, rankingValue, seasonLabel, viewUnavailableReason } from "@/lib/rotationRanking";

export function UnavailableViews({ branches }) {
  return (
    <ul className="mt-2 ml-4 list-disc text-xs leading-relaxed text-muted">
      {Object.entries(rankingOptions).map(([id, label]) => {
        const reason = viewUnavailableReason(branches, id);
        return reason ? <li key={id}>{label}: {reason}</li> : null;
      })}
    </ul>
  );
}

export function PowerSource({ sources }) {
  const power = sources?.find((source) => source.source_id === "nasa_power_daily");
  return (
    <p className="mt-3 text-xs leading-relaxed text-muted">
      {power ? (
        <>NASA POWER API history · {formatDate(power.observation_start)} to {formatDate(power.observation_end)}.
          {power.cache?.stale ? " Stale cache: history was not refreshed." : power.cache?.hit ? " Served from API cache." : " API-sourced history."}
          {power.retrieved_at && ` Retrieved ${formatDate(power.retrieved_at.slice(0, 10))}.`}
          {" "}Representative Rajshahi point/grid, not a district average or forecast.
        </>
      ) : "NASA POWER history is unavailable or its API provenance is not supplied in this response."}
    </p>
  );
}

export default function ClimateComparison({ branches, ranking }) {
  const preference = ranking.preference;
  const view = climateView(preference);
  if (!view) {
    return <p className="rounded-xl border border-line bg-white p-4 text-sm text-muted">Choose temperature match, dry-spell exposure, or heavy-rain exposure above to compare NASA weather evidence for these sequences.</p>;
  }

  return (
    <section aria-labelledby="weather-comparison-heading" className="min-w-0 space-y-3 rounded-xl border border-line bg-white p-3 sm:p-5">
      <h3 id="weather-comparison-heading" className="text-lg font-bold text-forest">NASA comparison · {rankingOptions[preference]}</h3>
      <p className="text-xs leading-relaxed text-muted">{rankingDescriptions[preference]} Groups are compared separately. These values use the higher exposure of two completion-optimized schedules, not the worst case over all possible schedules.</p>
      <div className={`grid min-w-0 gap-3 ${branches.length === 3 ? "lg:grid-cols-3" : branches.length === 2 ? "md:grid-cols-2" : ""}`}>
        {branches.map((branch, index) => {
          const group = ranking.groups[branch.status];
          const entry = group?.ranked.find((item) => item.branch_id === branch.branch_id);
          const unranked = group?.unranked.find((item) => item.branch_id === branch.branch_id);
          const tied = entry && group.ranked.filter((item) => item.metric_value === entry.metric_value).length > 1;
          const years = entry?.common_seasons ?? [];
          const reason = branch.metrics?.climate?.views?.[view]?.reason ?? unranked?.reason;
          return (
            <article key={branch.branch_id} className="min-w-0 rounded-lg bg-canvas p-3 text-xs leading-relaxed wrap-anywhere">
              <h4 className="font-bold text-forest">Sequence {index + 1} · {branch.status}</h4>
              <p className="mt-1 text-muted">{rotationName(branch)}</p>
              <p className="mt-3 text-sm font-bold text-forest">{rankingValue(entry?.metric_value, preference)}</p>
              {tied && <p className="mt-1 font-semibold text-leaf">Tied with other paths in this group</p>}
              <p className="mt-1 text-muted">{seasonLabel(years)}</p>
              {!entry && <p role="status" className="mt-2 text-muted">{reason?.replaceAll("_", " ") ?? "No comparable weather evidence. This sequence remains unranked."}</p>}
              {entry && (
                <details className="mt-2">
                  <summary className="cursor-pointer py-2 font-semibold text-leaf">Schedules, crops, and shared years</summary>
                  <p className="text-muted">Season start years: {years.join(", ")}. Missing days are not filled with zeros.</p>
                  {[
                    ["min_realization", "Shortest-completion example"],
                    ["max_realization", "Longest-completion example"],
                  ].map(([schedule, label]) => (
                    <div key={schedule} className="mt-3 border-t border-line pt-2">
                      <h5 className="font-semibold text-forest">{label}</h5>
                      <p>{rankingValue(entry.schedule_values?.[schedule], preference)}</p>
                      <ul className="mt-1 ml-4 list-disc text-muted">
                        {entry.climate?.per_schedule?.[schedule]?.per_crop?.map((crop) => (
                          <li key={crop.position}>{crop.position}. {branch.crops[crop.position - 1]?.name_en ?? crop.crop_id}: {rankingValue(cropExposure(crop, preference), preference)}</li>
                        ))}
                      </ul>
                    </div>
                  ))}
                </details>
              )}
            </article>
          );
        })}
      </div>
      <p className="text-xs leading-relaxed text-muted">No overall winner, yield prediction, or crop-damage rating. Irrigation supply, drainage, soil, and preparation still need local checks. A legume is not proof of a measured soil benefit. Different sequence durations are not annual savings, and third-to-first repeatability is unchecked.</p>
    </section>
  );
}
