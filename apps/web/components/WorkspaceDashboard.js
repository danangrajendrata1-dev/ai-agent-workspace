"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { useRouter } from "next/navigation";

import ActivityLogPanelCompact from "./ActivityLogPanelCompact";
import FloatingCard from "./FloatingCard";
import ProtectedRoute from "./ProtectedRoute";
import Sidebar from "./Sidebar";
import SimpleTable from "./SimpleTable";
import StatusBadge from "./StatusBadge";
import Topbar from "./Topbar";
import { SettingsPanelCompact } from "./WorkspaceSettingsCompact";
import { get, getCurrentUser } from "../lib/apiClient";
import { clearToken } from "../lib/auth";
import { formatDateTime, truncateText } from "../lib/format";

const WINDOW_DEFAULTS = {
  createAgent: { open: false, x: 230, y: 60, z: 20 },
  importSkill: { open: false, x: 290, y: 80, z: 21 },
  librarySkill: { open: false, x: 210, y: 90, z: 22 },
  libraryWorkflow: { open: false, x: 250, y: 110, z: 23 },
  workflowN8n: { open: false, x: 330, y: 75, z: 24 },
  activityLog: { open: false, x: 270, y: 60, z: 25 },
  settings: { open: false, x: 310, y: 70, z: 26 }
};

const WINDOW_WIDTH_HINTS = {
  createAgent: 560,
  importSkill: 520,
  librarySkill: 680,
  libraryWorkflow: 680,
  workflowN8n: 520,
  activityLog: 460,
  settings: 420
};

const ACTIVITY_FILTERS = ["All", "Agent", "Skill", "Workflow", "Approval", "Safety", "Settings"];

const PREVIEW_AGENTS = [
  {
    id: "preview-doc-converter",
    name: "Doc Converter",
    status: "active",
    roleDescription: "Convert dokumen dan file kerja.",
    skillNames: ["convert pdf", "convert document", "convert excel"],
    skillCount: 3,
    previewActivity: [
      { id: "doc-1", title: "idle", message: "waiting for file", createdAt: "2026-06-20T20:10:00Z" },
      { id: "doc-2", title: "sedang convert", message: "pdf to doc preview", createdAt: "2026-06-20T20:20:00Z" },
      { id: "doc-3", title: "sedang mengirim", message: "handoff preview", createdAt: "2026-06-20T20:30:00Z" }
    ]
  },
  {
    id: "preview-mail-agent",
    name: "Mail Agent",
    status: "idle",
    roleDescription: "Draft email, send report, schedule send.",
    skillNames: ["draft email", "send report", "schedule send"],
    skillCount: 3,
    previewActivity: [
      { id: "mail-1", title: "draft ready", message: "weekly report mail", createdAt: "2026-06-20T20:05:00Z" },
      { id: "mail-2", title: "queue", message: "scheduled for tomorrow", createdAt: "2026-06-20T20:16:00Z" }
    ]
  },
  {
    id: "preview-data-parser",
    name: "Data Parser",
    status: "idle",
    roleDescription: "Parse JSON, CSV, XML for workspace.",
    skillNames: ["parse json", "extract csv", "transform xml"],
    skillCount: 3,
    previewActivity: [
      { id: "parser-1", title: "parse json", message: "preview schema ready", createdAt: "2026-06-20T19:54:00Z" },
      { id: "parser-2", title: "extract csv", message: "sheet mapped", createdAt: "2026-06-20T20:02:00Z" }
    ]
  },
  {
    id: "preview-summarizer",
    name: "Summarizer",
    status: "active",
    roleDescription: "Summarize doc and make TLDR.",
    skillNames: ["summarize doc", "extract key pts", "generate tldr"],
    skillCount: 3,
    previewActivity: [
      { id: "sum-1", title: "summary draft", message: "preview notes built", createdAt: "2026-06-20T20:11:00Z" },
      { id: "sum-2", title: "extract key pts", message: "5 highlights found", createdAt: "2026-06-20T20:21:00Z" }
    ]
  },
  {
    id: "preview-notifier",
    name: "Notifier",
    status: "idle",
    roleDescription: "Push notifications and log events.",
    skillNames: ["slack notify", "webhook push", "log event"],
    skillCount: 3,
    previewActivity: [
      { id: "note-1", title: "slack notify", message: "preview channel target", createdAt: "2026-06-20T19:48:00Z" },
      { id: "note-2", title: "log event", message: "activity mirrored", createdAt: "2026-06-20T19:56:00Z" }
    ]
  },
  {
    id: "preview-translator",
    name: "Translator",
    status: "active",
    roleDescription: "Translate content for workspace notes.",
    skillNames: ["translate id-en", "localize tone", "review phrase"],
    skillCount: 3,
    previewActivity: [
      { id: "tr-1", title: "translate id-en", message: "preview phrase ready", createdAt: "2026-06-20T20:08:00Z" }
    ]
  },
  {
    id: "preview-scheduler",
    name: "Scheduler",
    status: "idle",
    roleDescription: "Arrange timing and recurring routine.",
    skillNames: ["set reminder", "plan routine", "queue task"],
    skillCount: 3,
    previewActivity: [
      { id: "sch-1", title: "queue task", message: "task moved to tomorrow", createdAt: "2026-06-20T20:18:00Z" }
    ]
  }
];

const PREVIEW_SKILLS = [
  {
    id: "skill-1",
    name: "PDF Helper",
    type: "prompt_skill",
    status: "approved",
    agent: "Doc Converter",
    sourceUrl: "github.com/private/pdf-helper",
    lastUpdate: "2026-06-18 21:10",
    action: "Attach"
  },
  {
    id: "skill-2",
    name: "Mail Draft SOP",
    type: "manual_skill",
    status: "attached",
    agent: "Mail Agent",
    sourceUrl: "github.com/private/mail-draft-sop",
    lastUpdate: "2026-06-19 18:40",
    action: "Detach"
  },
  {
    id: "skill-3",
    name: "JSON Parser",
    type: "tool_preview",
    status: "review",
    agent: "Data Parser",
    sourceUrl: "github.com/private/json-parser",
    lastUpdate: "2026-06-20 09:20",
    action: "Review"
  }
];

const PREVIEW_WORKFLOWS = [
  {
    id: "flow-1",
    name: "Weekly Report",
    trigger: "cron",
    status: "preview",
    agent: "Mail Agent",
    source: "WF-001",
    lastUpdate: "2026-06-20 07:30",
    action: "View"
  },
  {
    id: "flow-2",
    name: "PDF Intake",
    trigger: "webhook",
    status: "disabled",
    agent: "Doc Converter",
    source: "WF-002",
    lastUpdate: "2026-06-19 16:40",
    action: "Disable"
  },
  {
    id: "flow-3",
    name: "Slack Summary",
    trigger: "manual",
    status: "preview",
    agent: "Notifier",
    source: "WF-003",
    lastUpdate: "2026-06-18 13:05",
    action: "Duplicate"
  }
];

const PREVIEW_N8N_CARDS = [
  {
    id: "wf-preview-1",
    name: "Weekly Report Pipeline",
    status: "preview",
    workflowId: "n8n-2401",
    source: "private workspace",
    agent: "Mail Agent",
    trigger: "cron / monday",
    detail: "Compose report, queue review, push final note."
  },
  {
    id: "wf-preview-2",
    name: "Document Intake Flow",
    status: "locked",
    workflowId: "n8n-2408",
    source: "github import preview",
    agent: "Doc Converter",
    trigger: "webhook",
    detail: "Receive file metadata, classify file, hold for review."
  },
  {
    id: "wf-preview-3",
    name: "Summary Broadcast",
    status: "preview",
    workflowId: "n8n-2412",
    source: "workspace draft",
    agent: "Notifier",
    trigger: "manual",
    detail: "Summarize events, draft message, keep send locked."
  }
];

const PREVIEW_ACTIVITY = [
  {
    id: "act-1",
    eventType: "Skill",
    title: "Skill imported",
    message: "PDF Helper imported from GitHub.",
    status: "waiting review",
    actorType: "GitHub import",
    createdAt: "2026-06-20T21:10:00Z"
  },
  {
    id: "act-2",
    eventType: "Agent",
    title: "Agent updated",
    message: "Data Parser attached JSON Parser skill.",
    status: "done",
    actorType: "Workspace",
    createdAt: "2026-06-20T20:45:00Z"
  },
  {
    id: "act-3",
    eventType: "Safety",
    title: "Safety event",
    message: "Tool skill blocked from execution.",
    status: "blocked",
    actorType: "Safety",
    createdAt: "2026-06-20T20:30:00Z"
  },
  {
    id: "act-4",
    eventType: "Workflow",
    title: "Workflow draft saved",
    message: "Weekly Report Pipeline updated in preview mode.",
    status: "preview",
    actorType: "Workflow",
    createdAt: "2026-06-20T19:58:00Z"
  }
];

const PREVIEW_PROVIDER_SETTINGS = {
  preferred_provider: "openai",
  preferred_model: "gpt-4o"
};

const PREVIEW_MODEL_PROVIDERS = [
  { id: "openai", name: "OpenAI" },
  { id: "openrouter", name: "OpenRouter" }
];

const PREVIEW_API_KEYS = [
  { provider: "OpenAI", connection_status: "encrypted", masked_key: "sk-************3f2a" },
  { provider: "OpenRouter", connection_status: "not setup", masked_key: "not set" }
];

function normalizeCollection(payload) {
  if (Array.isArray(payload)) return payload;
  if (Array.isArray(payload?.items)) return payload.items;
  if (Array.isArray(payload?.data)) return payload.data;
  if (Array.isArray(payload?.results)) return payload.results;
  return [];
}

function buildAgentViewModel(agent, index) {
  const rawSkills = Array.isArray(agent?.active_skills)
    ? agent.active_skills
    : Array.isArray(agent?.skills)
      ? agent.skills
      : [];

  const skillNames = rawSkills
    .map((item) => (typeof item === "string" ? item : item?.name || item?.title || ""))
    .filter(Boolean);

  return {
    id: String(agent?.id || `agent-${index + 1}`),
    name: agent?.name || `Agent ${index + 1}`,
    status: agent?.status || "idle",
    roleDescription: agent?.role_description || agent?.description || "Workspace agent.",
    skillNames: skillNames.length ? skillNames : ["workspace skill"],
    skillCount: Number(agent?.skill_count || skillNames.length || 1),
    previewActivity: []
  };
}

function buildInitialWindows() {
  return Object.fromEntries(
    Object.entries(WINDOW_DEFAULTS).map(([key, value]) => [
      key,
      {
        ...value
      }
    ])
  );
}

function clamp(value, min, max) {
  return Math.min(Math.max(value, min), max);
}

function getInitials(text) {
  const value = String(text || "").trim();
  if (!value) return "AI";

  const parts = value.split(" ").filter(Boolean).slice(0, 2);
  if (!parts.length) return "AI";
  return parts.map((part) => part[0]).join("").toUpperCase();
}

function toneForStatus(status) {
  const value = String(status || "").toLowerCase();
  if (value.includes("done") || value.includes("active") || value.includes("approved") || value.includes("encrypted")) {
    return "success";
  }
  if (value.includes("blocked") || value.includes("locked") || value.includes("danger")) {
    return "danger";
  }
  if (value.includes("review") || value.includes("waiting") || value.includes("preview")) {
    return "warning";
  }
  return "neutral";
}

function PromptDock({
  historyOpen,
  onToggleHistory,
  promptDraft,
  onPromptDraftChange,
  onPromptSubmit,
  conversationEntries
}) {
  return (
    <div className="absolute bottom-0 left-0 right-0 z-30 border-t border-[rgba(62,54,46,0.12)] bg-[linear-gradient(180deg,rgba(246,241,234,0.04),rgba(246,241,234,0.92)_14%,rgba(246,241,234,1))] px-4 pb-4 pt-3 backdrop-blur md:px-6 lg:px-8">
      <div className="mx-auto max-w-[1500px] space-y-2">
        <div
          className={`overflow-hidden rounded-[24px] border border-[rgba(62,54,46,0.14)] bg-[#f5efe2] shadow-[0_18px_36px_rgba(62,54,46,0.09)] transition-all duration-300 ${
            historyOpen ? "max-h-[250px] opacity-100" : "max-h-0 opacity-0"
          }`}
        >
          <div className="px-4 pb-4 pt-4">
            <div className="flex items-center justify-between gap-3 pb-3">
              <div>
                <p className="text-[11px] uppercase tracking-[0.18em] text-[rgba(62,54,46,0.52)]">Main AI Conversation</p>
                <p className="mt-1 text-sm font-medium text-[#3E362E]">History drawer</p>
              </div>
              <span className="rounded-full border border-[rgba(62,54,46,0.12)] bg-[#fbf6eb] px-3 py-1 text-[11px] uppercase tracking-[0.16em] text-[rgba(62,54,46,0.58)]">
                collapsed by default
              </span>
            </div>
            <div className="max-h-[180px] space-y-2 overflow-y-auto pr-1">
              {conversationEntries.map((entry) => (
                <div key={entry.id} className="rounded-[16px] border border-[rgba(62,54,46,0.1)] bg-[#fbf6eb] px-4 py-3">
                  <div className="flex items-center justify-between gap-3">
                    <p className="text-[11px] uppercase tracking-[0.16em] text-[rgba(62,54,46,0.52)]">{entry.source}</p>
                    <p className="text-xs text-[rgba(62,54,46,0.52)]">{formatDateTime(entry.createdAt)}</p>
                  </div>
                  <p className="mt-2 text-sm font-medium text-[#3E362E]">{entry.title}</p>
                  <p className="mt-1 text-sm leading-6 text-[rgba(62,54,46,0.68)]">{entry.message}</p>
                </div>
              ))}
            </div>
          </div>
        </div>

        <form
          className="flex items-center gap-3 rounded-[22px] border border-[rgba(62,54,46,0.14)] bg-[#f5efe2] px-3 py-3 shadow-[0_18px_36px_rgba(62,54,46,0.09)]"
          onSubmit={onPromptSubmit}
        >
          <button
            type="button"
            onClick={onToggleHistory}
            className="rounded-[14px] border border-[rgba(62,54,46,0.12)] bg-[#fbf6eb] px-4 py-2.5 text-sm font-medium text-[#3E362E]"
          >
            History
          </button>
          <input
            value={promptDraft}
            onChange={(event) => onPromptDraftChange(event.target.value)}
            placeholder="ini tempat untuk main AI bisa langsung menyuruh lewat prompt..."
            className="min-w-0 flex-1 rounded-[16px] border border-[rgba(62,54,46,0.12)] bg-[#fbf6eb] px-4 py-3 text-sm text-[#3E362E] outline-none placeholder:text-[rgba(62,54,46,0.42)]"
          />
          <button
            type="button"
            className="rounded-[14px] border border-[rgba(62,54,46,0.12)] bg-[#fbf6eb] px-3 py-3 text-sm font-medium text-[rgba(62,54,46,0.72)]"
          >
            model
          </button>
          <button
            type="submit"
            className="flex h-11 w-11 shrink-0 items-center justify-center rounded-full border border-[rgba(62,54,46,0.12)] bg-[#c7643f] text-white"
          >
            →
          </button>
        </form>
      </div>
    </div>
  );
}

function AgentCard({
  agent,
  isSelected,
  isPreview,
  activityRows,
  onSelect,
  onCaptureCommand
}) {
  const [commandDraft, setCommandDraft] = useState("");
  const [localNotes, setLocalNotes] = useState([]);

  function handleCapture() {
    const trimmed = commandDraft.trim();
    if (!trimmed) return;

    const nextNote = {
      id: `note-${Date.now()}`,
      createdAt: new Date().toISOString(),
      message: trimmed
    };

    setLocalNotes((current) => [nextNote, ...current].slice(0, 2));
    onCaptureCommand?.(agent, trimmed);
    setCommandDraft("");
  }

  return (
    <article
      className={`w-[248px] shrink-0 rounded-[18px] border bg-[#fdfaf5] p-3 shadow-[0_10px_22px_rgba(62,54,46,0.06)] ${
        isSelected ? "border-[rgba(184,92,56,0.34)]" : "border-[rgba(62,54,46,0.12)]"
      }`}
    >
      <button type="button" onClick={onSelect} className="block w-full text-left">
        <div className="flex items-start gap-3">
          <div className="relative flex h-12 w-12 shrink-0 items-center justify-center rounded-[14px] border border-[rgba(62,54,46,0.12)] bg-[#f2ebe0] text-[16px] font-semibold tracking-[0.14em] text-[#a36a58]">
            {getInitials(agent.name)}
            <span className="absolute right-1 top-1 h-2 w-2 rounded-full bg-[#c7643f]" />
          </div>
          <div className="min-w-0 flex-1">
            <div className="flex items-start justify-between gap-2">
              <div className="min-w-0">
                <p className="text-[16px] font-semibold leading-5 text-[#3E362E]">{agent.name}</p>
                <p className="mt-1 text-[11px] uppercase tracking-[0.14em] text-[rgba(62,54,46,0.54)]">
                  {agent.skillCount} skill
                </p>
              </div>
              <div className="flex flex-col items-end gap-1">
                <StatusBadge tone={toneForStatus(agent.status)} label={agent.status} />
                {isPreview ? (
                  <span className="rounded-full border border-[rgba(163,106,88,0.18)] bg-[#f7eee4] px-2 py-0.5 text-[9px] font-medium uppercase tracking-[0.16em] text-[#c28b6c]">
                    Local preview
                  </span>
                ) : null}
              </div>
            </div>
            <p className="mt-2 line-clamp-2 text-xs leading-5 text-[rgba(62,54,46,0.64)]">{agent.roleDescription}</p>
          </div>
        </div>
      </button>

      <div className="mt-3 space-y-2">
        <div className="rounded-[14px] border border-[rgba(62,54,46,0.1)] bg-[#fbf6eb] p-3">
          <p className="text-[11px] uppercase tracking-[0.16em] text-[rgba(62,54,46,0.54)]">skills</p>
          <div className="mt-2 flex flex-wrap gap-1.5">
            {agent.skillNames.map((skillName) => (
              <span
                key={`${agent.id}-${skillName}`}
                className="rounded-full border border-[rgba(62,54,46,0.12)] bg-[#f2e8db] px-2.5 py-1 text-[11px] text-[rgba(62,54,46,0.76)]"
              >
                {truncateText(skillName, 18)}
              </span>
            ))}
          </div>
        </div>

        <div className="rounded-[14px] border border-[rgba(62,54,46,0.1)] bg-[#fbf6eb] p-3">
          <p className="text-[11px] uppercase tracking-[0.16em] text-[rgba(62,54,46,0.54)]">activity</p>
          <div className="mt-2 space-y-1.5">
            {activityRows.slice(0, 2).map((item) => (
              <div key={item.id} className="rounded-[12px] border border-[rgba(62,54,46,0.08)] bg-[#f5efe2] px-3 py-2">
                <p className="text-[11px] font-medium text-[#3E362E]">{truncateText(item.title, 30)}</p>
                <p className="mt-0.5 text-[11px] leading-4 text-[rgba(62,54,46,0.62)]">{truncateText(item.message, 52)}</p>
              </div>
            ))}
          </div>
        </div>

        {String(agent.status).toLowerCase().includes("active") ? (
          <div className="rounded-[14px] border border-[rgba(215,162,76,0.22)] bg-[rgba(247,239,217,0.92)] p-3">
            <div className="flex items-center justify-between gap-3">
              <p className="text-[11px] uppercase tracking-[0.16em] text-[rgba(62,54,46,0.54)]">approval needed</p>
              <StatusBadge tone="warning" label="preview" />
            </div>
            <p className="mt-2 text-[11px] leading-5 text-[rgba(62,54,46,0.66)]">
              Agent needs permission before continuing.
            </p>
            <div className="mt-2 text-[11px] leading-5 text-[rgba(62,54,46,0.62)]">use workflow • attach skill</div>
            <div className="mt-3 flex gap-2">
              <button type="button" className="rounded-[12px] bg-[#5f826f] px-3 py-2 text-[11px] font-semibold text-white">
                Approve
              </button>
              <button type="button" className="rounded-[12px] border border-[rgba(62,54,46,0.12)] bg-[#f5efe2] px-3 py-2 text-[11px] font-medium text-[#3E362E]">
                Reject
              </button>
            </div>
          </div>
        ) : null}

        <div className="rounded-[14px] border border-[rgba(62,54,46,0.1)] bg-[#fbf6eb] p-3">
          <p className="text-[11px] uppercase tracking-[0.16em] text-[rgba(62,54,46,0.54)]">ketik untuk menyuruh agent</p>
          <div className="mt-2 flex items-center gap-2">
            <input
              value={commandDraft}
              onChange={(event) => setCommandDraft(event.target.value)}
              onKeyDown={(event) => {
                if (event.key === "Enter") {
                  event.preventDefault();
                  handleCapture();
                }
              }}
              placeholder="ketik untuk menyuruh agent..."
              className="min-w-0 flex-1 rounded-[12px] border border-[rgba(62,54,46,0.1)] bg-[#f5efe2] px-3 py-2 text-[11px] text-[#3E362E] outline-none placeholder:text-[rgba(62,54,46,0.42)]"
            />
            <button type="button" onClick={handleCapture} className="rounded-[12px] border border-[rgba(62,54,46,0.12)] bg-[#f5efe2] px-3 py-2 text-[11px] font-medium text-[#3E362E]">
              →
            </button>
          </div>
          {localNotes.length ? (
            <div className="mt-3 space-y-2">
              {localNotes.map((note) => (
                <div key={note.id} className="rounded-[12px] border border-[rgba(62,54,46,0.08)] bg-[#f5efe2] px-3 py-2">
                  <p className="text-[10px] uppercase tracking-[0.14em] text-[rgba(62,54,46,0.5)]">{formatDateTime(note.createdAt)}</p>
                  <p className="mt-1 text-[11px] leading-5 text-[rgba(62,54,46,0.7)]">{note.message}</p>
                </div>
              ))}
            </div>
          ) : null}
        </div>
      </div>
    </article>
  );
}

function AgentLane({ agents, selectedAgentId, onSelectAgent, onCaptureCommand, isPreviewMode }) {
  const laneRef = useRef(null);
  const dragRef = useRef(null);

  useEffect(() => {
    function handlePointerMove(event) {
      if (!dragRef.current || !laneRef.current) return;
      const deltaX = event.clientX - dragRef.current.startX;
      laneRef.current.scrollLeft = dragRef.current.startScroll - deltaX;
    }

    function handlePointerUp() {
      dragRef.current = null;
    }

    window.addEventListener("pointermove", handlePointerMove);
    window.addEventListener("pointerup", handlePointerUp);

    return () => {
      window.removeEventListener("pointermove", handlePointerMove);
      window.removeEventListener("pointerup", handlePointerUp);
    };
  }, []);

  return (
    <section className="relative flex h-full min-h-0 flex-col px-4 pt-4 md:px-6 lg:px-8">
      <div className="flex min-h-0 flex-1 flex-col rounded-[32px] border border-[rgba(62,54,46,0.12)] bg-[linear-gradient(180deg,rgba(253,249,243,0.86),rgba(244,236,223,0.94))] px-4 pb-4 pt-4 shadow-[0_18px_40px_rgba(62,54,46,0.05)] md:px-5 lg:px-6">
        <div className="flex items-center justify-between gap-4">
          <div>
            <p className="text-[11px] uppercase tracking-[0.22em] text-[rgba(62,54,46,0.52)]">Agents — drag to scroll →</p>
            <p className="mt-1 text-sm text-[rgba(62,54,46,0.62)]">Main center lane. Preview-first shell.</p>
          </div>
          {isPreviewMode ? (
            <div className="rounded-full border border-[rgba(62,54,46,0.12)] bg-[#fbf6eb] px-3 py-1.5 text-[11px] uppercase tracking-[0.16em] text-[rgba(62,54,46,0.58)]">
              Local preview only
            </div>
          ) : null}
        </div>

        <div
          ref={laneRef}
          onPointerDown={(event) => {
            if (!laneRef.current) return;
            dragRef.current = {
              startX: event.clientX,
              startScroll: laneRef.current.scrollLeft
            };
          }}
          className="scrollbar-thin mt-4 min-h-0 flex-1 overflow-x-auto overflow-y-hidden cursor-grab pb-2 active:cursor-grabbing"
        >
          <div className="flex min-w-full w-max snap-x snap-mandatory items-stretch justify-between gap-4 pr-4">
            {agents.map((agent) => (
              <AgentCard
                key={agent.id}
                agent={agent}
                isSelected={selectedAgentId === agent.id}
                isPreview={isPreviewMode}
                activityRows={agent.previewActivity || PREVIEW_ACTIVITY}
                onSelect={() => onSelectAgent(agent.id)}
                onCaptureCommand={onCaptureCommand}
              />
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}

function PanelHeaderNote({ children }) {
  return <p className="text-[11px] uppercase tracking-[0.16em] text-[rgba(62,54,46,0.52)]">{children}</p>;
}

function CreateAgentPanel({ onCreatePreview }) {
  const [form, setForm] = useState({
    name: "",
    skill: "convert pdf",
    model: "gpt-4o",
    pinAgent: true
  });

  function updateField(key, value) {
    setForm((current) => ({
      ...current,
      [key]: value
    }));
  }

  function handleSubmit(event) {
    event.preventDefault();
    const name = form.name.trim();
    if (!name) return;
    onCreatePreview?.(name, form.skill, form.model, form.pinAgent);
    setForm((current) => ({
      ...current,
      name: ""
    }));
  }

  return (
    <form className="space-y-4" onSubmit={handleSubmit}>
      <div className="grid gap-4 lg:grid-cols-[1.15fr,0.85fr]">
        <div className="space-y-3">
          <div className="space-y-2">
            <PanelHeaderNote>Agent Name</PanelHeaderNote>
            <input
              value={form.name}
              onChange={(event) => updateField("name", event.target.value)}
              placeholder="Doc Converter"
              className="w-full rounded-[14px] border border-[rgba(62,54,46,0.12)] bg-[#fbf6eb] px-4 py-3 text-sm text-[#3E362E] outline-none"
            />
          </div>
          <div className="space-y-2">
            <PanelHeaderNote>import icon — PNG, JPG, WebP, GIF</PanelHeaderNote>
            <div className="rounded-[14px] border border-dashed border-[rgba(62,54,46,0.16)] bg-[#fbf6eb] px-4 py-5 text-sm text-[rgba(62,54,46,0.62)]">
              Animated icon concept. Upload UI only.
            </div>
          </div>
          <div className="space-y-2">
            <PanelHeaderNote>Skills</PanelHeaderNote>
            <select
              value={form.skill}
              onChange={(event) => updateField("skill", event.target.value)}
              className="w-full rounded-[14px] border border-[rgba(62,54,46,0.12)] bg-[#fbf6eb] px-4 py-3 text-sm text-[#3E362E] outline-none"
            >
              <option>convert pdf</option>
              <option>draft email</option>
              <option>parse json</option>
              <option>summarize doc</option>
            </select>
          </div>
          <div className="space-y-2">
            <PanelHeaderNote>Brain / Model</PanelHeaderNote>
            <select
              value={form.model}
              onChange={(event) => updateField("model", event.target.value)}
              className="w-full rounded-[14px] border border-[rgba(62,54,46,0.12)] bg-[#fbf6eb] px-4 py-3 text-sm text-[#3E362E] outline-none"
            >
              <option>gpt-4o</option>
              <option>gpt-4.1-mini</option>
              <option>claude-3.5-sonnet</option>
            </select>
          </div>
          <label className="flex items-center gap-2 rounded-[14px] border border-[rgba(62,54,46,0.12)] bg-[#fbf6eb] px-4 py-3 text-sm text-[#3E362E]">
            <input
              type="checkbox"
              checked={form.pinAgent}
              onChange={(event) => updateField("pinAgent", event.target.checked)}
              className="h-4 w-4 rounded border-[rgba(62,54,46,0.16)]"
            />
            pin agent
          </label>
          <button type="submit" className="rounded-[14px] bg-[#c7643f] px-4 py-3 text-sm font-medium text-white">
            Create
          </button>
        </div>

        <div className="rounded-[18px] border border-[rgba(62,54,46,0.12)] bg-[#fbf6eb] p-4">
          <PanelHeaderNote>Preview Agent</PanelHeaderNote>
          <div className="mt-4 rounded-[16px] border border-[rgba(62,54,46,0.12)] bg-[#f5efe2] p-4">
            <div className="flex items-start gap-3">
              <div className="flex h-12 w-12 items-center justify-center rounded-[14px] border border-[rgba(62,54,46,0.12)] bg-[#f2ebe0] text-[16px] font-semibold tracking-[0.14em] text-[#a36a58]">
                {getInitials(form.name || "DC")}
              </div>
              <div className="min-w-0 flex-1">
                <p className="text-[15px] font-semibold text-[#3E362E]">{form.name || "nama agent"}</p>
                <p className="mt-1 text-[11px] uppercase tracking-[0.14em] text-[rgba(62,54,46,0.54)]">skill 2</p>
              </div>
              <StatusBadge tone="warning" label="need setup" />
            </div>
            <div className="mt-4 space-y-2 text-sm text-[rgba(62,54,46,0.66)]">
              <p>icon</p>
              <p>{form.skill}</p>
              <p>{form.model}</p>
            </div>
          </div>
        </div>
      </div>
    </form>
  );
}

function ImportSkillPanel() {
  const [form, setForm] = useState({
    repository: "https://github.com/private/pdf-helper",
    branch: "main",
    filePath: "skills/pdf/SKILL.md",
    folderPath: "skills/pdf",
    previewFilePath: "skills/pdf/SKILL.md",
    previewFolderPath: "skills/pdf"
  });

  function updateField(key, value) {
    setForm((current) => ({
      ...current,
      [key]: value
    }));
  }

  return (
    <div className="space-y-4">
      <div className="grid gap-3">
        {[
          ["Repository URL", "repository"],
          ["Branch", "branch"],
          ["File Path", "filePath"],
          ["Folder Path", "folderPath"],
          ["preview file path", "previewFilePath"],
          ["preview folder path", "previewFolderPath"]
        ].map(([label, key]) => (
          <div key={key} className="space-y-2">
            <PanelHeaderNote>{label}</PanelHeaderNote>
            <input
              value={form[key]}
              onChange={(event) => updateField(key, event.target.value)}
              className="w-full rounded-[14px] border border-[rgba(62,54,46,0.12)] bg-[#fbf6eb] px-4 py-3 text-sm text-[#3E362E] outline-none"
            />
          </div>
        ))}
      </div>

      <div className="rounded-[18px] border border-[rgba(62,54,46,0.12)] bg-[#fbf6eb] p-4">
        <PanelHeaderNote>Result Card</PanelHeaderNote>
        <div className="mt-4 rounded-[16px] border border-[rgba(62,54,46,0.12)] bg-[#f5efe2] p-4">
          <div className="flex items-start justify-between gap-3">
            <div>
              <p className="text-[15px] font-semibold text-[#3E362E]">PDF Helper</p>
              <p className="mt-1 text-xs text-[rgba(62,54,46,0.62)]">import type • skill preview</p>
            </div>
            <StatusBadge tone="warning" label="Add" />
          </div>
          <div className="mt-4 space-y-2 text-sm text-[rgba(62,54,46,0.66)]">
            <p>file path: {form.previewFilePath}</p>
            <p>folder path: {form.previewFolderPath}</p>
            <p>Content Review: no clone, no install, no script execution.</p>
          </div>
        </div>
      </div>
    </div>
  );
}

function LibrarySkillPanel({ rows }) {
  const columns = [
    { key: "name", label: "Nama Skill" },
    { key: "type", label: "Type" },
    {
      key: "status",
      label: "Status",
      render: (value) => <StatusBadge tone={toneForStatus(value)} label={value} />
    },
    { key: "agent", label: "Attach Agent" },
    { key: "sourceUrl", label: "Source URL" },
    { key: "lastUpdate", label: "Last Update" },
    {
      key: "action",
      label: "Action",
      render: (value) => (
        <button type="button" className="rounded-full border border-[rgba(62,54,46,0.12)] bg-[#f5efe2] px-3 py-1.5 text-xs font-medium text-[#3E362E]">
          {value}
        </button>
      )
    }
  ];

  return (
    <div className="space-y-4">
      <div className="grid gap-3 md:grid-cols-3">
        <input placeholder="search skill..." className="rounded-[14px] border border-[rgba(62,54,46,0.12)] bg-[#fbf6eb] px-4 py-3 text-sm outline-none md:col-span-2" />
        <div className="grid grid-cols-2 gap-3">
          <select className="rounded-[14px] border border-[rgba(62,54,46,0.12)] bg-[#fbf6eb] px-4 py-3 text-sm outline-none">
            <option>Type</option>
          </select>
          <select className="rounded-[14px] border border-[rgba(62,54,46,0.12)] bg-[#fbf6eb] px-4 py-3 text-sm outline-none">
            <option>Status</option>
          </select>
        </div>
      </div>
      <SimpleTable columns={columns} rows={rows} emptyMessage="No skill row." />
    </div>
  );
}

function LibraryWorkflowPanel({ rows }) {
  const columns = [
    { key: "name", label: "Workflow Name" },
    { key: "trigger", label: "Type / Trigger" },
    {
      key: "status",
      label: "Status",
      render: (value) => <StatusBadge tone={toneForStatus(value)} label={value} />
    },
    { key: "agent", label: "Attach Agent" },
    { key: "source", label: "Source URL / Workflow ID" },
    { key: "lastUpdate", label: "Last Update" },
    {
      key: "action",
      label: "Action",
      render: (value) => (
        <button type="button" className="rounded-full border border-[rgba(62,54,46,0.12)] bg-[#f5efe2] px-3 py-1.5 text-xs font-medium text-[#3E362E]">
          {value}
        </button>
      )
    }
  ];

  return (
    <div className="space-y-4">
      <div className="grid gap-3 md:grid-cols-3">
        <input placeholder="search workflow..." className="rounded-[14px] border border-[rgba(62,54,46,0.12)] bg-[#fbf6eb] px-4 py-3 text-sm outline-none md:col-span-2" />
        <div className="grid grid-cols-2 gap-3">
          <select className="rounded-[14px] border border-[rgba(62,54,46,0.12)] bg-[#fbf6eb] px-4 py-3 text-sm outline-none">
            <option>Trigger</option>
          </select>
          <select className="rounded-[14px] border border-[rgba(62,54,46,0.12)] bg-[#fbf6eb] px-4 py-3 text-sm outline-none">
            <option>Status</option>
          </select>
        </div>
      </div>
      <SimpleTable columns={columns} rows={rows} emptyMessage="No workflow row." />
    </div>
  );
}

function WorkflowN8nPanel({ rows }) {
  return (
    <div className="space-y-3">
      {rows.map((item) => (
        <div key={item.id} className="rounded-[18px] border border-[rgba(62,54,46,0.12)] bg-[#fbf6eb] p-4">
          <div className="flex items-start justify-between gap-3">
            <div>
              <p className="text-[15px] font-semibold text-[#3E362E]">{item.name}</p>
              <p className="mt-1 text-xs text-[rgba(62,54,46,0.62)]">{item.workflowId} • {item.source}</p>
            </div>
            <StatusBadge tone={toneForStatus(item.status)} label={item.status} />
          </div>
          <div className="mt-4 grid gap-3 text-sm text-[rgba(62,54,46,0.66)]">
            <p>Agent: {item.agent}</p>
            <p>Trigger: {item.trigger}</p>
            <div className="rounded-[14px] border border-[rgba(62,54,46,0.1)] bg-[#f5efe2] px-3 py-3">
              {item.detail}
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}

function WorkspaceWindow({ title, subtitle, open, position, zIndex, widthClassName, onClose, onMove, onFocus, children }) {
  return (
    <FloatingCard
      title={title}
      subtitle={subtitle}
      open={open}
      position={position}
      zIndex={zIndex}
      widthClassName={widthClassName}
      onClose={onClose}
      onMove={onMove}
      onFocus={onFocus}
    >
      {children}
    </FloatingCard>
  );
}

function WorkspaceDashboardContent() {
  const router = useRouter();
  const [currentUser, setCurrentUser] = useState(null);
  const [realAgents, setRealAgents] = useState([]);
  const [draftAgents, setDraftAgents] = useState([]);
  const [selectedAgentId, setSelectedAgentId] = useState("");
  const [windows, setWindows] = useState(buildInitialWindows);
  const [zSeed, setZSeed] = useState(40);
  const [historyOpen, setHistoryOpen] = useState(false);
  const [promptDraft, setPromptDraft] = useState("");
  const [conversationEntries, setConversationEntries] = useState([
    {
      id: "seed-1",
      source: "Main AI",
      title: "Local preview only",
      message: "No external model call. No runtime call. No workflow execute call.",
      createdAt: new Date().toISOString()
    },
    {
      id: "seed-2",
      source: "You",
      title: "bantu convert dokumen",
      message: "Preview interaction kept local for visual shell.",
      createdAt: new Date().toISOString()
    }
  ]);

  const visibleAgents = useMemo(() => {
    const agentRows = [...draftAgents, ...realAgents];
    return agentRows.length ? agentRows : PREVIEW_AGENTS;
  }, [draftAgents, realAgents]);

  const isPreviewMode = !draftAgents.length && !realAgents.length;
  const selectedAgent = useMemo(
    () => visibleAgents.find((agent) => agent.id === selectedAgentId) || visibleAgents[0] || null,
    [selectedAgentId, visibleAgents]
  );
  const currentUserView = currentUser || {
    display_name: "nama user",
    username: "nama user",
    subscription_plan: "free",
    email: "user@email.com"
  };

  useEffect(() => {
    let active = true;

    async function loadWorkspace() {
      const [userResult, agentResult] = await Promise.allSettled([getCurrentUser(), get("/agents")]);
      if (!active) return;

      if (userResult.status === "fulfilled") {
        setCurrentUser(userResult.value);
      }

      if (agentResult.status === "fulfilled") {
        setRealAgents(normalizeCollection(agentResult.value).map(buildAgentViewModel));
      }
    }

    loadWorkspace();

    return () => {
      active = false;
    };
  }, []);

  useEffect(() => {
    if (!selectedAgentId && visibleAgents.length) {
      setSelectedAgentId(visibleAgents[0].id);
      return;
    }

    const stillExists = visibleAgents.some((agent) => agent.id === selectedAgentId);
    if (!stillExists && visibleAgents.length) {
      setSelectedAgentId(visibleAgents[0].id);
    }
  }, [selectedAgentId, visibleAgents]);

  function bringToFront(key) {
    setZSeed((current) => {
      const next = current + 1;
      setWindows((currentWindows) => ({
        ...currentWindows,
        [key]: {
          ...currentWindows[key],
          z: next
        }
      }));
      return next;
    });
  }

  function openWindow(key) {
    bringToFront(key);
    setWindows((current) => ({
      ...current,
      [key]: {
        ...current[key],
        open: true
      }
    }));
  }

  function closeWindow(key) {
    setWindows((current) => ({
      ...current,
      [key]: {
        ...current[key],
        open: false
      }
    }));
  }

  function moveWindow(key, nextPosition) {
    setWindows((current) => {
      const widthHint = WINDOW_WIDTH_HINTS[key] || 520;
      const maxX = Math.max(16, window.innerWidth - widthHint - 16);
      const maxY = Math.max(16, window.innerHeight - 640);

      return {
        ...current,
        [key]: {
          ...current[key],
          x: clamp(nextPosition.x, 16, maxX),
          y: clamp(nextPosition.y, 16, maxY)
        }
      };
    });
  }

  function handleSidebarAction(action) {
    const mapping = {
      create: "createAgent",
      importSkill: "importSkill",
      librarySkill: "librarySkill",
      libraryWorkflow: "libraryWorkflow",
      workflowN8n: "workflowN8n",
      activityLog: "activityLog",
      settings: "settings"
    };

    const nextKey = mapping[action];
    if (nextKey) openWindow(nextKey);
  }

  function handleLogout() {
    clearToken();
    router.replace("/login");
  }

  function handleCaptureCommand(agent, message) {
    setConversationEntries((current) => [
      {
        id: `cmd-${Date.now()}`,
        source: agent.name,
        title: "Command note",
        message,
        createdAt: new Date().toISOString()
      },
      ...current
    ]);
  }

  function handlePromptSubmit(event) {
    event.preventDefault();
    const trimmed = promptDraft.trim();
    if (!trimmed) return;

    setConversationEntries((current) => [
      {
        id: `prompt-${Date.now()}`,
        source: "You",
        title: "Prompt captured",
        message: trimmed,
        createdAt: new Date().toISOString()
      },
      ...current
    ]);
    setPromptDraft("");
    setHistoryOpen(true);
  }

  function handleCreatePreview(name, skill, model, pinAgent) {
    const nextAgent = {
      id: `draft-${Date.now()}`,
      name,
      status: pinAgent ? "active" : "idle",
      roleDescription: `${skill} • ${model}`,
      skillNames: [skill, "preview setup", "review output"],
      skillCount: 3,
      previewActivity: [
        { id: `draft-a-${Date.now()}`, title: "draft created", message: "local card added", createdAt: new Date().toISOString() }
      ]
    };

    setDraftAgents((current) => [nextAgent, ...current]);
    setSelectedAgentId(nextAgent.id);
  }

  const skillRows = PREVIEW_SKILLS;
  const workflowRows = PREVIEW_WORKFLOWS;
  const activityRows = PREVIEW_ACTIVITY;

  return (
    <ProtectedRoute>
      <div className="h-dvh overflow-hidden bg-[#F6F1EA] text-[#2C2217]">
        <div className="flex h-dvh overflow-hidden">
          <Sidebar
            variant="workspace"
            activeItem="create"
            onAction={handleSidebarAction}
          />

          <main className="relative flex min-w-0 flex-1 flex-col overflow-hidden">
            <Topbar currentUser={currentUserView} onLogout={handleLogout} />

            <div className="relative flex min-h-0 flex-1 overflow-hidden pb-[176px]">
              <div className="absolute inset-0 bg-[radial-gradient(circle_at_top_left,rgba(255,255,255,0.58),transparent_26%),radial-gradient(circle_at_bottom_right,rgba(184,92,56,0.08),transparent_30%)]" />

              <AgentLane
                agents={visibleAgents}
                selectedAgentId={selectedAgent?.id || ""}
                onSelectAgent={setSelectedAgentId}
                onCaptureCommand={handleCaptureCommand}
                isPreviewMode={isPreviewMode}
              />

              <WorkspaceWindow
                title="Create Agent"
                subtitle="Create agent profile only. Runtime disabled."
                open={windows.createAgent.open}
                position={{ x: windows.createAgent.x, y: windows.createAgent.y }}
                zIndex={windows.createAgent.z}
                widthClassName="w-[560px]"
                onClose={() => closeWindow("createAgent")}
                onMove={(nextPosition) => moveWindow("createAgent", nextPosition)}
                onFocus={() => bringToFront("createAgent")}
              >
                <CreateAgentPanel onCreatePreview={handleCreatePreview} />
              </WorkspaceWindow>

              <WorkspaceWindow
                title="Import Skill"
                subtitle="Preview only. No clone. No install."
                open={windows.importSkill.open}
                position={{ x: windows.importSkill.x, y: windows.importSkill.y }}
                zIndex={windows.importSkill.z}
                widthClassName="w-[520px]"
                onClose={() => closeWindow("importSkill")}
                onMove={(nextPosition) => moveWindow("importSkill", nextPosition)}
                onFocus={() => bringToFront("importSkill")}
              >
                <ImportSkillPanel />
              </WorkspaceWindow>

              <WorkspaceWindow
                title="Library Skill"
                subtitle="Excel-like table. Safe actions only."
                open={windows.librarySkill.open}
                position={{ x: windows.librarySkill.x, y: windows.librarySkill.y }}
                zIndex={windows.librarySkill.z}
                widthClassName="w-[680px]"
                onClose={() => closeWindow("librarySkill")}
                onMove={(nextPosition) => moveWindow("librarySkill", nextPosition)}
                onFocus={() => bringToFront("librarySkill")}
              >
                <LibrarySkillPanel rows={skillRows} />
              </WorkspaceWindow>

              <WorkspaceWindow
                title="Library Workflow"
                subtitle="Excel-like table. No execute."
                open={windows.libraryWorkflow.open}
                position={{ x: windows.libraryWorkflow.x, y: windows.libraryWorkflow.y }}
                zIndex={windows.libraryWorkflow.z}
                widthClassName="w-[680px]"
                onClose={() => closeWindow("libraryWorkflow")}
                onMove={(nextPosition) => moveWindow("libraryWorkflow", nextPosition)}
                onFocus={() => bringToFront("libraryWorkflow")}
              >
                <LibraryWorkflowPanel rows={workflowRows} />
              </WorkspaceWindow>

              <WorkspaceWindow
                title="Workflow n8n"
                subtitle="Preview / detail only. No trigger now."
                open={windows.workflowN8n.open}
                position={{ x: windows.workflowN8n.x, y: windows.workflowN8n.y }}
                zIndex={windows.workflowN8n.z}
                widthClassName="w-[520px]"
                onClose={() => closeWindow("workflowN8n")}
                onMove={(nextPosition) => moveWindow("workflowN8n", nextPosition)}
                onFocus={() => bringToFront("workflowN8n")}
              >
                <WorkflowN8nPanel rows={PREVIEW_N8N_CARDS} />
              </WorkspaceWindow>

              <WorkspaceWindow
                title="Activity Log"
                subtitle="Timeline / inbox. Read only."
                open={windows.activityLog.open}
                position={{ x: windows.activityLog.x, y: windows.activityLog.y }}
                zIndex={windows.activityLog.z}
                widthClassName="w-[460px]"
                onClose={() => closeWindow("activityLog")}
                onMove={(nextPosition) => moveWindow("activityLog", nextPosition)}
                onFocus={() => bringToFront("activityLog")}
              >
                <ActivityLogPanelCompact activityLogs={activityRows} filters={ACTIVITY_FILTERS} />
              </WorkspaceWindow>

              <WorkspaceWindow
                title="Settings"
                subtitle="Status only. No live provider test."
                open={windows.settings.open}
                position={{ x: windows.settings.x, y: windows.settings.y }}
                zIndex={windows.settings.z}
                widthClassName="w-[420px]"
                onClose={() => closeWindow("settings")}
                onMove={(nextPosition) => moveWindow("settings", nextPosition)}
                onFocus={() => bringToFront("settings")}
              >
                <SettingsPanelCompact
                  currentUser={currentUserView}
                  providerSettings={PREVIEW_PROVIDER_SETTINGS}
                  apiKeyStatuses={PREVIEW_API_KEYS}
                  modelProviders={PREVIEW_MODEL_PROVIDERS}
                  errors={{}}
                />
              </WorkspaceWindow>

              <PromptDock
                historyOpen={historyOpen}
                onToggleHistory={() => setHistoryOpen((current) => !current)}
                promptDraft={promptDraft}
                onPromptDraftChange={setPromptDraft}
                onPromptSubmit={handlePromptSubmit}
                conversationEntries={conversationEntries}
              />
            </div>
          </main>
        </div>
      </div>
    </ProtectedRoute>
  );
}

export default function WorkspaceDashboard() {
  return <WorkspaceDashboardContent />;
}
