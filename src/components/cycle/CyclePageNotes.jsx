"use client";

import Link from "next/link";
import { primaryButton } from "@/components/layout/layoutStyles";
import { CycleNotice, textLink } from "./CycleLayout";
import { useCycleLanguage } from "./CycleLanguage";

export function UnsupportedDistrict({ district }) {
  const { language, t } = useCycleLanguage();
  const named = district && language === "en";

  return (
    <CycleNotice>
      <h2 className="text-lg font-bold text-forest">
        {t(named ? "{district} District is outside the pilot" : "This district is outside the pilot", { district })}
        {district && !named && <> · <span lang="en">{district}</span></>}
      </h2>
      <p className="mt-2">{t("CycleAlgo currently evaluates crop rotations for Rajshahi District.")}</p>
      <Link href={`/rotation-planner?lang=${language}`} className={`${textLink} mt-2 inline-flex min-h-11 items-center`}>
        {t("Open the Rajshahi planner")}
      </Link>
    </CycleNotice>
  );
}

export function StartComparison() {
  const { language, t } = useCycleLanguage();

  return (
    <CycleNotice>
      <h2 className="text-lg font-bold text-forest">{t("Start with a rotation comparison")}</h2>
      <p className="mt-1">{t("Choose up to three rotations in the Rajshahi planner to see their historical growing conditions here.")}</p>
      <Link href={`/rotation-planner?lang=${language}`} className={`${primaryButton} mt-4`}>{t("Open Rotation Planner")}</Link>
    </CycleNotice>
  );
}

export function HistoricalGuide() {
  const { t } = useCycleLanguage();

  return (
    <section aria-labelledby="what-it-means" className="max-w-2xl">
      <h2 id="what-it-means" className="text-xl font-bold text-forest">{t("What does this mean for farmers?")}</h2>
      <p className="mt-2 text-sm leading-relaxed text-muted">
        {t("A wide rainfall range shows that similar planting windows have seen very different seasons. Use the ranges to discuss timing and water access with local advisors. The archive describes past seasons, and crop-specific risk ratings and weather forecasts are unavailable in this pilot.")}
      </p>
      <Link href="/data-method" className={`${textLink} mt-2 inline-flex min-h-11 items-center text-sm`}>{t("Read Data & Method")}</Link>
    </section>
  );
}
