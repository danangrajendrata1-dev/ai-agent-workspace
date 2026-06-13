export default function TemplateCard({
  name,
  icon,
  description,
  buttonLabel = "Select",
  onAction,
  disabled = false
}) {
  return (
    <article className="rounded-[18px] border border-[rgba(62,54,46,0.14)] bg-[#F5F1E6] p-4">
      <div className="flex items-start justify-between gap-3">
        <div className="flex h-10 w-10 items-center justify-center rounded-[12px] bg-[rgba(163,106,88,0.12)] text-xs font-semibold uppercase tracking-[0.14em] text-[#A36A58]">
          {icon}
        </div>
        <button
          type="button"
          onClick={onAction}
          disabled={disabled}
          className="rounded-full border border-[rgba(62,54,46,0.14)] bg-[#E5E0D3] px-3 py-1.5 text-xs text-[rgba(62,54,46,0.76)] transition hover:bg-[#D5CFBF] disabled:cursor-not-allowed disabled:opacity-70"
        >
          {buttonLabel}
        </button>
      </div>
      <h3 className="mt-3 text-sm font-semibold text-[#3E362E]">{name}</h3>
      <p className="mt-2 text-xs leading-6 text-[rgba(62,54,46,0.62)]">{description}</p>
    </article>
  );
}
