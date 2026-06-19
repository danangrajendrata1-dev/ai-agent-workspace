"use client";

import { useMemo, useState } from "react";

import StatusBadge from "./StatusBadge";
import { truncateText } from "../lib/format";

const ACTIVITY_FILTERS = ["All", "Agent", "Skill", "Workflow", "Approval", "Safety", "Settings"];

function formatTimeOnly(value) {
  if (!value) {
    return "-";
  }

  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) {
    return "-";
  }

  return new Intl.DateTimeFormat("en-US", {
    hour: "2-digit",
    minute: "2-digit"
  }).format(parsed);
}

function getActivityBucket(item) {
  const bucket = `${item?.eventType || ""} ${item?.title || ""} ${item?.message || ""}`.toLowerCase();

  if (bucket.includes("approval")) return "Approval";
  if (bucket.includes("skill")) return "Skill";
  if (bucket.includes("workflow") || bucket.includes("n8n")) return "Workflow";
  if (bucket.includes("safety") || bucket.includes("blocked") || bucket.includes("locked")) return "Safety";
  if (bucket.includes("setting") || bucket.includes("provider") || bucket.includes("vault")) return "Settings";
  if (bucket.includes("agent")) return "Agent";
  return "All";
}

export default function ActivityLogPanelCompact({ activityLogs = [], onSelectActivity }) {
  const [query, setQuery] = useState("");
  const [filter, setFilter] = useState("All");

  const rows = useMemo(() => {
    const normalizedQuery = query.trim().toLowerCase();

    return activityLogs.filter((item) => {
      const bucket = getActivityBucket(item);
      const matchesBucket = filter === "All" || bucket === filter;
      const matchesQuery =
        !normalizedQuery ||
        [item?.title, item?.message, item?.eventType, item?.status, item?.actorType, item?.detail]
          .join(" ")
          .toLowerCase()
          .includes(normalizedQuery);

      return matchesBucket && matchesQuery;
    });
  }, [activityLogs, filter, query]);

  const visibleRows = rows.slice(0, 4);

  return (
    <div className="space-y-4">
      <div className="flex flex-col gap-3 md:flex-row md:items-center">
        <label className="block flex-1">
          <span className="sr-only">Search activity</span>
          <input
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="search activity..."
            className="w-full rounded-[14px] border border-[rgba(62,54,46,0.12)] bg-[#fbf6eb] px-4 py-3 text-sm text-[#3E362E] outline-none placeholder:text-[rgba(62,54,46,0.42)]"
          />
        </label>

        <div className="flex items-center gap-2">
          <label className="block">
            <span className="sr-only">Filter</span>
            <select
              value={filter}
              onChange={(event) => setFilter(event.target.value)}
              className="rounded-[14px] border border-[rgba(62,54,46,0.12)] bg-[#fbf6eb] px-4 py-3 text-sm text-[#3E362E] outline-none"
            >
              {ACTIVITY_FILTERS.map((option) => (
                <option key={option} value={option}>
                  {option}
                </option>
              ))}
            </select>
          </label>
          <button
            type="button"
            className="rounded-[14px] border border-[rgba(62,54,46,0.12)] bg-[#f5efe2] px-4 py-3 text-sm font-medium text-[#3E362E]"
          >
            Today
          </button>
        </div>
      </div>

      <section className="rounded-[18px] border border-[rgba(62,54,46,0.12)] bg-[#f6efe3] p-4">
        <div className="flex items-center justify-between gap-3">
          <p className="text-[11px] uppercase tracking-[0.18em] text-[rgba(62,54,46,0.56)]">Today</p>
        </div>

        <div className="mt-4">
          {visibleRows.length ? (
            visibleRows.map((item) => (
              <article key={item.id} className="border-t border-[rgba(62,54,46,0.1)] py-4 first:border-t-0 first:pt-0">
                <div className="flex items-start gap-3">
                  <div className="min-w-[48px] pt-1 text-[11px] font-medium text-[rgba(62,54,46,0.56)]">
                    {formatTimeOnly(item.createdAt)}
                  </div>
                  <div className="mt-1 h-2.5 w-2.5 rounded-full bg-[#eadcc8]" />
                  <div className="min-w-0 flex-1">
                    <div className="flex items-start justify-between gap-3">
                      <div className="min-w-0">
                        <h3 className="text-[15px] font-semibold text-[#3E362E]">{item.title}</h3>
                        <p className="mt-1 text-sm leading-6 text-[rgba(62,54,46,0.7)]">
                          {truncateText(item.message, 86)}
                        </p>
                      </div>
                      <StatusBadge
                        tone={
                          item.status === "blocked"
                            ? "danger"
                            : item.status === "warning"
                              ? "warning"
                              : item.status === "done"
                                ? "success"
                                : "neutral"
                        }
                        label={item.status || "info"}
                      />
                    </div>
                    <div className="mt-3 flex items-center justify-between gap-3">
                      <p className="text-xs text-[rgba(62,54,46,0.54)]">
                        {item.eventType}
                        {item.actorType ? ` - ${item.actorType}` : ""}
                      </p>
                      <button
                        type="button"
                        onClick={() => onSelectActivity?.(item.id)}
                        className="rounded-full border border-[rgba(62,54,46,0.12)] bg-[#fbf6eb] px-3 py-1.5 text-xs font-medium text-[#3E362E]"
                      >
                        View Detail
                      </button>
                    </div>
                  </div>
                </div>
              </article>
            ))
          ) : (
            <div className="rounded-[16px] border border-dashed border-[rgba(62,54,46,0.14)] bg-[#fbf6eb] px-5 py-8 text-sm text-[rgba(62,54,46,0.64)]">
              No activity row match current filter.
            </div>
          )}
        </div>
      </section>
    </div>
  );
}
