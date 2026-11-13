import { Suspense } from "react";
import districts from "@/data/bangladeshDistricts.json";
import CycleLayout from "@/components/cycle/CycleLayout";
import { CycleLanguageProvider } from "@/components/cycle/CycleLanguage";
import CycleLoading from "@/components/cycle/CycleLoading";
import { UnsupportedDistrict } from "@/components/cycle/CyclePageNotes";
import RotationPlanner from "@/components/cycle/RotationPlanner";
import { readComparison, readScenario, todayInDhaka } from "@/lib/cycleAlgo";

export const metadata = {
  title: "Rotation Planner | FosholCycle",
  description: "Compare crop sequences, planting windows, and evidence for Rajshahi District.",
};

const rajshahi = districts.find((district) => district.name === "Rajshahi");

async function PlannerScenario({ searchParams }) {
  const query = await searchParams;
  if (query.district !== undefined && query.district !== rajshahi.id) {
    const selected = districts.find((district) => district.id === query.district);
    return <UnsupportedDistrict district={selected?.name} />;
  }

  const scenario = readScenario(query, todayInDhaka());
  const branchIds = readComparison(query);
  return <RotationPlanner key={JSON.stringify([scenario, branchIds])} initialScenario={scenario} initialBranches={branchIds} />;
}

export default function RotationPlannerPage({ searchParams }) {
  const loading = <CycleLoading message="Loading Rotation Planner…" variant="picker" route />;

  return (
    <Suspense fallback={<PlannerLayout showLanguage={false}>{loading}</PlannerLayout>}>
      <CycleLanguageProvider>
        <PlannerLayout>
          <Suspense fallback={loading}>
            <PlannerScenario searchParams={searchParams} />
          </Suspense>
        </PlannerLayout>
      </CycleLanguageProvider>
    </Suspense>
  );
}

function PlannerLayout({ children, showLanguage }) {
  return (
    <CycleLayout
      title="Find the Right Rotation for Your Land"
      description="Explore planting windows and compare three-crop sequences using crop calendars and historical conditions for Rajshahi District."
      showLanguage={showLanguage}
    >
      {children}
    </CycleLayout>
  );
}
