"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";

import {
  deleteSession,
  getSession,
  listSessions,
  orchestratorChat
} from "../lib/apiClient";
import { formatDateTime } from "../lib/format";
import WorkflowSuggestionList from "./WorkflowSuggestionList";


function getFriendlyWorkspaceChatErrorMessage(error) {
  const message = error instanceof Error ? error.message.trim() : "";

  if (message === "Terlalu banyak pesan, tunggu sebentar") {
    return message;
  }

  if (message === "No LLM provider configured for this agent") {
    return "Configure your model provider first.";
  }

  if (message === "No API key found. Please configure your provider first.") {
    return "Please save your provider API key first.";
  }

  return message || "Failed to send workspace message.";
}

function getSafeSessionMessage(error, fallbackMessage) {
  const message = error instanceof Error ? error.message.trim() : "";
  return message || fallbackMessage;
}

function buildMessageId(role, index) {
  return `${role}-${index + 1}`;
}

function normalizeCollection(payload) {
  if (Array.isArray(payload)) {
    return payload;
  }

  if (Array.isArray(payload?.sessions)) {
    return payload.sessions;
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

function buildSessionViewModel(session) {
  return {
    id: String(session?.id || ""),
    title: session?.title || "New chat",
    sessionType: session?.session_type || "orchestrator",
    agentId: session?.agent_id ? String(session.agent_id) : null,
    agentName: session?.agent_name || null,
    messageCount: Number(session?.message_count || 0),
    createdAt: session?.created_at || "",
    updatedAt: session?.updated_at || ""
  };
}


export default function WorkspaceChatPanel() {
  const [messages, setMessages] = useState([]);
  const [draft, setDraft] = useState("");
  const [isSending, setIsSending] = useState(false);
  const [isLoadingSessions, setIsLoadingSessions] = useState(true);
  const [openingSessionId, setOpeningSessionId] = useState("");
  const [deletingSessionId, setDeletingSessionId] = useState("");
  const [error, setError] = useState("");
  const [warning, setWarning] = useState("");
  const [responseMeta, setResponseMeta] = useState(null);
  const [sessionId, setSessionId] = useState(null);
  const [sessions, setSessions] = useState([]);
  const scrollAnchorRef = useRef(null);

  const loadSessions = useCallback(async () => {
    setIsLoadingSessions(true);

    try {
      const response = await listSessions();
      const nextSessions = normalizeCollection(response)
        .filter((session) => session?.session_type === "orchestrator")
        .map(buildSessionViewModel)
        .filter((session) => Boolean(session.id))
        .slice(0, 10);

      setSessions(nextSessions);
    } catch (sessionError) {
      setSessions([]);
      setError((currentError) => currentError || getSafeSessionMessage(sessionError, "Workspace sessions unavailable."));
    } finally {
      setIsLoadingSessions(false);
    }
  }, []);

  useEffect(() => {
    void loadSessions();
  }, [loadSessions]);

  useEffect(() => {
    if (!scrollAnchorRef.current) {
      return;
    }

    scrollAnchorRef.current.scrollIntoView({ block: "end", behavior: "smooth" });
  }, [messages, isSending]);

  const activeSession = useMemo(
    () => sessions.find((item) => item.id === sessionId) || null,
    [sessionId, sessions]
  );

  const currentSessionLabel = activeSession?.title || (sessionId ? "Loaded session" : "New chat");
  const routedAgentId = responseMeta?.routedToAgentId ? String(responseMeta.routedToAgentId) : "";

  const handleNewChat = useCallback(() => {
    setMessages([]);
    setDraft("");
    setError("");
    setWarning("");
    setResponseMeta(null);
    setSessionId(null);
  }, []);

  const handleClearDraft = useCallback(() => {
    setDraft("");
  }, []);

  const handleOpenSession = useCallback(
    async (targetSession) => {
      if (!targetSession?.id || openingSessionId) {
        return;
      }

      setOpeningSessionId(targetSession.id);
      setError("");
      setWarning("");

      try {
        const response = await getSession(targetSession.id);
        const nextMessages = Array.isArray(response?.messages)
          ? response.messages.map((message) => ({
              role: message.role,
              content: message.content
            }))
          : [];

        setMessages(nextMessages);
        setSessionId(targetSession.id);
        setDraft("");
        setResponseMeta(null);
      } catch (sessionError) {
        setError(getSafeSessionMessage(sessionError, "Unable to open session."));
      } finally {
        setOpeningSessionId("");
      }
    },
    [openingSessionId]
  );

  const handleDeleteSession = useCallback(
    async (targetSession) => {
      if (!targetSession?.id || deletingSessionId) {
        return;
      }

      setDeletingSessionId(targetSession.id);
      setError("");

      try {
        await deleteSession(targetSession.id);
        setSessions((currentSessions) => currentSessions.filter((item) => item.id !== targetSession.id));

        if (sessionId === targetSession.id) {
          handleNewChat();
        }
      } catch (sessionError) {
        setError(getSafeSessionMessage(sessionError, "Unable to delete session."));
      } finally {
        setDeletingSessionId("");
      }
    },
    [deletingSessionId, handleNewChat, sessionId]
  );

  async function handleSubmit(event) {
    event.preventDefault();

    if (isSending) {
      return;
    }

    const trimmedDraft = draft.trim();
    if (!trimmedDraft) {
      return;
    }

    const userMessage = { role: "user", content: trimmedDraft };
    const nextMessages = [...messages, userMessage];

    setMessages(nextMessages);
    setDraft("");
    setError("");
    setIsSending(true);

    try {
      const response = await orchestratorChat(trimmedDraft, nextMessages, sessionId);
      setMessages((currentMessages) => [
        ...currentMessages,
        { role: "assistant", content: response.reply }
      ]);
      setSessionId(response.session_id || sessionId || null);
      setResponseMeta({
        status: response.status,
        confidence: response.confidence,
        routedToAgentId: response.routed_to_agent_id || "",
        routedToAgentName: response.routed_to_agent_name || "",
        routingReasons: Array.isArray(response.routing_reasons) ? response.routing_reasons : [],
        provider: response.provider || "",
        model: response.model || "",
        promptSkillsUsed: Array.isArray(response.prompt_skills_used)
          ? response.prompt_skills_used
          : [],
        knowledgeSkillsUsed: Array.isArray(response.knowledge_skills_used)
          ? response.knowledge_skills_used
          : [],
        knowledgeTruncated: Boolean(response.knowledge_truncated),
        workflowSuggestions: Array.isArray(response.workflow_suggestions)
          ? response.workflow_suggestions
          : []
      });
      setWarning(response.warning || "");
      void loadSessions();
    } catch (workspaceError) {
      setError(getFriendlyWorkspaceChatErrorMessage(workspaceError));
    } finally {
      setIsSending(false);
    }
  }

  const canSend = Boolean(draft.trim()) && !isSending;
  const isRouted = responseMeta?.status === "routed";

  return (
    <div className="rounded-[18px] border border-[rgba(62,54,46,0.14)] bg-[#F5F1E6] p-4">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="min-w-0">
          <p className="text-[11px] uppercase tracking-[0.18em] text-[rgba(62,54,46,0.56)]">
            Workspace Chat
          </p>
          <p className="mt-1 text-sm font-semibold text-[#3E362E]">
            Orchestrator routes your message to the best matching agent.
          </p>
          <p className="mt-1 text-sm leading-6 text-[rgba(62,54,46,0.64)]">
            Chat history stays in DB per session and is encrypted at rest.
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <span className="rounded-full border border-[rgba(163,106,88,0.2)] bg-[rgba(163,106,88,0.1)] px-3 py-1 text-[11px] uppercase tracking-[0.14em] text-[#A36A58]">
            Orchestrator
          </span>
          {sessionId ? (
            <span className="rounded-full border border-[rgba(62,54,46,0.12)] bg-white px-3 py-1 text-[11px] text-[rgba(62,54,46,0.72)]">
              Session: {currentSessionLabel}
            </span>
          ) : null}
        </div>
      </div>

      <div className="mt-3 flex flex-wrap gap-2">
        {responseMeta?.status ? (
          <span className="rounded-full border border-[rgba(62,54,46,0.12)] bg-white px-3 py-1 text-[11px] text-[rgba(62,54,46,0.72)]">
            {responseMeta.status === "routed" ? "Routed" : "Fallback"}
          </span>
        ) : null}
        {responseMeta?.confidence ? (
          <span className="rounded-full border border-[rgba(62,54,46,0.12)] bg-white px-3 py-1 text-[11px] text-[rgba(62,54,46,0.72)]">
            Confidence: {responseMeta.confidence}
          </span>
        ) : null}
        {isRouted && responseMeta?.routedToAgentName ? (
          <span className="rounded-full border border-[rgba(96,112,86,0.18)] bg-[rgba(96,112,86,0.08)] px-3 py-1 text-[11px] text-[#607056]">
            Agent: {responseMeta.routedToAgentName}
          </span>
        ) : null}
        {responseMeta?.provider ? (
          <span className="rounded-full border border-[rgba(62,54,46,0.12)] bg-white px-3 py-1 text-[11px] text-[rgba(62,54,46,0.72)]">
            Provider: {responseMeta.provider}
          </span>
        ) : null}
        {responseMeta?.model ? (
          <span className="rounded-full border border-[rgba(62,54,46,0.12)] bg-white px-3 py-1 text-[11px] text-[rgba(62,54,46,0.72)]">
            Model: {responseMeta.model}
          </span>
        ) : null}
      </div>

      {responseMeta?.status === "fallback" ? (
        <div className="mt-3 rounded-[14px] border border-[rgba(163,142,88,0.18)] bg-[rgba(163,142,88,0.08)] px-4 py-3 text-sm leading-6 text-[rgba(62,54,46,0.74)]">
          No agent matched
        </div>
      ) : null}

      {responseMeta?.routingReasons?.length ? (
        <div className="mt-3 rounded-[14px] border border-[rgba(62,54,46,0.12)] bg-white px-4 py-3">
          <p className="text-[11px] uppercase tracking-[0.14em] text-[rgba(62,54,46,0.52)]">
            Routing reasons
          </p>
          <ul className="mt-2 space-y-1 text-sm leading-6 text-[rgba(62,54,46,0.72)]">
            {responseMeta.routingReasons.map((reason, index) => (
              <li key={`${reason}-${index}`} className="flex gap-2">
                <span className="mt-[9px] h-1.5 w-1.5 rounded-full bg-[rgba(163,106,88,0.55)]" />
                <span className="min-w-0">{reason}</span>
              </li>
            ))}
          </ul>
        </div>
      ) : null}

      {responseMeta?.promptSkillsUsed?.length ? (
        <div className="mt-3 flex flex-wrap gap-2">
          {responseMeta.promptSkillsUsed.map((skillName) => (
            <span
              key={skillName}
              className="rounded-full border border-[rgba(96,112,86,0.18)] bg-[rgba(96,112,86,0.08)] px-3 py-1 text-[11px] text-[#607056]"
            >
              {skillName}
            </span>
          ))}
        </div>
      ) : null}

      {responseMeta?.knowledgeSkillsUsed?.length ? (
        <div className="mt-3 flex flex-wrap gap-2">
          {responseMeta.knowledgeSkillsUsed.map((skillName) => (
            <span
              key={skillName}
              className="rounded-full border border-[rgba(105,92,72,0.18)] bg-[rgba(105,92,72,0.08)] px-3 py-1 text-[11px] text-[rgba(105,92,72,0.92)]"
            >
              Knowledge: {skillName}
            </span>
          ))}
        </div>
      ) : null}

      {responseMeta?.knowledgeTruncated ? (
        <p className="mt-2 text-xs leading-5 text-[rgba(62,54,46,0.58)]">
          Sebagian knowledge dipotong karena terlalu panjang.
        </p>
      ) : null}

      <WorkflowSuggestionList
        agentId={routedAgentId}
        suggestions={responseMeta?.workflowSuggestions || []}
      />

      {warning ? (
        <div className="mt-3 rounded-[14px] border border-[rgba(163,142,88,0.18)] bg-[rgba(163,142,88,0.08)] px-4 py-3 text-sm leading-6 text-[rgba(62,54,46,0.74)]">
          {warning}
        </div>
      ) : null}

      {error ? (
        <div className="mt-3 rounded-[14px] border border-[rgba(163,106,88,0.2)] bg-[rgba(163,106,88,0.1)] px-4 py-3 text-sm leading-6 text-[#A36A58]">
          {error}
        </div>
      ) : null}

      <div className="mt-4 rounded-[16px] border border-[rgba(62,54,46,0.12)] bg-white p-3">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <p className="text-[11px] uppercase tracking-[0.14em] text-[rgba(62,54,46,0.52)]">
              Session history
            </p>
            <p className="mt-1 text-sm font-semibold text-[#3E362E]">
              Recent workspace sessions
            </p>
          </div>
          <button
            type="button"
            onClick={handleNewChat}
            className="rounded-full border border-[rgba(62,54,46,0.14)] bg-[#F5F1E6] px-3 py-1.5 text-xs font-medium text-[#3E362E] transition hover:bg-[#efe7d6]"
          >
            New Chat
          </button>
        </div>

        <div className="mt-3 max-h-[196px] overflow-y-auto pr-1">
          {isLoadingSessions ? (
            <div className="rounded-[14px] border border-[rgba(62,54,46,0.12)] bg-[#F5F1E6] px-4 py-3 text-sm text-[rgba(62,54,46,0.64)]">
              Loading sessions...
            </div>
          ) : sessions.length ? (
            <div className="space-y-2">
              {sessions.map((item) => {
                const isActive = item.id === sessionId;
                return (
                  <div
                    key={item.id}
                    className={`rounded-[14px] border px-4 py-3 ${
                      isActive
                        ? "border-[rgba(163,106,88,0.22)] bg-[rgba(163,106,88,0.08)]"
                        : "border-[rgba(62,54,46,0.12)] bg-[#F5F1E6]"
                    }`}
                  >
                    <div className="flex flex-wrap items-start justify-between gap-3">
                      <div className="min-w-0">
                        <p className="text-sm font-semibold text-[#3E362E]">{item.title}</p>
                        <p className="mt-1 text-xs leading-6 text-[rgba(62,54,46,0.62)]">
                          {item.messageCount} messages
                          {item.updatedAt ? ` Updated ${formatDateTime(item.updatedAt)}` : ""}
                        </p>
                      </div>
                      <div className="flex flex-wrap gap-2">
                        <button
                          type="button"
                          onClick={() => handleOpenSession(item)}
                          disabled={openingSessionId === item.id || deletingSessionId === item.id}
                          className="rounded-full border border-[rgba(62,54,46,0.14)] bg-white px-3 py-1.5 text-xs font-medium text-[#3E362E] transition hover:bg-[#efe7d6] disabled:cursor-not-allowed disabled:opacity-70"
                        >
                          {openingSessionId === item.id ? "Opening..." : "Open"}
                        </button>
                        <button
                          type="button"
                          onClick={() => handleDeleteSession(item)}
                          disabled={deletingSessionId === item.id || openingSessionId === item.id}
                          className="rounded-full border border-[rgba(163,106,88,0.18)] bg-[rgba(163,106,88,0.08)] px-3 py-1.5 text-xs font-medium text-[#A36A58] transition hover:bg-[rgba(163,106,88,0.12)] disabled:cursor-not-allowed disabled:opacity-70"
                        >
                          {deletingSessionId === item.id ? "Deleting..." : "Delete"}
                        </button>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          ) : (
            <div className="rounded-[14px] border border-dashed border-[rgba(62,54,46,0.16)] bg-[rgba(229,224,211,0.34)] px-4 py-3 text-sm leading-6 text-[rgba(62,54,46,0.6)]">
              No saved workspace sessions yet.
            </div>
          )}
        </div>
      </div>

      <div className="scrollbar-thin mt-4 max-h-[320px] overflow-y-auto rounded-[16px] border border-[rgba(62,54,46,0.12)] bg-white p-3">
        {messages.length ? (
          <div className="space-y-3">
            {messages.map((message, index) => (
              <div
                key={buildMessageId(message.role, index)}
                className={`flex ${message.role === "user" ? "justify-end" : "justify-start"}`}
              >
                <div
                  className={`max-w-[85%] rounded-[16px] px-4 py-3 text-sm leading-6 ${
                    message.role === "user"
                      ? "bg-[#A36A58] text-white"
                      : "border border-[rgba(62,54,46,0.12)] bg-[#F5F1E6] text-[#3E362E]"
                  }`}
                >
                  <p className="whitespace-pre-wrap break-words">{message.content}</p>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="flex min-h-[160px] items-center justify-center rounded-[14px] border border-dashed border-[rgba(62,54,46,0.16)] bg-[rgba(229,224,211,0.34)] px-4 py-8 text-center text-sm leading-6 text-[rgba(62,54,46,0.6)]">
            Mulai percakapan workspace dengan task yang ingin kamu delegasikan.
          </div>
        )}
        <div ref={scrollAnchorRef} />
      </div>

      <form onSubmit={handleSubmit} className="mt-4 space-y-3">
        <label className="grid gap-2">
          <span className="text-xs uppercase tracking-[0.14em] text-[rgba(62,54,46,0.52)]">
            Task
          </span>
          <textarea
            value={draft}
            onChange={(event) => setDraft(event.target.value)}
            rows={4}
            placeholder="Tuliskan task untuk workspace orchestrator..."
            className="resize-none rounded-[14px] border border-[rgba(62,54,46,0.14)] bg-white px-4 py-3 text-sm leading-6 text-[#3E362E] outline-none transition placeholder:text-[rgba(62,54,46,0.42)] focus:border-[#A36A58]"
          />
        </label>

        <div className="flex flex-wrap items-center justify-between gap-3">
          <p className="text-xs leading-6 text-[rgba(62,54,46,0.58)]">
            Session aktif tersimpan per user dan terenkripsi di database.
          </p>
          <div className="flex flex-wrap gap-2">
            <button
              type="button"
              onClick={handleClearDraft}
              disabled={isSending && !messages.length}
              className="rounded-full border border-[rgba(62,54,46,0.14)] bg-[#F5F1E6] px-4 py-2.5 text-sm font-medium text-[#3E362E] transition hover:bg-[#efe7d6] disabled:cursor-not-allowed disabled:opacity-70"
            >
              Clear
            </button>
            <button
              type="submit"
              disabled={!canSend}
              className="rounded-full bg-[#A36A58] px-4 py-2.5 text-sm font-medium text-white transition hover:bg-[#94604f] disabled:cursor-not-allowed disabled:opacity-70"
            >
              {isSending ? "Mengirim..." : "Kirim ke Workspace"}
            </button>
          </div>
        </div>
      </form>
    </div>
  );
}
