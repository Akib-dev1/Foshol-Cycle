import { Suspense } from "react";
import CycleLayout from "@/components/cycle/CycleLayout";
import { CycleLanguageProvider } from "@/components/cycle/CycleLanguage";
import CycleLoading from "@/components/cycle/CycleLoading";
import { HistoricalGuide, StartComparison } from "@/components/cycle/CyclePageNotes";
import HistoricalConditions from "@/components/cycle/HistoricalConditions";
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
    return <StartComparison />;
  }
  return <HistoricalConditions key={JSON.stringify([scenario, branchIds])} scenario={scenario} branchIds={branchIds} />;
}

export default function RiskPage({ searchParams }) {
  const loading = <CycleLoading message="Loading historical conditions…" variant="history" route />;

  return (
    <Suspense fallback={<RiskLayout showLanguage={false}>{loading}</RiskLayout>}>
      <CycleLanguageProvider>
        <RiskLayout>
          <Suspense fallback={loading}>
            <RiskScenario searchParams={searchParams} />
          </Suspense>
        </RiskLayout>
      </CycleLanguageProvider>
    </Suspense>
  );
}

function RiskLayout({ children, showLanguage }) {
  return (
    <CycleLayout
      title="Understand the Risk Before You Plant"
      description="See how temperature and rainfall varied during comparable growing seasons for the rotations you selected in Rajshahi."
      showLanguage={showLanguage}
    >
      {children}
      <HistoricalGuide />
    </CycleLayout>
  );
}
