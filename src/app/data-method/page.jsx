import Link from "next/link";
import { CalendarDays, CloudSun, Droplet, Leaf } from "lucide-react";
import CycleLayout, { panel, textLink } from "@/components/cycle/CycleLayout";
import { primaryButton } from "@/components/layout/layoutStyles";

export const metadata = {
  title: "Data & Method | FosholCycle",
  description: "See the climate records, crop calendars, and evidence limits behind the Rajshahi pilot.",
};

const engineDocs = "https://github.com/hosain-ahmed/CycleAlgo/blob/main/fosol-cycle-engine/docs";

const sources = [
  { title: "NASA POWER", status: "Used · API history and cache", Icon: CloudSun, detail: "Default Rajshahi reference point: 24.3767 N, 88.6029 E. The engine requests 1991–2025 daily history and compares complete historical growing seasons. Coverage and cache status are shown with each response; cross-year schedules may exclude the final season.", href: `${engineDocs}/ENVIRONMENTAL_DATA.md`, linkText: "Environmental data notes" },
  { title: "Crop calendars and profiles", status: "Used · Local reference", Icon: CalendarDays, detail: "Documented planting windows, crop durations, and crop families inform the three-crop sequences and timing estimates.", href: `${engineDocs}/TIMELINE.md`, linkText: "Timeline method" },
  { title: "NASA SMAP", status: "Unavailable in this pilot", Icon: Droplet, detail: "Soil moisture can provide context when observations are available. CycleAlgo evaluates the scenario independently of SMAP." },
  { title: "Vegetation monitoring", status: "Planned", Icon: Leaf, detail: "The map’s NDVI card is a demo value. Vegetation observations are planned for a future release." },
];

const steps = [
  ["Set the scenario", "Choose a start date and indicate what you know about water access in Rajshahi."],
  ["Explore crop sequences", "CycleAlgo checks documented windows, builds three-crop sequences, and flags unresolved checks."],
  ["Compare timing and diversity", "Fastest completion orders rotations by the upper end of the time from first planting to final harvest. The wait before first planting is shown separately. Diversity counts distinct crop families."],
  ["Compare NASA weather exposure", "Choose temperature match, dry spells, or heavy rain. The engine ranks paths within candidate/conditional groups over shared complete seasons. All three crop summaries receive equal weight. Ties stay tied; unavailable evidence stays unranked. There is no overall best-rotation score."],
  ["Understand the measures", "Temperature compares growing-period medians with general species-level EcoCrop guidance, not stage-specific heat limits. Dry spells are runs below 1 mm/day; heavy-rain days have at least 20 mm. Lower exposure is not automatically better for every farm."],
  ["Review schedules and context", "The weather value is the higher exposure of two completion-optimized example schedules, not a worst-case bound over all possible schedules. Supporting crop values use the same shared years. Reference-window historical ranges are separate context, not ranking scores."],
];

export default function DataMethodPage() {
  return (
    <CycleLayout
      title="Powered by Earth Data. Built for Better Decisions."
      description="See where the Rajshahi pilot gets its evidence, how CycleAlgo compares rotations, and which decisions still need local information."
    >
      <section aria-labelledby="sources-heading" className="space-y-4">
        <h2 id="sources-heading" className="text-2xl font-bold tracking-tight text-forest">Data sources</h2>
        <div className="grid gap-4 md:grid-cols-2">
          {sources.map(({ title, status, Icon, detail, href, linkText }) => (
            <article className={panel} key={title}>
              <span className="grid size-10 place-items-center rounded-xl bg-mist text-leaf"><Icon size={20} aria-hidden="true" /></span>
              <h3 className="mt-3 text-lg font-bold text-forest">{title}</h3>
              <p className="mt-1 text-xs font-semibold text-leaf">{status}</p>
              <p className="mt-2 text-sm leading-relaxed text-muted">{detail}</p>
              {href && <a className={`${textLink} mt-2 inline-flex min-h-11 items-center text-sm`} href={href}>{linkText}</a>}
            </article>
          ))}
        </div>
      </section>

      <section className={panel} aria-labelledby="method-heading">
        <h2 id="method-heading" className="text-xl font-bold text-forest">How a rotation is evaluated</h2>
        <ol className="mt-4 grid gap-x-6 gap-y-4 md:grid-cols-2">
          {steps.map(([title, detail]) => (
            <li className="border-l-2 border-mist pl-3" key={title}>
              <h3 className="text-sm font-bold text-forest">{title}</h3>
              <p className="mt-1 text-sm leading-relaxed text-muted">{detail}</p>
            </li>
          ))}
        </ol>
      </section>

      <section className={panel} aria-labelledby="limits-heading">
        <h2 id="limits-heading" className="text-xl font-bold text-forest">Where local evidence is still needed</h2>
        <ul className="mt-3 ml-5 max-w-3xl list-disc space-y-2 text-sm leading-relaxed text-muted">
          <li>The reference point represents one point/grid, not a measured district average. Soils, drainage, water access, and management can vary by field.</li>
          <li>Field preparation time and irrigation needs can change whether a sequence is practical. A conditional rotation has unresolved checks.</li>
          <li>Historical ranges describe past conditions. Local input is needed for current-season risk, field suitability, yield, and farm economics.</li>
          <li>Water access changes checks and cautions; it does not establish irrigation demand or a validated irrigation-based ranking. Economics and measured soil-health controls remain unavailable.</li>
          <li>A legume is descriptive, not a measured soil benefit. Third-to-first compatibility is unchecked, so these are three-crop sequences rather than guaranteed repeating rotations.</li>
          <li>The engine documents a Rajshahi Mustard–Boro–T. Aman baseline. Its optional featured alternatives have geographic/variety limits; they do not replace interactive API results or establish local field validation. <a className={textLink} href={`${engineDocs}/EXPLAINER.md`}>Read the sourced examples.</a></li>
        </ul>
        <Link href="/rotation-planner" className={`${primaryButton} mt-5`}>Open the Rajshahi planner</Link>
      </section>
    </CycleLayout>
  );
}
