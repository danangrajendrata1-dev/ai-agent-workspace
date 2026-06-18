"use client";

import StatusBadge from "./StatusBadge";


function getRuntimeReadinessTone(status) {
  switch (status) {
    case "planned":
    case "queued_future":
      return "warning";
    case "blocked":
    case "failed_future":
      return "danger";
    case "completed_future":
      return "success";
    case "disabled":
    default:
      return "neutral";
  }
}


function getRuntimeReadinessLabel(status) {
  switch (status) {
    case "planned":
      return "Planned";
    case "queued_future":
      return "Queued for future";
    case "blocked":
      return "Blocked";
    case "completed_future":
      return "Ready in future";
    case "failed_future":
      return "Failed";
    case "disabled":
    default:
      return "Disabled";
  }
}


function boolLabel(value) {
  return value ? "True" : "False";
}


export default function RuntimeReadinessPanel({
  readiness = null,
  loading = false,
  error = "",
  title = "Runtime readiness",
  description = "Read-only status for future runtime activation. Nothing is executable from this view.",
  emptyMessage = "Runtime readiness information is unavailable."
}) {
  return (
    <div className="rounded-[16px] border border-[rgba(62,54,46,0.14)] bg-white p-4">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="min-w-0">
          <p className="text-[11px] uppercase tracking-[0.14em] text-[rgba(62,54,46,0.52)]">
            Runtime readiness
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
          Loading runtime readiness...
        </div>
      ) : error ? (
        <div className="mt-3 rounded-[14px] border border-[rgba(163,106,88,0.2)] bg-[rgba(163,106,88,0.1)] px-4 py-3 text-sm leading-6 text-[#A36A58]">
          {error}
        </div>
      ) : readiness ? (
        <div className="mt-3 space-y-2">
          <div className="rounded-[14px] border border-[rgba(62,54,46,0.12)] bg-[#F5F1E6] px-4 py-3">
            <div className="flex flex-wrap items-start justify-between gap-3">
              <div className="min-w-0">
                <p className="text-sm font-semibold text-[#3E362E]">Runtime status</p>
                <p className="mt-1 text-sm leading-6 text-[rgba(62,54,46,0.64)]">
                  {readiness.message || emptyMessage}
                </p>
              </div>
              <StatusBadge
                tone={getRuntimeReadinessTone(readiness.status)}
                label={getRuntimeReadinessLabel(readiness.status)}
              />
            </div>
          </div>

          <div className="grid gap-2 md:grid-cols-2">
            <div className="rounded-[14px] border border-[rgba(62,54,46,0.12)] bg-[#F5F1E6] px-4 py-3">
              <p className="text-[11px] uppercase tracking-[0.14em] text-[rgba(62,54,46,0.52)]">
                Runtime execution enabled
              </p>
              <p className="mt-1 text-sm font-semibold text-[#3E362E]">
                {boolLabel(readiness.runtime_execution_enabled)}
              </p>
            </div>
            <div className="rounded-[14px] border border-[rgba(62,54,46,0.12)] bg-[#F5F1E6] px-4 py-3">
              <p className="text-[11px] uppercase tracking-[0.14em] text-[rgba(62,54,46,0.52)]">
                Tool execution enabled
              </p>
              <p className="mt-1 text-sm font-semibold text-[#3E362E]">
                {boolLabel(readiness.tool_execution_enabled)}
              </p>
            </div>
            <div className="rounded-[14px] border border-[rgba(62,54,46,0.12)] bg-[#F5F1E6] px-4 py-3">
              <p className="text-[11px] uppercase tracking-[0.14em] text-[rgba(62,54,46,0.52)]">
                Model raw generation enabled
              </p>
              <p className="mt-1 text-sm font-semibold text-[#3E362E]">
                {boolLabel(readiness.model_raw_generation_enabled)}
              </p>
            </div>
            <div className="rounded-[14px] border border-[rgba(62,54,46,0.12)] bg-[#F5F1E6] px-4 py-3">
              <p className="text-[11px] uppercase tracking-[0.14em] text-[rgba(62,54,46,0.52)]">
                Future safety review required
              </p>
              <p className="mt-1 text-sm font-semibold text-[#3E362E]">
                {boolLabel(readiness.requires_future_safety_review)}
              </p>
            </div>
          </div>
        </div>
      ) : (
        <div className="mt-3 rounded-[14px] border border-dashed border-[rgba(62,54,46,0.16)] bg-[rgba(229,224,211,0.34)] px-4 py-3 text-sm leading-6 text-[rgba(62,54,46,0.6)]">
          {emptyMessage}
        </div>
      )}
    </div>
  );
}
