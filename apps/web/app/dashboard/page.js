"use client";

import { useEffect, useMemo, useState } from "react";

import AppShell from "../../components/AppShell";
import CommandInput from "../../components/CommandInput";
import FloatingCard from "../../components/FloatingCard";
import ProtectedRoute from "../../components/ProtectedRoute";
import Sidebar from "../../components/Sidebar";
import TemplateCard from "../../components/TemplateCard";
import {
  createAgent,
  get,
  getActivityLogs,
  getCurrentUser,
  getModelProviders,
  getSkills
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
    status: skill?.status || "inactive"
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

  return "Failed to create agent.";
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

const SKILL_TEMPLATES = [
  {
    name: "Reminder / Alarm",
    icon: "RA",
    description: "Pengingat terjadwal untuk tugas personal dan kerja rutin."
  },
  {
    name: "Email",
    icon: "EM",
    description: "Template agent email untuk alur komunikasi yang aman."
  },
  {
    name: "Notification",
    icon: "NT",
    description: "Template notifikasi internal lintas kanal."
  },
  {
    name: "Report",
    icon: "RP",
    description: "Rangkuman laporan berkala dan hasil monitoring ringan."
  },
  {
    name: "API Data Fetcher",
    icon: "AP",
    description: "Konsep agent pengambil data API via backend nanti."
  },
  {
    name: "Webhook Automation",
    icon: "WA",
    description: "Placeholder otomasi alur event tanpa eksekusi nyata."
  },
  {
    name: "Database Saver",
    icon: "DB",
    description: "Konsep penyimpanan data terkontrol dengan approval."
  }
];

const RECOMMENDED_SKILLS = [
  "Web Search",
  "Data Analysis",
  "Document Summarization",
  "Code Interpreter",
  "Email Assistant"
];

const MODEL_OPTIONS = ["model", "gpt-4.1", "gpt-4o-mini"];
const INITIAL_AGENT_FORM = {
  name: "",
  icon: "",
  skillId: "",
  skillName: "",
  providerId: "",
  workflow: "use",
  pinToSidebar: true
};

export default function DashboardPage() {
  const [workspace, setWorkspace] = useState({
    currentUser: null,
    agents: []
  });
  const [availableSkills, setAvailableSkills] = useState([]);
  const [availableProviders, setAvailableProviders] = useState([]);
  const [isLoadingSkills, setIsLoadingSkills] = useState(true);
  const [isLoadingProviders, setIsLoadingProviders] = useState(true);
  const [activityLogs, setActivityLogs] = useState([]);
  const [isLoadingActivityLogs, setIsLoadingActivityLogs] = useState(true);
  const [activityLogsNotice, setActivityLogsNotice] = useState("");
  const [skillLoadNotice, setSkillLoadNotice] = useState("");
  const [providerLoadNotice, setProviderLoadNotice] = useState("");
  const [cards, setCards] = useState(buildInitialCards);
  const [zIndexSeed, setZIndexSeed] = useState(30);
  const [commandNotice, setCommandNotice] = useState("");
  const [draftPreview, setDraftPreview] = useState(null);
  const [commandResetSignal, setCommandResetSignal] = useState(0);
  const [skillQuery, setSkillQuery] = useState("");
  const [workflowMode, setWorkflowMode] = useState("template");
  const [createNotice, setCreateNotice] = useState("");
  const [importNotice, setImportNotice] = useState("");
  const [pinnedIds, setPinnedIds] = useState([]);
  const [didLoadPinnedIds, setDidLoadPinnedIds] = useState(false);
  const [activeAgentId, setActiveAgentId] = useState(null);
  const [didLoadActiveAgentId, setDidLoadActiveAgentId] = useState(false);
  const [isCreatingAgent, setIsCreatingAgent] = useState(false);
  const [selectedModel, setSelectedModel] = useState(MODEL_OPTIONS[0]);
  const [agentForm, setAgentForm] = useState(INITIAL_AGENT_FORM);

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
    let isMounted = true;

    async function loadWorkspace() {
      const results = await Promise.allSettled([
        getCurrentUser(),
        get("/agents"),
        getSkills(),
        getModelProviders()
      ]);

      if (!isMounted) {
        return;
      }

      const [currentUserResult, agentsResult, skillsResult, providersResult] = results;
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

      if (providersResult.status === "fulfilled") {
        setAvailableProviders(normalizeCollection(providersResult.value).map(buildProviderViewModel));
        setProviderLoadNotice("");
      } else {
        setAvailableProviders([]);
        setProviderLoadNotice("Daftar provider belum bisa dimuat. Form tetap bisa dipakai.");
      }
      setIsLoadingProviders(false);
    }

    loadWorkspace();

    return () => {
      isMounted = false;
    };
  }, []);

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

  const allAgents = useMemo(() => workspace.agents, [workspace.agents]);

  const pinnedAgents = useMemo(
    () => allAgents.filter((agent) => pinnedIds.includes(agent.id)),
    [allAgents, pinnedIds]
  );

  const activeAgent = useMemo(
    () => pinnedAgents.find((agent) => agent.id === activeAgentId) || null,
    [activeAgentId, pinnedAgents]
  );
  const workspaceStatusItems = useMemo(
    () => [
      { label: "Pinned agents", value: String(pinnedAgents.length) },
      { label: "Skills loaded", value: String(availableSkills.length) },
      { label: "Providers loaded", value: String(availableProviders.length) }
    ],
    [availableProviders.length, availableSkills.length, pinnedAgents.length]
  );

  const filteredTemplates = useMemo(() => {
    const query = skillQuery.trim().toLowerCase();
    if (!query) {
      return SKILL_TEMPLATES;
    }

    return SKILL_TEMPLATES.filter((template) =>
      `${template.name} ${template.description}`.toLowerCase().includes(query)
    );
  }, [skillQuery]);

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

  async function handleCreateAgentSave() {
    const trimmedName = agentForm.name.trim();

    if (!trimmedName) {
      setCreateNotice("Nama agent masih kosong.");
      return;
    }

    setIsCreatingAgent(true);
    setCreateNotice("Saving...");

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
      setCreateNotice("Agent created.");
    } catch (error) {
      setCreateNotice(getSafeCreateNotice(error));
    } finally {
      setIsCreatingAgent(false);
    }
  }

  function handleCreateAgentDelete() {
    setAgentForm(INITIAL_AGENT_FORM);
    setCreateNotice("Draft dibersihkan.");
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
        subtitle="Design and configure your personal AI agent"
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
                Delete
              </button>
            </div>
            {createNotice ? <p className="text-xs text-[rgba(62,54,46,0.66)]">{createNotice}</p> : null}
          </div>
        }
      >
        <label className="grid gap-2">
          <span className="text-[17px] font-medium text-[#3E362E]">Name</span>
          <input
            value={agentForm.name}
            onChange={(event) => handleAgentFormChange("name", event.target.value)}
            placeholder="Enter agent name"
            className="rounded-[14px] border border-[rgba(62,54,46,0.14)] bg-[#F5F1E6] px-4 py-3 text-[16px] text-[#3E362E] outline-none transition placeholder:text-[rgba(62,54,46,0.4)] focus:border-[#A36A58]"
          />
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
          {skillLoadNotice ? <p className="text-xs text-[#A36A58]">{skillLoadNotice}</p> : null}
          {!isLoadingSkills && !availableSkills.length && !skillLoadNotice ? (
            <p className="text-xs text-[rgba(62,54,46,0.58)]">No skills available yet.</p>
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
          {providerLoadNotice ? <p className="text-xs text-[#A36A58]">{providerLoadNotice}</p> : null}
          {!isLoadingProviders && !availableProviders.length && !providerLoadNotice ? (
            <p className="text-xs text-[rgba(62,54,46,0.58)]">No provider configured yet.</p>
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
        subtitle="Browse skill templates for your agents"
        open={cards.skills.open}
        position={{ x: cards.skills.x, y: cards.skills.y }}
        zIndex={cards.skills.z}
        widthClassName="w-[420px] max-w-[calc(100vw-2rem)]"
        bodyClassName="space-y-4"
        onClose={() => closeCard("skills")}
        onMove={(nextPosition) => moveCard("skills", nextPosition)}
        onFocus={() => bringCardToFront("skills")}
      >
        <input
          value={skillQuery}
          onChange={(event) => setSkillQuery(event.target.value)}
          placeholder="Search skill templates"
          className="w-full rounded-[14px] border border-[rgba(62,54,46,0.14)] bg-[#F5F1E6] px-4 py-3 text-sm text-[#3E362E] outline-none transition placeholder:text-[rgba(62,54,46,0.42)] focus:border-[#A36A58]"
        />

        <div className="space-y-3">
          {filteredTemplates.map((template) => (
            <TemplateCard
              key={template.name}
              name={template.name}
              icon={template.icon}
              description={template.description}
              buttonLabel="Preview"
              onAction={() => setImportNotice(`${template.name} dipilih.`)}
            />
          ))}
        </div>

        {importNotice ? <p className="text-xs text-[rgba(62,54,46,0.6)]">{importNotice}</p> : null}
      </FloatingCard>

      <FloatingCard
        title="Settings"
        subtitle="Manage your workspace preferences"
        open={cards.settings.open}
        position={{ x: cards.settings.x, y: cards.settings.y }}
        zIndex={cards.settings.z}
        widthClassName="w-[440px] max-w-[calc(100vw-2rem)]"
        bodyClassName="space-y-4"
        onClose={() => closeCard("settings")}
        onMove={(nextPosition) => moveCard("settings", nextPosition)}
        onFocus={() => bringCardToFront("settings")}
        footer={
          <div className="space-y-3">
            <div className="flex gap-3">
              <button
                type="button"
                disabled
                className="flex-1 cursor-not-allowed rounded-full border border-[rgba(62,54,46,0.14)] bg-[#F5F1E6] px-4 py-2.5 text-sm text-[rgba(62,54,46,0.52)] opacity-70"
              >
                Preview only
              </button>
              <button
                type="button"
                disabled
                className="flex-1 cursor-not-allowed rounded-full border border-[rgba(62,54,46,0.14)] bg-[#F5F1E6] px-4 py-2.5 text-sm font-medium text-[rgba(62,54,46,0.52)] opacity-70"
              >
                Save disabled
              </button>
            </div>
            <p className="text-xs text-[rgba(62,54,46,0.6)]">Preview only. Save and connection test stay disabled for this MVP step.</p>
          </div>
        }
      >
        <section className="rounded-[16px] border border-[rgba(62,54,46,0.14)] bg-[#F5F1E6] p-4">
          <p className="text-sm font-medium text-[#3E362E]">Profile</p>
          <p className="mt-2 text-sm text-[rgba(62,54,46,0.64)]">
            {workspace.currentUser?.display_name || "Workspace owner"}
          </p>
        </section>

        <section className="rounded-[16px] border border-[rgba(62,54,46,0.14)] bg-[#F5F1E6] p-4">
          <p className="text-sm font-medium text-[#3E362E]">Appearance</p>
          <div className="mt-3 flex gap-2">
            <button type="button" className="rounded-full border border-[rgba(62,54,46,0.14)] bg-[#E5E0D3] px-3 py-1.5 text-xs text-[rgba(62,54,46,0.72)]">
              Ivory
            </button>
            <button type="button" className="rounded-full border border-[rgba(62,54,46,0.14)] bg-[#E5E0D3] px-3 py-1.5 text-xs text-[rgba(62,54,46,0.72)]">
              Minimal
            </button>
          </div>
        </section>

        <section className="rounded-[16px] border border-[rgba(62,54,46,0.14)] bg-[#F5F1E6] p-4">
          <p className="text-sm font-medium text-[#3E362E]">AI Model / Brain</p>
          <div className="mt-3 grid gap-3">
            <input
              placeholder="Provider preview"
              disabled
              className="rounded-[14px] border border-[rgba(62,54,46,0.14)] bg-[#E5E0D3] px-4 py-3 text-sm text-[#3E362E] outline-none"
            />
            <select disabled className="rounded-[14px] border border-[rgba(62,54,46,0.14)] bg-[#E5E0D3] px-4 py-3 text-sm text-[rgba(62,54,46,0.6)] outline-none">
              <option>Preview only</option>
            </select>
            <input
              placeholder="Default model preview"
              disabled
              className="rounded-[14px] border border-[rgba(62,54,46,0.14)] bg-[#E5E0D3] px-4 py-3 text-sm text-[#3E362E] outline-none"
            />
            <input
              placeholder="Fallback model preview"
              disabled
              className="rounded-[14px] border border-[rgba(62,54,46,0.14)] bg-[#E5E0D3] px-4 py-3 text-sm text-[#3E362E] outline-none"
            />
            <div className="rounded-[14px] border border-[rgba(62,54,46,0.14)] bg-[#E5E0D3] px-4 py-3 text-sm text-[rgba(62,54,46,0.72)]">
              Status: Not connected yet
            </div>
          </div>
        </section>

        <section className="rounded-[16px] border border-[rgba(62,54,46,0.14)] bg-[#F5F1E6] p-4">
          <p className="text-sm font-medium text-[#3E362E]">n8n Connection</p>
          <p className="mt-2 text-sm text-[rgba(62,54,46,0.64)]">Preview only. Runtime disabled.</p>
        </section>

        <section className="rounded-[16px] border border-[rgba(62,54,46,0.14)] bg-[#F5F1E6] p-4">
          <p className="text-sm font-medium text-[#3E362E]">Security</p>
          <p className="mt-2 text-sm text-[rgba(62,54,46,0.64)]">Backend-managed secrets only</p>
        </section>
      </FloatingCard>

      <FloatingCard
        title="Workflow n8n"
        subtitle="Manage workflow connection concept."
        open={cards.workflow.open}
        position={{ x: cards.workflow.x, y: cards.workflow.y }}
        zIndex={cards.workflow.z}
        widthClassName="w-[380px] max-w-[calc(100vw-2rem)]"
        bodyClassName="space-y-4"
        onClose={() => closeCard("workflow")}
        onMove={(nextPosition) => moveCard("workflow", nextPosition)}
        onFocus={() => bringCardToFront("workflow")}
      >
        <div className="grid gap-2">
          <label className="rounded-[14px] border border-[rgba(62,54,46,0.14)] bg-[#F5F1E6] px-4 py-4 text-sm text-[rgba(62,54,46,0.78)]">
            <input
              type="radio"
              name="workflow-mode"
              value="template"
              checked={workflowMode === "template"}
              onChange={(event) => setWorkflowMode(event.target.value)}
              className="mr-3"
            />
            Use template workflow
          </label>
          <label className="rounded-[14px] border border-[rgba(62,54,46,0.14)] bg-[#F5F1E6] px-4 py-4 text-sm text-[rgba(62,54,46,0.78)]">
            <input
              type="radio"
              name="workflow-mode"
              value="existing"
              checked={workflowMode === "existing"}
              onChange={(event) => setWorkflowMode(event.target.value)}
              className="mr-3"
            />
            Connect existing n8n workflow
          </label>
          <label className="rounded-[14px] border border-[rgba(62,54,46,0.14)] bg-[#F5F1E6] px-4 py-4 text-sm text-[rgba(62,54,46,0.78)]">
            <input
              type="radio"
              name="workflow-mode"
              value="manual"
              checked={workflowMode === "manual"}
              onChange={(event) => setWorkflowMode(event.target.value)}
              className="mr-3"
            />
            Create/edit manually in n8n
          </label>
        </div>

        <button
          type="button"
          disabled
          className="w-full cursor-not-allowed rounded-[14px] border border-[rgba(62,54,46,0.14)] bg-[#F5F1E6] px-4 py-4 text-sm font-medium text-[rgba(62,54,46,0.54)] opacity-70"
        >
          Runtime disabled
        </button>

        <p className="text-xs text-[rgba(62,54,46,0.6)]">Preview only. n8n connection and workflow execution stay disabled for this MVP step.</p>
      </FloatingCard>
    </>
  );

  return (
    <ProtectedRoute>
      <AppShell minimal sidebar={canvasSidebar}>
        <div className="relative min-h-screen bg-[#F5F1E6]">
          <div className="grid min-h-screen grid-cols-1 xl:grid-cols-[minmax(0,1fr)_320px]">
            <section className="min-w-0 p-6">
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
                        {activeAgent
                          ? `Ready to draft commands for ${activeAgent.name}.`
                          : "Select active associate or start drafting locally."}
                      </p>
                    </div>

                    {activeAgent ? (
                      <div className="rounded-[18px] border border-[rgba(62,54,46,0.14)] bg-[#E5E0D3] px-5 py-4">
                        <p className="text-[11px] uppercase tracking-[0.18em] text-[rgba(62,54,46,0.56)]">
                          Active associate
                        </p>
                        <p className="mt-2 text-xl font-semibold text-[#3E362E]">{activeAgent.name}</p>
                        <div className="mt-2 flex flex-wrap gap-3 text-xs text-[rgba(62,54,46,0.64)]">
                          <span>Status: {activeAgent.status}</span>
                          {activeAgent.defaultModelName ? <span>Model: {activeAgent.defaultModelName}</span> : null}
                        </div>
                        {activeAgent.description ? (
                          <p className="mt-3 text-sm leading-6 text-[rgba(62,54,46,0.64)]">{activeAgent.description}</p>
                        ) : null}
                      </div>
                    ) : null}

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
            </section>

            <aside className="border-t border-[rgba(62,54,46,0.14)] bg-[#E5E0D3] p-4 xl:border-l xl:border-t-0">
              <div className="flex h-full min-h-[320px] flex-col gap-4">
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
              </div>
            </aside>
          </div>

          {floatingCards}
        </div>
      </AppShell>
    </ProtectedRoute>
  );
}
