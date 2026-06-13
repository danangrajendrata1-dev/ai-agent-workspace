"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";

import AppShell from "../../../components/AppShell";
import DetailCard from "../../../components/DetailCard";
import ErrorState from "../../../components/ErrorState";
import KeyValueList from "../../../components/KeyValueList";
import LoadingState from "../../../components/LoadingState";
import ProtectedRoute from "../../../components/ProtectedRoute";
import StatusBadge from "../../../components/StatusBadge";
import { getAgent } from "../../../lib/apiClient";
import { formatDateTime } from "../../../lib/format";


export default function AgentDetailPage() {
  const params = useParams();
  const agentId = params?.id;
  const [state, setState] = useState({
    loading: true,
    error: "",
    item: null
  });

  useEffect(() => {
    let isMounted = true;

    async function loadAgent() {
      try {
        const response = await getAgent(agentId);
        if (!isMounted) {
          return;
        }

        setState({
          loading: false,
          error: "",
          item: response
        });
      } catch (error) {
        if (!isMounted) {
          return;
        }

        setState({
          loading: false,
          error: error.message || "Unable to load agent detail safely.",
          item: null
        });
      }
    }

    loadAgent();
    return () => {
      isMounted = false;
    };
  }, [agentId]);

  const agent = state.item;

  return (
    <ProtectedRoute>
      <AppShell
        title="Agent Detail"
        description="Read-only agent detail from the safe backend GET detail endpoint. No edit, delete, chat, or run action is available here."
      >
        <Link href="/agents" className="inline-flex text-sm font-medium text-[color:var(--accent)] hover:underline">
          Back to agents
        </Link>

        {state.loading ? (
          <LoadingState title="Loading agent detail" description="Fetching safe agent detail from the backend..." />
        ) : state.error ? (
          <ErrorState title="Agent detail unavailable" description={state.error} />
        ) : (
          <div className="space-y-6">
            <DetailCard title={agent?.name || "Agent"}>
              <div className="flex flex-wrap items-center gap-3">
                <StatusBadge tone={agent?.status === "active" ? "success" : "warning"} label={agent?.status || "unknown"} />
                <span className="text-sm text-[color:var(--muted)]">{agent?.slug || "-"}</span>
              </div>
              <p className="text-sm leading-7 text-[color:var(--muted)]">
                {agent?.description || "No description is available for this agent."}
              </p>
            </DetailCard>

            <DetailCard title="Configuration">
              <KeyValueList
                items={[
                  { label: "Role description", value: agent?.role_description || "-" },
                  { label: "Default model", value: agent?.default_model_name || "-" },
                  { label: "Max steps", value: String(agent?.max_steps ?? "-") },
                  { label: "Max runtime seconds", value: String(agent?.max_runtime_seconds ?? "-") },
                  { label: "Max token budget", value: agent?.max_token_budget ?? "-" },
                  {
                    label: "Approval by default",
                    value: agent?.requires_approval_by_default ? "Yes" : "No"
                  },
                  { label: "Created", value: formatDateTime(agent?.created_at) },
                  { label: "Updated", value: formatDateTime(agent?.updated_at) }
                ]}
              />
            </DetailCard>
          </div>
        )}
      </AppShell>
    </ProtectedRoute>
  );
}
