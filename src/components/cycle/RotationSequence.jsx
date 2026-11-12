const plotColors = ["border-[#a3b79e] bg-[#eef3eb]", "border-[#c4ab75] bg-[#f8f3e7]", "border-[#8faf9d] bg-[#e8f2ed]"];

export function BranchStatus({ status, compact = false }) {
  const candidate = status === "candidate";
  return (
    <span className={`inline-flex max-w-full min-w-0 items-center gap-1.5 rounded-full font-semibold ${compact ? "text-[11px] sm:px-2.5 sm:py-1 sm:text-xs" : "px-2.5 py-1 text-xs"} ${candidate ? (compact ? "text-forest sm:bg-mist" : "bg-mist text-forest") : (compact ? "text-[#704b1c] sm:bg-[#f8f1dd]" : "bg-[#f8f1dd] text-[#704b1c]")}`}>
      <span className={`size-1.5 shrink-0 rounded-full bg-current ${compact ? "hidden sm:block" : ""}`} aria-hidden="true" />
      <span className="min-w-0 wrap-anywhere">{candidate ? "Candidate" : "Conditional"}</span>
    </span>
  );
}

export function rotationLetter(index) {
  return "ABC"[index];
}

export default function RotationSequence({ crops }) {
  return (
    <ol aria-label="Crop sequence" className="grid min-w-0 grid-cols-3 gap-1.5 sm:gap-2">
      {crops.map((crop, index) => (
        <li key={index} className={`min-w-0 rounded-sm border-t-[3px] px-2 py-2 sm:px-3 ${plotColors[index]}`}>
          <span aria-hidden="true" className="block text-xs font-semibold tabular-nums text-forest/75">0{index + 1}</span>
          <span className="mt-0.5 block text-sm leading-snug font-semibold wrap-anywhere text-forest">{crop.name_en}</span>
        </li>
      ))}
    </ol>
  );
}
