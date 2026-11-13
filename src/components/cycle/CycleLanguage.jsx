"use client";

import { createContext, useContext } from "react";
import { useSearchParams } from "next/navigation";
import { cycleLocales, readCycleLanguage } from "@/lib/cycleLocale";

const CycleLanguage = createContext(cycleLocales.bn);

export function useCycleLanguage() {
  return useContext(CycleLanguage);
}

export function CycleLanguageProvider({ children }) {
  const query = useSearchParams();
  const language = readCycleLanguage(query.getAll("lang").length === 1 ? query.get("lang") : null);

  return <CycleLanguage.Provider value={cycleLocales[language]}>{children}</CycleLanguage.Provider>;
}

export function LanguageSwitch() {
  const { language, t } = useCycleLanguage();

  function changeLanguage(next) {
    const url = new URL(window.location.href);
    url.searchParams.set("lang", next);
    window.history.replaceState(null, "", url);
  }

  return (
    <div role="group" aria-label={t("Page language")} className="inline-flex rounded-xl border border-line bg-white p-1">
      {[["bn", "বাংলা"], ["en", "English"]].map(([id, label]) => (
        <button key={id} type="button" lang={id} aria-pressed={language === id} onClick={() => changeLanguage(id)} className="min-h-11 cursor-pointer rounded-lg px-3 text-sm font-semibold text-leaf hover:bg-canvas aria-pressed:bg-mist aria-pressed:text-forest">
          {label}
        </button>
      ))}
    </div>
  );
}
