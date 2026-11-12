import { Suspense } from "react";
import Link from "next/link";
import districts from "@/data/bangladeshDistricts.json";
import CycleLayout, { CycleNotice, textLink } from "@/components/cycle/CycleLayout";
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
    return (
      <CycleNotice>
        <h2 className="text-lg font-bold text-forest">
          {selected ? `${selected.name} District is outside the pilot` : "This district is outside the pilot"}
        </h2>
        <p className="mt-2">CycleAlgo currently evaluates crop rotations for Rajshahi District.</p>
        <Link href="/rotation-planner" className={`${textLink} mt-2 inline-flex min-h-11 items-center`}>
          Open the Rajshahi planner
        </Link>
      </CycleNotice>
    );
  }

  const scenario = readScenario(query, todayInDhaka());
  const branchIds = readComparison(query);
  return <RotationPlanner key={JSON.stringify([scenario, branchIds])} initialScenario={scenario} initialBranches={branchIds} />;
}

export default function RotationPlannerPage({ searchParams }) {
  return (
    <CycleLayout
      title="Find the Right Rotation for Your Land"
      description="Explore planting windows and compare three-crop sequences using crop calendars and historical conditions for Rajshahi District."
    >
      <Suspense fallback={<CycleNotice pending>Loading Rotation Planner…</CycleNotice>}>
        <PlannerScenario searchParams={searchParams} />
      </Suspense>
    </CycleLayout>
  );
}
