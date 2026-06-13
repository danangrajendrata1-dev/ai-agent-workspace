"use client";

import { useEffect, useState } from "react";

import AppShell from "../../components/AppShell";
import ErrorState from "../../components/ErrorState";
import LoadingState from "../../components/LoadingState";
import ProtectedRoute from "../../components/ProtectedRoute";
import SimpleTable from "../../components/SimpleTable";
import StatusBadge from "../../components/StatusBadge";
import { get } from "../../lib/apiClient";
import { maskSensitiveReference, truncateText } from "../../lib/format";


export default function SettingsPage() {
  const [state, setState] = useState({
    loading: true,
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
      const results = await Promise.allSettled([
        get("/model-providers"),
        get("/tools"),
        get("/skills"),
        get("/n8n-workflows")
      ]);

      if (!isMounted) {
        return;
      }

      const [providersResult, toolsResult, skillsResult, workflowsResult] = results;

      setState({
        loading: false,
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
            workflowsResult.status === "fulfilled"
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
          </div>
        )}
      </AppShell>
    </ProtectedRoute>
  );
}
