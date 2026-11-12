"use client";

import { useEffect, useState } from "react";

export function useCycleAnalysis(scenario) {
  const body = scenario ? JSON.stringify(scenario) : null;
  const [attempt, setAttempt] = useState(0);
  const [result, setResult] = useState(null);
  const key = body ? `${attempt}:${body}` : null;

  useEffect(() => {
    if (!body) return;
    const controller = new AbortController();

    async function load() {
      try {
        const response = await fetch("/api/cycle-algo/explore", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body,
          signal: controller.signal,
        });
        const data = await response.json();
        if (controller.signal.aborted) return;
        if (response.ok) {
          setResult({ key, data });
        } else {
          setResult({
            key,
            error: data.error ?? { message: "FosholCycle returned an unexpected response." },
            retryable: response.status >= 500,
          });
        }
      } catch {
        if (!controller.signal.aborted) {
          setResult({ key, error: { message: "The planner could not reach FosholCycle. Try again." }, retryable: true });
        }
      }
    }

    load();
    return () => controller.abort();
  }, [body, key]);

  return {
    ...(key && result?.key === key ? result : { pending: Boolean(key) }),
    retry: () => setAttempt((previous) => previous + 1),
  };
}
