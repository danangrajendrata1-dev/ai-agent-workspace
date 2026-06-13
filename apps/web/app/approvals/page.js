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


export default function ApprovalsPage() {
  const [state, setState] = useState({
    loading: true,
    error: "",
    items: []
  });

  useEffect(() => {
    let isMounted = true;

    async function loadPendingApprovals() {
      try {
        const response = await get("/approvals/pending");
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
          error: error.message || "Unable to load pending approvals safely.",
          items: []
        });
      }
    }

    loadPendingApprovals();
    return () => {
      isMounted = false;
    };
  }, []);

  const columns = [
    {
      key: "requested_action",
      label: "Requested action",
      render: (value, row) =>
        row.id ? (
          <Link href={`/approvals/${row.id}`} className="font-medium text-[color:var(--accent)] hover:underline">
            {truncateText(value, 110)}
          </Link>
        ) : (
          truncateText(value, 110)
        )
    },
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
      render: (value) => <StatusBadge tone="warning" label={value || "unknown"} />
    },
    {
      key: "created_at",
      label: "Created",
      render: (value) => formatDateTime(value)
    }
  ];

  return (
    <ProtectedRoute>
      <AppShell title="Approvals" description="Read-only pending approval list from `GET /approvals/pending`. This step does not approve or reject anything.">
        {state.loading ? (
          <LoadingState title="Loading pending approvals" description="Fetching approval records without triggering review actions..." />
        ) : state.error ? (
          <ErrorState title="Pending approvals unavailable" description={state.error} />
        ) : (
          <SimpleTable
            columns={columns}
            rows={state.items}
            emptyMessage="No pending approvals are waiting for review right now."
          />
        )}
      </AppShell>
    </ProtectedRoute>
  );
}
