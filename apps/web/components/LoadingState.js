export default function LoadingState({ title = "Loading data...", description = "Please wait while the workspace fetches safe read-only data." }) {
  return (
    <section className="rounded-[28px] border border-[var(--border)] bg-white p-8 shadow-panel">
      <div className="space-y-3">
        <div className="h-2 w-16 rounded-full bg-[color:var(--accent-soft)]" />
        <h2 className="text-xl text-ink">{title}</h2>
        <p className="text-sm leading-7 text-[color:var(--muted)]">{description}</p>
      </div>
    </section>
  );
}
