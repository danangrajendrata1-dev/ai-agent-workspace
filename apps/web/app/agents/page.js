"use client";

import { useEffect, useState } from "react";
import Link from "next/link";

import AppShell from "../../components/AppShell";
import ErrorState from "../../components/ErrorState";
import LoadingState from "../../components/LoadingState";
import ProtectedRoute from "../../components/ProtectedRoute";
import SimpleTable from "../../components/SimpleTable";
import StatusBadge from "../../components/StatusBadge";
import { get } from "../../lib/apiClient";
import { formatDateTime, truncateText } from "../../lib/format";


export default function AgentsPage() {
  const [state, setState] = useState({
    loading: true,
    error: "",
    items: []
  });

  useEffect(() => {
    let isMounted = true;

    async function loadAgents() {
      try {
        const response = await get("/agents");
        if (!isMounted) {
          return;
        }

        setState({
          loading: false,
          error: "",
          items: response?.items || []
        });
      } catch (error) {
        if (!isMounted) {
          return;
        }

        setState({
          loading: false,
          error: error.message || "Unable to load agents safely.",
          items: []
        });
      }
    }

    loadAgents();
    return () => {
      isMounted = false;
    };
  }, []);

  const columns = [
    {
      key: "name",
      label: "Name",
      render: (value, row) =>
        row.id ? (
          <Link href={`/agents/${row.id}`} className="font-medium text-[color:var(--accent)] hover:underline">
            {value}
          </Link>
        ) : (
          value || "-"
        )
    },
    {
      key: "slug",
      label: "Slug"
    },
    {
      key: "status",
      label: "Status",
      render: (value) => (
        <StatusBadge tone={value === "active" ? "success" : "warning"} label={value || "unknown"} />
      )
    },
    {
      key: "role_description",
      label: "Role / Persona",
      render: (value) => truncateText(value, 90)
    },
    {
      key: "default_model_name",
      label: "Default Provider",
      render: (_, row) => row.default_model_name || row.default_model_provider_id || "-"
    },
    {
      key: "updated_at",
      label: "Updated",
      render: (value) => formatDateTime(value)
    }
  ];

  return (
    <ProtectedRoute>
      <AppShell title="Agents" description="Read-only list of owner agents from the safe `GET /agents` endpoint. No create, update, delete, or chat actions are triggered here.">
        {state.loading ? (
          <LoadingState title="Loading agents" description="Fetching registered agents from the backend safely..." />
        ) : state.error ? (
          <ErrorState title="Agents unavailable" description={state.error} />
        ) : (
          <SimpleTable
            columns={columns}
            rows={state.items}
            emptyMessage="No agents are registered yet in this workspace."
          />
        )}
      </AppShell>
    </ProtectedRoute>
  );
}
