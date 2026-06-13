export default function EmptyState({ title, description }) {
  return (
    <section className="rounded-[28px] border border-dashed border-[var(--border)] bg-[rgba(255,255,255,0.84)] p-8 text-center shadow-panel">
      <div className="mx-auto max-w-2xl space-y-3">
        <h2 className="text-2xl text-ink">{title}</h2>
        <p className="text-sm leading-7 text-[color:var(--muted)]">{description}</p>
      </div>
    </section>
  );
}
