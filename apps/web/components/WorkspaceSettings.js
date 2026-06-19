"use client";

import { useEffect, useMemo, useState } from "react";

import ErrorState from "./ErrorState";
import LoadingState from "./LoadingState";
import ProtectedRoute from "./ProtectedRoute";
import StatusBadge from "./StatusBadge";
import { get, getCurrentUser, getModelProviderKeyStatuses, getModelProviderSettings } from "../lib/apiClient";
import { formatDateTime, maskSensitiveReference } from "../lib/format";

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

function getProviderLabel(providerId, modelProviders) {
  const match = modelProviders.find((provider) => provider?.id === providerId);
  return match?.name || match?.label || providerId || "-";
}

function getPlanLabel(currentUser) {
  const role = currentUser?.role || "user";
  const plan = currentUser?.subscription_plan || "free";

  if (role === "admin") {
    return "admin";
  }

  return plan;
}

function getSafetyRows() {
  return [
    { label: "Tool execution", value: "locked" },
    { label: "n8n execution", value: "locked" },
    { label: "Runtime", value: "preview only" },
    { label: "Workflow execution", value: "locked" },
    { label: "Provider live test", value: "locked" }
  ];
}

function getSafetyTone(value) {
  if (value === "preview only") {
    return "warning";
  }

  return "danger";
}

export function SettingsPanel({
  currentUser = null,
  providerSettings = null,
  apiKeyStatuses = [],
  modelProviders = [],
  errors = {}
}) {
  const apiKeyRows = useMemo(
    () =>
      apiKeyStatuses.map((item, index) => ({
        id: item?.provider || `provider-${index + 1}`,
        provider: item?.provider || "-",
        status: item?.connection_status || "not_connected",
        maskedKey:
          maskSensitiveReference(item?.masked_key || item?.key_masked || item?.api_key_masked || "") ||
          "masked",
        last4: item?.key_last4 || item?.last4 || "-",
        updatedAt: item?.updated_at || "",
        source: item?.source || item?.source_type || "vault"
      })),
    [apiKeyStatuses]
  );

  const preferredProvider = providerSettings?.preferred_provider || "";
  const preferredModel = providerSettings?.preferred_model || "";

  return (
    <div className="space-y-4">
      {errors.general ? (
        <ErrorState title="Settings unavailable" description={errors.general} />
      ) : null}

      <div className="grid gap-4 xl:grid-cols-2">
        <section className="rounded-[24px] border border-[rgba(62,54,46,0.14)] bg-[#F5F1E6] p-5 shadow-[0_12px_28px_rgba(62,54,46,0.08)]">
          <p className="text-[11px] uppercase tracking-[0.24em] text-[rgba(62,54,46,0.56)]">
            Account / Profile
          </p>
          <div className="mt-4 space-y-3 text-sm leading-6 text-[rgba(62,54,46,0.78)]">
            <div className="flex items-start justify-between gap-4">
              <span className="text-[rgba(62,54,46,0.58)]">Nama</span>
              <span className="text-right font-medium text-[#3E362E]">
                {currentUser?.display_name || currentUser?.username || "Workspace owner"}
              </span>
            </div>
            <div className="flex items-start justify-between gap-4">
              <span className="text-[rgba(62,54,46,0.58)]">Role</span>
              <span className="text-right font-medium text-[#3E362E]">{currentUser?.role || "user"}</span>
            </div>
            <div className="flex items-start justify-between gap-4">
              <span className="text-[rgba(62,54,46,0.58)]">Plan</span>
              <span className="text-right font-medium text-[#3E362E]">{getPlanLabel(currentUser)}</span>
            </div>
            <div className="flex items-start justify-between gap-4">
              <span className="text-[rgba(62,54,46,0.58)]">Status</span>
              <StatusBadge tone="neutral" label="Protected" />
            </div>
          </div>
        </section>

        <section className="rounded-[24px] border border-[rgba(62,54,46,0.14)] bg-[#F5F1E6] p-5 shadow-[0_12px_28px_rgba(62,54,46,0.08)]">
          <p className="text-[11px] uppercase tracking-[0.24em] text-[rgba(62,54,46,0.56)]">
            Brain / Model
          </p>
          <div className="mt-4 space-y-3 text-sm leading-6 text-[rgba(62,54,46,0.78)]">
            <div className="flex items-start justify-between gap-4">
              <span className="text-[rgba(62,54,46,0.58)]">Preferred provider</span>
              <span className="text-right font-medium text-[#3E362E]">
                {getProviderLabel(preferredProvider, modelProviders)}
              </span>
            </div>
            <div className="flex items-start justify-between gap-4">
              <span className="text-[rgba(62,54,46,0.58)]">Preferred model</span>
              <span className="text-right font-medium text-[#3E362E]">
                {preferredModel || "Not set"}
              </span>
            </div>
            <div className="flex items-start justify-between gap-4">
              <span className="text-[rgba(62,54,46,0.58)]">Provider list</span>
              <span className="text-right font-medium text-[#3E362E]">
                {modelProviders.length ? `${modelProviders.length} provider` : "No provider data"}
              </span>
            </div>
            <p className="rounded-[18px] border border-[rgba(62,54,46,0.12)] bg-[#FBF8EF] p-3 text-xs leading-6 text-[rgba(62,54,46,0.66)]">
              API call safety stay locked. No live test. No runtime call.
            </p>
          </div>
        </section>
      </div>

      <section className="overflow-hidden rounded-[24px] border border-[rgba(62,54,46,0.14)] bg-[#F5F1E6] shadow-[0_12px_28px_rgba(62,54,46,0.08)]">
        <div className="border-b border-[rgba(62,54,46,0.12)] px-5 py-4">
          <p className="text-[11px] uppercase tracking-[0.24em] text-[rgba(62,54,46,0.56)]">
            API Key Vault
          </p>
          <p className="mt-2 text-sm leading-6 text-[rgba(62,54,46,0.68)]">
            Masked only. No raw key. No live provider test.
          </p>
        </div>

        {errors.apiKeyVault ? (
          <div className="p-5">
            <ErrorState title="API key vault unavailable" description={errors.apiKeyVault} />
          </div>
        ) : apiKeyRows.length ? (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-[rgba(62,54,46,0.12)]">
              <thead className="bg-[#FBF8EF]">
                <tr>
                  {["Provider", "Status", "Masked key", "Last 4", "Source", "Updated"].map((label) => (
                    <th
                      key={label}
                      className="px-4 py-3 text-left text-[11px] uppercase tracking-[0.2em] text-[rgba(62,54,46,0.56)]"
                    >
                      {label}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-[rgba(62,54,46,0.08)]">
                {apiKeyRows.map((row) => (
                  <tr key={row.id} className="align-top">
                    <td className="px-4 py-4 text-sm font-medium text-[#3E362E]">{row.provider}</td>
                    <td className="px-4 py-4">
                      <StatusBadge
                        tone={row.status === "connected" ? "success" : "neutral"}
                        label={row.status === "connected" ? "connected" : "not connected"}
                      />
                    </td>
                    <td className="px-4 py-4 text-sm text-[rgba(62,54,46,0.72)]">{row.maskedKey}</td>
                    <td className="px-4 py-4 text-sm text-[rgba(62,54,46,0.72)]">{row.last4}</td>
                    <td className="px-4 py-4 text-sm text-[rgba(62,54,46,0.72)]">{row.source}</td>
                    <td className="px-4 py-4 text-sm text-[rgba(62,54,46,0.72)]">
                      {formatDateTime(row.updatedAt)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="p-5 text-sm leading-6 text-[rgba(62,54,46,0.68)]">
            No masked keys stored yet.
          </div>
        )}
      </section>

      <section className="rounded-[24px] border border-[rgba(62,54,46,0.14)] bg-[#F5F1E6] p-5 shadow-[0_12px_28px_rgba(62,54,46,0.08)]">
        <p className="text-[11px] uppercase tracking-[0.24em] text-[rgba(62,54,46,0.56)]">Safety</p>
        <div className="mt-4 grid gap-3 md:grid-cols-2 xl:grid-cols-3">
          {getSafetyRows().map((row) => (
            <div
              key={row.label}
              className="rounded-[18px] border border-[rgba(62,54,46,0.12)] bg-[#FBF8EF] p-4"
            >
              <div className="flex items-center justify-between gap-3">
                <p className="text-sm font-medium text-[#3E362E]">{row.label}</p>
                <StatusBadge tone={getSafetyTone(row.value)} label={row.value} />
              </div>
              <p className="mt-2 text-xs leading-6 text-[rgba(62,54,46,0.64)]">
                Locked by design. No exposed live action on this surface.
              </p>
            </div>
          ))}
        </div>
      </section>

      <section className="rounded-[24px] border border-[rgba(62,54,46,0.14)] bg-[#F5F1E6] p-5 shadow-[0_12px_28px_rgba(62,54,46,0.08)]">
        <p className="text-[11px] uppercase tracking-[0.24em] text-[rgba(62,54,46,0.56)]">
          Notes
        </p>
        <div className="mt-3 space-y-2 text-sm leading-6 text-[rgba(62,54,46,0.68)]">
          <p>No Test Connection button on this UI.</p>
          <p>No raw key shown in browser.</p>
          <p>No runtime or workflow execute path exposed here.</p>
          <p className="text-xs text-[rgba(62,54,46,0.54)]">
            Provider metadata preview only. Last update: {providerSettings?.updated_at ? formatDateTime(providerSettings.updated_at) : "-"}.
          </p>
        </div>
      </section>
    </div>
  );
}

function WorkspaceSettingsLoader({ embedded = false }) {
  const [state, setState] = useState({
    loading: true,
    currentUser: null,
    providerSettings: null,
    apiKeyStatuses: [],
    modelProviders: [],
    errors: {
      general: "",
      apiKeyVault: ""
    }
  });

  useEffect(() => {
    let isMounted = true;

    async function loadSettings() {
      const [currentUserResult, providerSettingsResult, apiKeyStatusesResult, modelProvidersResult] =
        await Promise.allSettled([
          getCurrentUser(),
          getModelProviderSettings(),
          getModelProviderKeyStatuses(),
          get("/model-providers")
        ]);

      if (!isMounted) {
        return;
      }

      setState({
        loading: false,
        currentUser: currentUserResult.status === "fulfilled" ? currentUserResult.value : null,
        providerSettings: providerSettingsResult.status === "fulfilled" ? providerSettingsResult.value : null,
        apiKeyStatuses:
          apiKeyStatusesResult.status === "fulfilled" ? normalizeCollection(apiKeyStatusesResult.value) : [],
        modelProviders:
          modelProvidersResult.status === "fulfilled" ? normalizeCollection(modelProvidersResult.value) : [],
        errors: {
          general:
            currentUserResult.status === "rejected" || providerSettingsResult.status === "rejected"
              ? "Settings data unavailable."
              : "",
          apiKeyVault: apiKeyStatusesResult.status === "rejected" ? "Failed to load API key vault." : ""
        }
      });
    }

    loadSettings();

    return () => {
      isMounted = false;
    };
  }, []);

  if (state.loading) {
    return (
      <LoadingState
        title="Loading settings"
        description="Fetching safe profile, provider, key vault, and safety data..."
      />
    );
  }

  const content = (
    <SettingsPanel
      currentUser={state.currentUser}
      providerSettings={state.providerSettings}
      apiKeyStatuses={state.apiKeyStatuses}
      modelProviders={state.modelProviders}
      errors={state.errors}
    />
  );

  if (embedded) {
    return content;
  }

  return (
    <ProtectedRoute>
      <main className="min-h-screen bg-[#F5F1E6] px-4 py-6 text-[#3E362E] md:px-6 lg:px-8">
        <div className="mx-auto max-w-6xl space-y-5">
          <header className="rounded-[28px] border border-[rgba(62,54,46,0.14)] bg-[linear-gradient(180deg,#F5F1E6,#ECE5D4)] px-6 py-6 shadow-[0_12px_28px_rgba(62,54,46,0.08)]">
            <p className="text-[11px] uppercase tracking-[0.24em] text-[rgba(62,54,46,0.56)]">Workspace</p>
            <div className="mt-3 flex flex-col gap-2 md:flex-row md:items-end md:justify-between">
              <div>
                <h1 className="text-3xl font-semibold tracking-[-0.03em] text-[#3E362E]">Settings</h1>
                <p className="mt-2 max-w-3xl text-sm leading-7 text-[rgba(62,54,46,0.68)]">
                  Status only. No live provider test. No raw API key exposure.
                </p>
              </div>
              <StatusBadge tone="neutral" label="Preview only" />
            </div>
          </header>

          {content}
        </div>
      </main>
    </ProtectedRoute>
  );
}

export default WorkspaceSettingsLoader;
