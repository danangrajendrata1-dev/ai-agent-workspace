"use client";

import StatusBadge from "./StatusBadge";


function getRuntimeCapabilityStatusLabel(status) {
  switch (status) {
    case "suggestion_only":
      return "Suggestion only";
    case "explicit_confirm":
      return "Explicit confirmation required";
    case "forbidden":
      return "Forbidden";
    case "disabled":
    default:
      return "Disabled";
  }
}


function getRuntimeCapabilityStatusTone(status) {
  switch (status) {
    case "suggestion_only":
      return "neutral";
    case "explicit_confirm":
      return "warning";
    case "forbidden":
      return "danger";
    case "disabled":
    default:
      return "neutral";
  }
}


export default function RuntimeCapabilityPanel({
  capabilities = [],
  loading = false,
  error = "",
  title = "Runtime Capability Matrix",
  description = "Read-only safety metadata. No execution power is unlocked from this view.",
  emptyMessage = "No runtime capabilities are available yet."
}) {
  const visibleCapabilities = Array.isArray(capabilities)
    ? capabilities.filter((item) => item && item.userVisible !== false)
    : [];

  return (
    <div className="rounded-[16px] border border-[rgba(62,54,46,0.14)] bg-white p-4">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="min-w-0">
          <p className="text-[11px] uppercase tracking-[0.14em] text-[rgba(62,54,46,0.52)]">
            Capability matrix
          </p>
          <p className="mt-1 text-sm font-semibold text-[#3E362E]">{title}</p>
          <p className="mt-1 text-sm leading-6 text-[rgba(62,54,46,0.64)]">{description}</p>
        </div>
        <span className="rounded-full border border-[rgba(163,106,88,0.2)] bg-[rgba(163,106,88,0.1)] px-3 py-1 text-[11px] uppercase tracking-[0.14em] text-[#A36A58]">
          Read-only
        </span>
      </div>

      {loading ? (
        <div className="mt-3 rounded-[14px] border border-[rgba(62,54,46,0.12)] bg-[#F5F1E6] px-4 py-3 text-sm text-[rgba(62,54,46,0.64)]">
          Loading runtime capabilities...
        </div>
      ) : error ? (
        <div className="mt-3 rounded-[14px] border border-[rgba(163,106,88,0.2)] bg-[rgba(163,106,88,0.1)] px-4 py-3 text-sm leading-6 text-[#A36A58]">
          {error}
        </div>
      ) : visibleCapabilities.length ? (
        <div className="mt-3 space-y-2">
          {visibleCapabilities.map((capability) => (
            <div
              key={capability.key || capability.label}
              className="rounded-[14px] border border-[rgba(62,54,46,0.12)] bg-[#F5F1E6] px-4 py-3"
            >
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div className="min-w-0">
                  <p className="text-sm font-semibold text-[#3E362E]">{capability.label}</p>
                  <p className="mt-1 text-sm leading-6 text-[rgba(62,54,46,0.64)]">
                    {capability.description}
                  </p>
                </div>
                <div className="flex flex-wrap gap-2">
                  <StatusBadge
                    tone={getRuntimeCapabilityStatusTone(capability.status)}
                    label={getRuntimeCapabilityStatusLabel(capability.status)}
                  />
                  <span className="rounded-full border border-[rgba(62,54,46,0.12)] bg-white px-3 py-1 text-[11px] text-[rgba(62,54,46,0.72)]">
                    Confirmation: {capability.requiresConfirmation ? "Required" : "Not required"}
                  </span>
                </div>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="mt-3 rounded-[14px] border border-dashed border-[rgba(62,54,46,0.16)] bg-[rgba(229,224,211,0.34)] px-4 py-3 text-sm leading-6 text-[rgba(62,54,46,0.6)]">
          {emptyMessage}
        </div>
      )}
    </div>
  );
}
