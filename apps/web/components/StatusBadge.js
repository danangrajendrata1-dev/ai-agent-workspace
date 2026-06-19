export default function StatusBadge({ label, tone = "neutral" }) {
  const toneClasses = {
    success: "border-[#d7e7db] bg-[#edf5ef] text-[#5f826f]",
    danger: "border-[#ead0cc] bg-[#f8ece8] text-[#b05b50]",
    warning: "border-[#eadfbd] bg-[#f7efd9] text-[#9a6d19]",
    neutral: "border-[rgba(62,54,46,0.12)] bg-[#f4ecdf] text-[rgba(62,54,46,0.66)]"
  };

  return (
    <span className={`inline-flex rounded-full border px-2.5 py-1 text-[11px] font-medium capitalize tracking-normal ${toneClasses[tone] || toneClasses.neutral}`}>
      {label}
    </span>
  );
}
