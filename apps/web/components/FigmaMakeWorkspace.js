"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useRouter } from "next/navigation";

import AgentChatPanel from "./AgentChatPanel";
import ProtectedRoute from "./ProtectedRoute";
import RuntimeCapabilityPanel from "./RuntimeCapabilityPanel";
import N8nPanel from "./N8nPanel";
import { clearToken } from "../lib/auth";
import {
  approveGithubSkillImport,
  attachImportedSkillToAgent,
  createAgent,
  createN8nWorkflow,
  deleteModelProviderApiKey,
  deleteN8nWorkflow,
  detachImportedSkillFromAgent,
  get,
  getActivityLogs,
  getAuditLogs,
  getAgentActiveSkills,
  getCurrentUser,
  getModelProviderKeyStatuses,
  getModelProviderSettings,
  getModelProviders,
  getRuntimeCapabilities,
  getPendingApprovals,
  getSkillLibrary,
  getTasks,
  chatWithAgent,
  fetchAgentAvatarBlob,
  importSelectedGithubSkill,
  deleteWorkflowBinding,
  listN8nWorkflows,
  listWorkflowBindings,
  listWorkflowConsents,
  listWorkflowExecutionHistory,
  listWorkflowExecutions,
  listWorkflowTemplates,
  post,
  previewGithubSkillCollection,
  previewGithubSkillImport,
  revokeWorkflowConsent,
  rejectGithubImport,
  disableGithubImport,
  patch,
  remove,
  saveModelProviderApiKey,
  uploadAgentAvatar,
  orchestratorChat,
  updateN8nWorkflow,
  updateModelProviderSettings
} from "../lib/apiClient";

const C = {
  bg: "#F6F1EA",
  bgDeep: "#EDE6D8",
  card: "#FDFAF5",
  cardInner: "#F2EBE0",
  border: "rgba(90,65,35,0.13)",
  borderMid: "rgba(90,65,35,0.22)",
  accent: "#B85C38",
  accentLight: "rgba(184,92,56,0.10)",
  text: "#2C2217",
  textSub: "#5C4E3E",
  textMuted: "#8A7A68",
  textDim: "#B8A898",
  green: "#4E7A5E",
  greenLight: "rgba(78,122,94,0.12)",
  amber: "#B07820",
  amberLight: "rgba(176,120,32,0.12)"
};

const FONT = {
  fontFamily: 'Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif'
};
const SERIF = {
  fontFamily: '"Instrument Serif", Georgia, "Times New Roman", serif',
  fontStyle: "italic"
};

const NAV_ITEMS = [
  { id: "create-agent", label: "Create Agent", icon: "plus" },
  { id: "import-skill", label: "Import Skill", icon: "upload" },
  { id: "library-skill", label: "Library Skill", icon: "book" },
  { id: "library-workflow", label: "Library Workflow", icon: "workflow" },
  { id: "workflow-n8n", label: "Workflow n8n", icon: "nodes" }
];

const WIN_META = {
  "create-agent": { title: "Agent Panel", width: 560, ix: 230, iy: 60 },
  "skill-panel": { title: "Skill Panel", width: 640, ix: 250, iy: 80 },
  "import-skill": { title: "Import Skill", width: 720, ix: 220, iy: 90 },
  "library-skill": { title: "Library Skill", width: 900, ix: 180, iy: 70 },
  "active-skills": { title: "Active Skills", width: 620, ix: 270, iy: 100 },
  "library-workflow": { title: "Library Workflow", width: 680, ix: 250, iy: 110 },
  "workflow-n8n": { title: "Workflow n8n", width: 520, ix: 330, iy: 75 },
  providers: { title: "Provider / API Key", width: 620, ix: 290, iy: 85 },
  "oauth-connections": { title: "OAuth / Connections", width: 620, ix: 310, iy: 105 },
  "safety-center": { title: "Safety Center", width: 600, ix: 330, iy: 95 },
  "activity-log": { title: "Activity Log", width: 460, ix: 270, iy: 60 },
  "agent-detail": { title: "Agent Chat", width: 860, ix: 220, iy: 70 },
  settings: { title: "Settings Control Center", width: 1100, ix: 140, iy: 54 }
};

const SETTINGS_TABS = [
  { id: "account", label: "Account" },
  { id: "provider", label: "Provider / API Key" },
  { id: "oauth", label: "OAuth / Connections" },
  { id: "safety", label: "Safety Center" },
  { id: "activity", label: "Activity Log" },
  { id: "runtime", label: "Runtime Capabilities" },
  { id: "plan", label: "Plan / Limits" },
  { id: "system", label: "System Info" }
];

const PREVIEW_AGENTS = [
  {
    id: 1,
    name: "Doc Converter",
    icon: "DC",
    skillCount: 3,
    skills: ["convert pdf", "convert document", "convert excel"],
    status: "idle",
    activity: ["idle", "sedang convert", "sedang mengirim"],
    needApproval: false
  },
  {
    id: 2,
    name: "Mail Agent",
    icon: "MA",
    skillCount: 3,
    skills: ["draft email", "send report", "schedule send"],
    status: "sending",
    activity: ["queue", "draft ready", "waiting send"],
    needApproval: true
  },
  {
    id: 3,
    name: "Data Parser",
    icon: "DP",
    skillCount: 3,
    skills: ["parse json", "extract csv", "transform xml"],
    status: "active",
    activity: ["parse json", "extract csv", "transform xml"],
    needApproval: false
  },
  {
    id: 4,
    name: "Summarizer",
    icon: "SU",
    skillCount: 3,
    skills: ["summarize doc", "extract key pts", "generate tldr"],
    status: "idle",
    activity: ["idle", "draft summary", "review tldr"],
    needApproval: false
  },
  {
    id: 5,
    name: "Notifier",
    icon: "NO",
    skillCount: 3,
    skills: ["slack notify", "webhook push", "log event"],
    status: "active",
    activity: ["slack notify", "webhook push", "log event"],
    needApproval: false
  },
  {
    id: 6,
    name: "Translator",
    icon: "TR",
    skillCount: 2,
    skills: ["translate text", "detect language"],
    status: "idle",
    activity: ["idle", "review phrase", "translate id-en"],
    needApproval: false
  },
  {
    id: 7,
    name: "Scheduler",
    icon: "SC",
    skillCount: 2,
    skills: ["schedule task", "set reminder"],
    status: "idle",
    activity: ["idle", "queue task", "set reminder"],
    needApproval: false
  }
];

const PREVIEW_SKILLS = [
  {
    id: "skill-1",
    name: "PDF Helper",
    type: "prompt_skill",
    status: "approved",
    runtimeStatus: "preview only",
    agent: "Doc Converter",
    sourceUrl: "github.com/private/pdf-helper",
    lastUpdate: "2026-06-18 21:10",
    action: "Attach"
  },
  {
    id: "skill-2",
    name: "Knowledge Index",
    type: "knowledge_skill",
    status: "imported",
    runtimeStatus: "safe",
    agent: "Data Parser",
    sourceUrl: "github.com/private/knowledge-index",
    lastUpdate: "2026-06-19 18:40",
    action: "Attach"
  },
  {
    id: "skill-3",
    name: "JSON Parser",
    type: "tool_skill",
    status: "blocked",
    runtimeStatus: "blocked",
    agent: "Data Parser",
    sourceUrl: "github.com/private/json-parser",
    lastUpdate: "2026-06-20 09:20",
    action: "View"
  },
  {
    id: "skill-4",
    name: "Slack Sync Flow",
    type: "workflow_skill",
    status: "blocked",
    runtimeStatus: "blocked",
    agent: "Notifier",
    sourceUrl: "github.com/private/slack-sync-flow",
    lastUpdate: "2026-06-20 09:30",
    action: "View"
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
    id: "activity-preview-1",
    created_at: "2026-06-20T07:10:00Z",
    event_type: "workspace.preview",
    message: "Workspace preview loaded.",
    status: "info",
    actor_type: "system"
  },
  {
    id: "activity-preview-2",
    created_at: "2026-06-20T07:20:00Z",
    event_type: "provider.snapshot",
    message: "Provider metadata ready.",
    status: "info",
    actor_type: "system"
  },
  {
    id: "activity-preview-3",
    created_at: "2026-06-20T07:30:00Z",
    event_type: "safety.lock",
    message: "Tool and n8n execution stay locked.",
    status: "review",
    actor_type: "system"
  }
];

const SKILL_ROWS = [
  { name: "PDF Helper", type: "file", status: "active", agent: "Doc Converter" },
  { name: "Excel Parser", type: "file", status: "review", agent: "Data Parser" },
  { name: "Mail Draft", type: "function", status: "active", agent: "Mail Agent" },
  { name: "Webhook Push", type: "function", status: "inactive", agent: "Notifier" }
];

const FLOW_ROWS = [
  { name: "Daily Report", type: "schedule", status: "active", agent: "Doc Converter" },
  { name: "Approval Gate", type: "webhook", status: "review", agent: "Mail Agent" },
  { name: "Data Sync", type: "manual", status: "inactive", agent: "Data Parser" }
];

const N8N_ROWS = [
  { name: "Daily Report", id: "wf_001", agent: "Doc Converter", trigger: "schedule", status: "active" },
  { name: "Approval Gate", id: "wf_002", agent: "Mail Agent", trigger: "webhook", status: "review" },
  { name: "Data Sync", id: "wf_003", agent: "Data Parser", trigger: "manual", status: "inactive" }
];

const SETTINGS_KEYS = [
  { provider: "OpenAI", masked: "sk-************3f2a", status: "encrypted" },
  { provider: "OpenRouter", masked: "not set", status: "not setup" }
];

const SKILL_TYPE_META = {
  prompt_skill: {
    label: "Prompt",
    detail: "Prompt / instruction",
    executionState: "preview only",
    blocked: false
  },
  knowledge_skill: {
    label: "Knowledge",
    detail: "Read-only context",
    executionState: "safe",
    blocked: false
  },
  tool_skill: {
    label: "Tool",
    detail: "Blocked from execution",
    executionState: "blocked",
    blocked: true
  },
  workflow_skill: {
    label: "Workflow",
    detail: "Blocked from execution",
    executionState: "blocked",
    blocked: true
  }
};

function normalizeSkillType(type) {
  const raw = String(type || "").toLowerCase();

  if (raw === "manual_skill" || raw === "prompt" || raw === "instruction") {
    return "prompt_skill";
  }

  if (raw === "knowledge" || raw === "knowledge_skill") {
    return "knowledge_skill";
  }

  if (raw === "tool" || raw === "tool_preview" || raw === "tool_skill") {
    return "tool_skill";
  }

  if (raw === "workflow" || raw === "workflow_preview" || raw === "workflow_skill") {
    return "workflow_skill";
  }

  return raw || "prompt_skill";
}

function getSkillTypeMeta(type) {
  return SKILL_TYPE_META[normalizeSkillType(type)] || SKILL_TYPE_META.prompt_skill;
}

function normalizeCollection(payload) {
  return normalizeArrayResponse(payload);
}

function normalizeArrayResponse(payload, preferredKeys = []) {
  if (Array.isArray(payload)) return payload;
  if (!payload || typeof payload !== "object") return [];

  const keys = [...preferredKeys, "items", "data", "results", "skills", "imported_skills", "active_skills", "candidates"];
  for (const key of keys) {
    if (Array.isArray(payload[key])) {
      return payload[key];
    }
  }

  return [];
}

function normalizeObjectResponse(payload, fallback = {}) {
  if (!payload || typeof payload !== "object" || Array.isArray(payload)) {
    return fallback;
  }

  return payload;
}

function safeString(value, fallback = "-") {
  const text = typeof value === "string" ? value.trim() : value;
  return text ? String(text) : fallback;
}

function getSkillLibraryId(skill, fallbackIndex = 0) {
  const candidate = skill?.id || skill?.skill_id || skill?.imported_skill_id || skill?.import_id || skill?.slug || skill?.name || "";
  return safeString(candidate, fallbackIndex ? `skill-${fallbackIndex + 1}` : "");
}

function getSkillLibraryLabel(skill) {
  return safeString(skill?.name || skill?.title || skill?.display_name || skill?.slug || skill?.skill_path, "Unnamed skill");
}

function getSkillLibraryType(skill) {
  const raw = String(skill?.skill_type || skill?.type || "").toLowerCase();

  if (raw === "prompt" || raw === "instruction" || raw === "manual_skill") {
    return "prompt_skill";
  }

  if (raw === "knowledge") {
    return "knowledge_skill";
  }

  if (raw === "workflow" || raw === "workflow_preview") {
    return "workflow_skill";
  }

  if (raw === "tool" || raw === "tool_preview") {
    return "tool_skill";
  }

  if (raw === "prompt_skill" || raw === "knowledge_skill" || raw === "workflow_skill" || raw === "tool_skill") {
    return raw;
  }

  return "unknown";
}

function getSkillLibraryTypeLabel(type) {
  const normalized = String(type || "").toLowerCase();
  const labels = {
    prompt_skill: "prompt",
    knowledge_skill: "knowledge",
    workflow_skill: "workflow",
    tool_skill: "tool",
    unknown: "unknown"
  };

  return labels[normalized] || labels.unknown;
}

function getSkillLibraryStatus(skill) {
  return safeString(skill?.import_status || skill?.security_status || skill?.status, "unknown");
}

function getSkillLibraryDescription(skill) {
  return safeString(skill?.description || skill?.summary || skill?.content_preview || skill?.file_path || skill?.source_reference, "");
}

function getSkillLibrarySelectionState(skill) {
  const id = getSkillLibraryId(skill);
  const status = String(skill?.status || skill?.import_status || skill?.security_status || "").toLowerCase();
  const attachBlockReason = safeString(skill?.attach_block_reason, "");
  const rejected = status === "rejected" || status === "disabled" || status === "blocked" || status === "pending" || status === "draft" || status === "inactive";
  const isAttachable = skill?.is_attachable !== false && !rejected;
  const selectable = Boolean(id) && isAttachable;

  return {
    id,
    selectable,
    disabledReason: selectable ? "" : attachBlockReason || (Boolean(id) ? `Status ${status || "unknown"}` : "Missing skill id.")
  };
}

function isSkillSelectable(skill) {
  return Boolean(getSkillLibrarySelectionState(skill).selectable);
}

function getSkillPickerEntry(skill, index, selectedSkillIdSet = new Set()) {
  const id = getSkillLibraryId(skill, index);
  const type = getSkillLibraryType(skill);
  const selectionState = getSkillLibrarySelectionState(skill);
  const label = getSkillLibraryLabel(skill);
  const status = getSkillLibraryStatus(skill);
  const description = getSkillLibraryDescription(skill);
  const searchText = [label, id, type, status, description].join(" ").toLowerCase();
  const selected = selectedSkillIdSet.has(id);

  return {
    raw: skill,
    id,
    label,
    type,
    typeLabel: getSkillLibraryTypeLabel(type),
    status,
    description,
    selected,
    selectable: isSkillSelectable(skill),
    disabledReason: selectionState.disabledReason,
    searchText,
  };
}

function normalizeSkillPickerOptions(skills, selectedSkillIds = [], query = "") {
  const source = Array.isArray(skills) ? skills : [];
  const selectedSkillIdSet = new Set((Array.isArray(selectedSkillIds) ? selectedSkillIds : []).map((item) => String(item || "").trim()).filter(Boolean));
  const normalizedQuery = String(query || "").trim().toLowerCase();

  return source
    .map((skill, index) => getSkillPickerEntry(skill, index, selectedSkillIdSet))
    .filter((item) => !normalizedQuery || item.searchText.includes(normalizedQuery))
    .sort((a, b) => {
      if (a.selectable !== b.selectable) return a.selectable ? -1 : 1;
      if (a.selected !== b.selected) return a.selected ? -1 : 1;
      const statusRank = (value) => {
        const normalized = String(value || "").toLowerCase();
        if (normalized === "approved" || normalized === "active" || normalized === "ready" || normalized === "imported") return 0;
        if (normalized === "review" || normalized === "warning") return 1;
        if (normalized === "pending" || normalized === "draft") return 2;
        if (normalized === "disabled" || normalized === "rejected" || normalized === "blocked" || normalized === "inactive") return 3;
        return 2;
      };

      const statusDiff = statusRank(a.status) - statusRank(b.status);
      if (statusDiff !== 0) return statusDiff;
      return a.label.localeCompare(b.label);
    });
}

function formatShortDate(value) {
  if (!value) {
    return "-";
  }

  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) {
    return "-";
  }

  return new Intl.DateTimeFormat("id-ID", {
    day: "2-digit",
    month: "short",
    hour: "2-digit",
    minute: "2-digit"
  }).format(parsed);
}

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

function getAgentInitials(name) {
  const source = String(name || "AI").trim();

  if (!source) {
    return "AI";
  }

  const words = source
    .split(/\s+/)
    .filter(Boolean);

  if (!words.length) {
    return "AI";
  }

  return words
    .slice(0, 2)
    .map((word) => word.charAt(0))
    .join("")
    .toUpperCase();
}

function buildAgentActivities(agent, activityRows, fallbackRows) {
  const agentId = String(agent?.id || "");
  const agentName = String(agent?.name || "").toLowerCase();

  const matches = activityRows.filter((row) => {
    const actorId = String(row?.actor_id || "");
    const message = String(row?.message || "").toLowerCase();
    const eventType = String(row?.event_type || "").toLowerCase();
    return actorId === agentId || message.includes(agentName) || eventType.includes("agent");
  });

  if (matches.length) {
    return matches.slice(0, 3).map((row) => row.message || row.event_type || "-");
  }

  return fallbackRows.slice(0, 2);
}

function buildAgentView(agent, index, agentSkillMap, activityRows, approvalRows, fallbackAgent) {
  if (!agent) return fallbackAgent;

  const skillItems = agentSkillMap[String(agent.id)] || [];
  const skillNames = skillItems
    .map((item) => {
      const skill = item?.skill || {};
      return skill?.title || skill?.name || skill?.slug || skill?.file_path || "";
    })
    .filter(Boolean);

  const fallbackSkills = fallbackAgent?.skills || [];

  const pendingApproval = approvalRows.find((row) => String(row?.agent_id || "") === String(agent.id)) || null;

  return {
    id: String(agent.id),
    name: agent.name || `Agent ${index + 1}`,
    icon: getAgentInitials(agent.name),
    skillCount: skillNames.length || skillItems.length || Number(agent.skill_count || 0) || fallbackSkills.length || 0,
    skills: skillNames.length ? skillNames : fallbackSkills,
    status: agent.status || "inactive",
    activity: buildAgentActivities(agent, activityRows, fallbackAgent?.activity || []),
    needApproval: Boolean(pendingApproval),
    approval: pendingApproval
  };
}

function buildSkillRows(skillRows, selectedAgent, agentSkillMap) {
  const attachedSkillIds = new Set();
  const attachedAgentBySkill = new Map();

  Object.entries(agentSkillMap).forEach(([agentId, skills]) => {
    skills.forEach((item) => {
      const skill = item?.skill || {};
      if (skill?.id) {
        attachedSkillIds.add(String(skill.id));
        attachedAgentBySkill.set(String(skill.id), String(agentId));
      }
    });
  });

  return skillRows.map((row, index) => {
    const id = String(row?.id || `skill-${index + 1}`);
    const isAttached = attachedSkillIds.has(id);
    const attachedAgentId = attachedAgentBySkill.get(id) || "";
    const attachedAgentLabel = attachedAgentId && selectedAgent?.id === attachedAgentId ? selectedAgent?.name : row.agent || "-";
    const status = row?.import_status || row?.security_status || row?.status || "active";
    const normalizedType = normalizeSkillType(row?.skill_type || row?.type || "prompt_skill");
    const typeMeta = getSkillTypeMeta(normalizedType);
    const hasReviewSignal = Boolean(row?.security_status === "warning" || row?.security_status === "blocked" || row?.attach_block_reason);
    const actions = row?.is_attachable
      ? isAttached
        ? ["Detach", "Disable"]
        : ["Attach", "Disable"]
      : ["View"];

    return {
      id,
      name: row?.title || row?.name || `Skill ${index + 1}`,
      type: normalizedType,
      typeLabel: typeMeta.label,
      typeDetail: typeMeta.detail,
      status,
      runtimeStatus: row?.is_attachable === false || typeMeta.blocked ? "blocked" : hasReviewSignal ? "review" : typeMeta.executionState,
      agent: attachedAgentLabel,
      sourceUrl: row?.source_url || row?.source_reference || row?.file_path || "-",
      lastUpdate: formatShortDate(row?.updated_at || row?.created_at),
      action: actions[0] || "View",
      actions,
      attachedAgentId,
      blockedReason: row?.attach_block_reason || (typeMeta.blocked ? "Non-executable skill." : ""),
      raw: row
    };
  });
}

function buildWorkflowRows(workflows, templates, consents, bindings, executions, history) {
  if (workflows.length) {
    return workflows.map((row, index) => ({
      id: String(row?.id || `workflow-${index + 1}`),
      name: row?.name || `Workflow ${index + 1}`,
      type: row?.trigger_type || "manual",
      status: row?.status || "inactive",
      agent: row?.metadata?.agent_name || row?.metadata?.agent || row?.metadata?.agent_id || "-",
      source: row?.workflow_external_id || row?.slug || String(row?.id || "-"),
      lastUpdate: formatShortDate(row?.updated_at || row?.created_at),
      action: row?.status === "active" ? "Disable" : "View",
      raw: row
    }));
  }

  const bindingMap = new Map(bindings.map((item) => [String(item?.template_id || ""), item]));
  const consentMap = new Map(consents.map((item) => [String(item?.template_id || ""), item]));
  const executionMap = new Map();
  [...executions, ...history].forEach((item) => {
    const key = String(item?.template_id || "");
    if (!key) return;
    if (!executionMap.has(key)) {
      executionMap.set(key, item);
    }
  });

  return templates.map((template, index) => {
    const binding = bindingMap.get(String(template?.id || ""));
    const consent = consentMap.get(String(template?.id || ""));
    const execution = executionMap.get(String(template?.id || ""));
    const name = template?.name || `Workflow ${index + 1}`;
    const status = consent?.status === "active" || template?.consented ? "active" : template?.enabled ? "preview" : "disabled";
    return {
      id: String(template?.id || `template-${index + 1}`),
      name,
      type: template?.risk_level || "manual",
      status,
      agent: binding?.skill_name || binding?.skill_id || "-",
      source: template?.id || "-",
      lastUpdate: formatShortDate(consent?.consented_at || execution?.created_at || template?.consented_at || template?.updated_at),
      action: status === "active" ? "Disable" : "View",
      raw: { template, consent, binding, execution }
    };
  });
}

function buildN8nRows(workflows, templates, consents, bindings, executions, history) {
  if (workflows.length) {
    return workflows.map((row, index) => ({
      id: String(row?.id || `n8n-${index + 1}`),
      name: row?.name || `Workflow ${index + 1}`,
      status: row?.status || "inactive",
      workflowId: row?.workflow_external_id || row?.slug || String(row?.id || "-"),
      source: row?.description || row?.metadata?.source || "workspace record",
      agent: row?.metadata?.agent_name || row?.metadata?.agent || "-",
      trigger: row?.trigger_type || "manual",
      detail: row?.description || "Preview only. No execution."
    }));
  }

  const consentMap = new Map(consents.map((item) => [String(item?.template_id || ""), item]));
  const bindingMap = new Map(bindings.map((item) => [String(item?.template_id || ""), item]));
  const executionMap = new Map();
  [...executions, ...history].forEach((item) => {
    const key = String(item?.template_id || "");
    if (!key) return;
    if (!executionMap.has(key)) {
      executionMap.set(key, item);
    }
  });

  return templates.slice(0, 4).map((template, index) => {
    const consent = consentMap.get(String(template?.id || ""));
    const binding = bindingMap.get(String(template?.id || ""));
    const execution = executionMap.get(String(template?.id || ""));
    return {
      id: String(template?.id || `n8n-${index + 1}`),
      name: template?.name || `Workflow ${index + 1}`,
      status: consent?.status === "active" || template?.consented ? "preview" : "locked",
      workflowId: template?.id || "-",
      source: template?.description || "workspace template",
      agent: binding?.skill_name || binding?.skill_id || "-",
      trigger: template?.input_schema ? "manual" : "scheduled",
      detail: execution?.output_summary || template?.description || "Preview only. No execution."
    };
  });
}

function buildActivityRows(activityRows) {
  return activityRows.map((row, index) => {
    const status = String(row?.status || row?.event_type || "info").toLowerCase();
    return {
      id: String(row?.id || `activity-${index + 1}`),
      time: formatTimeOnly(row?.created_at),
      title: row?.event_type || row?.title || `Activity ${index + 1}`,
      desc: row?.message || row?.detail || "-",
      status: row?.status || row?.event_type || "info",
      tone: status,
      actor: row?.actor_type || "-"
    };
  });
}

function buildAuditRows(auditRows) {
  return auditRows.map((row, index) => {
    const action = String(row?.action || "audit").toLowerCase();
    const entityType = safeString(row?.entity_type, "entity");
    const entityId = safeString(row?.entity_id, "-");
    return {
      id: String(row?.id || `audit-${index + 1}`),
      time: formatShortDate(row?.created_at),
      title: row?.action || `Audit ${index + 1}`,
      desc: [entityType, entityId, row?.ip_address ? `ip ${row.ip_address}` : ""].filter(Boolean).join(" | "),
      status: row?.action || "audit",
      tone: action,
      actor: row?.user_id || "-"
    };
  });
}

function buildTaskRows(taskRows) {
  return taskRows.map((row, index) => {
    const status = String(row?.status || "received").toLowerCase();
    const skillId = safeString(row?.selected_skill_id, "");
    const toolId = safeString(row?.selected_tool_id, "");
    const selection = skillId ? `skill ${skillId}` : toolId ? `tool ${toolId}` : "no selection";
    const inputText = safeString(row?.input_text, `Task ${index + 1}`);
    return {
      id: String(row?.id || `task-${index + 1}`),
      time: formatShortDate(row?.created_at),
      title: inputText.length > 84 ? `${inputText.slice(0, 84)}...` : inputText,
      desc: [row?.request_id ? `request ${row.request_id}` : "", selection].filter(Boolean).join(" | "),
      status: row?.status || "received",
      tone: status,
      actor: row?.agent_id || "-",
      startedAt: formatShortDate(row?.started_at),
      completedAt: formatShortDate(row?.completed_at)
    };
  });
}

function buildApprovalRows(approvalRows) {
  return approvalRows.map((row, index) => {
    const status = String(row?.status || "pending").toLowerCase();
    const riskLevel = String(row?.risk_level || "medium").toLowerCase();
    return {
      id: String(row?.id || `approval-${index + 1}`),
      time: formatShortDate(row?.created_at),
      title: row?.requested_action || `Approval ${index + 1}`,
      desc: [row?.task_id ? `task ${row.task_id}` : "", row?.agent_id ? `agent ${row.agent_id}` : ""].filter(Boolean).join(" | "),
      status: row?.status || "pending",
      tone: status,
      riskLevel,
      taskId: row?.task_id || "-",
      decisionReason: safeString(row?.decision_reason, ""),
      isPending: status === "pending",
      raw: row
    };
  });
}

function clampCardPosition(x, y, width, height) {
  if (typeof window === "undefined") {
    return { x, y };
  }

  const margin = 12;
  const maxX = Math.max(margin, window.innerWidth - width - margin);
  const maxY = Math.max(margin, window.innerHeight - height - margin);

  return {
    x: Math.min(Math.max(margin, x), maxX),
    y: Math.min(Math.max(margin, y), maxY)
  };
}

function getCenteredCardPosition(width, height, offsetX = 0, offsetY = 0) {
  if (typeof window === "undefined") {
    return { x: 24 + offsetX, y: 24 + offsetY };
  }

  const left = Math.round((window.innerWidth - width) / 2) + offsetX;
  const top = Math.round((window.innerHeight - height) / 2) + offsetY;
  return clampCardPosition(left, top, width, height);
}

function getBrainProviderKey(provider, fallbackIndex = 0) {
  return safeString(provider?.id || provider?.provider || provider?.name || `brain-${fallbackIndex + 1}`, "");
}

function getBrainProviderLabel(provider) {
  return safeString(provider?.name || provider?.label || provider?.provider || provider?.id, "Default workspace");
}

function getBrainModelName(provider, providerSettings = null) {
  return safeString(
    provider?.model_name || provider?.default_model_name || provider?.preferred_model || provider?.model || providerSettings?.preferred_model || "gpt-4o",
    "gpt-4o"
  );
}

function getBrainModeLabel(modelName) {
  const normalized = String(modelName || "").toLowerCase();
  if (normalized.includes("mini") || normalized.includes("fast")) {
    return "fast";
  }
  if (normalized.includes("reason") || normalized.includes("o1") || normalized.includes("thinking")) {
    return "reasoning";
  }
  if (normalized.includes("code")) {
    return "coding";
  }
  return "balanced";
}

function getBrainStatusLabel(provider, providerSettings = null, apiKeyStatuses = []) {
  const providerKey = String(provider?.provider || provider?.id || provider?.name || "").toLowerCase();
  const providerType = String(provider?.provider_type || provider?.type || "").toLowerCase();
  const authType = String(provider?.auth_type || "").toLowerCase();
  const isLocal = providerType.includes("local") || providerType.includes("ollama") || providerKey.includes("local");
  const keyStatus = (Array.isArray(apiKeyStatuses) ? apiKeyStatuses : []).find((item) => String(item?.provider || "").toLowerCase() === providerKey) || null;
  const connectionStatus = String(keyStatus?.connection_status || provider?.connection_status || "").toLowerCase();
  const preferredProvider = String(providerSettings?.preferred_provider || "").toLowerCase();

  if (providerKey && providerKey === preferredProvider) {
    return "default";
  }
  if (isLocal || authType === "deferred" || connectionStatus === "deferred") {
    return "deferred";
  }
  if (connectionStatus === "active" || connectionStatus === "configured") {
    return "configured";
  }
  if (connectionStatus === "locked" || authType === "oauth_gateway" || providerType.includes("subscription_oauth")) {
    return "deferred";
  }
  if (providerKey) {
    return "not configured";
  }
  return "default";
}

function getBrainDescription(provider, providerSettings = null) {
  return safeString(
    provider?.description ||
      provider?.summary ||
      provider?.notes ||
      provider?.model_description ||
      (provider ? `${getBrainProviderLabel(provider)} · ${getBrainModelName(provider, providerSettings)}` : "Default workspace model will be used."),
    "Default workspace model will be used."
  );
}

function getBrainOptions(modelProviders = [], providerSettings = null, apiKeyStatuses = []) {
  const providers = Array.isArray(modelProviders) ? modelProviders : [];
  const preferredProvider = String(providerSettings?.preferred_provider || "").toLowerCase();
  const preferredModel = safeString(providerSettings?.preferred_model, "gpt-4o");
  const options = [];
  const defaultOption = {
    id: "default-workspace",
    providerId: "default",
    providerKey: "default",
    providerLabel: "Default workspace",
    model: preferredModel,
    mode: getBrainModeLabel(preferredModel),
    status: "default",
    description: "Default workspace model will be used.",
    selectable: true,
    family: "default"
  };

  options.push(defaultOption);

  providers.forEach((provider, index) => {
    const providerId = getBrainProviderKey(provider, index);
    const providerLabel = getBrainProviderLabel(provider);
    const model = getBrainModelName(provider, providerSettings);
    const mode = getBrainModeLabel(model);
    const providerKey = String(provider?.provider || provider?.provider_type || provider?.type || providerId).toLowerCase();
    const family =
      providerKey.includes("anthropic") || providerLabel.toLowerCase().includes("anthropic")
        ? "anthropic"
        : providerKey.includes("google") || providerLabel.toLowerCase().includes("google")
          ? "google"
          : providerKey.includes("local") || providerKey.includes("ollama") || providerLabel.toLowerCase().includes("local")
            ? "local"
            : providerKey.includes("openrouter") || providerLabel.toLowerCase().includes("openrouter")
              ? "openrouter"
              : "openai";
    const status = getBrainStatusLabel(provider, providerSettings, apiKeyStatuses);
    const selectable = status === "configured" || status === "default";
    const preferred = providerKey === preferredProvider;

    options.push({
      id: providerId,
      providerId,
      providerKey,
      providerLabel,
      model,
      mode,
      status,
      preferred,
      selectable,
      family,
      description: getBrainDescription(provider, providerSettings)
    });
  });

  if (!providers.length) {
    options.push({
      id: "openai-gpt-4o",
      providerId: "openai",
      providerKey: "openai",
      providerLabel: "OpenAI",
      model: preferredModel,
      mode: getBrainModeLabel(preferredModel),
      status: "default",
      preferred: true,
      selectable: true,
      family: "openai",
      description: "Balanced general workspace model."
    });
    options.push({
      id: "openai-gpt-4o-mini",
      providerId: "openai",
      providerKey: "openai",
      providerLabel: "OpenAI",
      model: "gpt-4o-mini",
      mode: "fast",
      status: "not configured",
      preferred: false,
      selectable: false,
      family: "openai",
      description: "Fast and cheaper model."
    });
  }

  return options;
}

function getGitHubImportStatusMeta(validationStatus, imported = false, importStatus = "") {
  const normalized = String(validationStatus || importStatus || "").toLowerCase();

  if (imported || normalized === "imported" || normalized === "approved") {
    return { tone: "ready", label: "Already in library" };
  }

  if (normalized === "blocked") {
    return { tone: "blocked", label: "Blocked: needs review" };
  }

  if (normalized === "warning" || normalized === "review" || normalized === "pending") {
    return { tone: "review", label: "Review needed" };
  }

  if (normalized === "rejected") {
    return { tone: "rejected", label: "Rejected" };
  }

  if (normalized === "disabled") {
    return { tone: "inactive", label: "Disabled" };
  }

  return { tone: "safe", label: "Safe to import" };
}

function getGitHubImportBlockedSummary(candidate) {
  const rawText = [
    candidate?.warning,
    candidate?.review_notes,
    candidate?.description,
    candidate?.content_preview,
    Array.isArray(candidate?.inspection_errors) ? candidate.inspection_errors.join(" ") : "",
    Array.isArray(candidate?.inspection_warnings) ? candidate.inspection_warnings.join(" ") : ""
  ]
    .filter(Boolean)
    .join(" ")
    .toLowerCase();

  if (!rawText) {
    return "Needs review.";
  }

  if (rawText.includes("localhost") || rawText.includes("127.0.0.1")) {
    return "Localhost reference detected";
  }

  if (rawText.includes("local file") || rawText.includes("file path") || rawText.includes("drive path") || rawText.includes("/tmp")) {
    return "Local file path detected";
  }

  if (rawText.includes("external resource") || rawText.includes("http://") || rawText.includes("https://")) {
    return "External resource reference detected";
  }

  if (rawText.includes("resource reference")) {
    return "Resource reference detected";
  }

  if (rawText.includes("blocked")) {
    return "Blocked reference detected";
  }

  return safeString(candidate?.warning || candidate?.review_notes || candidate?.description || candidate?.content_preview || "", "Needs review.");
}

function getGitHubImportTechnicalDetail(candidate) {
  const text = safeString(
    candidate?.warning ||
      candidate?.review_notes ||
      (Array.isArray(candidate?.inspection_errors) ? candidate.inspection_errors.join(" · ") : "") ||
      (Array.isArray(candidate?.inspection_warnings) ? candidate.inspection_warnings.join(" · ") : "") ||
      candidate?.content_preview ||
      "",
    ""
  );

  return text;
}

function getGitHubImportFriendlyError(error) {
  const raw = safeString(error?.message || error, "");
  const lowered = raw.toLowerCase();

  if (!raw) {
    return { message: "Import gagal.", technical: "" };
  }

  if (lowered.includes("slug") || lowered.includes("already in use") || lowered.includes("already in your library") || lowered.includes("duplicate")) {
    return {
      message: "This skill is already in your library. Review it in Skill Library or choose a different skill.",
      technical: raw
    };
  }

  if (lowered.includes("blocked")) {
    return {
      message: "This skill cannot be imported until blocked references are cleaned.",
      technical: raw
    };
  }

  return { message: raw, technical: "" };
}

function getGitHubImportCandidateView(candidate, selectedSkillPath = "", importedSkillPath = "") {
  const path = safeString(candidate?.path || candidate?.manifest_path || "", "");
  const manifestPath = safeString(candidate?.manifest_path || candidate?.path || "", "");
  const title = safeString(candidate?.title || path || manifestPath, "skill");
  const skillType = safeString(candidate?.skill_import_type || "skill import", "skill import");
  const status = String(candidate?.validation_status || candidate?.status || candidate?.import_status || "").toLowerCase();
  const imported = Boolean(importedSkillPath) && (path === importedSkillPath || manifestPath === importedSkillPath);
  const statusMeta = getGitHubImportStatusMeta(status, imported, candidate?.import_status);
  const searchText = [title, path, manifestPath, skillType, safeString(candidate?.description || ""), safeString(candidate?.warning || ""), status, statusMeta.label]
    .join(" ")
    .toLowerCase();

  return {
    raw: candidate,
    path,
    manifestPath,
    title,
    description: safeString(candidate?.description || "", ""),
    skillType,
    validationStatus: status || "review",
    imported,
    selected: Boolean(selectedSkillPath) && (path === selectedSkillPath || manifestPath === selectedSkillPath),
    statusMeta,
    blockedSummary: getGitHubImportBlockedSummary(candidate),
    technicalDetail: getGitHubImportTechnicalDetail(candidate),
    searchText
  };
}

function useDraggableCardPosition(isOpen, width, height) {
  const [position, setPosition] = useState(() => getCenteredCardPosition(width, height));
  const dragStateRef = useRef(null);
  const [isDragging, setIsDragging] = useState(false);

  useEffect(() => {
    if (!isOpen) {
      return;
    }
    setPosition((current) => clampCardPosition(current.x, current.y, width, height));
  }, [height, isOpen, width]);

  const startDrag = useCallback(
    (event) => {
      if (event.button !== 0) {
        return;
      }

      event.preventDefault();
      dragStateRef.current = {
        startX: event.clientX,
        startY: event.clientY,
        originX: position.x,
        originY: position.y
      };
      setIsDragging(true);
    },
    [position.x, position.y]
  );

  useEffect(() => {
    if (!isOpen || !isDragging) {
      return undefined;
    }

    function handleMove(event) {
      const dragState = dragStateRef.current;
      if (!dragState) {
        return;
      }

      const nextX = dragState.originX + (event.clientX - dragState.startX);
      const nextY = dragState.originY + (event.clientY - dragState.startY);
      setPosition(clampCardPosition(nextX, nextY, width, height));
    }

    function handleUp() {
      dragStateRef.current = null;
      setIsDragging(false);
    }

    document.addEventListener("mousemove", handleMove);
    document.addEventListener("mouseup", handleUp);

    return () => {
      document.removeEventListener("mousemove", handleMove);
      document.removeEventListener("mouseup", handleUp);
    };
  }, [height, isDragging, isOpen, width]);

  return { position, startDrag, isDragging, setPosition };
}

function SvgIcon({ children, size = 15 }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.85"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      {children}
    </svg>
  );
}

function MenuIcon({ name }) {
  switch (name) {
    case "plus":
      return (
        <SvgIcon>
          <path d="M12 5v14" />
          <path d="M5 12h14" />
        </SvgIcon>
      );
    case "upload":
      return (
        <SvgIcon>
          <path d="M12 16V6" />
          <path d="m8 10 4-4 4 4" />
          <path d="M5 18h14" />
        </SvgIcon>
      );
    case "book":
      return (
        <SvgIcon>
          <path d="M4 6.5A2.5 2.5 0 0 1 6.5 4H20v15.5a.5.5 0 0 1-.8.4C18 19.2 16.5 18 14 18c-2.7 0-4.1 1.3-5.2 1.9a.5.5 0 0 1-.8-.4V6.5Z" />
          <path d="M8 7h8" />
          <path d="M8 10h8" />
        </SvgIcon>
      );
    case "spark":
      return (
        <SvgIcon>
          <path d="M12 3l1.9 5.4L19 10.5l-5.1 2.1L12 18l-1.9-5.4L5 10.5l5.1-2.1L12 3Z" />
          <path d="M4 19.5h3" />
          <path d="M17 19.5h3" />
        </SvgIcon>
      );
    case "key":
      return (
        <SvgIcon>
          <circle cx="8" cy="12" r="3" />
          <path d="M11 12h9" />
          <path d="M17 12v3" />
          <path d="M19 12v2" />
        </SvgIcon>
      );
    case "link":
      return (
        <SvgIcon>
          <path d="M9 12a4 4 0 0 1 4-4h2" />
          <path d="M15 12a4 4 0 0 1-4 4H9" />
          <path d="M7 12h10" />
          <path d="M12 8v8" />
        </SvgIcon>
      );
    case "shield":
      return (
        <SvgIcon>
          <path d="M12 3 19 6v6c0 4.4-3.2 8-7 11-3.8-3-7-6.6-7-11V6l7-3Z" />
          <path d="M9.5 12.2 11.2 14 14.8 10.4" />
        </SvgIcon>
      );
    case "workflow":
      return (
        <SvgIcon>
          <circle cx="6" cy="6" r="2.5" />
          <circle cx="18" cy="12" r="2.5" />
          <circle cx="6" cy="18" r="2.5" />
          <path d="M8.5 7.5 15.5 10.5" />
          <path d="M8.5 16.5 15.5 13.5" />
        </SvgIcon>
      );
    case "nodes":
      return (
        <SvgIcon>
          <rect x="3.5" y="4.5" width="5" height="5" rx="1.2" />
          <rect x="15.5" y="4.5" width="5" height="5" rx="1.2" />
          <rect x="9.5" y="14.5" width="5" height="5" rx="1.2" />
          <path d="M8.5 7h7" />
          <path d="M12 9.5v5" />
        </SvgIcon>
      );
    case "activity":
      return (
        <SvgIcon>
          <path d="M3 12h4l2.2-5 4.2 10 2.2-5H21" />
        </SvgIcon>
      );
    case "settings":
      return (
        <SvgIcon>
          <circle cx="12" cy="12" r="3" />
          <path d="M19.4 15a1 1 0 0 0 .2 1.1l.1.1a1.9 1.9 0 1 1-2.7 2.7l-.1-.1a1 1 0 0 0-1.1-.2 1 1 0 0 0-.6.9V20a1.9 1.9 0 1 1-3.8 0v-.2a1 1 0 0 0-.6-.9 1 1 0 0 0-1.1.2l-.1.1a1.9 1.9 0 1 1-2.7-2.7l.1-.1a1 1 0 0 0 .2-1.1 1 1 0 0 0-.9-.6H4a1.9 1.9 0 1 1 0-3.8h.2a1 1 0 0 0 .9-.6 1 1 0 0 0-.2-1.1l-.1-.1a1.9 1.9 0 1 1 2.7-2.7l.1.1a1 1 0 0 0 1.1.2 1 1 0 0 0 .6-.9V4a1.9 1.9 0 1 1 3.8 0v.2a1 1 0 0 0 .6.9 1 1 0 0 0 1.1-.2l.1-.1a1.9 1.9 0 1 1 2.7 2.7l-.1.1a1 1 0 0 0-.2 1.1 1 1 0 0 0 .9.6h.2a1.9 1.9 0 1 1 0 3.8h-.2a1 1 0 0 0-.9.6Z" />
        </SvgIcon>
      );
    case "logout":
      return (
        <SvgIcon>
          <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" />
          <path d="M16 17l5-5-5-5" />
          <path d="M21 12H9" />
        </SvgIcon>
      );
    default:
      return null;
  }
}

function Label({ text }) {
  return (
    <div
      style={{
        fontSize: 11,
        fontWeight: 600,
        color: C.textMuted,
        marginBottom: 5,
        textTransform: "uppercase",
        letterSpacing: "0.05em"
      }}
    >
      {text}
    </div>
  );
}

function InputField({ label, placeholder, value, onChange, type = "text" }) {
  return (
    <div style={{ marginBottom: 10 }}>
      {label ? <Label text={label} /> : null}
      <input
        type={type}
        value={value}
        onChange={onChange}
        placeholder={placeholder}
        style={{
          width: "100%",
          padding: "9px 12px",
          borderRadius: 10,
          border: `1.5px solid ${C.border}`,
          background: C.cardInner,
          color: C.text,
          fontSize: 13,
          outline: "none",
          boxSizing: "border-box",
          ...FONT
        }}
      />
    </div>
  );
}

function DropField({ label, placeholder, value, onChange, options = [] }) {
  return (
    <div style={{ marginBottom: 10 }}>
      {label ? <Label text={label} /> : null}
      <div
        style={{
          padding: "9px 12px",
          borderRadius: 10,
          border: `1.5px solid ${C.border}`,
          background: C.cardInner,
          color: C.textMuted,
          fontSize: 13,
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          cursor: "pointer"
        }}
      >
        {options.length ? (
          <select
            value={value}
            onChange={onChange}
            style={{
              flex: 1,
              border: "none",
              background: "none",
              color: C.text,
              fontSize: 13,
              outline: "none",
              appearance: "none",
              ...FONT
            }}
          >
            {options.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        ) : (
          <input
            value={value}
            onChange={onChange}
            placeholder={placeholder}
            style={{
              flex: 1,
              border: "none",
              background: "none",
              color: C.text,
              fontSize: 13,
              outline: "none",
              minWidth: 0,
              ...FONT
            }}
          />
        )}
        <span style={{ color: C.textDim, flexShrink: 0 }}>v</span>
      </div>
    </div>
  );
}

function Card({ children, style }) {
  return (
    <div
      style={{
        padding: 14,
        borderRadius: 12,
        background: C.bgDeep,
        border: `1px solid ${C.border}`,
        ...style
      }}
    >
      {children}
    </div>
  );
}

function PanelHeader({ title, description, badge, actionLabel, onAction, actionDisabled = false }) {
  return (
    <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", gap: 12, marginBottom: 12 }}>
      <div style={{ minWidth: 0 }}>
        <div style={{ fontSize: 11, fontWeight: 700, color: C.textDim, textTransform: "uppercase", letterSpacing: "0.08em", marginBottom: 4 }}>
          {title}
        </div>
        <div style={{ fontSize: 13, lineHeight: 1.65, color: C.textSub }}>{description}</div>
      </div>
      <div style={{ display: "flex", gap: 8, alignItems: "center", flexShrink: 0 }}>
        {badge ? <span style={statusStyle(badge)}>{badge}</span> : null}
        {actionLabel ? (
          <button
            type="button"
            onClick={onAction}
            disabled={actionDisabled || !onAction}
            style={{
              padding: "6px 10px",
              borderRadius: 8,
              border: `1px solid ${C.border}`,
              background: C.cardInner,
              color: actionDisabled || !onAction ? C.textDim : C.textMuted,
              fontSize: 12,
              cursor: actionDisabled || !onAction ? "not-allowed" : "pointer",
              flexShrink: 0,
              ...FONT
            }}
          >
            {actionLabel}
          </button>
        ) : null}
      </div>
    </div>
  );
}

function PanelStateCard({ title, description, tone = "inactive", actionLabel, onAction, disabled = false }) {
  const toneStyle =
    tone === "review"
      ? { background: "rgba(255,244,226,0.96)", borderColor: "rgba(176,120,32,0.18)", color: C.amber }
      : {
          background: "rgba(255,255,255,0.74)",
          borderColor: "rgba(90,65,35,0.10)",
          color: C.textMuted
        };

  return (
    <div
      style={{
        padding: 12,
        borderRadius: 12,
        border: `1px solid ${toneStyle.borderColor}`,
        background: toneStyle.background
      }}
    >
      <div style={{ display: "flex", justifyContent: "space-between", gap: 10, alignItems: "flex-start" }}>
        <div style={{ minWidth: 0 }}>
          <div style={{ fontSize: 12, fontWeight: 700, color: toneStyle.color, marginBottom: 4 }}>{title}</div>
          <div style={{ fontSize: 12, lineHeight: 1.6, color: C.textMuted }}>{description}</div>
        </div>
        {actionLabel ? (
          <button
            type="button"
            disabled={disabled || !onAction}
            onClick={onAction}
            style={{
              padding: "6px 10px",
              borderRadius: 8,
              border: `1px solid ${C.border}`,
              background: C.cardInner,
              color: disabled ? C.textDim : C.textMuted,
              fontSize: 12,
              cursor: disabled || !onAction ? "not-allowed" : "pointer",
              flexShrink: 0,
              ...FONT
            }}
          >
            {actionLabel}
          </button>
        ) : null}
      </div>
    </div>
  );
}

function SectionTitle({ title, subtitle, actionLabel, onAction }) {
  return (
    <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: 10, marginBottom: 10 }}>
      <div>
        <div style={{ fontSize: 12, fontWeight: 700, color: C.textMuted, textTransform: "uppercase", letterSpacing: "0.05em" }}>{title}</div>
        {subtitle ? <div style={{ marginTop: 3, fontSize: 12, color: C.textDim }}>{subtitle}</div> : null}
      </div>
      {actionLabel ? (
        <button
          type="button"
          disabled={!onAction}
          onClick={onAction}
          style={{
            padding: "6px 10px",
            borderRadius: 8,
            border: `1px solid ${C.border}`,
            background: C.cardInner,
            color: onAction ? C.textMuted : C.textDim,
            fontSize: 12,
            cursor: onAction ? "pointer" : "not-allowed",
            opacity: onAction ? 1 : 0.72,
            flexShrink: 0,
            ...FONT
          }}
        >
          {actionLabel}
        </button>
      ) : null}
    </div>
  );
}

function EmptyPanelState({ title, description, actionLabel, onAction }) {
  return <PanelStateCard title={title} description={description} tone="review" actionLabel={actionLabel} onAction={onAction} />;
}

function LoadingPanelState({ title, description }) {
  return <PanelStateCard title={title} description={description} tone="inactive" />;
}

function InlineFeedback({ message, error = false }) {
  if (!message) {
    return null;
  }

  return (
    <div
      style={{
        padding: "8px 10px",
        borderRadius: 10,
        border: `1px solid ${error ? "rgba(176,88,80,0.22)" : "rgba(90,65,35,0.10)"}`,
        background: error ? "rgba(248,236,232,0.96)" : "rgba(255,255,255,0.72)",
        color: error ? C.accent : C.textMuted,
        fontSize: 12
      }}
    >
      {message}
    </div>
  );
}

function FloatingWindow({ id, onClose, onFocus, zIndex, children }) {
  const meta = WIN_META[id] || { title: safeString(id, "Panel"), width: 640, ix: 240, iy: 80 };
  const { pos, handleDown } = useWindowDrag(meta.ix, meta.iy);

  return (
    <div
      onMouseDown={onFocus}
      style={{
        position: "fixed",
        left: pos.x,
        top: pos.y,
        width: meta.width,
        maxWidth: "calc(100vw - 24px)",
        zIndex,
        background: C.card,
        border: `1.5px solid ${C.borderMid}`,
        borderRadius: 18,
        boxShadow: "0 8px 40px rgba(90,65,35,0.14), 0 2px 8px rgba(90,65,35,0.06)",
        maxHeight: "82vh",
        display: "flex",
        flexDirection: "column",
        overflow: "hidden",
        ...FONT
      }}
    >
      <div
        onMouseDown={handleDown}
        style={{
          cursor: "grab",
          padding: "11px 16px",
          borderBottom: `1px solid ${C.border}`,
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          background: C.bgDeep,
          borderRadius: "16px 16px 0 0",
          userSelect: "none"
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <span style={{ color: C.textDim, fontSize: 13 }}>::</span>
          <span style={{ fontSize: 14, fontWeight: 600, color: C.text }}>{meta.title}</span>
        </div>
        <button
          type="button"
          onMouseDown={(event) => event.stopPropagation()}
          onClick={onClose}
          style={{
            width: 24,
            height: 24,
            borderRadius: 8,
            border: `1px solid ${C.border}`,
            background: "transparent",
            cursor: "pointer",
            color: C.textMuted,
            display: "flex",
            alignItems: "center",
            justifyContent: "center"
          }}
        >
          x
        </button>
      </div>
      <div style={{ flex: 1, overflowY: "auto", padding: 18, scrollbarWidth: "thin" }}>{children}</div>
    </div>
  );
}

function AgentAvatar({ agent, size = 42 }) {
  const avatarType = safeString(agent?.avatar_type || agent?.avatarType || "", "").toLowerCase();
  const avatarValue = safeString(
    agent?.avatar_value || agent?.avatarValue || agent?.avatar_url || agent?.avatarUrl || agent?.avatar_content_url || agent?.avatarContentUrl,
    ""
  );
  const [blobUrl, setBlobUrl] = useState("");
  const [loadFailed, setLoadFailed] = useState(false);

  useEffect(() => {
    let cancelled = false;
    let objectUrl = "";

    setLoadFailed(false);
    setBlobUrl("");

    const wantsUploadedAvatar = avatarType === "uploaded_image" || avatarType === "uploaded_animation" || avatarType === "uploaded";
    if (!wantsUploadedAvatar || !agent?.id) {
      return undefined;
    }

    fetchAgentAvatarBlob(agent.id)
      .then((blob) => {
        if (cancelled || !blob) {
          return;
        }

        objectUrl = URL.createObjectURL(blob);
        setBlobUrl(objectUrl);
      })
      .catch(() => {
        if (!cancelled) {
          setLoadFailed(true);
        }
      });

    return () => {
      cancelled = true;
      if (objectUrl) {
        URL.revokeObjectURL(objectUrl);
      }
    };
  }, [agent?.id, avatarType]);

  const initials = getAgentInitials(agent?.name || "AI");
  const isRemoteAvatar = (avatarType === "image_url" || avatarType === "animation_url") && /^https?:\/\//i.test(avatarValue);
  const imageSrc = blobUrl || (isRemoteAvatar ? avatarValue : "");
  const emojiAvatar = avatarType === "emoji" && avatarValue ? avatarValue : "";

  return (
    <div
      aria-hidden="true"
      style={{
        width: size,
        height: size,
        borderRadius: 12,
        border: `1px solid ${C.borderMid}`,
        background: C.accentLight,
        overflow: "hidden",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        flexShrink: 0,
        color: C.accent,
        fontSize: Math.max(14, Math.round(size * 0.38)),
        fontWeight: 700
      }}
    >
      {emojiAvatar ? (
        <span style={{ lineHeight: 1 }}>{emojiAvatar}</span>
      ) : imageSrc && !loadFailed ? (
        <img
          src={imageSrc}
          alt=""
          referrerPolicy="no-referrer"
          onError={() => setLoadFailed(true)}
          style={{
            width: "100%",
            height: "100%",
            objectFit: "cover",
            display: "block"
          }}
        />
      ) : (
        <span>{initials}</span>
      )}
    </div>
  );
}

function CreateAgentContent({ onCreateAgent, isSubmitting = false, error = "", defaultProviderId = "", modelProviders = [] }) {
  const [name, setName] = useState("Doc Converter");
  const [skill, setSkill] = useState("convert pdf");
  const [model, setModel] = useState("gpt-4o");
  const [pinned, setPinned] = useState(false);
  const [message, setMessage] = useState("");
  const canCreate = Boolean(onCreateAgent) && !isSubmitting;

  const modelOptions = useMemo(
    () =>
      modelProviders.length
        ? modelProviders.map((item) => ({
            value: item?.id || item?.provider || item?.name || "openai",
            label: item?.name || item?.label || item?.id || item?.provider || "OpenAI"
          }))
        : [
            { value: "openai", label: "OpenAI" },
            { value: "openrouter", label: "OpenRouter" }
          ],
    [modelProviders]
  );

  useEffect(() => {
    if (!model && modelOptions.length) {
      setModel(modelOptions[0].value);
    }
  }, [model, modelOptions]);

  async function handleCreate() {
    if (!onCreateAgent) {
      setMessage("Create agent backend endpoint not available yet.");
      return;
    }

    const trimmedName = name.trim();
    if (!trimmedName) {
      setMessage("Agent name wajib.");
      return;
    }

    setMessage("");
    try {
      await onCreateAgent({
        name: trimmedName,
        skill,
        model,
        defaultProviderId,
        pinned
      });
      setMessage("Agent saved.");
    } catch (createError) {
      setMessage(createError?.message || "Create agent gagal.");
    }
  }

  return (
    <div style={{ display: "flex", gap: 18 }}>
      <div style={{ flex: 1, minWidth: 0 }}>
        <InputField label="Agent Name" placeholder="e.g. Doc Converter" value={name} onChange={(event) => setName(event.target.value)} />
        <div style={{ marginBottom: 10 }}>
          <Label text="Icon" />
          <div
            style={{
              padding: "9px 12px",
              borderRadius: 10,
              border: `1.5px dashed ${C.borderMid}`,
              background: C.cardInner,
              color: C.textMuted,
              fontSize: 12,
              display: "flex",
              alignItems: "center",
              gap: 8,
              cursor: "pointer"
            }}
          >
            <span style={{ color: C.textDim }}>^</span>
            import icon - PNG, JPG, WebP, GIF
          </div>
        </div>
        <DropField label="Skills" placeholder="search or type skill name..." value={skill} onChange={(event) => setSkill(event.target.value)} />
        <DropField
          label="Brain / Model"
          placeholder="select AI model..."
          value={model}
          onChange={(event) => setModel(event.target.value)}
          options={modelOptions}
        />
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginTop: 14 }}>
          <button
            type="button"
            onClick={() => setPinned((value) => !value)}
            style={{
              display: "flex",
              alignItems: "center",
              gap: 8,
              background: "none",
              border: "none",
              cursor: "pointer",
              color: C.textMuted,
              fontSize: 13,
              ...FONT
            }}
          >
            <div
              style={{
                width: 16,
                height: 16,
                borderRadius: 5,
                border: `1.5px solid ${pinned ? C.accent : C.textDim}`,
                background: pinned ? C.accentLight : "transparent",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                color: C.accent,
                fontSize: 10
              }}
            >
              {pinned ? "v" : ""}
            </div>
            pin agent
          </button>
          <button
            type="button"
            onClick={handleCreate}
            disabled={!canCreate}
            style={{
              padding: "8px 22px",
              borderRadius: 10,
              border: "none",
              background: C.accent,
              color: "#fff",
              fontSize: 13,
              fontWeight: 600,
              cursor: canCreate ? "pointer" : "not-allowed",
              opacity: canCreate ? 1 : 0.72,
              ...FONT
            }}
            title={canCreate ? "Create agent." : "Create agent backend endpoint not available yet."}
          >
            {isSubmitting ? "Saving..." : "Create"}
          </button>
        </div>
        <div style={{ marginTop: 10, display: "grid", gap: 8 }}>
          <InlineFeedback message={error} error />
          <InlineFeedback message={message} />
        </div>
      </div>

      <div style={{ width: 148, flexShrink: 0 }}>
        <Label text="Preview Agent" />
        <Card style={{ display: "flex", flexDirection: "column", gap: 8 }}>
          <div
            style={{
              width: 40,
              height: 40,
              borderRadius: 12,
              background: C.accentLight,
              border: `1px solid ${C.borderMid}`,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              fontSize: 14,
              fontWeight: 700,
              color: C.accent
            }}
          >
            {getAgentInitials(name)}
          </div>
          <div style={{ fontSize: 13, fontWeight: 600, color: C.text }}>{name || "nama agent"}</div>
          <div style={{ fontSize: 11, color: C.textMuted }}>icon</div>
          {[skill || "skill 2", model || "brain / model"].map((text) => (
            <div
              key={text}
              style={{
                padding: "6px 9px",
                borderRadius: 8,
                background: C.card,
                border: `1px solid ${C.border}`,
                fontSize: 11,
                color: C.textMuted
              }}
            >
              {text}
            </div>
          ))}
          <div style={{ display: "flex", gap: 6 }}>
            <span style={statusStyle("need setup")}>need setup</span>
            <span style={statusStyle(pinned ? "ready" : "preview only")}>{pinned ? "ready" : "preview only"}</span>
          </div>
        </Card>
      </div>
    </div>
  );
}

function ImportSkillContent({
  onPreviewImport,
  onPreviewCollection,
  onImportSkill,
  onApproveImport,
  onRejectImport,
  onDisableImport,
  isSubmitting = false,
  error = ""
}) {
  const [repository, setRepository] = useState("https://github.com/private/pdf-helper");
  const [branch, setBranch] = useState("main");
  const [filePath, setFilePath] = useState("skills/pdf/SKILL.md");
  const [folderPath, setFolderPath] = useState("skills/pdf");
  const [previewFilePath, setPreviewFilePath] = useState("skills/pdf/SKILL.md");
  const [previewFolderPath, setPreviewFolderPath] = useState("skills/pdf");
  const [previewResult, setPreviewResult] = useState(null);
  const [collectionPreview, setCollectionPreview] = useState(null);
  const [selectedSkillPath, setSelectedSkillPath] = useState("skills/pdf/SKILL.md");
  const [message, setMessage] = useState("");
  const [technicalMessage, setTechnicalMessage] = useState("");
  const [searchText, setSearchText] = useState("");
  const [activeFilter, setActiveFilter] = useState("all");
  const [previewTab, setPreviewTab] = useState("summary");
  const [importedSkillRecord, setImportedSkillRecord] = useState(null);

  const collectionCandidates = useMemo(
    () => normalizeArrayResponse(collectionPreview, ["candidates"]),
    [collectionPreview],
  );
  const filePreviewCandidates = useMemo(() => {
    if (!previewResult) {
      return [];
    }

    const previewPath = safeString(previewFilePath || filePath, "");
    if (!previewPath) {
      return [];
    }

    const validationStatus = Array.isArray(previewResult?.inspection_errors) && previewResult.inspection_errors.length
      ? "blocked"
      : Array.isArray(previewResult?.inspection_warnings) && previewResult.inspection_warnings.length
        ? "warning"
        : previewResult?.requires_review
          ? "warning"
          : "safe";

    return [
      {
        path: previewPath,
        manifest_path: previewPath,
        title: safeString(previewResult?.skill_import_type || previewResult?.file_path || previewPath, "Selected skill"),
        description: safeString(previewResult?.content_preview || previewResult?.review_notes || "", ""),
        skill_import_type: safeString(previewResult?.skill_import_type || "skill import", "skill import"),
        validation_status: validationStatus,
        warning: safeString(previewResult?.inspection_errors?.[0] || previewResult?.inspection_warnings?.[0] || previewResult?.review_notes || "", ""),
        status: safeString(previewResult?.status, "preview"),
        content_preview: safeString(previewResult?.content_preview || "", ""),
        inspection_warnings: Array.isArray(previewResult?.inspection_warnings) ? previewResult.inspection_warnings : [],
        inspection_errors: Array.isArray(previewResult?.inspection_errors) ? previewResult.inspection_errors : []
      }
    ];
  }, [filePath, previewFilePath, previewResult]);
  const candidateSource = useMemo(() => (collectionCandidates.length ? collectionCandidates : filePreviewCandidates), [collectionCandidates, filePreviewCandidates]);
  const importedSkillPath = safeString(importedSkillRecord?.file_path || importedSkillRecord?.skill_path || importedSkillRecord?.path || "", "");
  const candidateEntries = useMemo(
    () => candidateSource.map((candidate) => getGitHubImportCandidateView(candidate, selectedSkillPath, importedSkillPath)),
    [candidateSource, importedSkillPath, selectedSkillPath]
  );
  const selectedCollectionCandidate = candidateEntries.find((item) => item.selected) || candidateEntries[0] || null;
  const selectedImportedSkill = useMemo(() => {
    if (!importedSkillRecord?.id || !selectedCollectionCandidate) {
      return null;
    }

    if (!importedSkillPath) {
      return importedSkillRecord;
    }

    if (selectedCollectionCandidate.path === importedSkillPath || selectedCollectionCandidate.manifestPath === importedSkillPath) {
      return importedSkillRecord;
    }

    return null;
  }, [importedSkillPath, importedSkillRecord, selectedCollectionCandidate]);
  const candidateSummary = useMemo(
    () =>
      candidateEntries.reduce(
        (acc, item) => {
          acc.found += 1;
          if (item.validationStatus === "safe") acc.safe += 1;
          if (item.validationStatus === "blocked") acc.blocked += 1;
          if (item.validationStatus === "warning") acc.warning += 1;
          if (item.imported) acc.imported += 1;
          return acc;
        },
        { found: 0, safe: 0, blocked: 0, warning: 0, imported: 0 }
      ),
    [candidateEntries]
  );
  const filteredCandidates = useMemo(() => {
    const query = searchText.trim().toLowerCase();

    return candidateEntries.filter((item) => {
      const matchesQuery = !query || item.searchText.includes(query);
      const matchesFilter =
        activeFilter === "all"
          ? true
          : activeFilter === "selected"
            ? item.selected
            : activeFilter === "safe"
              ? item.validationStatus === "safe"
              : activeFilter === "blocked"
                ? item.validationStatus === "blocked"
                : activeFilter === "warning"
                  ? item.validationStatus === "warning"
                  : activeFilter === "imported"
                    ? item.imported
                    : true;
      return matchesQuery && matchesFilter;
    });
  }, [activeFilter, candidateEntries, searchText]);
  const selectedCandidateStatus = selectedCollectionCandidate?.statusMeta?.label || "Select a skill first";
  const importActionLabel = !selectedCollectionCandidate
    ? "Select a skill first"
    : selectedCollectionCandidate.imported
      ? "Already in Library"
      : selectedCollectionCandidate.validationStatus === "blocked" || selectedCollectionCandidate.validationStatus === "warning"
        ? "Import for Review"
        : "Import to Library";
  const canPreviewImport = Boolean(onPreviewImport);
  const canPreviewCollection = Boolean(onPreviewCollection);
  const canImportSkill = Boolean(onImportSkill) && !isSubmitting && Boolean(selectedCollectionCandidate?.path || selectedCollectionCandidate?.manifestPath) && !selectedCollectionCandidate?.imported;
  const canApproveImport = Boolean(onApproveImport) && Boolean(selectedImportedSkill?.id);
  const canRejectImport = Boolean(onRejectImport) && Boolean(selectedImportedSkill?.id);
  const canDisableImport = Boolean(onDisableImport) && Boolean(selectedImportedSkill?.id);

  useEffect(() => {
    if (!selectedSkillPath && filePath) {
      setSelectedSkillPath(filePath);
    }
  }, [filePath, selectedSkillPath]);

  useEffect(() => {
    if (!candidateSource.length) {
      return;
    }

    const hasSelectedCandidate = candidateSource.some((item) => {
      const candidatePath = String(item?.path || "").trim();
      const manifestPath = String(item?.manifest_path || "").trim();
      return candidatePath === selectedSkillPath || manifestPath === selectedSkillPath;
    });

    if (!hasSelectedCandidate) {
      const firstCandidate = candidateSource[0];
      setSelectedSkillPath(String(firstCandidate?.path || firstCandidate?.manifest_path || filePath || "").trim());
    }
  }, [candidateSource, filePath, selectedSkillPath]);

  async function handlePreviewFile() {
    if (!onPreviewImport) {
      setMessage("Preview file endpoint not available yet.");
      return;
    }

    setMessage("");
    setTechnicalMessage("");
    setPreviewTab("summary");
    setPreviewFilePath(filePath);
    setSelectedSkillPath(filePath);
    setCollectionPreview(null);
    try {
      const result = await onPreviewImport({
        repo_url: repository,
        branch,
        file_path: filePath
      });
      setPreviewResult(result || null);
      setMessage(result ? "Preview siap." : "Preview kosong.");
    } catch (previewError) {
      setMessage(previewError?.message || "Preview gagal.");
    }
  }

  async function handlePreviewCollection() {
    if (!onPreviewCollection) {
      setMessage("Collection preview endpoint not available yet.");
      return;
    }

    setMessage("");
    setTechnicalMessage("");
    setPreviewTab("summary");
    setPreviewFolderPath(folderPath);
    setPreviewResult(null);
    try {
      const result = await onPreviewCollection({
        repo_url: repository,
        branch
      });
      setCollectionPreview(result || null);
      const normalizedCandidates = normalizeArrayResponse(result, ["candidates"]);
      const firstCandidate = normalizedCandidates[0] || null;
      const nextSelectedPath = String(firstCandidate?.path || firstCandidate?.manifest_path || filePath || "").trim();
      if (nextSelectedPath) {
        setSelectedSkillPath(nextSelectedPath);
      }
      setMessage(result ? "Collection preview siap." : "Preview kosong.");
    } catch (previewError) {
      setMessage(previewError?.message || "Preview gagal.");
    }
  }

  async function handleImport() {
    if (!onImportSkill) {
      setMessage("Import endpoint not available yet.");
      return;
    }

    setMessage("");
    setTechnicalMessage("");
    setPreviewTab("summary");
    try {
      const skillPath = String(selectedCollectionCandidate?.path || selectedCollectionCandidate?.manifestPath || selectedSkillPath || previewFilePath || filePath || "").trim();
      const result = await onImportSkill({
        repo_url: repository,
        branch,
        skill_path: skillPath
      });
      setPreviewResult(result || null);
      setImportedSkillRecord(result || null);
      if (skillPath) {
        setSelectedSkillPath(skillPath);
      }
      setMessage("Skill imported to library for review.");
    } catch (importError) {
      const friendly = getGitHubImportFriendlyError(importError);
      setMessage(friendly.message || "Import gagal.");
      setTechnicalMessage(friendly.technical || "");
    }
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
      <Card style={{ display: "grid", gap: 12 }}>
        <div style={{ display: "grid", gap: 6 }}>
          <div style={{ fontSize: 18, fontWeight: 700, color: C.text }}>Import Skill</div>
          <div style={{ fontSize: 12, color: C.textMuted }}>Review skill candidates before adding them to your library.</div>
          <div style={{ fontSize: 11, color: C.textDim }}>Imported skills stay inactive until approved.</div>
        </div>
        {error ? <PanelStateCard title="Import data" description={error} tone="review" /> : null}

        <div style={{ display: "grid", gridTemplateColumns: "2fr 1fr 1fr 1fr", gap: 10 }}>
          <div style={{ padding: 12, borderRadius: 12, border: `1px solid ${C.border}`, background: C.bgDeep }}>
            <div style={{ fontSize: 11, color: C.textDim, textTransform: "uppercase", letterSpacing: "0.04em" }}>Candidates found</div>
            <div style={{ marginTop: 4, fontSize: 20, fontWeight: 700, color: C.text }}>{candidateSummary.found}</div>
          </div>
          <div style={{ padding: 12, borderRadius: 12, border: `1px solid ${C.border}`, background: C.bgDeep }}>
            <div style={{ fontSize: 11, color: C.textDim, textTransform: "uppercase", letterSpacing: "0.04em" }}>Safe</div>
            <div style={{ marginTop: 4, fontSize: 20, fontWeight: 700, color: C.green }}>{candidateSummary.safe}</div>
          </div>
          <div style={{ padding: 12, borderRadius: 12, border: `1px solid ${C.border}`, background: C.bgDeep }}>
            <div style={{ fontSize: 11, color: C.textDim, textTransform: "uppercase", letterSpacing: "0.04em" }}>Blocked</div>
            <div style={{ marginTop: 4, fontSize: 20, fontWeight: 700, color: C.accent }}>{candidateSummary.blocked}</div>
          </div>
          <div style={{ padding: 12, borderRadius: 12, border: `1px solid ${C.border}`, background: C.bgDeep }}>
            <div style={{ fontSize: 11, color: C.textDim, textTransform: "uppercase", letterSpacing: "0.04em" }}>Already imported</div>
            <div style={{ marginTop: 4, fontSize: 20, fontWeight: 700, color: C.textMuted }}>{candidateSummary.imported}</div>
          </div>
        </div>

        <div style={{ padding: 12, borderRadius: 12, border: `1px solid ${C.border}`, background: C.card }}>
          <SectionTitle title="Source / scan summary" subtitle="Repo, branch, file path, dan folder path." />
          <InputField label="Repository URL" placeholder="https://github.com/user/repo" value={repository} onChange={(event) => setRepository(event.target.value)} />
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 10, marginBottom: 10 }}>
            <InputField label="Branch" placeholder="main" value={branch} onChange={(event) => setBranch(event.target.value)} />
            <InputField label="File Path" placeholder="src/skill.py" value={filePath} onChange={(event) => setFilePath(event.target.value)} />
            <InputField label="Folder Path" placeholder="src/skills/" value={folderPath} onChange={(event) => setFolderPath(event.target.value)} />
          </div>
          <div style={{ display: "flex", gap: 10, marginBottom: 10 }}>
            {[
              { text: "Preview file", action: handlePreviewFile, disabled: !canPreviewImport },
              { text: "Preview collection", action: handlePreviewCollection, disabled: !canPreviewCollection }
            ].map((item) => (
              <button
                key={item.text}
                type="button"
                onClick={item.action}
                disabled={item.disabled}
                style={{
                  flex: 1,
                  padding: "8px 12px",
                  borderRadius: 10,
                  border: `1px solid ${C.border}`,
                  background: C.cardInner,
                  color: item.disabled ? C.textDim : C.textMuted,
                  fontSize: 12,
                  cursor: item.disabled ? "not-allowed" : "pointer",
                  opacity: item.disabled ? 0.72 : 1,
                  ...FONT
                }}
              >
                {item.text}
              </button>
            ))}
          </div>
          <div style={{ display: "grid", gridTemplateColumns: "1.6fr 1fr 1fr", gap: 8 }}>
            <div style={{ padding: "7px 10px", borderRadius: 8, background: C.bgDeep, border: `1px solid ${C.border}`, fontSize: 11, color: C.textMuted }}>
              selected candidate: {safeString(selectedCollectionCandidate?.title || selectedCollectionCandidate?.path, "No candidate selected")}
            </div>
            <div style={{ padding: "7px 10px", borderRadius: 8, background: C.bgDeep, border: `1px solid ${C.border}`, fontSize: 11, color: C.textMuted }}>
              status: {selectedCandidateStatus}
            </div>
            <div style={{ padding: "7px 10px", borderRadius: 8, background: C.bgDeep, border: `1px solid ${C.border}`, fontSize: 11, color: C.textMuted }}>
              class: {safeString(selectedCollectionCandidate?.skillType || selectedCollectionCandidate?.raw?.skill_import_type, "preview")}
            </div>
          </div>
        </div>

        <div style={{ padding: 12, borderRadius: 12, border: `1px solid ${C.border}`, background: C.card }}>
          <SectionTitle title="Candidate list" subtitle="Search, filter, lalu buka detail kandidat." />
          <div style={{ display: "grid", gap: 10, marginBottom: 12 }}>
            <div
              style={{
                display: "flex",
                alignItems: "center",
                gap: 8,
                padding: "8px 12px",
                borderRadius: 10,
                border: `1px solid ${C.border}`,
                background: C.cardInner
              }}
            >
              <span style={{ color: C.textDim }}>o</span>
              <input
                value={searchText}
                onChange={(event) => setSearchText(event.target.value)}
                placeholder="Search skill candidates..."
                style={{ background: "none", border: "none", outline: "none", width: "100%", fontSize: 13, color: C.text, ...FONT }}
              />
            </div>
            <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
              {[
                { key: "all", label: `All (${candidateEntries.length})` },
                { key: "safe", label: `Safe (${candidateSummary.safe})` },
                { key: "blocked", label: `Blocked (${candidateSummary.blocked})` },
                { key: "warning", label: `Warning (${candidateSummary.warning})` },
                { key: "imported", label: `Imported (${candidateSummary.imported})` },
                { key: "selected", label: "Selected" }
              ].map((tab) => {
                const active = activeFilter === tab.key;
                return (
                  <button
                    key={tab.key}
                    type="button"
                    onClick={() => setActiveFilter(tab.key)}
                    style={{
                      padding: "6px 10px",
                      borderRadius: 999,
                      border: `1px solid ${active ? C.accent : C.border}`,
                      background: active ? C.accentLight : C.cardInner,
                      color: active ? C.accent : C.textMuted,
                      fontSize: 12,
                      cursor: "pointer",
                      ...FONT
                    }}
                  >
                    {tab.label}
                  </button>
                );
              })}
            </div>
          </div>

          {filteredCandidates.length ? (
            <div style={{ display: "grid", gap: 8 }}>
              {filteredCandidates.map((candidate) => {
                const isSelected = candidate.selected;
                return (
                  <div
                    key={`${candidate.manifestPath || candidate.path || candidate.title}`}
                    style={{
                      padding: 12,
                      borderRadius: 12,
                      border: `1px solid ${isSelected ? C.accent : C.border}`,
                      background: isSelected ? "rgba(255,248,242,0.96)" : C.bgDeep,
                      boxShadow: isSelected ? "0 8px 18px rgba(154,74,31,0.08)" : "none"
                    }}
                  >
                    <div style={{ display: "flex", justifyContent: "space-between", gap: 10, alignItems: "flex-start" }}>
                      <div style={{ minWidth: 0, display: "grid", gap: 3 }}>
                        <div style={{ display: "flex", alignItems: "center", gap: 8, minWidth: 0 }}>
                          <div style={{ fontSize: 13, fontWeight: 700, color: C.text, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                            {candidate.title}
                          </div>
                          {isSelected ? <span style={statusStyle("ready")}>selected</span> : null}
                          {candidate.imported ? <span style={statusStyle("ready")}>Already in library</span> : null}
                        </div>
                        <div style={{ fontSize: 11, color: C.textMuted, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                          {candidate.path} · {candidate.manifestPath}
                        </div>
                      </div>
                      <span style={statusStyle(candidate.statusMeta.tone)}>{candidate.statusMeta.label}</span>
                    </div>
                    <div style={{ marginTop: 8, display: "flex", gap: 6, flexWrap: "wrap" }}>
                      <span style={statusStyle(candidate.skillType === "workflow_skill" ? "review" : candidate.skillType === "tool_skill" ? "blocked" : "ready")}>
                        {candidate.skillType}
                      </span>
                      {candidate.validationStatus === "blocked" ? <span style={statusStyle("blocked")}>{candidate.blockedSummary}</span> : null}
                      {candidate.validationStatus === "warning" ? <span style={statusStyle("review")}>{candidate.blockedSummary || "Review needed"}</span> : null}
                    </div>
                    <div style={{ marginTop: 8, display: "flex", justifyContent: "space-between", gap: 12, alignItems: "center" }}>
                      <div style={{ minWidth: 0, flex: 1, fontSize: 11, color: C.textDim, lineHeight: 1.5 }}>
                        {safeString(candidate.description, candidate.validationStatus === "blocked" ? "Blocked candidate." : "Preview candidate.")}
                      </div>
                      <button
                        type="button"
                        disabled={!candidate.path}
                        onClick={() => {
                          setSelectedSkillPath(candidate.path || filePath);
                          setMessage("");
                          setTechnicalMessage("");
                        }}
                        style={{
                          padding: "6px 10px",
                          borderRadius: 8,
                          border: `1px solid ${C.border}`,
                          background: C.cardInner,
                          color: candidate.path ? C.textMuted : C.textDim,
                          fontSize: 12,
                          cursor: candidate.path ? "pointer" : "not-allowed",
                          opacity: candidate.path ? 1 : 0.72,
                          ...FONT
                        }}
                      >
                        View details
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>
          ) : (
            <EmptyPanelState
              title="No matching skill candidates."
              description="Ubah search atau filter, lalu preview source lagi kalau perlu."
              actionLabel="Preview collection"
              onAction={handlePreviewCollection}
            />
          )}
        </div>

        <div style={{ padding: 12, borderRadius: 12, border: `1px solid ${C.border}`, background: C.card }}>
          <SectionTitle title="Selected Skill Review" subtitle="Nama, path, type, status, alasan blocked, lalu next action." />
          {!selectedCollectionCandidate ? (
            <div style={{ padding: 12, borderRadius: 12, border: `1px dashed ${C.border}`, background: C.bgDeep, color: C.textMuted, fontSize: 12 }}>
              Select a skill candidate to review details before importing.
            </div>
          ) : (
            <div style={{ display: "grid", gap: 10 }}>
              <div style={{ display: "flex", justifyContent: "space-between", gap: 12, alignItems: "flex-start" }}>
                <div style={{ minWidth: 0 }}>
                  <div style={{ fontSize: 15, fontWeight: 700, color: C.text }}>{selectedCollectionCandidate.title}</div>
                  <div style={{ marginTop: 3, fontSize: 11, color: C.textMuted }}>{selectedCollectionCandidate.path}</div>
                </div>
                <div style={{ display: "flex", gap: 6, flexWrap: "wrap", justifyContent: "flex-end" }}>
                  <span style={statusStyle(selectedCollectionCandidate.statusMeta.tone)}>{selectedCollectionCandidate.statusMeta.label}</span>
                  <span style={statusStyle(selectedCollectionCandidate.imported ? "ready" : selectedCollectionCandidate.validationStatus || "review")}>
                    {selectedCollectionCandidate.imported ? "Already in library" : safeString(selectedCollectionCandidate.validationStatus, "preview")}
                  </span>
                </div>
              </div>

              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8 }}>
                <div style={{ padding: 10, borderRadius: 10, border: `1px solid ${C.border}`, background: C.bgDeep }}>
                  <div style={{ fontSize: 10, fontWeight: 700, color: C.textDim, marginBottom: 4, textTransform: "uppercase", letterSpacing: "0.04em" }}>Skill type</div>
                  <div style={{ fontSize: 12, color: C.text }}>{selectedCollectionCandidate.skillType}</div>
                </div>
                <div style={{ padding: 10, borderRadius: 10, border: `1px solid ${C.border}`, background: C.bgDeep }}>
                  <div style={{ fontSize: 10, fontWeight: 700, color: C.textDim, marginBottom: 4, textTransform: "uppercase", letterSpacing: "0.04em" }}>Import state</div>
                  <div style={{ fontSize: 12, color: C.text }}>{selectedCollectionCandidate.imported ? "Already in library" : "Not imported yet"}</div>
                </div>
              </div>

              <div style={{ display: "grid", gap: 8 }}>
                <div style={{ padding: 10, borderRadius: 10, border: `1px solid ${C.border}`, background: C.bgDeep }}>
                  <div style={{ fontSize: 10, fontWeight: 700, color: C.textDim, marginBottom: 4, textTransform: "uppercase", letterSpacing: "0.04em" }}>Why blocked</div>
                  <div style={{ fontSize: 12, color: C.textMuted, lineHeight: 1.5 }}>
                    {selectedCollectionCandidate.validationStatus === "blocked"
                      ? selectedCollectionCandidate.blockedSummary
                      : selectedCollectionCandidate.validationStatus === "warning"
                        ? "Review needed before import."
                        : "Safe to import."}
                  </div>
                  {selectedCollectionCandidate.technicalDetail ? (
                    <div style={{ marginTop: 8, fontSize: 11, color: C.textDim }}>
                      Technical details: {selectedCollectionCandidate.technicalDetail}
                    </div>
                  ) : null}
                </div>

                <div style={{ padding: 10, borderRadius: 10, border: `1px solid ${C.border}`, background: C.bgDeep }}>
                  <div style={{ fontSize: 10, fontWeight: 700, color: C.textDim, marginBottom: 4, textTransform: "uppercase", letterSpacing: "0.04em" }}>Next action</div>
                  <div style={{ fontSize: 12, color: C.textMuted, lineHeight: 1.5 }}>
                    {selectedCollectionCandidate.imported
                      ? "Skill already in library. Open library or review approval state."
                      : selectedCollectionCandidate.validationStatus === "blocked"
                        ? "You can import for review, but blocked references must be cleaned before approval."
                        : selectedCollectionCandidate.validationStatus === "warning"
                          ? "You can import for review, then approve or reject after review."
                          : "You can import to library, then approve or reject after review."}
                  </div>
                </div>
              </div>

              <div style={{ display: "flex", justifyContent: "space-between", gap: 12, alignItems: "center", flexWrap: "wrap" }}>
              <div style={{ fontSize: 12, color: C.textMuted }}>
                  Selected candidate: {selectedCollectionCandidate.title} · {selectedCollectionCandidate.path}
                </div>
                <button
                  type="button"
                  disabled={!canImportSkill}
                  onClick={handleImport}
                  style={{
                    padding: "8px 16px",
                    borderRadius: 10,
                    border: "none",
                    background: selectedCollectionCandidate.imported ? C.textDim : C.accent,
                    color: "#fff",
                    fontSize: 12,
                    fontWeight: 600,
                    cursor: canImportSkill ? "pointer" : "not-allowed",
                    opacity: canImportSkill ? 1 : 0.72,
                    ...FONT
                  }}
                  title={canImportSkill ? "Import candidate to library." : "Import endpoint not available yet."}
                >
                  {isSubmitting ? "Importing..." : importActionLabel}
                </button>
              </div>
              {selectedCollectionCandidate.imported ? (
                <div style={{ fontSize: 11, color: C.textDim }}>
                  This skill already exists in your library.
                </div>
              ) : null}
            </div>
          )}
        </div>

        <div style={{ padding: 12, borderRadius: 12, border: `1px solid ${C.border}`, background: C.card }}>
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: 12, flexWrap: "wrap", marginBottom: 10 }}>
            <SectionTitle title="Skill Manifest Preview" subtitle="Summary default. Raw Manifest bounded and scrollable." />
            <div style={{ display: "flex", gap: 8 }}>
              {[
                { key: "summary", label: "Summary" },
                { key: "raw", label: "Raw Manifest" }
              ].map((tab) => {
                const active = previewTab === tab.key;
                return (
                  <button
                    key={tab.key}
                    type="button"
                    onClick={() => setPreviewTab(tab.key)}
                    style={{
                      padding: "6px 10px",
                      borderRadius: 999,
                      border: `1px solid ${active ? C.accent : C.border}`,
                      background: active ? C.accentLight : C.cardInner,
                      color: active ? C.accent : C.textMuted,
                      fontSize: 12,
                      cursor: "pointer",
                      ...FONT
                    }}
                  >
                    {tab.label}
                  </button>
                );
              })}
            </div>
          </div>

          {previewTab === "summary" ? (
            <div style={{ display: "grid", gap: 10 }}>
              <div style={{ display: "grid", gridTemplateColumns: "1.2fr 1fr 1fr", gap: 8 }}>
                <div style={{ padding: 10, borderRadius: 10, border: `1px solid ${C.border}`, background: C.bgDeep }}>
                  <div style={{ fontSize: 10, fontWeight: 700, color: C.textDim, marginBottom: 4, textTransform: "uppercase", letterSpacing: "0.04em" }}>Import type</div>
                  <div style={{ fontSize: 12, color: C.text }}>{safeString(previewResult?.import_type || selectedCollectionCandidate?.skillType, "skill")}</div>
                </div>
                <div style={{ padding: 10, borderRadius: 10, border: `1px solid ${C.border}`, background: C.bgDeep }}>
                  <div style={{ fontSize: 10, fontWeight: 700, color: C.textDim, marginBottom: 4, textTransform: "uppercase", letterSpacing: "0.04em" }}>File path</div>
                  <div style={{ fontSize: 12, color: C.text }}>{safeString(previewResult?.file_path || selectedCollectionCandidate?.path || previewFilePath, "preview")}</div>
                </div>
                <div style={{ padding: 10, borderRadius: 10, border: `1px solid ${C.border}`, background: C.bgDeep }}>
                  <div style={{ fontSize: 10, fontWeight: 700, color: C.textDim, marginBottom: 4, textTransform: "uppercase", letterSpacing: "0.04em" }}>Folder path</div>
                  <div style={{ fontSize: 12, color: C.text }}>{safeString(previewFolderPath || folderPath, "preview")}</div>
                </div>
              </div>

              <div style={{ padding: 12, borderRadius: 12, border: `1px solid ${C.border}`, background: C.bgDeep }}>
                <div style={{ fontSize: 10, fontWeight: 700, color: C.textDim, marginBottom: 6, textTransform: "uppercase", letterSpacing: "0.04em" }}>Summary</div>
                <div style={{ fontSize: 12, color: C.textMuted, lineHeight: 1.6 }}>
                  {previewResult?.content_preview
                    ? previewResult.content_preview
                    : "Review candidate list dulu. Manifest detail tampil di Raw Manifest tab."}
                </div>
                <div style={{ marginTop: 10, display: "flex", gap: 6, flexWrap: "wrap" }}>
                  <span style={statusStyle(previewResult?.status || "preview")}>{safeString(previewResult?.status, "preview")}</span>
                  {Array.isArray(previewResult?.inspection_warnings) && previewResult.inspection_warnings.length ? (
                    <span style={statusStyle("review")}>{previewResult.inspection_warnings.length} warning</span>
                  ) : null}
                  {Array.isArray(previewResult?.inspection_errors) && previewResult.inspection_errors.length ? (
                    <span style={statusStyle("blocked")}>{previewResult.inspection_errors.length} blocked</span>
                  ) : null}
                </div>
              </div>
            </div>
          ) : (
            <div
              style={{
                padding: 12,
                borderRadius: 12,
                border: `1px solid ${C.border}`,
                background: C.bgDeep,
                maxHeight: 240,
                overflowY: "auto"
              }}
            >
              <div style={{ fontSize: 10, fontWeight: 700, color: C.textDim, marginBottom: 8, textTransform: "uppercase", letterSpacing: "0.04em" }}>
                Skill Manifest Preview
              </div>
              <pre style={{ margin: 0, fontSize: 11, lineHeight: 1.6, color: C.textMuted, whiteSpace: "pre-wrap", wordBreak: "break-word", ...FONT }}>
                {safeString(previewResult?.content_preview || JSON.stringify(previewResult || selectedCollectionCandidate?.raw || {}, null, 2), "no clone / no install / no script execution")}
              </pre>
            </div>
          )}
        </div>

        {selectedImportedSkill?.id ? (
          <div style={{ padding: 12, borderRadius: 12, border: `1px solid ${C.border}`, background: C.card }}>
            <SectionTitle
              title="Imported Skill Review"
              subtitle="Approval makes reviewed skill available for agent attachment. Reject keeps it blocked. Disable turns off imported skill."
            />
            <div style={{ display: "grid", gridTemplateColumns: "1.2fr 1fr 1fr", gap: 8, marginBottom: 10 }}>
              <div style={{ padding: 10, borderRadius: 10, border: `1px solid ${C.border}`, background: C.bgDeep, fontSize: 11, color: C.textMuted }}>
                name: {safeString(selectedImportedSkill?.name || selectedImportedSkill?.skill_name || selectedCollectionCandidate?.title, "Imported skill")}
              </div>
              <div style={{ padding: 10, borderRadius: 10, border: `1px solid ${C.border}`, background: C.bgDeep, fontSize: 11, color: C.textMuted }}>
                status: {safeString(selectedImportedSkill?.status, "imported")}
              </div>
              <div style={{ padding: 10, borderRadius: 10, border: `1px solid ${C.border}`, background: C.bgDeep, fontSize: 11, color: C.textMuted }}>
                next: Review then approve / reject / disable
              </div>
            </div>
            <div style={{ marginBottom: 10, fontSize: 12, color: C.textMuted, lineHeight: 1.6 }}>
              Approval makes a reviewed skill available for agent attachment.
            </div>
            <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
              <button
                type="button"
                disabled={!canApproveImport}
                onClick={async () => {
                  try {
                    const next = await onApproveImport(selectedImportedSkill);
                    if (next) setImportedSkillRecord(next);
                    setPreviewResult(next || selectedImportedSkill);
                    setMessage("Imported skill approved.");
                    setTechnicalMessage("");
                  } catch (approveError) {
                    setMessage(approveError?.message || "Approve import gagal.");
                  }
                }}
                style={{
                  padding: "6px 10px",
                  borderRadius: 8,
                  border: `1px solid ${C.border}`,
                  background: C.cardInner,
                  color: canApproveImport ? C.textMuted : C.textDim,
                  fontSize: 12,
                  cursor: canApproveImport ? "pointer" : "not-allowed",
                  opacity: canApproveImport ? 1 : 0.72,
                  ...FONT
                }}
              >
                Approve imported skill
              </button>
              <button
                type="button"
                disabled={!canRejectImport}
                onClick={async () => {
                  try {
                    const next = await onRejectImport(selectedImportedSkill);
                    if (next) setImportedSkillRecord(next);
                    setPreviewResult(next || selectedImportedSkill);
                    setMessage("Imported skill rejected.");
                    setTechnicalMessage("");
                  } catch (rejectError) {
                    setMessage(rejectError?.message || "Reject import gagal.");
                  }
                }}
                style={{
                  padding: "6px 10px",
                  borderRadius: 8,
                  border: `1px solid ${C.border}`,
                  background: C.cardInner,
                  color: canRejectImport ? C.textMuted : C.textDim,
                  fontSize: 12,
                  cursor: canRejectImport ? "pointer" : "not-allowed",
                  opacity: canRejectImport ? 1 : 0.72,
                  ...FONT
                }}
              >
                Reject imported skill
              </button>
              <button
                type="button"
                disabled={!canDisableImport}
                onClick={async () => {
                  try {
                    const next = await onDisableImport(selectedImportedSkill);
                    if (next) setImportedSkillRecord(next);
                    setPreviewResult(next || selectedImportedSkill);
                    setMessage("Imported skill disabled.");
                    setTechnicalMessage("");
                  } catch (disableError) {
                    setMessage(disableError?.message || "Disable import gagal.");
                  }
                }}
                style={{
                  padding: "6px 10px",
                  borderRadius: 8,
                  border: `1px solid ${C.border}`,
                  background: C.cardInner,
                  color: canDisableImport ? C.textMuted : C.textDim,
                  fontSize: 12,
                  cursor: canDisableImport ? "pointer" : "not-allowed",
                  opacity: canDisableImport ? 1 : 0.72,
                  ...FONT
                }}
              >
                Disable imported skill
              </button>
            </div>
          </div>
        ) : null}

        <div style={{ display: "grid", gap: 8 }}>
          <InlineFeedback message={message} />
          {technicalMessage ? <InlineFeedback message={technicalMessage} /> : null}
          <InlineFeedback message={error} error />
        </div>
      </Card>
    </div>
  );
}

function LibraryTable({ rows, columns, onRowAction }) {
  const safeRows = Array.isArray(rows) ? rows : [];
  const safeColumns = Array.isArray(columns) ? columns : [];
  const normalizedColumns = safeColumns.map((column) => (typeof column === "string" ? { key: column, label: column } : column));
  const gridTemplateColumns = normalizedColumns.length >= 7 ? "2fr 1fr 1fr 1.5fr 1.8fr 1fr 1fr" : "2fr 1fr 1fr 1.5fr 1fr";

  return (
    <div>
      <div style={{ display: "flex", gap: 8, marginBottom: 14 }}>
        <div
          style={{
            flex: 1,
            display: "flex",
            alignItems: "center",
            gap: 6,
            padding: "7px 12px",
            borderRadius: 10,
            background: C.cardInner,
            border: `1.5px solid ${C.border}`
          }}
        >
          <span style={{ color: C.textDim }}>o</span>
          <input
            placeholder="search..."
            style={{ background: "none", border: "none", outline: "none", fontSize: 13, color: C.text, width: "100%", ...FONT }}
          />
        </div>
        {["Type", "Status"].map((text) => (
          <button
            key={text}
            type="button"
            style={{
              padding: "7px 14px",
              borderRadius: 10,
              border: `1.5px solid ${C.border}`,
              background: C.cardInner,
              color: C.textMuted,
              fontSize: 12,
              cursor: "pointer",
              display: "flex",
              alignItems: "center",
              gap: 5,
              ...FONT
            }}
          >
            {text} <span>v</span>
          </button>
        ))}
      </div>

      <div style={{ borderRadius: 12, border: `1px solid ${C.border}`, overflow: "hidden" }}>
        <div
          style={{
            display: "grid",
            gridTemplateColumns,
            padding: "8px 14px",
            background: C.bgDeep,
            borderBottom: `1px solid ${C.border}`
          }}
        >
          {normalizedColumns.map((column) => (
            <div key={column.key} style={{ fontSize: 11, fontWeight: 600, color: C.textMuted, textTransform: "uppercase", letterSpacing: "0.04em" }}>
              {column.label}
            </div>
          ))}
        </div>
        {safeRows.map((row, index) => (
          <div
            key={`${row.name}-${index}`}
            style={{
              display: "grid",
              gridTemplateColumns,
              padding: "10px 14px",
              borderBottom: index < safeRows.length - 1 ? `1px solid ${C.border}` : "none",
              background: index % 2 === 0 ? C.card : C.bgDeep,
              alignItems: "center"
            }}
          >
            {normalizedColumns.map((column) => {
              if (column.key === "action") {
                return (
                  <div key={column.key} style={{ display: "flex", gap: 5, flexWrap: "wrap" }}>
                    {(row.actions || [row.action || "View"]).map((action) => (
                    <button
                      key={action}
                      type="button"
                      disabled={action !== "View" && !row?.id}
                      onClick={() => onRowAction?.(action, row)}
                      style={{
                        fontSize: 11,
                        padding: "3px 8px",
                        borderRadius: 6,
                        border: `1px solid ${C.border}`,
                        background: "none",
                        color: action !== "View" && !row?.id ? C.textDim : C.textMuted,
                        cursor: action !== "View" && !row?.id ? "not-allowed" : "pointer",
                        opacity: action !== "View" && !row?.id ? 0.72 : 1,
                        ...FONT
                      }}
                    >
                        {action}
                      </button>
                    ))}
                  </div>
                );
              }

              const value = row[column.key];
              return (
                <div key={column.key} style={{ fontSize: 12, color: column.key === "name" ? C.text : C.textMuted, fontWeight: column.key === "name" ? 500 : 400 }}>
                  {column.render ? column.render(value, row) : value || "-"}
                </div>
              );
            })}
          </div>
        ))}
      </div>
    </div>
  );
}

function LibrarySkillContent({ rows = [], onRowAction }) {
  return (
    <LibraryTable
      rows={rows}
      columns={[
        { key: "name", label: "Nama Skill" },
        {
          key: "type",
          label: "Type",
          render: (_value, row) => (
            <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
              <span style={{ fontWeight: 600, color: C.text }}>{safeString(row.typeLabel, row.type)}</span>
              <span style={{ fontSize: 11, color: C.textDim }}>{safeString(row.typeDetail, "skill")}</span>
            </div>
          )
        },
        {
          key: "runtimeStatus",
          label: "Runtime",
          render: (value) => <span style={statusStyle(value)}>{value}</span>
        },
        {
          key: "status",
          label: "Status",
          render: (value, row) => (
            <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
              <span style={statusStyle(value)}>{value}</span>
              {row?.blockedReason ? <span style={{ fontSize: 11, color: C.textDim }}>{row.blockedReason}</span> : null}
            </div>
          )
        },
        { key: "agent", label: "Attach Agent" },
        { key: "sourceUrl", label: "Source URL" },
        { key: "lastUpdate", label: "Last Update" },
        { key: "action", label: "Action" }
      ]}
      onRowAction={onRowAction}
    />
  );
}

function LibraryWorkflowContent({ rows = [], onRowAction }) {
  return (
    <LibraryTable
      rows={rows}
      columns={[
        { key: "name", label: "Workflow Name" },
        { key: "type", label: "Trigger" },
        {
          key: "status",
          label: "Status",
          render: (value) => <span style={statusStyle(value)}>{value}</span>
        },
        { key: "agent", label: "Attach Agent" },
        { key: "source", label: "Source URL" },
        { key: "lastUpdate", label: "Last Update" },
        { key: "action", label: "Action" }
      ]}
      onRowAction={onRowAction}
    />
  );
}

function WorkflowN8nContent(props) {
  return <N8nPanel {...props} />;
}

function ActivityLogContent({ rows = [] }) {
  const [filter, setFilter] = useState("All");
  const [query, setQuery] = useState("");
  const [detail, setDetail] = useState(null);

  const safeRows = Array.isArray(rows) ? rows : [];
  const filteredRows = safeRows.filter((row) => {
    const haystack = `${row.title} ${row.desc} ${row.status} ${row.actor}`.toLowerCase();
    const matchesFilter = filter === "All" || haystack.includes(filter.toLowerCase());
    const matchesQuery = !query.trim() || haystack.includes(query.trim().toLowerCase());
    return matchesFilter && matchesQuery;
  });

  return (
    <div>
      <div style={{ display: "flex", gap: 8, marginBottom: 14 }}>
        <div
          style={{
            flex: 1,
            display: "flex",
            alignItems: "center",
            gap: 6,
            padding: "7px 12px",
            borderRadius: 10,
            background: C.cardInner,
            border: `1.5px solid ${C.border}`
          }}
        >
          <span style={{ color: C.textDim }}>o</span>
          <input
            placeholder="search activity..."
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            style={{ background: "none", border: "none", outline: "none", fontSize: 13, color: C.text, width: "100%", ...FONT }}
          />
        </div>
        {["All", "Agent", "Skill", "Workflow", "Approval", "Safety", "Settings"].map((value) => (
          <button
            key={value}
            type="button"
            onClick={() => setFilter(value)}
            style={{
              padding: "7px 14px",
              borderRadius: 10,
              border: `1.5px solid ${C.border}`,
              background: filter === value ? C.card : C.cardInner,
              color: C.textMuted,
              fontSize: 12,
              cursor: "pointer",
              ...FONT
            }}
          >
            {value}
          </button>
        ))}
      </div>
      <div style={{ fontSize: 11, fontWeight: 700, color: C.textMuted, marginBottom: 10, textTransform: "uppercase", letterSpacing: "0.05em" }}>
        Today
      </div>
      {filteredRows.length ? (
        <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
          {filteredRows.map((item) => (
            <Card key={`${item.time}-${item.title}`} style={{ background: C.card, padding: 12 }}>
              <div style={{ display: "flex", gap: 10 }}>
                <div style={{ width: 44, flexShrink: 0, fontSize: 12, color: C.textMuted }}>{item.time}</div>
                <div style={{ flex: 1 }}>
                  <div style={{ display: "flex", justifyContent: "space-between", gap: 10 }}>
                    <div>
                      <div style={{ fontSize: 13, fontWeight: 600, color: C.text }}>{item.title}</div>
                      <div style={{ fontSize: 12, color: C.textMuted, marginTop: 3 }}>{item.desc}</div>
                    </div>
                    <span style={statusStyle(item.tone)}>{item.status}</span>
                  </div>
                  <div style={{ marginTop: 9 }}>
                    <button
                      type="button"
                      onClick={() => setDetail(item)}
                      style={{
                        fontSize: 11,
                        padding: "4px 9px",
                        borderRadius: 7,
                        border: `1px solid ${C.border}`,
                        background: "none",
                        color: C.textMuted,
                        cursor: "pointer",
                        ...FONT
                      }}
                    >
                      View Detail
                    </button>
                  </div>
                </div>
              </div>
            </Card>
          ))}
        </div>
      ) : (
        <EmptyPanelState title="No activity log yet" description="Activity log kosong. Panel tetap read-only dan aman." />
      )}
      {detail ? (
        <div style={{ marginTop: 12, padding: 12, borderRadius: 12, border: `1px solid ${C.border}`, background: C.cardInner }}>
          <div style={{ fontSize: 11, color: C.textDim, textTransform: "uppercase", letterSpacing: "0.04em", marginBottom: 4 }}>Detail</div>
          <div style={{ fontSize: 13, fontWeight: 600, color: C.text }}>{detail.title}</div>
          <div style={{ marginTop: 4, fontSize: 12, color: C.textMuted }}>{detail.desc}</div>
        </div>
      ) : null}
    </div>
  );
}

function SettingsControlCenterContent({
  currentUser,
  providerSettings,
  apiKeyStatuses,
  modelProviders = [],
  runtimeCapabilities = [],
  activityRows = [],
  auditRows = [],
  taskRows = [],
  approvalRows = [],
  isLoading = false,
  workspaceLoaded = false,
  errors = {},
  onSaveSettings,
  onSaveApiKey,
  onDeleteApiKey,
  onRefresh,
  onApproveApproval,
  onRejectApproval,
  onOpenPanel
}) {
  const [activeTab, setActiveTab] = useState("account");
  const user = currentUser || {
    display_name: "nama user",
    username: "nama user",
    email: "user@email.com",
    subscription_plan: "free"
  };
  const safeModelProviders = Array.isArray(modelProviders) ? modelProviders : [];
  const safeRuntimeCapabilities = Array.isArray(runtimeCapabilities) ? runtimeCapabilities : [];
  const safeActivityRows = Array.isArray(activityRows) ? activityRows : [];
  const safeAuditRows = Array.isArray(auditRows) ? auditRows : [];
  const safeTaskRows = Array.isArray(taskRows) ? taskRows : [];
  const safeApprovalRows = Array.isArray(approvalRows) ? approvalRows : [];
  const planLabel = safeString(user.subscription_plan || user.plan || user.membership_plan || "free", "free");
  const userName = safeString(user.display_name || user.username || user.email, "nama user");
  const email = safeString(user.email, "-");
  const providerCount = safeModelProviders.length;
  const runtimeCount = safeRuntimeCapabilities.length;
  const keyCount = Array.isArray(apiKeyStatuses) ? apiKeyStatuses.length : 0;
  const activeTabConfig = SETTINGS_TABS.find((tab) => tab.id === activeTab) || SETTINGS_TABS[0];

  return (
    <div style={{ display: "grid", gap: 14 }}>
      <PanelHeader
        title="Settings Control Center"
        description="Panel admin ditaruh di sini. Board agent tetap layar utama."
        badge={planLabel}
        actionLabel="Refresh"
        onAction={onRefresh}
        actionDisabled={!onRefresh}
      />

      <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
        {SETTINGS_TABS.map((tab) => (
          <button
            key={tab.id}
            type="button"
            onClick={() => setActiveTab(tab.id)}
            style={{
              padding: "7px 12px",
              borderRadius: 10,
              border: `1px solid ${activeTab === tab.id ? C.accent : C.border}`,
              background: activeTab === tab.id ? C.accentLight : C.cardInner,
              color: activeTab === tab.id ? C.text : C.textMuted,
              fontSize: 12,
              cursor: "pointer",
              ...FONT
            }}
          >
            {tab.label}
          </button>
        ))}
      </div>

      <Card style={{ display: "grid", gap: 12, background: C.card }}>
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: 10 }}>
          <div>
            <div style={{ fontSize: 11, fontWeight: 700, color: C.textMuted, textTransform: "uppercase", letterSpacing: "0.06em" }}>
              {activeTabConfig.label}
            </div>
            <div style={{ marginTop: 4, fontSize: 13, color: C.textSub }}>
              Safe view only. No secret, no token, no execution.
            </div>
          </div>
          <span style={statusStyle("preview only")}>{isLoading ? "loading" : "read only"}</span>
        </div>

        {activeTab === "account" ? (
          <div style={{ display: "grid", gap: 10 }}>
            <div style={{ display: "grid", gap: 8, gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))" }}>
              <div style={{ padding: 12, borderRadius: 12, border: `1px solid ${C.border}`, background: C.bg }}>
                <div style={{ fontSize: 11, color: C.textMuted, textTransform: "uppercase", letterSpacing: "0.05em" }}>User</div>
                <div style={{ marginTop: 4, fontSize: 13, fontWeight: 600, color: C.text }}>{userName}</div>
              </div>
              <div style={{ padding: 12, borderRadius: 12, border: `1px solid ${C.border}`, background: C.bg }}>
                <div style={{ fontSize: 11, color: C.textMuted, textTransform: "uppercase", letterSpacing: "0.05em" }}>Email</div>
                <div style={{ marginTop: 4, fontSize: 13, fontWeight: 600, color: C.text }}>{email}</div>
              </div>
              <div style={{ padding: 12, borderRadius: 12, border: `1px solid ${C.border}`, background: C.bg }}>
                <div style={{ fontSize: 11, color: C.textMuted, textTransform: "uppercase", letterSpacing: "0.05em" }}>Plan</div>
                <div style={{ marginTop: 4, fontSize: 13, fontWeight: 600, color: C.text }}>{planLabel}</div>
              </div>
            </div>
            <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
              <span style={statusStyle("ready")}>{providerCount} providers</span>
              <span style={statusStyle("ready")}>{keyCount} api keys</span>
              <span style={statusStyle(runtimeCount ? "ready" : "review")}>{runtimeCount ? `${runtimeCount} runtime caps` : "runtime missing"}</span>
            </div>
            <PanelStateCard
              title="Account metadata only"
              description="Data account dibatasi ke info aman. Secret, token, dan key mentah tidak ditaruh di sini."
              tone="review"
              actionLabel="Open Provider / API Key"
              onAction={() => onOpenPanel?.("providers")}
            />
          </div>
        ) : null}

        {activeTab === "provider" ? (
          <ProviderApiKeyContent
            currentUser={user}
            providerSettings={providerSettings}
            apiKeyStatuses={apiKeyStatuses}
            modelProviders={safeModelProviders}
            onSaveSettings={onSaveSettings}
            onSaveApiKey={onSaveApiKey}
            onDeleteApiKey={onDeleteApiKey}
            errors={errors}
            onOpenPanel={onOpenPanel}
          />
        ) : null}

        {activeTab === "oauth" ? (
          <OAuthConnectionsContent
            modelProviders={safeModelProviders}
            apiKeyStatuses={apiKeyStatuses}
            runtimeCapabilities={safeRuntimeCapabilities}
            errors={errors}
            onOpenPanel={onOpenPanel}
          />
        ) : null}

        {activeTab === "safety" ? (
          <SafetyCenterContent
            runtimeCapabilities={safeRuntimeCapabilities}
            activityRows={safeActivityRows}
            auditRows={safeAuditRows}
            taskRows={safeTaskRows}
            approvalRows={safeApprovalRows}
            isLoading={isLoading}
            errors={errors}
            onRefresh={onRefresh}
            onApproveApproval={onApproveApproval}
            onRejectApproval={onRejectApproval}
            onOpenPanel={onOpenPanel}
          />
        ) : null}

        {activeTab === "activity" ? <ActivityLogContent rows={safeActivityRows} /> : null}

        {activeTab === "runtime" ? (
          <RuntimeCapabilityPanel
            capabilities={safeRuntimeCapabilities}
            loading={isLoading}
            error={errors.runtime || ""}
            emptyMessage="Capability belum muncul. Semua execution tetap blocked."
          />
        ) : null}

        {activeTab === "plan" ? (
          <div style={{ display: "grid", gap: 10 }}>
            <div style={{ display: "grid", gap: 8, gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))" }}>
              <div style={{ padding: 12, borderRadius: 12, border: `1px solid ${C.border}`, background: C.bg }}>
                <div style={{ fontSize: 11, color: C.textMuted, textTransform: "uppercase", letterSpacing: "0.05em" }}>Plan</div>
                <div style={{ marginTop: 4, fontSize: 13, fontWeight: 600, color: C.text }}>{planLabel}</div>
              </div>
              <div style={{ padding: 12, borderRadius: 12, border: `1px solid ${C.border}`, background: C.bg }}>
                <div style={{ fontSize: 11, color: C.textMuted, textTransform: "uppercase", letterSpacing: "0.05em" }}>Agents</div>
                <div style={{ marginTop: 4, fontSize: 13, fontWeight: 600, color: C.text }}>
                  {currentUser?.agent_quota ?? currentUser?.agent_limit ?? "n/a"}
                </div>
              </div>
              <div style={{ padding: 12, borderRadius: 12, border: `1px solid ${C.border}`, background: C.bg }}>
                <div style={{ fontSize: 11, color: C.textMuted, textTransform: "uppercase", letterSpacing: "0.05em" }}>Limits</div>
                <div style={{ marginTop: 4, fontSize: 13, fontWeight: 600, color: C.text }}>
                  {currentUser?.usage_limit ?? currentUser?.quota_status ?? "unavailable"}
                </div>
              </div>
            </div>
            <PanelStateCard
              title="Plan view"
              description="Kalau backend belum kirim kuota, status tampil unavailable. Tidak ada angka palsu."
              tone="review"
              actionLabel="Open account"
              onAction={() => setActiveTab("account")}
            />
          </div>
        ) : null}

        {activeTab === "system" ? (
          <div style={{ display: "grid", gap: 10 }}>
            <div style={{ display: "grid", gap: 8, gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))" }}>
              <div style={{ padding: 12, borderRadius: 12, border: `1px solid ${C.border}`, background: C.bg }}>
                <div style={{ fontSize: 11, color: C.textMuted, textTransform: "uppercase", letterSpacing: "0.05em" }}>Workspace</div>
                <div style={{ marginTop: 4, fontSize: 13, fontWeight: 600, color: C.text }}>{workspaceLoaded ? "loaded" : "loading"}</div>
              </div>
              <div style={{ padding: 12, borderRadius: 12, border: `1px solid ${C.border}`, background: C.bg }}>
                <div style={{ fontSize: 11, color: C.textMuted, textTransform: "uppercase", letterSpacing: "0.05em" }}>Activity rows</div>
                <div style={{ marginTop: 4, fontSize: 13, fontWeight: 600, color: C.text }}>{safeActivityRows.length}</div>
              </div>
              <div style={{ padding: 12, borderRadius: 12, border: `1px solid ${C.border}`, background: C.bg }}>
                <div style={{ fontSize: 11, color: C.textMuted, textTransform: "uppercase", letterSpacing: "0.05em" }}>Safety rows</div>
                <div style={{ marginTop: 4, fontSize: 13, fontWeight: 600, color: C.text }}>{safeAuditRows.length + safeTaskRows.length + safeApprovalRows.length}</div>
              </div>
            </div>
            <PanelStateCard
              title="System info"
              description="Tanpa endpoint baru. Hanya status yang sudah ada di workspace."
              tone="review"
              actionLabel="Open Safety Center"
              onAction={() => onOpenPanel?.("safety-center")}
            />
          </div>
        ) : null}
      </Card>
    </div>
  );
}

function SettingsContent({
  currentUser,
  providerSettings,
  apiKeyStatuses,
  modelProviders,
  onSaveSettings,
  onSaveApiKey,
  onDeleteApiKey,
  errors = {}
}) {
  const user = currentUser || {
    display_name: "nama user",
    username: "nama user",
    email: "user@email.com",
    subscription_plan: "free"
  };
  const providerOptions = [
    { value: "openai", label: "OpenAI" },
    { value: "anthropic", label: "Anthropic" },
    { value: "google_gemini", label: "Google Gemini" },
    { value: "openrouter", label: "OpenRouter" },
    { value: "ollama_local", label: "Ollama Local" },
    { value: "custom", label: "Custom" }
  ].map((item) => {
    const match = modelProviders.find((provider) => {
      const name = String(provider?.name || "").toLowerCase();
      const type = String(provider?.provider_type || "").toLowerCase();
      return type === item.value || name.includes(item.value.replace("_", " "));
    });

    return {
      value: item.value,
      label: match?.name || item.label
    };
  });
  const [preferredProvider, setPreferredProvider] = useState(providerSettings?.preferred_provider || providerOptions[0]?.value || "openai");
  const [preferredModel, setPreferredModel] = useState(providerSettings?.preferred_model || "gpt-4o");
  const [message, setMessage] = useState("");
  const [keyDrafts, setKeyDrafts] = useState({});
  const testConnectionLabel = "test connection not available yet";
  const testConnectionEnabled = false;
  const canSaveSettings = Boolean(onSaveSettings);

  useEffect(() => {
    setPreferredProvider(providerSettings?.preferred_provider || providerOptions[0]?.value || "openai");
    setPreferredModel(providerSettings?.preferred_model || "gpt-4o");
  }, [providerSettings?.preferred_provider, providerSettings?.preferred_model, providerOptions]);

  useEffect(() => {
    const next = {};
    (apiKeyStatuses.length ? apiKeyStatuses : SETTINGS_KEYS).forEach((item) => {
      next[item.provider] = "";
    });
    setKeyDrafts(next);
  }, [apiKeyStatuses]);

  async function handleSaveSettings() {
    if (!onSaveSettings) {
      setMessage("Save settings backend endpoint not available yet.");
      return;
    }

    setMessage("");
    try {
      await onSaveSettings({
        preferred_provider: preferredProvider,
        preferred_model: preferredModel
      });
      setMessage("Model setting saved.");
    } catch (saveError) {
      setMessage(saveError?.message || "Save settings gagal.");
    }
  }

  async function handleSaveKey(provider) {
    if (!onSaveApiKey) {
      setMessage("Save key backend endpoint not available yet.");
      return;
    }

    const apiKey = String(keyDrafts[provider] || "").trim();
    if (!apiKey) {
      setMessage("API key kosong.");
      return;
    }

    setMessage("");
    try {
      await onSaveApiKey(provider, apiKey);
      setKeyDrafts((current) => ({ ...current, [provider]: "" }));
      setMessage(`${provider} key saved.`);
    } catch (saveError) {
      setMessage(saveError?.message || "Save key gagal.");
    }
  }

  async function handleDeleteKey(provider) {
    if (!onDeleteApiKey) {
      setMessage("Delete key backend endpoint not available yet.");
      return;
    }

    setMessage("");
    try {
      await onDeleteApiKey(provider);
      setMessage(`${provider} key deleted.`);
    } catch (deleteError) {
      setMessage(deleteError?.message || "Delete key gagal.");
    }
  }

  const keyRows = apiKeyStatuses.length
    ? apiKeyStatuses.map((item, index) => ({
        id: item?.provider || `provider-${index + 1}`,
        provider: item?.provider || "-",
        masked: item?.masked_key || item?.key_last4 || item?.maskedKey || "not set",
        status: item?.connection_status || "not setup"
      }))
    : SETTINGS_KEYS.map((item) => ({
        id: item.provider,
        provider: item.provider,
        masked: item.masked,
        status: item.status
      }));

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
      <InlineFeedback message={errors.general} error />

      <Card style={{ background: C.card }}>
        <div style={{ fontSize: 12, fontWeight: 600, color: C.textMuted, marginBottom: 10, textTransform: "uppercase", letterSpacing: "0.05em" }}>
          Account / Profile
        </div>
        <div style={{ display: "grid", gap: 8 }}>
          <div style={{ padding: "8px 10px", borderRadius: 8, background: C.bgDeep, border: `1px solid ${C.border}`, fontSize: 12, color: C.textSub }}>
            Name: {user.display_name || user.username}
          </div>
          <div style={{ padding: "8px 10px", borderRadius: 8, background: C.bgDeep, border: `1px solid ${C.border}`, fontSize: 12, color: C.textSub }}>
            Email: {user.email || "user@email.com"}
          </div>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <div style={{ fontSize: 12, color: C.textMuted }}>Plan</div>
            <span style={statusStyle("ready")}>{String(user.subscription_plan || "FREE").toUpperCase()}</span>
          </div>
        </div>
      </Card>

      <Card style={{ background: C.card }}>
        <div style={{ fontSize: 12, fontWeight: 600, color: C.textMuted, marginBottom: 10, textTransform: "uppercase", letterSpacing: "0.05em" }}>
          Brain / Model
        </div>
        <div style={{ display: "grid", gap: 8 }}>
          <div style={{ padding: "8px 10px", borderRadius: 8, background: C.bgDeep, border: `1px solid ${C.border}` }}>
            <div style={{ fontSize: 11, color: C.textMuted, marginBottom: 4 }}>Default Provider</div>
            <select
              value={preferredProvider}
              onChange={(event) => setPreferredProvider(event.target.value)}
              style={{ width: "100%", background: "none", border: "none", outline: "none", fontSize: 12, color: C.textSub, ...FONT }}
            >
              {providerOptions.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </div>
          <div style={{ padding: "8px 10px", borderRadius: 8, background: C.bgDeep, border: `1px solid ${C.border}` }}>
            <div style={{ fontSize: 11, color: C.textMuted, marginBottom: 4 }}>Default Model</div>
            <input
              value={preferredModel}
              onChange={(event) => setPreferredModel(event.target.value)}
              style={{ width: "100%", background: "none", border: "none", outline: "none", fontSize: 12, color: C.textSub, ...FONT }}
            />
          </div>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <div style={{ fontSize: 12, color: C.textMuted }}>Status</div>
            <span style={statusStyle(preferredProvider ? "ready" : "need setup")}>{preferredProvider ? "ready" : "need setup"}</span>
          </div>
          <button
            type="button"
            onClick={handleSaveSettings}
            disabled={!canSaveSettings}
            style={{
              marginTop: 4,
              width: "100%",
              padding: "8px 12px",
              borderRadius: 10,
              border: `1px solid ${C.border}`,
              background: C.cardInner,
              color: canSaveSettings ? C.textMuted : C.textDim,
              fontSize: 12,
              cursor: canSaveSettings ? "pointer" : "not-allowed",
              opacity: canSaveSettings ? 1 : 0.72,
              ...FONT
            }}
            title={canSaveSettings ? "Save model settings." : "Save settings backend endpoint not available yet."}
          >
            Save Model Settings
          </button>
        </div>
      </Card>

      <Card style={{ background: C.card }}>
        <div style={{ fontSize: 12, fontWeight: 600, color: C.textMuted, marginBottom: 10, textTransform: "uppercase", letterSpacing: "0.05em" }}>
          API Key Vault
        </div>
        <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
          {keyRows.map((item) => (
            <div key={item.provider} style={{ padding: "9px 10px", borderRadius: 8, background: C.bgDeep, border: `1px solid ${C.border}` }}>
              <div style={{ display: "flex", justifyContent: "space-between", gap: 10 }}>
                <div>
                  <div style={{ fontSize: 12, fontWeight: 600, color: C.text }}>{item.provider}</div>
                  <div style={{ fontSize: 11, color: C.textMuted, marginTop: 2 }}>{item.masked}</div>
                </div>
                <span style={statusStyle(item.status)}>{item.status}</span>
              </div>
              <div style={{ marginTop: 8, display: "flex", gap: 8 }}>
                <input
                  type="password"
                  autoComplete="off"
                  spellCheck={false}
                  autoCorrect="off"
                  autoCapitalize="off"
                  value={keyDrafts[item.provider] || ""}
                  onChange={(event) => setKeyDrafts((current) => ({ ...current, [item.provider]: event.target.value }))}
                  placeholder="paste api key"
                  style={{
                    flex: 1,
                    padding: "7px 10px",
                    borderRadius: 8,
                    border: `1px solid ${C.border}`,
                    background: C.card,
                    fontSize: 12,
                    color: C.text,
                    ...FONT
                  }}
                />
                {(() => {
                  const draftKey = String(keyDrafts[item.provider] || "").trim();
                  const canSaveKey = Boolean(onSaveApiKey) && Boolean(draftKey);
                  const canDeleteKey = Boolean(onDeleteApiKey);

                  return (
                    <>
                      <button
                        type="button"
                        disabled={!canSaveKey}
                        onClick={() => handleSaveKey(item.provider)}
                        style={{
                          padding: "7px 10px",
                          borderRadius: 8,
                          border: `1px solid ${C.border}`,
                          background: C.cardInner,
                          color: canSaveKey ? C.textMuted : C.textDim,
                          fontSize: 12,
                          cursor: canSaveKey ? "pointer" : "not-allowed",
                          opacity: canSaveKey ? 1 : 0.72,
                          ...FONT
                        }}
                        title={canSaveKey ? "Save or update key." : "Need key input or backend save endpoint."}
                      >
                        Save / Update
                      </button>
                      <button
                        type="button"
                        disabled={!canDeleteKey}
                        onClick={() => handleDeleteKey(item.provider)}
                        style={{
                          padding: "7px 10px",
                          borderRadius: 8,
                          border: `1px solid ${C.border}`,
                          background: C.cardInner,
                          color: canDeleteKey ? C.textMuted : C.textDim,
                          fontSize: 12,
                          cursor: canDeleteKey ? "pointer" : "not-allowed",
                          opacity: canDeleteKey ? 1 : 0.72,
                          ...FONT
                        }}
                        title={canDeleteKey ? "Delete key." : "Delete key backend endpoint not available yet."}
                      >
                        Delete
                      </button>
                    </>
                  );
                })()}
              </div>
              <div style={{ marginTop: 6, fontSize: 11, lineHeight: 1.5, color: C.textMuted }}>
                Raw key cuma hidup di input sementara. Setelah save/update, field langsung dikosongkan.
              </div>
            </div>
          ))}
        </div>
      </Card>

      <Card style={{ background: C.card }}>
        <div style={{ fontSize: 12, fontWeight: 600, color: C.textMuted, marginBottom: 10, textTransform: "uppercase", letterSpacing: "0.05em" }}>
          Safety
        </div>
        <div style={{ display: "grid", gap: 8 }}>
          {[
            ["tool execution", "locked"],
            ["n8n execution", "locked"],
            ["runtime", "preview only"],
            ["workflow execution", "locked"],
            ["provider live test", "locked"]
          ].map(([label, value]) => (
            <div key={label} style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <div style={{ fontSize: 12, color: C.textMuted }}>{label}</div>
              <span style={statusStyle(value)}>{value}</span>
            </div>
          ))}
          <button
            type="button"
            disabled={!testConnectionEnabled}
            title="Backend belum sediakan test endpoint aman."
            style={{
              marginTop: 4,
              width: "100%",
              padding: "8px 12px",
              borderRadius: 10,
              border: `1px solid ${C.border}`,
              background: C.bgDeep,
              color: C.textMuted,
              fontSize: 12,
              cursor: "not-allowed",
              opacity: 0.72,
              ...FONT
            }}
          >
            {testConnectionLabel}
          </button>
        </div>
      </Card>
      <div style={{ display: "grid", gap: 8 }}>
        <InlineFeedback message={errors.apiKeyVault} error />
        <InlineFeedback message={message} />
      </div>
    </div>
  );
}

function SkillHubContent({ rows = [], selectedAgent, selectedAgentSkills = [], error = "", onOpenPanel }) {
  const libraryCount = rows.length;
  const activeCount = selectedAgentSkills.length;
  const activeSkillItems = Array.isArray(selectedAgentSkills) ? selectedAgentSkills : [];
  const typeCounts = rows.reduce((acc, row) => {
    const key = normalizeSkillType(row?.type || "prompt_skill");
    acc[key] = (acc[key] || 0) + 1;
    return acc;
  }, {
    prompt_skill: 0,
    knowledge_skill: 0,
    tool_skill: 0,
    workflow_skill: 0
  });
  const typeCards = [
    "prompt_skill",
    "knowledge_skill",
    "tool_skill",
    "workflow_skill"
  ].map((type) => {
    const meta = getSkillTypeMeta(type);
    const count = typeCounts[type] || 0;
    return { type, count, meta };
  });

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
      <PanelHeader
        title="Skill Hub"
        description="Panel ringkas untuk buka import, library, dan skill aktif tanpa pindah backend flow."
        badge={libraryCount ? "ready" : "preview only"}
      />

      {error ? <PanelStateCard title="Skill data" description={error} tone="review" /> : null}

      <Card style={{ background: C.card }}>
        <SectionTitle
          title="Quick Actions"
          subtitle="Buka panel detail kalau mau lihat import atau library."
        />
        <div style={{ display: "grid", gap: 8 }}>
          <PanelStateCard
            title="Import skill"
            description="Buka panel import GitHub skill. Preview dulu, baru approve."
            actionLabel="Open"
            onAction={() => onOpenPanel?.("import-skill")}
          />
          <PanelStateCard
            title="Library skill"
            description="Buka daftar skill library dan attach/detach yang sudah ada."
            actionLabel="Open"
            onAction={() => onOpenPanel?.("library-skill")}
          />
        </div>
      </Card>

      <Card style={{ background: C.card }}>
        <SectionTitle title="Skill Type Matrix" subtitle="Semua tipe skill harus kebaca jelas." />
        <div style={{ display: "grid", gridTemplateColumns: "repeat(4, minmax(0, 1fr))", gap: 8 }}>
          {typeCards.map((item) => (
            <div
              key={item.type}
              style={{
                padding: "10px 11px",
                borderRadius: 10,
                border: `1px solid ${C.border}`,
                background: item.meta.blocked ? "rgba(248,236,232,0.92)" : C.bgDeep
              }}
            >
              <div style={{ display: "flex", justifyContent: "space-between", gap: 8, alignItems: "flex-start" }}>
                <div>
                  <div style={{ fontSize: 12, fontWeight: 700, color: C.text }}>{item.meta.label}</div>
                  <div style={{ fontSize: 11, color: C.textMuted, marginTop: 2 }}>{item.meta.detail}</div>
                </div>
                <span style={statusStyle(item.meta.executionState)}>{item.meta.executionState}</span>
              </div>
              <div style={{ marginTop: 8, display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                <div style={{ fontSize: 16, fontWeight: 700, color: C.text }}>{item.count}</div>
                <span style={statusStyle(item.meta.blocked ? "blocked" : "safe")}>{item.meta.blocked ? "blocked" : "ready"}</span>
              </div>
            </div>
          ))}
        </div>
      </Card>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
        <Card style={{ background: C.card }}>
          <SectionTitle title="Library Snapshot" subtitle={`${libraryCount} item terlihat`} />
          {rows.length ? (
            <div style={{ display: "grid", gap: 8 }}>
              {rows.slice(0, 4).map((row) => (
                <div
                  key={row.id}
                  style={{
                    padding: "9px 10px",
                    borderRadius: 9,
                    background: C.bgDeep,
                    border: `1px solid ${C.border}`
                  }}
                >
                  <div style={{ display: "flex", justifyContent: "space-between", gap: 10, alignItems: "flex-start" }}>
                    <div>
                      <div style={{ fontSize: 12, fontWeight: 600, color: C.text }}>{row.name}</div>
                      <div style={{ fontSize: 11, color: C.textMuted, marginTop: 2 }}>
                        {row.agent || "-"} | {safeString(row.typeLabel || getSkillTypeMeta(row.type).label, "Prompt")}
                      </div>
                    </div>
                    <div style={{ display: "flex", flexDirection: "column", gap: 4, alignItems: "flex-end" }}>
                      <span style={statusStyle(row.status)}>{row.status}</span>
                      <span style={statusStyle(row.runtimeStatus || "preview only")}>{row.runtimeStatus || "preview only"}</span>
                    </div>
                  </div>
                  <div style={{ marginTop: 7, fontSize: 11, color: C.textDim }}>{safeString(row.sourceUrl, "-")}</div>
                </div>
              ))}
            </div>
          ) : (
            <EmptyPanelState
              title="Skill library kosong"
              description="Belum ada skill yang bisa ditampilkan. Buka import panel untuk menambah sumber."
              actionLabel="Open import"
              onAction={() => onOpenPanel?.("import-skill")}
            />
          )}
        </Card>

        <Card style={{ background: C.card }}>
          <SectionTitle title="Active skills" subtitle={selectedAgent ? `Agent ${selectedAgent.name}` : "Belum ada agent"} />
          {selectedAgent ? (
            <div style={{ display: "grid", gap: 8 }}>
              <PanelStateCard
                title={selectedAgent.name}
                description={`${activeCount} skill aktif di agent terpilih.`}
                actionLabel="Open active"
                onAction={() => onOpenPanel?.("active-skills")}
              />
              {activeSkillItems.slice(0, 3).map((item) => {
                const skill = item?.skill || {};
                const typeMeta = getSkillTypeMeta(skill?.skill_type || skill?.type);
                return (
                  <div
                    key={String(item?.id || skill?.id || skill?.name || `skill-${item?.created_at || "active"}`)}
                    style={{
                      padding: "9px 10px",
                      borderRadius: 9,
                      background: C.bgDeep,
                      border: `1px solid ${C.border}`
                    }}
                  >
                    <div style={{ display: "flex", justifyContent: "space-between", gap: 10 }}>
                      <div>
                        <div style={{ fontSize: 12, fontWeight: 600, color: C.text }}>{skill?.title || skill?.name || "Skill"}</div>
                        <div style={{ fontSize: 11, color: C.textMuted, marginTop: 2 }}>
                          {safeString(typeMeta.label, "Skill")} | {safeString(skill?.skill_type || skill?.type, "active skill")}
                        </div>
                      </div>
                      <span style={statusStyle(item?.is_enabled ? "active" : "inactive")}>
                        {item?.is_enabled ? "enabled" : "disabled"}
                      </span>
                    </div>
                    <div style={{ marginTop: 7, display: "flex", gap: 6, flexWrap: "wrap" }}>
                      <span style={statusStyle(typeMeta.executionState)}>{typeMeta.executionState}</span>
                      {typeMeta.blocked ? <span style={statusStyle("blocked")}>non-executable</span> : null}
                    </div>
                  </div>
                );
              })}
              {activeSkillItems.length > 3 ? <div style={{ fontSize: 11, color: C.textDim }}>+{activeSkillItems.length - 3} more</div> : null}
            </div>
          ) : (
            <EmptyPanelState
              title="No agent selected"
              description="Pilih agent dulu dari lane utama supaya active skill panel kebaca."
              actionLabel="Open agent"
              onAction={() => onOpenPanel?.("create-agent")}
            />
          )}
        </Card>
      </div>
    </div>
  );
}

function ProviderApiKeyContent({
  currentUser,
  providerSettings,
  apiKeyStatuses,
  modelProviders,
  onSaveSettings,
  onSaveApiKey,
  onDeleteApiKey,
  errors = {},
  onOpenPanel
}) {
  const user = currentUser || {
    display_name: "nama user",
    username: "nama user",
    email: "user@email.com",
    subscription_plan: "free"
  };
  const providerOptions = [
    { value: "openai", label: "OpenAI" },
    { value: "anthropic", label: "Anthropic" },
    { value: "google_gemini", label: "Google Gemini" },
    { value: "openrouter", label: "OpenRouter" },
    { value: "ollama_local", label: "Ollama Local" },
    { value: "custom", label: "Custom" }
  ].map((item) => {
    const match = modelProviders.find((provider) => {
      const name = String(provider?.name || "").toLowerCase();
      const type = String(provider?.provider_type || "").toLowerCase();
      return type === item.value || name.includes(item.value.replace("_", " "));
    });

    return {
      value: item.value,
      label: match?.name || item.label
    };
  });
  const [preferredProvider, setPreferredProvider] = useState(providerSettings?.preferred_provider || providerOptions[0]?.value || "openai");
  const [preferredModel, setPreferredModel] = useState(providerSettings?.preferred_model || "gpt-4o");
  const [message, setMessage] = useState("");
  const [keyDrafts, setKeyDrafts] = useState({});
  const testConnectionLabel = "test connection not available yet";
  const testConnectionEnabled = false;
  const canSaveSettings = Boolean(onSaveSettings);

  useEffect(() => {
    setPreferredProvider(providerSettings?.preferred_provider || providerOptions[0]?.value || "openai");
    setPreferredModel(providerSettings?.preferred_model || "gpt-4o");
  }, [providerSettings?.preferred_provider, providerSettings?.preferred_model, providerOptions]);

  useEffect(() => {
    const next = {};
    (apiKeyStatuses.length ? apiKeyStatuses : SETTINGS_KEYS).forEach((item) => {
      next[item.provider] = "";
    });
    setKeyDrafts(next);
  }, [apiKeyStatuses]);

  async function handleSaveSettings() {
    if (!onSaveSettings) {
      setMessage("Save settings backend endpoint not available yet.");
      return;
    }

    setMessage("");
    try {
      await onSaveSettings({
        preferred_provider: preferredProvider,
        preferred_model: preferredModel
      });
      setMessage("Model setting saved.");
    } catch (saveError) {
      setMessage(saveError?.message || "Save settings gagal.");
    }
  }

  async function handleSaveKey(provider) {
    if (!onSaveApiKey) {
      setMessage("Save key backend endpoint not available yet.");
      return;
    }

    const apiKey = String(keyDrafts[provider] || "").trim();
    if (!apiKey) {
      setMessage("API key kosong.");
      return;
    }

    setMessage("");
    try {
      await onSaveApiKey(provider, apiKey);
      setKeyDrafts((current) => ({ ...current, [provider]: "" }));
      setMessage(`${provider} key saved.`);
    } catch (saveError) {
      setMessage(saveError?.message || "Save key gagal.");
    }
  }

  async function handleDeleteKey(provider) {
    if (!onDeleteApiKey) {
      setMessage("Delete key backend endpoint not available yet.");
      return;
    }

    setMessage("");
    try {
      await onDeleteApiKey(provider);
      setMessage(`${provider} key deleted.`);
    } catch (deleteError) {
      setMessage(deleteError?.message || "Delete key gagal.");
    }
  }

  const keyRows = apiKeyStatuses.length
    ? apiKeyStatuses.map((item, index) => ({
        id: item?.provider || `provider-${index + 1}`,
        provider: item?.provider || "-",
        masked: item?.masked_key || item?.key_last4 || item?.maskedKey || "not set",
        status: item?.connection_status || "not setup"
      }))
    : SETTINGS_KEYS.map((item) => ({
        id: item.provider,
        provider: item.provider,
        masked: item.masked,
        status: item.status
      }));

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
      <PanelHeader
        title="Provider / API Key"
        description="Panel ringkas untuk atur provider default, simpan key, dan lihat status vault."
        badge={preferredProvider ? "ready" : "need setup"}
      />

      <InlineFeedback message={errors.general} error />

      <Card style={{ background: C.card }}>
        <SectionTitle title="Account" subtitle={user.display_name || user.username} />
        <div style={{ display: "grid", gap: 8 }}>
          <div style={{ padding: "8px 10px", borderRadius: 8, background: C.bgDeep, border: `1px solid ${C.border}`, fontSize: 12, color: C.textSub }}>
            Email: {user.email || "user@email.com"}
          </div>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <div style={{ fontSize: 12, color: C.textMuted }}>Plan</div>
            <span style={statusStyle("ready")}>{String(user.subscription_plan || "FREE").toUpperCase()}</span>
          </div>
        </div>
      </Card>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
        <Card style={{ background: C.card }}>
          <SectionTitle title="Brain / Model" subtitle="Default provider dan model." />
          <div style={{ display: "grid", gap: 8 }}>
            <div style={{ padding: "8px 10px", borderRadius: 8, background: C.bgDeep, border: `1px solid ${C.border}` }}>
              <div style={{ fontSize: 11, color: C.textMuted, marginBottom: 4 }}>Default Provider</div>
              <select
                value={preferredProvider}
                onChange={(event) => setPreferredProvider(event.target.value)}
                style={{ width: "100%", background: "none", border: "none", outline: "none", fontSize: 12, color: C.textSub, ...FONT }}
              >
                {providerOptions.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </div>
            <div style={{ padding: "8px 10px", borderRadius: 8, background: C.bgDeep, border: `1px solid ${C.border}` }}>
              <div style={{ fontSize: 11, color: C.textMuted, marginBottom: 4 }}>Default Model</div>
              <input
                value={preferredModel}
                onChange={(event) => setPreferredModel(event.target.value)}
                style={{ width: "100%", background: "none", border: "none", outline: "none", fontSize: 12, color: C.textSub, ...FONT }}
              />
            </div>
          <button
            type="button"
            onClick={handleSaveSettings}
            disabled={!canSaveSettings}
            style={{
              marginTop: 2,
              width: "100%",
              padding: "8px 12px",
              borderRadius: 10,
              border: `1px solid ${C.border}`,
              background: C.cardInner,
              color: canSaveSettings ? C.textMuted : C.textDim,
              fontSize: 12,
              cursor: canSaveSettings ? "pointer" : "not-allowed",
              opacity: canSaveSettings ? 1 : 0.72,
              ...FONT
            }}
            title={canSaveSettings ? "Save model settings." : "Save settings backend endpoint not available yet."}
          >
            Save Model Settings
          </button>
          </div>
        </Card>

        <Card style={{ background: C.card }}>
          <SectionTitle title="API Key Vault" subtitle="Raw key tidak ditampilkan." />
          <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
            {keyRows.map((item) => (
              <div key={item.provider} style={{ padding: "9px 10px", borderRadius: 8, background: C.bgDeep, border: `1px solid ${C.border}` }}>
                <div style={{ display: "flex", justifyContent: "space-between", gap: 10 }}>
                  <div>
                    <div style={{ fontSize: 12, fontWeight: 600, color: C.text }}>{item.provider}</div>
                    <div style={{ fontSize: 11, color: C.textMuted, marginTop: 2 }}>{item.masked}</div>
                  </div>
                  <span style={statusStyle(item.status)}>{item.status}</span>
                </div>
              <div style={{ marginTop: 8, display: "flex", gap: 8 }}>
                {(() => {
                  const draftKey = String(keyDrafts[item.provider] || "").trim();
                  const canSaveKey = Boolean(onSaveApiKey) && Boolean(draftKey);
                  const canDeleteKey = Boolean(onDeleteApiKey);

                  return (
                    <>
                  <input
                    type="password"
                    autoComplete="off"
                    spellCheck={false}
                    autoCorrect="off"
                    autoCapitalize="off"
                    value={keyDrafts[item.provider] || ""}
                    onChange={(event) => setKeyDrafts((current) => ({ ...current, [item.provider]: event.target.value }))}
                    placeholder="paste api key"
                    style={{
                      flex: 1,
                      padding: "7px 10px",
                      borderRadius: 8,
                      border: `1px solid ${C.border}`,
                      background: C.card,
                      fontSize: 12,
                      color: C.text,
                      ...FONT
                    }}
                  />
                  <button
                    type="button"
                    disabled={!canSaveKey}
                    onClick={() => handleSaveKey(item.provider)}
                    style={{
                      padding: "7px 10px",
                      borderRadius: 8,
                      border: `1px solid ${C.border}`,
                      background: C.cardInner,
                      color: canSaveKey ? C.textMuted : C.textDim,
                      fontSize: 12,
                      cursor: canSaveKey ? "pointer" : "not-allowed",
                      opacity: canSaveKey ? 1 : 0.72,
                      ...FONT
                    }}
                    title={canSaveKey ? "Save or update key." : "Need key input or backend save endpoint."}
                  >
                    Save / Update
                  </button>
                  <button
                    type="button"
                    disabled={!canDeleteKey}
                    onClick={() => handleDeleteKey(item.provider)}
                    style={{
                      padding: "7px 10px",
                      borderRadius: 8,
                      border: `1px solid ${C.border}`,
                      background: C.cardInner,
                      color: canDeleteKey ? C.textMuted : C.textDim,
                      fontSize: 12,
                      cursor: canDeleteKey ? "pointer" : "not-allowed",
                      opacity: canDeleteKey ? 1 : 0.72,
                      ...FONT
                    }}
                    title={canDeleteKey ? "Delete key." : "Delete key backend endpoint not available yet."}
                  >
                    Delete
                  </button>
                    </>
                  );
                })()}
                </div>
                <div style={{ marginTop: 6, fontSize: 11, lineHeight: 1.5, color: C.textMuted }}>
                  Raw key cuma hidup di input sementara. Setelah save/update, field langsung dikosongkan.
                </div>
              </div>
            ))}
          </div>
        </Card>
      </div>

      <PanelStateCard
        title="Connection note"
        description="Provider test dan OAuth connection tetap backend-owned. Panel ini cuma mount shell dan simpan metadata aman."
        tone="review"
        actionLabel="Open connections"
        onAction={() => onOpenPanel?.("oauth-connections")}
      />
      <button
        type="button"
        disabled={!testConnectionEnabled}
        title="Backend belum sediakan test endpoint aman."
        style={{
          width: "100%",
          padding: "8px 12px",
          borderRadius: 10,
          border: `1px solid ${C.border}`,
          background: C.bgDeep,
          color: C.textMuted,
          fontSize: 12,
          cursor: "not-allowed",
          opacity: 0.72,
          ...FONT
        }}
      >
        {testConnectionLabel}
      </button>

      <div style={{ display: "grid", gap: 8 }}>
        <InlineFeedback message={errors.apiKeyVault} error />
        <InlineFeedback message={message} />
      </div>
    </div>
  );
}

function OAuthConnectionsContent({ modelProviders = [], apiKeyStatuses = [], runtimeCapabilities = [], errors = {}, onOpenPanel }) {
  const oauthCapability = runtimeCapabilities.find((item) => String(item?.key || "") === "oauth.connection") || null;
  const oauthBackendAvailable = Boolean(oauthCapability && oauthCapability.status !== "forbidden");
  const providerRows = modelProviders.length
    ? modelProviders.map((item, index) => {
        const providerKey = String(item?.provider || item?.id || item?.name || `provider-${index + 1}`).toLowerCase();
        const keyStatus = apiKeyStatuses.find((statusItem) => String(statusItem?.provider || "").toLowerCase() === providerKey) || null;
        const providerType = String(item?.provider_type || item?.type || "").toLowerCase();
        const authType = String(item?.auth_type || "").toLowerCase();
        const statusSummary = getOAuthConnectionSummary(
          keyStatus?.connection_status || item?.connection_status || (authType === "oauth_gateway" || providerType === "subscription_oauth" ? "locked" : "not setup")
        );

        return {
          id: providerKey,
          name: item?.name || item?.label || item?.provider || item?.id || `Provider ${index + 1}`,
          type: providerType || authType || "api",
          status: statusSummary.label,
          statusTone: statusSummary.tone,
          description: item?.description || item?.summary || keyStatus?.masked_key || "Connection metadata only.",
          connectionDetail: oauthBackendAvailable ? "Backend metadata only. No token stored in frontend." : "OAuth backend endpoint not available yet.",
          canConnect: Boolean(oauthBackendAvailable && (item?.oauth_auth_url || item?.auth_url || item?.connect_url || item?.auth_endpoint)),
          canDisconnect: Boolean(oauthBackendAvailable && (item?.oauth_disconnect_url || item?.disconnect_url || item?.disconnect_endpoint))
        };
      })
    : [];

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
      <PanelHeader
        title="OAuth / Connections"
        description="Panel koneksi. OAuth flow masih backend-required, jadi shell cuma baca status aman."
        badge={oauthBackendAvailable ? "preview only" : "locked"}
      />

      <InlineFeedback message={errors.general} error />

      <PanelStateCard
        title={safeString(oauthCapability?.label, "OAuth connection")}
        description={safeString(oauthBackendAvailable ? "OAuth backend endpoint available." : "OAuth backend endpoint not available yet.", "OAuth backend endpoint not available yet.")}
        tone={oauthBackendAvailable ? "inactive" : "review"}
        actionLabel="Open safety"
        onAction={() => onOpenPanel?.("safety-center")}
      />

      <Card style={{ background: C.card }}>
        <SectionTitle
          title="Provider links"
          subtitle={oauthBackendAvailable ? "Status sinkron dari provider metadata dan vault." : "Backend belum sediakan auth/disconnect URL. Panel hanya tampilkan metadata aman."}
        />
        {providerRows.length ? (
          <div style={{ display: "grid", gap: 8 }}>
            {providerRows.map((row) => (
              <div
                key={row.id}
                style={{
                  padding: "9px 10px",
                  borderRadius: 9,
                  background: C.bgDeep,
                  border: `1px solid ${C.border}`
                }}
              >
                <div style={{ display: "flex", justifyContent: "space-between", gap: 10, alignItems: "flex-start" }}>
                  <div>
                    <div style={{ fontSize: 12, fontWeight: 600, color: C.text }}>{row.name}</div>
                    <div style={{ fontSize: 11, color: C.textMuted, marginTop: 2 }}>{row.type}</div>
                  </div>
                  <span style={statusStyle(row.statusTone)}>{row.status}</span>
                </div>
                <div style={{ marginTop: 7, fontSize: 11, lineHeight: 1.55, color: C.textDim }}>
                  {row.description}
                </div>
                <div style={{ marginTop: 6, fontSize: 11, lineHeight: 1.55, color: C.textMuted }}>
                  {row.connectionDetail}
                </div>
                <div style={{ display: "flex", gap: 8, marginTop: 8, flexWrap: "wrap" }}>
                  <button
                    type="button"
                    disabled={!row.canConnect}
                    title={row.canConnect ? "Connect via backend auth URL." : "Backend auth URL belum tersedia."}
                    style={{
                      padding: "6px 10px",
                      borderRadius: 8,
                      border: `1px solid ${C.border}`,
                      background: row.canConnect ? C.bg : C.bgDeep,
                      color: row.canConnect ? C.text : C.textMuted,
                      fontSize: 11,
                      fontWeight: 600,
                      cursor: row.canConnect ? "pointer" : "not-allowed",
                      opacity: row.canConnect ? 1 : 0.7,
                      ...FONT
                    }}
                  >
                    Connect
                  </button>
                  <button
                    type="button"
                    disabled={!row.canDisconnect}
                    title={row.canDisconnect ? "Disconnect via backend endpoint." : "Backend disconnect endpoint belum tersedia."}
                    style={{
                      padding: "6px 10px",
                      borderRadius: 8,
                      border: `1px solid ${C.border}`,
                      background: row.canDisconnect ? C.bg : C.bgDeep,
                      color: row.canDisconnect ? C.text : C.textMuted,
                      fontSize: 11,
                      fontWeight: 600,
                      cursor: row.canDisconnect ? "pointer" : "not-allowed",
                      opacity: row.canDisconnect ? 1 : 0.7,
                      ...FONT
                    }}
                  >
                    Disconnect
                  </button>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <EmptyPanelState
            title="Belum ada connection row"
            description="Backend belum kirim metadata koneksi. Buka Provider panel kalau mau atur key dulu."
            actionLabel="Open provider panel"
            onAction={() => onOpenPanel?.("providers")}
          />
        )}
      </Card>

      <PanelStateCard
        title="Backend required"
        description="Tidak ada live OAuth action di shell ini. Kalau endpoint koneksi muncul nanti, baru kita sambungkan."
        tone="review"
        actionLabel="Open provider keys"
        onAction={() => onOpenPanel?.("providers")}
      />
    </div>
  );
}

function SafetyCenterContent({
  runtimeCapabilities = [],
  activityRows = [],
  auditRows = [],
  taskRows = [],
  approvalRows = [],
  isLoading = false,
  errors = {},
  onOpenPanel,
  onRefresh,
  onApproveApproval,
  onRejectApproval
}) {
  const capabilityRows = runtimeCapabilities.slice();
  const pendingApprovals = approvalRows.filter((row) => row?.isPending);
  const waitingApprovalTasks = taskRows.filter((row) => String(row?.status || "").toLowerCase().replace(/_/g, " ") === "waiting approval");
  const completedTasks = taskRows.filter((row) => String(row?.status || "").toLowerCase() === "completed");
  const failedTasks = taskRows.filter((row) => String(row?.status || "").toLowerCase() === "failed");
  const recentActivity = activityRows.slice(0, 5);
  const recentAudit = auditRows.slice(0, 5);
  const recentTasks = taskRows.slice(0, 5);

  const summaryCards = [
    {
      title: "Runtime",
      value: capabilityRows.length,
      detail: capabilityRows.length ? capabilityRows[0].label : "backend required",
      badge: isLoading ? "loading" : capabilityRows.length ? "ready" : "preview only"
    },
    {
      title: "Activity",
      value: activityRows.length,
      detail: activityRows.length ? recentActivity[0]?.title || "recent event" : "no rows",
      badge: errors.activity ? "review" : activityRows.length ? "ready" : "preview only"
    },
    {
      title: "Tasks",
      value: taskRows.length,
      detail: `${waitingApprovalTasks.length} waiting approval | ${completedTasks.length} completed | ${failedTasks.length} failed`,
      badge: errors.tasks ? "review" : taskRows.length ? "ready" : "preview only"
    },
    {
      title: "Approvals",
      value: pendingApprovals.length,
      detail: pendingApprovals.length ? "pending review" : "no pending approval",
      badge: errors.approvals ? "review" : pendingApprovals.length ? "pending" : "ready"
    }
  ];

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
      <PanelHeader
        title="Safety Center"
        description="Read-only safe. Logs, audit, task, approval cuma view. Tidak ada execution di sini."
        badge={isLoading ? "loading" : capabilityRows.length ? "ready" : "preview only"}
        actionLabel="Refresh"
        onAction={onRefresh}
        actionDisabled={isLoading}
      />

      {errors.safety ? <PanelStateCard title="Safety data" description={errors.safety} tone="review" /> : null}

      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(150px, 1fr))", gap: 10 }}>
        {summaryCards.map((item) => (
          <Card key={item.title} style={{ background: C.card, padding: 12 }}>
            <div style={{ display: "flex", justifyContent: "space-between", gap: 10, alignItems: "flex-start" }}>
              <div>
                <div style={{ fontSize: 11, fontWeight: 700, color: C.textDim, textTransform: "uppercase", letterSpacing: "0.05em" }}>
                  {item.title}
                </div>
                <div style={{ marginTop: 6, fontSize: 22, fontWeight: 700, color: C.text }}>{item.value}</div>
                <div style={{ marginTop: 3, fontSize: 11, color: C.textMuted, lineHeight: 1.45 }}>{item.detail}</div>
              </div>
              <span style={statusStyle(item.badge)}>{item.badge}</span>
            </div>
          </Card>
        ))}
      </div>

      <Card style={{ background: C.card }}>
        <SectionTitle
          title="Capability matrix"
          subtitle="Mode backend menentukan mana yang confirm, suggestion-only, atau forbidden."
        />
        {errors.safety ? (
          <PanelStateCard title="Capability data" description={errors.safety} tone="review" />
        ) : capabilityRows.length ? (
          <div style={{ display: "grid", gap: 8 }}>
            {capabilityRows.map((item) => (
              <div
                key={item.key}
                style={{
                  padding: "9px 10px",
                  borderRadius: 9,
                  background: C.bgDeep,
                  border: `1px solid ${C.border}`
                }}
              >
                <div style={{ display: "flex", justifyContent: "space-between", gap: 10, alignItems: "flex-start" }}>
                  <div>
                    <div style={{ fontSize: 12, fontWeight: 600, color: C.text }}>{item.label}</div>
                    <div style={{ fontSize: 11, color: C.textMuted, marginTop: 2 }}>{item.key}</div>
                  </div>
                  <div style={{ display: "flex", gap: 6, flexWrap: "wrap", justifyContent: "flex-end" }}>
                    <span style={statusStyle(item.status)}>{item.status}</span>
                    <span style={statusStyle(item.requires_confirmation ? "review" : "inactive")}>
                      {item.requires_confirmation ? "confirm" : "no confirm"}
                    </span>
                  </div>
                </div>
                <div style={{ marginTop: 7, fontSize: 11, lineHeight: 1.55, color: C.textDim }}>
                  {item.description}
                </div>
              </div>
            ))}
          </div>
        ) : isLoading ? (
          <LoadingPanelState
            title="Capability matrix not loaded"
            description="Panel ini menunggu data runtime capabilities dari backend."
          />
        ) : (
          <EmptyPanelState
            title="Capability matrix empty"
            description="Backend belum kirim runtime capability data. Panel tetap read-only."
          />
        )}
      </Card>

      <Card style={{ background: C.card }}>
        <SectionTitle
          title="Activity logs"
          subtitle="Recent event stream from GET /logs/activity."
          actionLabel="Open activity log"
          onAction={() => onOpenPanel?.("activity-log")}
        />
        {errors.activity ? (
          <PanelStateCard title="Activity logs" description={errors.activity} tone="review" />
        ) : isLoading ? (
          <LoadingPanelState title="Activity logs loading" description="Menunggu activity log dari backend." />
        ) : recentActivity.length ? (
          <div style={{ display: "grid", gap: 8 }}>
            {recentActivity.map((item) => (
              <div
                key={`${item.time}-${item.title}`}
                style={{
                  padding: "9px 10px",
                  borderRadius: 9,
                  background: C.bgDeep,
                  border: `1px solid ${C.border}`
                }}
              >
                <div style={{ display: "flex", justifyContent: "space-between", gap: 10 }}>
                  <div style={{ minWidth: 0 }}>
                    <div style={{ fontSize: 12, fontWeight: 600, color: C.text }}>{item.title}</div>
                    <div style={{ fontSize: 11, color: C.textMuted, marginTop: 2, lineHeight: 1.5 }}>{item.desc}</div>
                    <div style={{ fontSize: 11, color: C.textDim, marginTop: 4 }}>actor {safeString(item.actor, "-")}</div>
                  </div>
                  <div style={{ display: "flex", flexDirection: "column", alignItems: "flex-end", gap: 6, flexShrink: 0 }}>
                    <span style={statusStyle(item.tone)}>{item.status}</span>
                    <span style={{ fontSize: 11, color: C.textDim }}>{item.time}</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <EmptyPanelState
            title="No activity log yet"
            description="GET /logs/activity balikin kosong. Shell tetap read-only."
            actionLabel="Refresh"
            onAction={onRefresh}
          />
        )}
      </Card>

      <Card style={{ background: C.card }}>
        <SectionTitle title="Audit logs" subtitle="Recent audit trail from GET /logs/audit." />
        {errors.audit ? (
          <PanelStateCard title="Audit logs" description={errors.audit} tone="review" />
        ) : isLoading ? (
          <LoadingPanelState title="Audit logs loading" description="Menunggu audit trail dari backend." />
        ) : recentAudit.length ? (
          <div style={{ display: "grid", gap: 8 }}>
            {recentAudit.map((item) => (
              <div
                key={`${item.time}-${item.title}`}
                style={{
                  padding: "9px 10px",
                  borderRadius: 9,
                  background: C.bgDeep,
                  border: `1px solid ${C.border}`
                }}
              >
                <div style={{ display: "flex", justifyContent: "space-between", gap: 10 }}>
                  <div style={{ minWidth: 0 }}>
                    <div style={{ fontSize: 12, fontWeight: 600, color: C.text }}>{item.title}</div>
                    <div style={{ fontSize: 11, color: C.textMuted, marginTop: 2, lineHeight: 1.5 }}>{item.desc}</div>
                    <div style={{ fontSize: 11, color: C.textDim, marginTop: 4 }}>actor {safeString(item.actor, "-")}</div>
                  </div>
                  <div style={{ display: "flex", flexDirection: "column", alignItems: "flex-end", gap: 6, flexShrink: 0 }}>
                    <span style={statusStyle(item.tone)}>{item.status}</span>
                    <span style={{ fontSize: 11, color: C.textDim }}>{item.time}</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <EmptyPanelState
            title="No audit log yet"
            description="GET /logs/audit balikin kosong. Shell tetap aman."
            actionLabel="Refresh"
            onAction={onRefresh}
          />
        )}
      </Card>

      <Card style={{ background: C.card }}>
        <SectionTitle title="Task summary" subtitle="Ringkas status dari GET /tasks." />
        {errors.tasks ? (
          <PanelStateCard title="Task summary" description={errors.tasks} tone="review" />
        ) : isLoading ? (
          <LoadingPanelState title="Task summary loading" description="Menunggu task list dari backend." />
        ) : taskRows.length ? (
          <div style={{ display: "grid", gap: 10 }}>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(120px, 1fr))", gap: 8 }}>
              {[
                { label: "Received", value: taskRows.filter((row) => String(row.status || "").toLowerCase() === "received").length },
                { label: "Waiting approval", value: waitingApprovalTasks.length },
                { label: "Completed", value: completedTasks.length },
                { label: "Failed", value: failedTasks.length }
              ].map((item) => (
                <div key={item.label} style={{ padding: 10, borderRadius: 9, background: C.bgDeep, border: `1px solid ${C.border}` }}>
                  <div style={{ fontSize: 11, color: C.textDim, textTransform: "uppercase", letterSpacing: "0.04em" }}>{item.label}</div>
                  <div style={{ marginTop: 5, fontSize: 18, fontWeight: 700, color: C.text }}>{item.value}</div>
                </div>
              ))}
            </div>
            <div style={{ display: "grid", gap: 8 }}>
              {recentTasks.map((item) => (
                <div
                  key={item.id}
                  style={{
                    padding: "9px 10px",
                    borderRadius: 9,
                    background: C.bgDeep,
                    border: `1px solid ${C.border}`
                  }}
                >
                  <div style={{ display: "flex", justifyContent: "space-between", gap: 10 }}>
                    <div style={{ minWidth: 0 }}>
                      <div style={{ fontSize: 12, fontWeight: 600, color: C.text }}>{item.title}</div>
                      <div style={{ fontSize: 11, color: C.textMuted, marginTop: 2, lineHeight: 1.5 }}>{item.desc}</div>
                      <div style={{ fontSize: 11, color: C.textDim, marginTop: 4 }}>
                        started {safeString(item.startedAt, "-")} | done {safeString(item.completedAt, "-")}
                      </div>
                    </div>
                    <div style={{ display: "flex", flexDirection: "column", alignItems: "flex-end", gap: 6, flexShrink: 0 }}>
                      <span style={statusStyle(item.tone)}>{item.status}</span>
                      <span style={{ fontSize: 11, color: C.textDim }}>{item.time}</span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        ) : (
          <EmptyPanelState
            title="No task row yet"
            description="GET /tasks kosong. Task summary tetap tampil kosong, bukan sukses palsu."
            actionLabel="Refresh"
            onAction={onRefresh}
          />
        )}
      </Card>

      <Card style={{ background: C.card }}>
        <SectionTitle title="Pending approvals" subtitle="Record-only approve/reject. No tool, n8n, or model execution." />
        {errors.approvals ? (
          <PanelStateCard title="Approvals" description={errors.approvals} tone="review" />
        ) : isLoading ? (
          <LoadingPanelState title="Approval list loading" description="Menunggu pending approvals dari backend." />
        ) : pendingApprovals.length ? (
          <div style={{ display: "grid", gap: 8 }}>
            {pendingApprovals.map((item) => (
              <div
                key={item.id}
                style={{
                  padding: "9px 10px",
                  borderRadius: 9,
                  background: C.bgDeep,
                  border: `1px solid ${C.border}`
                }}
              >
                <div style={{ display: "flex", justifyContent: "space-between", gap: 10, alignItems: "flex-start" }}>
                  <div style={{ minWidth: 0 }}>
                    <div style={{ fontSize: 12, fontWeight: 600, color: C.text }}>{item.title}</div>
                    <div style={{ fontSize: 11, color: C.textMuted, marginTop: 2, lineHeight: 1.5 }}>{item.desc}</div>
                    <div style={{ fontSize: 11, color: C.textDim, marginTop: 4 }}>task {safeString(item.taskId, "-")}</div>
                  </div>
                  <div style={{ display: "flex", gap: 6, flexWrap: "wrap", justifyContent: "flex-end", flexShrink: 0 }}>
                    <span style={statusStyle(item.riskLevel)}>{item.riskLevel}</span>
                    <span style={statusStyle(item.status)}>{item.status}</span>
                    {item.time ? <span style={{ fontSize: 11, color: C.textDim, alignSelf: "center" }}>{item.time}</span> : null}
                  </div>
                </div>
                <div style={{ display: "flex", gap: 8, marginTop: 8, flexWrap: "wrap" }}>
                  <button
                    type="button"
                    onClick={() => onApproveApproval?.(item.raw)}
                    style={{
                      padding: "6px 10px",
                      borderRadius: 8,
                      border: `1px solid ${C.border}`,
                      background: C.cardInner,
                      color: C.green,
                      fontSize: 11,
                      fontWeight: 600,
                      cursor: "pointer",
                      ...FONT
                    }}
                  >
                    Approve
                  </button>
                  <button
                    type="button"
                    onClick={() => onRejectApproval?.(item.raw)}
                    style={{
                      padding: "6px 10px",
                      borderRadius: 8,
                      border: `1px solid ${C.border}`,
                      background: C.cardInner,
                      color: C.accent,
                      fontSize: 11,
                      fontWeight: 600,
                      cursor: "pointer",
                      ...FONT
                    }}
                  >
                    Reject
                  </button>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <EmptyPanelState
            title="No pending approvals"
            description="Tidak ada approval menunggu keputusan. Aksi tetap hidden."
            actionLabel="Refresh"
            onAction={onRefresh}
          />
        )}
      </Card>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
        <PanelStateCard
          title="Provider test"
          description="Model provider test tetap explicit-confirm. Tidak dijalankan otomatis dari shell."
          tone="review"
          actionLabel="Open providers"
          onAction={() => onOpenPanel?.("providers")}
        />
        <PanelStateCard
          title="OAuth guard"
          description="OAuth connection memang forbidden di release ini."
          tone="review"
          actionLabel="Open connections"
          onAction={() => onOpenPanel?.("oauth-connections")}
        />
      </div>
    </div>
  );
}

function ActiveSkillsContent({ selectedAgent, selectedAgentSkills = [], error = "", onOpenPanel }) {
  const agentName = selectedAgent?.name || "Belum ada agent";

  const rows = selectedAgentSkills.map((item, index) => {
    const skill = item?.skill || {};
    return {
      id: String(item?.id || skill?.id || `active-skill-${index + 1}`),
      name: skill?.title || skill?.name || skill?.slug || `Skill ${index + 1}`,
      type: skill?.skill_type || skill?.type || "active_skill",
      enabled: item?.is_enabled !== false,
      source: skill?.source_url || skill?.source_reference || skill?.file_path || "-"
    };
  });

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
      <PanelHeader
        title="Active Skills"
        description="Skill aktif ngikut agent yang sedang dipilih di lane utama."
        badge={selectedAgent ? "ready" : "preview only"}
      />

      {error ? <PanelStateCard title="Active skill data" description={error} tone="review" /> : null}

      <PanelStateCard
        title={agentName}
        description={selectedAgent ? `${rows.length} skill aktif terhubung.` : "Pilih agent dulu supaya daftar active skill kebaca."}
        tone={selectedAgent ? "inactive" : "review"}
        actionLabel="Open skill panel"
        onAction={() => onOpenPanel?.("skill-panel")}
      />

      <Card style={{ background: C.card }}>
        <SectionTitle title="Active list" subtitle="Data dari GET /agents/{id}/active-skills." />
        {rows.length ? (
          <div style={{ display: "grid", gap: 8 }}>
            {rows.map((row) => (
              <div
                key={row.id}
                style={{
                  padding: "9px 10px",
                  borderRadius: 9,
                  background: C.bgDeep,
                  border: `1px solid ${C.border}`
                }}
              >
                <div style={{ display: "flex", justifyContent: "space-between", gap: 10, alignItems: "flex-start" }}>
                  <div>
                    <div style={{ fontSize: 12, fontWeight: 600, color: C.text }}>{row.name}</div>
                    <div style={{ fontSize: 11, color: C.textMuted, marginTop: 2 }}>{row.type}</div>
                  </div>
                  <span style={statusStyle(row.enabled ? "active" : "inactive")}>{row.enabled ? "enabled" : "disabled"}</span>
                </div>
                <div style={{ marginTop: 7, fontSize: 11, color: C.textDim }}>{row.source}</div>
              </div>
            ))}
          </div>
        ) : (
          <EmptyPanelState
            title="No active skills"
            description="Agent ini belum punya active skill. Buka skill panel untuk attach dari library."
            actionLabel="Open skill hub"
            onAction={() => onOpenPanel?.("skill-panel")}
          />
        )}
      </Card>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
        <PanelStateCard
          title="Agent switch"
          description="Kalau mau lihat agent lain, balik ke lane utama dulu."
          actionLabel="Open agent"
          onAction={() => onOpenPanel?.("create-agent")}
        />
        <PanelStateCard
          title="Library shortcut"
          description="Attach/detach tetap di library skill panel."
          actionLabel="Open library"
          onAction={() => onOpenPanel?.("library-skill")}
        />
      </div>
    </div>
  );
}

function getOAuthConnectionSummary(status) {
  const normalized = String(status || "").toLowerCase();

  if (normalized === "connected" || normalized === "active" || normalized === "ready") {
    return { label: "connected", tone: "active" };
  }

  if (normalized === "disconnected" || normalized === "not_connected") {
    return { label: "disconnected", tone: "not setup" };
  }

  if (normalized === "locked" || normalized === "forbidden") {
    return { label: "locked", tone: "locked" };
  }

  if (normalized === "not setup" || normalized === "inactive") {
    return { label: "disconnected", tone: "not setup" };
  }

  return { label: normalized || "unknown", tone: "inactive" };
}

function NavButton({ label, icon, onClick, active = false }) {
  const [hovered, setHovered] = useState(false);
  const onState = hovered || active;

  return (
    <button
      type="button"
      onClick={onClick}
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
      style={{
        display: "flex",
        alignItems: "center",
        gap: 9,
        padding: "9px 12px 9px 11px",
        borderRadius: 13,
        width: "100%",
        textAlign: "left",
        border: `1px solid ${onState ? "rgba(90,65,35,0.10)" : "transparent"}`,
        background: onState ? "rgba(255,255,255,0.86)" : "transparent",
        color: onState ? C.text : C.textSub,
        fontSize: 12.5,
        cursor: "pointer",
        transition:
          "background 160ms ease, border-color 160ms ease, color 160ms ease, transform 160ms ease, box-shadow 160ms ease",
        transform: onState ? "translateX(1px)" : "translateX(0)",
        boxShadow: onState ? "inset 0 1px 0 rgba(255,255,255,0.72), 0 3px 10px rgba(90,65,35,0.04)" : "none",
        ...FONT
      }}
    >
      <span
        style={{
          color: onState ? C.accent : C.textMuted,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          width: 14,
          height: 14,
          transition: "color 160ms ease"
        }}
      >
        <MenuIcon name={icon} />
      </span>
      <span>{label}</span>
    </button>
  );
}

function AgentCard({ agent }) {
  const [cmd, setCmd] = useState("");
  const [decision, setDecision] = useState(null);
  const [notes, setNotes] = useState([]);
  const skillItems = Array.isArray(agent?.skills) ? agent.skills : [];
  const activityItems = Array.isArray(agent?.activity) ? agent.activity : [];
  const statusMap = {
    idle: { label: "Idle", color: C.textDim, bg: "rgba(0,0,0,0.05)" },
    active: { label: "Running", color: C.amber, bg: C.amberLight },
    sending: { label: "Sending", color: C.green, bg: C.greenLight }
  };
  const status = statusMap[agent.status] || statusMap.idle;

  function handleSend() {
    const trimmed = cmd.trim();
    if (!trimmed) return;
    setNotes((current) => [{ id: Date.now(), text: trimmed }, ...current].slice(0, 2));
    setCmd("");
  }

  return (
    <div
      style={{
        flexShrink: 0,
        width: 196,
        background: C.card,
        border: `1.5px solid ${C.border}`,
        borderRadius: 16,
        padding: 14,
        display: "flex",
        flexDirection: "column",
        gap: 11,
        transition: "border-color 0.18s, box-shadow 0.18s"
      }}
    >
      <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between" }}>
        <AgentAvatar agent={agent} size={42} />
        <span style={{ fontSize: 11, fontWeight: 600, padding: "3px 8px", borderRadius: 7, color: status.color, background: status.bg }}>
          {status.label}
        </span>
      </div>

      <div>
        <div style={{ fontSize: 14, fontWeight: 600, color: C.text, marginBottom: 2 }}>{agent.name}</div>
        <div style={{ fontSize: 12, color: C.textMuted }}>skill {agent.skillCount}</div>
      </div>

      <div style={{ background: C.bgDeep, borderRadius: 10, padding: "8px 10px", border: `1px solid ${C.border}` }}>
        <div style={{ fontSize: 10, fontWeight: 700, color: C.textDim, marginBottom: 6, textTransform: "uppercase", letterSpacing: "0.05em" }}>Skills</div>
        {skillItems.slice(0, 3).map((skill) => (
          <div key={skill} style={{ display: "flex", alignItems: "center", gap: 6, marginBottom: 4 }}>
            <div style={{ width: 4, height: 4, borderRadius: "50%", background: C.textDim, flexShrink: 0 }} />
            <span style={{ fontSize: 11, color: C.textMuted }}>{skill}</span>
          </div>
        ))}
        {skillItems.length > 3 ? <div style={{ fontSize: 11, color: C.textDim }}>+{skillItems.length - 3} more</div> : null}
      </div>

      <div style={{ background: C.bgDeep, borderRadius: 10, padding: "8px 10px", border: `1px solid ${C.border}` }}>
        <div style={{ fontSize: 10, fontWeight: 700, color: C.textDim, marginBottom: 6, textTransform: "uppercase", letterSpacing: "0.05em" }}>Activity</div>
        {activityItems.map((activity, index) => (
          <div key={activity} style={{ display: "flex", alignItems: "center", gap: 6, marginBottom: index < activityItems.length - 1 ? 4 : 0 }}>
            <div
              style={{
                width: 5,
                height: 5,
                borderRadius: "50%",
                flexShrink: 0,
                background: index === 0 ? C.textDim : index === 1 ? C.amber : C.green
              }}
            />
            <span style={{ fontSize: 11, color: C.textMuted }}>{activity}</span>
          </div>
        ))}
      </div>

      {agent.needApproval && decision === null ? (
        <div
          style={{
            background: C.amberLight,
            border: `1.5px solid rgba(176,120,32,0.25)`,
            borderRadius: 12,
            padding: 12
          }}
        >
          <div style={{ fontSize: 12, fontWeight: 700, color: C.amber, marginBottom: 3 }}>Approval Needed</div>
          <div style={{ fontSize: 11, color: C.textSub, marginBottom: 7 }}>Agent needs permission before continuing.</div>
          <div style={{ fontSize: 11, color: C.textMuted, marginBottom: 9 }}>• use workflow<br />• attach skill</div>
          <div style={{ display: "flex", gap: 6 }}>
            <button
              type="button"
              onClick={() => setDecision("approved")}
              style={{ flex: 1, padding: "5px 0", borderRadius: 7, border: "none", background: C.green, color: "#fff", fontSize: 11, fontWeight: 600, cursor: "pointer", ...FONT }}
            >
              Approve
            </button>
            <button
              type="button"
              onClick={() => setDecision("rejected")}
              style={{ flex: 1, padding: "5px 0", borderRadius: 7, border: `1px solid ${C.borderMid}`, background: "none", color: C.textMuted, fontSize: 11, cursor: "pointer", ...FONT }}
            >
              Reject
            </button>
          </div>
        </div>
      ) : null}

      {agent.needApproval && decision !== null ? (
        <div style={{ fontSize: 12, color: decision === "approved" ? C.green : C.textDim, textAlign: "center", padding: "4px 0" }}>
          {decision === "approved" ? "Approved" : "Rejected"}
        </div>
      ) : null}

      <div style={{ marginTop: "auto" }}>
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: 6,
            padding: "7px 10px",
            borderRadius: 10,
            border: `1.5px solid ${C.border}`,
            background: C.bgDeep
          }}
        >
          <input
            value={cmd}
            onChange={(event) => setCmd(event.target.value)}
            onKeyDown={(event) => {
              if (event.key === "Enter") {
                event.preventDefault();
                handleSend();
              }
            }}
            placeholder="ketik untuk menyuruh agent..."
            style={{ flex: 1, background: "none", border: "none", outline: "none", fontSize: 11, color: C.text, minWidth: 0, ...FONT }}
          />
          <button type="button" onClick={handleSend} style={{ background: "none", border: "none", cursor: "pointer", color: cmd ? C.accent : C.textDim, padding: 0 }}>
            &gt;
          </button>
        </div>
        {notes.length ? (
          <div style={{ marginTop: 8, display: "flex", flexDirection: "column", gap: 6 }}>
            {notes.map((note) => (
              <div key={note.id} style={{ padding: "7px 9px", borderRadius: 8, background: C.bgDeep, border: `1px solid ${C.border}`, fontSize: 11, color: C.textMuted }}>
                {note.text}
              </div>
            ))}
          </div>
        ) : null}
      </div>
    </div>
  );
}

function WorkspaceAgentCard({ agent, selected = false, onSelect, onApprove, onReject, onSendCommand }) {
  const [cmd, setCmd] = useState("");
  const [notes, setNotes] = useState([]);
  const [sendState, setSendState] = useState({ status: "idle", message: "" });
  const statusMap = {
    idle: { label: "Idle", color: C.textDim, bg: "rgba(0,0,0,0.05)" },
    active: { label: "Running", color: C.amber, bg: C.amberLight },
    sending: { label: "Sending", color: C.green, bg: C.greenLight }
  };
  const status = statusMap[agent?.status] || statusMap.idle;
  const approval = agent?.approval || (agent?.needApproval ? { id: `preview-${agent.id}`, requested_action: "use workflow", risk_level: "medium", status: "pending" } : null);
  const canSend = Boolean(agent?.id && onSendCommand);

  async function handleSend() {
    const trimmed = cmd.trim();
    if (!trimmed || !canSend || sendState.status === "sending") return;

    setSendState({ status: "sending", message: "" });
    setNotes((current) => [{ id: Date.now(), text: `You: ${trimmed}` }, ...current].slice(0, 3));

    try {
      const response = await onSendCommand(agent, trimmed);
      const replyText = safeString(response?.reply || response?.message || response?.output, "");
      if (replyText && replyText !== "-") {
        setNotes((current) => [{ id: Date.now() + 1, text: `Agent: ${replyText}` }, ...current].slice(0, 3));
      }
      setSendState({
        status: "success",
        message: replyText && replyText !== "-" ? "Balasan diterima." : "Command terkirim."
      });
      setCmd("");
    } catch (error) {
      setSendState({ status: "error", message: error?.message || "Send command gagal." });
    }
  }

  return (
    <div
      onClick={onSelect}
      style={{
        flexShrink: 0,
        width: 196,
        background: C.card,
        border: `1.5px solid ${selected ? "rgba(184,92,56,0.30)" : C.border}`,
        borderRadius: 16,
        padding: 14,
        display: "flex",
        flexDirection: "column",
        gap: 11,
        transition: "border-color 0.18s, box-shadow 0.18s",
        boxShadow: selected ? "0 0 0 1px rgba(184,92,56,0.10), 0 12px 24px rgba(62,54,46,0.06)" : "none",
        cursor: "pointer"
      }}
    >
      <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between" }}>
        <AgentAvatar agent={agent} size={42} />
        <span style={{ fontSize: 11, fontWeight: 600, padding: "3px 8px", borderRadius: 7, color: status.color, background: status.bg }}>
          {status.label}
        </span>
      </div>

      <div>
        <div style={{ fontSize: 14, fontWeight: 600, color: C.text, marginBottom: 2 }}>{agent.name}</div>
        <div style={{ fontSize: 12, color: C.textMuted }}>skill {agent.skillCount}</div>
      </div>

      <div style={{ background: C.bgDeep, borderRadius: 10, padding: "8px 10px", border: `1px solid ${C.border}` }}>
        <div style={{ fontSize: 10, fontWeight: 700, color: C.textDim, marginBottom: 6, textTransform: "uppercase", letterSpacing: "0.05em" }}>Skills</div>
        {agent.skills.map((skill) => (
          <div key={skill} style={{ display: "flex", alignItems: "center", gap: 6, marginBottom: 4 }}>
            <div style={{ width: 4, height: 4, borderRadius: "50%", background: C.textDim, flexShrink: 0 }} />
            <span style={{ fontSize: 11, color: C.textMuted }}>{skill}</span>
          </div>
        ))}
      </div>

      <div style={{ background: C.bgDeep, borderRadius: 10, padding: "8px 10px", border: `1px solid ${C.border}` }}>
        <div style={{ fontSize: 10, fontWeight: 700, color: C.textDim, marginBottom: 6, textTransform: "uppercase", letterSpacing: "0.05em" }}>Activity</div>
        {agent.activity.map((activity, index) => (
          <div key={activity} style={{ display: "flex", alignItems: "center", gap: 6, marginBottom: index < agent.activity.length - 1 ? 4 : 0 }}>
            <div
              style={{
                width: 5,
                height: 5,
                borderRadius: "50%",
                flexShrink: 0,
                background: index === 0 ? C.textDim : index === 1 ? C.amber : C.green
              }}
            />
            <span style={{ fontSize: 11, color: C.textMuted }}>{activity}</span>
          </div>
        ))}
      </div>

      {approval ? (
        <div
          style={{
            background: C.amberLight,
            border: `1.5px solid rgba(176,120,32,0.25)`,
            borderRadius: 12,
            padding: 12
          }}
        >
          <div style={{ fontSize: 12, fontWeight: 700, color: C.amber, marginBottom: 3 }}>Approval Needed</div>
          <div style={{ fontSize: 11, color: C.textSub, marginBottom: 7 }}>Agent needs permission before continuing.</div>
          <div style={{ fontSize: 11, color: C.textMuted, marginBottom: 9 }}>
            {approval.requested_action || "use workflow"}
            <br />
            {approval.risk_level ? `risk: ${approval.risk_level}` : "risk: medium"}
          </div>
          <div style={{ display: "flex", gap: 6 }}>
            <button
              type="button"
              onClick={(event) => {
                event.stopPropagation();
                onApprove?.(approval);
              }}
              style={{ flex: 1, padding: "5px 0", borderRadius: 7, border: "none", background: C.green, color: "#fff", fontSize: 11, fontWeight: 600, cursor: "pointer", ...FONT }}
            >
              Approve
            </button>
            <button
              type="button"
              onClick={(event) => {
                event.stopPropagation();
                onReject?.(approval);
              }}
              style={{ flex: 1, padding: "5px 0", borderRadius: 7, border: `1px solid ${C.borderMid}`, background: "none", color: C.textMuted, fontSize: 11, cursor: "pointer", ...FONT }}
            >
              Reject
            </button>
          </div>
        </div>
      ) : null}

      {approval?.status && approval.status !== "pending" ? (
        <div style={{ fontSize: 12, color: approval.status === "approved" ? C.green : C.textDim, textAlign: "center", padding: "4px 0" }}>
          {approval.status === "approved" ? "Approved" : "Rejected"}
        </div>
      ) : null}

      <div style={{ marginTop: "auto" }}>
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: 6,
            padding: "7px 10px",
            borderRadius: 10,
            border: `1.5px solid ${C.border}`,
            background: C.bgDeep
          }}
        >
          <input
            value={cmd}
            onChange={(event) => setCmd(event.target.value)}
            onKeyDown={(event) => {
              if (event.key === "Enter") {
                event.preventDefault();
                handleSend();
              }
            }}
            placeholder="ketik untuk menyuruh agent..."
            style={{ flex: 1, background: "none", border: "none", outline: "none", fontSize: 11, color: C.text, minWidth: 0, ...FONT }}
          />
          <button
            type="button"
            onClick={handleSend}
            disabled={!canSend || !cmd.trim() || sendState.status === "sending"}
            title={canSend ? "Kirim command ke agent ini." : "Chat backend belum tersedia."}
            style={{ background: "none", border: "none", cursor: !canSend || !cmd.trim() || sendState.status === "sending" ? "not-allowed" : "pointer", color: cmd ? C.accent : C.textDim, padding: 0, opacity: !canSend || sendState.status === "sending" ? 0.55 : 1 }}
          >
            &gt;
          </button>
        </div>
        {sendState.message ? (
          <div style={{ marginTop: 6, fontSize: 11, color: sendState.status === "error" ? C.accent : C.textMuted }}>
            {sendState.message}
          </div>
        ) : null}
        {notes.length ? (
          <div style={{ marginTop: 8, display: "flex", flexDirection: "column", gap: 6 }}>
            {notes.map((note) => (
              <div key={note.id} style={{ padding: "7px 9px", borderRadius: 8, background: C.bgDeep, border: `1px solid ${C.border}`, fontSize: 11, color: C.textMuted }}>
                {note.text}
              </div>
            ))}
          </div>
        ) : null}
      </div>
    </div>
  );
}

function Sidebar({ onOpen }) {
  const [activeId, setActiveId] = useState("create-agent");

  function handleOpen(id) {
    setActiveId(id);
    onOpen(id);
  }

  return (
    <div
      style={{
        width: 196,
        flexShrink: 0,
        background: C.bgDeep,
        borderRight: `1px solid ${C.border}`,
        display: "flex",
        flexDirection: "column",
        gap: 2,
        padding: "10px 10px 12px",
        overflowY: "auto",
        scrollbarWidth: "thin"
      }}
    >
      {NAV_ITEMS.map((item) => (
        <NavButton
          key={item.id}
          label={item.label}
          icon={item.icon}
          active={activeId === item.id}
          onClick={() => handleOpen(item.id)}
        />
      ))}
      <div style={{ flex: 1 }} />
      <NavButton
        label="Settings"
        icon="settings"
        active={activeId === "settings"}
        onClick={() => handleOpen("settings")}
      />
    </div>
  );
}

function WindowContent({ id, currentUser, panelProps = {} }) {
  switch (id) {
    case "create-agent":
      return <CreateAgentContent {...panelProps.createAgent} />;
    case "skill-panel":
      return <SkillHubContent {...panelProps.skillHub} />;
    case "import-skill":
      return <ImportSkillContent {...panelProps.importSkill} />;
    case "library-skill":
      return <LibrarySkillContent {...panelProps.librarySkill} />;
    case "library-workflow":
      return <LibraryWorkflowContent {...panelProps.libraryWorkflow} />;
    case "workflow-n8n":
      return <WorkflowN8nContent {...panelProps.workflowN8n} />;
    case "providers":
      return <ProviderApiKeyContent {...panelProps.providerApiKey} />;
    case "oauth-connections":
      return <OAuthConnectionsContent {...panelProps.oauthConnections} />;
    case "safety-center":
      return <SafetyCenterContent {...panelProps.safetyCenter} />;
    case "active-skills":
      return <ActiveSkillsContent {...panelProps.activeSkills} />;
    case "activity-log":
      return <ActivityLogContent {...panelProps.activityLog} />;
    case "agent-detail":
      return <AgentChatPanel {...panelProps.agentDetail} />;
    case "settings":
      return <SettingsControlCenterContent currentUser={currentUser} {...panelProps.settings} />;
    default:
      return null;
  }
}

export default function FigmaMakeWorkspace() {
  const router = useRouter();
  const [currentUser, setCurrentUser] = useState(null);
  const [windows, setWindows] = useState([]);
  const [zTop, setZTop] = useState(100);
  const laneRef = useRef(null);
  const laneDrag = useRef(false);
  const laneX0 = useRef(0);
  const laneScroll = useRef(0);
  const [selectedAgentId, setSelectedAgentId] = useState("");
  const [apiAgents, setApiAgents] = useState([]);
  const [apiAgentSkillsById, setApiAgentSkillsById] = useState({});
  const [apiSkillLibrary, setApiSkillLibrary] = useState([]);
  const [apiN8nWorkflows, setApiN8nWorkflows] = useState([]);
  const [apiWorkflowTemplates, setApiWorkflowTemplates] = useState([]);
  const [apiWorkflowConsents, setApiWorkflowConsents] = useState([]);
  const [apiWorkflowBindings, setApiWorkflowBindings] = useState([]);
  const [apiWorkflowExecutions, setApiWorkflowExecutions] = useState([]);
  const [apiWorkflowHistory, setApiWorkflowHistory] = useState([]);
  const [apiActivityLogs, setApiActivityLogs] = useState([]);
  const [apiAuditLogs, setApiAuditLogs] = useState([]);
  const [apiTasks, setApiTasks] = useState([]);
  const [apiApprovals, setApiApprovals] = useState([]);
  const [apiProviderSettings, setApiProviderSettings] = useState(null);
  const [apiKeyStatuses, setApiKeyStatuses] = useState([]);
  const [apiModelProviders, setApiModelProviders] = useState([]);
  const [apiRuntimeCapabilities, setApiRuntimeCapabilities] = useState([]);
  const [workspaceLoaded, setWorkspaceLoaded] = useState(false);
  const [createAgentStage, setCreateAgentStage] = useState("idle");
  const [panelErrors, setPanelErrors] = useState({
    general: "",
    createAgent: "",
    importSkill: "",
    skills: "",
    workflows: "",
    activity: "",
    audit: "",
    tasks: "",
    settings: "",
    apiKeyVault: "",
    approvals: "",
    n8n: "",
    safety: ""
  });
  const [actionBusy, setActionBusy] = useState({
    createAgent: false,
    importSkill: false,
    settings: false,
    n8n: false
  });
  const [conversationEntries, setConversationEntries] = useState([
    { role: "You", text: "bantu convert dokumen" },
    { role: "Main AI", text: "saya akan arahkan ke agent PDF" },
    { role: "You", text: "lanjut" },
    { role: "Main AI", text: "menunggu approval sebelum melanjutkan" }
  ]);
  const [orchestratorDraft, setOrchestratorDraft] = useState("");
  const [orchestratorSessionId, setOrchestratorSessionId] = useState(null);
  const [orchestratorMessages, setOrchestratorMessages] = useState([]);
  const [orchestratorSending, setOrchestratorSending] = useState(false);
  const [attachMenuOpen, setAttachMenuOpen] = useState(false);
  const [orchestratorModelId, setOrchestratorModelId] = useState("");
  const [orchestratorState, setOrchestratorState] = useState({
    status: "draft",
    message: "Siap terima command global.",
    routedToAgentId: "",
    routedToAgentName: "",
    confidence: ""
  });
  const attachMenuButtonRef = useRef(null);
  const attachMenuRef = useRef(null);

  const refreshWorkspace = useCallback(async () => {
    const results = await Promise.allSettled([
      getCurrentUser(),
      get("/agents"),
      getSkillLibrary(),
      getActivityLogs(),
      getAuditLogs(),
      getTasks(),
      getPendingApprovals(),
      getModelProviderSettings(),
      getModelProviderKeyStatuses(),
      getModelProviders(),
      getRuntimeCapabilities(),
      listN8nWorkflows(),
      listWorkflowTemplates(),
      listWorkflowConsents(),
      listWorkflowBindings(),
      listWorkflowExecutions(),
      listWorkflowExecutionHistory()
    ]);

    const [
      userResult,
      agentsResult,
      skillsResult,
      activityResult,
      auditResult,
      taskResult,
      approvalsResult,
      settingsResult,
      keyStatusResult,
      modelProvidersResult,
      runtimeCapabilitiesResult,
      n8nResult,
      templatesResult,
      consentsResult,
      bindingsResult,
      executionsResult,
      historyResult
    ] = results;

    setCurrentUser(userResult.status === "fulfilled" ? userResult.value : null);

    const agents = agentsResult.status === "fulfilled" ? normalizeCollection(agentsResult.value) : [];
    setApiAgents(agents);

    const nextAgentSkillMap = {};
    if (agents.length) {
      const skillResults = await Promise.allSettled(agents.map((agent) => getAgentActiveSkills(agent.id)));
      skillResults.forEach((skillResult, index) => {
        if (skillResult.status === "fulfilled") {
          nextAgentSkillMap[String(agents[index].id)] = normalizeArrayResponse(skillResult.value);
        }
      });
    }
    setApiAgentSkillsById(nextAgentSkillMap);

    setApiSkillLibrary(skillsResult.status === "fulfilled" ? normalizeArrayResponse(skillsResult.value) : []);
    setApiActivityLogs(activityResult.status === "fulfilled" ? normalizeCollection(activityResult.value) : []);
    setApiAuditLogs(auditResult.status === "fulfilled" ? normalizeCollection(auditResult.value) : []);
    setApiTasks(taskResult.status === "fulfilled" ? normalizeCollection(taskResult.value) : []);
    setApiApprovals(approvalsResult.status === "fulfilled" ? normalizeCollection(approvalsResult.value) : []);
    setApiProviderSettings(settingsResult.status === "fulfilled" ? normalizeObjectResponse(settingsResult.value, {}) : {});
    setApiKeyStatuses(keyStatusResult.status === "fulfilled" ? normalizeArrayResponse(keyStatusResult.value) : []);
    setApiModelProviders(modelProvidersResult.status === "fulfilled" ? normalizeArrayResponse(modelProvidersResult.value) : []);
    setApiRuntimeCapabilities(runtimeCapabilitiesResult.status === "fulfilled" ? normalizeArrayResponse(runtimeCapabilitiesResult.value) : []);
    setApiN8nWorkflows(n8nResult.status === "fulfilled" ? normalizeCollection(n8nResult.value) : []);
    setApiWorkflowTemplates(templatesResult.status === "fulfilled" ? normalizeCollection(templatesResult.value) : []);
    setApiWorkflowConsents(consentsResult.status === "fulfilled" ? normalizeCollection(consentsResult.value) : []);
    setApiWorkflowBindings(bindingsResult.status === "fulfilled" ? normalizeCollection(bindingsResult.value) : []);
    setApiWorkflowExecutions(executionsResult.status === "fulfilled" ? normalizeCollection(executionsResult.value) : []);
    setApiWorkflowHistory(historyResult.status === "fulfilled" ? normalizeCollection(historyResult.value) : []);

    setPanelErrors({
      general: agentsResult.status === "rejected" ? "Agents unavailable. Preview fallback used." : "",
      createAgent: "",
      importSkill: "",
      skills: skillsResult.status === "rejected" ? "Skill library unavailable. Preview fallback used." : "",
      workflows: n8nResult.status === "rejected" ? "n8n registry unavailable." : "",
      activity:
        activityResult.status === "rejected"
          ? activityResult.reason?.status === 404 || activityResult.reason?.status === 405
            ? "GET /logs/activity missing. Backend-required."
            : activityResult.reason?.message || "Activity log unavailable."
          : "",
      audit:
        auditResult.status === "rejected"
          ? auditResult.reason?.status === 404 || auditResult.reason?.status === 405
            ? "GET /logs/audit missing. Backend-required."
            : auditResult.reason?.message || "Audit log unavailable."
          : "",
      tasks:
        taskResult.status === "rejected"
          ? taskResult.reason?.status === 404 || taskResult.reason?.status === 405
            ? "GET /tasks missing. Backend-required."
            : taskResult.reason?.message || "Task summary unavailable."
          : "",
      settings: settingsResult.status === "rejected" || modelProvidersResult.status === "rejected" ? "Settings data unavailable. Preview fallback used." : "",
      apiKeyVault: keyStatusResult.status === "rejected" ? "API key vault unavailable. Preview fallback used." : "",
      approvals:
        approvalsResult.status === "rejected"
          ? approvalsResult.reason?.status === 404 || approvalsResult.reason?.status === 405
            ? "GET /approvals/pending missing. Backend-required."
            : approvalsResult.reason?.message || "Approval data unavailable."
          : "",
      n8n:
        n8nResult.status === "rejected"
          ? n8nResult.reason?.status === 403
            ? n8nResult.reason?.message || "Free plan blocked. Upgrade to Pro, Executive, or admin."
            : n8nResult.reason?.status === 404 || n8nResult.reason?.status === 405
              ? "n8n backend required. /n8n-workflows endpoint missing."
              : n8nResult.reason?.message || "n8n backend unavailable."
          : "",
      safety: runtimeCapabilitiesResult.status === "rejected" ? "Runtime capabilities unavailable. Backend-required panel only." : ""
    });
    setWorkspaceLoaded(true);
  }, []);

  useEffect(() => {
    refreshWorkspace().catch(() => {});
  }, [refreshWorkspace]);

  useEffect(() => {
    if (!attachMenuOpen) {
      return undefined;
    }

    function handleDocumentMouseDown(event) {
      const target = event.target;
      if (!(target instanceof Node)) {
        return;
      }

      if (attachMenuRef.current?.contains(target) || attachMenuButtonRef.current?.contains(target)) {
        return;
      }

      setAttachMenuOpen(false);
    }

    function handleDocumentKeyDown(event) {
      if (event.key === "Escape") {
        setAttachMenuOpen(false);
      }
    }

    document.addEventListener("mousedown", handleDocumentMouseDown);
    document.addEventListener("keydown", handleDocumentKeyDown);

    return () => {
      document.removeEventListener("mousedown", handleDocumentMouseDown);
      document.removeEventListener("keydown", handleDocumentKeyDown);
    };
  }, [attachMenuOpen]);

  function openWindow(id) {
    const next = zTop + 1;
    setZTop(next);
    setWindows((current) => {
      const existing = current.find((item) => item.id === id);
      if (existing) {
        return current.map((item) => (item.id === id ? { ...item, zIndex: next } : item));
      }
      return [...current, { id, zIndex: next }];
    });
  }

  function closeWindow(id) {
    setWindows((current) => current.filter((item) => item.id !== id));
  }

  function focusWindow(id) {
    const next = zTop + 1;
    setZTop(next);
    setWindows((current) => current.map((item) => (item.id === id ? { ...item, zIndex: next } : item)));
  }

  function handleLogout() {
    clearToken();
    router.replace("/login");
  }

  function laneDown(event) {
    if (!laneRef.current) return;
    laneDrag.current = true;
    laneX0.current = event.pageX - laneRef.current.getBoundingClientRect().left;
    laneScroll.current = laneRef.current.scrollLeft;
    laneRef.current.style.cursor = "grabbing";
  }

  function laneMove(event) {
    if (!laneDrag.current || !laneRef.current) return;
    const x = event.pageX - laneRef.current.getBoundingClientRect().left;
    laneRef.current.scrollLeft = laneScroll.current - (x - laneX0.current);
  }

  function laneUp() {
    laneDrag.current = false;
    if (laneRef.current) laneRef.current.style.cursor = "grab";
  }

  const visibleAgents = useMemo(() => {
    if (!workspaceLoaded) {
      return PREVIEW_AGENTS;
    }

    if (!apiAgents.length) {
      return [];
    }

    return apiAgents.map((agent, index) =>
      buildAgentView(
        agent,
        index,
        apiAgentSkillsById,
        apiActivityLogs,
        apiApprovals,
        PREVIEW_AGENTS[index % PREVIEW_AGENTS.length]
      )
    );
  }, [workspaceLoaded, apiAgents, apiAgentSkillsById, apiActivityLogs, apiApprovals]);

  const selectedAgent = useMemo(() => {
    return visibleAgents.find((agent) => agent.id === selectedAgentId) || visibleAgents[0] || null;
  }, [selectedAgentId, visibleAgents]);

  const selectedAgentSkills = useMemo(() => {
    if (!selectedAgent?.id) return [];
    return normalizeArrayResponse(apiAgentSkillsById[String(selectedAgent.id)] || []);
  }, [apiAgentSkillsById, selectedAgent]);

  useEffect(() => {
    if (!visibleAgents.length) return;
    if (!selectedAgentId) {
      setSelectedAgentId(visibleAgents[0].id);
      return;
    }
    if (!visibleAgents.some((agent) => agent.id === selectedAgentId)) {
      setSelectedAgentId(visibleAgents[0].id);
    }
  }, [selectedAgentId, visibleAgents]);

  const activityRows = useMemo(() => {
    return apiActivityLogs.length ? buildActivityRows(apiActivityLogs) : [];
  }, [apiActivityLogs]);

  const auditRows = useMemo(() => {
    return apiAuditLogs.length ? buildAuditRows(apiAuditLogs) : [];
  }, [apiAuditLogs]);

  const taskRows = useMemo(() => {
    return apiTasks.length ? buildTaskRows(apiTasks) : [];
  }, [apiTasks]);

  const approvalRows = useMemo(() => {
    return apiApprovals.length ? buildApprovalRows(apiApprovals) : [];
  }, [apiApprovals]);

  const skillRows = useMemo(() => {
    if (!workspaceLoaded) {
      return PREVIEW_SKILLS;
    }
    return apiSkillLibrary.length ? buildSkillRows(apiSkillLibrary, selectedAgent, apiAgentSkillsById) : [];
  }, [workspaceLoaded, apiSkillLibrary, selectedAgent, apiAgentSkillsById]);

  const workflowRows = useMemo(() => {
    if (apiN8nWorkflows.length) {
      return buildWorkflowRows(apiN8nWorkflows, [], [], [], [], []);
    }
    if (apiWorkflowTemplates.length) {
      return buildWorkflowRows(
        [],
        apiWorkflowTemplates,
        apiWorkflowConsents,
        apiWorkflowBindings,
        apiWorkflowExecutions,
        apiWorkflowHistory
      );
    }
    return PREVIEW_WORKFLOWS;
  }, [apiN8nWorkflows, apiWorkflowTemplates, apiWorkflowConsents, apiWorkflowBindings, apiWorkflowExecutions, apiWorkflowHistory]);

  const n8nRows = useMemo(() => {
    if (!apiN8nWorkflows.length) {
      return [];
    }
    return buildN8nRows(apiN8nWorkflows, [], [], [], [], []);
  }, [apiN8nWorkflows]);

  const currentUserView = currentUser || {
    display_name: "nama user",
    username: "nama user",
    subscription_plan: "free",
    email: "user@email.com"
  };

  const normalizedOrchestratorMessages = useMemo(() => {
    const source = Array.isArray(orchestratorMessages) ? orchestratorMessages : [];
    const userRoles = new Set(["user", "human", "you", "client"]);
    const assistantRoles = new Set(["assistant", "ai", "main_ai", "main-ai", "orchestrator"]);
    const systemRoles = new Set(["system", "status", "routing", "router", "tool", "workflow"]);

    return source
      .map((entry, index) => {
        const rawRole = safeString(entry?.role, "system").toLowerCase();
        const rawContent = safeString(
          entry?.content ?? entry?.text ?? entry?.message ?? entry?.body ?? entry?.result ?? entry?.response,
          ""
        ).trim();

        if (!rawContent) {
          return null;
        }

        let kind = "system";
        if (userRoles.has(rawRole)) {
          kind = "user";
        } else if (assistantRoles.has(rawRole)) {
          kind = "assistant";
        } else if (systemRoles.has(rawRole)) {
          kind = "system";
        }

        return {
          id: `orchestrator-${index}-${rawRole}`,
          role: kind,
          label: kind === "user" ? "You" : kind === "assistant" ? "Main AI" : "System",
          content: rawContent
        };
      })
      .filter(Boolean);
  }, [orchestratorMessages]);

  const orchestratorModelOptions = useMemo(() => {
    const providerOptions = Array.isArray(apiModelProviders) ? apiModelProviders : [];
    const mappedOptions = providerOptions
      .map((item, index) => {
        const value = String(item?.id || item?.provider || item?.name || `model-${index + 1}`);
        const label = [item?.name, item?.model_name || item?.default_model_name || item?.preferred_model]
          .filter(Boolean)
          .join(" / ") || item?.name || item?.provider || `Model ${index + 1}`;
        return { value, label };
      })
      .filter((item) => Boolean(item.value));

    if (mappedOptions.length) {
      return mappedOptions;
    }

    return [
      {
        value: "default",
        label: [apiProviderSettings?.preferred_provider || "default", apiProviderSettings?.preferred_model || "gpt-4o"]
          .filter(Boolean)
          .join(" / ")
      }
    ];
  }, [apiModelProviders, apiProviderSettings?.preferred_model, apiProviderSettings?.preferred_provider]);

  useEffect(() => {
    if (!orchestratorModelOptions.length) return;
    if (!orchestratorModelId || !orchestratorModelOptions.some((item) => item.value === orchestratorModelId)) {
      setOrchestratorModelId(orchestratorModelOptions[0].value);
    }
  }, [orchestratorModelId, orchestratorModelOptions]);

  const defaultProviderId = apiModelProviders[0]?.id || "";

  async function handleCreateAgent(payload) {
    setActionBusy((current) => ({ ...current, createAgent: true }));
    setCreateAgentStage("creating");
    setPanelErrors((current) => ({ ...current, createAgent: "" }));

    try {
      const skillMap = new Map();
      apiSkillLibrary.forEach((item, index) => {
        const id = getSkillLibraryId(item, index);
        if (id) {
          skillMap.set(id, item);
        }
      });

      const selectedSkillIds = Array.from(
        new Set((Array.isArray(payload.selectedSkillIds) ? payload.selectedSkillIds : []).map((value) => String(value || "").trim()).filter(Boolean))
      );
      const selectedSkills = selectedSkillIds.map((id) => skillMap.get(id)).filter(Boolean);
      const selectedSkillLabels = selectedSkills.map((item) => getSkillLibraryLabel(item));
      const selectedSkillSummary = selectedSkillLabels.slice(0, 3).join(", ");
      const defaultProvider =
        apiModelProviders.find((item) => {
          const id = String(item?.id || "").toLowerCase();
          const name = String(item?.name || "").toLowerCase();
          const preferred = String(apiProviderSettings?.preferred_provider || "").toLowerCase();
          return id === preferred || name.includes(preferred) || preferred.includes(name);
        }) || apiModelProviders[0] || null;

      const createPayload = {
        name: payload.name,
        slug: payload.name.toLowerCase().replace(/\s+/g, "-"),
        description: selectedSkillSummary ? `${payload.name} agent for ${selectedSkillSummary}.` : `${payload.name} agent.`,
        role_description: selectedSkillSummary ? `${payload.name} workspace agent with ${selectedSkillSummary}.` : `${payload.name} workspace agent.`,
        default_model_provider_id: payload.defaultProviderId || defaultProvider?.id || null,
        default_model_name: payload.model,
        status: payload.pinned ? "active" : "inactive",
        max_steps: 10,
        max_runtime_seconds: 300,
        max_token_budget: null,
        requires_approval_by_default: false,
        instruction_text: selectedSkillSummary
          ? `Workspace agent. Approved skills: ${selectedSkillSummary}.`
          : `Workspace agent for ${payload.name}.`
      };

      if (payload.avatarMode && payload.avatarMode !== "upload" && payload.avatarType && payload.avatarValue) {
        createPayload.avatar_type = payload.avatarType;
        createPayload.avatar_value = payload.avatarValue;
      }

      const createdAgent = await createAgent(createPayload);
      const avatarUploadRequested = payload.avatarMode === "upload" && payload.avatarFile;
      let avatarUploadFailed = false;
      let avatarUploadMessage = "";

      if (avatarUploadRequested) {
        setCreateAgentStage("uploading");
        try {
          await uploadAgentAvatar(createdAgent.id, payload.avatarFile, payload.avatarKind || null);
        } catch (uploadError) {
          avatarUploadFailed = true;
          avatarUploadMessage = uploadError?.message || "Avatar upload gagal.";
        }
      }

      let attachedCount = 0;
      let failedCount = 0;

      if (selectedSkills.length) {
        setCreateAgentStage("attaching");
        const attachResults = await Promise.allSettled(
          selectedSkills.map((skill) => attachImportedSkillToAgent(createdAgent.id, getSkillLibraryId(skill)))
        );
        attachResults.forEach((result) => {
          if (result.status === "fulfilled") {
            attachedCount += 1;
          } else {
            failedCount += 1;
          }
        });
      }

      await refreshWorkspace();
      setSelectedAgentId(String(createdAgent.id));

      if (avatarUploadFailed || failedCount) {
        const reasons = [];
        if (avatarUploadFailed) {
          reasons.push(`avatar upload failed${avatarUploadMessage ? `: ${avatarUploadMessage}` : ""}`);
        }
        if (failedCount) {
          reasons.push(`${failedCount} skill${failedCount === 1 ? "" : "s"} failed to attach`);
        }

        return {
          status: "partial",
          message: `Agent created, but ${reasons.join(" and ")}.`,
          agent: createdAgent,
          attachedCount,
          failedCount,
          avatarUploadFailed
        };
      }

      setConversationEntries((current) => [
        {
          role: "Main AI",
          text: `agent ${payload.name} saved`
        },
        ...current
      ]);

      return {
        status: "ok",
        message: "Agent saved.",
        agent: createdAgent,
        attachedCount,
        failedCount: 0
      };
    } catch (error) {
      setPanelErrors((current) => ({ ...current, createAgent: error?.message || "Create agent gagal." }));
      throw error;
    } finally {
      setActionBusy((current) => ({ ...current, createAgent: false }));
      setCreateAgentStage("idle");
    }
  }

  async function handlePreviewImport(payload) {
    return previewGithubSkillImport(payload);
  }

  async function handlePreviewCollection(payload) {
    return previewGithubSkillCollection(payload);
  }

  async function handleImportSkill(payload) {
    setActionBusy((current) => ({ ...current, importSkill: true }));
    setPanelErrors((current) => ({ ...current, importSkill: "" }));

    try {
      const result = await importSelectedGithubSkill(payload);
      setConversationEntries((current) => [
        {
          role: "Main AI",
          text: `skill imported ${safeString(result?.file_path, payload.skill_path)}`
        },
        ...current
      ]);
      await refreshWorkspace();
      return result;
    } catch (error) {
      setPanelErrors((current) => ({ ...current, importSkill: error?.message || "Import skill gagal." }));
      throw error;
    } finally {
      setActionBusy((current) => ({ ...current, importSkill: false }));
    }
  }

  async function handleApproveImport(importRecord) {
    if (!importRecord?.id) return;

    try {
      const result = await approveGithubSkillImport(importRecord.id, {
        name: safeString(importRecord?.skill_import_type || importRecord?.file_path || importRecord?.repo_url, "Imported Skill"),
        slug: safeString(importRecord?.file_path || importRecord?.repo_url, "imported-skill")
          .toLowerCase()
          .replace(/[^a-z0-9]+/g, "-")
          .replace(/^-+|-+$/g, ""),
        description: importRecord?.content_preview || "Approved from workspace",
        version_label: "workspace",
        risk_level: "medium",
        status: "active",
        review_notes: importRecord?.review_notes || "approved from workspace"
      });
      await refreshWorkspace();
      return result;
    } catch (error) {
      setPanelErrors((current) => ({ ...current, importSkill: error?.message || "Approve import gagal." }));
      throw error;
    }
  }

  async function handleRejectImport(importRecord) {
    if (!importRecord?.id) return;

    try {
      const result = await rejectGithubImport(importRecord.id, {
        review_notes: importRecord?.review_notes || "rejected from workspace"
      });
      await refreshWorkspace();
      return result;
    } catch (error) {
      setPanelErrors((current) => ({ ...current, importSkill: error?.message || "Reject import gagal." }));
      throw error;
    }
  }

  async function handleDisableImport(importRecord) {
    if (!importRecord?.id) return;

    try {
      const result = await disableGithubImport(importRecord.id);
      await refreshWorkspace();
      return result;
    } catch (error) {
      setPanelErrors((current) => ({ ...current, importSkill: error?.message || "Disable import gagal." }));
      throw error;
    }
  }

  async function handleSkillRowAction(action, row) {
    const agentId = selectedAgent?.id || visibleAgents[0]?.id || "";

    try {
      if (action === "Attach" && agentId) {
        await attachImportedSkillToAgent(agentId, row.id);
      } else if (action === "Detach" && agentId) {
        await detachImportedSkillFromAgent(agentId, row.id);
      } else if (action === "Disable") {
        await post(`/skills/${row.id}/deactivate`);
      } else {
        setConversationEntries((current) => [
          {
            role: "Main AI",
            text: `selected skill ${row.name}`
          },
          ...current
        ]);
        return;
      }

      await refreshWorkspace();
    } catch (error) {
      setPanelErrors((current) => ({ ...current, skills: error?.message || "Skill action gagal." }));
    }
  }

  async function handleWorkflowRowAction(action, row) {
    try {
      if (action === "Disable") {
        if (row?.raw?.consent?.id) {
          await revokeWorkflowConsent(row.raw.consent.id);
        } else if (row?.raw?.binding?.id) {
          await deleteWorkflowBinding(row.raw.binding.id);
        } else if (row?.raw?.id) {
          await patch(`/n8n-workflows/${row.raw.id}`, { status: "disabled" });
        }
      } else if (action === "Delete" && row?.raw?.id) {
        await remove(`/n8n-workflows/${row.raw.id}`);
      } else {
        setConversationEntries((current) => [
          {
            role: "Main AI",
            text: `selected workflow ${row.name}`
          },
          ...current
        ]);
        return;
      }

      await refreshWorkspace();
    } catch (error) {
      setPanelErrors((current) => ({ ...current, workflows: error?.message || "Workflow action gagal." }));
    }
  }

  async function handleCreateN8nWorkflow(workflowId, payload) {
    setActionBusy((current) => ({ ...current, n8n: true }));
    setPanelErrors((current) => ({ ...current, n8n: "" }));

    try {
      if (workflowId) {
        await updateN8nWorkflow(workflowId, payload);
      } else {
        await createN8nWorkflow(payload);
      }
      await refreshWorkspace();
    } catch (error) {
      setPanelErrors((current) => ({ ...current, n8n: error?.message || "n8n registry save gagal." }));
      throw error;
    } finally {
      setActionBusy((current) => ({ ...current, n8n: false }));
    }
  }

  async function handleDeleteN8nWorkflow(workflowId) {
    if (!workflowId) return;

    setActionBusy((current) => ({ ...current, n8n: true }));
    setPanelErrors((current) => ({ ...current, n8n: "" }));

    try {
      await deleteN8nWorkflow(workflowId);
      await refreshWorkspace();
    } catch (error) {
      setPanelErrors((current) => ({ ...current, n8n: error?.message || "n8n registry delete gagal." }));
      throw error;
    } finally {
      setActionBusy((current) => ({ ...current, n8n: false }));
    }
  }

  async function handleApprovalDecision(approval, decision) {
    try {
      await post(`/approvals/${approval.id}/${decision}`, {
        decision_reason: `${decision} from workspace`
      });
      await refreshWorkspace();
    } catch (error) {
      setPanelErrors((current) => ({ ...current, approvals: error?.message || "Approval action gagal." }));
    }
  }

  async function handleSaveSettings(payload) {
    setActionBusy((current) => ({ ...current, settings: true }));
    try {
      await updateModelProviderSettings(payload);
      await refreshWorkspace();
    } catch (error) {
      setPanelErrors((current) => ({ ...current, settings: error?.message || "Settings save gagal." }));
      throw error;
    } finally {
      setActionBusy((current) => ({ ...current, settings: false }));
    }
  }

  async function handleSaveApiKey(provider, apiKey) {
    await saveModelProviderApiKey(provider, { api_key: apiKey });
    await refreshWorkspace();
  }

  async function handleDeleteApiKey(provider) {
    await deleteModelProviderApiKey(provider);
    await refreshWorkspace();
  }

  async function handleAgentCardCommand(agent, commandText) {
    if (!agent?.id) {
      throw new Error("Agent target missing.");
    }

    setSelectedAgentId(String(agent.id));
    const response = await chatWithAgent(agent.id, [{ role: "user", content: commandText }], null);
    const replyPreview = safeString(response?.reply || response?.message || response?.output, "");
    setConversationEntries((current) => [
      {
        role: agent?.name || "Agent",
        text: commandText
      },
      ...(replyPreview && replyPreview !== "-" ? [{ role: `${agent?.name || "Agent"} reply`, text: replyPreview }] : []),
      ...current
    ].slice(0, 8));
    return response;
  }

  async function handleOrchestratorSubmit(event) {
    event.preventDefault();
    return submitOrchestratorMessage();
  }

  async function submitOrchestratorMessage() {
    if (orchestratorSending) {
      return;
    }

    const messageToSend = orchestratorDraft.trim();
    if (!messageToSend) {
      setOrchestratorState((current) => ({
        ...current,
        status: "draft",
        message: "Tulis command dulu."
      }));
      return;
    }

    const userMessage = { role: "user", content: messageToSend };
    const nextMessages = [...orchestratorMessages, userMessage];

    setOrchestratorMessages(nextMessages);
    setOrchestratorDraft("");
    setOrchestratorSending(true);
    setOrchestratorState((current) => ({
      ...current,
      status: "routing preview",
      message: "Main AI sedang pilih target agent..."
    }));

    try {
      const response = await orchestratorChat(messageToSend, nextMessages, orchestratorSessionId);
      const routedToAgentId = response?.routed_to_agent_id ? String(response.routed_to_agent_id) : "";
      const routedToAgentName = safeString(response?.routed_to_agent_name, "");
      const replyText = safeString(response?.reply || response?.message || response?.output, "");
      const status = safeString(response?.status, routedToAgentId ? "routed" : "preview");

      if (routedToAgentId) {
        setSelectedAgentId(routedToAgentId);
      }

      setOrchestratorSessionId(response?.session_id || orchestratorSessionId || null);
      setOrchestratorMessages((current) =>
        [
          ...current,
          ...(replyText && replyText !== "-" ? [{ role: "assistant", content: replyText }] : [])
        ].slice(-8)
      );
      setOrchestratorState({
        status,
        message: replyText && replyText !== "-" ? replyText : response?.warning || "Routing preview selesai.",
        routedToAgentId,
        routedToAgentName,
        confidence: safeString(response?.confidence, "")
      });
      setConversationEntries((current) =>
        [
          { role: "You", text: messageToSend },
          {
            role: "Main AI",
            text: routedToAgentName ? `routed to ${routedToAgentName}` : status === "fallback" ? "fallback route" : status
          },
          ...(replyText && replyText !== "-" ? [{ role: "Main AI", text: replyText }] : []),
          ...current
        ].slice(0, 8)
      );
    } catch (error) {
      setOrchestratorState({
        status: "blocked",
        message: error?.message || "Orchestrator command gagal.",
        routedToAgentId: "",
        routedToAgentName: "",
        confidence: ""
      });
    } finally {
      setOrchestratorSending(false);
    }
  }

  const panelProps = {
    createAgent: {
      onCreateAgent: handleCreateAgent,
      isSubmitting: actionBusy.createAgent,
      error: panelErrors.createAgent,
      defaultProviderId,
      providerSettings: apiProviderSettings,
      apiKeyStatuses,
      modelProviders: apiModelProviders,
      skillLibrary: apiSkillLibrary,
      skillLibraryLoading: !workspaceLoaded,
      skillLibraryError: panelErrors.skills,
      submitStage: createAgentStage
    },
    skillHub: {
      rows: skillRows,
      selectedAgent,
      selectedAgentSkills,
      error: panelErrors.skills,
      onOpenPanel: openWindow
    },
    importSkill: {
      onPreviewImport: handlePreviewImport,
      onPreviewCollection: handlePreviewCollection,
      onImportSkill: handleImportSkill,
      onApproveImport: handleApproveImport,
      onRejectImport: handleRejectImport,
      onDisableImport: handleDisableImport,
      isSubmitting: actionBusy.importSkill,
      error: panelErrors.importSkill
    },
    librarySkill: {
      rows: skillRows,
      onRowAction: handleSkillRowAction
    },
    libraryWorkflow: {
      rows: workflowRows,
      onRowAction: handleWorkflowRowAction
    },
    workflowN8n: {
      currentUser,
      rows: n8nRows,
      error: panelErrors.n8n,
      isLoading: !workspaceLoaded,
      onRefresh: refreshWorkspace,
      onSaveWorkflow: handleCreateN8nWorkflow,
      onDeleteWorkflow: handleDeleteN8nWorkflow
    },
    activityLog: {
      rows: activityRows
    },
    auditLog: {
      rows: auditRows
    },
    taskSummary: {
      rows: taskRows
    },
    providerApiKey: {
      currentUser: currentUserView,
      providerSettings: apiProviderSettings,
      apiKeyStatuses,
      modelProviders: apiModelProviders,
      onSaveSettings: handleSaveSettings,
      onSaveApiKey: handleSaveApiKey,
      onDeleteApiKey: handleDeleteApiKey,
      errors: {
        general: panelErrors.settings,
        apiKeyVault: panelErrors.apiKeyVault
      },
      onOpenPanel: openWindow
    },
    oauthConnections: {
      modelProviders: apiModelProviders,
      apiKeyStatuses,
      runtimeCapabilities: apiRuntimeCapabilities,
      errors: {
        general: panelErrors.settings
      },
      onOpenPanel: openWindow
    },
    safetyCenter: {
      runtimeCapabilities: apiRuntimeCapabilities,
      activityRows,
      auditRows,
      taskRows,
      approvalRows,
      isLoading: !workspaceLoaded,
      errors: {
        activity: panelErrors.activity,
        audit: panelErrors.audit,
        tasks: panelErrors.tasks,
        approvals: panelErrors.approvals,
        safety: panelErrors.safety
      },
      onRefresh: refreshWorkspace,
      onApproveApproval: (approval) => handleApprovalDecision(approval, "approve"),
      onRejectApproval: (approval) => handleApprovalDecision(approval, "reject"),
      onOpenPanel: openWindow
    },
    activeSkills: {
      selectedAgent,
      selectedAgentSkills,
      error: panelErrors.skills,
      onOpenPanel: openWindow
    },
    settings: {
      currentUser: currentUserView,
      providerSettings: apiProviderSettings,
      apiKeyStatuses,
      modelProviders: apiModelProviders,
      runtimeCapabilities: apiRuntimeCapabilities,
      activityRows,
      auditRows,
      taskRows,
      approvalRows,
      isLoading: !workspaceLoaded,
      workspaceLoaded,
      onSaveSettings: handleSaveSettings,
      onSaveApiKey: handleSaveApiKey,
      onDeleteApiKey: handleDeleteApiKey,
      errors: {
        general: panelErrors.settings,
        apiKeyVault: panelErrors.apiKeyVault,
        runtime: panelErrors.safety
      },
      onRefresh: refreshWorkspace,
      onApproveApproval: (approval) => handleApprovalDecision(approval, "approve"),
      onRejectApproval: (approval) => handleApprovalDecision(approval, "reject"),
      onOpenPanel: openWindow
    },
    agentDetail: {
      agent: selectedAgent,
      providerLabel:
        apiProviderSettings?.preferred_provider || apiProviderSettings?.preferred_model
          ? [apiProviderSettings?.preferred_provider, apiProviderSettings?.preferred_model].filter(Boolean).join(" / ")
          : "preview only"
    },
  };

  const user = currentUserView;

  return (
    <ProtectedRoute>
      <div style={{ width: "100vw", height: "100vh", display: "flex", flexDirection: "column", background: C.bg, overflow: "hidden", ...FONT }}>
        <div
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            padding: "11px 20px",
            borderBottom: `1px solid ${C.border}`,
            background: C.bgDeep,
            flexShrink: 0
          }}
        >
        <div style={{ display: "flex", alignItems: "center", gap: 16 }}>
            <span
              style={{
                fontSize: 21,
                color: C.text,
                ...SERIF,
                letterSpacing: "-0.02em",
                lineHeight: 1
              }}
            >
              workspace
            </span>
            <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
              <div
                style={{
                  width: 28,
                  height: 28,
                  borderRadius: "50%",
                  background: C.accentLight,
                  border: `1.5px solid ${C.borderMid}`,
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  fontSize: 13,
                  fontWeight: 600,
                  color: C.accent
                }}
              >
                U
              </div>
              <span style={{ fontSize: 13, color: C.textSub }}>{user.display_name || user.username}</span>
              <span
                style={{
                  fontSize: 10,
                  fontWeight: 700,
                  padding: "2px 8px",
                  borderRadius: 6,
                  background: C.accentLight,
                  color: C.accent,
                  letterSpacing: "0.05em",
                  lineHeight: 1
                }}
              >
                {String(user.subscription_plan || "FREE").toUpperCase()}
              </span>
            </div>
          </div>
          <button
            type="button"
            onClick={handleLogout}
              style={{
                display: "flex",
                alignItems: "center",
                gap: 7,
                padding: "7px 13px",
                borderRadius: 10,
                border: `1.5px solid ${C.border}`,
                background: "none",
              color: C.textMuted,
              fontSize: 13,
              cursor: "pointer",
              ...FONT
            }}
          >
            <span style={{ display: "flex", alignItems: "center", justifyContent: "center", width: 15, height: 15 }}>
              <MenuIcon name="logout" />
            </span>
            Logout
          </button>
        </div>

        <div style={{ flex: 1, display: "flex", minHeight: 0 }}>
          <Sidebar onOpen={openWindow} />

          <div style={{ flex: 1, display: "flex", flexDirection: "column", minWidth: 0 }}>
            <div style={{ flex: 1, padding: "18px 20px 0", minHeight: 0, display: "flex", flexDirection: "column", gap: 10 }}>
              <div style={{ fontSize: 11, fontWeight: 600, color: C.textDim, textTransform: "uppercase", letterSpacing: "0.06em" }}>
                Agents - drag to scroll -&gt;
              </div>
              <div
                ref={laneRef}
                onMouseDown={laneDown}
                onMouseMove={laneMove}
                onMouseUp={laneUp}
                onMouseLeave={laneUp}
                style={{
                  display: "flex",
                  gap: 14,
                  overflowX: "auto",
                  paddingBottom: 12,
                  cursor: "grab",
                  scrollbarWidth: "none",
                  userSelect: "none",
                  flex: 1,
                  alignItems: "flex-start"
                }}
              >
                {!workspaceLoaded ? (
                  <LoadingPanelState
                    title="Loading agents"
                    description="Ambil list agent dan active skill dari backend."
                  />
                ) : visibleAgents.length ? (
                  visibleAgents.map((agent) => (
                    <WorkspaceAgentCard
                      key={agent.id}
                      agent={agent}
                      selected={selectedAgent?.id === agent.id}
                      onSelect={() => setSelectedAgentId(agent.id)}
                      onApprove={(approval) => handleApprovalDecision(approval, "approve")}
                      onReject={(approval) => handleApprovalDecision(approval, "reject")}
                      onSendCommand={handleAgentCardCommand}
                    />
                  ))
                ) : (
                  <EmptyPanelState
                    title="No agents yet"
                    description="Buat agent dulu. Setelah itu pilih satu agent buat lihat detail dan chat."
                    actionLabel="Create agent"
                    onAction={() => openWindow("create-agent")}
                  />
                )}
              </div>
            </div>

            <div style={{ flexShrink: 0, borderTop: `1px solid ${C.border}`, background: C.bgDeep, padding: "12px 20px 14px" }}>
              <div style={{ display: "grid", gap: 10 }}>
                {normalizedOrchestratorMessages.length ? (
                  <Card style={{ background: C.card, display: "grid", gap: 10 }}>
                    <div
                      style={{
                        maxHeight: 192,
                        overflowY: "auto",
                        paddingRight: 4,
                        display: "grid",
                        gap: 8,
                        scrollbarWidth: "thin"
                      }}
                    >
                      {normalizedOrchestratorMessages.slice(-12).map((entry) => {
                        if (entry.role === "system") {
                          return (
                            <div key={entry.id} style={{ display: "flex", justifyContent: "center" }}>
                              <div
                                style={{
                                  maxWidth: "88%",
                                  padding: "6px 10px",
                                  borderRadius: 999,
                                  background: "rgba(0,0,0,0.05)",
                                  color: C.textMuted,
                                  fontSize: 11,
                                  lineHeight: 1.45,
                                  textAlign: "center",
                                  whiteSpace: "pre-wrap",
                                  ...FONT
                                }}
                              >
                                {entry.content}
                              </div>
                            </div>
                          );
                        }

                        const isUser = entry.role === "user";
                        const bubbleAlign = isUser ? "flex-end" : "flex-start";
                        const bubbleBackground = isUser ? C.accentLight : C.cardInner;
                        const bubbleBorder = isUser ? `1px solid rgba(184,92,56,0.14)` : `1px solid ${C.border}`;
                        const bubbleColor = isUser ? C.textSub : C.text;

                        return (
                          <div key={entry.id} style={{ display: "flex", justifyContent: bubbleAlign }}>
                            <div style={{ maxWidth: "74%", display: "grid", gap: 4 }}>
                              <div
                                style={{
                                  fontSize: 10,
                                  color: C.textDim,
                                  textTransform: "uppercase",
                                  letterSpacing: "0.05em",
                                  textAlign: isUser ? "right" : "left"
                                }}
                              >
                                {entry.label}
                              </div>
                              <div
                                style={{
                                  padding: "10px 12px",
                                  borderRadius: 14,
                                  border: bubbleBorder,
                                  background: bubbleBackground,
                                  color: bubbleColor,
                                  fontSize: 12,
                                  lineHeight: 1.65,
                                  whiteSpace: "pre-wrap",
                                  wordBreak: "break-word",
                                  boxShadow: isUser ? "none" : "0 1px 0 rgba(255,255,255,0.7)"
                                }}
                              >
                                {entry.content}
                              </div>
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </Card>
                ) : null}

                <Card style={{ background: C.card, display: "grid", gap: 10, position: "relative" }}>
                  {attachMenuOpen ? (
                    <div
                      ref={attachMenuRef}
                      style={{
                        position: "absolute",
                        left: 12,
                        bottom: 58,
                        zIndex: 5,
                        width: 220,
                        padding: 10,
                        borderRadius: 12,
                        border: `1px solid ${C.border}`,
                        background: C.card,
                        boxShadow: "0 12px 28px rgba(62,54,46,0.12)"
                      }}
                    >
                      {["Attach image - coming soon", "Attach file - coming soon", "Add context - coming soon"].map((item) => (
                        <button
                          key={item}
                          type="button"
                          onClick={() => setAttachMenuOpen(false)}
                          title={item}
                          style={{
                            width: "100%",
                            marginBottom: 6,
                            padding: "8px 10px",
                            borderRadius: 10,
                            border: `1px solid ${C.border}`,
                            background: C.bgDeep,
                            color: C.textDim,
                            fontSize: 12,
                            textAlign: "left",
                            cursor: "not-allowed",
                            opacity: 0.9,
                            ...FONT
                          }}
                        >
                          {item}
                        </button>
                      ))}
                    </div>
                  ) : null}

                  <form onSubmit={handleOrchestratorSubmit} style={{ display: "flex", alignItems: "center", gap: 8, minWidth: 0 }}>
                    <button
                      type="button"
                      ref={attachMenuButtonRef}
                      onClick={() => setAttachMenuOpen((value) => !value)}
                      aria-expanded={attachMenuOpen}
                      title="Attach coming soon"
                      style={{
                        width: 40,
                        height: 40,
                        borderRadius: 12,
                        border: `1px solid ${C.border}`,
                        background: C.bgDeep,
                        color: C.textMuted,
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "center",
                        cursor: "pointer",
                        flexShrink: 0
                      }}
                    >
                      <MenuIcon name="plus" />
                    </button>

                    <textarea
                      value={orchestratorDraft}
                      onChange={(event) => setOrchestratorDraft(event.target.value)}
                      onKeyDown={(event) => {
                        if (event.key !== "Enter") {
                          return;
                        }

                        if (event.shiftKey || event.nativeEvent?.isComposing || event.isComposing) {
                          return;
                        }

                        event.preventDefault();
                        if (!orchestratorDraft.trim() || orchestratorSending) {
                          return;
                        }

                        submitOrchestratorMessage();
                      }}
                      placeholder="Tulis pesan ke Main AI..."
                      rows={1}
                      style={{
                        flex: "1 1 auto",
                        minWidth: 0,
                        height: 40,
                        maxHeight: 92,
                        resize: "none",
                        padding: "10px 12px",
                        borderRadius: 12,
                        border: `1px solid ${C.borderMid}`,
                        background: C.bgDeep,
                        color: C.text,
                        fontSize: 13,
                        outline: "none",
                        lineHeight: 1.4,
                        overflowY: "auto",
                        ...FONT
                      }}
                    />

                    <select
                      value={orchestratorModelId}
                      onChange={(event) => setOrchestratorModelId(event.target.value)}
                      style={{
                        width: 156,
                        height: 40,
                        borderRadius: 999,
                        border: `1px solid ${C.border}`,
                        background: C.bgDeep,
                        color: C.textMuted,
                        fontSize: 12,
                        padding: "0 12px",
                        flexShrink: 0,
                        ...FONT
                      }}
                    >
                      {orchestratorModelOptions.map((option) => (
                        <option key={option.value} value={option.value}>
                          {option.label}
                        </option>
                      ))}
                    </select>

                    <button
                      type="button"
                      disabled
                      title="Voice input coming soon"
                      style={{
                        width: 40,
                        height: 40,
                        borderRadius: 12,
                        border: `1px solid ${C.border}`,
                        background: C.bgDeep,
                        color: C.textDim,
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "center",
                        cursor: "not-allowed",
                        flexShrink: 0,
                        opacity: 0.72
                      }}
                    >
                      mic
                    </button>

                    <button
                      type="submit"
                      disabled={!orchestratorDraft.trim() || orchestratorSending}
                      style={{
                        padding: "0 16px",
                        height: 40,
                        borderRadius: 12,
                        border: "none",
                        background: C.accent,
                        color: "#fff",
                        fontSize: 13,
                        fontWeight: 600,
                        cursor: !orchestratorDraft.trim() || orchestratorSending ? "not-allowed" : "pointer",
                        opacity: !orchestratorDraft.trim() || orchestratorSending ? 0.72 : 1,
                        flexShrink: 0,
                        ...FONT
                      }}
                    >
                      {orchestratorSending ? "Sending..." : "Send"}
                    </button>
                  </form>
                </Card>
              </div>
            </div>
          </div>
        </div>

        {windows.map((windowItem) => (
          <FloatingWindow
            key={windowItem.id}
            id={windowItem.id}
            onClose={() => closeWindow(windowItem.id)}
            onFocus={() => focusWindow(windowItem.id)}
            zIndex={windowItem.zIndex}
          >
            <WindowContent id={windowItem.id} currentUser={user} panelProps={panelProps} />
          </FloatingWindow>
        ))}
      </div>
    </ProtectedRoute>
  );
}
