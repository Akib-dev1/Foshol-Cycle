import Image from "next/image";
import Link from "next/link";
import {
  ArrowDown, ArrowRight, ArrowUpRight, CalendarDays, CloudRain, CloudSun, MapPin,
  ShieldAlert, Sprout, Sunrise, Wheat, Workflow,
} from "lucide-react";
import SectionHeading from "@/components/common/SectionHeading";
import PlatformPreview from "@/components/home/PlatformPreview";
import { button, container, primaryButton } from "@/components/layout/layoutStyles";

const features = [
  {
    title: "Explore Your Land",
    description: "Find your district on the map and explore a sample climate snapshot.",
    link: "Open the map",
    href: "/explore",
    icon: MapPin,
    tone: "bg-[#e7f1f8] text-[#245d83]",
  },
  {
    title: "Compare Crop Rotations",
    description: "Compare planting windows, completion time, and crop diversity in Rajshahi.",
    link: "Open the planner",
    href: "/rotation-planner",
    icon: Workflow,
    tone: "bg-mist text-leaf",
  },
  {
    title: "Understand Climate Risks",
    description: "Review how temperature and rainfall have varied during comparable growing seasons.",
    link: "Explore climate risks",
    href: "/risk-uncertainty",
    icon: ShieldAlert,
    tone: "bg-[#fbefd9] text-[#80521b]",
  },
];

const steps = [
  {
    title: "Select a location",
    description: "Explore Bangladesh’s districts and open the Rajshahi planner from the map.",
  },
  {
    title: "Compare rotations",
    description: "Put crop sequences side by side to compare timing and evidence gaps.",
  },
  {
    title: "Understand the risks",
    description: "See the historical temperature and rainfall ranges for the rotations you select.",
  },
];

const seasons = [
  {
    name: "Rabi",
    label: "Cool, dry season",
    months: "Nov–Feb",
    crops: "Mustard, wheat, potato",
    detail: "Factor in irrigation as winter rainfall drops.",
    icon: Sunrise,
    tone: "border-[#decaa0] bg-[#fcf5e6] text-[#80521b]",
  },
  {
    name: "Kharif-I",
    label: "Pre-monsoon",
    months: "Mar–Jun",
    crops: "Aus rice, jute, mung bean",
    detail: "Watch for heat and uneven early rains.",
    icon: CloudSun,
    tone: "border-[#b9d7bb] bg-mist text-leaf",
  },
  {
    name: "Kharif-II",
    label: "Monsoon",
    months: "Jul–Oct",
    crops: "Aman rice, monsoon vegetables",
    detail: "Consider drainage where fields hold water.",
    icon: CloudRain,
    tone: "border-[#bad6e8] bg-[#eaf3f9] text-[#245d83]",
  },
];

export default function Home() {
  return (
    <>
      <section aria-labelledby="home-heading" className={`${container} pt-12 sm:pt-16 lg:pt-20`}>
        <div className="mx-auto max-w-3xl text-center">
          <p className="inline-flex items-center gap-2 rounded-full border border-[#d4e5d6] bg-mist px-3.5 py-1.5 text-xs font-semibold text-leaf">
            <Sprout size={15} aria-hidden="true" /> Smarter Crop Rotations. Resilient Farms.
          </p>
          <h1 id="home-heading" className="mt-5 text-[clamp(2.5rem,6vw,5.125rem)] leading-[1.01] font-bold tracking-[-0.065em] text-balance text-forest sm:mt-6">
            Better Farming Starts with <span className="text-leaf">Better Data.</span>
          </h1>
          <p className="mx-auto mt-5 max-w-xl text-base leading-relaxed text-muted sm:text-lg">
            Explore climate insights, compare crop rotations, and prepare your farm for an uncertain future.
          </p>
          <div className="mt-7 flex flex-wrap justify-center gap-3 sm:mt-8">
            <Link href="/explore" className={primaryButton}>
              Start Exploring <ArrowUpRight size={17} aria-hidden="true" />
            </Link>
            <Link href="#how-it-works" className={`${button} border border-line bg-white text-forest hover:bg-mist`}>
              How It Works <ArrowDown size={16} aria-hidden="true" />
            </Link>
          </div>
        </div>
        <figure className="relative mt-9 overflow-hidden rounded-[1.65rem] bg-forest shadow-[0_18px_45px_-27px_#163d2b88] sm:mt-12 sm:rounded-4xl">
          <div className="relative aspect-5/4 sm:aspect-[2.35/1] lg:aspect-[2.85/1]">
            <Image
              src="/nazirhat-paddy-fields.webp"
              alt="Aerial view of green paddy fields and village roads in Nazirhat"
              fill
              preload
              sizes="(min-width: 1024px) 75vw, (min-width: 768px) 84vw, 92vw"
              className="object-cover object-[50%_63%]"
            />
          </div>
          <figcaption className="absolute bottom-3.5 left-3.5 flex items-center gap-2 rounded-xl bg-forest px-3 py-2 text-xs font-medium text-white sm:bottom-5 sm:left-5 sm:px-4 sm:py-2.5">
            <MapPin size={15} className="text-[#b2dfab]" aria-hidden="true" />
            Paddy fields in Nazirhat, Bangladesh
          </figcaption>
        </figure>
      </section>

      <section aria-labelledby="features-heading" className={`${container} py-16 sm:py-20 lg:py-24`}>
        <SectionHeading
          id="features-heading"
          label="Decision tools"
          title="What should you plant next?"
          description="Get to know your district’s climate and see how different crop sequences fit the seasons ahead."
        />
        <div className="mt-7 grid gap-4 md:grid-cols-3 lg:mt-9 lg:gap-5">
          {features.map(({ title, description, link, href, icon: Icon, tone }) => (
            <article key={href} className="flex flex-col rounded-3xl border border-line bg-white p-5 shadow-[0_7px_24px_-19px_#163d2b66] sm:p-6">
              <span className={`grid size-11 place-items-center rounded-xl ${tone}`}>
                <Icon size={21} aria-hidden="true" />
              </span>
              <h3 className="mt-4 text-lg font-bold tracking-tight text-forest">{title}</h3>
              <p className="mt-2 grow text-sm leading-relaxed text-muted">{description}</p>
              <Link href={href} className="group mt-4 inline-flex min-h-11 w-fit items-center gap-2 rounded text-sm font-semibold text-leaf hover:underline hover:underline-offset-4">
                {link} <ArrowRight size={16} aria-hidden="true" />
              </Link>
            </article>
          ))}
        </div>
      </section>

      <section id="how-it-works" aria-labelledby="workflow-heading" className="scroll-mt-6 border-y border-[#d8e7d9] bg-mist py-12 sm:py-16 lg:py-18">
        <div className={container}>
          <SectionHeading id="workflow-heading" label="How it works" title="From district to planting decision" />
          <ol className="mt-7 grid gap-4 md:grid-cols-3 lg:mt-9 lg:gap-5">
            {steps.map(({ title, description }, index) => (
              <li key={title} className="rounded-2xl border border-[#d4e5d6] bg-white/75 p-5 sm:p-6">
                <div className="flex items-center gap-3" aria-hidden="true">
                  <span className="grid size-9 shrink-0 place-items-center rounded-full bg-forest text-xs font-bold text-white">0{index + 1}</span>
                  <span className="h-px w-full bg-[#cbdfcd]" />
                </div>
                <h3 className="mt-4 text-base font-bold text-forest">{title}</h3>
                <p className="mt-2 text-sm leading-relaxed text-muted">{description}</p>
              </li>
            ))}
          </ol>
        </div>
      </section>

      <section aria-labelledby="seasons-heading" className={`${container} py-16 sm:py-20 lg:py-24`}>
        <SectionHeading
          id="seasons-heading"
          label="Bangladesh farming seasons"
          title="Three seasons shape what you can grow"
          description="Use these broad growing windows as a starting point. Planting and harvest dates vary by crop and district."
        />
        <div className="mt-7 grid gap-4 md:grid-cols-3 lg:mt-9 lg:gap-5">
          {seasons.map(({ name, label, months, crops, detail, icon: Icon, tone }) => (
            <article key={name} className={`rounded-3xl border p-5 sm:p-6 ${tone}`}>
              <div className="flex items-center justify-between gap-2">
                <span className="grid size-10 shrink-0 place-items-center rounded-xl bg-white/80">
                  <Icon size={20} aria-hidden="true" />
                </span>
                <span className="inline-flex items-center gap-1.5 rounded-full bg-white/80 px-2.5 py-1 text-xs font-semibold">
                  <CalendarDays size={13} aria-hidden="true" /> {months}
                </span>
              </div>
              <p className="mt-4 text-xs font-bold tracking-wide uppercase">{label}</p>
              <h3 className="mt-1 text-2xl font-bold tracking-tight text-forest">{name}</h3>
              <p className="mt-2 text-sm font-semibold text-ink">{crops}</p>
              <p className="mt-1.5 text-sm leading-relaxed text-muted">{detail}</p>
            </article>
          ))}
        </div>
      </section>

      <section aria-labelledby="preview-heading" className="border-y border-line bg-[#edf2ed] py-12 sm:py-16 lg:py-18">
        <div className={container}>
          <SectionHeading
            id="preview-heading"
            label="Platform preview"
            title="A closer look at Rajshahi"
            description="Get a preview of the climate and rotation information FosholCycle brings together."
          />
          <div className="mt-7 lg:mt-9"><PlatformPreview /></div>
        </div>
      </section>

      <section aria-labelledby="cta-heading" className={`${container} py-14 sm:py-20 lg:py-24`}>
        <div className="relative isolate overflow-hidden rounded-[1.75rem] bg-forest px-6 py-9 text-white sm:rounded-4xl sm:px-10 sm:py-12 lg:px-12 lg:py-14">
          <svg aria-hidden="true" viewBox="0 0 480 300" className="pointer-events-none absolute right-0 bottom-0 -z-10 hidden w-[43%] text-[#a7d5a2]/25 sm:block" fill="none" stroke="currentColor" strokeWidth="1.5">
            <path d="M0 300C100 160 207 263 314 130 382 45 428 50 480 28M46 300C141 183 232 265 334 147 394 77 435 73 480 54M89 300C179 207 252 271 354 167 409 111 443 96 480 81M136 300C213 232 274 277 376 188 424 146 451 127 480 108M184 300C246 254 299 279 398 208 437 180 457 160 480 135M237 300C283 272 330 282 419 230 452 211 470 187 480 163M289 300C330 283 371 280 440 251 460 242 471 226 480 207" />
          </svg>
          <span className="inline-flex items-center gap-2 rounded-full bg-white/10 px-3 py-1.5 text-xs font-semibold text-[#d2ebcb]">
            <Wheat size={15} aria-hidden="true" /> Plan your next season
          </span>
          <h2 id="cta-heading" className="mt-4 max-w-xl text-[clamp(2rem,4vw,3.25rem)] leading-[1.06] font-bold tracking-tighter text-balance">
            Plan for a more resilient harvest.
          </h2>
          <p className="mt-4 max-w-md text-sm leading-relaxed text-[#d2e4d6] sm:text-base">
            Explore the Bangladesh map, then compare crop rotations in the Rajshahi pilot.
          </p>
          <div className="mt-6 flex flex-wrap gap-3">
            <Link href="/explore" className={`${button} bg-white text-forest hover:bg-mist focus-visible:outline-white`}>
              Explore the Map <ArrowUpRight size={16} aria-hidden="true" />
            </Link>
            <Link href="/data-method" className={`${button} border border-white/35 text-white hover:bg-white/10`}>
              View Data &amp; Method
            </Link>
          </div>
        </div>
      </section>
    </>
  );
}
