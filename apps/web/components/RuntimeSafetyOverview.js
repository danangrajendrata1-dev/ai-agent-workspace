"use client";

import RuntimeCapabilityPanel from "./RuntimeCapabilityPanel";
import RuntimeEventContractPanel from "./RuntimeEventContractPanel";
import RuntimeReadinessPanel from "./RuntimeReadinessPanel";

function statusPillClassName(index) {
  const classes = [
    "border-[rgba(96,112,86,0.18)] bg-[rgba(96,112,86,0.08)] text-[#607056]",
    "border-[rgba(163,106,88,0.18)] bg-[rgba(163,106,88,0.08)] text-[#A36A58]",
    "border-[rgba(62,54,46,0.12)] bg-white text-[rgba(62,54,46,0.72)]",
  ];

  return classes[index] || classes[2];
}


export default function RuntimeSafetyOverview({
  capabilities = [],
  capabilitiesLoading = false,
  capabilitiesError = "",
  readiness = null,
  readinessLoading = false,
  readinessError = "",
  contract = null,
  contractLoading = false,
  contractError = "",
}) {
  const runtimeIsDisabled = readiness?.runtime_execution_enabled === false;
  const toolExecutionBlocked = readiness?.tool_execution_enabled === false;
  const modelGenerationBlocked = readiness?.model_raw_generation_enabled === false;

  const statusPills = [
    runtimeIsDisabled ? "Runtime not active" : "Runtime preview only",
    toolExecutionBlocked && modelGenerationBlocked
      ? "Tool/model blocked"
      : toolExecutionBlocked
        ? "Tool blocked"
        : modelGenerationBlocked
          ? "Model blocked"
          : "Tool/model preview",
    readiness?.requires_future_safety_review === false ? "Review not required" : "Future review required",
  ];

  return (
    <section className="space-y-4">
      <div className="rounded-[18px] border border-[rgba(62,54,46,0.14)] bg-[#F5F1E6] p-4">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div className="min-w-0">
            <p className="text-[11px] uppercase tracking-[0.18em] text-[rgba(62,54,46,0.56)]">
              Runtime safety overview
            </p>
            <p className="mt-1 text-base font-semibold text-[#3E362E]">
              Runtime is not active. Tool/model execution remains blocked.
            </p>
            <p className="mt-1 text-sm leading-6 text-[rgba(62,54,46,0.64)]">
              Future execution still requires a safety review and backend validation. This section is
              read-only.
            </p>
          </div>
          <div className="flex flex-wrap gap-2">
            {statusPills.map((label, index) => (
              <span
                key={label}
                className={`rounded-full border px-3 py-1 text-[11px] uppercase tracking-[0.14em] ${statusPillClassName(index)}`}
              >
                {label}
              </span>
            ))}
          </div>
        </div>

        <div className="mt-3 grid gap-3 lg:grid-cols-2">
          <RuntimeReadinessPanel
            readiness={readiness}
            loading={readinessLoading}
            error={readinessError}
            title="Runtime readiness status"
            description="Read-only status for future runtime activation. Nothing is executable from this view."
            emptyMessage="Runtime readiness is not available yet."
          />

          <RuntimeCapabilityPanel
            capabilities={capabilities}
            loading={capabilitiesLoading}
            error={capabilitiesError}
            title="Runtime capability matrix"
            description="Read-only safety metadata from the backend. It does not unlock execution or bypass validation."
            emptyMessage="No user-visible runtime capabilities are available yet."
          />
        </div>

        <details className="mt-3 rounded-[16px] border border-[rgba(62,54,46,0.14)] bg-white p-4" open>
          <summary className="flex cursor-pointer list-none items-center justify-between gap-3">
            <div className="min-w-0">
              <p className="text-[11px] uppercase tracking-[0.14em] text-[rgba(62,54,46,0.52)]">
                Runtime event contract
              </p>
              <p className="mt-1 text-sm font-semibold text-[#3E362E]">
                Safe future event fields, statuses, and forbidden fields
              </p>
            </div>
            <span className="rounded-full border border-[rgba(163,106,88,0.2)] bg-[rgba(163,106,88,0.1)] px-3 py-1 text-[11px] uppercase tracking-[0.14em] text-[#A36A58]">
              Read-only
            </span>
          </summary>

          <p className="mt-2 text-sm leading-6 text-[rgba(62,54,46,0.64)]">
            Contract metadata is visible for future planning only. It does not create runtime
            history, event records, or execution permissions.
          </p>

          <div className="mt-3">
            <RuntimeEventContractPanel
              contract={contract}
              loading={contractLoading}
              error={contractError}
              title="Event contract reference"
              description="Compact read-only contract metadata for future runtime event reporting. It does not unlock execution."
              emptyMessage="Runtime event contract is not available yet."
            />
          </div>
        </details>
      </div>
    </section>
  );
}
