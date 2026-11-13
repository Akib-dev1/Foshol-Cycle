import { useState } from "react";
import { ArrowDown, ArrowDownUp, Check, ChevronDown, ClipboardList, Plus } from "lucide-react";
import RotationSequence, { rotationLetter } from "./RotationSequence";
import { control, textLink } from "./CycleLayout";
import { useCycleLanguage } from "./CycleLanguage";
import { EngineMessage } from "./LocalizedCycleData";
import { dayRange, MAX_COMPARISONS, rankingOptions, rotationName } from "@/lib/cycleAlgo";
import { climateView, rankGroup, rankingDescriptions, rankingValue, seasonLabel, viewUnavailableReason } from "@/lib/rotationRanking";
import { PowerSource, UnavailableViews } from "./ClimateComparison";

const PAGE_SIZE = 6;

function RankingGroup({ type, group, branchesById, preference, selectedIds, onToggle, commonSeasons }) {
  const locale = useCycleLanguage();
  const { language, t, number } = locale;
  const [visibleCount, setVisibleCount] = useState(PAGE_SIZE);
  const entries = rankGroup(group, branchesById);
  if (!entries.length) return null;

  const conditional = type === "conditional";
  const label = t(conditional ? "Conditional rotations" : "Candidate rotations");
  return (
    <section aria-labelledby={`${type}-rotations`} className={`min-w-0 rounded-2xl border ${conditional ? "border-[#e3d5b6] bg-[#faf6ed]" : "border-line bg-[#edf3eb]"}`}>
      <header className="flex items-start gap-3 px-3 py-4 sm:px-5">
        <span className={`grid size-9 shrink-0 place-items-center rounded-lg ${conditional ? "bg-[#efe4ca] text-[#735020]" : "bg-[#dce9dc] text-forest"}`}>
          <ClipboardList size={18} aria-hidden="true" />
        </span>
        <div className="min-w-0">
          <h3 id={`${type}-rotations`} className="flex flex-wrap items-baseline gap-x-2 text-base font-bold text-forest">
            {label} <span className="text-xs font-medium tabular-nums text-muted">{t("{count} sequences", { count: entries.length })}</span>
          </h3>
          <p className="text-xs leading-relaxed text-muted">{t(conditional ? "These sequences have checks to resolve before planting." : "These sequences passed the checks available for this scenario.")}</p>
          {climateView(preference) && <p className="mt-1 text-xs text-muted">{seasonLabel(commonSeasons, locale)} · {t("Only paths within this group are compared.")}</p>}
        </div>
      </header>

      <ul className="grid gap-2 px-2 pb-2 sm:px-3 sm:pb-3">
        {entries.slice(0, visibleCount).map(({ id, value, rank, tied, reason }) => {
          const branch = branchesById.get(id);
          const selectedIndex = selectedIds.indexOf(id);
          const selected = selectedIndex !== -1;
          const openChecks = branch.missing_evidence?.length ?? 0;
          const rotation = rotationName(branch, locale);

          return (
            <li key={id} className={`grid min-w-0 gap-2.5 rounded-xl border bg-white p-2.5 sm:p-3 lg:grid-cols-[minmax(0,1fr)_9.5rem] lg:items-center lg:gap-x-4 ${selected ? "border-agriculture/75" : "border-line"}`}>
              <div className="flex min-w-0 flex-wrap items-center gap-x-2 gap-y-1 lg:col-start-1">
                <span className="rounded bg-canvas px-1.5 py-0.5 text-xs font-semibold tabular-nums text-muted">
                  {rank === null ? t("Unranked") : <><span className="sr-only">{t("Rank")} </span>#{number(rank)}{tied && <> · {t("tied")}</>}</>}
                </span>
                <span className="min-w-0 text-xs font-semibold wrap-anywhere text-forest">{rankingValue(value, preference, locale)}</span>
                {rank === null && reason && <span className="text-xs text-muted"><EngineMessage message={reason} humanize /></span>}
              </div>
              <div className="lg:col-start-1"><RotationSequence crops={branch.crops} /></div>
              <div className="flex min-w-0 flex-wrap items-center gap-x-4 gap-y-1 text-xs leading-relaxed text-muted lg:col-start-1">
                <span>{t("First planting wait")}: {dayRange({ min: branch.initial_wait_days, max: branch.initial_wait_days }, locale)}</span>
                <span>{t("Planting to final harvest")}: {dayRange(branch.metrics?.completion?.completion_days, locale)}</span>
                {conditional && openChecks > 0 && (
                  <span className="font-medium text-[#735020]">{t(openChecks === 1 ? "{count} evidence gap" : "{count} evidence gaps", { count: openChecks })}</span>
                )}
              </div>
              <button
                type="button"
                aria-label={t(rank === null ? "Compare {rotation}" : "Compare {rotation}, rank {rank}", { rotation, rank })}
                aria-pressed={selected}
                disabled={!selected && selectedIds.length >= MAX_COMPARISONS}
                onClick={() => onToggle(id)}
                className="inline-flex min-h-11 w-full cursor-pointer items-center justify-center gap-1.5 rounded-lg border border-line px-2 text-sm font-semibold text-leaf hover:bg-canvas aria-pressed:border-agriculture/50 aria-pressed:bg-mist disabled:cursor-default disabled:opacity-45 sm:w-fit sm:px-3 lg:col-start-2 lg:row-start-1 lg:row-span-3 lg:w-full"
              >
                {selected ? <Check size={16} aria-hidden="true" /> : <Plus size={16} aria-hidden="true" />}
                {selected ? t("Rotation {id}", { id: rotationLetter(selectedIndex, language) }) : t("Compare")}
              </button>
            </li>
          );
        })}
      </ul>
      {visibleCount < entries.length && (
        <button type="button" className="mx-3 mb-3 inline-flex min-h-11 cursor-pointer items-center gap-2 rounded-lg px-2 text-sm font-semibold text-leaf hover:underline" onClick={() => setVisibleCount((count) => count + PAGE_SIZE)}>
          <ChevronDown size={16} aria-hidden="true" /> {t(conditional ? "Show more conditional rotations ({count})" : "Show more candidate rotations ({count})", { count: entries.length - visibleCount })}
        </button>
      )}
    </section>
  );
}

export default function RotationResults({ data, preference, onRankChange, selectedIds, onToggle }) {
  const { t } = useCycleLanguage();
  const { branches, branch_summary: summary, ranking, warnings } = data;
  const branchesById = new Map(branches.map((branch) => [branch.branch_id, branch]));
  const notes = ranking.notes;
  const unavailable = viewUnavailableReason(branches, preference);

  return (
    <section aria-labelledby="rotation-results" className="min-w-0 space-y-4">
      <div>
        <h2 id="rotation-results" className="scroll-mt-24 text-2xl font-bold tracking-tight text-forest">{t("Rotation options")}</h2>
        <p role="status" className="mt-1 text-sm leading-relaxed wrap-anywhere text-muted"><EngineMessage message={summary.message} /></p>
      </div>
      {branches.length > 0 && (
        <div className="min-w-0 rounded-xl border border-line bg-white p-3 sm:p-4">
          <div className="grid min-w-0 items-start gap-3 md:grid-cols-[minmax(0,18rem)_minmax(0,1fr)] md:items-center md:gap-5">
            <label className="grid min-w-0 gap-1.5 text-sm font-semibold text-forest">
              <span className="flex items-center gap-1.5"><ArrowDownUp size={15} aria-hidden="true" /> {t("Rank by")}</span>
              <select value={preference} onChange={(event) => onRankChange(event.target.value)} aria-describedby="rotation-rank-basis" className={control}>
                {Object.entries(rankingOptions).map(([id, label]) => {
                  const reason = viewUnavailableReason(branches, id);
                  return <option key={id} value={id} disabled={Boolean(reason)}>{t(label)}{reason && t(" (unavailable)")}</option>;
                })}
                <option disabled>{t("Lowest production cost (unavailable)")}</option>
                <option disabled>{t("Highest net return (unavailable)")}</option>
                <option disabled>{t("Least irrigation dependence (unavailable)")}</option>
                <option disabled>{t("Measured soil health (unavailable)")}</option>
              </select>
            </label>
            <p id="rotation-rank-basis" className="min-w-0 text-xs leading-relaxed wrap-anywhere text-muted" aria-live="polite">{t(rankingDescriptions[preference])}</p>
          </div>
          {unavailable && <p role="status" className="mt-2 text-xs text-muted"><EngineMessage message={unavailable} /></p>}
          {climateView(preference) && <p className="mt-3 text-xs leading-relaxed text-muted">{t("The higher exposure of two completion-optimized example schedules is compared, not the worst case over every possible schedule. No overall winner or crop-damage prediction is implied.")}</p>}
          <PowerSource sources={data.data_sources} />
          <details className="mt-2 text-xs leading-relaxed wrap-anywhere text-muted">
            <summary className="w-fit cursor-pointer py-2 font-semibold text-leaf">{t("What data is missing?")}</summary>
            <p>{t("The pilot lacks comparable crop production costs, irrigation requirements, and field measurements of soil health. Water access changes checks and cautions; it does not establish a validated irrigation-based ordering. Legume presence is descriptive, not a measured soil-health benefit.")}</p>
            <UnavailableViews branches={branches} />
          </details>
        </div>
      )}
      {branches.length > 0 && (
        <div className="flex min-w-0 flex-wrap items-center justify-between gap-x-4 rounded-lg border border-line bg-mist/65 px-3 py-1.5 text-sm text-forest sm:px-4">
          <p className="py-2 font-semibold" aria-live="polite">{t("{selected} of {max} selected", { selected: selectedIds.length, max: MAX_COMPARISONS })}</p>
          {selectedIds.length > 0 ? (
            <a href="#rotation-comparison" className={`${textLink} inline-flex min-h-11 items-center gap-1.5`}>
              {t("View comparison")} <ArrowDown size={15} aria-hidden="true" />
            </a>
          ) : <p className="pb-2 text-xs text-muted sm:py-2">{t("Pick up to three sequences to compare.")}</p>}
        </div>
      )}
      {["candidate", "conditional"].map((type) => (
        <RankingGroup key={`${type}-${preference}`} type={type} group={ranking.groups[type]} branchesById={branchesById} preference={preference} selectedIds={selectedIds} onToggle={onToggle} commonSeasons={ranking.climate?.common_seasons?.[type]} />
      ))}
      {(notes?.length > 0 || warnings?.length > 0) && (
        <details className="rounded-xl border border-line bg-white px-3 py-2 text-sm leading-relaxed wrap-anywhere text-muted sm:px-4">
          <summary className="cursor-pointer py-2 font-semibold text-leaf">{t("Ranking notes and data warnings")}</summary>
          <ul className="mb-2 ml-4 list-disc space-y-1">
            {notes?.map((note) => <li key={note}><EngineMessage message={note} /></li>)}
            {warnings?.map((warning) => <li key={warning.code}><EngineMessage message={warning.message} code={warning.code} /></li>)}
          </ul>
        </details>
      )}
    </section>
  );
}
