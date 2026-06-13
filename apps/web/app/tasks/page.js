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


export default function TasksPage() {
  const [state, setState] = useState({
    loading: true,
    error: "",
    items: []
  });

  useEffect(() => {
    let isMounted = true;

    async function loadTasks() {
      try {
        const response = await get("/tasks");
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
          error: error.message || "Unable to load tasks safely.",
          items: []
        });
      }
    }

    loadTasks();
    return () => {
      isMounted = false;
    };
  }, []);

  const columns = [
    {
      key: "request_id",
      label: "Request ID",
      render: (value, row) =>
        row.id ? (
          <Link href={`/tasks/${row.id}`} className="font-medium text-[color:var(--accent)] hover:underline">
            {truncateText(value, 28)}
          </Link>
        ) : (
          truncateText(value, 28)
        )
    },
    {
      key: "agent_id",
      label: "Agent ID",
      render: (value) => truncateText(value, 18)
    },
    {
      key: "status",
      label: "Status",
      render: (value) => (
        <StatusBadge
          tone={value === "completed" ? "success" : value === "failed" ? "danger" : "neutral"}
          label={value || "unknown"}
        />
      )
    },
    {
      key: "created_at",
      label: "Created",
      render: (value) => formatDateTime(value)
    },
    {
      key: "completed_at",
      label: "Completed",
      render: (value) => formatDateTime(value)
    }
  ];

  return (
    <ProtectedRoute>
      <AppShell title="Tasks" description="Read-only task history from `GET /tasks`. This page does not create tasks and does not call any chat or execution endpoint.">
        {state.loading ? (
          <LoadingState title="Loading tasks" description="Fetching task records safely from the backend..." />
        ) : state.error ? (
          <ErrorState title="Tasks unavailable" description={state.error} />
        ) : (
          <SimpleTable
            columns={columns}
            rows={state.items}
            emptyMessage="No task records are available yet."
          />
        )}
      </AppShell>
    </ProtectedRoute>
  );
}
