export default function SectionHeading({ id, label, title, description }) {
  return (
    <div className="max-w-2xl">
      <p className="mb-3 text-xs font-bold tracking-[0.16em] text-leaf uppercase">{label}</p>
      <h2 id={id} className="text-[clamp(1.875rem,3.7vw,2.75rem)] leading-[1.08] font-bold tracking-[-0.045em] text-balance text-forest">
        {title}
      </h2>
      {description && <p className="mt-3.5 max-w-xl text-base leading-relaxed text-muted">{description}</p>}
    </div>
  );
}
