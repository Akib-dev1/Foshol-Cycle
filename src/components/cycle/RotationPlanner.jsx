"use client";

import { useState } from "react";
import { CalendarDays } from "lucide-react";
import { control, CycleNotice, panel } from "./CycleLayout";
import RotationComparison from "./RotationComparison";
import { BranchStatus } from "./RotationSequence";
import RotationResults from "./RotationResults";
import { useCycleAnalysis } from "./useCycleAnalysis";
import { dayRange, isPlanningDate, MAX_COMPARISONS, MIN_START_DATE, MAX_START_DATE, waterOptions } from "@/lib/cycleAlgo";

function SelectField({ label, options, value, onChange }) {
  return (
    <label className="grid min-w-0 gap-1.5 text-sm font-semibold text-forest">
      {label}
      <select value={value} onChange={(event) => onChange(event.target.value)} className={control}>
        {Object.entries(options).map(([id, name]) => <option key={id} value={id}>{name}</option>)}
      </select>
    </label>
  );
}

export default function RotationPlanner({ initialScenario, initialBranches }) {
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
            <h2 id="scenario-heading" className="text-lg font-bold text-forest">Planning scenario</h2>
            <p className="text-sm text-muted">Rajshahi District</p>
          </div>
        </div>
        <div className="mt-5 grid gap-4 md:grid-cols-2">
          <label className="grid min-w-0 gap-1.5 text-sm font-semibold text-forest">
            Start date
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
          <SelectField label="Water access" options={waterOptions} value={scenario.water_access} onChange={(value) => changeScenario("water_access", value, true)} />
        </div>
        {!dateValid && <p id="start-date-error" role="alert" className="mt-3 text-sm font-medium text-[#933d35]">Choose a valid start date between {MIN_START_DATE} and {MAX_START_DATE}.</p>}
      </section>

      {discovery.pending && <CycleNotice pending>Finding first crops for this scenario…</CycleNotice>}
      {discovery.error && <CycleNotice error retry={discovery.retryable ? discovery.retry : undefined}>{discovery.error.message}</CycleNotice>}
      {discovery.data && (crops.length ? (
        <section className={panel} aria-labelledby="first-crop-heading">
          <h2 id="first-crop-heading" className="text-lg font-bold text-forest">Choose the first crop</h2>
          <div className="mt-3 grid items-start gap-4 md:grid-cols-2">
            <SelectField
              label="First crop"
              value={firstCrop?.crop_id ?? ""}
              options={Object.fromEntries([["", "Select a crop"], ...crops.map((crop) => [crop.crop_id, `${crop.name_en}${crop.reference_variety ? ` · ${crop.reference_variety}` : ""}`])])}
              onChange={(value) => changeScenario("first_crop_id", value || null)}
            />
            <div className="min-w-0 text-sm leading-relaxed wrap-anywhere text-muted">
              {firstCrop ? (
                <>
                  <BranchStatus status={firstCrop.status} />
                  <p className="mt-2">Initial wait · <strong className="text-ink">{dayRange({ min: firstCrop.initial_wait_days, max: firstCrop.initial_wait_days })}</strong></p>
                  {firstCrop.checks?.water?.reason && <p className="mt-1">{firstCrop.checks.water.reason}</p>}
                </>
              ) : <p>Choose a crop to see the planting and harvest windows for the full rotation.</p>}
              {scenario.first_crop_id && !firstCrop && <p role="status" className="mt-2">The crop from the shared scenario is unavailable. Choose another first crop.</p>}
            </div>
          </div>
        </section>
      ) : (
        <CycleNotice>{discovery.data.status === "data_unavailable" ? "Crop profiles are unavailable for this scenario." : discovery.data.branch_summary.message || "No supported crop options for this scenario."}</CycleNotice>
      ))}

      {analysis.pending && <CycleNotice pending>Evaluating rotations and historical growing conditions…</CycleNotice>}
      {analysis.error && <CycleNotice error retry={analysis.retryable ? analysis.retry : undefined}>{analysis.error.message}</CycleNotice>}
      {staleComparison && <CycleNotice>Some rotations from the shared comparison are unavailable in this run.</CycleNotice>}
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
