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
import { getApproval } from "../../../lib/apiClient";
import { formatDateTime } from "../../../lib/format";
import { formatPayloadPreview } from "../../../lib/safeDisplay";


export default function ApprovalDetailPage() {
  const params = useParams();
  const approvalId = params?.id;
  const [state, setState] = useState({
    loading: true,
    error: "",
    item: null
  });

  useEffect(() => {
    let isMounted = true;

    async function loadApproval() {
      try {
        const response = await getApproval(approvalId);
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
          error: error.message || "Unable to load approval detail safely.",
          item: null
        });
      }
    }

    loadApproval();
    return () => {
      isMounted = false;
    };
  }, [approvalId]);

  const approval = state.item;

  return (
    <ProtectedRoute>
      <AppShell
        title="Approval Detail"
        description="Read-only approval detail from the safe backend GET detail endpoint. No approve, reject, execute, or resume action is available here."
      >
        <Link href="/approvals" className="inline-flex text-sm font-medium text-[color:var(--accent)] hover:underline">
          Back to approvals
        </Link>

        {state.loading ? (
          <LoadingState title="Loading approval detail" description="Fetching safe approval detail from the backend..." />
        ) : state.error ? (
          <ErrorState title="Approval detail unavailable" description={state.error} />
        ) : (
          <div className="space-y-6">
            <DetailCard title="Approval Request">
              <div className="flex flex-wrap items-center gap-3">
                <StatusBadge
                  tone={approval?.risk_level === "critical" || approval?.risk_level === "high" ? "danger" : approval?.risk_level === "medium" ? "warning" : "neutral"}
                  label={approval?.risk_level || "unknown"}
                />
                <StatusBadge
                  tone={approval?.status === "approved" ? "success" : approval?.status === "rejected" ? "danger" : "warning"}
                  label={approval?.status || "unknown"}
                />
              </div>
              <p className="text-sm leading-7 text-[color:var(--muted)]">
                {approval?.requested_action || "-"}
              </p>
            </DetailCard>

            <DetailCard title="Approval Summary">
              <KeyValueList
                items={[
                  { label: "Agent ID", value: approval?.agent_id || "-" },
                  { label: "Task ID", value: approval?.task_id || "-" },
                  { label: "Tool ID", value: approval?.tool_id || "-" },
                  { label: "Decision reason", value: approval?.decision_reason || "-" },
                  { label: "Decided at", value: formatDateTime(approval?.decided_at) },
                  { label: "Created", value: formatDateTime(approval?.created_at) }
                ]}
              />
            </DetailCard>

            <DetailCard title="Masked Request Payload Preview">
              <pre className="overflow-x-auto rounded-3xl border border-[var(--border)] bg-[color:var(--mist)] p-4 text-xs leading-6 text-ink">
                {formatPayloadPreview(approval?.request_payload)}
              </pre>
            </DetailCard>
          </div>
        )}
      </AppShell>
    </ProtectedRoute>
  );
}
