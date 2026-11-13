import { container } from "@/components/layout/layoutStyles";

export const panel = "min-w-0 rounded-3xl border border-line bg-white p-4 sm:p-6";
export const control = "min-h-11 w-full min-w-0 rounded-xl border border-line bg-canvas px-3 text-sm text-ink focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-leaf";
export const textLink = "font-semibold text-leaf underline decoration-leaf/40 underline-offset-4 hover:decoration-leaf";

export default function CycleLayout({ title, description, children }) {
  return (
    <div className={`${container} space-y-7 py-10 sm:space-y-9 sm:py-14 lg:py-16`}>
      <header className="max-w-3xl">
        <h1 className="text-[clamp(2.25rem,5vw,3.75rem)] leading-[1.05] font-bold tracking-[-0.055em] text-balance text-forest">
          {title}
        </h1>
        <p className="mt-4 max-w-2xl text-base leading-relaxed text-muted">{description}</p>
      </header>
      {children}
    </div>
  );
}

export function HistoricalGrid({ count, children }) {
  return (
    <div className={`grid gap-4 ${count === 3 ? "md:grid-cols-2 xl:grid-cols-3" : count === 2 ? "md:grid-cols-2" : ""}`}>
      {children}
    </div>
  );
}

export function CycleNotice({ children, error = false, retry }) {
  return (
    <div className={`${panel} text-sm leading-relaxed ${error ? "border-risk/50 text-ink" : "text-muted"}`}>
      <div role={error ? "alert" : undefined}>{children}</div>
      {retry && (
        <button type="button" onClick={retry} className={`${textLink} mt-2 min-h-11 cursor-pointer`}>
          Try again
        </button>
      )}
    </div>
  );
}
