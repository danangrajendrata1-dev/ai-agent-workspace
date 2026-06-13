function getInitials(agent) {
  const source = agent?.icon || agent?.name || "AG";
  const text = String(source).trim();

  if (text.length <= 2) {
    return text.toUpperCase();
  }

  return text
    .split(" ")
    .slice(0, 2)
    .map((part) => part[0] || "")
    .join("")
    .toUpperCase();
}

function getCardTheme(agent) {
  const lowerName = (agent?.name || "").toLowerCase();
  if (lowerName.includes("2") || lowerName.includes("green")) {
    return {
      border: "border-[rgba(96,112,86,0.28)]",
      glow: "shadow-none",
      iconBg: "bg-[rgba(96,112,86,0.12)]",
      iconBorder: "border-[rgba(96,112,86,0.24)]",
      iconColor: "text-[#607056]",
      dot: "bg-[#607056]"
    };
  }

  return {
    border: "border-[rgba(163,106,88,0.22)]",
    glow: "shadow-none",
    iconBg: "bg-[rgba(163,106,88,0.12)]",
    iconBorder: "border-[rgba(163,106,88,0.2)]",
    iconColor: "text-[#A36A58]",
    dot: "bg-[#A36A58]"
  };
}

export default function AgentCard({ agent }) {
  const theme = getCardTheme(agent);

  return (
    <div className={`min-h-[124px] rounded-[18px] border bg-[#F5F1E6] p-4 ${theme.border} ${theme.glow}`}>
      <div className="flex items-start gap-3">
        <div className={`flex h-12 w-12 shrink-0 items-center justify-center rounded-[14px] border ${theme.iconBorder} ${theme.iconBg} text-[18px] font-semibold uppercase tracking-[0.14em] ${theme.iconColor}`}>
          {getInitials(agent)}
        </div>
        <div className="min-w-0">
          <p className="truncate text-[15px] font-semibold text-[#3E362E]">{agent?.name || "Untitled"}</p>
          <p className="mt-1 truncate text-[12px] text-[rgba(62,54,46,0.6)]">{agent?.skill || "skill name"}</p>
        </div>
      </div>

      <div className="mt-4 space-y-2.5">
        <div className="flex items-center gap-2 text-[12px] text-[rgba(62,54,46,0.7)]">
          <span className={`h-2.5 w-2.5 rounded-full ${theme.dot}`} />
          <span>{agent?.status === "active" ? "Active associate" : "Saved locally"}</span>
        </div>
        <div className="flex items-center gap-2 text-[12px] text-[rgba(62,54,46,0.7)]">
          <span className={`h-2.5 w-2.5 rounded-full ${theme.dot}`} />
          <span>{agent?.defaultModelName || "Preview only"}</span>
        </div>
      </div>
    </div>
  );
}
