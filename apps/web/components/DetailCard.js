export default function DetailCard({ title, children }) {
  return (
    <section className="rounded-[28px] border border-[var(--border)] bg-white p-6 shadow-panel">
      <div className="space-y-4">
        <h2 className="text-2xl text-ink">{title}</h2>
        {children}
      </div>
    </section>
  );
}
