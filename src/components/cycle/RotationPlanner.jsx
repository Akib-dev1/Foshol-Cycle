"use client";

import { useState } from "react";
import { CalendarDays } from "lucide-react";
import { control, CycleNotice, panel } from "./CycleLayout";
import CycleLoading from "./CycleLoading";
import { useCycleLanguage } from "./CycleLanguage";
import { EngineMessage } from "./LocalizedCycleData";
import RotationComparison from "./RotationComparison";
import { BranchStatus } from "./RotationSequence";
import RotationResults from "./RotationResults";
import { useCycleAnalysis } from "./useCycleAnalysis";
import { dayRange, formatDate, isPlanningDate, MAX_COMPARISONS, MIN_START_DATE, MAX_START_DATE, waterOptions } from "@/lib/cycleAlgo";

function SelectField({ label, options, value, onChange }) {
  return (
    <label className="grid min-w-0 gap-1.5 text-sm font-semibold text-forest">
      {label}
      <select value={value} onChange={(event) => onChange(event.target.value)} className={control}>
        {options.map(({ id, text, lang }) => <option key={id} value={id} lang={lang}>{text}</option>)}
      </select>
    </label>
  );
}

export default function RotationPlanner({ initialScenario, initialBranches }) {
  const locale = useCycleLanguage();
  const { t, cropName } = locale;
  const [scenario, setScenario] = useState(initialScenario);
  const [comparisonIds, setComparisonIds] = useState(initialBranches);
  const dateValid = isPlanningDate(scenario.start_date);
  const discovery = useCycleAnalysis(dateValid ? { ...scenario, first_crop_id: null, preference: "fastest_completion" } : null);
  const crops = discovery.data?.crop_options.filter((crop) => crop.shown) ?? [];
  const firstCrop = crops.find((crop) => crop.crop_id === scenario.first_crop_id);
  const analysis = useCycleAnalysis(firstCrop ? scenario : null);
  const branchesById = new Map(analysis.data?.branches.map((branch) => [branch.branch_id, branch]));
  const comparison = comparisonIds.map((id) => branchesById.get(id)).filter(Boolean);
  const staleComparison = Boolean(analysis.data && comparisonIds.length !== comparison.length);

  function changeScenario(field, value, resetCrop = false) {
    setScenario((current) => ({ ...current, ...(resetCrop ? { first_crop_id: null } : {}), [field]: value }));
    setComparisonIds([]);
  }

  function toggleComparison(id) {
    setComparisonIds((previous) => {
      const available = previous.filter((branchId) => branchesById.has(branchId));
      if (available.includes(id)) return available.filter((branchId) => branchId !== id);
      return available.length < MAX_COMPARISONS ? [...available, id] : available;
    });
  }

  return (
    <div className="space-y-6">
      <section className={panel} aria-labelledby="scenario-heading">
        <div className="flex items-center gap-3">
          <span className="grid size-10 shrink-0 place-items-center rounded-xl bg-mist text-leaf"><CalendarDays size={19} aria-hidden="true" /></span>
          <div>
            <h2 id="scenario-heading" className="text-lg font-bold text-forest">{t("Planning scenario")}</h2>
            <p className="text-sm text-muted">{t("Rajshahi District")}</p>
          </div>
        </div>
        <div className="mt-5 grid gap-4 md:grid-cols-2">
          <label className="grid min-w-0 gap-1.5 text-sm font-semibold text-forest">
            {t("Start date")}
            <input
              type="date"
              min={MIN_START_DATE}
              max={MAX_START_DATE}
              className={control}
              value={scenario.start_date}
              aria-invalid={!dateValid || discovery.error?.field === "start_date"}
              aria-describedby={!dateValid ? "start-date-error" : undefined}
              onInput={(event) => changeScenario("start_date", event.currentTarget.value, true)}
              required
            />
          </label>
          <SelectField label={t("Water access")} options={Object.entries(waterOptions).map(([id, label]) => ({ id, text: t(label) }))} value={scenario.water_access} onChange={(value) => changeScenario("water_access", value, true)} />
        </div>
        {!dateValid && <p id="start-date-error" role="alert" className="mt-3 text-sm font-medium text-[#933d35]">{t("Choose a valid start date between {min} and {max}.", { min: formatDate(MIN_START_DATE, locale), max: formatDate(MAX_START_DATE, locale) })}</p>}
      </section>

      {discovery.pending && <CycleLoading key={discovery.requestKey} message="Finding first crops for this scenario…" variant="picker" />}
      {discovery.error && <CycleNotice error retry={discovery.retryable ? discovery.retry : undefined}><EngineMessage message={discovery.error.message} code={discovery.error.code} /></CycleNotice>}
      {discovery.data && (crops.length ? (
        <section className={panel} aria-labelledby="first-crop-heading">
          <h2 id="first-crop-heading" className="text-lg font-bold text-forest">{t("Choose the first crop")}</h2>
          <div className="mt-3 grid items-start gap-4 md:grid-cols-2">
            <SelectField
              label={t("First crop")}
              value={firstCrop?.crop_id ?? ""}
              options={[{ id: "", text: t("Select a crop") }, ...crops.map((crop) => {
                const { text, lang } = cropName(crop);
                return { id: crop.crop_id, lang, text: crop.reference_variety ? `${text} · ${crop.reference_variety}` : text };
              })]}
              onChange={(value) => changeScenario("first_crop_id", value || null)}
            />
            <div className="min-w-0 text-sm leading-relaxed wrap-anywhere text-muted">
              {firstCrop ? (
                <>
                  <BranchStatus status={firstCrop.status} />
                  <p className="mt-2">{t("Initial wait")} · <strong className="text-ink">{dayRange({ min: firstCrop.initial_wait_days, max: firstCrop.initial_wait_days }, locale)}</strong></p>
                  {firstCrop.checks?.water?.reason && <p className="mt-1"><EngineMessage message={firstCrop.checks.water.reason} code={firstCrop.checks.water.code} /></p>}
                </>
              ) : <p>{t("Choose a crop to see the planting and harvest windows for the full rotation.")}</p>}
              {scenario.first_crop_id && !firstCrop && <p role="status" className="mt-2">{t("The crop from the shared scenario is unavailable. Choose another first crop.")}</p>}
            </div>
          </div>
        </section>
      ) : (
        <CycleNotice>{discovery.data.status === "data_unavailable"
          ? t("Crop profiles are unavailable for this scenario.")
          : discovery.data.branch_summary.message
            ? <EngineMessage message={discovery.data.branch_summary.message} />
            : t("No supported crop options for this scenario.")}</CycleNotice>
      ))}

      {analysis.pending && <CycleLoading key={analysis.requestKey} message="Evaluating rotations and historical growing conditions…" variant="rotations" />}
      {analysis.error && <CycleNotice error retry={analysis.retryable ? analysis.retry : undefined}><EngineMessage message={analysis.error.message} code={analysis.error.code} /></CycleNotice>}
      {staleComparison && <CycleNotice>{t("Some rotations from the shared comparison are unavailable in this run.")}</CycleNotice>}
      {analysis.data && (
        <RotationResults
          data={analysis.data}
          preference={scenario.preference}
          onRankChange={(preference) => setScenario((current) => ({ ...current, preference }))}
          selectedIds={comparison.map((branch) => branch.branch_id)}
          onToggle={toggleComparison}
        />
      )}
      {comparison.length > 0 && <RotationComparison branches={comparison} scenario={scenario} data={analysis.data} onRemove={toggleComparison} />}
    </div>
  );
}
