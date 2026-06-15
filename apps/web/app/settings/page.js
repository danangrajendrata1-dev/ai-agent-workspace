"use client";

import { useEffect, useState } from "react";

import AppShell from "../../components/AppShell";
import ErrorState from "../../components/ErrorState";
import LoadingState from "../../components/LoadingState";
import ProtectedRoute from "../../components/ProtectedRoute";
import SimpleTable from "../../components/SimpleTable";
import StatusBadge from "../../components/StatusBadge";
import { get, getCurrentUser } from "../../lib/apiClient";
import { maskSensitiveReference, truncateText } from "../../lib/format";


export default function SettingsPage() {
  const [state, setState] = useState({
    loading: true,
    currentUser: null,
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
      const [currentUserResult, providersResult, toolsResult, skillsResult] = await Promise.allSettled([
        getCurrentUser(),
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

      setState({
        loading: false,
        currentUser,
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

  const currentSubscriptionPlan = state.currentUser?.subscription_plan || "free";
  const currentUserRole = state.currentUser?.role || "user";
  const n8nStateNote =
    currentUserRole === "admin"
      ? "Admin bypasses n8n access and workflow limits."
      : currentSubscriptionPlan === "pro"
        ? "Pro plan can save 1 workflow draft."
        : currentSubscriptionPlan === "executive"
          ? "Executive plan can save up to 10 workflow drafts."
          : "Free plan is locked. Upgrade to Pro or Executive to save workflows.";

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

  return (
    <ProtectedRoute>
      <AppShell title="Settings" description="Read-only backend configuration lists from safe GET endpoints. No create, update, delete, import, or execution actions are triggered here.">
        {state.loading ? (
          <LoadingState title="Loading settings data" description="Fetching safe provider, tool, skill, and n8n workflow lists..." />
        ) : (
          <div className="space-y-6">
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
            <div className="rounded-[18px] border border-[rgba(62,54,46,0.14)] bg-[#f5f1e6] px-4 py-3 text-sm text-[rgba(62,54,46,0.72)]">
              {n8nStateNote}
            </div>
          </div>
        )}
      </AppShell>
    </ProtectedRoute>
  );
}
