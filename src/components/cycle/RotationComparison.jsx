import Link from "next/link";
import { ArrowRight, ArrowUp, CalendarDays, ChevronDown, ClipboardList, X } from "lucide-react";
import { BranchStatus, rotationLetter } from "./RotationSequence";
import { textLink } from "./CycleLayout";
import { dateRange, dayRange, formatDate, rotationName, scenarioLink, waterOptions } from "@/lib/cycleAlgo";
import ClimateComparison from "./ClimateComparison";

const columns = ["", "grid-cols-1", "grid-cols-2", "grid-cols-3"];
const matrixRow = "grid min-w-0 gap-2 px-3 py-3 sm:gap-3 sm:px-5 md:grid-cols-[8.5rem_minmax(0,1fr)]";

function harvestWindow(branch) {
  const { earliest_completion_date: start, latest_completion_date: end } = branch.metrics?.completion ?? {};
  if (!start || !end || start === end) return formatDate(start);

  return (
    <span className="text-[11px] sm:text-sm">
      <time dateTime={start}>{formatDate(start)}</time>
      <span className="sr-only sm:not-sr-only"> to </span>
      <time dateTime={end} className="block text-muted sm:inline sm:text-ink">{formatDate(end)}</time>
    </span>
  );
}

const metrics = [
  ["Wait to first planting", (branch) => dayRange({ min: branch.initial_wait_days, max: branch.initial_wait_days })],
  ["First planting to final harvest", (branch) => dayRange(branch.metrics?.completion?.completion_days)],
  ["Final harvest window", harvestWindow],
  ["Distinct crop families", (branch) => branch.metrics?.diversity?.distinct_family_count ?? "Unknown"],
  ["Legume in sequence", (branch) => {
    const present = branch.metrics?.diversity?.legume_present;
    return present === true ? "Present" : present === false ? "None" : "Unknown";
  }],
];

function ComparisonOverview({ branches }) {
  const valueGrid = `grid min-w-0 gap-x-2 sm:gap-x-4 ${columns[branches.length]}`;
  return (
    <div className="min-w-0 rounded-xl border border-line bg-white">
      <div className={`${matrixRow} rounded-t-xl border-b border-line bg-[#eef3eb]`}>
        <p className="hidden self-end pb-1 text-xs font-semibold tracking-wide text-leaf uppercase md:block">Field notes</p>
        <div className={valueGrid}>
          {branches.map((branch, index) => (
            <div key={branch.branch_id} className="min-w-0 space-y-2">
              <div className="flex min-w-0 flex-wrap items-center gap-1.5 text-sm font-bold text-forest">
                <span className="grid size-7 shrink-0 place-items-center rounded-sm bg-forest text-white" aria-hidden="true">{rotationLetter(index)}</span>
                <h3 className="sr-only">Rotation {rotationLetter(index)}</h3>
                <BranchStatus status={branch.status} compact />
              </div>
              <ol aria-label={`Rotation ${rotationLetter(index)} crop sequence`} className="space-y-1.5 text-xs leading-snug text-forest sm:text-sm">
                {branch.crops.map((crop, step) => (
                  <li key={step} className="flex min-w-0 items-baseline gap-1 sm:gap-1.5">
                    <span className="shrink-0 text-[0.625rem] font-semibold text-muted" aria-hidden="true">{step + 1}</span>
                    <span className="min-w-0 font-semibold wrap-anywhere">{crop.name_en}</span>
                  </li>
                ))}
              </ol>
            </div>
          ))}
        </div>
      </div>
      <dl className="divide-y divide-line">
        {metrics.map(([label, value]) => (
          <div key={label} className={matrixRow}>
            <dt className="text-xs leading-snug font-semibold text-muted md:self-center">{label}</dt>
            <dd className={`${valueGrid} text-xs leading-snug font-semibold tabular-nums text-ink sm:text-sm`}>
              {branches.map((branch, index) => (
                <span key={branch.branch_id} className="min-w-0 wrap-anywhere">
                  <span className="sr-only">Rotation {rotationLetter(index)}: </span>{value(branch)}
                </span>
              ))}
            </dd>
          </div>
        ))}
      </dl>
    </div>
  );
}

function CropWindow({ crop, transition, letter }) {
  return (
    <div className="min-w-0 space-y-2 rounded-lg border border-line bg-white p-3 leading-relaxed wrap-anywhere">
      <p className="text-xs font-semibold text-leaf">Rotation {letter}</p>
      <p className="text-sm font-bold text-forest">{crop.name_en}</p>
      {crop.reference_variety && <p className="text-xs text-muted">{crop.reference_variety}</p>}
      <dl className="grid gap-2 text-xs">
        <div><dt className="text-muted">Planting</dt><dd className="font-semibold text-ink">{dateRange(crop.planting_range)}</dd></div>
        <div><dt className="text-muted">Harvest</dt><dd className="font-semibold text-ink">{dateRange(crop.harvest_range)}</dd></div>
      </dl>
      {transition && (
        <div className="space-y-2 border-t border-dashed border-line pt-2 text-xs text-muted">
          <p className="font-semibold text-forest">Before the next crop</p>
          <dl className="space-y-1">
            <div><dt className="inline">Field preparation: </dt><dd className="inline font-medium text-ink">{dayRange(transition.preparation_range)}</dd></div>
            <div><dt className="inline">Wait once field is ready: </dt><dd className="inline font-medium text-ink">{dayRange(transition.waiting_range)}</dd></div>
            <div><dt className="inline">Harvest to next planting window: </dt><dd className="inline font-medium text-ink">{dayRange(transition.harvest_to_next_window_days)}</dd></div>
          </dl>
          {transition.window_only_gap && <p className="text-[#735020]">This calendar gap does not establish how long field preparation takes.</p>}
        </div>
      )}
    </div>
  );
}

function ComparisonCalendar({ branches }) {
  return (
    <details className="group min-w-0 rounded-xl border border-line bg-white px-3 sm:px-5">
      <summary className="flex min-h-12 cursor-pointer list-none items-center gap-2 py-2 text-sm font-semibold text-forest [&::-webkit-details-marker]:hidden">
        <CalendarDays size={17} className="shrink-0 text-leaf" aria-hidden="true" /> Planting and harvest calendar
        <ChevronDown size={16} className="ml-auto shrink-0 group-open:rotate-180" aria-hidden="true" />
      </summary>
      <ol className="divide-y divide-line border-t border-line">
        {branches[0].crops.map((_, step) => (
          <li key={step} className="py-3">
            <h3 className="mb-2 text-sm font-bold text-forest">Crop {step + 1}</h3>
            <div className={`grid min-w-0 gap-2 sm:gap-3 ${branches.length === 3 ? "sm:grid-cols-3" : branches.length === 2 ? "sm:grid-cols-2" : ""}`}>
              {branches.map((branch, index) => (
                <CropWindow key={branch.branch_id} crop={branch.crops[step]} transition={branch.transitions[step]} letter={rotationLetter(index)} />
              ))}
            </div>
          </li>
        ))}
      </ol>
    </details>
  );
}

function ComparisonChecks({ branches, onRemove }) {
  return (
    <div className={`grid min-w-0 gap-2 ${branches.length === 3 ? "md:grid-cols-3" : branches.length === 2 ? "sm:grid-cols-2" : ""}`}>
      {branches.map((branch, index) => {
        const letter = rotationLetter(index);
        const cautions = [...new Set([...(branch.cautions ?? []), ...(branch.reasons ?? [])])];
        return (
          <article key={branch.branch_id} className="min-w-0 rounded-xl border border-line bg-white px-3 text-xs leading-relaxed wrap-anywhere text-muted sm:px-4">
            <div className="flex min-w-0 items-center justify-between gap-2">
              <h3 className="font-bold text-forest">Rotation {letter}</h3>
              <button type="button" aria-label={`Remove rotation ${letter}: ${rotationName(branch)}`} onClick={() => onRemove(branch.branch_id)} className="inline-flex min-h-11 shrink-0 cursor-pointer items-center gap-1 px-1 font-semibold text-leaf hover:underline">
                <X size={14} aria-hidden="true" /> Remove
              </button>
            </div>
            <details className="border-t border-line">
              <summary className="min-h-11 cursor-pointer py-3 font-semibold text-leaf">Evidence gaps and cautions</summary>
              {branch.missing_evidence?.length > 0 && (
                <p className="pb-2"><strong className="text-ink">Still needed:</strong> {branch.missing_evidence.map((id) => id.replaceAll("_", " ").replace(/\bph\b/g, "pH")).join(", ")}</p>
              )}
              {cautions.length > 0 ? (
                <ul className="ml-4 list-disc space-y-1 pb-3">
                  {cautions.map((caution) => <li key={caution}>{caution}</li>)}
                </ul>
              ) : !branch.missing_evidence?.length && <p className="pb-3">No additional cautions recorded for this sequence.</p>}
            </details>
          </article>
        );
      })}
    </div>
  );
}

export default function RotationComparison({ branches, scenario, data, onRemove }) {
  return (
    <section aria-labelledby="rotation-comparison" className="min-w-0 space-y-3 rounded-2xl border border-line bg-[#eef3eb] p-2 sm:p-3">
      <header className="min-w-0 rounded-xl bg-forest p-4 text-white sm:p-5">
        <p className="flex items-center gap-2 text-xs font-semibold tracking-wide text-mist uppercase">
          <ClipboardList size={16} aria-hidden="true" /> Rajshahi field plan
        </p>
        <h2 id="rotation-comparison" className="mt-2 scroll-mt-24 text-2xl font-bold tracking-tight">Compare rotations</h2>
        <p className="mt-2 flex min-w-0 flex-wrap items-center gap-x-4 gap-y-1 text-xs leading-relaxed text-mist sm:text-sm">
          <span>Start date: {formatDate(scenario.start_date)}</span>
          <span>{waterOptions[scenario.water_access]}</span>
        </p>
      </header>
      <ComparisonOverview branches={branches} />
      <ClimateComparison branches={branches} ranking={data.ranking} />
      <ComparisonCalendar branches={branches} />
      <ComparisonChecks branches={branches} onRemove={onRemove} />
      <div className="flex min-w-0 flex-wrap items-center justify-between gap-x-4 px-2 py-1 text-sm sm:px-3">
        <a href="#rotation-results" className={`${textLink} inline-flex min-h-11 items-center gap-1.5`}>
          <ArrowUp size={16} aria-hidden="true" /> Back to rotation options
        </a>
        <Link href={scenarioLink("/risk-uncertainty", scenario, branches.map((branch) => branch.branch_id))} className={`${textLink} inline-flex min-h-11 items-center gap-1.5`}>
          View historical conditions <ArrowRight size={16} className="shrink-0" aria-hidden="true" />
        </Link>
      </div>
    </section>
  );
}
