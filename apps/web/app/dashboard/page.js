"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";

import AppShell from "../../components/AppShell";
import CommandInput from "../../components/CommandInput";
import FloatingCard from "../../components/FloatingCard";
import ProtectedRoute from "../../components/ProtectedRoute";
import Sidebar from "../../components/Sidebar";
import AgentChatPanel from "../../components/AgentChatPanel";
import WorkspaceChatPanel from "../../components/WorkspaceChatPanel";
import WorkflowToolsPanel from "../../components/WorkflowToolsPanel";
import {
  approveGithubSkillImport,
  attachImportedSkillToAgent,
  createAgent,
  createHandoffDraft,
  detachImportedSkillFromAgent,
  get,
  getActivityLogs,
  getAgent,
  getAgentActiveSkills,
  getCurrentUser,
  getHandoffDraft,
  getHandoffDrafts,
  getPendingApprovals,
  getModelProviders,
  getTasks,
  getSkills,
  getSkillLibrary,
  post,
  generateTaskDraft,
  previewAgentRouting,
  previewGithubSkillImport
} from "../../lib/apiClient";
import { formatDateTime, truncateText } from "../../lib/format";

const PINNED_AGENT_IDS_STORAGE_KEY = "personal-ai-agent-workspace:pinned-agent-ids";
const ACTIVE_AGENT_ID_STORAGE_KEY = "personal-ai-agent-workspace:active-agent-id";

function normalizeCollection(payload) {
  if (Array.isArray(payload)) {
    return payload;
  }

  if (Array.isArray(payload?.items)) {
    return payload.items;
  }

  if (Array.isArray(payload?.data)) {
    return payload.data;
  }

  if (Array.isArray(payload?.results)) {
    return payload.results;
  }

  return [];
}

function buildAgentId(prefix, value) {
  return `${prefix}-${value}`;
}

function buildAgentViewModel(agent, index) {
  return {
    id: String(agent?.id || buildAgentId("remote", index)),
    name: agent?.name || `agent ${index + 1}`,
    icon: agent?.icon || agent?.avatar || "",
    skill: agent?.default_skill || agent?.skill_name || "Skill belum dihubungkan",
    status: agent?.status || "inactive",
    description: agent?.description || "",
    defaultModelName: agent?.default_model_name || ""
  };
}

function buildSkillViewModel(skill, index) {
  return {
    id: String(skill?.id || buildAgentId("skill", index)),
    name: skill?.name || `Skill ${index + 1}`,
    description: skill?.description || "",
    riskLevel: skill?.risk_level || "",
    status: skill?.status || "inactive",
    sourceType: skill?.source_type || "manual",
    sourceId: skill?.source_id ? String(skill.source_id) : "",
    createdAt: skill?.created_at || ""
  };
}

function buildSkillLibraryViewModel(skill, index) {
  return {
    id: String(skill?.id || buildAgentId("library-skill", index)),
    title: skill?.title || skill?.name || `Imported skill ${index + 1}`,
    type: skill?.skill_type || "prompt_skill",
    status: skill?.status || "inactive",
    importStatus: skill?.import_status || "manual",
    securityStatus: skill?.security_status || "safe",
    riskLevel: skill?.risk_level || "low",
    warnings: Array.isArray(skill?.warnings) ? skill.warnings : [],
    resourceReferences: Array.isArray(skill?.resource_references) ? skill.resource_references : [],
    sourceUrl: skill?.source_url || "",
    sourceReference: skill?.source_reference || "",
    sourceBranch: skill?.source_branch || "",
    filePath: skill?.file_path || "",
    repoUrl: skill?.source_url || "",
    branch: skill?.source_branch || "",
    resourcePaths: Array.isArray(skill?.resource_references) ? skill.resource_references : [],
    reviewStatus:
      skill?.security_status === "blocked"
        ? "blocked"
        : skill?.security_status === "warning"
          ? "review recommended"
          : "approved",
    importedAt: skill?.created_at || "",
    createdAt: skill?.created_at || "",
    isAttachable: skill?.is_attachable !== false,
    attachBlockReason: skill?.attach_block_reason || ""
  };
}

function buildActiveAgentSkillViewModel(assignment, index) {
  return {
    id: String(assignment?.id || buildAgentId("active-skill", index)),
    skillId: String(assignment?.skill_id || assignment?.skill?.id || ""),
    isEnabled: Boolean(assignment?.is_enabled),
    createdAt: assignment?.created_at || "",
    skill: buildSkillLibraryViewModel(assignment?.skill, index)
  };
}

function buildRoutingPreviewSkillMatchViewModel(match, index) {
  return {
    id: String(match?.skill_id || buildAgentId("routing-skill", index)),
    skillId: String(match?.skill_id || ""),
    title: match?.title || `Matched skill ${index + 1}`,
    skillType: match?.skill_type || "prompt_skill",
    status: match?.status || "inactive",
    securityStatus: match?.security_status || "safe",
    matchedTerms: Array.isArray(match?.matched_terms) ? match.matched_terms : [],
    matchScore: Number(match?.match_score || 0),
    reason: match?.reason || ""
  };
}

function buildRoutingPreviewCandidateViewModel(candidate, index) {
  return {
    id: String(candidate?.agent_id || buildAgentId("routing-agent", index)),
    agentId: String(candidate?.agent_id || ""),
    name: candidate?.name || `Agent ${index + 1}`,
    slug: candidate?.slug || "",
    description: candidate?.description || "",
    roleDescription: candidate?.role_description || "",
    score: Number(candidate?.score || 0),
    reasons: Array.isArray(candidate?.reasons) ? candidate.reasons : [],
    activeSkillMatches: Array.isArray(candidate?.active_skill_matches)
      ? candidate.active_skill_matches.map((match, matchIndex) =>
          buildRoutingPreviewSkillMatchViewModel(match, matchIndex)
        )
      : []
  };
}

function buildRoutingPreviewResultViewModel(payload) {
  return {
    taskText: payload?.task_text || "",
    recommendedAgent: payload?.recommended_agent
      ? buildRoutingPreviewCandidateViewModel(payload.recommended_agent, 0)
      : null,
    candidateAgents: Array.isArray(payload?.candidate_agents)
      ? payload.candidate_agents.map((candidate, index) =>
          buildRoutingPreviewCandidateViewModel(candidate, index)
        )
      : [],
    confidence: payload?.confidence || "low",
    reasons: Array.isArray(payload?.reasons) ? payload.reasons : [],
    activeSkillMatches: Array.isArray(payload?.active_skill_matches)
      ? payload.active_skill_matches.map((match, index) =>
          buildRoutingPreviewSkillMatchViewModel(match, index)
        )
      : [],
    note: payload?.note || "Preview only, no execution."
  };
}

function buildTaskDraftRelevantSkillViewModel(skill, index) {
  return {
    id: String(skill?.skill_id || buildAgentId("task-draft-skill", index)),
    skillId: String(skill?.skill_id || ""),
    title: skill?.title || `Relevant skill ${index + 1}`,
    skillType: skill?.skill_type || "prompt_skill",
    relevanceNote: skill?.relevance_note || ""
  };
}

function buildTaskDraftResultViewModel(payload) {
  return {
    taskText: payload?.task_text || "",
    selectedAgentId: payload?.selected_agent_id ? String(payload.selected_agent_id) : null,
    selectedAgentName: payload?.selected_agent_name || null,
    confidence: payload?.confidence || "none",
    reasons: Array.isArray(payload?.reasons) ? payload.reasons : [],
    relevantSkills: Array.isArray(payload?.relevant_skills)
      ? payload.relevant_skills.map((skill, index) => buildTaskDraftRelevantSkillViewModel(skill, index))
      : [],
    taskSummary: payload?.task_summary || "",
    safetyNote:
      payload?.safety_note ||
      "This is a draft preview only. No agent has been run. No skill has been executed.",
    status: payload?.status || "draft_only",
    candidateAgents: Array.isArray(payload?.candidate_agents)
      ? payload.candidate_agents.map((candidate, index) =>
          buildRoutingPreviewCandidateViewModel(candidate, index)
        )
      : []
  };
}

function buildHandoffDraftAgentViewModel(agent) {
  if (!agent) {
    return null;
  }

  return {
    id: String(agent?.agent_id || agent?.id || ""),
    agentId: String(agent?.agent_id || agent?.id || ""),
    name: agent?.name || "Unknown agent",
    slug: agent?.slug || "",
    description: agent?.description || "",
    roleDescription: agent?.role_description || ""
  };
}

function buildHandoffDraftSkillMatchViewModel(match, index) {
  return {
    id: String(match?.skill_id || buildAgentId("handoff-skill", index)),
    skillId: String(match?.skill_id || ""),
    title: match?.title || `Matched skill ${index + 1}`,
    skillType: match?.skill_type || "prompt_skill",
    matchReason: match?.match_reason || ""
  };
}

function buildHandoffDraftViewModel(draft, index) {
  return {
    id: String(draft?.id || buildAgentId("handoff-draft", index)),
    taskText: draft?.task_text || "",
    routingConfidence: draft?.routing_confidence || "low",
    routingReasons: Array.isArray(draft?.routing_reasons) ? draft.routing_reasons : [],
    recommendedAgentId: draft?.recommended_agent_id ? String(draft.recommended_agent_id) : "",
    selectedAgentId: draft?.selected_agent_id ? String(draft.selected_agent_id) : "",
    recommendedAgent: buildHandoffDraftAgentViewModel(draft?.recommended_agent),
    selectedAgent: buildHandoffDraftAgentViewModel(draft?.selected_agent),
    activeSkillMatches: Array.isArray(draft?.active_skill_matches)
      ? draft.active_skill_matches.map((match, matchIndex) =>
          buildHandoffDraftSkillMatchViewModel(match, matchIndex)
        )
      : [],
    draftPayload: {
      taskSummary: draft?.draft_payload?.task_summary || "",
      handoffMessage: draft?.draft_payload?.handoff_message || "",
      suggestedSteps: Array.isArray(draft?.draft_payload?.suggested_steps)
        ? draft.draft_payload.suggested_steps
        : [],
      safetyNote: draft?.draft_payload?.safety_note || "Draft only, no execution."
    },
    status: draft?.status || "draft",
    createdAt: draft?.created_at || "",
    updatedAt: draft?.updated_at || ""
  };
}

function buildProviderViewModel(provider, index) {
  return {
    id: String(provider?.id || buildAgentId("provider", index)),
    name: provider?.name || `Provider ${index + 1}`,
    providerType: provider?.provider_type || "api",
    status: provider?.status || "inactive",
    defaultModel: provider?.default_model || ""
  };
}

function buildActivityLogViewModel(log, index) {
  return {
    id: String(log?.id || buildAgentId("activity", index)),
    eventType: log?.event_type || "Activity",
    message: log?.message || "No message available.",
    requestId: log?.request_id || "",
    actorType: log?.actor_type || "",
    createdAt: log?.created_at || ""
  };
}

function buildTaskSummaryViewModel(task, index) {
  return {
    id: String(task?.id || buildAgentId("task", index)),
    requestId: task?.request_id || "Unknown request",
    status: task?.status || "unknown",
    createdAt: task?.created_at || "",
    agentId: task?.agent_id || ""
  };
}

function buildPendingApprovalViewModel(approval, index) {
  return {
    id: String(approval?.id || buildAgentId("approval", index)),
    action: approval?.requested_action || "Pending approval",
    riskLevel: approval?.risk_level || "unknown",
    createdAt: approval?.created_at || "",
    status: approval?.status || "pending"
  };
}

function buildAgentPayload(form, providerOptions) {
  const trimmedName = form.name.trim();
  const selectedSkillName = form.skillName.trim();
  const workflowLabel = form.workflow.trim();
  const selectedProvider = providerOptions.find((provider) => provider.id === form.providerId) || null;
  const instructionSegments = [
    `You are ${trimmedName}.`,
    "Operate only inside the personal workspace with explicit approval for risky actions.",
    selectedSkillName
      ? `Preferred focus: ${selectedSkillName}.`
      : "Preferred focus: general workspace assistance.",
    selectedProvider?.name
      ? `Preferred provider: ${selectedProvider.name}.`
      : "Preferred provider is not selected yet.",
    `Workflow selection is still UI-only: ${workflowLabel}.`
  ];

  return {
    name: trimmedName,
    description: selectedSkillName
      ? `Created from Command Center UI with selected skill "${selectedSkillName}".`
      : "Created from Command Center UI.",
    role_description: "Personal workspace agent created from the Command Center UI.",
    default_model_provider_id: selectedProvider?.id || null,
    default_model_name: selectedProvider?.defaultModel || null,
    status: "active",
    max_steps: 10,
    max_runtime_seconds: 300,
    max_token_budget: null,
    requires_approval_by_default: true,
    instruction_text: instructionSegments.join(" ")
  };
}

function getSafeErrorMessage(error, fallbackMessage) {
  if (error instanceof Error && error.message.trim()) {
    return error.message.trim();
  }

  return fallbackMessage;
}

function normalizeName(value) {
  return value.trim().toLowerCase();
}

function getSafeCreateNotice(error) {
  const message = getSafeErrorMessage(error, "");

  if (message === "Frontend API configuration missing. Set NEXT_PUBLIC_API_BASE_URL.") {
    return message;
  }

  if (!message) {
    return "Failed to create agent.";
  }

  return truncateText(message.split("\n")[0].trim(), 140) || "Failed to create agent.";
}

function getCreateNoticeTone(message) {
  const lowerMessage = String(message || "").toLowerCase();

  if (lowerMessage.includes("created") || lowerMessage.includes("saved")) {
    return "success";
  }

  if (lowerMessage.includes("saving") || lowerMessage.includes("loading")) {
    return "loading";
  }

  if (
    lowerMessage.includes("empty") ||
    lowerMessage.includes("kosong") ||
    lowerMessage.includes("required") ||
    lowerMessage.includes("failed") ||
    lowerMessage.includes("error")
  ) {
    return "error";
  }

  return "info";
}

function getCreateNoticeStyles(tone) {
  if (tone === "success") {
    return "border-[rgba(96,112,86,0.22)] bg-[rgba(96,112,86,0.1)] text-[#607056]";
  }

  if (tone === "error") {
    return "border-[rgba(163,106,88,0.22)] bg-[rgba(163,106,88,0.1)] text-[#A36A58]";
  }

  if (tone === "loading") {
    return "border-[rgba(62,54,46,0.14)] bg-[#E5E0D3] text-[rgba(62,54,46,0.72)]";
  }

  return "border-[rgba(62,54,46,0.14)] bg-[#E5E0D3] text-[rgba(62,54,46,0.72)]";
}

function buildInitialCards() {
  return {
    create: { open: false, x: 286, y: 64, z: 20 },
    skills: { open: false, x: 360, y: 148, z: 21 },
    workflow: { open: false, x: 780, y: 148, z: 22 },
    settings: { open: false, x: 840, y: 78, z: 23 }
  };
}

function readStoredPinnedAgentIds() {
  if (typeof window === "undefined") {
    return [];
  }

  try {
    const rawValue = window.localStorage.getItem(PINNED_AGENT_IDS_STORAGE_KEY);
    if (!rawValue) {
      return [];
    }

    const parsed = JSON.parse(rawValue);
    if (!Array.isArray(parsed)) {
      return [];
    }

    return parsed
      .filter((value) => typeof value === "string" || typeof value === "number")
      .map((value) => String(value));
  } catch {
    return [];
  }
}

function writeStoredPinnedAgentIds(pinnedIds) {
  if (typeof window === "undefined") {
    return;
  }

  window.localStorage.setItem(
    PINNED_AGENT_IDS_STORAGE_KEY,
    JSON.stringify(pinnedIds.map((id) => String(id)))
  );
}

function readStoredActiveAgentId() {
  if (typeof window === "undefined") {
    return null;
  }

  const value = window.localStorage.getItem(ACTIVE_AGENT_ID_STORAGE_KEY);
  if (!value || typeof value !== "string") {
    return null;
  }

  return value.trim() ? value : null;
}

function writeStoredActiveAgentId(activeAgentId) {
  if (typeof window === "undefined") {
    return;
  }

  if (!activeAgentId) {
    window.localStorage.removeItem(ACTIVE_AGENT_ID_STORAGE_KEY);
    return;
  }

  window.localStorage.setItem(ACTIVE_AGENT_ID_STORAGE_KEY, String(activeAgentId));
}

const RECOMMENDED_SKILLS = [
  "Web Search",
  "Data Analysis",
  "Document Summarization",
  "Code Interpreter",
  "Email Assistant"
];

const SKILL_IMPORT_REQUIREMENTS = [
  {
    title: "GitHub repository URL",
    detail: "Backend preview fetch only. No execution."
  },
  {
    title: "Skill manifest file",
    detail: "Preview SKILL.md from GitHub as untrusted text."
  },
  {
    title: "Permission declaration",
    detail: "Shown as review metadata only."
  },
  {
    title: "Workflow template reference",
    detail: "n8n remains disabled in MVP."
  },
  {
    title: "Required credentials",
    detail: "Preview only. Do not save secrets here."
  },
  {
    title: "Safety review",
    detail: "Preview only. No import yet."
  }
];

const N8N_REQUIREMENTS = [
  {
    title: "n8n base URL",
    detail: "Server-side only, no raw execution path."
  },
  {
    title: "n8n API key",
    detail: "Stored server-side only."
  },
  {
    title: "Public webhook or domain",
    detail: "Only if future workflow needs it."
  },
  {
    title: "Selected credential inside n8n",
    detail: "Reference only during planning."
  },
  {
    title: "Workflow template",
    detail: "Draft template for later review."
  },
  {
    title: "Schedule or manual trigger",
    detail: "Trigger plan only."
  },
  {
    title: "Approval before activation",
    detail: "No activation without review."
  }
];

const MODEL_OPTIONS = ["model", "gpt-4.1", "gpt-4o-mini"];
const PLAN_LIMIT_NOTES = {
  free: "Free plan: up to 5 agents. n8n access is not included.",
  pro: "Pro plan: up to 10 agents. n8n access is included.",
  executive: "Executive plan: up to 50 agents. n8n access is included."
};
const N8N_PLAN_NOTES = {
  free: "Free plan is locked. Upgrade to Pro or Executive to save workflows.",
  pro: "Pro plan can save 1 workflow draft.",
  executive: "Executive plan can save up to 10 workflow drafts."
};
const INITIAL_AGENT_FORM = {
  name: "",
  icon: "",
  skillId: "",
  skillName: "",
  providerId: "",
  workflow: "use",
  pinToSidebar: true
};

const INITIAL_GITHUB_SKILL_PREVIEW_FORM = {
  repoUrl: "",
  branch: "main",
  filePath: "SKILL.md"
};

const INITIAL_GITHUB_SKILL_APPROVE_FORM = {
  name: "",
  slug: "",
  description: "",
  versionLabel: "",
  riskLevel: "medium",
  reviewNotes: "",
  status: "inactive"
};

const INITIAL_WORKFLOW_DRAFT_FORM = {
  name: "",
  description: ""
};

function getPlanLimitNote(subscriptionPlan) {
  return PLAN_LIMIT_NOTES[subscriptionPlan] || PLAN_LIMIT_NOTES.free;
}

function getN8nPlanNote(subscriptionPlan, role) {
  if (role === "admin") {
    return "Admin access bypasses n8n access and workflow limits.";
  }

  return N8N_PLAN_NOTES[subscriptionPlan] || N8N_PLAN_NOTES.free;
}

function getWorkflowStatusLabel(status) {
  if (status === "disabled") {
    return "disabled";
  }

  return "draft";
}

function buildWorkflowDraftViewModel(workflow, index) {
  return {
    id: String(workflow?.id || `workflow-${index + 1}`),
    name: workflow?.name || `Workflow ${index + 1}`,
    description: workflow?.description || "No description provided.",
    status: workflow?.status || "inactive",
    triggerType: workflow?.trigger_type || "manual",
    createdAt: workflow?.created_at || "",
    updatedAt: workflow?.updated_at || ""
  };
}

export default function DashboardPage() {
  const [workspace, setWorkspace] = useState({
    currentUser: null,
    agents: []
  });
  const [availableSkills, setAvailableSkills] = useState([]);
  const [skillLibrary, setSkillLibrary] = useState([]);
  const [availableProviders, setAvailableProviders] = useState([]);
  const [isLoadingSkills, setIsLoadingSkills] = useState(true);
  const [isLoadingSkillLibrary, setIsLoadingSkillLibrary] = useState(true);
  const [isLoadingProviders, setIsLoadingProviders] = useState(true);
  const [activityLogs, setActivityLogs] = useState([]);
  const [isLoadingActivityLogs, setIsLoadingActivityLogs] = useState(true);
  const [activityLogsNotice, setActivityLogsNotice] = useState("");
  const [taskSummaries, setTaskSummaries] = useState([]);
  const [isLoadingTaskSummaries, setIsLoadingTaskSummaries] = useState(true);
  const [taskSummariesNotice, setTaskSummariesNotice] = useState("");
  const [pendingApprovalSummaries, setPendingApprovalSummaries] = useState([]);
  const [isLoadingPendingApprovalSummaries, setIsLoadingPendingApprovalSummaries] = useState(true);
  const [pendingApprovalSummariesNotice, setPendingApprovalSummariesNotice] = useState("");
  const [activeAgentDetail, setActiveAgentDetail] = useState(null);
  const [isLoadingActiveAgentDetail, setIsLoadingActiveAgentDetail] = useState(true);
  const [activeAgentDetailNotice, setActiveAgentDetailNotice] = useState("");
  const [activeAgentSkills, setActiveAgentSkills] = useState([]);
  const [isLoadingActiveAgentSkills, setIsLoadingActiveAgentSkills] = useState(true);
  const [activeAgentSkillsNotice, setActiveAgentSkillsNotice] = useState("");
  const [skillLoadNotice, setSkillLoadNotice] = useState("");
  const [skillLibraryNotice, setSkillLibraryNotice] = useState("");
  const [selectedImportedGithubSkillId, setSelectedImportedGithubSkillId] = useState("");
  const [routingPreviewForm, setRoutingPreviewForm] = useState({ taskText: "" });
  const [routingPreviewResult, setRoutingPreviewResult] = useState(null);
  const [routingPreviewNotice, setRoutingPreviewNotice] = useState("");
  const [isPreviewingAgentMatch, setIsPreviewingAgentMatch] = useState(false);
  const [taskDraftResult, setTaskDraftResult] = useState(null);
  const [taskDraftNotice, setTaskDraftNotice] = useState("");
  const [isGeneratingTaskDraft, setIsGeneratingTaskDraft] = useState(false);
  const [handoffDrafts, setHandoffDrafts] = useState([]);
  const [isLoadingHandoffDrafts, setIsLoadingHandoffDrafts] = useState(true);
  const [handoffDraftsNotice, setHandoffDraftsNotice] = useState("");
  const [selectedHandoffDraftId, setSelectedHandoffDraftId] = useState("");
  const [selectedHandoffDraftDetail, setSelectedHandoffDraftDetail] = useState(null);
  const [isLoadingHandoffDraftDetail, setIsLoadingHandoffDraftDetail] = useState(false);
  const [handoffDraftDetailNotice, setHandoffDraftDetailNotice] = useState("");
  const [handoffDraftActionNotice, setHandoffDraftActionNotice] = useState("");
  const [isCreatingHandoffDraft, setIsCreatingHandoffDraft] = useState(false);
  const [providerLoadNotice, setProviderLoadNotice] = useState("");
  const [savedWorkflows, setSavedWorkflows] = useState([]);
  const [isLoadingSavedWorkflows, setIsLoadingSavedWorkflows] = useState(true);
  const [savedWorkflowsNotice, setSavedWorkflowsNotice] = useState("");
  const [workflowDraftForm, setWorkflowDraftForm] = useState(INITIAL_WORKFLOW_DRAFT_FORM);
  const [workflowDraftNotice, setWorkflowDraftNotice] = useState("");
  const [isSavingWorkflowDraft, setIsSavingWorkflowDraft] = useState(false);
  const [cards, setCards] = useState(buildInitialCards);
  const [zIndexSeed, setZIndexSeed] = useState(30);
  const [commandNotice, setCommandNotice] = useState("");
  const [draftPreview, setDraftPreview] = useState(null);
  const [commandResetSignal, setCommandResetSignal] = useState(0);
  const [githubSkillPreviewForm, setGithubSkillPreviewForm] = useState(
    INITIAL_GITHUB_SKILL_PREVIEW_FORM
  );
  const [githubSkillPreviewResult, setGithubSkillPreviewResult] = useState(null);
  const [githubSkillPreviewNotice, setGithubSkillPreviewNotice] = useState("");
  const [isPreviewingGithubSkill, setIsPreviewingGithubSkill] = useState(false);
  const [githubSkillApproveForm, setGithubSkillApproveForm] = useState(
    INITIAL_GITHUB_SKILL_APPROVE_FORM
  );
  const [githubSkillApproveNotice, setGithubSkillApproveNotice] = useState("");
  const [githubSkillApproveResult, setGithubSkillApproveResult] = useState(null);
  const [isApprovingGithubSkill, setIsApprovingGithubSkill] = useState(false);
  const [createNotice, setCreateNotice] = useState("");
  const [pinnedIds, setPinnedIds] = useState([]);
  const [didLoadPinnedIds, setDidLoadPinnedIds] = useState(false);
  const [activeAgentId, setActiveAgentId] = useState(null);
  const [didLoadActiveAgentId, setDidLoadActiveAgentId] = useState(false);
  const [isCreatingAgent, setIsCreatingAgent] = useState(false);
  const [selectedModel, setSelectedModel] = useState(MODEL_OPTIONS[0]);
  const [agentForm, setAgentForm] = useState(INITIAL_AGENT_FORM);
  const currentSubscriptionPlan = workspace.currentUser?.subscription_plan || "free";
  const currentUserRole = workspace.currentUser?.role || "user";
  const canUseN8n = currentUserRole === "admin" || currentSubscriptionPlan !== "free";
  const savedWorkflowLimit = currentUserRole === "admin" ? null : currentSubscriptionPlan === "pro" ? 1 : currentSubscriptionPlan === "executive" ? 10 : 0;
  const activeSavedWorkflowCount = savedWorkflows.filter((workflow) => workflow.status !== "disabled").length;
  const [skillLibraryActionNotice, setSkillLibraryActionNotice] = useState("");
  const [skillAssignmentActionId, setSkillAssignmentActionId] = useState("");
  const loadedWorkspaceRef = useRef(false);

  const loadSavedWorkflows = useCallback(
    async (options = {}) => {
      const { isMounted = true, allowAccess = canUseN8n } = options;

      if (!allowAccess) {
        if (!isMounted) {
          return;
        }

        setSavedWorkflows([]);
        setSavedWorkflowsNotice("Free plan does not include n8n access.");
        setIsLoadingSavedWorkflows(false);
        return;
      }

      try {
        const response = await get("/n8n-workflows");
        if (!isMounted) {
          return;
        }

        setSavedWorkflows(normalizeCollection(response).map(buildWorkflowDraftViewModel));
        setSavedWorkflowsNotice("");
      } catch (error) {
        if (!isMounted) {
          return;
        }

        setSavedWorkflows([]);
        setSavedWorkflowsNotice(getSafeErrorMessage(error, "Saved workflow drafts unavailable."));
      } finally {
        if (isMounted) {
          setIsLoadingSavedWorkflows(false);
        }
      }
    },
    [canUseN8n]
  );

  async function loadAgents() {
    const agentsResponse = await get("/agents");
    const normalizedAgents = normalizeCollection(agentsResponse).map(buildAgentViewModel);

    setWorkspace((current) => ({
      ...current,
      agents: normalizedAgents
    }));

    setPinnedIds((current) => {
      const availableIds = new Set(normalizedAgents.map((agent) => agent.id));
      return current.filter((id) => availableIds.has(id));
    });
    setActiveAgentId((current) => {
      if (!current) {
        return null;
      }

      const availableIds = new Set(normalizedAgents.map((agent) => agent.id));
      const isStillPinned = pinnedIds.includes(current);
      return availableIds.has(current) && isStillPinned ? current : null;
    });

    return normalizedAgents;
  }

  useEffect(() => {
    setPinnedIds(readStoredPinnedAgentIds());
    setDidLoadPinnedIds(true);
  }, []);

  useEffect(() => {
    setActiveAgentId(readStoredActiveAgentId());
    setDidLoadActiveAgentId(true);
  }, []);

  useEffect(() => {
    if (!didLoadPinnedIds) {
      return;
    }

    writeStoredPinnedAgentIds(pinnedIds);
  }, [didLoadPinnedIds, pinnedIds]);

  useEffect(() => {
    if (!didLoadActiveAgentId) {
      return;
    }

    writeStoredActiveAgentId(activeAgentId);
  }, [activeAgentId, didLoadActiveAgentId]);

  useEffect(() => {
    if (loadedWorkspaceRef.current) {
      return;
    }
    loadedWorkspaceRef.current = true;

    let isMounted = true;

    async function loadWorkspace() {
      const results = await Promise.allSettled([
        getCurrentUser(),
        get("/agents"),
        getSkills(),
        getSkillLibrary(),
        getModelProviders(),
        getHandoffDrafts({ query: { limit: 20, offset: 0 } })
      ]);

      if (!isMounted) {
        return;
      }

      const [
        currentUserResult,
        agentsResult,
        skillsResult,
        skillLibraryResult,
        providersResult,
        handoffDraftsResult
      ] = results;
      const currentUser =
        currentUserResult.status === "fulfilled" ? currentUserResult.value : null;
      const normalizedAgents =
        agentsResult.status === "fulfilled"
          ? normalizeCollection(agentsResult.value).map(buildAgentViewModel)
          : [];

      setWorkspace({
        currentUser,
        agents: normalizedAgents
      });
      setPinnedIds((current) => {
        const availableIds = new Set(normalizedAgents.map((agent) => agent.id));
        return current.filter((id) => availableIds.has(id));
      });
      setActiveAgentId((current) => {
        if (!current) {
          return null;
        }

        const availableIds = new Set(normalizedAgents.map((agent) => agent.id));
        return availableIds.has(current) ? current : null;
      });

      if (skillsResult.status === "fulfilled") {
        setAvailableSkills(normalizeCollection(skillsResult.value).map(buildSkillViewModel));
        setSkillLoadNotice("");
      } else {
        setAvailableSkills([]);
        setSkillLoadNotice("Daftar skill belum bisa dimuat. Form tetap bisa dipakai.");
      }
      setIsLoadingSkills(false);

      if (skillLibraryResult.status === "fulfilled") {
        setSkillLibrary(normalizeCollection(skillLibraryResult.value).map(buildSkillLibraryViewModel));
        setSkillLibraryNotice("");
      } else {
        setSkillLibrary([]);
        setSkillLibraryNotice("Skill library belum bisa dimuat. Preview import tetap tersedia.");
      }
      setIsLoadingSkillLibrary(false);

      if (providersResult.status === "fulfilled") {
        setAvailableProviders(normalizeCollection(providersResult.value).map(buildProviderViewModel));
        setProviderLoadNotice("");
      } else {
        setAvailableProviders([]);
        setProviderLoadNotice("Daftar provider belum bisa dimuat. Form tetap bisa dipakai.");
      }
      setIsLoadingProviders(false);

      if (handoffDraftsResult.status === "fulfilled") {
        const nextDrafts = normalizeCollection(handoffDraftsResult.value).map(buildHandoffDraftViewModel);
        setHandoffDrafts(nextDrafts);
        setHandoffDraftsNotice("");
        setSelectedHandoffDraftId((current) =>
          nextDrafts.some((draft) => draft.id === current) ? current : nextDrafts[0]?.id || ""
        );
      } else {
        setHandoffDrafts([]);
        setHandoffDraftsNotice("Draft history belum bisa dimuat.");
        setSelectedHandoffDraftId("");
      }
      setIsLoadingHandoffDrafts(false);

      if (currentUser?.role === "admin" || (currentUser?.subscription_plan || "free") !== "free") {
        await loadSavedWorkflows({
          isMounted,
          allowAccess: currentUser?.role === "admin" || (currentUser?.subscription_plan || "free") !== "free"
        });
      } else {
        setSavedWorkflows([]);
        setSavedWorkflowsNotice("Free plan does not include n8n access.");
        setIsLoadingSavedWorkflows(false);
      }
    }

    loadWorkspace();

    return () => {
      isMounted = false;
    };
  }, [loadSavedWorkflows]);

  useEffect(() => {
    let isMounted = true;

    async function loadActivityLogs() {
      try {
        const response = await getActivityLogs({ query: { limit: 5 } });

        if (!isMounted) {
          return;
        }

        setActivityLogs(
          normalizeCollection(response)
            .slice(0, 5)
            .map(buildActivityLogViewModel)
        );
        setActivityLogsNotice("");
      } catch (error) {
        if (!isMounted) {
          return;
        }

        setActivityLogs([]);
        setActivityLogsNotice("Activity logs unavailable.");
      } finally {
        if (isMounted) {
          setIsLoadingActivityLogs(false);
        }
      }
    }

    loadActivityLogs();

    return () => {
      isMounted = false;
    };
  }, []);

  useEffect(() => {
    let isMounted = true;

    async function loadSafetySummaries() {
      const results = await Promise.allSettled([
        getTasks({ query: { limit: 3 } }),
        getPendingApprovals({ query: { limit: 3 } })
      ]);

      if (!isMounted) {
        return;
      }

      const [tasksResult, approvalsResult] = results;

      if (tasksResult.status === "fulfilled") {
        setTaskSummaries(
          normalizeCollection(tasksResult.value)
            .slice(0, 3)
            .map(buildTaskSummaryViewModel)
        );
        setTaskSummariesNotice("");
      } else {
        setTaskSummaries([]);
        setTaskSummariesNotice("Tasks preview unavailable.");
      }
      setIsLoadingTaskSummaries(false);

      if (approvalsResult.status === "fulfilled") {
        setPendingApprovalSummaries(
          normalizeCollection(approvalsResult.value)
            .slice(0, 3)
            .map(buildPendingApprovalViewModel)
        );
        setPendingApprovalSummariesNotice("");
      } else {
        setPendingApprovalSummaries([]);
        setPendingApprovalSummariesNotice("Pending approvals preview unavailable.");
      }
      setIsLoadingPendingApprovalSummaries(false);
    }

    loadSafetySummaries();

    return () => {
      isMounted = false;
    };
  }, []);

  useEffect(() => {
    let isMounted = true;

    async function loadActiveAgentDetail() {
      if (!activeAgentId) {
        setActiveAgentDetail(null);
        setActiveAgentDetailNotice("");
        setIsLoadingActiveAgentDetail(false);
        return;
      }

      setIsLoadingActiveAgentDetail(true);

      try {
        const response = await getAgent(activeAgentId);

        if (!isMounted) {
          return;
        }

        setActiveAgentDetail(response || null);
        setActiveAgentDetailNotice("");
      } catch {
        if (!isMounted) {
          return;
        }

        setActiveAgentDetail(null);
        setActiveAgentDetailNotice("Agent detail unavailable");
      } finally {
        if (isMounted) {
          setIsLoadingActiveAgentDetail(false);
        }
      }
    }

    loadActiveAgentDetail();

    return () => {
      isMounted = false;
    };
  }, [activeAgentId]);

  useEffect(() => {
    let isMounted = true;

    async function loadActiveAgentSkills() {
      if (!activeAgentId) {
        setActiveAgentSkills([]);
        setActiveAgentSkillsNotice("Select an active associate to view attached skills.");
        setIsLoadingActiveAgentSkills(false);
        return;
      }

      setIsLoadingActiveAgentSkills(true);

      try {
        const response = await getAgentActiveSkills(activeAgentId);

        if (!isMounted) {
          return;
        }

        setActiveAgentSkills(
          normalizeCollection(response).map((assignment, index) => buildActiveAgentSkillViewModel(assignment, index))
        );
        setActiveAgentSkillsNotice("");
      } catch (error) {
        if (!isMounted) {
          return;
        }

        setActiveAgentSkills([]);
        setActiveAgentSkillsNotice(getSafeErrorMessage(error, "Active skills unavailable."));
      } finally {
        if (isMounted) {
          setIsLoadingActiveAgentSkills(false);
        }
      }
    }

    loadActiveAgentSkills();

    return () => {
      isMounted = false;
    };
  }, [activeAgentId]);

  const allAgents = useMemo(() => workspace.agents, [workspace.agents]);

  const pinnedAgents = useMemo(
    () => allAgents.filter((agent) => pinnedIds.includes(agent.id)),
    [allAgents, pinnedIds]
  );

  const activeAgent = useMemo(
    () => pinnedAgents.find((agent) => agent.id === activeAgentId) || null,
    [activeAgentId, pinnedAgents]
  );
  const activeAgentProviderLabel = useMemo(() => {
    if (!activeAgentDetail) {
      return "";
    }

    const providerName =
      availableProviders.find((provider) => provider.id === activeAgentDetail.default_model_provider_id)
        ?.name || "";

    if (providerName && activeAgentDetail.default_model_name) {
      return `${providerName} / ${activeAgentDetail.default_model_name}`;
    }

    return providerName || activeAgentDetail.default_model_name || "";
  }, [activeAgentDetail, availableProviders]);
  const importedGithubSkills = useMemo(() => skillLibrary, [skillLibrary]);
  const selectedImportedGithubSkill = useMemo(() => {
    if (!importedGithubSkills.length) {
      return null;
    }

    return (
      importedGithubSkills.find((item) => item.id === selectedImportedGithubSkillId) ||
      importedGithubSkills[0] ||
      null
    );
  }, [importedGithubSkills, selectedImportedGithubSkillId]);
  const workspaceStatusItems = useMemo(
    () => [
      { label: "Pinned agents", value: String(pinnedAgents.length) },
      { label: "Skills loaded", value: String(availableSkills.length) },
      { label: "Providers loaded", value: String(availableProviders.length) }
    ],
    [availableProviders.length, availableSkills.length, pinnedAgents.length]
  );

  const selectedProvider = useMemo(
    () => availableProviders.find((provider) => provider.id === agentForm.providerId) || null,
    [availableProviders, agentForm.providerId]
  );

  const selectedSkill = useMemo(
    () => availableSkills.find((skill) => skill.id === agentForm.skillId) || null,
    [availableSkills, agentForm.skillId]
  );

  const recommendedSkillMatch = useMemo(() => {
    if (!agentForm.skillName.trim()) {
      return null;
    }

    const normalizedSkillName = normalizeName(agentForm.skillName);
    return availableSkills.find((skill) => normalizeName(skill.name) === normalizedSkillName) || null;
  }, [availableSkills, agentForm.skillName]);

  const isCreateDisabled = isCreatingAgent || !agentForm.name.trim();

  useEffect(() => {
    setActiveAgentId((current) => {
      if (!current) {
        return null;
      }

      return pinnedIds.includes(current) ? current : null;
    });
  }, [pinnedIds]);

  useEffect(() => {
    if (!importedGithubSkills.length) {
      if (selectedImportedGithubSkillId) {
        setSelectedImportedGithubSkillId("");
      }
      return;
    }

    setSelectedImportedGithubSkillId((current) =>
      importedGithubSkills.some((item) => item.id === current)
        ? current
        : importedGithubSkills[0].id
    );
  }, [importedGithubSkills, selectedImportedGithubSkillId]);

  useEffect(() => {
    if (!selectedHandoffDraftId) {
      setSelectedHandoffDraftDetail(null);
      setHandoffDraftDetailNotice("");
      return;
    }

    let isMounted = true;

    async function loadHandoffDraftDetail() {
      setIsLoadingHandoffDraftDetail(true);

      try {
        const response = await getHandoffDraft(selectedHandoffDraftId);
        if (!isMounted) {
          return;
        }

        setSelectedHandoffDraftDetail(buildHandoffDraftViewModel(response));
        setHandoffDraftDetailNotice("");
      } catch (error) {
        if (!isMounted) {
          return;
        }

        setSelectedHandoffDraftDetail(null);
        setHandoffDraftDetailNotice(getSafeErrorMessage(error, "Draft detail unavailable."));
      } finally {
        if (isMounted) {
          setIsLoadingHandoffDraftDetail(false);
        }
      }
    }

    loadHandoffDraftDetail();

    return () => {
      isMounted = false;
    };
  }, [selectedHandoffDraftId]);

  function bringCardToFront(cardKey) {
    setZIndexSeed((current) => {
      const next = current + 1;
      setCards((currentCards) => ({
        ...currentCards,
        [cardKey]: {
          ...currentCards[cardKey],
          z: next
        }
      }));
      return next;
    });
  }

  function openCard(cardKey) {
    bringCardToFront(cardKey);
    setCards((current) => ({
      ...current,
      [cardKey]: {
        ...current[cardKey],
        open: true
      }
    }));
  }

  function closeCard(cardKey) {
    setCards((current) => ({
      ...current,
      [cardKey]: {
        ...current[cardKey],
        open: false
      }
    }));
  }

  function moveCard(cardKey, nextPosition) {
    setCards((current) => ({
      ...current,
      [cardKey]: {
        ...current[cardKey],
        ...nextPosition
      }
    }));
  }

  function handleSidebarAction(action) {
    if (action === "create") {
      openCard("create");
      return;
    }

    if (action === "skills") {
      openCard("skills");
      return;
    }

    if (action === "workflow") {
      openCard("workflow");
      return;
    }

    if (action === "settings") {
      openCard("settings");
    }
  }

  function togglePinned(agentId) {
    setPinnedIds((current) => {
      const isPinned = current.includes(agentId);
      const nextPinnedIds = isPinned
        ? current.filter((id) => id !== agentId)
        : [...current, agentId];

      if (isPinned && activeAgentId === agentId) {
        setActiveAgentId(null);
      }

      return nextPinnedIds;
    });
  }

  function handlePinnedAgentSelect(agentId) {
    setActiveAgentId((current) => (current === agentId ? agentId : agentId));
  }

  function handleClearActiveAssociate() {
    setActiveAgentId(null);
    setActiveAgentDetail(null);
    setActiveAgentDetailNotice("");
    setActiveAgentSkills([]);
    setActiveAgentSkillsNotice("Select an active associate to view attached skills.");
  }

  function handleAgentFormChange(field, value) {
    setAgentForm((current) => ({
      ...current,
      [field]: value
    }));
  }

  function handleSkillSelect(value) {
    if (!value) {
      setAgentForm((current) => ({
        ...current,
        skillId: "",
        skillName: ""
      }));
      return;
    }

    const selectedSkill = availableSkills.find((skill) => skill.id === value);
    setAgentForm((current) => ({
      ...current,
      skillId: value,
      skillName: selectedSkill?.name || current.skillName
    }));
  }

  function handleRecommendedSkillClick(skillName) {
    const matchedSkill =
      availableSkills.find((skill) => normalizeName(skill.name) === normalizeName(skillName)) || null;

    setAgentForm((current) => ({
      ...current,
      skillId: matchedSkill?.id || "",
      skillName
    }));
  }

  async function refreshActiveAgentSkills(targetAgentId = activeAgentId) {
    if (!targetAgentId) {
      setActiveAgentSkills([]);
      setActiveAgentSkillsNotice("Select an active associate to view attached skills.");
      return;
    }

    const response = await getAgentActiveSkills(targetAgentId);
    setActiveAgentSkills(
      normalizeCollection(response).map((assignment, index) => buildActiveAgentSkillViewModel(assignment, index))
    );
    setActiveAgentSkillsNotice("");
  }

  async function refreshImportedGithubSkills() {
    setIsLoadingSkillLibrary(true);

    try {
      const [skillsResult, skillLibraryResult] = await Promise.allSettled([
        getSkills(),
        getSkillLibrary()
      ]);

      if (skillsResult.status === "fulfilled") {
        setAvailableSkills(normalizeCollection(skillsResult.value).map(buildSkillViewModel));
        setSkillLoadNotice("");
      } else {
        setSkillLoadNotice("Daftar skill belum bisa dimuat ulang. Form tetap bisa dipakai.");
      }

      if (skillLibraryResult.status === "fulfilled") {
        setSkillLibrary(normalizeCollection(skillLibraryResult.value).map(buildSkillLibraryViewModel));
        setSkillLibraryNotice("");
      } else {
        setSkillLibraryNotice("Skill library belum bisa dimuat ulang.");
      }

    } finally {
      setIsLoadingSkillLibrary(false);
    }
  }

  async function handleAttachImportedSkill(skillId) {
    if (!activeAgentDetail?.id) {
      setSkillLibraryActionNotice("Select an active associate before attaching a skill.");
      return;
    }

    setSkillAssignmentActionId(skillId);
    setSkillLibraryActionNotice("Attaching imported skill...");

    try {
      await attachImportedSkillToAgent(activeAgentDetail.id, skillId);
      await Promise.all([
        refreshActiveAgentSkills(activeAgentDetail.id),
        refreshImportedGithubSkills()
      ]);
      setSkillLibraryActionNotice("Imported skill attached to the active associate.");
    } catch (error) {
      setSkillLibraryActionNotice(getSafeErrorMessage(error, "Unable to attach imported skill."));
    } finally {
      setSkillAssignmentActionId("");
    }
  }

  async function handleDetachImportedSkill(skillId) {
    if (!activeAgentDetail?.id) {
      setActiveAgentSkillsNotice("Select an active associate before detaching a skill.");
      return;
    }

    setSkillAssignmentActionId(skillId);
    setActiveAgentSkillsNotice("Detaching imported skill...");

    try {
      await detachImportedSkillFromAgent(activeAgentDetail.id, skillId);
      await Promise.all([
        refreshActiveAgentSkills(activeAgentDetail.id),
        refreshImportedGithubSkills()
      ]);
      setActiveAgentSkillsNotice("Imported skill detached.");
    } catch (error) {
      setActiveAgentSkillsNotice(getSafeErrorMessage(error, "Unable to detach imported skill."));
    } finally {
      setSkillAssignmentActionId("");
    }
  }

  async function refreshHandoffDrafts(options = {}) {
    const { isMounted = true } = options;

    try {
      const response = await getHandoffDrafts({ query: { limit: 20, offset: 0 } });
      if (!isMounted) {
        return [];
      }

      const nextDrafts = normalizeCollection(response).map(buildHandoffDraftViewModel);
      setHandoffDrafts(nextDrafts);
      setHandoffDraftsNotice("");
      if (nextDrafts.length === 0) {
        setSelectedHandoffDraftId("");
      } else {
        setSelectedHandoffDraftId((current) =>
          nextDrafts.some((draft) => draft.id === current) ? current : nextDrafts[0].id
        );
      }
      return nextDrafts;
    } catch (error) {
      if (!isMounted) {
        return [];
      }

      setHandoffDrafts([]);
      setHandoffDraftsNotice(getSafeErrorMessage(error, "Draft history unavailable."));
      setSelectedHandoffDraftId("");
      return [];
    } finally {
      if (isMounted) {
        setIsLoadingHandoffDrafts(false);
      }
    }
  }

  async function handleCreateHandoffDraft() {
    const taskText = routingPreviewResult?.taskText?.trim();
    if (!taskText) {
      setHandoffDraftActionNotice("Preview a task first.");
      return;
    }

    setIsCreatingHandoffDraft(true);
    setHandoffDraftActionNotice("Saving draft handoff...");

    try {
      const payload = {
        task_text: taskText
      };
      if (routingPreviewResult?.recommendedAgent?.agentId) {
        payload.selected_agent_id = routingPreviewResult.recommendedAgent.agentId;
      }

      const response = await createHandoffDraft(payload);
      const nextDraft = buildHandoffDraftViewModel(response);
      setHandoffDraftActionNotice("Draft handoff saved.");
      setSelectedHandoffDraftId(nextDraft.id);
      setSelectedHandoffDraftDetail(nextDraft);
      await refreshHandoffDrafts();
    } catch (error) {
      setHandoffDraftActionNotice(getSafeErrorMessage(error, "Failed to save draft handoff."));
    } finally {
      setIsCreatingHandoffDraft(false);
    }
  }

  function handleRoutingPreviewFieldChange(value) {
    setRoutingPreviewForm({ taskText: value });
    setRoutingPreviewNotice("");
    setRoutingPreviewResult(null);
    setTaskDraftNotice("");
    setTaskDraftResult(null);
  }

  async function handleRoutingPreviewSubmit(event) {
    event.preventDefault();

    const taskText = routingPreviewForm.taskText.trim();
    if (!taskText) {
      setRoutingPreviewNotice("Task text is required.");
      return;
    }

    setIsPreviewingAgentMatch(true);
    setRoutingPreviewNotice("Previewing agent match...");

    try {
      const response = await previewAgentRouting({ task_text: taskText });
      setRoutingPreviewResult(buildRoutingPreviewResultViewModel(response));
      setRoutingPreviewNotice("Preview ready.");
    } catch (error) {
      setRoutingPreviewResult(null);
      setRoutingPreviewNotice(getSafeErrorMessage(error, "Failed to preview agent match."));
    } finally {
      setIsPreviewingAgentMatch(false);
    }
  }

  async function handleGenerateTaskDraft() {
    const taskText = routingPreviewForm.taskText.trim();
    if (!taskText) {
      setTaskDraftNotice("Task text is required.");
      return;
    }

    setIsGeneratingTaskDraft(true);
    setTaskDraftNotice("Generating draft preview...");

    try {
      const response = await generateTaskDraft(taskText);
      setTaskDraftResult(buildTaskDraftResultViewModel(response));
      setTaskDraftNotice("Draft preview ready.");
    } catch (error) {
      setTaskDraftResult(null);
      setTaskDraftNotice(getSafeErrorMessage(error, "Failed to generate task draft."));
    } finally {
      setIsGeneratingTaskDraft(false);
    }
  }

  function handleClearTaskDraft() {
    setTaskDraftResult(null);
    setTaskDraftNotice("");
  }

  function handleGithubSkillPreviewFieldChange(field, value) {
    setGithubSkillPreviewForm((current) => ({
      ...current,
      [field]: value
    }));
    setGithubSkillPreviewNotice("");
    setGithubSkillPreviewResult(null);
  }

  async function handleGithubSkillPreviewSubmit(event) {
    event.preventDefault();

    const repoUrl = githubSkillPreviewForm.repoUrl.trim();
    const branch = githubSkillPreviewForm.branch.trim();
    const filePath = githubSkillPreviewForm.filePath.trim();

    if (!repoUrl) {
      setGithubSkillPreviewNotice("Repository URL is required.");
      return;
    }

    if (!filePath) {
      setGithubSkillPreviewNotice("File path is required.");
      return;
    }

    setIsPreviewingGithubSkill(true);
    setGithubSkillPreviewResult(null);
    setGithubSkillApproveResult(null);
    setGithubSkillApproveNotice("");
    setGithubSkillApproveForm(INITIAL_GITHUB_SKILL_APPROVE_FORM);
    setGithubSkillPreviewNotice("Fetching preview...");

    try {
      const response = await previewGithubSkillImport({
        repo_url: repoUrl,
        branch: branch || undefined,
        file_path: filePath
      });

      if (!response || typeof response !== "object") {
        throw new Error("Preview response was empty.");
      }

      setGithubSkillPreviewResult(response);
      setGithubSkillPreviewNotice("Preview loaded. Review only.");
    } catch (error) {
      setGithubSkillPreviewResult(null);
      const message = getSafeErrorMessage(error, "Preview failed.");
      setGithubSkillPreviewNotice(truncateText(message.split("\n")[0].trim(), 180));
    } finally {
      setIsPreviewingGithubSkill(false);
    }
  }

  function handleGithubSkillApproveFieldChange(field, value) {
    setGithubSkillApproveForm((current) => ({
      ...current,
      [field]: value
    }));
  }

  async function handleGithubSkillApproveSubmit(event) {
    event.preventDefault();

    if (!githubSkillPreviewResult?.id) {
      setGithubSkillApproveNotice("Preview first before importing to quarantine.");
      return;
    }

    const name = githubSkillApproveForm.name.trim();
    if (!name) {
      setGithubSkillApproveNotice("Skill name is required.");
      return;
    }

    setIsApprovingGithubSkill(true);
    setGithubSkillApproveResult(null);
    setGithubSkillApproveNotice("Importing safely...");

    try {
      const response = await approveGithubSkillImport(githubSkillPreviewResult.id, {
        name,
        slug: githubSkillApproveForm.slug.trim() || undefined,
        description: githubSkillApproveForm.description.trim() || undefined,
        version_label: githubSkillApproveForm.versionLabel.trim() || undefined,
        risk_level: githubSkillApproveForm.riskLevel,
        status: githubSkillApproveForm.status || "inactive",
        review_notes: githubSkillApproveForm.reviewNotes.trim() || undefined
      });

      setGithubSkillPreviewResult(response);
      setGithubSkillApproveResult(response);
      setGithubSkillApproveNotice(
        "Imported as inactive/quarantine-style. Not assigned to any agent and not executed."
      );
      refreshImportedGithubSkills();
    } catch (error) {
      const message = getSafeErrorMessage(error, "Unable to import preview safely.");
      if (String(message).toLowerCase().includes("skill manifest safety check failed")) {
        setGithubSkillApproveNotice(`Blocked safely: ${truncateText(message, 180)}`);
      } else {
        setGithubSkillApproveNotice(truncateText(message.split("\n")[0].trim(), 180));
      }
    } finally {
      setIsApprovingGithubSkill(false);
    }
  }

  async function handleCreateAgentSave() {
    const trimmedName = agentForm.name.trim();

    if (!trimmedName) {
      setCreateNotice("Name is required.");
      return;
    }

    setIsCreatingAgent(true);
    setCreateNotice("Saving agent profile...");

    try {
      const payload = buildAgentPayload(agentForm, availableProviders);
      const createdAgent = await createAgent(payload);
      await loadAgents();

      if (agentForm.pinToSidebar && createdAgent?.id) {
        const createdId = String(createdAgent.id);
        setPinnedIds((current) => (
          current.includes(createdId) ? current : [...current, createdId]
        ));
      }

      setAgentForm(INITIAL_AGENT_FORM);
      setCreateNotice("Agent profile created.");
    } catch (error) {
      setCreateNotice(getSafeCreateNotice(error));
    } finally {
      setIsCreatingAgent(false);
    }
  }

  async function handleWorkflowDraftSave() {
    const trimmedName = workflowDraftForm.name.trim();
    const trimmedDescription = workflowDraftForm.description.trim();

    if (!canUseN8n) {
      setWorkflowDraftNotice("Your Free plan does not include n8n access. Upgrade to Pro or Executive to save workflows.");
      return;
    }

    if (!trimmedName) {
      setWorkflowDraftNotice("Draft name is required.");
      return;
    }

    if (savedWorkflowLimit !== null && activeSavedWorkflowCount >= savedWorkflowLimit) {
      setWorkflowDraftNotice(
        currentSubscriptionPlan === "pro"
          ? "Your Pro plan allows 1 saved workflow. Upgrade to Executive to save more."
          : "Your Executive plan allows up to 10 saved workflows. Delete an existing workflow to save another."
      );
      return;
    }

    setIsSavingWorkflowDraft(true);
    setWorkflowDraftNotice("Saving workflow draft...");

    try {
      await post("/n8n-workflows", {
        name: trimmedName,
        description: trimmedDescription || null,
        workflow_external_id: null,
        trigger_type: "manual",
        webhook_url_reference: null,
        status: "inactive",
        risk_level: "low",
        approval_required: false,
        metadata: {
          source: "dashboard",
          draft_type: "manual"
        }
      });

      setWorkflowDraftForm(INITIAL_WORKFLOW_DRAFT_FORM);
      setWorkflowDraftNotice("Workflow draft saved.");
      setIsLoadingSavedWorkflows(true);
      await loadSavedWorkflows();
    } catch (error) {
      setWorkflowDraftNotice(getSafeErrorMessage(error, "Failed to save workflow draft."));
    } finally {
      setIsSavingWorkflowDraft(false);
    }
  }

  function handleCreateAgentDelete() {
    setAgentForm(INITIAL_AGENT_FORM);
    setCreateNotice("Draft cleared.");
  }

  function handleCommandSend(value) {
    const trimmedValue = value.trim();

    if (!trimmedValue) {
      return;
    }

    setDraftPreview({
      targetName: activeAgent?.name || "Hermes / Workspace",
      text: trimmedValue,
      status: "Draft only"
    });
    setCommandNotice("");
    setCommandResetSignal((current) => current + 1);
  }

  const canvasSidebar = (
    <Sidebar
      variant="workspace"
      onAction={handleSidebarAction}
      pinnedAgents={pinnedAgents}
      activeAgentId={activeAgentId}
      onPinnedAgentSelect={handlePinnedAgentSelect}
      onPinnedAgentUnpin={(agentId) => togglePinned(agentId)}
    />
  );

  const floatingCards = (
    <>
      <FloatingCard
        title="Create Agent"
        subtitle="Create agent profile only. Runtime disabled."
        open={cards.create.open}
        position={{ x: cards.create.x, y: cards.create.y }}
        zIndex={cards.create.z}
        widthClassName="w-[680px] max-w-[calc(100vw-2rem)]"
        bodyClassName="space-y-6"
        onClose={() => closeCard("create")}
        onMove={(nextPosition) => moveCard("create", nextPosition)}
        onFocus={() => bringCardToFront("create")}
        footer={
          <div className="space-y-3">
            <div className="flex gap-3">
              <button
                type="button"
                onClick={handleCreateAgentSave}
                disabled={isCreateDisabled}
                className="flex-1 rounded-[14px] bg-[#A36A58] px-4 py-3 text-[16px] font-medium text-white transition hover:bg-[#94604f] disabled:cursor-not-allowed disabled:opacity-70"
              >
                {isCreatingAgent ? "Saving..." : "Save"}
              </button>
              <button
                type="button"
                onClick={handleCreateAgentDelete}
                disabled={isCreatingAgent}
                className="flex-1 rounded-[14px] border border-[rgba(62,54,46,0.14)] bg-[#F5F1E6] px-4 py-3 text-[16px] text-[#A36A58] transition hover:bg-[#D5CFBF] disabled:cursor-not-allowed disabled:opacity-60"
              >
                Reset draft
              </button>
            </div>
            <p className="text-xs text-[rgba(62,54,46,0.6)]">
              Runtime execution is disabled. This only creates an agent profile.
            </p>
            <div className="rounded-[14px] border border-[rgba(62,54,46,0.14)] bg-[#E5E0D3] px-4 py-3 text-sm text-[rgba(62,54,46,0.72)]">
              {getPlanLimitNote(currentSubscriptionPlan)}
            </div>
            {createNotice ? (
              <div className={`rounded-[14px] border px-4 py-3 text-sm ${getCreateNoticeStyles(getCreateNoticeTone(createNotice))}`}>
                {truncateText(createNotice, 140)}
              </div>
            ) : null}
          </div>
        }
      >
        <label className="grid gap-2">
          <span className="text-[17px] font-medium text-[#3E362E]">
            Name <span className="text-[#A36A58]">*</span>
          </span>
          <input
            value={agentForm.name}
            onChange={(event) => handleAgentFormChange("name", event.target.value)}
            placeholder="Enter agent name"
            className="rounded-[14px] border border-[rgba(62,54,46,0.14)] bg-[#F5F1E6] px-4 py-3 text-[16px] text-[#3E362E] outline-none transition placeholder:text-[rgba(62,54,46,0.4)] focus:border-[#A36A58]"
          />
          <p className="text-xs text-[rgba(62,54,46,0.58)]">Required. Used as agent profile name.</p>
        </label>

        <label className="grid gap-2">
          <span className="text-[17px] font-medium text-[#3E362E]">Icon</span>
          <button
            type="button"
            onClick={() => setCreateNotice("Import icon masih UI-only di step ini.")}
            className="flex items-center justify-between rounded-[14px] border border-[rgba(62,54,46,0.14)] bg-[#F5F1E6] px-4 py-3 text-left transition hover:bg-[#D5CFBF]"
          >
            <div>
              <p className="text-[15px] text-[#3E362E]">Import icon PNG</p>
              <p className="mt-1 text-xs text-[rgba(62,54,46,0.48)]">PNG, up to 2MB</p>
            </div>
            <span className="text-[24px] text-[#A36A58]">+</span>
          </button>
        </label>

        <label className="grid gap-2">
          <span className="text-[17px] font-medium text-[#3E362E]">Skill</span>
          <select
            value={agentForm.skillId}
            onChange={(event) => handleSkillSelect(event.target.value)}
            className="rounded-[14px] border border-[rgba(62,54,46,0.14)] bg-[#F5F1E6] px-4 py-3 text-[16px] text-[#3E362E] outline-none transition focus:border-[#A36A58]"
          >
            <option value="">
              {isLoadingSkills ? "Loading skills..." : "Select a skill (UI-only)"}
            </option>
            {availableSkills.map((skill) => (
              <option key={skill.id} value={skill.id}>
                {skill.name}
              </option>
            ))}
          </select>
          <p className="text-xs text-[rgba(62,54,46,0.58)]">
            Skill preview only. No skill assignment yet.
          </p>
          {isLoadingSkills ? (
            <div className="rounded-[14px] border border-[rgba(62,54,46,0.14)] bg-[#E5E0D3] px-4 py-3 text-sm text-[rgba(62,54,46,0.64)]">
              Loading skills...
            </div>
          ) : skillLoadNotice ? (
            <div className="rounded-[14px] border border-[rgba(163,106,88,0.22)] bg-[rgba(163,106,88,0.08)] px-4 py-3 text-sm text-[#A36A58]">
              <p className="font-medium">Skills unavailable</p>
              <p className="mt-1">{truncateText(skillLoadNotice, 140)}</p>
            </div>
          ) : !availableSkills.length ? (
            <div className="rounded-[14px] border border-[rgba(62,54,46,0.14)] bg-[#E5E0D3] px-4 py-3 text-sm text-[rgba(62,54,46,0.64)]">
              No skills available yet. Agent profile can still be saved.
            </div>
          ) : null}
          {agentForm.skillName ? (
            <p className="text-xs text-[rgba(62,54,46,0.64)]">Selected skill: {agentForm.skillName}</p>
          ) : null}
        </label>
        {selectedSkill ? (
          <div className="rounded-[14px] border border-[rgba(62,54,46,0.14)] bg-[#F5F1E6] px-4 py-3 text-sm text-[rgba(62,54,46,0.72)]">
            <p className="font-medium text-[#3E362E]">{selectedSkill.name}</p>
            <p className="mt-1 text-xs text-[rgba(62,54,46,0.58)]">
              {selectedSkill.description || "No description available."}
            </p>
            <div className="mt-2 flex flex-wrap gap-2 text-[11px] uppercase tracking-[0.16em] text-[rgba(62,54,46,0.42)]">
              {selectedSkill.riskLevel ? <span>Risk: {selectedSkill.riskLevel}</span> : null}
              {selectedSkill.status ? <span>Status: {selectedSkill.status}</span> : null}
            </div>
          </div>
        ) : null}
        {!selectedSkill && recommendedSkillMatch ? (
          <div className="rounded-[14px] border border-[rgba(62,54,46,0.14)] bg-[#F5F1E6] px-4 py-3 text-sm text-[rgba(62,54,46,0.72)]">
            <p className="font-medium text-[#3E362E]">{recommendedSkillMatch.name}</p>
            <p className="mt-1 text-xs text-[rgba(62,54,46,0.58)]">
              {recommendedSkillMatch.description || "No description available."}
            </p>
            <div className="mt-2 flex flex-wrap gap-2 text-[11px] uppercase tracking-[0.16em] text-[rgba(62,54,46,0.42)]">
              {recommendedSkillMatch.riskLevel ? <span>Risk: {recommendedSkillMatch.riskLevel}</span> : null}
              {recommendedSkillMatch.status ? <span>Status: {recommendedSkillMatch.status}</span> : null}
            </div>
          </div>
        ) : null}

        <div className="grid gap-2">
          <span className="text-[17px] font-medium text-[#3E362E]">Brain / Model</span>
          <select
            value={agentForm.providerId}
            onChange={(event) => handleAgentFormChange("providerId", event.target.value)}
            className="rounded-[14px] border border-[rgba(62,54,46,0.14)] bg-[#F5F1E6] px-4 py-3 text-[16px] text-[#3E362E] outline-none transition focus:border-[#A36A58]"
          >
            <option value="">
              {isLoadingProviders ? "Loading providers..." : "No provider selected"}
            </option>
            {availableProviders.map((provider) => (
              <option key={provider.id} value={provider.id}>
                {provider.name} - {provider.providerType} - {provider.status}
              </option>
            ))}
          </select>
          <p className="text-xs text-[rgba(62,54,46,0.58)]">
            Provider selection is saved in agent profile only. No test call.
          </p>
          {isLoadingProviders ? (
            <div className="rounded-[14px] border border-[rgba(62,54,46,0.14)] bg-[#E5E0D3] px-4 py-3 text-sm text-[rgba(62,54,46,0.64)]">
              Loading providers...
            </div>
          ) : providerLoadNotice ? (
            <div className="rounded-[14px] border border-[rgba(163,106,88,0.22)] bg-[rgba(163,106,88,0.08)] px-4 py-3 text-sm text-[#A36A58]">
              <p className="font-medium">Providers unavailable</p>
              <p className="mt-1">{truncateText(providerLoadNotice, 140)}</p>
            </div>
          ) : !availableProviders.length ? (
            <div className="rounded-[14px] border border-[rgba(62,54,46,0.14)] bg-[#E5E0D3] px-4 py-3 text-sm text-[rgba(62,54,46,0.64)]">
              No provider configured yet. Agent profile can still be saved.
            </div>
          ) : null}
          {selectedProvider ? (
            <div className="rounded-[14px] border border-[rgba(62,54,46,0.14)] bg-[#F5F1E6] px-4 py-3 text-sm text-[rgba(62,54,46,0.72)]">
              <p className="font-medium text-[#3E362E]">{selectedProvider.name}</p>
              <p className="mt-1 text-xs text-[rgba(62,54,46,0.56)]">
                Type: {selectedProvider.providerType} | Status: {selectedProvider.status}
              </p>
              <p className="mt-1 text-xs text-[rgba(62,54,46,0.56)]">
                Default model: {selectedProvider.defaultModel || "Not set"}
              </p>
            </div>
          ) : null}
        </div>

        <label className="grid gap-2">
          <span className="text-[17px] font-medium text-[#3E362E]">Workflow</span>
          <select
            value={agentForm.workflow}
            onChange={(event) => handleAgentFormChange("workflow", event.target.value)}
            className="rounded-[14px] border border-[rgba(62,54,46,0.14)] bg-[#F5F1E6] px-4 py-3 text-[16px] text-[#3E362E] outline-none transition focus:border-[#A36A58]"
          >
            <option value="use">Use / Create n8n</option>
            <option value="template">Use template workflow</option>
            <option value="manual">Create/edit manually in n8n</option>
          </select>
          <p className="text-xs text-[rgba(62,54,46,0.58)]">Workflow stays preview-only. No execution yet.</p>
        </label>

        <label className="flex items-center gap-3 text-sm text-[rgba(62,54,46,0.74)]">
          <input
            type="checkbox"
            checked={agentForm.pinToSidebar}
            onChange={(event) => handleAgentFormChange("pinToSidebar", event.target.checked)}
            className="h-4 w-4 rounded border-[rgba(62,54,46,0.24)] bg-[#F5F1E6]"
          />
          Pin to sidebar
        </label>

        <div className="rounded-[16px] border border-[rgba(62,54,46,0.14)] bg-[#F5F1E6] p-4">
          <p className="text-[17px] font-medium text-[#3E362E]">Recommended Skills</p>
          <div className="scrollbar-thin mt-4 max-h-[220px] space-y-3 overflow-y-auto pr-1">
            {RECOMMENDED_SKILLS.map((skill) => (
              <button
                key={skill}
                type="button"
                onClick={() => handleRecommendedSkillClick(skill)}
                className="flex w-full items-center justify-between rounded-[14px] border border-[rgba(62,54,46,0.14)] bg-[#E5E0D3] px-4 py-3 text-left text-[15px] text-[#3E362E] transition hover:bg-[#D5CFBF]"
              >
                <span>{skill}</span>
                <span className="text-[rgba(62,54,46,0.4)]">{">"}</span>
              </button>
            ))}
          </div>
          <p className="mt-3 text-xs text-[rgba(62,54,46,0.6)]">
            Saran ini masih UI-only dan belum meng-assign skill ke backend.
          </p>
          {agentForm.skillName && !agentForm.skillId ? (
            <p className="mt-2 text-xs text-[#A36A58]">
              Suggested skill is UI-only until it matches a backend skill.
            </p>
          ) : null}
        </div>

        <div className="rounded-[16px] border border-[rgba(62,54,46,0.14)] bg-[#F5F1E6] p-4">
          <p className="text-sm font-medium text-[#3E362E]">Sidebar Pins</p>
          <div className="scrollbar-thin mt-3 max-h-[160px] space-y-2 overflow-y-auto pr-1">
            {allAgents.length ? (
              allAgents.map((agent) => (
                <div
                  key={agent.id}
                  className="flex items-center justify-between gap-3 rounded-[14px] bg-[#E5E0D3] px-3 py-2"
                >
                  <div>
                    <p className="text-sm text-[#3E362E]">{agent.name}</p>
                    <p className="text-xs text-[rgba(62,54,46,0.56)]">{agent.skill}</p>
                  </div>
                  <button
                    type="button"
                    onClick={() => togglePinned(agent.id)}
                    className={`rounded-full px-3 py-1 text-xs transition ${
                      pinnedIds.includes(agent.id)
                        ? "bg-[#A36A58] text-white"
                        : "border border-[rgba(62,54,46,0.14)] text-[rgba(62,54,46,0.72)]"
                    }`}
                  >
                    {pinnedIds.includes(agent.id) ? "Pinned" : "Pin"}
                  </button>
                </div>
              ))
            ) : (
              <p className="text-xs text-[rgba(62,54,46,0.58)]">No agents yet</p>
            )}
          </div>
        </div>
      </FloatingCard>

      <FloatingCard
        title="Import Skill"
        subtitle="Preview GitHub skill safely, then import to quarantine-style storage."
        open={cards.skills.open}
        position={{ x: cards.skills.x, y: cards.skills.y }}
        zIndex={cards.skills.z}
        widthClassName="w-[760px] max-w-[calc(100vw-2rem)]"
        bodyClassName="space-y-4"
        onClose={() => closeCard("skills")}
        onMove={(nextPosition) => moveCard("skills", nextPosition)}
        onFocus={() => bringCardToFront("skills")}
      >
        <div className="rounded-[18px] border border-[rgba(163,106,88,0.18)] bg-[rgba(163,106,88,0.08)] p-4">
          <p className="text-sm font-semibold text-[#A36A58]">Safety banner</p>
          <p className="mt-2 text-sm leading-6 text-[rgba(62,54,46,0.72)]">
            Preview only. This skill is not imported, not assigned to any agent, and not executed. Runtime remains disabled.
          </p>
          <div className="mt-3 inline-flex rounded-full border border-[rgba(163,106,88,0.2)] bg-[#F5F1E6] px-3 py-1 text-[11px] uppercase tracking-[0.14em] text-[#A36A58]">
            Preview only
          </div>
        </div>

        <form onSubmit={handleGithubSkillPreviewSubmit} className="rounded-[18px] border border-[rgba(62,54,46,0.14)] bg-[#F5F1E6] p-4">
          <div className="grid gap-3">
            <label className="grid gap-2">
              <span className="text-sm font-medium text-[#3E362E]">Repository URL</span>
              <input
                value={githubSkillPreviewForm.repoUrl}
                onChange={(event) => handleGithubSkillPreviewFieldChange("repoUrl", event.target.value)}
                placeholder="https://github.com/owner/repo"
                className="rounded-[14px] border border-[rgba(62,54,46,0.14)] bg-[#F5F1E6] px-4 py-3 text-sm text-[#3E362E] outline-none transition placeholder:text-[rgba(62,54,46,0.42)] focus:border-[#A36A58]"
              />
            </label>

            <div className="grid gap-3 sm:grid-cols-2">
              <label className="grid gap-2">
                <span className="text-sm font-medium text-[#3E362E]">Branch</span>
                <input
                  value={githubSkillPreviewForm.branch}
                  onChange={(event) => handleGithubSkillPreviewFieldChange("branch", event.target.value)}
                  placeholder="main"
                  className="rounded-[14px] border border-[rgba(62,54,46,0.14)] bg-[#F5F1E6] px-4 py-3 text-sm text-[#3E362E] outline-none transition placeholder:text-[rgba(62,54,46,0.42)] focus:border-[#A36A58]"
                />
              </label>

              <label className="grid gap-2">
                <span className="text-sm font-medium text-[#3E362E]">File path</span>
                <input
                  value={githubSkillPreviewForm.filePath}
                  onChange={(event) => handleGithubSkillPreviewFieldChange("filePath", event.target.value)}
                  placeholder="SKILL.md"
                  className="rounded-[14px] border border-[rgba(62,54,46,0.14)] bg-[#F5F1E6] px-4 py-3 text-sm text-[#3E362E] outline-none transition placeholder:text-[rgba(62,54,46,0.42)] focus:border-[#A36A58]"
                />
                <p className="text-xs leading-6 text-[rgba(62,54,46,0.58)]">
                  Isi path file SKILL.md dari root repo. Contoh: skills/pdf/SKILL.md, skills/docx/SKILL.md, skills/canvas-design/SKILL.md. Jangan isi URL GitHub penuh atau raw URL.
                </p>
              </label>
            </div>
          </div>

          <div className="mt-4 flex flex-wrap items-center justify-between gap-3">
            <p className="text-xs leading-6 text-[rgba(62,54,46,0.62)]">
              Backend preview only. GitHub text is fetched through the API and stays untrusted.
            </p>
            <button
              type="submit"
              disabled={isPreviewingGithubSkill}
              className="rounded-full bg-[#A36A58] px-4 py-2.5 text-sm font-medium text-white transition hover:bg-[#94604f] disabled:cursor-not-allowed disabled:opacity-70"
            >
              {isPreviewingGithubSkill ? "Fetching preview..." : "Preview GitHub Skill"}
            </button>
          </div>

          {githubSkillPreviewNotice ? (
            <div className="mt-4 rounded-[14px] border border-[rgba(62,54,46,0.14)] bg-[#E5E0D3] px-4 py-3 text-sm text-[rgba(62,54,46,0.72)]">
              {truncateText(githubSkillPreviewNotice, 180)}
            </div>
          ) : null}
        </form>

        <div className="grid gap-3 sm:grid-cols-2">
          {SKILL_IMPORT_REQUIREMENTS.map((item) => (
            <div
              key={item.title}
              className="rounded-[16px] border border-[rgba(62,54,46,0.14)] bg-[#F5F1E6] px-4 py-3"
            >
              <p className="text-sm font-semibold text-[#3E362E]">{item.title}</p>
              <p className="mt-1 text-xs leading-6 text-[rgba(62,54,46,0.62)]">{item.detail}</p>
            </div>
          ))}
        </div>

        {githubSkillPreviewResult ? (
          <div className="space-y-4 rounded-[18px] border border-[rgba(62,54,46,0.14)] bg-[#E5E0D3] p-4">
            <div className="flex items-start justify-between gap-3">
              <div className="min-w-0">
                <p className="text-[11px] uppercase tracking-[0.18em] text-[rgba(62,54,46,0.56)]">
                  Preview result
                </p>
                <p className="mt-1 text-lg font-semibold text-[#3E362E]">
                  Import preview ID
                </p>
                <p className="mt-2 break-words text-sm text-[rgba(62,54,46,0.68)]">
                  {githubSkillPreviewResult.id || "-"}
                </p>
              </div>
              <span className="rounded-full border border-[rgba(163,106,88,0.2)] bg-[rgba(163,106,88,0.1)] px-3 py-1 text-[11px] uppercase tracking-[0.14em] text-[#A36A58]">
                {githubSkillPreviewResult.status || "preview"}
              </span>
            </div>

            <div className="grid gap-3 sm:grid-cols-2">
              {[
                { label: "Repository URL", value: githubSkillPreviewResult.repo_url },
                { label: "Branch", value: githubSkillPreviewResult.branch || "-" },
                { label: "File path", value: githubSkillPreviewResult.file_path || "-" },
                {
                  label: "Import type",
                  value:
                    githubSkillPreviewResult.skill_import_type ||
                    githubSkillPreviewResult.import_type ||
                    "markdown_instruction"
                },
                { label: "Created at", value: formatDateTime(githubSkillPreviewResult.created_at) },
                { label: "Updated at", value: formatDateTime(githubSkillPreviewResult.updated_at) }
              ].map((item) => (
                <div
                  key={item.label}
                  className="rounded-[16px] border border-[rgba(62,54,46,0.14)] bg-[#F5F1E6] px-4 py-3"
                >
                  <p className="text-[11px] uppercase tracking-[0.16em] text-[rgba(62,54,46,0.54)]">
                    {item.label}
                  </p>
                  <p className="mt-1 break-words text-sm leading-6 text-[#3E362E]">{item.value || "-"}</p>
                </div>
              ))}
            </div>

            <div className="rounded-[16px] border border-[rgba(62,54,46,0.14)] bg-[#F5F1E6] p-4">
              <div className="flex items-start justify-between gap-3">
                <div>
                  <p className="text-sm font-medium text-[#3E362E]">Content preview</p>
                  <p className="mt-1 text-xs text-[rgba(62,54,46,0.58)]">
                    Treat this as untrusted text.
                  </p>
                </div>
                <span className="rounded-full border border-[rgba(62,54,46,0.14)] bg-[#E5E0D3] px-2.5 py-1 text-[10px] uppercase tracking-[0.14em] text-[rgba(62,54,46,0.68)]">
                  Read-only
                </span>
              </div>
              <pre className="scrollbar-thin mt-3 max-h-[280px] overflow-auto whitespace-pre-wrap break-words rounded-[14px] border border-[rgba(62,54,46,0.14)] bg-[#FAF7EF] p-4 text-sm leading-6 text-[#3E362E]">
                {githubSkillPreviewResult.content_preview || "No preview content returned."}
              </pre>
              <div className="mt-4 grid gap-3 sm:grid-cols-2">
                {[
                  {
                    label: "Detected resources",
                    value:
                      githubSkillPreviewResult.resource_paths?.length > 0
                        ? githubSkillPreviewResult.resource_paths.join(", ")
                        : "None detected"
                  },
                  {
                    label: "Safety note",
                    value: "Resources are detected only. Nothing is fetched or executed."
                  }
                ].map((item) => (
                  <div
                    key={item.label}
                    className="rounded-[14px] border border-[rgba(62,54,46,0.12)] bg-white px-4 py-3"
                  >
                    <p className="text-[11px] uppercase tracking-[0.16em] text-[rgba(62,54,46,0.54)]">
                      {item.label}
                    </p>
                    <p className="mt-1 break-words text-sm leading-6 text-[#3E362E]">
                      {item.value}
                    </p>
                  </div>
                ))}
              </div>
              {Array.isArray(githubSkillPreviewResult.inspection_warnings) &&
              githubSkillPreviewResult.inspection_warnings.length > 0 ? (
                <div className="mt-4 rounded-[14px] border border-[rgba(163,106,88,0.18)] bg-[rgba(163,106,88,0.08)] px-4 py-3">
                  <p className="text-xs uppercase tracking-[0.16em] text-[rgba(62,54,46,0.54)]">
                    Warnings
                  </p>
                  <ul className="mt-2 space-y-1 text-sm leading-6 text-[#3E362E]">
                    {githubSkillPreviewResult.inspection_warnings.map((warning, index) => (
                      <li key={`${warning}-${index}`}>{warning}</li>
                    ))}
                  </ul>
                </div>
              ) : null}
            </div>
            <p className="text-xs leading-6 text-[rgba(62,54,46,0.58)]">
              Kalau di GitHub kamu membuka: repo → skills → canvas-design → SKILL.md. Maka file path: skills/canvas-design/SKILL.md.
            </p>

            <form onSubmit={handleGithubSkillApproveSubmit} className="rounded-[18px] border border-[rgba(62,54,46,0.14)] bg-[#F5F1E6] p-4">
              <div className="flex items-start justify-between gap-3">
                <div>
                  <p className="text-sm font-semibold text-[#3E362E]">Review before import</p>
                  <p className="mt-1 text-xs text-[rgba(62,54,46,0.58)]">
                    Imported skill is saved inactive/quarantine-style only.
                  </p>
                </div>
                <span className="rounded-full border border-[rgba(163,106,88,0.2)] bg-[rgba(163,106,88,0.1)] px-3 py-1 text-[11px] uppercase tracking-[0.14em] text-[#A36A58]">
                  Inactive only
                </span>
              </div>

              <div className="mt-4 grid gap-3">
                <div className="grid gap-3 sm:grid-cols-2">
                  <label className="grid gap-2">
                    <span className="text-sm font-medium text-[#3E362E]">
                      Name <span className="text-[#A36A58]">*</span>
                    </span>
                    <input
                      value={githubSkillApproveForm.name}
                      onChange={(event) => handleGithubSkillApproveFieldChange("name", event.target.value)}
                      placeholder="Enter skill name"
                      className="rounded-[14px] border border-[rgba(62,54,46,0.14)] bg-[#F5F1E6] px-4 py-3 text-sm text-[#3E362E] outline-none transition placeholder:text-[rgba(62,54,46,0.42)] focus:border-[#A36A58]"
                    />
                  </label>

                  <label className="grid gap-2">
                    <span className="text-sm font-medium text-[#3E362E]">Slug</span>
                    <input
                      value={githubSkillApproveForm.slug}
                      onChange={(event) => handleGithubSkillApproveFieldChange("slug", event.target.value)}
                      placeholder="skill-slug"
                      className="rounded-[14px] border border-[rgba(62,54,46,0.14)] bg-[#F5F1E6] px-4 py-3 text-sm text-[#3E362E] outline-none transition placeholder:text-[rgba(62,54,46,0.42)] focus:border-[#A36A58]"
                    />
                  </label>
                </div>

                <label className="grid gap-2">
                  <span className="text-sm font-medium text-[#3E362E]">Description</span>
                  <textarea
                    rows={3}
                    value={githubSkillApproveForm.description}
                    onChange={(event) => handleGithubSkillApproveFieldChange("description", event.target.value)}
                    placeholder="Optional description for the imported skill."
                    className="resize-none rounded-[14px] border border-[rgba(62,54,46,0.14)] bg-[#F5F1E6] px-4 py-3 text-sm text-[#3E362E] outline-none transition placeholder:text-[rgba(62,54,46,0.42)] focus:border-[#A36A58]"
                  />
                </label>

                <div className="grid gap-3 sm:grid-cols-2">
                  <label className="grid gap-2">
                    <span className="text-sm font-medium text-[#3E362E]">Version label</span>
                    <input
                      value={githubSkillApproveForm.versionLabel}
                      onChange={(event) =>
                        handleGithubSkillApproveFieldChange("versionLabel", event.target.value)
                      }
                      placeholder="1.0.0"
                      className="rounded-[14px] border border-[rgba(62,54,46,0.14)] bg-[#F5F1E6] px-4 py-3 text-sm text-[#3E362E] outline-none transition placeholder:text-[rgba(62,54,46,0.42)] focus:border-[#A36A58]"
                    />
                  </label>

                  <label className="grid gap-2">
                    <span className="text-sm font-medium text-[#3E362E]">Risk level</span>
                    <select
                      value={githubSkillApproveForm.riskLevel}
                      onChange={(event) => handleGithubSkillApproveFieldChange("riskLevel", event.target.value)}
                      className="rounded-[14px] border border-[rgba(62,54,46,0.14)] bg-[#F5F1E6] px-4 py-3 text-sm text-[#3E362E] outline-none transition focus:border-[#A36A58]"
                    >
                      <option value="low">low</option>
                      <option value="medium">medium</option>
                      <option value="high">high</option>
                    </select>
                  </label>
                </div>

                <label className="grid gap-2">
                  <span className="text-sm font-medium text-[#3E362E]">Review notes</span>
                  <textarea
                    rows={3}
                    value={githubSkillApproveForm.reviewNotes}
                    onChange={(event) =>
                      handleGithubSkillApproveFieldChange("reviewNotes", event.target.value)
                    }
                    placeholder="Optional review notes."
                    className="resize-none rounded-[14px] border border-[rgba(62,54,46,0.14)] bg-[#F5F1E6] px-4 py-3 text-sm text-[#3E362E] outline-none transition placeholder:text-[rgba(62,54,46,0.42)] focus:border-[#A36A58]"
                  />
                </label>

                <div className="rounded-[14px] border border-[rgba(62,54,46,0.14)] bg-[#E5E0D3] px-4 py-3">
                  <p className="text-xs uppercase tracking-[0.16em] text-[rgba(62,54,46,0.52)]">
                    Locked status
                  </p>
                  <p className="mt-1 text-sm font-medium text-[#3E362E]">{githubSkillApproveForm.status}</p>
                  <p className="mt-1 text-xs text-[rgba(62,54,46,0.58)]">
                    Frontend sends inactive only. Active state is not allowed here.
                  </p>
                </div>
              </div>

              <div className="mt-4 flex flex-wrap items-center justify-between gap-3">
                <p className="text-xs leading-6 text-[rgba(62,54,46,0.62)]">
                  Import to quarantine-style storage only. No agent assignment. No runtime.
                </p>
                <button
                  type="submit"
                  disabled={isApprovingGithubSkill}
                  className="rounded-full bg-[#A36A58] px-4 py-2.5 text-sm font-medium text-white transition hover:bg-[#94604f] disabled:cursor-not-allowed disabled:opacity-70"
                >
                  {isApprovingGithubSkill ? "Importing safely..." : "Import to Quarantine"}
                </button>
              </div>

              {githubSkillApproveNotice ? (
                <div className="mt-4 rounded-[14px] border border-[rgba(62,54,46,0.14)] bg-[#E5E0D3] px-4 py-3 text-sm text-[rgba(62,54,46,0.72)]">
                  {truncateText(githubSkillApproveNotice, 180)}
                </div>
              ) : null}
            </form>

            {githubSkillApproveResult ? (
              <div className="rounded-[18px] border border-[rgba(96,112,86,0.18)] bg-[rgba(96,112,86,0.08)] p-4">
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <p className="text-sm font-semibold text-[#607056]">Import success</p>
                    <p className="mt-1 text-sm leading-6 text-[rgba(62,54,46,0.72)]">
                      Imported as inactive/quarantine-style. Not assigned to any agent and not executed.
                    </p>
                  </div>
                  <span className="rounded-full border border-[rgba(96,112,86,0.2)] bg-[rgba(96,112,86,0.12)] px-3 py-1 text-[11px] uppercase tracking-[0.14em] text-[#607056]">
                    {githubSkillApproveResult.status || "imported"}
                  </span>
                </div>

                <div className="mt-4 grid gap-3 sm:grid-cols-2">
                  {[
                    { label: "Import ID", value: githubSkillApproveResult.id },
                    { label: "Repo URL", value: githubSkillApproveResult.repo_url },
                    { label: "Branch", value: githubSkillApproveResult.branch || "-" },
                    { label: "File path", value: githubSkillApproveResult.file_path || "-" },
                    { label: "Status", value: githubSkillApproveResult.status || "-" },
                    { label: "Content preview", value: "Available above as untrusted text." }
                  ].map((item) => (
                    <div
                      key={item.label}
                      className="rounded-[16px] border border-[rgba(62,54,46,0.14)] bg-[#F5F1E6] px-4 py-3"
                    >
                      <p className="text-[11px] uppercase tracking-[0.16em] text-[rgba(62,54,46,0.54)]">
                        {item.label}
                      </p>
                      <p className="mt-1 break-words text-sm leading-6 text-[#3E362E]">{item.value || "-"}</p>
                    </div>
                  ))}
                </div>
              </div>
            ) : null}

            <section className="space-y-4 rounded-[18px] border border-[rgba(62,54,46,0.14)] bg-[#E5E0D3] p-4">
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div className="min-w-0">
                  <p className="text-sm font-semibold text-[#3E362E]">Skill Library</p>
                  <p className="mt-1 text-xs leading-6 text-[rgba(62,54,46,0.62)]">
                    Imported GitHub skills stay inactive in quarantine-style storage. Attaching a skill makes it active on an agent, not executable.
                  </p>
                </div>
                <span className="rounded-full border border-[rgba(62,54,46,0.14)] bg-[#F5F1E6] px-3 py-1 text-[11px] uppercase tracking-[0.14em] text-[rgba(62,54,46,0.72)]">
                  {importedGithubSkills.length} items
                </span>
              </div>

              {skillLibraryNotice ? (
                <div className="rounded-[14px] border border-[rgba(163,106,88,0.18)] bg-[rgba(163,106,88,0.08)] px-4 py-3 text-sm text-[rgba(62,54,46,0.72)]">
                  <div className="flex flex-wrap items-center justify-between gap-3">
                    <p>{truncateText(skillLibraryNotice, 180)}</p>
                    <button
                      type="button"
                      onClick={() => refreshImportedGithubSkills()}
                      className="rounded-full border border-[rgba(62,54,46,0.14)] bg-[#F5F1E6] px-3 py-1.5 text-xs font-medium text-[#3E362E] transition hover:bg-[#efe7d6]"
                    >
                      Retry
                    </button>
                  </div>
                </div>
              ) : null}

              {skillLibraryActionNotice ? (
                <div className="rounded-[14px] border border-[rgba(96,112,86,0.16)] bg-[rgba(96,112,86,0.08)] px-4 py-3 text-sm text-[rgba(62,54,46,0.72)]">
                  {truncateText(skillLibraryActionNotice, 180)}
                </div>
              ) : null}

              {isLoadingSkillLibrary ? (
                <div className="space-y-3">
                  <div className="h-16 animate-pulse rounded-[16px] border border-[rgba(62,54,46,0.12)] bg-[#F5F1E6]" />
                  <div className="h-16 animate-pulse rounded-[16px] border border-[rgba(62,54,46,0.12)] bg-[#F5F1E6]" />
                  <div className="h-16 animate-pulse rounded-[16px] border border-[rgba(62,54,46,0.12)] bg-[#F5F1E6]" />
                </div>
              ) : importedGithubSkills.length === 0 ? (
                <div className="rounded-[16px] border border-dashed border-[rgba(62,54,46,0.18)] bg-[#F5F1E6] p-5">
                  <p className="text-sm font-medium text-[#3E362E]">
                    No imported skills yet. Preview a GitHub SKILL.md file and import it to quarantine.
                  </p>
                  <p className="mt-2 text-xs leading-6 text-[rgba(62,54,46,0.58)]">
                    Imported skills will appear here as safe metadata-only records.
                  </p>
                </div>
              ) : (
                <div className="space-y-3">
                  {importedGithubSkills.map((item) => {
                    const canAttach = item.isAttachable && Boolean(activeAgentDetail?.id);
                    const attachDisabledReason = !activeAgentDetail?.id
                      ? "Select an active associate first."
                      : item.attachBlockReason || "";

                    return (
                      <article
                        key={item.id}
                        className={`rounded-[16px] border p-4 ${
                          selectedImportedGithubSkillId === item.id
                            ? "border-[rgba(163,106,88,0.28)] bg-white shadow-[0_10px_26px_rgba(62,54,46,0.08)]"
                            : "border-[rgba(62,54,46,0.14)] bg-[#F5F1E6]"
                        }`}
                      >
                        <div className="flex flex-wrap items-start justify-between gap-3">
                          <div className="min-w-0">
                            <p className="text-sm font-semibold text-[#3E362E]">{item.title}</p>
                            <p className="mt-1 text-xs leading-6 text-[rgba(62,54,46,0.58)]">
                              Read-only imported skill record.
                            </p>
                            <p className="mt-2 text-[11px] uppercase tracking-[0.16em] text-[rgba(62,54,46,0.5)]">
                              {item.resourceReferences.length > 0
                                ? `${item.resourceReferences.length} resource reference${item.resourceReferences.length === 1 ? "" : "s"} detected`
                                : "No resource references detected"}
                            </p>
                          </div>

                          <div className="flex flex-wrap items-center gap-2">
                            <span className="rounded-full border border-[rgba(62,54,46,0.14)] bg-[#E5E0D3] px-2.5 py-1 text-[10px] uppercase tracking-[0.14em] text-[rgba(62,54,46,0.68)]">
                              {item.type}
                            </span>
                            <span className="rounded-full border border-[rgba(96,112,86,0.2)] bg-[rgba(96,112,86,0.12)] px-2.5 py-1 text-[10px] uppercase tracking-[0.14em] text-[#607056]">
                              {item.status || "inactive"}
                            </span>
                            <button
                              type="button"
                              onClick={() => setSelectedImportedGithubSkillId(item.id)}
                              className="rounded-full border border-[rgba(62,54,46,0.14)] bg-[#F5F1E6] px-3 py-1 text-[10px] uppercase tracking-[0.14em] text-[rgba(62,54,46,0.72)] transition hover:bg-[#efe7d6]"
                            >
                              View details
                            </button>
                          </div>
                        </div>

                        <div className="mt-4 grid gap-3 sm:grid-cols-2">
                          {[
                            { label: "Import status", value: item.importStatus || "-" },
                            { label: "Security status", value: item.securityStatus || "-" },
                            { label: "Risk level", value: item.riskLevel || "-" },
                            { label: "Source URL", value: item.sourceUrl || "-" },
                            { label: "Source reference", value: item.sourceReference || "-" },
                            { label: "Branch", value: item.sourceBranch || "-" },
                            { label: "File path", value: item.filePath || "-" },
                            { label: "Created at", value: formatDateTime(item.createdAt) }
                          ].map((field) => (
                            <div
                              key={`${item.id}-${field.label}`}
                              className="rounded-[14px] border border-[rgba(62,54,46,0.12)] bg-[#E5E0D3] px-4 py-3"
                            >
                              <p className="text-[11px] uppercase tracking-[0.16em] text-[rgba(62,54,46,0.54)]">
                                {field.label}
                              </p>
                              <p className="mt-1 break-words text-sm leading-6 text-[#3E362E]">
                                {field.value || "-"}
                              </p>
                            </div>
                          ))}
                        </div>

                        {item.warnings.length > 0 ? (
                          <div className="mt-4 rounded-[14px] border border-[rgba(163,106,88,0.18)] bg-[rgba(163,106,88,0.08)] px-4 py-3">
                            <p className="text-xs uppercase tracking-[0.16em] text-[rgba(62,54,46,0.54)]">
                              Warnings
                            </p>
                            <ul className="mt-2 space-y-1 text-sm leading-6 text-[#3E362E]">
                              {item.warnings.map((warning, index) => (
                                <li key={`${item.id}-warning-${index}`}>{warning}</li>
                              ))}
                            </ul>
                          </div>
                        ) : null}

                        <div className="mt-4 flex flex-wrap items-center justify-between gap-3">
                          <p className="text-xs leading-6 text-[rgba(62,54,46,0.62)]">
                            {item.isAttachable
                              ? attachDisabledReason || "Attach to an active associate to make it active on that agent."
                              : item.attachBlockReason || "Blocked imported skill cannot be attached."}
                          </p>
                          <button
                            type="button"
                            disabled={!canAttach || skillAssignmentActionId === item.id}
                            onClick={() => handleAttachImportedSkill(item.id)}
                            className="rounded-full bg-[#A36A58] px-4 py-2.5 text-sm font-medium text-white transition hover:bg-[#94604f] disabled:cursor-not-allowed disabled:opacity-70"
                          >
                            {skillAssignmentActionId === item.id
                              ? "Attaching..."
                              : item.isAttachable
                                ? "Attach"
                                : "Blocked"}
                          </button>
                        </div>
                      </article>
                    );
                  })}
                </div>
              )}

              {selectedImportedGithubSkill ? (
                <div className="rounded-[16px] border border-[rgba(62,54,46,0.14)] bg-white p-4">
                  <div className="flex flex-wrap items-start justify-between gap-3">
                    <div className="min-w-0">
                      <p className="text-sm font-semibold text-[#3E362E]">
                        {selectedImportedGithubSkill.title}
                      </p>
                      <p className="mt-1 text-xs leading-6 text-[rgba(62,54,46,0.62)]">
                        Safe detail view for quarantine-style imported skill records.
                      </p>
                    </div>
                    <div className="flex flex-wrap items-center gap-2">
                      <span className="rounded-full border border-[rgba(62,54,46,0.14)] bg-[#E5E0D3] px-2.5 py-1 text-[10px] uppercase tracking-[0.14em] text-[rgba(62,54,46,0.68)]">
                        {selectedImportedGithubSkill.type || "prompt_skill"}
                      </span>
                      <span className="rounded-full border border-[rgba(96,112,86,0.2)] bg-[rgba(96,112,86,0.12)] px-2.5 py-1 text-[10px] uppercase tracking-[0.14em] text-[#607056]">
                        {selectedImportedGithubSkill.status || "inactive"}
                      </span>
                    </div>
                  </div>

                  <div className="mt-4 grid gap-3 sm:grid-cols-2">
                    {[
                      { label: "Source URL", value: selectedImportedGithubSkill.sourceUrl || "-" },
                      { label: "Source reference", value: selectedImportedGithubSkill.sourceReference || "-" },
                      { label: "Branch", value: selectedImportedGithubSkill.sourceBranch || "-" },
                      { label: "File path", value: selectedImportedGithubSkill.filePath || "-" },
                      { label: "Import status", value: selectedImportedGithubSkill.importStatus || "-" },
                      { label: "Security status", value: selectedImportedGithubSkill.securityStatus || "-" }
                    ].map((item) => (
                      <div
                        key={`detail-${item.label}`}
                        className="rounded-[14px] border border-[rgba(62,54,46,0.12)] bg-[#F5F1E6] px-4 py-3"
                      >
                        <p className="text-[11px] uppercase tracking-[0.16em] text-[rgba(62,54,46,0.54)]">
                          {item.label}
                        </p>
                        <p className="mt-1 break-words text-sm leading-6 text-[#3E362E]">
                          {item.value}
                        </p>
                      </div>
                    ))}
                  </div>

                  <div className="mt-4 grid gap-3 sm:grid-cols-2">
                    <div className="rounded-[14px] border border-[rgba(62,54,46,0.12)] bg-[#F5F1E6] px-4 py-3">
                      <p className="text-[11px] uppercase tracking-[0.16em] text-[rgba(62,54,46,0.54)]">
                        Resource references
                      </p>
                      <ul className="mt-2 space-y-1 text-sm leading-6 text-[#3E362E]">
                        {selectedImportedGithubSkill.resourceReferences.length > 0 ? (
                          selectedImportedGithubSkill.resourceReferences.map((path) => (
                            <li key={path}>{path}</li>
                          ))
                        ) : (
                          <li>None detected.</li>
                        )}
                      </ul>
                    </div>
                    <div className="rounded-[14px] border border-[rgba(62,54,46,0.12)] bg-[#F5F1E6] px-4 py-3">
                      <p className="text-[11px] uppercase tracking-[0.16em] text-[rgba(62,54,46,0.54)]">
                        Safety note
                      </p>
                      <p className="mt-2 text-sm leading-6 text-[#3E362E]">
                        Resources are detected only. Nothing is fetched, executed, enabled, or assigned.
                      </p>
                    </div>
                  </div>

                  {selectedImportedGithubSkill.warnings.length > 0 ? (
                    <div className="mt-4 rounded-[14px] border border-[rgba(163,106,88,0.18)] bg-[rgba(163,106,88,0.08)] px-4 py-3">
                      <p className="text-xs uppercase tracking-[0.16em] text-[rgba(62,54,46,0.54)]">
                        Warnings
                      </p>
                      <ul className="mt-2 space-y-1 text-sm leading-6 text-[#3E362E]">
                        {selectedImportedGithubSkill.warnings.map((warning, index) => (
                          <li key={`${selectedImportedGithubSkill.id}-warning-${index}`}>{warning}</li>
                        ))}
                      </ul>
                    </div>
                  ) : null}
                </div>
              ) : null}
            </section>
          </div>
        ) : null}
      </FloatingCard>

      <FloatingCard
        title="Settings"
        subtitle="Settings are preview-only in MVP. Provider credentials and runtime configuration will be handled in a later secure phase."
        open={cards.settings.open}
        position={{ x: cards.settings.x, y: cards.settings.y }}
        zIndex={cards.settings.z}
        widthClassName="w-[480px] max-w-[calc(100vw-2rem)]"
        bodyClassName="space-y-4"
        onClose={() => closeCard("settings")}
        onMove={(nextPosition) => moveCard("settings", nextPosition)}
        onFocus={() => bringCardToFront("settings")}
        footer={
          <div className="space-y-3">
            <div className="grid gap-3 sm:grid-cols-2">
              <button
                type="button"
                disabled
                className="cursor-not-allowed rounded-full border border-[rgba(62,54,46,0.14)] bg-[#F5F1E6] px-4 py-2.5 text-sm text-[rgba(62,54,46,0.52)] opacity-70"
              >
                Provider setup disabled
              </button>
              <button
                type="button"
                disabled
                className="cursor-not-allowed rounded-full border border-[rgba(62,54,46,0.14)] bg-[#F5F1E6] px-4 py-2.5 text-sm font-medium text-[rgba(62,54,46,0.52)] opacity-70"
              >
                Model testing disabled
              </button>
            </div>
            <p className="text-xs text-[rgba(62,54,46,0.6)]">
              MVP mode prevents credential saving, model testing, runtime execution, and workflow activation.
            </p>
          </div>
        }
      >
        <section className="rounded-[16px] border border-[rgba(62,54,46,0.14)] bg-[#F5F1E6] p-4">
          <p className="text-sm font-medium text-[#3E362E]">Workspace owner</p>
          <p className="mt-2 text-sm text-[rgba(62,54,46,0.64)]">
            {workspace.currentUser?.display_name || "Workspace owner"}
          </p>
        </section>

        <section className="rounded-[16px] border border-[rgba(62,54,46,0.14)] bg-[#F5F1E6] p-4">
          <p className="text-sm font-medium text-[#3E362E]">Provider setup preview</p>
          <p className="mt-2 text-sm text-[rgba(62,54,46,0.64)]">
            Provider credentials stay server-side in a later secure phase.
          </p>
          <div className="mt-3 grid gap-3">
            <input
              placeholder="Provider setup disabled"
              disabled
              className="rounded-[14px] border border-[rgba(62,54,46,0.14)] bg-[#E5E0D3] px-4 py-3 text-sm text-[#3E362E] opacity-80 outline-none"
            />
            <select disabled className="rounded-[14px] border border-[rgba(62,54,46,0.14)] bg-[#E5E0D3] px-4 py-3 text-sm text-[rgba(62,54,46,0.6)] opacity-80 outline-none">
              <option>Preview only</option>
            </select>
            <input
              placeholder="Model testing disabled"
              disabled
              className="rounded-[14px] border border-[rgba(62,54,46,0.14)] bg-[#E5E0D3] px-4 py-3 text-sm text-[#3E362E] opacity-80 outline-none"
            />
          </div>
        </section>

        <section className="grid gap-3 sm:grid-cols-2">
          <div className="rounded-[16px] border border-[rgba(62,54,46,0.14)] bg-[#F5F1E6] p-4">
            <p className="text-sm font-medium text-[#3E362E]">Runtime config preview</p>
            <div className="mt-3 space-y-2 text-sm text-[rgba(62,54,46,0.64)]">
              <p>API base URL: preview only</p>
              <p>n8n base URL: preview only</p>
              <p>Public webhook or domain: preview only</p>
            </div>
          </div>
          <div className="rounded-[16px] border border-[rgba(62,54,46,0.14)] bg-[#F5F1E6] p-4">
            <p className="text-sm font-medium text-[#3E362E]">Security notes</p>
            <div className="mt-3 space-y-2 text-sm text-[rgba(62,54,46,0.64)]">
              <p>Server-side credential storage only.</p>
              <p>Runtime mode disabled.</p>
              <p>Workflow activation disabled.</p>
            </div>
          </div>
        </section>

        <section className="rounded-[16px] border border-[rgba(62,54,46,0.14)] bg-[#F5F1E6] p-4">
          <p className="text-sm font-medium text-[#3E362E]">Safety note</p>
          <p className="mt-2 text-sm text-[rgba(62,54,46,0.64)]">
            MVP mode prevents credential saving, model testing, runtime execution, and workflow activation.
          </p>
        </section>
      </FloatingCard>

      <FloatingCard
        title="Workflow n8n"
        subtitle="n8n workflow creation and execution are disabled in MVP. Future phase will create inactive workflow drafts only after review."
        open={cards.workflow.open}
        position={{ x: cards.workflow.x, y: cards.workflow.y }}
        zIndex={cards.workflow.z}
        widthClassName="w-[460px] max-w-[calc(100vw-2rem)]"
        bodyClassName="space-y-4"
        onClose={() => closeCard("workflow")}
        onMove={(nextPosition) => moveCard("workflow", nextPosition)}
        onFocus={() => bringCardToFront("workflow")}
      >
        <div className="rounded-[18px] border border-[rgba(62,54,46,0.14)] bg-[#F5F1E6] p-4">
          <p className="text-sm font-medium text-[#3E362E]">Planning only</p>
          <p className="mt-2 text-sm leading-6 text-[rgba(62,54,46,0.68)]">
            n8n workflow creation and execution are disabled in MVP. Future phase will create inactive workflow drafts only after review.
          </p>
          <div className="mt-3 inline-flex rounded-full border border-[rgba(163,106,88,0.2)] bg-[rgba(163,106,88,0.1)] px-3 py-1 text-[11px] uppercase tracking-[0.14em] text-[#A36A58]">
            Preview only
          </div>
        </div>

        <div className="grid gap-3 sm:grid-cols-2">
          {N8N_REQUIREMENTS.map((item) => (
            <div
              key={item.title}
              className="rounded-[16px] border border-[rgba(62,54,46,0.14)] bg-[#F5F1E6] px-4 py-3"
            >
              <p className="text-sm font-semibold text-[#3E362E]">{item.title}</p>
              <p className="mt-1 text-xs leading-6 text-[rgba(62,54,46,0.62)]">{item.detail}</p>
            </div>
          ))}
        </div>

        <div className="rounded-[18px] border border-[rgba(62,54,46,0.14)] bg-[#E5E0D3] p-4">
          <p className="text-sm font-medium text-[#3E362E]">Future phase states</p>
          <div className="mt-3 flex flex-wrap gap-2">
            <button
              type="button"
              disabled
              className="cursor-not-allowed rounded-full border border-[rgba(62,54,46,0.14)] bg-[#F5F1E6] px-3 py-1.5 text-xs text-[rgba(62,54,46,0.54)] opacity-70"
            >
              Preview only
            </button>
            <button
              type="button"
              disabled
              className="cursor-not-allowed rounded-full border border-[rgba(62,54,46,0.14)] bg-[#F5F1E6] px-3 py-1.5 text-xs text-[rgba(62,54,46,0.54)] opacity-70"
            >
              Workflow creation disabled
            </button>
            <button
              type="button"
              disabled
              className="cursor-not-allowed rounded-full border border-[rgba(62,54,46,0.14)] bg-[#F5F1E6] px-3 py-1.5 text-xs text-[rgba(62,54,46,0.54)] opacity-70"
            >
              Runtime disabled
            </button>
            <button
              type="button"
              disabled
              className="cursor-not-allowed rounded-full border border-[rgba(62,54,46,0.14)] bg-[#F5F1E6] px-3 py-1.5 text-xs text-[rgba(62,54,46,0.54)] opacity-70"
            >
              Activation disabled
            </button>
          </div>
          <p className="mt-3 text-xs text-[rgba(62,54,46,0.6)]">
            Create workflow = future. Execute workflow = disabled. Activate workflow = disabled.
          </p>
        </div>

        <div className="rounded-[18px] border border-[rgba(62,54,46,0.14)] bg-[#F5F1E6] p-4">
          <div className="flex items-center justify-between gap-3">
            <p className="text-sm font-semibold text-[#3E362E]">Subscription-aware n8n state</p>
            <span className="rounded-full border border-[rgba(163,106,88,0.2)] bg-[rgba(163,106,88,0.1)] px-2.5 py-1 text-[10px] uppercase tracking-[0.14em] text-[#A36A58]">
              {currentUserRole === "admin" ? "admin" : currentSubscriptionPlan}
            </span>
          </div>
          <p className="mt-2 text-sm leading-6 text-[rgba(62,54,46,0.68)]">
            {getN8nPlanNote(currentSubscriptionPlan, currentUserRole)}
          </p>
          <p className="mt-2 text-xs uppercase tracking-[0.14em] text-[rgba(62,54,46,0.52)]">
            {savedWorkflowLimit === null
              ? "Saved workflow limit: unlimited"
              : `Saved workflow limit: ${savedWorkflowLimit} | Used: ${activeSavedWorkflowCount}`}
          </p>
        </div>

        {canUseN8n ? (
          <div className="space-y-4 rounded-[18px] border border-[rgba(62,54,46,0.14)] bg-[#F5F1E6] p-4">
            <div className="space-y-2">
              <p className="text-sm font-semibold text-[#3E362E]">Save Draft Workflow</p>
              <p className="text-sm leading-6 text-[rgba(62,54,46,0.68)]">
                Store workflow metadata only. No external n8n connection, activation, or execution is used.
              </p>
            </div>

            <div className="space-y-3">
              <label className="block space-y-2">
                <span className="text-sm font-medium text-[#3E362E]">Draft name</span>
                <input
                  value={workflowDraftForm.name}
                  onChange={(event) => setWorkflowDraftForm((current) => ({ ...current, name: event.target.value }))}
                  placeholder="Email summary draft"
                  className="w-full rounded-[14px] border border-[rgba(62,54,46,0.14)] bg-[#E5E0D3] px-4 py-3 text-[15px] text-[#3E362E] outline-none transition placeholder:text-[rgba(62,54,46,0.4)] focus:border-[#A36A58]"
                />
              </label>

              <label className="block space-y-2">
                <span className="text-sm font-medium text-[#3E362E]">Description</span>
                <textarea
                  value={workflowDraftForm.description}
                  onChange={(event) => setWorkflowDraftForm((current) => ({ ...current, description: event.target.value }))}
                  placeholder="Short note about what this workflow draft should do."
                  rows={3}
                  className="w-full rounded-[14px] border border-[rgba(62,54,46,0.14)] bg-[#E5E0D3] px-4 py-3 text-[15px] text-[#3E362E] outline-none transition placeholder:text-[rgba(62,54,46,0.4)] focus:border-[#A36A58]"
                />
              </label>
            </div>

            <div className="flex flex-wrap items-center gap-3">
              <button
                type="button"
                onClick={handleWorkflowDraftSave}
                disabled={
                  isSavingWorkflowDraft ||
                  !workflowDraftForm.name.trim() ||
                  (savedWorkflowLimit !== null && activeSavedWorkflowCount >= savedWorkflowLimit)
                }
                className="rounded-full bg-[#A36A58] px-4 py-2.5 text-sm font-semibold text-white transition hover:bg-[#94604f] disabled:cursor-not-allowed disabled:opacity-60"
              >
                {isSavingWorkflowDraft ? "Saving draft..." : "Save Draft Workflow"}
              </button>
              <span className="text-xs text-[rgba(62,54,46,0.58)]">
                Drafts stay inactive and never call external n8n.
              </span>
            </div>

            {workflowDraftNotice ? (
              <div className="rounded-[14px] border border-[rgba(62,54,46,0.14)] bg-[#E5E0D3] px-4 py-3 text-sm text-[rgba(62,54,46,0.72)]">
                {workflowDraftNotice}
              </div>
            ) : null}

            <div className="space-y-3 rounded-[16px] border border-[rgba(62,54,46,0.14)] bg-[#E5E0D3] p-4">
              <div className="flex items-center justify-between gap-3">
                <p className="text-sm font-semibold text-[#3E362E]">Saved workflows</p>
                <span className="text-xs uppercase tracking-[0.14em] text-[rgba(62,54,46,0.56)]">
                  {activeSavedWorkflowCount}/{savedWorkflowLimit === null ? "∞" : savedWorkflowLimit}
                </span>
              </div>

              {isLoadingSavedWorkflows ? (
                <div className="rounded-[14px] border border-[rgba(62,54,46,0.14)] bg-[#F5F1E6] px-4 py-3 text-sm text-[rgba(62,54,46,0.64)]">
                  Loading saved workflow drafts...
                </div>
              ) : savedWorkflowsNotice ? (
                <div className="rounded-[14px] border border-[rgba(62,54,46,0.14)] bg-[#F5F1E6] px-4 py-3 text-sm text-[rgba(62,54,46,0.64)]">
                  {savedWorkflowsNotice}
                </div>
              ) : savedWorkflows.length ? (
                <div className="space-y-3">
                  {savedWorkflows.map((workflow) => (
                    <div key={workflow.id} className="rounded-[14px] border border-[rgba(62,54,46,0.14)] bg-[#F5F1E6] px-4 py-3">
                      <div className="flex items-start justify-between gap-3">
                        <div className="min-w-0">
                          <p className="text-sm font-semibold text-[#3E362E]">{workflow.name}</p>
                          <p className="mt-1 text-xs leading-6 text-[rgba(62,54,46,0.64)]">
                            {truncateText(workflow.description, 110)}
                          </p>
                        </div>
                        <span className="rounded-full border border-[rgba(163,106,88,0.2)] bg-[rgba(163,106,88,0.1)] px-2.5 py-1 text-[10px] uppercase tracking-[0.14em] text-[#A36A58]">
                          {getWorkflowStatusLabel(workflow.status)}
                        </span>
                      </div>
                      <div className="mt-3 flex flex-wrap gap-2 text-[11px] text-[rgba(62,54,46,0.58)]">
                        <span className="rounded-full border border-[rgba(62,54,46,0.12)] bg-[#F5F1E6] px-2.5 py-1">
                          {truncateText(workflow.triggerType, 18)}
                        </span>
                        <span className="rounded-full border border-[rgba(62,54,46,0.12)] bg-[#F5F1E6] px-2.5 py-1">
                          {formatDateTime(workflow.createdAt)}
                        </span>
                        <span className="rounded-full border border-[rgba(62,54,46,0.12)] bg-[#F5F1E6] px-2.5 py-1">
                          Updated {formatDateTime(workflow.updatedAt)}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="rounded-[14px] border border-[rgba(62,54,46,0.14)] bg-[#F5F1E6] px-4 py-3 text-sm text-[rgba(62,54,46,0.64)]">
                  No saved workflow drafts yet.
                </div>
              )}
            </div>
          </div>
        ) : (
          <div className="rounded-[18px] border border-[rgba(62,54,46,0.14)] bg-[#F5F1E6] p-4">
            <p className="text-sm font-semibold text-[#3E362E]">n8n locked on Free</p>
            <p className="mt-2 text-sm leading-6 text-[rgba(62,54,46,0.68)]">
              Your Free plan does not include n8n access. Upgrade to Pro or Executive to save workflow drafts.
            </p>
          </div>
        )}

        <p className="text-xs text-[rgba(62,54,46,0.6)]">
          This workspace can plan automation requirements, but it cannot run imported code or execute workflows in MVP mode.
        </p>
      </FloatingCard>
    </>
  );

  return (
    <ProtectedRoute>
      <AppShell minimal sidebar={canvasSidebar}>
        <div className="relative min-h-screen overflow-hidden bg-[#F5F1E6]">
          <div className="grid min-h-screen min-h-0 grid-cols-1 xl:grid-cols-[minmax(0,1fr)_340px]">
            <section className="min-w-0 p-6 xl:min-h-0">
              <div className="flex h-full min-h-[calc(100vh-48px)] flex-col rounded-[20px] border border-[rgba(62,54,46,0.14)] bg-[#F5F1E6] p-6">
                <header className="mb-6 flex items-start justify-between gap-4">
                  <div>
                    <p className="text-xs uppercase tracking-[0.18em] text-[rgba(62,54,46,0.62)]">
                      Workspace
                    </p>
                    <h1 className="mt-2 text-3xl font-semibold tracking-[-0.03em] text-[#3E362E]">
                      Command Center
                    </h1>
                  </div>
                  {activeAgent ? (
                    <div className="rounded-full border border-[rgba(163,106,88,0.2)] bg-[rgba(163,106,88,0.1)] px-3 py-1.5 text-xs font-medium text-[#A36A58]">
                      Active: {activeAgent.name}
                    </div>
                  ) : null}
                </header>

                <div className="flex flex-1 flex-col rounded-[20px] border border-[rgba(62,54,46,0.14)] bg-[#F5F1E6] p-5">
                  <div className="flex-1 space-y-4">
                    <div className="rounded-[18px] border border-[rgba(62,54,46,0.14)] bg-[#E5E0D3] px-5 py-4">
                      <p className="text-sm text-[rgba(62,54,46,0.7)]">
                        Workspace Chat is the primary entrypoint. Use advanced tools only when you need manual routing or draft review.
                      </p>
                    </div>

                    <WorkspaceChatPanel />

                    <div className="rounded-[18px] border border-[rgba(62,54,46,0.14)] bg-[#E5E0D3] px-5 py-4">
                      <div className="flex items-center justify-between gap-3">
                        <p className="text-[11px] uppercase tracking-[0.18em] text-[rgba(62,54,46,0.56)]">
                          Active associate
                        </p>
                        <span className="rounded-full border border-[rgba(163,106,88,0.2)] bg-[rgba(163,106,88,0.1)] px-2.5 py-1 text-[10px] uppercase tracking-[0.14em] text-[#A36A58]">
                          Read-only
                        </span>
                      </div>

                      {activeAgent ? (
                        <p className="mt-2 text-xl font-semibold text-[#3E362E]">{activeAgent.name}</p>
                      ) : (
                        <p className="mt-2 text-xl font-semibold text-[#3E362E]">
                          No active associate selected
                        </p>
                      )}

                      {activeAgent ? (
                        <div className="mt-2 flex flex-wrap gap-3 text-xs text-[rgba(62,54,46,0.64)]">
                          <span>Status: {activeAgent.status}</span>
                          {activeAgent.defaultModelName ? <span>Model: {activeAgent.defaultModelName}</span> : null}
                        </div>
                      ) : null}

                      <div className="mt-3 flex flex-wrap items-center gap-2">
                        <span className="rounded-full border border-[rgba(62,54,46,0.12)] bg-white px-2.5 py-1 text-[11px] text-[rgba(62,54,46,0.72)]">
                          Active skills: {activeAgentSkills.length}
                        </span>
                        {activeAgent ? (
                          <button
                            type="button"
                            onClick={handleClearActiveAssociate}
                            className="rounded-full border border-[rgba(62,54,46,0.14)] bg-[#F5F1E6] px-3 py-1.5 text-xs font-medium text-[#3E362E] transition hover:bg-[#efe7d6]"
                          >
                            Clear selection
                          </button>
                        ) : null}
                      </div>

                      <p className="mt-3 text-sm leading-6 text-[rgba(62,54,46,0.68)]">
                        {activeAgentDetail
                          ? truncateText(
                              activeAgentDetail.role_description ||
                                activeAgentDetail.description ||
                                "No summary available.",
                              180
                            )
                          : "Select an associate from the sidebar for direct agent chat. Workspace Chat stays primary."}
                      </p>

                      {activeAgentDetailNotice ? (
                        <p className="mt-3 text-sm text-[rgba(62,54,46,0.64)]">
                          {activeAgentDetailNotice}
                        </p>
                      ) : null}

                      <div className="hidden">
                      {isLoadingActiveAgentDetail ? (
                        <p className="mt-3 text-sm text-[rgba(62,54,46,0.64)]">
                          Loading active agent detail...
                        </p>
                      ) : activeAgentDetail ? (
                        <div className="mt-4 grid gap-3">
                          <div className="rounded-[16px] border border-[rgba(62,54,46,0.14)] bg-[#F5F1E6] px-4 py-3">
                            <p className="text-[11px] uppercase tracking-[0.14em] text-[rgba(62,54,46,0.52)]">
                              Provider / model
                            </p>
                            <p className="mt-1 text-sm font-semibold text-[#3E362E]">
                              {activeAgentProviderLabel || "Not set"}
                            </p>
                          </div>

                          <div className="rounded-[16px] border border-[rgba(62,54,46,0.14)] bg-[#F5F1E6] px-4 py-3">
                            <p className="text-[11px] uppercase tracking-[0.14em] text-[rgba(62,54,46,0.52)]">
                              Description / instruction summary
                            </p>
                            <p className="mt-1 text-sm leading-6 text-[rgba(62,54,46,0.68)]">
                              {truncateText(
                                activeAgentDetail.role_description ||
                                  activeAgentDetail.description ||
                                  "No summary available.",
                                220
                              )}
                            </p>
                          </div>

                          <div className="grid gap-3 sm:grid-cols-2">
                          <div className="rounded-[16px] border border-[rgba(62,54,46,0.14)] bg-[#F5F1E6] px-4 py-3">
                            <p className="text-[11px] uppercase tracking-[0.14em] text-[rgba(62,54,46,0.52)]">
                              Status
                            </p>
                              <p className="mt-1 text-sm font-semibold text-[#3E362E]">
                                {activeAgentDetail.status || "unknown"}
                              </p>
                            </div>
                            <div className="rounded-[16px] border border-[rgba(62,54,46,0.14)] bg-[#F5F1E6] px-4 py-3">
                              <p className="text-[11px] uppercase tracking-[0.14em] text-[rgba(62,54,46,0.52)]">
                                Dates
                              </p>
                              <p className="mt-1 text-sm leading-6 text-[rgba(62,54,46,0.68)]">
                                {formatDateTime(activeAgentDetail.created_at)}
                                <span className="mx-2">•</span>
                                {formatDateTime(activeAgentDetail.updated_at)}
                              </p>
                            </div>
                          </div>

                          <div className="rounded-[16px] border border-[rgba(62,54,46,0.14)] bg-[#F5F1E6] px-4 py-3">
                            <div className="flex flex-wrap items-center justify-between gap-3">
                              <div>
                                <p className="text-[11px] uppercase tracking-[0.14em] text-[rgba(62,54,46,0.52)]">
                                  Active skills
                                </p>
                                <p className="mt-1 text-sm font-semibold text-[#3E362E]">
                                  Active as instruction/capability. Not executable runtime yet.
                                </p>
                              </div>
                              <span className="rounded-full border border-[rgba(163,106,88,0.2)] bg-[rgba(163,106,88,0.1)] px-2.5 py-1 text-[10px] uppercase tracking-[0.14em] text-[#A36A58]">
                                Read-only
                              </span>
                            </div>

                            {activeAgentSkillsNotice ? (
                              <div className="mt-3 rounded-[14px] border border-[rgba(163,106,88,0.18)] bg-[rgba(163,106,88,0.08)] px-4 py-3 text-sm text-[rgba(62,54,46,0.72)]">
                                {activeAgentSkillsNotice}
                              </div>
                            ) : null}

                            {isLoadingActiveAgentSkills ? (
                              <div className="mt-3 space-y-3">
                                <div className="h-14 animate-pulse rounded-[14px] border border-[rgba(62,54,46,0.12)] bg-white" />
                                <div className="h-14 animate-pulse rounded-[14px] border border-[rgba(62,54,46,0.12)] bg-white" />
                              </div>
                            ) : activeAgentSkills.length ? (
                              <div className="mt-3 space-y-3">
                                {activeAgentSkills.map((item) => (
                                  <div
                                    key={item.id}
                                    className="rounded-[14px] border border-[rgba(62,54,46,0.12)] bg-white px-4 py-3"
                                  >
                                    <div className="flex flex-wrap items-start justify-between gap-3">
                                      <div className="min-w-0">
                                        <p className="text-sm font-semibold text-[#3E362E]">
                                          {item.skill.title}
                                        </p>
                                        <p className="mt-1 text-xs leading-6 text-[rgba(62,54,46,0.62)]">
                                          {item.skill.type} | {item.skill.status} | {item.skill.securityStatus}
                                        </p>
                                      </div>
                                      <button
                                        type="button"
                                        onClick={() => handleDetachImportedSkill(item.skillId)}
                                        disabled={skillAssignmentActionId === item.skillId}
                                        className="rounded-full border border-[rgba(62,54,46,0.14)] bg-[#F5F1E6] px-3 py-1.5 text-xs font-medium text-[#3E362E] transition hover:bg-[#efe7d6] disabled:cursor-not-allowed disabled:opacity-70"
                                      >
                                        {skillAssignmentActionId === item.skillId ? "Detaching..." : "Detach"}
                                      </button>
                                    </div>
                                    <div className="mt-3 flex flex-wrap gap-2 text-[11px] text-[rgba(62,54,46,0.58)]">
                                      {item.skill.sourceUrl ? (
                                        <span className="rounded-full border border-[rgba(62,54,46,0.12)] bg-[#F5F1E6] px-2.5 py-1">
                                          {truncateText(item.skill.sourceUrl, 24)}
                                        </span>
                                      ) : null}
                                      <span className="rounded-full border border-[rgba(62,54,46,0.12)] bg-[#F5F1E6] px-2.5 py-1">
                                        {truncateText(item.skill.type, 18)}
                                      </span>
                                      <span className="rounded-full border border-[rgba(62,54,46,0.12)] bg-[#F5F1E6] px-2.5 py-1">
                                        {formatDateTime(item.createdAt)}
                                      </span>
                                    </div>
                                  </div>
                                ))}
                              </div>
                            ) : (
                              <div className="mt-3 rounded-[14px] border border-[rgba(62,54,46,0.12)] bg-white px-4 py-3 text-sm text-[rgba(62,54,46,0.64)]">
                                No active imported skills attached yet.
                              </div>
                            )}
                          </div>

                      </div>
                      ) : null}
                    </div>

                    {activeAgentDetail ? (
                      <AgentChatPanel
                        key={activeAgentDetail.id}
                        agent={activeAgentDetail}
                        providerLabel={activeAgentProviderLabel}
                      />
                    ) : null}

                    <details className="rounded-[18px] border border-[rgba(62,54,46,0.14)] bg-[#F5F1E6] p-4">
                      <summary className="flex cursor-pointer list-none items-center justify-between gap-3 [&::-webkit-details-marker]:hidden">
                        <div className="min-w-0">
                          <p className="text-[11px] uppercase tracking-[0.18em] text-[rgba(62,54,46,0.56)]">
                            Advanced Preview Tools
                          </p>
                          <p className="mt-1 text-sm font-semibold text-[#3E362E]">
                            Routing Preview, Task Draft, Draft History
                          </p>
                        </div>
                        <span className="rounded-full border border-[rgba(62,54,46,0.14)] bg-white px-3 py-1 text-[11px] uppercase tracking-[0.14em] text-[rgba(62,54,46,0.72)]">
                          Expand
                        </span>
                      </summary>
                      <div className="mt-4 space-y-4">
                    <div className="rounded-[18px] border border-[rgba(62,54,46,0.14)] bg-[#F5F1E6] p-4">
                      <div className="flex flex-wrap items-start justify-between gap-3">
                        <div className="min-w-0">
                          <p className="text-[11px] uppercase tracking-[0.18em] text-[rgba(62,54,46,0.56)]">
                            Routing Preview
                          </p>
                          <p className="mt-1 text-sm font-semibold text-[#3E362E]">
                            Preview Agent Match
                          </p>
                        </div>
                        <span className="rounded-full border border-[rgba(163,106,88,0.2)] bg-[rgba(163,106,88,0.1)] px-3 py-1 text-[11px] uppercase tracking-[0.14em] text-[#A36A58]">
                          Preview only
                        </span>
                      </div>
                      <p className="mt-2 text-sm leading-6 text-[rgba(62,54,46,0.64)]">
                        Enter a task and preview which agent would be recommended based on agent profile and active skills.
                      </p>

                      <form onSubmit={handleRoutingPreviewSubmit} className="mt-4 space-y-3">
                        <label className="grid gap-2">
                          <span className="text-xs uppercase tracking-[0.14em] text-[rgba(62,54,46,0.52)]">
                            Task text
                          </span>
                          <textarea
                            value={routingPreviewForm.taskText}
                            onChange={(event) => handleRoutingPreviewFieldChange(event.target.value)}
                            rows={4}
                            placeholder="Example: summarize these notes and choose the best agent."
                            className="rounded-[14px] border border-[rgba(62,54,46,0.14)] bg-white px-4 py-3 text-sm leading-6 text-[#3E362E] outline-none transition placeholder:text-[rgba(62,54,46,0.4)] focus:border-[#A36A58]"
                          />
                        </label>

                        <div className="flex flex-wrap gap-3">
                          <button
                            type="submit"
                            disabled={isPreviewingAgentMatch || !routingPreviewForm.taskText.trim()}
                            className="rounded-full bg-[#A36A58] px-4 py-2.5 text-sm font-medium text-white transition hover:bg-[#94604f] disabled:cursor-not-allowed disabled:opacity-70"
                          >
                            {isPreviewingAgentMatch ? "Previewing..." : "Preview Agent Match"}
                          </button>
                          <button
                            type="button"
                            onClick={() => handleRoutingPreviewFieldChange("")}
                            disabled={isPreviewingAgentMatch && !routingPreviewForm.taskText.trim()}
                            className="rounded-full border border-[rgba(62,54,46,0.14)] bg-[#F5F1E6] px-4 py-2.5 text-sm font-medium text-[#3E362E] transition hover:bg-[#efe7d6] disabled:cursor-not-allowed disabled:opacity-70"
                          >
                            Clear
                          </button>
                        </div>
                      </form>

                      {routingPreviewNotice ? (
                        <div className="mt-4 rounded-[14px] border border-[rgba(62,54,46,0.14)] bg-[#E5E0D3] px-4 py-3 text-sm text-[rgba(62,54,46,0.72)]">
                          {truncateText(routingPreviewNotice, 180)}
                        </div>
                      ) : null}

                      {routingPreviewResult ? (
                        <div className="mt-4 space-y-4">
                          <div className="rounded-[16px] border border-[rgba(62,54,46,0.14)] bg-white p-4">
                            <div className="flex flex-wrap items-start justify-between gap-3">
                              <div className="min-w-0">
                                <p className="text-[11px] uppercase tracking-[0.14em] text-[rgba(62,54,46,0.52)]">
                                  Recommended agent
                                </p>
                                <p className="mt-1 text-base font-semibold text-[#3E362E]">
                                  {routingPreviewResult.recommendedAgent?.name || "No recommendation"}
                                </p>
                                <p className="mt-1 text-sm leading-6 text-[rgba(62,54,46,0.64)]">
                                  {routingPreviewResult.recommendedAgent?.roleDescription ||
                                    routingPreviewResult.recommendedAgent?.description ||
                                    "No summary available."}
                                </p>
                              </div>
                              <span
                                className={`rounded-full border px-3 py-1 text-[11px] uppercase tracking-[0.14em] ${
                                  routingPreviewResult.confidence === "high"
                                    ? "border-[rgba(96,112,86,0.2)] bg-[rgba(96,112,86,0.12)] text-[#607056]"
                                    : routingPreviewResult.confidence === "medium"
                                      ? "border-[rgba(163,142,88,0.2)] bg-[rgba(163,142,88,0.12)] text-[#9A7A35]"
                                      : "border-[rgba(163,106,88,0.2)] bg-[rgba(163,106,88,0.1)] text-[#A36A58]"
                                }`}
                              >
                                {routingPreviewResult.confidence} confidence
                              </span>
                            </div>
                            <div className="mt-4 flex flex-wrap items-center gap-3">
                              <button
                                type="button"
                                onClick={handleCreateHandoffDraft}
                                disabled={
                                  isCreatingHandoffDraft ||
                                  !routingPreviewResult.recommendedAgent ||
                                  !routingPreviewResult.taskText.trim()
                                }
                                className="rounded-full bg-[#A36A58] px-4 py-2.5 text-sm font-medium text-white transition hover:bg-[#94604f] disabled:cursor-not-allowed disabled:opacity-70"
                              >
                                {isCreatingHandoffDraft ? "Saving draft..." : "Create Draft Handoff"}
                              </button>
                              <p className="text-xs leading-6 text-[rgba(62,54,46,0.58)]">
                                Draft only, no execution.
                              </p>
                            </div>

                            <div className="mt-4 grid gap-3 sm:grid-cols-2">
                              {(routingPreviewResult.reasons.length
                                ? routingPreviewResult.reasons
                                : ["Preview only, no execution."]
                              ).map((reason, index) => (
                                <div
                                  key={`routing-reason-${index}`}
                                  className="rounded-[14px] border border-[rgba(62,54,46,0.12)] bg-[#F5F1E6] px-4 py-3 text-sm leading-6 text-[#3E362E]"
                                >
                                  {reason}
                                </div>
                              ))}
                            </div>

                            <div className="mt-4 rounded-[14px] border border-[rgba(62,54,46,0.12)] bg-[#F5F1E6] px-4 py-3">
                              <p className="text-[11px] uppercase tracking-[0.14em] text-[rgba(62,54,46,0.52)]">
                                Matched active skills
                              </p>
                              {routingPreviewResult.activeSkillMatches.length ? (
                                <div className="mt-2 flex flex-wrap gap-2">
                                  {routingPreviewResult.activeSkillMatches.map((match) => (
                                    <span
                                      key={match.id}
                                      className="rounded-full border border-[rgba(62,54,46,0.12)] bg-white px-3 py-1 text-[11px] text-[rgba(62,54,46,0.72)]"
                                    >
                                      {match.title} | {match.skillType}
                                    </span>
                                  ))}
                                </div>
                              ) : (
                                <p className="mt-2 text-sm text-[rgba(62,54,46,0.62)]">
                                  No strong active skill match found.
                                </p>
                              )}
                            </div>

                            <p className="mt-4 text-xs leading-6 text-[rgba(62,54,46,0.58)]">
                              {routingPreviewResult.note}
                            </p>
                          </div>

                          <div className="space-y-3">
                            <p className="text-xs uppercase tracking-[0.14em] text-[rgba(62,54,46,0.52)]">
                              Candidate agents
                            </p>
                            {routingPreviewResult.candidateAgents.length ? (
                              routingPreviewResult.candidateAgents.map((candidate) => (
                                <div
                                  key={candidate.id}
                                  className="rounded-[16px] border border-[rgba(62,54,46,0.12)] bg-white px-4 py-3"
                                >
                                  <div className="flex flex-wrap items-start justify-between gap-3">
                                    <div className="min-w-0">
                                      <p className="text-sm font-semibold text-[#3E362E]">{candidate.name}</p>
                                      <p className="mt-1 text-xs leading-6 text-[rgba(62,54,46,0.62)]">
                                        {candidate.roleDescription || candidate.description || "No summary available."}
                                      </p>
                                    </div>
                                    <span className="rounded-full border border-[rgba(62,54,46,0.12)] bg-[#F5F1E6] px-3 py-1 text-[11px] uppercase tracking-[0.14em] text-[rgba(62,54,46,0.7)]">
                                      {candidate.score > 0 ? candidate.score : "low"}
                                    </span>
                                  </div>

                                  <div className="mt-3 space-y-2">
                                    {candidate.reasons.length ? (
                                      candidate.reasons.map((reason, index) => (
                                        <p
                                          key={`${candidate.id}-reason-${index}`}
                                          className="text-sm leading-6 text-[rgba(62,54,46,0.68)]"
                                        >
                                          {reason}
                                        </p>
                                      ))
                                    ) : (
                                      <p className="text-sm leading-6 text-[rgba(62,54,46,0.68)]">
                                        No strong keyword overlap found.
                                      </p>
                                    )}
                                  </div>

                                  <div className="mt-3 flex flex-wrap gap-2">
                                    {candidate.activeSkillMatches.length ? (
                                      candidate.activeSkillMatches.map((match) => (
                                        <span
                                          key={match.id}
                                          className="rounded-full border border-[rgba(62,54,46,0.12)] bg-[#F5F1E6] px-2.5 py-1 text-[11px] text-[rgba(62,54,46,0.7)]"
                                        >
                                          {match.title}
                                        </span>
                                      ))
                                    ) : (
                                      <span className="rounded-full border border-[rgba(62,54,46,0.12)] bg-[#F5F1E6] px-2.5 py-1 text-[11px] text-[rgba(62,54,46,0.56)]">
                                        No active skill matches
                                      </span>
                                    )}
                                  </div>
                                </div>
                              ))
                            ) : (
                              <div className="rounded-[14px] border border-[rgba(62,54,46,0.12)] bg-white px-4 py-3 text-sm text-[rgba(62,54,46,0.64)]">
                                No candidate agents available.
                              </div>
                            )}
                          </div>
                        </div>
                      ) : (
                        <div className="mt-4 rounded-[14px] border border-dashed border-[rgba(62,54,46,0.18)] bg-white px-4 py-3 text-sm text-[rgba(62,54,46,0.62)]">
                          Preview only, no execution. Enter a task to see the best agent match.
                        </div>
                      )}
                    </div>

                    <div className="rounded-[18px] border border-[rgba(62,54,46,0.14)] bg-[#F5F1E6] p-4">
                      <div className="flex flex-wrap items-start justify-between gap-3">
                        <div className="min-w-0">
                          <p className="text-[11px] uppercase tracking-[0.18em] text-[rgba(62,54,46,0.56)]">
                            Task Draft
                          </p>
                          <p className="mt-1 text-sm font-semibold text-[#3E362E]">
                            Handoff Preview
                          </p>
                        </div>
                        <span className="rounded-full border border-[rgba(163,106,88,0.2)] bg-[rgba(163,106,88,0.1)] px-3 py-1 text-[11px] uppercase tracking-[0.14em] text-[#A36A58]">
                          Preview only
                        </span>
                      </div>
                      <p className="mt-2 text-sm leading-6 text-[rgba(62,54,46,0.64)]">
                        Menggunakan task text yang sama dari Routing Preview untuk membuat draft handoff lokal.
                      </p>

                      <div className="mt-4 rounded-[14px] border border-[rgba(62,54,46,0.12)] bg-[#E5E0D3] px-4 py-3">
                        <p className="text-[11px] uppercase tracking-[0.14em] text-[rgba(62,54,46,0.52)]">
                          Current task text
                        </p>
                        <p className="mt-2 text-sm leading-6 text-[#3E362E]">
                          {routingPreviewForm.taskText.trim() || "Enter a task in Routing Preview first."}
                        </p>
                      </div>

                      <div className="mt-4 flex flex-wrap items-center gap-3">
                        <button
                          type="button"
                          onClick={handleGenerateTaskDraft}
                          disabled={isGeneratingTaskDraft || !routingPreviewForm.taskText.trim()}
                          className="rounded-full bg-[#A36A58] px-4 py-2.5 text-sm font-medium text-white transition hover:bg-[#94604f] disabled:cursor-not-allowed disabled:opacity-70"
                        >
                          {isGeneratingTaskDraft ? "Generating..." : "Generate Task Draft"}
                        </button>
                        <button
                          type="button"
                          onClick={handleClearTaskDraft}
                          disabled={isGeneratingTaskDraft && !taskDraftResult}
                          className="rounded-full border border-[rgba(62,54,46,0.14)] bg-[#F5F1E6] px-4 py-2.5 text-sm font-medium text-[#3E362E] transition hover:bg-[#efe7d6] disabled:cursor-not-allowed disabled:opacity-70"
                        >
                          Clear Draft
                        </button>
                      </div>

                      {taskDraftNotice ? (
                        <div className="mt-4 rounded-[14px] border border-[rgba(62,54,46,0.14)] bg-[#E5E0D3] px-4 py-3 text-sm text-[rgba(62,54,46,0.72)]">
                          {truncateText(taskDraftNotice, 180)}
                        </div>
                      ) : null}

                      {taskDraftResult ? (
                        <div className="mt-4 space-y-4 rounded-[16px] border border-[rgba(62,54,46,0.12)] bg-white p-4">
                          <div className="flex flex-wrap items-start justify-between gap-3">
                            <div className="min-w-0">
                              <p className="text-[11px] uppercase tracking-[0.14em] text-[rgba(62,54,46,0.52)]">
                                Selected agent
                              </p>
                              <p className="mt-1 text-base font-semibold text-[#3E362E]">
                                {taskDraftResult.selectedAgentName || "No recommendation"}
                              </p>
                            </div>
                            <div className="flex flex-wrap items-center gap-2">
                              <span
                                className={`rounded-full border px-3 py-1 text-[11px] uppercase tracking-[0.14em] ${
                                  taskDraftResult.status === "draft_only"
                                    ? "border-[rgba(163,106,88,0.2)] bg-[rgba(163,106,88,0.1)] text-[#A36A58]"
                                    : "border-[rgba(62,54,46,0.14)] bg-[#E5E0D3] text-[rgba(62,54,46,0.7)]"
                                }`}
                              >
                                Draft Only
                              </span>
                              <span
                                className={`rounded-full border px-3 py-1 text-[11px] uppercase tracking-[0.14em] ${
                                  taskDraftResult.confidence === "high"
                                    ? "border-[rgba(96,112,86,0.2)] bg-[rgba(96,112,86,0.12)] text-[#607056]"
                                    : taskDraftResult.confidence === "medium"
                                      ? "border-[rgba(163,142,88,0.2)] bg-[rgba(163,142,88,0.12)] text-[#9A7A35]"
                                      : taskDraftResult.confidence === "low"
                                        ? "border-[rgba(163,106,88,0.2)] bg-[rgba(163,106,88,0.1)] text-[#A36A58]"
                                        : "border-[rgba(62,54,46,0.14)] bg-[#E5E0D3] text-[rgba(62,54,46,0.7)]"
                                }`}
                              >
                                {taskDraftResult.confidence} confidence
                              </span>
                            </div>
                          </div>

                          <div className="grid gap-3 sm:grid-cols-2">
                            {(taskDraftResult.reasons.length
                              ? taskDraftResult.reasons
                              : ["Preview only, no execution."]
                            ).map((reason, index) => (
                              <div
                                key={`task-draft-reason-${index}`}
                                className="rounded-[14px] border border-[rgba(62,54,46,0.12)] bg-[#F5F1E6] px-4 py-3 text-sm leading-6 text-[#3E362E]"
                              >
                                {reason}
                              </div>
                            ))}
                          </div>

                          <div className="rounded-[14px] border border-[rgba(62,54,46,0.12)] bg-[#F5F1E6] px-4 py-3">
                            <p className="text-[11px] uppercase tracking-[0.14em] text-[rgba(62,54,46,0.52)]">
                              Relevant skills
                            </p>
                            {taskDraftResult.relevantSkills.length ? (
                              <div className="mt-2 flex flex-wrap gap-2">
                                {taskDraftResult.relevantSkills.map((skill) => (
                                  <span
                                    key={skill.id}
                                    className="rounded-full border border-[rgba(62,54,46,0.12)] bg-white px-3 py-1 text-[11px] text-[rgba(62,54,46,0.72)]"
                                  >
                                    {skill.title} | {skill.skillType}
                                  </span>
                                ))}
                              </div>
                            ) : (
                              <p className="mt-2 text-sm text-[rgba(62,54,46,0.62)]">
                                No relevant active skills found.
                              </p>
                            )}
                          </div>

                          <div className="rounded-[14px] border border-[rgba(62,54,46,0.12)] bg-[#F5F1E6] px-4 py-3">
                            <p className="text-[11px] uppercase tracking-[0.14em] text-[rgba(62,54,46,0.52)]">
                              Task Summary
                            </p>
                            <p className="mt-2 text-sm leading-6 text-[#3E362E]">
                              {taskDraftResult.taskSummary || "No summary available."}
                            </p>
                          </div>

                          <div className="rounded-[14px] border border-[rgba(163,142,88,0.18)] bg-[rgba(163,142,88,0.08)] px-4 py-3 text-sm leading-6 text-[rgba(62,54,46,0.74)]">
                            {taskDraftResult.safetyNote}
                          </div>

                          <div className="space-y-2">
                            <p className="text-xs uppercase tracking-[0.14em] text-[rgba(62,54,46,0.52)]">
                              Candidate agents
                            </p>
                            {taskDraftResult.candidateAgents.length ? (
                              <div className="flex flex-wrap gap-2">
                                {taskDraftResult.candidateAgents.map((candidate) => (
                                  <span
                                    key={candidate.id}
                                    className="rounded-full border border-[rgba(62,54,46,0.12)] bg-[#F5F1E6] px-3 py-1 text-[11px] text-[rgba(62,54,46,0.72)]"
                                  >
                                    {candidate.name} | {candidate.score > 0 ? candidate.score : "low"}
                                  </span>
                                ))}
                              </div>
                            ) : (
                              <p className="text-sm text-[rgba(62,54,46,0.62)]">
                                No candidate agents available.
                              </p>
                            )}
                          </div>
                        </div>
                      ) : null}
                    </div>

                    <div className="rounded-[18px] border border-[rgba(62,54,46,0.14)] bg-[#F5F1E6] p-4">
                      <div className="flex flex-wrap items-start justify-between gap-3">
                        <div className="min-w-0">
                          <p className="text-[11px] uppercase tracking-[0.18em] text-[rgba(62,54,46,0.56)]">
                            Draft History
                          </p>
                          <p className="mt-1 text-sm font-semibold text-[#3E362E]">
                            Saved handoff drafts
                          </p>
                        </div>
                        <span className="rounded-full border border-[rgba(62,54,46,0.14)] bg-[#E5E0D3] px-3 py-1 text-[11px] uppercase tracking-[0.14em] text-[rgba(62,54,46,0.72)]">
                          Last 20 drafts
                        </span>
                      </div>
                      <p className="mt-2 text-sm leading-6 text-[rgba(62,54,46,0.64)]">
                        Draft history is immutable. Create a new draft if the task changes.
                      </p>

                      {handoffDraftsNotice ? (
                        <div className="mt-4 rounded-[14px] border border-[rgba(163,106,88,0.18)] bg-[rgba(163,106,88,0.08)] px-4 py-3 text-sm text-[rgba(62,54,46,0.72)]">
                          {truncateText(handoffDraftsNotice, 180)}
                        </div>
                      ) : null}

                      {handoffDraftActionNotice ? (
                        <div className="mt-4 rounded-[14px] border border-[rgba(96,112,86,0.16)] bg-[rgba(96,112,86,0.08)] px-4 py-3 text-sm text-[rgba(62,54,46,0.72)]">
                          {truncateText(handoffDraftActionNotice, 180)}
                        </div>
                      ) : null}

                      {isLoadingHandoffDrafts ? (
                        <div className="mt-4 space-y-3">
                          <div className="h-16 animate-pulse rounded-[16px] border border-[rgba(62,54,46,0.12)] bg-white" />
                          <div className="h-16 animate-pulse rounded-[16px] border border-[rgba(62,54,46,0.12)] bg-white" />
                        </div>
                      ) : handoffDrafts.length ? (
                        <div className="mt-4 grid gap-3 lg:grid-cols-[minmax(0,1fr)_360px]">
                          <div className="space-y-3">
                            {handoffDrafts.map((draft) => {
                              const isSelected = selectedHandoffDraftId === draft.id;
                              return (
                                <button
                                  key={draft.id}
                                  type="button"
                                  onClick={() => setSelectedHandoffDraftId(draft.id)}
                                  className={`w-full rounded-[16px] border px-4 py-3 text-left transition ${
                                    isSelected
                                      ? "border-[rgba(163,106,88,0.28)] bg-white shadow-[0_10px_26px_rgba(62,54,46,0.08)]"
                                      : "border-[rgba(62,54,46,0.12)] bg-[#F5F1E6] hover:bg-[#efe7d6]"
                                  }`}
                                >
                                  <div className="flex flex-wrap items-start justify-between gap-3">
                                    <div className="min-w-0">
                                      <p className="text-sm font-semibold text-[#3E362E]">
                                        {truncateText(draft.draftPayload.taskSummary || draft.taskText, 64)}
                                      </p>
                                      <p className="mt-1 text-xs leading-6 text-[rgba(62,54,46,0.62)]">
                                        {draft.selectedAgent?.name || "No selected agent"} | {draft.routingConfidence}
                                      </p>
                                    </div>
                                    <span className="rounded-full border border-[rgba(62,54,46,0.12)] bg-[#E5E0D3] px-2.5 py-1 text-[10px] uppercase tracking-[0.14em] text-[rgba(62,54,46,0.68)]">
                                      {draft.status}
                                    </span>
                                  </div>
                                  <div className="mt-3 flex flex-wrap gap-2 text-[11px] text-[rgba(62,54,46,0.58)]">
                                    <span className="rounded-full border border-[rgba(62,54,46,0.12)] bg-white px-2.5 py-1">
                                      Recommended: {draft.recommendedAgent?.name || "Unavailable"}
                                    </span>
                                    <span className="rounded-full border border-[rgba(62,54,46,0.12)] bg-white px-2.5 py-1">
                                      {formatDateTime(draft.createdAt)}
                                    </span>
                                  </div>
                                </button>
                              );
                            })}
                          </div>

                          <div className="rounded-[16px] border border-[rgba(62,54,46,0.12)] bg-white p-4">
                            <div className="flex flex-wrap items-start justify-between gap-3">
                              <div className="min-w-0">
                                <p className="text-[11px] uppercase tracking-[0.14em] text-[rgba(62,54,46,0.52)]">
                                  Draft detail
                                </p>
                                <p className="mt-1 text-base font-semibold text-[#3E362E]">
                                  {selectedHandoffDraftDetail?.selectedAgent?.name ||
                                    selectedHandoffDraftDetail?.recommendedAgent?.name ||
                                    "Select a draft"}
                                </p>
                              </div>
                              <span className="rounded-full border border-[rgba(163,106,88,0.2)] bg-[rgba(163,106,88,0.1)] px-3 py-1 text-[11px] uppercase tracking-[0.14em] text-[#A36A58]">
                                {selectedHandoffDraftDetail?.routingConfidence || "low"} confidence
                              </span>
                            </div>

                            {isLoadingHandoffDraftDetail ? (
                              <div className="mt-4 rounded-[14px] border border-[rgba(62,54,46,0.12)] bg-[#F5F1E6] px-4 py-3 text-sm text-[rgba(62,54,46,0.64)]">
                                Loading draft detail...
                              </div>
                            ) : handoffDraftDetailNotice ? (
                              <div className="mt-4 rounded-[14px] border border-[rgba(163,106,88,0.18)] bg-[rgba(163,106,88,0.08)] px-4 py-3 text-sm text-[rgba(62,54,46,0.72)]">
                                {truncateText(handoffDraftDetailNotice, 180)}
                              </div>
                            ) : selectedHandoffDraftDetail ? (
                              <div className="mt-4 space-y-4">
                                <div className="grid gap-3 sm:grid-cols-2">
                                  <div className="rounded-[14px] border border-[rgba(62,54,46,0.12)] bg-[#F5F1E6] px-4 py-3">
                                    <p className="text-[11px] uppercase tracking-[0.16em] text-[rgba(62,54,46,0.54)]">
                                      Recommended agent
                                    </p>
                                    <p className="mt-1 text-sm font-semibold text-[#3E362E]">
                                      {selectedHandoffDraftDetail.recommendedAgent?.name || "Unavailable"}
                                    </p>
                                  </div>
                                  <div className="rounded-[14px] border border-[rgba(62,54,46,0.12)] bg-[#F5F1E6] px-4 py-3">
                                    <p className="text-[11px] uppercase tracking-[0.16em] text-[rgba(62,54,46,0.54)]">
                                      Selected agent
                                    </p>
                                    <p className="mt-1 text-sm font-semibold text-[#3E362E]">
                                      {selectedHandoffDraftDetail.selectedAgent?.name || "Unavailable"}
                                    </p>
                                  </div>
                                </div>

                                <div className="rounded-[14px] border border-[rgba(62,54,46,0.12)] bg-[#F5F1E6] px-4 py-3">
                                  <p className="text-[11px] uppercase tracking-[0.16em] text-[rgba(62,54,46,0.54)]">
                                    Reasons
                                  </p>
                                  <div className="mt-2 space-y-2">
                                    {selectedHandoffDraftDetail.routingReasons.length ? (
                                      selectedHandoffDraftDetail.routingReasons.map((reason, index) => (
                                        <p key={`handoff-reason-${index}`} className="text-sm leading-6 text-[#3E362E]">
                                          {reason}
                                        </p>
                                      ))
                                    ) : (
                                      <p className="text-sm leading-6 text-[rgba(62,54,46,0.64)]">
                                        No routing reasons recorded.
                                      </p>
                                    )}
                                  </div>
                                </div>

                                <div className="rounded-[14px] border border-[rgba(62,54,46,0.12)] bg-[#F5F1E6] px-4 py-3">
                                  <p className="text-[11px] uppercase tracking-[0.16em] text-[rgba(62,54,46,0.54)]">
                                    Matched active skills
                                  </p>
                                  {selectedHandoffDraftDetail.activeSkillMatches.length ? (
                                    <div className="mt-2 flex flex-wrap gap-2">
                                      {selectedHandoffDraftDetail.activeSkillMatches.map((match) => (
                                        <div
                                          key={match.id}
                                          className="rounded-full border border-[rgba(62,54,46,0.12)] bg-white px-3 py-1 text-[11px] text-[rgba(62,54,46,0.72)]"
                                        >
                                          <span className="font-medium">{match.title}</span>
                                          <span className="mx-1 text-[rgba(62,54,46,0.42)]">|</span>
                                          <span>{match.skillType}</span>
                                          {match.matchReason ? (
                                            <span className="ml-2 text-[rgba(62,54,46,0.54)]">
                                              {truncateText(match.matchReason, 48)}
                                            </span>
                                          ) : null}
                                        </div>
                                      ))}
                                    </div>
                                  ) : (
                                    <p className="mt-2 text-sm text-[rgba(62,54,46,0.64)]">
                                      No matched active skills recorded.
                                    </p>
                                  )}
                                </div>

                                <div className="rounded-[14px] border border-[rgba(62,54,46,0.12)] bg-[#F5F1E6] px-4 py-3">
                                  <p className="text-[11px] uppercase tracking-[0.16em] text-[rgba(62,54,46,0.54)]">
                                    Handoff message
                                  </p>
                                  <p className="mt-2 text-sm leading-6 text-[#3E362E]">
                                    {selectedHandoffDraftDetail.draftPayload.handoffMessage}
                                  </p>
                                </div>

                                <div className="rounded-[14px] border border-[rgba(62,54,46,0.12)] bg-[#F5F1E6] px-4 py-3">
                                  <p className="text-[11px] uppercase tracking-[0.16em] text-[rgba(62,54,46,0.54)]">
                                    Suggested steps
                                  </p>
                                  <div className="mt-2 space-y-2">
                                    {selectedHandoffDraftDetail.draftPayload.suggestedSteps.length ? (
                                      selectedHandoffDraftDetail.draftPayload.suggestedSteps.map((step, index) => (
                                        <p key={`handoff-step-${index}`} className="text-sm leading-6 text-[#3E362E]">
                                          {step}
                                        </p>
                                      ))
                                    ) : (
                                      <p className="text-sm leading-6 text-[rgba(62,54,46,0.64)]">
                                        No suggested steps recorded.
                                      </p>
                                    )}
                                  </div>
                                </div>

                                <p className="text-xs leading-6 text-[rgba(62,54,46,0.58)]">
                                  {selectedHandoffDraftDetail.draftPayload.safetyNote}
                                </p>
                              </div>
                            ) : (
                              <div className="mt-4 rounded-[14px] border border-dashed border-[rgba(62,54,46,0.18)] bg-[#F5F1E6] px-4 py-3 text-sm text-[rgba(62,54,46,0.64)]">
                                Select a draft to review the handoff preview.
                              </div>
                            )}
                          </div>
                        </div>
                      ) : (
                        <div className="mt-4 rounded-[16px] border border-dashed border-[rgba(62,54,46,0.18)] bg-white px-4 py-3 text-sm text-[rgba(62,54,46,0.64)]">
                          No saved handoff drafts yet.
                        </div>
                      )}
                    </div>
                    <WorkflowToolsPanel
                      activeAgent={activeAgentDetail}
                      activeAgentSkills={activeAgentSkills}
                    />
                      </div>
                    </details>

                    {draftPreview ? (
                      <div className="rounded-[18px] border border-[rgba(62,54,46,0.14)] bg-[#E5E0D3] px-5 py-4">
                        <div className="flex items-center justify-between gap-3">
                          <div>
                            <p className="text-[11px] uppercase tracking-[0.18em] text-[rgba(62,54,46,0.56)]">Draft target</p>
                            <p className="mt-1 text-sm font-semibold text-[#3E362E]">{draftPreview.targetName}</p>
                          </div>
                          <span className="rounded-full border border-[rgba(163,106,88,0.2)] bg-[rgba(163,106,88,0.1)] px-3 py-1 text-[11px] uppercase tracking-[0.14em] text-[#A36A58]">
                            {draftPreview.status}
                          </span>
                        </div>
                        <p className="mt-3 text-sm leading-6 text-[rgba(62,54,46,0.72)]">{draftPreview.text}</p>
                        <p className="mt-3 text-xs text-[rgba(62,54,46,0.56)]">Runtime is not connected yet.</p>
                      </div>
                    ) : (
                      <div className="flex flex-1 items-center justify-center rounded-[18px] border border-dashed border-[rgba(62,54,46,0.18)] bg-[#E5E0D3]/55 px-6 py-12 text-center">
                        <p className="max-w-md text-base text-[rgba(62,54,46,0.56)]">
                          Ask me anything...
                        </p>
                      </div>
                    )}
                  </div>

                  <div className="mt-5">
                    <CommandInput
                      notice={commandNotice}
                      modelOptions={MODEL_OPTIONS}
                      selectedModel={selectedModel}
                      onModelChange={setSelectedModel}
                      onSubmit={handleCommandSend}
                      placeholder={activeAgent ? `Ask ${activeAgent.name}...` : "Ask me anything..."}
                      resetSignal={commandResetSignal}
                    />
                  </div>

                  <div className="mt-5 grid gap-4 md:grid-cols-2">
                    <div className="rounded-[18px] border border-[rgba(62,54,46,0.14)] bg-[#E5E0D3] p-4">
                      <p className="text-sm font-semibold text-[#3E362E]">Create local draft</p>
                      <p className="mt-2 text-sm text-[rgba(62,54,46,0.62)]">
                        Enter or Send tetap membuat preview lokal saja.
                      </p>
                    </div>
                    <div className="rounded-[18px] border border-[rgba(62,54,46,0.14)] bg-[#E5E0D3] p-4">
                      <p className="text-sm font-semibold text-[#3E362E]">Review workspace status</p>
                      <div className="mt-2 space-y-2 text-sm text-[rgba(62,54,46,0.62)]">
                        {workspaceStatusItems.map((item) => (
                          <div key={item.label} className="flex items-center justify-between gap-3">
                            <span>{item.label}</span>
                            <span className="font-semibold text-[#3E362E]">{item.value}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
            </section>

              <aside className="border-t border-[rgba(62,54,46,0.14)] bg-[#E5E0D3] p-4 xl:h-screen xl:border-l xl:border-t-0 xl:overflow-hidden">
                <div className="flex h-full min-h-0 flex-col gap-4 xl:overflow-y-auto xl:pr-1">
                <div className="rounded-[18px] border border-[rgba(62,54,46,0.14)] bg-[#F5F1E6] p-4">
                  <p className="text-lg font-semibold text-[#3E362E]">Safety Center</p>
                  <div className="mt-4 rounded-[16px] border border-[rgba(62,54,46,0.14)] bg-[#E5E0D3] p-4">
                    <p className="text-sm font-medium text-[#3E362E]">Runtime execution disabled</p>
                    <p className="mt-2 text-sm text-[rgba(62,54,46,0.62)]">
                      Command draft, workflow, dan settings tetap preview-only.
                    </p>
                    <div className="mt-3 inline-flex rounded-full border border-[rgba(163,106,88,0.2)] bg-[rgba(163,106,88,0.1)] px-3 py-1 text-xs font-medium text-[#A36A58]">
                      Preview only
                    </div>
                  </div>
                </div>

                <div className="rounded-[18px] border border-[rgba(62,54,46,0.14)] bg-[#F5F1E6] p-4">
                  <div className="flex items-center justify-between gap-3">
                    <p className="text-sm font-semibold text-[#3E362E]">Activity Logs</p>
                    <span className="rounded-full border border-[rgba(163,106,88,0.2)] bg-[rgba(163,106,88,0.1)] px-2.5 py-1 text-[11px] uppercase tracking-[0.14em] text-[#A36A58]">
                      Read-only
                    </span>
                  </div>

                  {isLoadingActivityLogs ? (
                    <div className="mt-3 rounded-[14px] border border-[rgba(62,54,46,0.14)] bg-[#E5E0D3] px-4 py-3 text-sm text-[rgba(62,54,46,0.64)]">
                      Loading recent activity...
                    </div>
                  ) : activityLogsNotice ? (
                    <div className="mt-3 rounded-[14px] border border-[rgba(62,54,46,0.14)] bg-[#E5E0D3] px-4 py-3">
                      <p className="text-sm font-medium text-[#3E362E]">Activity logs unavailable</p>
                      <p className="mt-1 text-sm text-[rgba(62,54,46,0.64)]">
                        Dashboard stays usable while activity feed is unavailable.
                      </p>
                    </div>
                  ) : activityLogs.length ? (
                    <div className="mt-3 space-y-3">
                      {activityLogs.map((item) => (
                        <div
                          key={item.id}
                          className="rounded-[14px] border border-[rgba(62,54,46,0.14)] bg-[#E5E0D3] px-4 py-3"
                        >
                          <div className="flex items-start justify-between gap-3">
                            <div className="min-w-0">
                              <p className="text-[11px] uppercase tracking-[0.14em] text-[rgba(62,54,46,0.52)]">
                                {truncateText(item.eventType, 32)}
                              </p>
                              <p className="mt-1 text-sm leading-6 text-[#3E362E]">
                                {truncateText(item.message, 120)}
                              </p>
                            </div>
                            <span className="rounded-full border border-[rgba(62,54,46,0.14)] bg-[#F5F1E6] px-2.5 py-1 text-[10px] uppercase tracking-[0.14em] text-[rgba(62,54,46,0.68)]">
                              Read-only
                            </span>
                          </div>
                          <div className="mt-3 flex flex-wrap gap-2 text-[11px] text-[rgba(62,54,46,0.58)]">
                            {item.requestId ? (
                              <span className="rounded-full border border-[rgba(62,54,46,0.12)] bg-[#F5F1E6] px-2.5 py-1">
                                {truncateText(item.requestId, 18)}
                              </span>
                            ) : null}
                            {item.actorType ? (
                              <span className="rounded-full border border-[rgba(62,54,46,0.12)] bg-[#F5F1E6] px-2.5 py-1">
                                {truncateText(item.actorType, 16)}
                              </span>
                            ) : null}
                            <span className="rounded-full border border-[rgba(62,54,46,0.12)] bg-[#F5F1E6] px-2.5 py-1">
                              {formatDateTime(item.createdAt)}
                            </span>
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="mt-3 rounded-[14px] border border-[rgba(62,54,46,0.14)] bg-[#E5E0D3] px-4 py-3 text-sm text-[rgba(62,54,46,0.64)]">
                      No activity logs yet.
                    </div>
                  )}
                </div>

                <div className="rounded-[18px] border border-[rgba(62,54,46,0.14)] bg-[#F5F1E6] p-4">
                  <div className="flex items-center justify-between gap-3">
                    <p className="text-sm font-semibold text-[#3E362E]">Tasks Summary</p>
                    <span className="rounded-full border border-[rgba(163,106,88,0.2)] bg-[rgba(163,106,88,0.1)] px-2.5 py-1 text-[11px] uppercase tracking-[0.14em] text-[#A36A58]">
                      Read-only
                    </span>
                  </div>

                  {isLoadingTaskSummaries ? (
                    <div className="mt-3 rounded-[14px] border border-[rgba(62,54,46,0.14)] bg-[#E5E0D3] px-4 py-3 text-sm text-[rgba(62,54,46,0.64)]">
                      Loading recent tasks...
                    </div>
                  ) : taskSummariesNotice ? (
                    <div className="mt-3 rounded-[14px] border border-[rgba(62,54,46,0.14)] bg-[#E5E0D3] px-4 py-3">
                      <p className="text-sm font-medium text-[#3E362E]">Tasks preview unavailable</p>
                      <p className="mt-1 text-sm text-[rgba(62,54,46,0.64)]">
                        Dashboard stays usable while task summary is unavailable.
                      </p>
                    </div>
                  ) : (
                    <div className="mt-3 space-y-3">
                      <div className="rounded-[14px] border border-[rgba(62,54,46,0.14)] bg-[#E5E0D3] px-4 py-3">
                        <p className="text-xs uppercase tracking-[0.14em] text-[rgba(62,54,46,0.52)]">Loaded tasks</p>
                        <p className="mt-1 text-2xl font-semibold text-[#3E362E]">{taskSummaries.length}</p>
                      </div>
                      {taskSummaries.length ? (
                        taskSummaries.map((item) => (
                          <div
                            key={item.id}
                            className="rounded-[14px] border border-[rgba(62,54,46,0.14)] bg-[#E5E0D3] px-4 py-3"
                          >
                            <div className="flex items-start justify-between gap-3">
                              <div className="min-w-0">
                                <p className="text-[11px] uppercase tracking-[0.14em] text-[rgba(62,54,46,0.52)]">
                                  {truncateText(item.status, 16)}
                                </p>
                                <p className="mt-1 text-sm font-semibold text-[#3E362E]">
                                  {truncateText(item.requestId, 34)}
                                </p>
                              </div>
                              <span className="rounded-full border border-[rgba(62,54,46,0.14)] bg-[#F5F1E6] px-2.5 py-1 text-[10px] uppercase tracking-[0.14em] text-[rgba(62,54,46,0.68)]">
                                Preview only
                              </span>
                            </div>
                            <div className="mt-3 flex flex-wrap gap-2 text-[11px] text-[rgba(62,54,46,0.58)]">
                              {item.agentId ? (
                                <span className="rounded-full border border-[rgba(62,54,46,0.12)] bg-[#F5F1E6] px-2.5 py-1">
                                  {truncateText(item.agentId, 18)}
                                </span>
                              ) : null}
                              <span className="rounded-full border border-[rgba(62,54,46,0.12)] bg-[#F5F1E6] px-2.5 py-1">
                                {formatDateTime(item.createdAt)}
                              </span>
                            </div>
                          </div>
                        ))
                      ) : (
                        <div className="rounded-[14px] border border-[rgba(62,54,46,0.14)] bg-[#E5E0D3] px-4 py-3 text-sm text-[rgba(62,54,46,0.64)]">
                          No task records yet.
                        </div>
                      )}
                    </div>
                  )}
                </div>

                <div className="rounded-[18px] border border-[rgba(62,54,46,0.14)] bg-[#F5F1E6] p-4">
                  <div className="flex items-center justify-between gap-3">
                    <p className="text-sm font-semibold text-[#3E362E]">Pending Approvals</p>
                    <span className="rounded-full border border-[rgba(163,106,88,0.2)] bg-[rgba(163,106,88,0.1)] px-2.5 py-1 text-[11px] uppercase tracking-[0.14em] text-[#A36A58]">
                      Preview only
                    </span>
                  </div>

                  {isLoadingPendingApprovalSummaries ? (
                    <div className="mt-3 rounded-[14px] border border-[rgba(62,54,46,0.14)] bg-[#E5E0D3] px-4 py-3 text-sm text-[rgba(62,54,46,0.64)]">
                      Loading pending approvals...
                    </div>
                  ) : pendingApprovalSummariesNotice ? (
                    <div className="mt-3 rounded-[14px] border border-[rgba(62,54,46,0.14)] bg-[#E5E0D3] px-4 py-3">
                      <p className="text-sm font-medium text-[#3E362E]">Pending approvals unavailable</p>
                      <p className="mt-1 text-sm text-[rgba(62,54,46,0.64)]">
                        Dashboard stays usable while approval summary is unavailable.
                      </p>
                    </div>
                  ) : (
                    <div className="mt-3 space-y-3">
                      <div className="rounded-[14px] border border-[rgba(62,54,46,0.14)] bg-[#E5E0D3] px-4 py-3">
                        <p className="text-xs uppercase tracking-[0.14em] text-[rgba(62,54,46,0.52)]">Pending approvals</p>
                        <p className="mt-1 text-2xl font-semibold text-[#3E362E]">{pendingApprovalSummaries.length}</p>
                      </div>
                      {pendingApprovalSummaries.length ? (
                        pendingApprovalSummaries.map((item) => (
                          <div
                            key={item.id}
                            className="rounded-[14px] border border-[rgba(62,54,46,0.14)] bg-[#E5E0D3] px-4 py-3"
                          >
                            <div className="flex items-start justify-between gap-3">
                              <div className="min-w-0">
                                <p className="text-[11px] uppercase tracking-[0.14em] text-[rgba(62,54,46,0.52)]">
                                  {truncateText(item.riskLevel, 16)}
                                </p>
                                <p className="mt-1 text-sm font-semibold text-[#3E362E]">
                                  {truncateText(item.action, 34)}
                                </p>
                              </div>
                              <span className="rounded-full border border-[rgba(62,54,46,0.14)] bg-[#F5F1E6] px-2.5 py-1 text-[10px] uppercase tracking-[0.14em] text-[rgba(62,54,46,0.68)]">
                                Read-only
                              </span>
                            </div>
                            <div className="mt-3 flex flex-wrap gap-2 text-[11px] text-[rgba(62,54,46,0.58)]">
                              <span className="rounded-full border border-[rgba(62,54,46,0.12)] bg-[#F5F1E6] px-2.5 py-1">
                                {truncateText(item.status, 16)}
                              </span>
                              <span className="rounded-full border border-[rgba(62,54,46,0.12)] bg-[#F5F1E6] px-2.5 py-1">
                                {formatDateTime(item.createdAt)}
                              </span>
                            </div>
                          </div>
                        ))
                      ) : (
                        <div className="rounded-[14px] border border-[rgba(62,54,46,0.14)] bg-[#E5E0D3] px-4 py-3 text-sm text-[rgba(62,54,46,0.64)]">
                          No pending approvals.
                        </div>
                      )}
                    </div>
                  )}
                </div>
              </div>
            </aside>
          </div>

          {floatingCards}
        </div>
      </AppShell>
    </ProtectedRoute>
  );
}
