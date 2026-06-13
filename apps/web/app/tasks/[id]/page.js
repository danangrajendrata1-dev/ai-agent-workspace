"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";

import AppShell from "../../../components/AppShell";
import DetailCard from "../../../components/DetailCard";
import EmptyState from "../../../components/EmptyState";
import ErrorState from "../../../components/ErrorState";
import KeyValueList from "../../../components/KeyValueList";
import LoadingState from "../../../components/LoadingState";
import ProtectedRoute from "../../../components/ProtectedRoute";
import SimpleTable from "../../../components/SimpleTable";
import StatusBadge from "../../../components/StatusBadge";
import { getTask } from "../../../lib/apiClient";
import { formatDateTime, truncateText } from "../../../lib/format";


export default function TaskDetailPage() {
  const params = useParams();
  const taskId = params?.id;
  const [state, setState] = useState({
    loading: true,
    error: "",
    item: null
  });

  useEffect(() => {
    let isMounted = true;

    async function loadTask() {
      try {
        const response = await getTask(taskId);
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
          error: error.message || "Unable to load task detail safely.",
          item: null
        });
      }
    }

    loadTask();
    return () => {
      isMounted = false;
    };
  }, [taskId]);

  const task = state.item;
  const stepColumns = [
    { key: "step_order", label: "Order" },
    { key: "step_name", label: "Step" },
    {
      key: "status",
      label: "Status",
      render: (value) => (
        <StatusBadge
          tone={value === "success" ? "success" : value === "failed" ? "danger" : value === "running" ? "warning" : "neutral"}
          label={value || "unknown"}
        />
      )
    },
    {
      key: "input_summary",
      label: "Input summary",
      render: (value) => truncateText(value, 60)
    },
    {
      key: "output_summary",
      label: "Output summary",
      render: (value) => truncateText(value, 60)
    },
    {
      key: "created_at",
      label: "Created",
      render: (value) => formatDateTime(value)
    }
  ];

  return (
    <ProtectedRoute>
      <AppShell
        title="Task Detail"
        description="Read-only task detail from the safe backend GET detail endpoint. No retry, execute, continue, or chat action is available here."
      >
        <Link href="/tasks" className="inline-flex text-sm font-medium text-[color:var(--accent)] hover:underline">
          Back to tasks
        </Link>

        {state.loading ? (
          <LoadingState title="Loading task detail" description="Fetching safe task detail from the backend..." />
        ) : state.error ? (
          <ErrorState title="Task detail unavailable" description={state.error} />
        ) : (
          <div className="space-y-6">
            <DetailCard title={task?.request_id || "Task"}>
              <div className="flex flex-wrap items-center gap-3">
                <StatusBadge
                  tone={task?.status === "completed" ? "success" : task?.status === "failed" ? "danger" : "warning"}
                  label={task?.status || "unknown"}
                />
                <span className="text-sm text-[color:var(--muted)]">Agent ID: {task?.agent_id || "-"}</span>
              </div>
              <p className="text-sm leading-7 text-[color:var(--muted)]">
                {truncateText(task?.input_text, 240)}
              </p>
            </DetailCard>

            <DetailCard title="Task Summary">
              <KeyValueList
                items={[
                  { label: "Selected skill ID", value: task?.selected_skill_id || "-" },
                  { label: "Selected tool ID", value: task?.selected_tool_id || "-" },
                  { label: "Final response", value: task?.final_response || "-" },
                  { label: "Error message", value: task?.error_message || "-" },
                  { label: "Started", value: formatDateTime(task?.started_at) },
                  { label: "Completed", value: formatDateTime(task?.completed_at) },
                  { label: "Created", value: formatDateTime(task?.created_at) },
                  { label: "Updated", value: formatDateTime(task?.updated_at) }
                ]}
              />
            </DetailCard>

            <DetailCard title="Task Steps">
              {task?.steps?.length ? (
                <SimpleTable
                  columns={stepColumns}
                  rows={task.steps}
                  emptyMessage="No task steps are available for this task."
                />
              ) : (
                <EmptyState
                  title="No task steps available"
                  description="This task does not include step detail records in the current response."
                />
              )}
            </DetailCard>
          </div>
        )}
      </AppShell>
    </ProtectedRoute>
  );
}
