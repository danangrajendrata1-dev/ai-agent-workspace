"use client";

import { useCallback, useEffect, useMemo, useState } from "react";

import {
  createWorkflowBinding,
  createWorkflowConsent,
  deleteWorkflowBinding,
  listWorkflowBindings,
  listWorkflowConsents,
  listWorkflowExecutions,
  listWorkflowTemplates
} from "../lib/apiClient";
import { formatDateTime, truncateText } from "../lib/format";


function normalizeCollection(payload) {
  if (Array.isArray(payload)) {
    return payload;
  }

  if (Array.isArray(payload?.items)) {
    return payload.items;
  }

  if (Array.isArray(payload?.data)) {
    return payload.data;
  }

  if (Array.isArray(payload?.results)) {
    return payload.results;
  }

  return [];
}


function getSafeErrorMessage(error, fallbackMessage) {
  if (error instanceof Error && error.message.trim()) {
    return error.message.trim();
  }

  return fallbackMessage;
}


function buildTemplateViewModel(template) {
  return {
    id: String(template?.id || ""),
    name: template?.name || "Unknown template",
    description: template?.description || "No description available.",
    templateVersion: template?.template_version || "1.0",
    riskLevel: template?.risk_level || "medium",
    outputType: template?.output_type || "json",
    enabled: Boolean(template?.enabled),
    maxPayloadBytes: Number(template?.max_payload_bytes || 0),
    consented: Boolean(template?.consented),
    consentedAt: template?.consented_at || null
  };
}


function buildConsentViewModel(consent) {
  return {
    id: String(consent?.id || ""),
    templateId: consent?.template_id || "",
    templateName: consent?.template_name || consent?.template_id || "Unknown template",
    templateVersion: consent?.template_version || "",
    consentedAt: consent?.consented_at || ""
  };
}


function buildBindingViewModel(binding) {
  return {
    id: String(binding?.id || ""),
    skillId: String(binding?.skill_id || ""),
    skillName: binding?.skill_name || "Deleted skill",
    skillType: binding?.skill_type || "workflow_skill",
    templateId: binding?.template_id || "",
    templateName: binding?.template_name || binding?.template_id || "Unknown template",
    templateVersion: binding?.template_version || "",
    createdAt: binding?.created_at || ""
  };
}


function buildExecutionViewModel(execution) {
  return {
    id: String(execution?.id || ""),
    templateId: execution?.template_id || "",
    templateName: execution?.template_name || execution?.template_id || "Unknown template",
    templateVersion: execution?.template_version || "",
    status: execution?.status || "unknown",
    errorMessage: execution?.error_message || "",
    httpStatusCode: execution?.http_status_code ?? null,
    outputSummary: execution?.output_summary || "",
    executedAt: execution?.executed_at || ""
  };
}


function buildWorkflowSkillOption(assignment) {
  const nestedSkill = assignment?.skill || {};
  const skillType = nestedSkill?.type || nestedSkill?.skillType || nestedSkill?.skill_type || "workflow_skill";
  return {
    id: String(assignment?.skillId || nestedSkill?.skillId || nestedSkill?.id || ""),
    title: nestedSkill?.title || nestedSkill?.name || "Workflow skill",
    skillType,
    isEnabled: Boolean(assignment?.isEnabled)
  };
}


export default function WorkflowToolsPanel({ activeAgent, activeAgentSkills = [] }) {
  const [templates, setTemplates] = useState([]);
  const [consents, setConsents] = useState([]);
  const [bindings, setBindings] = useState([]);
  const [executions, setExecutions] = useState([]);
  const [selectedTemplateId, setSelectedTemplateId] = useState("");
  const [selectedSkillId, setSelectedSkillId] = useState("");
  const [isLoading, setIsLoading] = useState(true);
  const [isSavingConsent, setIsSavingConsent] = useState("");
  const [isSavingBinding, setIsSavingBinding] = useState(false);
  const [deletingBindingId, setDeletingBindingId] = useState("");
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

  const workflowSkills = useMemo(
    () =>
      activeAgentSkills
        .map(buildWorkflowSkillOption)
        .filter((item) => item.isEnabled && item.skillType === "workflow_skill"),
    [activeAgentSkills]
  );

  const enabledTemplates = useMemo(
    () => templates.filter((template) => template.enabled),
    [templates]
  );

  const bindingLookup = useMemo(() => {
    const lookup = new Set();
    bindings.forEach((binding) => {
      lookup.add(`${binding.skillId}:${binding.templateId}`);
    });
    return lookup;
  }, [bindings]);

  const loadWorkflowData = useCallback(async () => {
    setIsLoading(true);
    setError("");

    try {
      const [templatesResponse, consentsResponse, bindingsResponse, executionsResponse] = await Promise.all([
        listWorkflowTemplates(),
        listWorkflowConsents(),
        listWorkflowBindings(),
        listWorkflowExecutions()
      ]);

      const nextTemplates = normalizeCollection(templatesResponse).map(buildTemplateViewModel);
      const nextConsents = normalizeCollection(consentsResponse).map(buildConsentViewModel);
      const nextBindings = normalizeCollection(bindingsResponse).map(buildBindingViewModel);
      const nextExecutions = normalizeCollection(executionsResponse).map(buildExecutionViewModel);

      setTemplates(nextTemplates);
      setConsents(nextConsents);
      setBindings(nextBindings);
      setExecutions(nextExecutions);
    } catch (loadError) {
      setTemplates([]);
      setConsents([]);
      setBindings([]);
      setExecutions([]);
      setError(getSafeErrorMessage(loadError, "Failed to load workflow templates."));
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadWorkflowData();
  }, [loadWorkflowData, activeAgent?.id]);

  useEffect(() => {
    if (!selectedTemplateId && enabledTemplates.length) {
      setSelectedTemplateId(enabledTemplates[0].id);
    }
  }, [enabledTemplates, selectedTemplateId]);

  useEffect(() => {
    if (!selectedSkillId && workflowSkills.length) {
      setSelectedSkillId(workflowSkills[0].id);
    }
  }, [workflowSkills, selectedSkillId]);

  const activeConsentLookup = useMemo(() => {
    const lookup = new Set();
    consents.forEach((consent) => {
      lookup.add(`${consent.templateId}:${consent.templateVersion}`);
    });
    return lookup;
  }, [consents]);

  const handleAllowTemplate = useCallback(
    async (templateId) => {
      if (!templateId || isSavingConsent) {
        return;
      }

      setIsSavingConsent(templateId);
      setError("");
      setNotice("");

      try {
        await createWorkflowConsent(templateId);
        setNotice("Template consent saved.");
        await loadWorkflowData();
      } catch (consentError) {
        setError(getSafeErrorMessage(consentError, "Failed to save template consent."));
      } finally {
        setIsSavingConsent("");
      }
    },
    [isSavingConsent, loadWorkflowData]
  );

  const handleCreateBinding = useCallback(async () => {
    if (!selectedSkillId || !selectedTemplateId || isSavingBinding) {
      return;
    }

    setIsSavingBinding(true);
    setError("");
    setNotice("");

    try {
      await createWorkflowBinding(selectedSkillId, selectedTemplateId);
      setNotice("Workflow skill binding saved.");
      await loadWorkflowData();
    } catch (bindingError) {
      setError(getSafeErrorMessage(bindingError, "Failed to save workflow binding."));
    } finally {
      setIsSavingBinding(false);
    }
  }, [isSavingBinding, loadWorkflowData, selectedSkillId, selectedTemplateId]);

  const handleDeleteBinding = useCallback(
    async (bindingId) => {
      if (!bindingId || deletingBindingId) {
        return;
      }

      setDeletingBindingId(bindingId);
      setError("");
      setNotice("");

      try {
        await deleteWorkflowBinding(bindingId);
        setNotice("Workflow binding deleted.");
        await loadWorkflowData();
      } catch (bindingError) {
        setError(getSafeErrorMessage(bindingError, "Failed to delete workflow binding."));
      } finally {
        setDeletingBindingId("");
      }
    },
    [deletingBindingId, loadWorkflowData]
  );

  const selectedTemplate = useMemo(
    () => templates.find((template) => template.id === selectedTemplateId) || null,
    [selectedTemplateId, templates]
  );

  const selectedTemplateBindingStatus = useMemo(() => {
    if (!selectedSkillId || !selectedTemplateId) {
      return false;
    }
    return bindingLookup.has(`${selectedSkillId}:${selectedTemplateId}`);
  }, [bindingLookup, selectedSkillId, selectedTemplateId]);

  return (
    <div className="rounded-[18px] border border-[rgba(62,54,46,0.14)] bg-[#F5F1E6] p-4">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="min-w-0">
          <p className="text-[11px] uppercase tracking-[0.18em] text-[rgba(62,54,46,0.56)]">
            Workflow Templates
          </p>
          <p className="mt-1 text-sm font-semibold text-[#3E362E]">
            Template registry, consent, bindings, and execution history.
          </p>
          <p className="mt-1 text-sm leading-6 text-[rgba(62,54,46,0.64)]">
            Execution is not enabled in this step. This panel only prepares consent, bindings, and audit history.
          </p>
        </div>
        <button
          type="button"
          onClick={loadWorkflowData}
          className="rounded-full border border-[rgba(62,54,46,0.14)] bg-white px-3 py-1.5 text-xs font-medium text-[#3E362E] transition hover:bg-[#efe7d6]"
        >
          Refresh
        </button>
      </div>

      {notice ? (
        <div className="mt-3 rounded-[14px] border border-[rgba(96,112,86,0.18)] bg-[rgba(96,112,86,0.08)] px-4 py-3 text-sm leading-6 text-[#607056]">
          {notice}
        </div>
      ) : null}

      {error ? (
        <div className="mt-3 rounded-[14px] border border-[rgba(163,106,88,0.2)] bg-[rgba(163,106,88,0.1)] px-4 py-3 text-sm leading-6 text-[#A36A58]">
          {error}
        </div>
      ) : null}

      <div className="mt-4 grid gap-4 lg:grid-cols-[1.5fr_1fr]">
        <div className="rounded-[16px] border border-[rgba(62,54,46,0.12)] bg-white p-3">
          <div className="flex items-center justify-between gap-3">
            <div>
              <p className="text-[11px] uppercase tracking-[0.14em] text-[rgba(62,54,46,0.52)]">
                Templates
              </p>
              <p className="mt-1 text-sm font-semibold text-[#3E362E]">Registry view</p>
            </div>
            <span className="rounded-full border border-[rgba(163,106,88,0.18)] bg-[rgba(163,106,88,0.08)] px-3 py-1 text-[11px] uppercase tracking-[0.14em] text-[#A36A58]">
              Read-only
            </span>
          </div>

          <div className="mt-3 space-y-3">
            {isLoading ? (
              <div className="rounded-[14px] border border-[rgba(62,54,46,0.12)] bg-[#F5F1E6] px-4 py-3 text-sm text-[rgba(62,54,46,0.64)]">
                Loading templates...
              </div>
            ) : templates.length ? (
              templates.map((template) => {
                const consented = activeConsentLookup.has(`${template.id}:${template.templateVersion}`);
                const canConsent = template.enabled && !consented;
                return (
                  <div
                    key={template.id}
                    className="rounded-[14px] border border-[rgba(62,54,46,0.12)] bg-[#F5F1E6] px-4 py-3"
                  >
                    <div className="flex flex-wrap items-start justify-between gap-3">
                      <div className="min-w-0">
                        <p className="text-sm font-semibold text-[#3E362E]">{template.name}</p>
                        <p className="mt-1 text-sm leading-6 text-[rgba(62,54,46,0.64)]">
                          {truncateText(template.description, 120)}
                        </p>
                      </div>
                      <div className="flex flex-wrap gap-2">
                        <span className="rounded-full border border-[rgba(62,54,46,0.12)] bg-white px-3 py-1 text-[11px] text-[rgba(62,54,46,0.72)]">
                          v{template.templateVersion}
                        </span>
                        <span className="rounded-full border border-[rgba(62,54,46,0.12)] bg-white px-3 py-1 text-[11px] text-[rgba(62,54,46,0.72)]">
                          {template.riskLevel}
                        </span>
                        <span
                          className={`rounded-full border px-3 py-1 text-[11px] ${
                            template.enabled
                              ? "border-[rgba(96,112,86,0.18)] bg-[rgba(96,112,86,0.08)] text-[#607056]"
                              : "border-[rgba(163,106,88,0.18)] bg-[rgba(163,106,88,0.08)] text-[#A36A58]"
                          }`}
                        >
                          {template.enabled ? "Enabled" : "Disabled"}
                        </span>
                        <span className="rounded-full border border-[rgba(62,54,46,0.12)] bg-white px-3 py-1 text-[11px] text-[rgba(62,54,46,0.72)]">
                          {consented ? "Consented" : "Not consented"}
                        </span>
                      </div>
                    </div>

                    <div className="mt-3 flex flex-wrap items-center justify-between gap-3">
                      <p className="text-xs leading-5 text-[rgba(62,54,46,0.58)]">
                        Output: {template.outputType} | Payload limit: {template.maxPayloadBytes} bytes
                      </p>
                      <button
                        type="button"
                        onClick={() => handleAllowTemplate(template.id)}
                        disabled={!canConsent || isSavingConsent === template.id}
                        className="rounded-full bg-[#A36A58] px-3 py-1.5 text-xs font-medium text-white transition hover:bg-[#94604f] disabled:cursor-not-allowed disabled:opacity-70"
                      >
                        {isSavingConsent === template.id ? "Saving..." : "Allow Template"}
                      </button>
                    </div>
                  </div>
                );
              })
            ) : (
              <div className="rounded-[14px] border border-dashed border-[rgba(62,54,46,0.16)] bg-[rgba(229,224,211,0.34)] px-4 py-3 text-sm leading-6 text-[rgba(62,54,46,0.6)]">
                No workflow templates available.
              </div>
            )}
          </div>
        </div>

        <div className="space-y-4">
          <div className="rounded-[16px] border border-[rgba(62,54,46,0.12)] bg-white p-3">
            <p className="text-[11px] uppercase tracking-[0.14em] text-[rgba(62,54,46,0.52)]">
              Binding
            </p>
            <p className="mt-1 text-sm font-semibold text-[#3E362E]">Attach a workflow skill to a template</p>

            <div className="mt-3 space-y-3">
              <label className="grid gap-2">
                <span className="text-xs uppercase tracking-[0.14em] text-[rgba(62,54,46,0.52)]">
                  Workflow skill
                </span>
                <select
                  value={selectedSkillId}
                  onChange={(event) => setSelectedSkillId(event.target.value)}
                  className="rounded-[14px] border border-[rgba(62,54,46,0.14)] bg-white px-3 py-2 text-sm text-[#3E362E] outline-none transition focus:border-[#A36A58]"
                >
                  {!workflowSkills.length ? <option value="">No workflow skill available</option> : null}
                  {workflowSkills.map((skill) => (
                    <option key={skill.id} value={skill.id}>
                      {skill.title}
                    </option>
                  ))}
                </select>
              </label>

              <label className="grid gap-2">
                <span className="text-xs uppercase tracking-[0.14em] text-[rgba(62,54,46,0.52)]">
                  Template
                </span>
                <select
                  value={selectedTemplateId}
                  onChange={(event) => setSelectedTemplateId(event.target.value)}
                  className="rounded-[14px] border border-[rgba(62,54,46,0.14)] bg-white px-3 py-2 text-sm text-[#3E362E] outline-none transition focus:border-[#A36A58]"
                >
                  {!templates.length ? <option value="">No template available</option> : null}
                  {templates.map((template) => (
                    <option key={template.id} value={template.id}>
                      {template.name} {template.enabled ? "" : "(disabled)"}
                    </option>
                  ))}
                </select>
              </label>

              <div className="flex flex-wrap items-center justify-between gap-3">
                <p className="text-xs leading-5 text-[rgba(62,54,46,0.58)]">
                  {selectedTemplate
                    ? `Selected template is ${selectedTemplate.enabled ? "available" : "disabled"} for consent and binding.`
                    : "Select a template to bind."}
                </p>
                <button
                  type="button"
                  onClick={handleCreateBinding}
                  disabled={!selectedSkillId || !selectedTemplateId || !selectedTemplate?.enabled || isSavingBinding}
                  className="rounded-full bg-[#A36A58] px-3 py-1.5 text-xs font-medium text-white transition hover:bg-[#94604f] disabled:cursor-not-allowed disabled:opacity-70"
                >
                  {isSavingBinding ? "Saving..." : "Bind Template"}
                </button>
              </div>
              {selectedTemplateBindingStatus ? (
                <p className="text-xs leading-5 text-[rgba(96,112,86,0.72)]">
                  Binding already exists for the selected skill and template.
                </p>
              ) : null}
            </div>
          </div>

          <div className="rounded-[16px] border border-[rgba(62,54,46,0.12)] bg-white p-3">
            <div className="flex items-center justify-between gap-3">
              <div>
                <p className="text-[11px] uppercase tracking-[0.14em] text-[rgba(62,54,46,0.52)]">
                  Consents
                </p>
                <p className="mt-1 text-sm font-semibold text-[#3E362E]">Saved template permissions</p>
              </div>
              <span className="rounded-full border border-[rgba(62,54,46,0.12)] bg-[#F5F1E6] px-3 py-1 text-[11px] text-[rgba(62,54,46,0.72)]">
                {consents.length}
              </span>
            </div>

            <div className="mt-3 space-y-2">
              {consents.length ? (
                consents.map((consent) => (
                  <div
                    key={consent.id}
                    className="rounded-[14px] border border-[rgba(62,54,46,0.12)] bg-[#F5F1E6] px-4 py-3"
                  >
                    <p className="text-sm font-semibold text-[#3E362E]">{consent.templateName}</p>
                    <p className="mt-1 text-xs leading-5 text-[rgba(62,54,46,0.58)]">
                      v{consent.templateVersion} | {formatDateTime(consent.consentedAt)}
                    </p>
                  </div>
                ))
              ) : (
                <div className="rounded-[14px] border border-dashed border-[rgba(62,54,46,0.16)] bg-[rgba(229,224,211,0.34)] px-4 py-3 text-sm leading-6 text-[rgba(62,54,46,0.6)]">
                  No saved consents yet.
                </div>
              )}
            </div>
          </div>

          <div className="rounded-[16px] border border-[rgba(62,54,46,0.12)] bg-white p-3">
            <div className="flex items-center justify-between gap-3">
              <div>
                <p className="text-[11px] uppercase tracking-[0.14em] text-[rgba(62,54,46,0.52)]">
                  Bindings
                </p>
                <p className="mt-1 text-sm font-semibold text-[#3E362E]">Workflow skill bindings</p>
              </div>
              <span className="rounded-full border border-[rgba(62,54,46,0.12)] bg-[#F5F1E6] px-3 py-1 text-[11px] text-[rgba(62,54,46,0.72)]">
                {bindings.length}
              </span>
            </div>

            <div className="mt-3 space-y-2">
              {bindings.length ? (
                bindings.map((binding) => (
                  <div
                    key={binding.id}
                    className="rounded-[14px] border border-[rgba(62,54,46,0.12)] bg-[#F5F1E6] px-4 py-3"
                  >
                    <div className="flex flex-wrap items-start justify-between gap-3">
                      <div className="min-w-0">
                        <p className="text-sm font-semibold text-[#3E362E]">{binding.skillName}</p>
                        <p className="mt-1 text-xs leading-5 text-[rgba(62,54,46,0.58)]">
                          {binding.templateName} | v{binding.templateVersion}
                        </p>
                      </div>
                      <button
                        type="button"
                        onClick={() => handleDeleteBinding(binding.id)}
                        disabled={deletingBindingId === binding.id}
                        className="rounded-full border border-[rgba(163,106,88,0.18)] bg-white px-3 py-1.5 text-xs font-medium text-[#A36A58] transition hover:bg-[rgba(163,106,88,0.08)] disabled:cursor-not-allowed disabled:opacity-70"
                      >
                        {deletingBindingId === binding.id ? "Deleting..." : "Delete Binding"}
                      </button>
                    </div>
                  </div>
                ))
              ) : (
                <div className="rounded-[14px] border border-dashed border-[rgba(62,54,46,0.16)] bg-[rgba(229,224,211,0.34)] px-4 py-3 text-sm leading-6 text-[rgba(62,54,46,0.6)]">
                  No workflow bindings saved yet.
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      <div className="mt-4 rounded-[16px] border border-[rgba(62,54,46,0.12)] bg-white p-3">
        <div className="flex items-center justify-between gap-3">
          <div>
            <p className="text-[11px] uppercase tracking-[0.14em] text-[rgba(62,54,46,0.52)]">
              History
            </p>
            <p className="mt-1 text-sm font-semibold text-[#3E362E]">Execution history</p>
          </div>
          <span className="rounded-full border border-[rgba(163,106,88,0.18)] bg-[rgba(163,106,88,0.08)] px-3 py-1 text-[11px] uppercase tracking-[0.14em] text-[#A36A58]">
            Read-only
          </span>
        </div>

        <div className="mt-3 space-y-2">
          {executions.length ? (
            executions.map((execution) => (
              <div
                key={execution.id}
                className="rounded-[14px] border border-[rgba(62,54,46,0.12)] bg-[#F5F1E6] px-4 py-3"
              >
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <div className="min-w-0">
                    <p className="text-sm font-semibold text-[#3E362E]">{execution.templateName}</p>
                    <p className="mt-1 text-xs leading-5 text-[rgba(62,54,46,0.58)]">
                      {execution.templateVersion} | {formatDateTime(execution.executedAt)}
                    </p>
                  </div>
                  <span className="rounded-full border border-[rgba(62,54,46,0.12)] bg-white px-3 py-1 text-[11px] text-[rgba(62,54,46,0.72)]">
                    {execution.status}
                  </span>
                </div>
                {execution.outputSummary ? (
                  <p className="mt-2 text-sm leading-6 text-[rgba(62,54,46,0.68)]">
                    {truncateText(execution.outputSummary, 160)}
                  </p>
                ) : null}
                {execution.errorMessage ? (
                  <p className="mt-2 text-sm leading-6 text-[#A36A58]">
                    {truncateText(execution.errorMessage, 160)}
                  </p>
                ) : null}
              </div>
            ))
          ) : (
            <div className="rounded-[14px] border border-dashed border-[rgba(62,54,46,0.16)] bg-[rgba(229,224,211,0.34)] px-4 py-3 text-sm leading-6 text-[rgba(62,54,46,0.6)]">
              No execution history yet.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
