import "leaflet/dist/leaflet.css";
import "@/components/explore/bangladeshMap.css";
import ExploreWorkspace from "@/components/explore/ExploreWorkspace";
import { container } from "@/components/layout/layoutStyles";

export const metadata = {
  title: "Explore Map | FosholCycle",
  description: "Explore sample temperature, rainfall, soil moisture, and vegetation data by district in Bangladesh.",
};

export default function ExplorePage() {
  return (
    <div className={`${container} py-10 sm:py-14 lg:py-16`}>
      <div className="mb-7 max-w-2xl sm:mb-9">
        <p className="mb-3 text-xs font-bold tracking-[0.16em] text-leaf uppercase">District explorer</p>
        <h1 className="text-[clamp(2.25rem,5vw,3.75rem)] leading-[1.05] font-bold tracking-[-0.055em] text-forest">
          Explore Bangladesh
        </h1>
        <p className="mt-4 max-w-xl text-base leading-relaxed text-muted">
          Place a pin or choose a district to see its sample climate and growing conditions.
        </p>
      </div>
      <ExploreWorkspace />
    </div>
  );
}
