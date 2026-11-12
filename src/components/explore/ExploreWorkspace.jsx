"use client";

import dynamic from "next/dynamic";
import { Map as MapIcon, MapPin } from "lucide-react";
import { useCallback, useState } from "react";
import districts from "@/data/bangladeshDistricts.json";
import { getExploreClimate } from "@/data/exploreClimate";
import ClimatePanel from "./ClimatePanel";

const BangladeshMap = dynamic(() => import("./BangladeshMap"), {
  ssr: false,
  loading: () => (
    <div
      role="status"
      className="grid h-[26rem] place-items-center bg-[#eef3ee] text-sm text-muted sm:h-[32rem]"
    >
      Loading Bangladesh map…
    </div>
  ),
});

const districtsById = new Map(
  districts.map((district) => [district.id, district]),
);
const rajshahi = districts.find((district) => district.name === "Rajshahi");
const initialLocation = getExploreClimate(rajshahi, ...rajshahi.center);

export default function ExploreWorkspace() {
  const [selection, setSelection] = useState({
    location: initialLocation,
    revealPin: false,
  });

  const selectLocation = useCallback(
    (districtId, latitude, longitude, revealPin = false) => {
      const location = getExploreClimate(
        districtsById.get(districtId),
        latitude,
        longitude,
      );
      setSelection({ location, revealPin });
    },
    [],
  );

  return (
    <div className="grid items-start gap-5 lg:grid-cols-[minmax(0,1.65fr)_minmax(0,1fr)] lg:gap-6">
      <section
        className="min-w-0 overflow-hidden rounded-3xl border border-line bg-white"
        aria-labelledby="district-map-heading"
      >
        <div className="flex flex-wrap items-center justify-between gap-3 px-4 py-4 sm:px-5">
          <div className="flex items-center gap-2.5">
            <span className="grid size-9 shrink-0 place-items-center rounded-xl bg-mist text-leaf">
              <MapIcon size={18} aria-hidden="true" />
            </span>
            <div>
              <h2
                id="district-map-heading"
                className="text-sm font-bold text-forest"
              >
                Bangladesh districts
              </h2>
              <p className="mt-0.5 text-xs text-muted">
                {districts.length} districts
              </p>
            </div>
          </div>
          <label className="flex w-full flex-wrap items-center gap-2 text-xs font-semibold text-forest sm:w-auto">
            District
            <select
              value={selection.location.districtId}
              onChange={(event) => {
                const district = districtsById.get(event.target.value);
                selectLocation(district.id, ...district.center, true);
              }}
              className="min-h-11 min-w-0 flex-1 rounded-xl border border-line bg-canvas px-3 text-sm font-medium focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-leaf sm:flex-none"
            >
              {districts.map(({ id, name }) => (
                <option key={id} value={id}>
                  {name}
                </option>
              ))}
            </select>
          </label>
        </div>
        <div className="isolate border-y border-line">
          <BangladeshMap selection={selection} onSelect={selectLocation} />
        </div>
        <div className="space-y-2 px-4 py-3 sm:px-5">
          <ul className="flex flex-wrap items-center gap-x-5 gap-y-1.5 text-xs text-muted">
            <li className="flex items-center gap-1.5">
              <span
                aria-hidden="true"
                className="size-3 rounded-sm border border-leaf bg-agriculture"
              />{" "}
              Rajshahi Division
            </li>
            <li className="flex items-center gap-1.5">
              <MapPin size={15} className="text-forest" aria-hidden="true" />{" "}
              Selected location
            </li>
          </ul>
          <p className="text-xs leading-relaxed text-muted">
            Boundaries by Bangladesh Bureau of Statistics and OCHA ROAP, via{" "}
            <a
              className="rounded font-medium text-leaf underline underline-offset-3"
              href="https://www.geoboundaries.org/api/current/gbOpen/BGD/ADM2/"
            >
              geoBoundaries
            </a>{" "}
            (
            <a
              className="rounded font-medium text-leaf underline underline-offset-3"
              href="https://creativecommons.org/licenses/by/3.0/igo/"
            >
              CC BY 3.0 IGO
            </a>
            ).
          </p>
        </div>
      </section>
      <ClimatePanel location={selection.location} />
    </div>
  );
}
