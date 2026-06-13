export default function ErrorState({ title = "Unable to load data", description = "The requested data could not be loaded safely right now." }) {
  return (
    <section className="rounded-[28px] border border-[#f0cfcf] bg-[#fff6f6] p-8 shadow-panel">
      <div className="space-y-3">
        <p className="text-xs uppercase tracking-[0.18em] text-[color:var(--danger)]">Read-only error</p>
        <h2 className="text-xl text-ink">{title}</h2>
        <p className="text-sm leading-7 text-[color:var(--danger)]">{description}</p>
      </div>
    </section>
  );
}
