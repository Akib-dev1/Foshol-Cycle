"use client";

import Link from "next/link";
import { useState } from "react";
import { CloudRain, ThermometerSun } from "lucide-react";
import { BranchStatus } from "./RotationSequence";
import { control, CycleNotice, HistoricalGrid, panel, textLink } from "./CycleLayout";
import CycleLoading from "./CycleLoading";
import ClimateComparison, { PowerSource, UnavailableViews } from "./ClimateComparison";
import { useCycleAnalysis } from "./useCycleAnalysis";
import { dateRange, formatDate, rankingOptions, rotationName, scenarioLink, waterOptions } from "@/lib/cycleAlgo";
import { viewUnavailableReason } from "@/lib/rotationRanking";

const indicators = [
  { id: "T2M", label: "Seasonal average temperature", unit: "°C", Icon: ThermometerSun, tone: "bg-sun" },
  { id: "PRECTOTCORR", label: "Seasonal rainfall total", unit: "mm", Icon: CloudRain, tone: "bg-rain" },
];

const number = new Intl.NumberFormat("en-GB", { maximumFractionDigits: 1 });

function indicatorFor(crop, id) {
  return crop.outlook?.seasonal_ranges?.indicators?.find((item) => item.variable === id);
}

function hasRange(item) {
  return [item?.min, item?.median, item?.max].every(Number.isFinite);
}

function HistoricalRange({ definition, item, domain }) {
  const { label, unit, Icon, tone } = definition;
  const available = domain && hasRange(item);
  const position = (value) => !domain || domain.max === domain.min ? 50 : 100 * (value - domain.min) / (domain.max - domain.min);

  return (
    <div className="space-y-2 rounded-xl bg-canvas p-3 text-sm">
      <h5 className="flex items-center gap-2 font-semibold text-forest"><Icon size={16} className="shrink-0 text-leaf" aria-hidden="true" />{label}</h5>
      {available ? (
        <>
          <div className="relative mx-1.5 my-3 h-2 rounded-full bg-line" aria-hidden="true">
            <span className={`absolute inset-y-0 rounded-full ${tone}`} style={{ left: `${position(item.min)}%`, right: `${100 - position(item.max)}%` }} />
            <span className="absolute top-1/2 size-3 -translate-x-1/2 -translate-y-1/2 rounded-full border-2 border-white bg-forest shadow-sm" style={{ left: `${position(item.median)}%` }} />
          </div>
          <dl className="grid grid-cols-3 gap-1 text-xs">
            {[["Min", item.min], ["Median", item.median], ["Max", item.max]].map(([statistic, value]) => (
              <div key={statistic}><dt className="text-muted">{statistic}</dt><dd className="font-semibold text-ink">{number.format(value)} {unit}</dd></div>
            ))}
          </dl>
        </>
      ) : <p className="text-xs text-muted">Historical range unavailable.</p>}
      {item && (
        <p className="text-xs leading-relaxed text-muted">
          {item.seasons_evaluated} of {item.seasons_total} seasons evaluated
          {item.seasons_excluded > 0 && ` · ${item.seasons_excluded} excluded for coverage`}
        </p>
      )}
    </div>
  );
}

function RotationHistory({ branch, index, domains }) {
  return (
    <article className={panel}>
      <BranchStatus status={branch.status} />
      <h3 className="mt-3 text-lg font-bold text-forest">Rotation {index + 1}</h3>
      <p className="mt-1 text-sm font-semibold leading-relaxed">{rotationName(branch)}</p>
      <ol className="mt-4 divide-y divide-line" aria-label="Crop growing seasons">
        {branch.crops.map((crop, cropIndex) => {
          const outlook = crop.outlook?.seasonal_ranges;
          return (
            <li className="py-4 first:pt-0 last:pb-0" key={cropIndex}>
              <h4 className="text-sm font-bold text-forest">{cropIndex + 1}. {crop.name_en}</h4>
              {outlook && (
                <p className="mt-1 text-xs leading-relaxed text-muted">
                  Crop window {dateRange({ earliest: outlook.period_start, latest: outlook.period_end })}
                </p>
              )}
              {crop.outlook?.reason && !outlook && <p className="mt-1 text-xs leading-relaxed text-muted">{crop.outlook.reason}</p>}
              <div className="mt-2 space-y-2">
                {indicators.map((definition) => (
                  <HistoricalRange key={definition.id} definition={definition} item={indicatorFor(crop, definition.id)} domain={domains[definition.id]} />
                ))}
              </div>
            </li>
          );
        })}
      </ol>
    </article>
  );
}

export default function HistoricalConditions({ scenario, branchIds }) {
  const [preference, setPreference] = useState(scenario.preference);
  const analysis = useCycleAnalysis({ ...scenario, preference });

  return (
    <section aria-labelledby="historical-ranges" className="space-y-4">
      <div className={panel}>
        <h2 id="historical-ranges" className="text-xl font-bold text-forest">Historical growing conditions</h2>
        <p className="mt-1 text-sm text-muted">Rajshahi District · {formatDate(scenario.start_date)} · {waterOptions[scenario.water_access]} · {rankingOptions[preference]}</p>
        <Link href={scenarioLink("/rotation-planner", { ...scenario, preference }, branchIds)} className={`${textLink} mt-2 inline-flex min-h-11 items-center text-sm`}>
          Back to rotation comparison
        </Link>
      </div>
      {analysis.pending && <CycleLoading key={analysis.requestKey} message="Loading historical conditions for your rotations…" variant="history" count={branchIds.length} />}
      {analysis.error && <CycleNotice error retry={analysis.retryable ? analysis.retry : undefined}>{analysis.error.message}</CycleNotice>}
      {analysis.data && <HistoricalResults data={analysis.data} branchIds={branchIds} preference={preference} onPreferenceChange={setPreference} />}
    </section>
  );
}

function HistoricalResults({ data, branchIds, preference, onPreferenceChange }) {
  const byId = new Map(data.branches.map((branch) => [branch.branch_id, branch]));
  const branches = branchIds.map((id) => byId.get(id)).filter(Boolean);
  if (!branches.length) {
    return (
      <CycleNotice>
        <p>{data.status === "data_unavailable" ? "Crop data is unavailable for this scenario." : "The selected rotations are unavailable in this run."}</p>
      </CycleNotice>
    );
  }

  const domains = Object.fromEntries(indicators.map(({ id }) => {
    const ranges = branches.flatMap((branch) => branch.crops.map((crop) => indicatorFor(crop, id))).filter(hasRange);
    return [id, ranges.length ? { min: Math.min(...ranges.map((range) => range.min)), max: Math.max(...ranges.map((range) => range.max)) } : null];
  }));
  const hasHistoricalData = Object.values(domains).some(Boolean);

  return (
    <>
      <div className={panel}>
        <p className="text-sm leading-relaxed text-muted">
          {hasHistoricalData
            ? "Each reference-window range spans the lowest to highest season value, with a dot at the median. Bars for the same measure share a scale. These full-coverage reference ranges are context, not the common-period realized-schedule scores shown in the NASA comparison."
            : "Historical NASA POWER ranges are unavailable for these rotations."}
        </p>
        <PowerSource sources={data.data_sources} />
        <label className="mt-4 grid max-w-sm gap-1.5 text-sm font-semibold text-forest">
          Comparison view
          <select className={control} value={preference} onChange={(event) => onPreferenceChange(event.target.value)}>
            {Object.entries(rankingOptions).map(([id, label]) => {
              const reason = viewUnavailableReason(data.branches, id);
              return <option key={id} value={id} disabled={Boolean(reason)} title={reason ?? undefined}>{label}{reason ? " (unavailable)" : ""}</option>;
            })}
          </select>
        </label>
        <UnavailableViews branches={data.branches} />
        {data.environment_context?.status === "unavailable" && <p className="mt-2 text-sm text-muted">SMAP soil moisture is unavailable in this run.</p>}
        {branches.length < branchIds.length && <p role="status" className="mt-2 text-sm text-muted">Some rotations from the shared comparison are unavailable in this run.</p>}
      </div>
      <ClimateComparison branches={branches} ranking={data.ranking} />
      <HistoricalGrid count={branches.length}>
        {branches.map((branch) => <RotationHistory key={branch.branch_id} branch={branch} index={branchIds.indexOf(branch.branch_id)} domains={domains} />)}
      </HistoricalGrid>
    </>
  );
}
