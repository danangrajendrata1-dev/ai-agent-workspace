"use client";

import { useEffect, useState } from "react";

import AppShell from "../../components/AppShell";
import ErrorState from "../../components/ErrorState";
import LoadingState from "../../components/LoadingState";
import ProtectedRoute from "../../components/ProtectedRoute";
import SimpleTable from "../../components/SimpleTable";
import StatusBadge from "../../components/StatusBadge";
import {
  deleteModelProviderApiKey,
  get,
  getCurrentUser,
  getModelProviderKeyStatuses,
  getModelProviderSettings,
  saveModelProviderApiKey,
  updateModelProviderSettings,
} from "../../lib/apiClient";
import { formatDateTime } from "../../lib/format";
import { maskSensitiveReference, truncateText } from "../../lib/format";


const MODEL_PROVIDER_OPTIONS = [
  {
    id: "openai",
    label: "OpenAI",
    description: "Preferred for general-purpose chat, reasoning, and writing."
  },
  {
    id: "anthropic",
    label: "Anthropic",
    description: "Good for structured analysis, long context, and careful output."
  },
  {
    id: "google_gemini",
    label: "Google Gemini",
    description: "Useful for fast responses and broad multimodal workflows."
  },
  {
    id: "openrouter",
    label: "OpenRouter",
    description: "Metadata-only label for routing through a preferred model hub."
  },
  {
    id: "ollama_local",
    label: "Ollama Local",
    description: "Marks a local model preference without connecting to runtime."
  },
  {
    id: "custom",
    label: "Custom",
    description: "Use any custom provider label that fits your workspace notes."
  }
];


const API_KEY_PROVIDER_OPTIONS = MODEL_PROVIDER_OPTIONS.filter(
  (option) => option.id !== "ollama_local"
);


const CONNECTION_STATUS_LABELS = {
  not_connected: "Not connected",
  metadata_configured: "Metadata configured"
};


function getConnectionStatusLabel(value) {
  return CONNECTION_STATUS_LABELS[value] || "Not connected";
}


function getConnectionStatusTone(value) {
  return value === "metadata_configured" ? "success" : "neutral";
}


function normalizeInputValue(value) {
  return value ?? "";
}


function getDefaultApiKeyProvider(providerSettings, apiKeyItems) {
  const preferredProvider = providerSettings?.preferred_provider;
  if (API_KEY_PROVIDER_OPTIONS.some((option) => option.id === preferredProvider)) {
    return preferredProvider;
  }

  const connectedProvider = apiKeyItems.find((item) => item.connection_status === "connected");
  return connectedProvider?.provider || API_KEY_PROVIDER_OPTIONS[0]?.id || "openai";
}


export default function SettingsPage() {
  const [state, setState] = useState({
    loading: true,
    currentUser: null,
    providerSettings: {
      item: null,
      error: "",
      saving: false,
      saveError: "",
      saveSuccess: ""
    },
    apiKeyVault: {
      items: [],
      error: "",
      saving: false,
      deletingProvider: "",
      saveError: "",
      saveSuccess: "",
      selectedProvider: "openai",
      apiKey: ""
    },
    providerForm: {
      preferred_provider: "",
      preferred_model: ""
    },
    sections: {
      providers: { items: [], error: "" },
      tools: { items: [], error: "" },
      skills: { items: [], error: "" },
      workflows: { items: [], error: "" }
    }
  });

  useEffect(() => {
    let isMounted = true;

    async function loadSettingsData() {
      const [currentUserResult, providerSettingsResult, apiKeyStatusesResult, providersResult, toolsResult, skillsResult] = await Promise.allSettled([
        getCurrentUser(),
        getModelProviderSettings(),
        getModelProviderKeyStatuses(),
        get("/model-providers"),
        get("/tools"),
        get("/skills")
      ]);

      if (!isMounted) {
        return;
      }

      const currentUser =
        currentUserResult.status === "fulfilled" ? currentUserResult.value : null;
      const canUseN8n =
        currentUser?.role === "admin" || (currentUser?.subscription_plan || "free") !== "free";
      const workflowsResult = canUseN8n
        ? await Promise.allSettled([get("/n8n-workflows")]).then(([result]) => result)
        : null;
      if (!isMounted) {
        return;
      }
      const providerSettings =
        providerSettingsResult.status === "fulfilled" ? providerSettingsResult.value : null;
      const apiKeyStatuses =
        apiKeyStatusesResult.status === "fulfilled" ? apiKeyStatusesResult.value?.items || [] : [];

      setState({
        loading: false,
        currentUser,
        providerSettings: {
          item: providerSettings,
          error:
            providerSettingsResult.status === "fulfilled"
              ? ""
              : "Failed to load model provider settings.",
          saving: false,
          saveError: "",
          saveSuccess: ""
        },
        apiKeyVault: {
          items: apiKeyStatuses,
          error:
            apiKeyStatusesResult.status === "fulfilled"
              ? ""
              : "Failed to load model provider API keys.",
          saving: false,
          deletingProvider: "",
          saveError: "",
          saveSuccess: "",
          selectedProvider: getDefaultApiKeyProvider(providerSettings, apiKeyStatuses),
          apiKey: ""
        },
        providerForm: {
          preferred_provider: normalizeInputValue(providerSettings?.preferred_provider),
          preferred_model: normalizeInputValue(providerSettings?.preferred_model)
        },
        sections: {
          providers:
            providersResult.status === "fulfilled"
              ? { items: providersResult.value?.items || [], error: "" }
              : { items: [], error: "Failed to load model providers." },
          tools:
            toolsResult.status === "fulfilled"
              ? { items: toolsResult.value?.items || [], error: "" }
              : { items: [], error: "Failed to load tools." },
          skills:
            skillsResult.status === "fulfilled"
              ? { items: skillsResult.value?.items || [], error: "" }
              : { items: [], error: "Failed to load skills." },
          workflows:
            workflowsResult === null
              ? { items: [], error: "" }
              : workflowsResult.status === "fulfilled"
                ? { items: workflowsResult.value?.items || [], error: "" }
                : { items: [], error: "Failed to load n8n workflows." }
        }
      });
    }

    loadSettingsData();
    return () => {
      isMounted = false;
    };
  }, []);

  const providerColumns = [
    { key: "name", label: "Name" },
    { key: "provider_type", label: "Type" },
    { key: "default_model", label: "Default model" },
    {
      key: "status",
      label: "Status",
      render: (value) => <StatusBadge tone={value === "active" ? "success" : "warning"} label={value || "unknown"} />
    },
    {
      key: "masked_secret_reference",
      label: "Secret reference",
      render: (value, row) => (row.has_secret_reference ? value || "[masked]" : "Not set")
    }
  ];

  const toolColumns = [
    { key: "name", label: "Tool" },
    { key: "tool_type", label: "Type" },
    {
      key: "risk_level",
      label: "Risk",
      render: (value) => (
        <StatusBadge
          tone={value === "critical" || value === "high" ? "danger" : value === "medium" ? "warning" : "neutral"}
          label={value || "unknown"}
        />
      )
    },
    {
      key: "status",
      label: "Status",
      render: (value) => <StatusBadge tone={value === "active" ? "success" : "warning"} label={value || "unknown"} />
    }
  ];

  const skillColumns = [
    { key: "name", label: "Skill" },
    { key: "source_type", label: "Source" },
    { key: "risk_level", label: "Risk" },
    {
      key: "status",
      label: "Status",
      render: (value) => <StatusBadge tone={value === "active" ? "success" : "warning"} label={value || "unknown"} />
    },
    {
      key: "description",
      label: "Description",
      render: (value) => truncateText(value, 80)
    }
  ];

  const workflowColumns = [
    { key: "name", label: "Workflow" },
    { key: "trigger_type", label: "Trigger" },
    {
      key: "webhook_url_reference",
      label: "Webhook reference",
      render: (value) => maskSensitiveReference(value)
    },
    {
      key: "status",
      label: "Status",
      render: (value) => <StatusBadge tone={value === "active" ? "success" : "warning"} label={value || "unknown"} />
    }
  ];

  const currentConnectionStatus = state.providerSettings.item?.connection_status || "not_connected";
  const currentConnectionLabel = getConnectionStatusLabel(currentConnectionStatus);
  const currentConnectionTone = getConnectionStatusTone(currentConnectionStatus);
  const apiKeyItemsByProvider = Object.fromEntries(
    state.apiKeyVault.items.map((item) => [item.provider, item])
  );

  async function handleSaveModelProviderSettings(event) {
    event.preventDefault();

    setState((prev) => ({
      ...prev,
      providerSettings: {
        ...prev.providerSettings,
        saving: true,
        saveError: "",
        saveSuccess: ""
      }
    }));

    try {
      const payload = {
        preferred_provider: state.providerForm.preferred_provider || null,
        preferred_model: state.providerForm.preferred_model.trim() || null
      };
      const result = await updateModelProviderSettings(payload);

      setState((prev) => ({
        ...prev,
        providerSettings: {
          ...prev.providerSettings,
          item: result,
          saving: false,
          saveError: "",
          saveSuccess: "Model provider metadata saved safely."
        },
        providerForm: {
          preferred_provider: normalizeInputValue(result.preferred_provider),
          preferred_model: normalizeInputValue(result.preferred_model)
        }
      }));
    } catch (error) {
      setState((prev) => ({
        ...prev,
        providerSettings: {
          ...prev.providerSettings,
          saving: false,
          saveError: error instanceof Error ? error.message : "Failed to save model provider settings.",
          saveSuccess: ""
        }
      }));
    }
  }

  async function handleSaveModelProviderApiKey(event) {
    event.preventDefault();

    const provider = state.apiKeyVault.selectedProvider;
    const apiKey = state.apiKeyVault.apiKey.trim();
    if (!provider || !apiKey) {
      setState((prev) => ({
        ...prev,
        apiKeyVault: {
          ...prev.apiKeyVault,
          saveError: "Choose a provider and enter an API key before saving.",
          saveSuccess: ""
        }
      }));
      return;
    }

    setState((prev) => ({
      ...prev,
      apiKeyVault: {
        ...prev.apiKeyVault,
        saving: true,
        saveError: "",
        saveSuccess: ""
      }
    }));

    try {
      const result = await saveModelProviderApiKey(provider, { api_key: apiKey });

      setState((prev) => ({
        ...prev,
        apiKeyVault: {
          ...prev.apiKeyVault,
          items: prev.apiKeyVault.items.map((item) => (item.provider === result.provider ? result : item)),
          saving: false,
          saveError: "",
          saveSuccess: "API key saved encrypted. It is not used for model calls yet.",
          apiKey: ""
        }
      }));
    } catch (error) {
      setState((prev) => ({
        ...prev,
        apiKeyVault: {
          ...prev.apiKeyVault,
          saving: false,
          saveError: error instanceof Error ? error.message : "Failed to save API key.",
          saveSuccess: ""
        }
      }));
    }
  }

  async function handleDeleteModelProviderApiKey(provider) {
    if (!provider) {
      return;
    }

    setState((prev) => ({
      ...prev,
      apiKeyVault: {
        ...prev.apiKeyVault,
        deletingProvider: provider,
        saveError: "",
        saveSuccess: ""
      }
    }));

    try {
      const result = await deleteModelProviderApiKey(provider);

      setState((prev) => ({
        ...prev,
        apiKeyVault: {
          ...prev.apiKeyVault,
          items: prev.apiKeyVault.items.map((item) => (item.provider === result.provider ? result : item)),
          deletingProvider: "",
          saveError: "",
          saveSuccess: "API key disconnected safely.",
          apiKey: prev.apiKeyVault.selectedProvider === provider ? "" : prev.apiKeyVault.apiKey
        }
      }));
    } catch (error) {
      setState((prev) => ({
        ...prev,
        apiKeyVault: {
          ...prev.apiKeyVault,
          deletingProvider: "",
          saveError: error instanceof Error ? error.message : "Failed to disconnect API key.",
          saveSuccess: ""
        }
      }));
    }
  }

  function handleApiKeyProviderSelect(event) {
    const { value } = event.target;
    setState((prev) => ({
      ...prev,
      apiKeyVault: {
        ...prev.apiKeyVault,
        selectedProvider: value,
        saveError: "",
        saveSuccess: ""
      }
    }));
  }

  function handleApiKeyChange(event) {
    const { value } = event.target;
    setState((prev) => ({
      ...prev,
      apiKeyVault: {
        ...prev.apiKeyVault,
        apiKey: value,
        saveError: "",
        saveSuccess: ""
      }
    }));
  }

  function handleProviderSelect(providerId) {
    setState((prev) => {
      const nextProvider = prev.providerForm.preferred_provider === providerId ? "" : providerId;

      return {
        ...prev,
        providerForm: {
          ...prev.providerForm,
          preferred_provider: nextProvider
        },
        providerSettings: {
          ...prev.providerSettings,
          saveError: "",
          saveSuccess: ""
        }
      };
    });
  }

  function handleModelChange(event) {
    const { value } = event.target;
    setState((prev) => ({
      ...prev,
      providerForm: {
        ...prev.providerForm,
        preferred_model: value
      },
      providerSettings: {
        ...prev.providerSettings,
        saveError: "",
        saveSuccess: ""
      }
    }));
  }

  function renderSection(title, rows, columns, emptyMessage, error) {
    return (
      <section className="space-y-3">
        <h2 className="text-xl text-ink">{title}</h2>
        {error ? (
          <ErrorState title={`${title} unavailable`} description={error} />
        ) : (
          <SimpleTable columns={columns} rows={rows} emptyMessage={emptyMessage} />
        )}
      </section>
    );
  }

  const apiKeyColumns = [
    { key: "provider", label: "Provider" },
    {
      key: "connection_status",
      label: "Status",
      render: (value) => (
        <StatusBadge
          tone={value === "connected" ? "success" : "neutral"}
          label={value === "connected" ? "Connected" : "Not connected"}
        />
      )
    },
    {
      key: "masked_key",
      label: "Masked key",
      render: (value) => value || "-"
    },
    { key: "key_last4", label: "Last 4" },
    {
      key: "created_at",
      label: "Created",
      render: (value) => formatDateTime(value)
    },
    {
      key: "updated_at",
      label: "Updated",
      render: (value) => formatDateTime(value)
    },
    {
      key: "actions",
      label: "Action",
      render: (_, row) =>
        row.connection_status === "connected" ? (
          <button
            type="button"
            onClick={() => handleDeleteModelProviderApiKey(row.provider)}
            disabled={state.apiKeyVault.deletingProvider === row.provider}
            className="rounded-full border border-[color:var(--danger)] px-4 py-2 text-xs font-semibold uppercase tracking-[0.16em] text-[color:var(--danger)] transition hover:bg-[#fff4f4] disabled:cursor-not-allowed disabled:opacity-60"
          >
            {state.apiKeyVault.deletingProvider === row.provider ? "Disconnecting..." : "Disconnect"}
          </button>
        ) : (
          "-"
        )
    }
  ];

  function renderApiKeyVaultSection() {
    if (state.apiKeyVault.error) {
      return (
        <section className="space-y-3">
          <h2 className="text-xl text-ink">API Key Vault</h2>
          <ErrorState title="API key vault unavailable" description={state.apiKeyVault.error} />
        </section>
      );
    }

    const selectedProvider = state.apiKeyVault.selectedProvider;
    const selectedStatus = apiKeyItemsByProvider[selectedProvider];
    const selectedProviderLabel =
      API_KEY_PROVIDER_OPTIONS.find((option) => option.id === selectedProvider)?.label || selectedProvider;

    return (
      <section className="space-y-3">
        <h2 className="text-xl text-ink">API Key Vault</h2>
        <div className="rounded-[28px] border border-[var(--border)] bg-white p-6 shadow-panel">
          <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
            <div className="max-w-3xl space-y-2">
              <p className="text-sm leading-7 text-[color:var(--muted)]">
                API keys are stored encrypted and are not used for model calls yet.
              </p>
              <p className="text-sm leading-7 text-[color:var(--muted)]">
                Supported providers: OpenAI, Anthropic, Google Gemini, OpenRouter, and Custom. Ollama Local is intentionally excluded from API key storage.
              </p>
            </div>
            <StatusBadge
              tone={selectedStatus?.connection_status === "connected" ? "success" : "neutral"}
              label={selectedStatus?.connection_status === "connected" ? "Connected" : "Not connected"}
            />
          </div>

          <form className="mt-6 space-y-5" onSubmit={handleSaveModelProviderApiKey}>
            <label className="block space-y-2">
              <span className="text-sm uppercase tracking-[0.18em] text-[color:var(--muted)]">
                Provider
              </span>
              <select
                value={state.apiKeyVault.selectedProvider}
                onChange={handleApiKeyProviderSelect}
                className="w-full rounded-2xl border border-[var(--border)] bg-[#fbfaf5] px-4 py-3 text-sm text-ink outline-none transition focus:border-[color:var(--accent)]"
              >
                {API_KEY_PROVIDER_OPTIONS.map((option) => (
                  <option key={option.id} value={option.id}>
                    {option.label}
                  </option>
                ))}
              </select>
            </label>

            <label className="block space-y-2">
              <span className="text-sm uppercase tracking-[0.18em] text-[color:var(--muted)]">
                API key
              </span>
              <input
                type="password"
                value={state.apiKeyVault.apiKey}
                onChange={handleApiKeyChange}
                placeholder="Write-only API key"
                autoComplete="off"
                className="w-full rounded-2xl border border-[var(--border)] bg-[#fbfaf5] px-4 py-3 text-sm text-ink outline-none transition placeholder:text-[color:var(--muted)] focus:border-[color:var(--accent)]"
              />
            </label>

            <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
              <button
                type="submit"
                disabled={state.apiKeyVault.saving}
                className="rounded-full border border-[color:var(--accent)] bg-[color:var(--accent)] px-5 py-3 text-sm font-semibold text-white transition hover:opacity-95 disabled:cursor-not-allowed disabled:opacity-60"
              >
                {state.apiKeyVault.saving ? "Saving..." : "Save API key"}
              </button>
              <p className="text-sm leading-6 text-[color:var(--muted)]">
                The input is write-only. Saving clears the field and stores only encrypted data.
              </p>
            </div>

            {state.apiKeyVault.saveError ? (
              <p className="text-sm leading-6 text-[color:var(--danger)]">{state.apiKeyVault.saveError}</p>
            ) : null}
            {state.apiKeyVault.saveSuccess ? (
              <p className="text-sm leading-6 text-[color:var(--success)]">{state.apiKeyVault.saveSuccess}</p>
            ) : null}
          </form>

          <div className="mt-6 overflow-hidden rounded-[22px] border border-[var(--border)]">
            <div className="border-b border-[var(--border)] bg-[#fbfaf5] px-4 py-3 text-sm text-[color:var(--muted)]">
              Selected provider: <span className="font-semibold text-ink">{selectedProviderLabel}</span>
            </div>
            <SimpleTable
              columns={apiKeyColumns}
              rows={state.apiKeyVault.items}
              emptyMessage="No API keys stored yet. Save a key to quarantine it here."
            />
          </div>
        </div>
      </section>
    );
  }

  function renderProviderSettingsSection() {
    if (state.providerSettings.error) {
      return (
        <section className="space-y-3">
          <h2 className="text-xl text-ink">Model Provider Settings</h2>
          <ErrorState
            title="Model provider settings unavailable"
            description={state.providerSettings.error}
          />
        </section>
      );
    }

    return (
      <section className="space-y-3">
        <h2 className="text-xl text-ink">Model Provider Settings</h2>
        <div className="rounded-[28px] border border-[var(--border)] bg-white p-6 shadow-panel">
          <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
            <div className="max-w-3xl space-y-2">
              <p className="text-sm leading-7 text-[color:var(--muted)]">
                Choose a preferred provider and model name. This only saves your preferred provider/model metadata. API keys and OAuth connections are not enabled yet.
              </p>
              <p className="text-sm leading-7 text-[color:var(--muted)]">
                Leave both fields blank to keep the workspace in Not connected mode.
              </p>
            </div>
            <StatusBadge tone={currentConnectionTone} label={currentConnectionLabel} />
          </div>

          <form className="mt-6 space-y-5" onSubmit={handleSaveModelProviderSettings}>
            <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
              {MODEL_PROVIDER_OPTIONS.map((option) => {
                const isSelected = state.providerForm.preferred_provider === option.id;

                return (
                  <button
                    key={option.id}
                    type="button"
                    onClick={() => handleProviderSelect(option.id)}
                    className={`rounded-[24px] border p-4 text-left transition ${
                      isSelected
                        ? "border-[color:var(--accent)] bg-[#f7f1e0]"
                        : "border-[var(--border)] bg-[#fbfaf5] hover:border-[color:var(--accent-soft)]"
                    }`}
                  >
                    <div className="flex items-start justify-between gap-3">
                      <div>
                        <h3 className="text-base text-ink">{option.label}</h3>
                        <p className="mt-1 text-xs uppercase tracking-[0.18em] text-[color:var(--muted)]">
                          Metadata only
                        </p>
                      </div>
                      {isSelected ? <StatusBadge tone="success" label="Selected" /> : null}
                    </div>
                    <p className="mt-3 text-sm leading-6 text-[color:var(--muted)]">{option.description}</p>
                  </button>
                );
              })}
            </div>

            <label className="block space-y-2">
              <span className="text-sm uppercase tracking-[0.18em] text-[color:var(--muted)]">
                Preferred model name / id
              </span>
              <input
                type="text"
                value={state.providerForm.preferred_model}
                onChange={handleModelChange}
                placeholder="gpt-4o-mini"
                className="w-full rounded-2xl border border-[var(--border)] bg-[#fbfaf5] px-4 py-3 text-sm text-ink outline-none transition placeholder:text-[color:var(--muted)] focus:border-[color:var(--accent)]"
              />
            </label>

            <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
              <button
                type="submit"
                disabled={state.providerSettings.saving}
                className="rounded-full border border-[color:var(--accent)] bg-[color:var(--accent)] px-5 py-3 text-sm font-semibold text-white transition hover:opacity-95 disabled:cursor-not-allowed disabled:opacity-60"
              >
                {state.providerSettings.saving ? "Saving..." : "Save metadata"}
              </button>
              <p className="text-sm leading-6 text-[color:var(--muted)]">
                No API keys are stored here. This screen only keeps safe preference metadata.
              </p>
            </div>

            {state.providerSettings.saveError ? (
              <p className="text-sm leading-6 text-[color:var(--danger)]">
                {state.providerSettings.saveError}
              </p>
            ) : null}
            {state.providerSettings.saveSuccess ? (
              <p className="text-sm leading-6 text-[color:var(--success)]">
                {state.providerSettings.saveSuccess}
              </p>
            ) : null}
          </form>
        </div>
      </section>
    );
  }

  return (
    <ProtectedRoute>
      <AppShell
        title="Settings"
        description="Read-only backend configuration lists and safe metadata settings from authenticated endpoints."
      >
        {state.loading ? (
          <LoadingState
            title="Loading settings data"
            description="Fetching safe provider, tool, skill, workflow, and model preference data..."
          />
        ) : (
          <div className="space-y-6">
            {renderApiKeyVaultSection()}
            {renderProviderSettingsSection()}
            {renderSection(
              "Model Providers",
              state.sections.providers.items,
              providerColumns,
              "No model providers are configured yet.",
              state.sections.providers.error
            )}
            {renderSection(
              "Tools",
              state.sections.tools.items,
              toolColumns,
              "No tools are registered yet.",
              state.sections.tools.error
            )}
            {renderSection(
              "Skills",
              state.sections.skills.items,
              skillColumns,
              "No skills are available yet.",
              state.sections.skills.error
            )}
            {renderSection(
              "n8n Workflow Registry",
              state.sections.workflows.items,
              workflowColumns,
              "No n8n workflow registry records are available yet.",
              state.sections.workflows.error
            )}
          </div>
        )}
      </AppShell>
    </ProtectedRoute>
  );
}
