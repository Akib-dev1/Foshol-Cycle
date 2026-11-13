import { Suspense } from "react";
import Link from "next/link";
import CycleLayout, { CycleNotice, textLink } from "@/components/cycle/CycleLayout";
import CycleLoading from "@/components/cycle/CycleLoading";
import HistoricalConditions from "@/components/cycle/HistoricalConditions";
import { primaryButton } from "@/components/layout/layoutStyles";
import { isPlanningDate, readComparison, readScenario } from "@/lib/cycleAlgo";

export const metadata = {
  title: "Risk & Uncertainty | FosholCycle",
  description: "Review historical temperature and rainfall ranges for selected crop rotations in Rajshahi.",
};

async function RiskScenario({ searchParams }) {
  const query = await searchParams;
  const scenario = readScenario(query, "");
  const branchIds = readComparison(query);
  if (!scenario.first_crop_id || !isPlanningDate(scenario.start_date) || !branchIds.length) {
    return (
      <CycleNotice>
        <h2 className="text-lg font-bold text-forest">Start with a rotation comparison</h2>
        <p className="mt-1">Choose up to three rotations in the Rajshahi planner to see their historical growing conditions here.</p>
        <Link href="/rotation-planner" className={`${primaryButton} mt-4`}>Open Rotation Planner</Link>
      </CycleNotice>
    );
  }
  return <HistoricalConditions key={JSON.stringify([scenario, branchIds])} scenario={scenario} branchIds={branchIds} />;
}

export default function RiskPage({ searchParams }) {
  return (
    <CycleLayout
      title="Understand the Risk Before You Plant"
      description="See how temperature and rainfall varied during comparable growing seasons for the rotations you selected in Rajshahi."
    >
      <Suspense fallback={<CycleLoading message="Loading historical conditions…" variant="history" route />}>
        <RiskScenario searchParams={searchParams} />
      </Suspense>
      <section aria-labelledby="what-it-means" className="max-w-2xl">
        <h2 id="what-it-means" className="text-xl font-bold text-forest">What does this mean for farmers?</h2>
        <p className="mt-2 text-sm leading-relaxed text-muted">
          A wide rainfall range shows that similar planting windows have seen very different seasons. Use the ranges to discuss timing and water access with local advisors. The archive describes past seasons, and crop-specific risk ratings and weather forecasts are unavailable in this pilot.
        </p>
        <Link href="/data-method" className={`${textLink} mt-2 inline-flex min-h-11 items-center text-sm`}>Read Data &amp; Method</Link>
      </section>
    </CycleLayout>
  );
}
