export default function KeyValueList({ items }) {
  return (
    <dl className="grid gap-4 md:grid-cols-2">
      {items.map((item) => (
        <div key={item.label} className="rounded-3xl border border-[var(--border)] bg-[color:var(--mist)] p-4">
          <dt className="text-xs uppercase tracking-[0.16em] text-[color:var(--muted)]">
            {item.label}
          </dt>
          <dd className="mt-2 break-words text-sm leading-7 text-ink">
            {item.value}
          </dd>
        </div>
      ))}
    </dl>
  );
}
