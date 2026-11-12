import Link from "next/link";
import {
  ArrowUpRight,
  CloudRain,
  Droplet,
  Leaf,
  MapPin,
  ThermometerSun,
} from "lucide-react";
import { primaryButton } from "@/components/layout/layoutStyles";

const metricCards = [
  {
    key: "averageTemperatureC",
    label: "Average temperature",
    unit: "°C",
    decimals: 1,
    icon: ThermometerSun,
    tone: "bg-[#fbefd9] text-[#80521b]",
  },
  {
    key: "annualRainfallMm",
    label: "Annual rainfall",
    unit: "mm",
    decimals: 0,
    icon: CloudRain,
    tone: "bg-[#e7f1f8] text-[#245d83]",
  },
  {
    key: "soilMoistureM3M3",
    label: "Soil moisture",
    unit: "m³/m³",
    decimals: 2,
    icon: Droplet,
    tone: "bg-[#e7f1f8] text-[#245d83]",
  },
  {
    key: "vegetationNdvi",
    label: "Vegetation greenness",
    unit: "NDVI",
    decimals: 2,
    icon: Leaf,
    tone: "bg-mist text-leaf",
  },
];

export default function ClimatePanel({ location }) {
  const { districtId, districtName, latitude, longitude, metrics } = location;

  return (
    <aside
      className="min-w-0 rounded-3xl border border-line bg-white p-4 sm:p-5"
      aria-labelledby="climate-panel-heading"
    >
      <div className="flex flex-wrap items-center justify-between gap-2">
        <p className="text-xs font-bold tracking-[0.12em] text-leaf uppercase">
          Climate snapshot
        </p>
        <span className="rounded-full bg-[#f8f1dd] px-2.5 py-1 text-xs font-semibold text-[#6c4a18]">
          Demo data
        </span>
      </div>
      <div className="mt-3" aria-live="polite" aria-atomic="true">
        <h2
          id="climate-panel-heading"
          className="text-2xl font-bold tracking-tight text-forest"
        >
          {districtName} District
        </h2>
        <p className="mt-1.5 flex items-center gap-1.5 text-sm tabular-nums text-muted">
          <MapPin size={15} className="shrink-0 text-leaf" aria-hidden="true" />
          {latitude.toFixed(5)}° N, {longitude.toFixed(5)}° E
        </p>
      </div>
      <dl className="mt-5 grid grid-cols-2 gap-2.5">
        {metricCards.map(({ key, label, unit, decimals, icon: Icon, tone }) => (
          <div
            key={key}
            className="min-w-0 rounded-2xl border border-line bg-canvas p-3"
          >
            <dt className="text-xs leading-snug font-medium text-muted">
              <span
                className={`mb-2 grid size-8 place-items-center rounded-lg ${tone}`}
              >
                <Icon size={16} aria-hidden="true" />
              </span>
              {label}
            </dt>
            <dd className="mt-1.5 flex flex-wrap items-baseline gap-x-1.5 gap-y-0.5 text-xl font-bold tracking-tight tabular-nums text-forest">
              {metrics[key].toLocaleString("en-GB", {
                minimumFractionDigits: decimals,
                maximumFractionDigits: decimals,
              })}
              <span className="text-xs font-medium tracking-normal text-muted">
                {unit}
              </span>
            </dd>
          </div>
        ))}
      </dl>
      <p className="mt-4 text-xs leading-relaxed text-muted">
        Sample values are shared across each district. The coordinates show your
        exact pin location.
      </p>
      <Link
        href={{ pathname: "/rotation-planner", query: { district: districtId } }}
        className={`${primaryButton} mt-5 w-full`}
      >
        Open Rotation Planner <ArrowUpRight size={16} aria-hidden="true" />
      </Link>
    </aside>
  );
}
