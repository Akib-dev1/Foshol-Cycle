"use client";

import { useEffect, useState } from "react";
import { LoaderCircle } from "lucide-react";
import { useCycleLanguage } from "./CycleLanguage";

export default function LoadingStatus({ message }) {
  const { t } = useCycleLanguage();
  const [slow, setSlow] = useState(false);

  useEffect(() => {
    const timer = setTimeout(() => setSlow(true), 8_000);
    return () => clearTimeout(timer);
  }, []);

  return (
    <div role="status" className="flex items-center gap-2 text-sm font-medium text-forest">
      <LoaderCircle size={18} className="shrink-0 text-leaf motion-safe:animate-spin" aria-hidden="true" />
      <p>{message}{slow && <> {t("Still working. Results will appear here when ready.")}</>}</p>
    </div>
  );
}
