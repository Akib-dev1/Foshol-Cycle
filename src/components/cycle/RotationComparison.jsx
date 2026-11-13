import Link from "next/link";
import { ArrowRight, ArrowUp, CalendarDays, ChevronDown, ClipboardList, X } from "lucide-react";
import { BranchStatus, rotationLetter } from "./RotationSequence";
import { textLink } from "./CycleLayout";
import { useCycleLanguage } from "./CycleLanguage";
import { CropName, EngineMessage } from "./LocalizedCycleData";
import { dateRange, dayRange, formatDate, rotationName, scenarioLink, waterOptions } from "@/lib/cycleAlgo";
import ClimateComparison from "./ClimateComparison";

const columns = ["", "grid-cols-1", "grid-cols-2", "grid-cols-3"];
const matrixRow = "grid min-w-0 gap-2 px-3 py-3 sm:gap-3 sm:px-5 md:grid-cols-[8.5rem_minmax(0,1fr)]";

function harvestWindow(branch, locale) {
  const { earliest_completion_date: start, latest_completion_date: end } = branch.metrics?.completion ?? {};
  if (!start || !end || start === end) return formatDate(start, locale);

  return (
    <span className="text-[11px] sm:text-sm">
      <time dateTime={start}>{formatDate(start, locale)}</time>
      <span className="sr-only sm:not-sr-only">{locale.t(" to ")}</span>
      <time dateTime={end} className="block text-muted sm:inline sm:text-ink">{formatDate(end, locale)}</time>
    </span>
  );
}

const metrics = [
  ["Wait to first planting", (branch, locale) => dayRange({ min: branch.initial_wait_days, max: branch.initial_wait_days }, locale)],
  ["First planting to final harvest", (branch, locale) => dayRange(branch.metrics?.completion?.completion_days, locale)],
  ["Final harvest window", harvestWindow],
  ["Distinct crop families", (branch, { t, number }) => {
    const count = branch.metrics?.diversity?.distinct_family_count;
    return Number.isFinite(count) ? number(count) : t("Unknown");
  }],
  ["Legume in sequence", (branch, { t }) => {
    const present = branch.metrics?.diversity?.legume_present;
    return t(present === true ? "Present" : present === false ? "None" : "Unknown");
  }],
];

function ComparisonOverview({ branches }) {
  const locale = useCycleLanguage();
  const { language, t, number } = locale;
  const valueGrid = `grid min-w-0 gap-x-2 sm:gap-x-4 ${columns[branches.length]}`;
  return (
    <div className="min-w-0 rounded-xl border border-line bg-white">
      <div className={`${matrixRow} rounded-t-xl border-b border-line bg-[#eef3eb]`}>
        <p className="hidden self-end pb-1 text-xs font-semibold tracking-wide text-leaf uppercase md:block">{t("Field notes")}</p>
        <div className={valueGrid}>
          {branches.map((branch, index) => (
            <div key={branch.branch_id} className="min-w-0 space-y-2">
              <div className="flex min-w-0 flex-wrap items-center gap-1.5 text-sm font-bold text-forest">
                <span className="grid size-7 shrink-0 place-items-center rounded-sm bg-forest text-white" aria-hidden="true">{rotationLetter(index, language)}</span>
                <h3 className="sr-only">{t("Rotation {id}", { id: rotationLetter(index, language) })}</h3>
                <BranchStatus status={branch.status} compact />
              </div>
              <ol aria-label={t("Rotation {id} crop sequence", { id: rotationLetter(index, language) })} className="space-y-1.5 text-xs leading-snug text-forest sm:text-sm">
                {branch.crops.map((crop, step) => (
                  <li key={step} className="flex min-w-0 items-baseline gap-1 sm:gap-1.5">
                    <span className="shrink-0 text-[0.625rem] font-semibold text-muted" aria-hidden="true">{number(step + 1)}</span>
                    <span className="min-w-0 font-semibold wrap-anywhere"><CropName crop={crop} /></span>
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
            <dt className="text-xs leading-snug font-semibold text-muted md:self-center">{t(label)}</dt>
            <dd className={`${valueGrid} text-xs leading-snug font-semibold tabular-nums text-ink sm:text-sm`}>
              {branches.map((branch, index) => (
                <span key={branch.branch_id} className="min-w-0 wrap-anywhere">
                  <span className="sr-only">{t("Rotation {id}", { id: rotationLetter(index, language) })}: </span>{value(branch, locale)}
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
  const locale = useCycleLanguage();
  const { t } = locale;

  return (
    <div className="min-w-0 space-y-2 rounded-lg border border-line bg-white p-3 leading-relaxed wrap-anywhere">
      <p className="text-xs font-semibold text-leaf">{t("Rotation {id}", { id: letter })}</p>
      <p className="text-sm font-bold text-forest"><CropName crop={crop} /></p>
      {crop.reference_variety && <p lang="en" className="text-xs text-muted">{crop.reference_variety}</p>}
      <dl className="grid gap-2 text-xs">
        <div><dt className="text-muted">{t("Planting")}</dt><dd className="font-semibold text-ink">{dateRange(crop.planting_range, locale)}</dd></div>
        <div><dt className="text-muted">{t("Harvest")}</dt><dd className="font-semibold text-ink">{dateRange(crop.harvest_range, locale)}</dd></div>
      </dl>
      {transition && (
        <div className="space-y-2 border-t border-dashed border-line pt-2 text-xs text-muted">
          <p className="font-semibold text-forest">{t("Before the next crop")}</p>
          <dl className="space-y-1">
            <div><dt className="inline">{t("Field preparation")}: </dt><dd className="inline font-medium text-ink">{dayRange(transition.preparation_range, locale)}</dd></div>
            <div><dt className="inline">{t("Wait once field is ready")}: </dt><dd className="inline font-medium text-ink">{dayRange(transition.waiting_range, locale)}</dd></div>
            <div><dt className="inline">{t("Harvest to next planting window")}: </dt><dd className="inline font-medium text-ink">{dayRange(transition.harvest_to_next_window_days, locale)}</dd></div>
          </dl>
          {transition.window_only_gap && <p className="text-[#735020]">{t("This calendar gap does not establish how long field preparation takes.")}</p>}
        </div>
      )}
    </div>
  );
}

function ComparisonCalendar({ branches }) {
  const { language, t } = useCycleLanguage();

  return (
    <details className="group min-w-0 rounded-xl border border-line bg-white px-3 sm:px-5">
      <summary className="flex min-h-12 cursor-pointer list-none items-center gap-2 py-2 text-sm font-semibold text-forest [&::-webkit-details-marker]:hidden">
        <CalendarDays size={17} className="shrink-0 text-leaf" aria-hidden="true" /> {t("Planting and harvest calendar")}
        <ChevronDown size={16} className="ml-auto shrink-0 group-open:rotate-180" aria-hidden="true" />
      </summary>
      <ol className="divide-y divide-line border-t border-line">
        {branches[0].crops.map((_, step) => (
          <li key={step} className="py-3">
            <h3 className="mb-2 text-sm font-bold text-forest">{t("Crop {id}", { id: step + 1 })}</h3>
            <div className={`grid min-w-0 gap-2 sm:gap-3 ${branches.length === 3 ? "sm:grid-cols-3" : branches.length === 2 ? "sm:grid-cols-2" : ""}`}>
              {branches.map((branch, index) => (
                <CropWindow key={branch.branch_id} crop={branch.crops[step]} transition={branch.transitions[step]} letter={rotationLetter(index, language)} />
              ))}
            </div>
          </li>
        ))}
      </ol>
    </details>
  );
}

function ComparisonChecks({ branches, onRemove }) {
  const locale = useCycleLanguage();
  const { language, t } = locale;

  return (
    <div className={`grid min-w-0 gap-2 ${branches.length === 3 ? "md:grid-cols-3" : branches.length === 2 ? "sm:grid-cols-2" : ""}`}>
      {branches.map((branch, index) => {
        const letter = rotationLetter(index, language);
        const rotation = rotationName(branch, locale);
        const cautions = [...new Set([...(branch.cautions ?? []), ...(branch.reasons ?? [])])];
        return (
          <article key={branch.branch_id} className="min-w-0 rounded-xl border border-line bg-white px-3 text-xs leading-relaxed wrap-anywhere text-muted sm:px-4">
            <div className="flex min-w-0 items-center justify-between gap-2">
              <h3 className="font-bold text-forest">{t("Rotation {id}", { id: letter })}</h3>
              <button type="button" aria-label={t("Remove rotation {id}: {rotation}", { id: letter, rotation })} onClick={() => onRemove(branch.branch_id)} className="inline-flex min-h-11 shrink-0 cursor-pointer items-center gap-1 px-1 font-semibold text-leaf hover:underline">
                <X size={14} aria-hidden="true" /> {t("Remove")}
              </button>
            </div>
            <details className="border-t border-line">
              <summary className="min-h-11 cursor-pointer py-3 font-semibold text-leaf">{t("Evidence gaps and cautions")}</summary>
              {branch.missing_evidence?.length > 0 && (
                <p className="pb-2"><strong className="text-ink">{t("Still needed")}:</strong> {branch.missing_evidence.map((id, index) => (
                  <span key={id}>{index > 0 && ", "}<EngineMessage message={id} humanize /></span>
                ))}</p>
              )}
              {cautions.length > 0 ? (
                <ul className="ml-4 list-disc space-y-1 pb-3">
                  {cautions.map((caution) => <li key={caution}><EngineMessage message={caution} /></li>)}
                </ul>
              ) : !branch.missing_evidence?.length && <p className="pb-3">{t("No additional cautions recorded for this sequence.")}</p>}
            </details>
          </article>
        );
      })}
    </div>
  );
}

export default function RotationComparison({ branches, scenario, data, onRemove }) {
  const locale = useCycleLanguage();
  const { language, t } = locale;

  return (
    <section aria-labelledby="rotation-comparison" className="min-w-0 space-y-3 rounded-2xl border border-line bg-[#eef3eb] p-2 sm:p-3">
      <header className="min-w-0 rounded-xl bg-forest p-4 text-white sm:p-5">
        <p className="flex items-center gap-2 text-xs font-semibold tracking-wide text-mist uppercase">
          <ClipboardList size={16} aria-hidden="true" /> {t("Rajshahi field plan")}
        </p>
        <h2 id="rotation-comparison" className="mt-2 scroll-mt-24 text-2xl font-bold tracking-tight">{t("Compare rotations")}</h2>
        <p className="mt-2 flex min-w-0 flex-wrap items-center gap-x-4 gap-y-1 text-xs leading-relaxed text-mist sm:text-sm">
          <span>{t("Start date")}: {formatDate(scenario.start_date, locale)}</span>
          <span>{t(waterOptions[scenario.water_access])}</span>
        </p>
      </header>
      <ComparisonOverview branches={branches} />
      <ClimateComparison branches={branches} ranking={data.ranking} />
      <ComparisonCalendar branches={branches} />
      <ComparisonChecks branches={branches} onRemove={onRemove} />
      <div className="flex min-w-0 flex-wrap items-center justify-between gap-x-4 px-2 py-1 text-sm sm:px-3">
        <a href="#rotation-results" className={`${textLink} inline-flex min-h-11 items-center gap-1.5`}>
          <ArrowUp size={16} aria-hidden="true" /> {t("Back to rotation options")}
        </a>
        <Link href={scenarioLink("/risk-uncertainty", scenario, branches.map((branch) => branch.branch_id), language)} className={`${textLink} inline-flex min-h-11 items-center gap-1.5`}>
          {t("View historical conditions")} <ArrowRight size={16} className="shrink-0" aria-hidden="true" />
        </Link>
      </div>
    </section>
  );
}
