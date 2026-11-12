import { CloudRain, MapPin, ThermometerSun } from "lucide-react";
import { rajshahiPreview } from "@/data/homePreview";
import RainfallChart from "./RainfallChart";

export default function PlatformPreview() {
  const { location, averageTemperature, monthlyRainfall, rotations } = rajshahiPreview;
  const annualRainfall = monthlyRainfall.reduce((total, month) => total + month.millimeters, 0);

  return (
    <div className="overflow-hidden rounded-[1.75rem] border border-line bg-white shadow-[0_16px_40px_-25px_#163d2b55]">
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-line px-4 py-4 sm:px-6">
        <div className="flex items-center gap-3">
          <span className="grid size-9 shrink-0 place-items-center rounded-xl bg-mist text-leaf">
            <MapPin size={17} aria-hidden="true" />
          </span>
          <div>
            <h3 className="text-sm font-bold text-forest">{location}</h3>
            <p className="mt-0.5 text-xs text-muted">District overview</p>
          </div>
        </div>
        <span className="rounded-full bg-[#f8f1dd] px-3 py-1 text-xs font-semibold text-[#6c4a18]">
          Illustrative data
        </span>
      </div>
      <div className="bg-canvas p-3.5 sm:p-6">
        <dl className="mb-3.5 grid grid-cols-2 gap-2.5 sm:mb-4 sm:gap-4">
          <div className="rounded-xl border border-line bg-white p-3 sm:p-4">
            <dt className="flex items-center gap-1.5 text-xs font-medium text-muted">
              <ThermometerSun size={16} className="shrink-0 text-[#8d591d]" aria-hidden="true" />
              Average temperature
            </dt>
            <dd className="mt-1.5 text-xl font-bold tracking-tight text-forest sm:text-2xl">{averageTemperature} °C</dd>
          </div>
          <div className="rounded-xl border border-line bg-white p-3 sm:p-4">
            <dt className="flex items-center gap-1.5 text-xs font-medium text-muted">
              <CloudRain size={16} className="shrink-0 text-[#337aa8]" aria-hidden="true" />
              Annual rainfall
            </dt>
            <dd className="mt-1.5 text-xl font-bold tracking-tight text-forest sm:text-2xl">{annualRainfall.toLocaleString("en-GB")} mm</dd>
          </div>
        </dl>
        <div className="grid gap-3.5 sm:gap-4 lg:grid-cols-[1.25fr_1fr]">
          <RainfallChart monthlyRainfall={monthlyRainfall} />
          <section className="min-w-0 rounded-2xl border border-line bg-white p-4 sm:p-5" aria-labelledby="rotation-preview-heading">
            <h4 id="rotation-preview-heading" className="text-sm font-semibold text-forest">Rotation comparison</h4>
            <p className="mt-1 text-xs text-muted">Estimated suitability on a 0–100 scale</p>
            <ul className="mt-4 space-y-3">
              {rotations.map(({ middleCrop, suitability }, index) => (
                <li key={middleCrop}>
                  <div className="mb-1.5 flex items-baseline justify-between gap-2 text-xs">
                    <span className="font-medium text-ink">Rice → {middleCrop} → Mung Bean</span>
                    <span className="shrink-0 font-bold tabular-nums text-forest">{suitability}<span className="sr-only"> out of 100</span></span>
                  </div>
                  <div aria-hidden="true" className="h-1.5 overflow-hidden rounded-full bg-mist">
                    <div className={`h-full rounded-full ${index === 0 ? "bg-leaf" : "bg-agriculture/65"}`} style={{ width: `${suitability}%` }} />
                  </div>
                </li>
              ))}
            </ul>
          </section>
        </div>
        <p className="mt-3.5 text-xs leading-relaxed text-muted">
          Sample climate figures and suitability estimates for comparing rotations. Crop yields depend on local growing conditions.
        </p>
      </div>
    </div>
  );
}
