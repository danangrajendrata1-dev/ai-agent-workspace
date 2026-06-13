export default function StatusBadge({ label, tone = "neutral" }) {
  const toneClasses = {
    success: "border-[#cbe7df] bg-[#edf9f4] text-[#1c6b5c]",
    danger: "border-[#f0cfcf] bg-[#fff4f4] text-[#a33a3a]",
    warning: "border-[#f0dfbf] bg-[#fff8eb] text-[#8f6424]",
    neutral: "border-[var(--border)] bg-white text-[color:var(--muted)]"
  };

  return (
    <span className={`inline-flex rounded-full border px-3 py-1 text-xs font-semibold uppercase tracking-[0.18em] ${toneClasses[tone] || toneClasses.neutral}`}>
      {label}
    </span>
  );
}
