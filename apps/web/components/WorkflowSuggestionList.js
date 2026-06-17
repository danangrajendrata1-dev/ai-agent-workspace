"use client";

export function buildWorkflowSuggestionKey(suggestion, index = 0) {
  return `${suggestion?.template_id || "workflow"}-${suggestion?.skill_id || index}`;
}

export default function WorkflowSuggestionList({
  suggestions = [],
  agentId = "",
  onConfirmExecute,
  executionStates = {}
}) {
  if (!Array.isArray(suggestions) || suggestions.length === 0) {
    return null;
  }

  return (
    <div className="mt-3 space-y-2">
      {suggestions.map((suggestion, index) => {
        const suggestionKey = buildWorkflowSuggestionKey(suggestion, index);
        const templateName = suggestion?.template_name || "Workflow template";
        const skillTitle = suggestion?.skill_title || "Workflow skill";
        const reason = suggestion?.reason || "Matched workflow skill with task";
        const consentRequired = Boolean(suggestion?.consent_required);
        const bindingExists = Boolean(suggestion?.binding_exists);
        const executionAvailable = Boolean(suggestion?.execution_available);
        const executionState = executionStates?.[suggestionKey] || null;
        const canConfirmExecute =
          executionAvailable && Boolean(agentId) && typeof onConfirmExecute === "function";
        const isExecuting = executionState?.status === "executing";

        return (
          <div
            key={suggestionKey}
            className="rounded-[14px] border border-[rgba(96,112,86,0.18)] bg-[rgba(96,112,86,0.06)] px-4 py-3"
          >
            <div className="flex flex-wrap items-start justify-between gap-3">
              <div className="min-w-0">
                <p className="text-xs uppercase tracking-[0.14em] text-[rgba(62,54,46,0.52)]">
                  Workflow available
                </p>
                <p className="mt-1 text-sm font-semibold text-[#3E362E]">{templateName}</p>
                <p className="mt-1 text-sm leading-6 text-[rgba(62,54,46,0.72)]">
                  Matched skill: {skillTitle}
                </p>
              </div>
              <div className="flex flex-wrap gap-2">
                <span className="rounded-full border border-[rgba(62,54,46,0.12)] bg-white px-3 py-1 text-[11px] text-[rgba(62,54,46,0.72)]">
                  Consent: {consentRequired ? "Required" : "Allowed"}
                </span>
                <span className="rounded-full border border-[rgba(62,54,46,0.12)] bg-white px-3 py-1 text-[11px] text-[rgba(62,54,46,0.72)]">
                  Binding: {bindingExists ? "Bound" : "Not bound"}
                </span>
                <span className="rounded-full border border-[rgba(62,54,46,0.12)] bg-white px-3 py-1 text-[11px] text-[rgba(62,54,46,0.72)]">
                  Execution: {executionAvailable ? "Available" : "Not ready"}
                </span>
              </div>
            </div>

            <p className="mt-2 text-sm leading-6 text-[rgba(62,54,46,0.72)]">{reason}</p>

            {executionAvailable ? (
              <>
                <div className="mt-3 flex flex-wrap items-center gap-3">
                  {canConfirmExecute ? (
                    <button
                      type="button"
                      onClick={() => onConfirmExecute(suggestion)}
                      disabled={isExecuting}
                      className="rounded-full bg-[#A36A58] px-3 py-1.5 text-xs font-medium text-white transition hover:bg-[#94604f] disabled:cursor-not-allowed disabled:opacity-70"
                    >
                      {isExecuting ? "Executing..." : "Confirm Execute"}
                    </button>
                  ) : (
                    <span className="rounded-full border border-[rgba(62,54,46,0.12)] bg-white px-3 py-1 text-[11px] text-[rgba(62,54,46,0.72)]">
                      Confirm execution unavailable in this view.
                    </span>
                  )}
                  <span className="text-xs leading-5 text-[rgba(62,54,46,0.58)]">
                    Executes only after an explicit click for this run.
                  </span>
                </div>
                {executionState?.message ? (
                  <p
                    className={`mt-2 text-xs leading-5 ${
                      executionState.status === "success"
                        ? "text-[#607056]"
                        : executionState.status === "executing"
                          ? "text-[rgba(62,54,46,0.58)]"
                          : "text-[#A36A58]"
                    }`}
                  >
                    {executionState.message}
                  </p>
                ) : null}
              </>
            ) : (
              <p className="mt-2 text-xs leading-5 text-[rgba(62,54,46,0.58)]">
                {consentRequired
                  ? "Consent is required before execution. Use Advanced Workflow Tools."
                  : bindingExists
                    ? "Template metadata is ready for manual execution review."
                    : "Bind this workflow skill in Advanced Workflow Tools."}
              </p>
            )}
          </div>
        );
      })}
    </div>
  );
}
