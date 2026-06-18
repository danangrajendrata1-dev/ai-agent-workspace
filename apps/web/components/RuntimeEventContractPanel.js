"use client";

import StatusBadge from "./StatusBadge";


function getTruncatedList(items, limit = 6) {
  if (!Array.isArray(items) || !items.length) {
    return [];
  }

  const visibleItems = items.slice(0, limit);
  const remainingCount = items.length - visibleItems.length;
  if (remainingCount > 0) {
    visibleItems.push(`+${remainingCount} more`);
  }

  return visibleItems;
}


function renderStatusBadge(value) {
  return (
    <StatusBadge
      tone={value === "disabled" ? "neutral" : value === "blocked" ? "danger" : value === "completed_future" ? "success" : "warning"}
      label={value}
    />
  );
}


export default function RuntimeEventContractPanel({
  contract = null,
  loading = false,
  error = "",
  title = "Runtime event contract",
  description = "Read-only contract metadata for future runtime event reporting. It does not unlock execution.",
  emptyMessage = "Runtime event contract information is unavailable."
}) {
  const eventFields = Array.isArray(contract?.event_fields) ? contract.event_fields : [];
  const forbiddenFields = Array.isArray(contract?.forbidden_fields) ? contract.forbidden_fields : [];
  const safeFieldNames = eventFields.map((field) => field?.name).filter(Boolean);

  return (
    <div className="rounded-[16px] border border-[rgba(62,54,46,0.14)] bg-white p-4">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="min-w-0">
          <p className="text-[11px] uppercase tracking-[0.14em] text-[rgba(62,54,46,0.52)]">
            Runtime event contract
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
          Loading runtime event contract...
        </div>
      ) : error ? (
        <div className="mt-3 rounded-[14px] border border-[rgba(163,106,88,0.2)] bg-[rgba(163,106,88,0.1)] px-4 py-3 text-sm leading-6 text-[#A36A58]">
          {error}
        </div>
      ) : contract ? (
        <div className="mt-3 space-y-2">
          <div className="rounded-[14px] border border-[rgba(62,54,46,0.12)] bg-[#F5F1E6] px-4 py-3">
            <div className="flex flex-wrap items-start justify-between gap-3">
              <div className="min-w-0">
                <p className="text-sm font-semibold text-[#3E362E]">Contract status</p>
                <p className="mt-1 text-sm leading-6 text-[rgba(62,54,46,0.64)]">
                  {contract.message || emptyMessage}
                </p>
              </div>
              {renderStatusBadge(contract.status)}
            </div>
          </div>

          <div className="grid gap-2 md:grid-cols-2">
            <div className="rounded-[14px] border border-[rgba(62,54,46,0.12)] bg-[#F5F1E6] px-4 py-3">
              <p className="text-[11px] uppercase tracking-[0.14em] text-[rgba(62,54,46,0.52)]">
                Allowed statuses
              </p>
              <div className="mt-2 flex flex-wrap gap-2">
                {Array.isArray(contract.event_status_values) && contract.event_status_values.length ? (
                  contract.event_status_values.map((value) => (
                    <span
                      key={value}
                      className="rounded-full border border-[rgba(62,54,46,0.12)] bg-white px-2.5 py-1 text-[11px] text-[rgba(62,54,46,0.72)]"
                    >
                      {value}
                    </span>
                  ))
                ) : (
                  <span className="text-sm text-[rgba(62,54,46,0.6)]">None</span>
                )}
              </div>
            </div>

            <div className="rounded-[14px] border border-[rgba(62,54,46,0.12)] bg-[#F5F1E6] px-4 py-3">
              <p className="text-[11px] uppercase tracking-[0.14em] text-[rgba(62,54,46,0.52)]">
                Event types
              </p>
              <div className="mt-2 flex flex-wrap gap-2">
                {Array.isArray(contract.event_type_values) && contract.event_type_values.length ? (
                  contract.event_type_values.map((value) => (
                    <span
                      key={value}
                      className="rounded-full border border-[rgba(62,54,46,0.12)] bg-white px-2.5 py-1 text-[11px] text-[rgba(62,54,46,0.72)]"
                    >
                      {value}
                    </span>
                  ))
                ) : (
                  <span className="text-sm text-[rgba(62,54,46,0.6)]">None</span>
                )}
              </div>
            </div>

            <div className="rounded-[14px] border border-[rgba(62,54,46,0.12)] bg-[#F5F1E6] px-4 py-3">
              <p className="text-[11px] uppercase tracking-[0.14em] text-[rgba(62,54,46,0.52)]">
                Confirmation states
              </p>
              <div className="mt-2 flex flex-wrap gap-2">
                {Array.isArray(contract.confirmation_state_values) && contract.confirmation_state_values.length ? (
                  contract.confirmation_state_values.map((value) => (
                    <span
                      key={value}
                      className="rounded-full border border-[rgba(62,54,46,0.12)] bg-white px-2.5 py-1 text-[11px] text-[rgba(62,54,46,0.72)]"
                    >
                      {value}
                    </span>
                  ))
                ) : (
                  <span className="text-sm text-[rgba(62,54,46,0.6)]">None</span>
                )}
              </div>
            </div>

            <div className="rounded-[14px] border border-[rgba(62,54,46,0.12)] bg-[#F5F1E6] px-4 py-3">
              <p className="text-[11px] uppercase tracking-[0.14em] text-[rgba(62,54,46,0.52)]">
                Safe fields
              </p>
              <div className="mt-2 flex flex-wrap gap-2">
                {safeFieldNames.length ? (
                  safeFieldNames.map((value) => (
                    <span
                      key={value}
                      className="rounded-full border border-[rgba(96,112,86,0.18)] bg-[rgba(96,112,86,0.08)] px-2.5 py-1 text-[11px] text-[#607056]"
                    >
                      {value}
                    </span>
                  ))
                ) : (
                  <span className="text-sm text-[rgba(62,54,46,0.6)]">None</span>
                )}
              </div>
            </div>
          </div>

          <div className="rounded-[14px] border border-[rgba(62,54,46,0.12)] bg-[#F5F1E6] px-4 py-3">
            <p className="text-[11px] uppercase tracking-[0.14em] text-[rgba(62,54,46,0.52)]">
              Forbidden fields
            </p>
            <div className="mt-2 flex flex-wrap gap-2">
              {getTruncatedList(forbiddenFields).length ? (
                getTruncatedList(forbiddenFields).map((value) => (
                  <span
                    key={value}
                    className={`rounded-full border px-2.5 py-1 text-[11px] ${
                      value.startsWith("+")
                        ? "border-[rgba(62,54,46,0.12)] bg-white text-[rgba(62,54,46,0.72)]"
                        : "border-[rgba(163,106,88,0.18)] bg-[rgba(163,106,88,0.08)] text-[#A36A58]"
                    }`}
                  >
                    {value}
                  </span>
                ))
              ) : (
                <span className="text-sm text-[rgba(62,54,46,0.6)]">None</span>
              )}
            </div>
          </div>

          <div className="grid gap-2 md:grid-cols-2">
            <div className="rounded-[14px] border border-[rgba(62,54,46,0.12)] bg-[#F5F1E6] px-4 py-3">
              <p className="text-[11px] uppercase tracking-[0.14em] text-[rgba(62,54,46,0.52)]">
                Guard requirements
              </p>
              <ul className="mt-2 space-y-1 text-sm leading-6 text-[rgba(62,54,46,0.72)]">
                {Array.isArray(contract.guard_requirements) && contract.guard_requirements.length ? (
                  contract.guard_requirements.slice(0, 4).map((value) => (
                    <li key={value} className="flex gap-2">
                      <span className="mt-[9px] h-1.5 w-1.5 rounded-full bg-[rgba(163,106,88,0.55)]" />
                      <span className="min-w-0">{value}</span>
                    </li>
                  ))
                ) : (
                  <li className="text-[rgba(62,54,46,0.6)]">None</li>
                )}
              </ul>
            </div>

            <div className="rounded-[14px] border border-[rgba(62,54,46,0.12)] bg-[#F5F1E6] px-4 py-3">
              <p className="text-[11px] uppercase tracking-[0.14em] text-[rgba(62,54,46,0.52)]">
                Logging rules
              </p>
              <ul className="mt-2 space-y-1 text-sm leading-6 text-[rgba(62,54,46,0.72)]">
                {Array.isArray(contract.logging_rules) && contract.logging_rules.length ? (
                  contract.logging_rules.slice(0, 4).map((value) => (
                    <li key={value} className="flex gap-2">
                      <span className="mt-[9px] h-1.5 w-1.5 rounded-full bg-[rgba(163,106,88,0.55)]" />
                      <span className="min-w-0">{value}</span>
                    </li>
                  ))
                ) : (
                  <li className="text-[rgba(62,54,46,0.6)]">None</li>
                )}
              </ul>
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
