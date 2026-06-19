"use client";

import { useEffect, useMemo, useState } from "react";

import ErrorState from "./ErrorState";
import LoadingState from "./LoadingState";
import ProtectedRoute from "./ProtectedRoute";
import StatusBadge from "./StatusBadge";
import { get, getCurrentUser, getModelProviderKeyStatuses, getModelProviderSettings } from "../lib/apiClient";
import { maskSensitiveReference } from "../lib/format";

function normalizeCollection(payload) {
  if (Array.isArray(payload)) return payload;
  if (Array.isArray(payload?.items)) return payload.items;
  if (Array.isArray(payload?.data)) return payload.data;
  if (Array.isArray(payload?.results)) return payload.results;
  return [];
}

function getProviderLabel(providerId, modelProviders) {
  const match = modelProviders.find((provider) => provider?.id === providerId);
  return match?.name || match?.label || providerId || "-";
}

function getPlanLabel(currentUser) {
  if (currentUser?.role === "admin") return "ADMIN";
  return String(currentUser?.subscription_plan || "FREE").toUpperCase();
}

function SectionShell({ title, children, icon = "\u25e6" }) {
  return (
    <section className="rounded-[18px] border border-[rgba(62,54,46,0.12)] bg-[#f1e7d8] p-4">
      <div className="flex items-center gap-2 text-[11px] uppercase tracking-[0.18em] text-[rgba(62,54,46,0.56)]">
        <span className="flex h-4 w-4 items-center justify-center rounded-full border border-[rgba(62,54,46,0.18)] text-[9px] leading-none text-[rgba(62,54,46,0.58)]">
          {icon}
        </span>
        <span>{title}</span>
      </div>
      <div className="mt-4">{children}</div>
    </section>
  );
}

function SelectRow({ label, value }) {
  return (
    <div className="space-y-2">
      <p className="text-[11px] uppercase tracking-[0.16em] text-[rgba(62,54,46,0.56)]">{label}</p>
      <div className="flex items-center justify-between rounded-[14px] border border-[rgba(62,54,46,0.12)] bg-[#fbf6eb] px-4 py-3">
        <span className="text-sm text-[#3E362E]">{value}</span>
        <span className="text-[12px] leading-none text-[rgba(62,54,46,0.44)]">{'\u2304'}</span>
      </div>
    </div>
  );
}

export function SettingsPanelCompact({
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
        status: item?.connection_status || "not setup",
        maskedKey:
          maskSensitiveReference(item?.masked_key || item?.key_masked || item?.api_key_masked || "") || "masked"
      })),
    [apiKeyStatuses]
  );

  const preferredProvider = providerSettings?.preferred_provider || "";
  const preferredModel = providerSettings?.preferred_model || "";
  const preferredProviderLabel = preferredProvider ? getProviderLabel(preferredProvider, modelProviders) : "OpenAI";
  const preferredModelLabel = preferredModel || "gpt-4o";

  const rows =
    apiKeyRows.length > 0
      ? apiKeyRows
      : [
          { id: "openai", provider: "OpenAI", status: "encrypted", maskedKey: "sk-************3f2a" },
          { id: "anthropic", provider: "Anthropic", status: "not setup", maskedKey: "not set" }
        ];

  return (
    <div className="space-y-4">
      {errors.general ? <ErrorState title="Settings unavailable" description={errors.general} /> : null}

      <SectionShell title="Account / Profile" icon="\u25cc">
        <div className="space-y-3">
          <div className="space-y-2">
            <p className="text-[11px] uppercase tracking-[0.16em] text-[rgba(62,54,46,0.56)]">Name</p>
            <input
              value={currentUser?.display_name || currentUser?.username || "nama user"}
              readOnly
              className="w-full rounded-[14px] border border-[rgba(62,54,46,0.12)] bg-[#fbf6eb] px-4 py-3 text-sm text-[#3E362E] outline-none"
            />
          </div>

          <div className="space-y-2">
            <p className="text-[11px] uppercase tracking-[0.16em] text-[rgba(62,54,46,0.56)]">Email</p>
            <input
              value={currentUser?.email || "user@email.com"}
              readOnly
              className="w-full rounded-[14px] border border-[rgba(62,54,46,0.12)] bg-[#fbf6eb] px-4 py-3 text-sm text-[#3E362E] outline-none"
            />
          </div>

          <div className="flex items-center justify-between gap-3">
            <p className="text-sm text-[rgba(62,54,46,0.68)]">Plan</p>
            <span className="inline-flex rounded-full border border-[rgba(163,106,88,0.18)] bg-[#f7eee4] px-2.5 py-1 text-[10px] font-medium uppercase tracking-[0.16em] text-[#c28b6c]">
              {getPlanLabel(currentUser)}
            </span>
          </div>
        </div>
      </SectionShell>

      <SectionShell title="Brain / Model" icon="\u25d4">
        <div className="space-y-3">
          <SelectRow label="Default provider" value={preferredProviderLabel} />
          <SelectRow label="Default model" value={preferredModelLabel} />

          <div className="flex items-center justify-between gap-3">
            <p className="text-sm text-[rgba(62,54,46,0.68)]">Status</p>
            <span
              className={`inline-flex rounded-full border px-2.5 py-1 text-[10px] font-medium uppercase tracking-[0.16em] ${
                preferredProvider
                  ? "border-[#d7e7db] bg-[#edf5ef] text-[#5f826f]"
                  : "border-[rgba(234,223,189,0.95)] bg-[#f7efd9] text-[#9a6d19]"
              }`}
            >
              {preferredProvider ? "ready" : "need setup"}
            </span>
          </div>
        </div>
      </SectionShell>

      <SectionShell title="API Key Vault" icon="\u25cd">
        <div className="space-y-2">
          {rows.map((row) => (
            <div key={row.id} className="rounded-[14px] border border-[rgba(62,54,46,0.1)] bg-[#fbf6eb] p-3">
              <div className="flex items-start justify-between gap-3">
                <div className="min-w-0">
                  <p className="text-sm font-medium text-[#3E362E]">{row.provider}</p>
                  <p className="mt-1 text-xs text-[rgba(62,54,46,0.62)]">{row.maskedKey}</p>
                </div>
                <span
                  className={`inline-flex shrink-0 rounded-full border px-2.5 py-1 text-[10px] font-medium uppercase tracking-[0.16em] ${
                    row.status === "encrypted"
                      ? "border-[#d7e7db] bg-[#edf5ef] text-[#5f826f]"
                      : "border-[rgba(62,54,46,0.12)] bg-[#f4ecdf] text-[rgba(62,54,46,0.66)]"
                  }`}
                >
                  {row.status}
                </span>
              </div>
              <div className="mt-3 flex items-center justify-end gap-2">
                <button
                  type="button"
                  className="rounded-full border border-[rgba(62,54,46,0.12)] bg-[#f5efe2] px-3 py-1.5 text-xs font-medium text-[#3E362E]"
                >
                  Update
                </button>
              </div>
            </div>
          ))}
        </div>
      </SectionShell>

      <SectionShell title="Safety" icon="\u25c9">
        <div className="overflow-hidden rounded-[14px] border border-[rgba(62,54,46,0.1)] bg-[#fbf6eb]">
          {[
            ["tool execution", "locked", "danger"],
            ["n8n execution", "locked", "danger"],
            ["runtime", "preview only", "warning"],
            ["workflow execution", "locked", "danger"],
            ["provider live test", "locked", "danger"]
          ].map(([label, value, tone]) => (
            <div
              key={label}
              className="flex items-center justify-between gap-3 border-b border-[rgba(62,54,46,0.08)] px-4 py-3 last:border-b-0"
            >
              <p className="text-sm text-[#3E362E]">{label}</p>
              <span
                className={`inline-flex rounded-full border px-2.5 py-1 text-[10px] font-medium uppercase tracking-[0.16em] ${
                  tone === "warning"
                    ? "border-[rgba(234,223,189,0.95)] bg-[#f7efd9] text-[#9a6d19]"
                    : "border-[rgba(62,54,46,0.12)] bg-[#f4ecdf] text-[rgba(62,54,46,0.66)]"
                }`}
              >
                {value}
              </span>
            </div>
          ))}
        </div>
      </SectionShell>
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

      if (!isMounted) return;

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
    return <LoadingState title="Loading settings" description="Fetching safe profile, provider, and vault data..." />;
  }

  const content = (
    <SettingsPanelCompact
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
