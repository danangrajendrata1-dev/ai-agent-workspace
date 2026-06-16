"use client";

import { useEffect, useRef, useState } from "react";

import { orchestratorChat } from "../lib/apiClient";


function getFriendlyWorkspaceChatErrorMessage(error) {
  const message = error instanceof Error ? error.message.trim() : "";

  if (message === "Terlalu banyak pesan, tunggu sebentar") {
    return message;
  }

  return message || "Failed to send workspace message.";
}


function buildMessageId(role, index) {
  return `${role}-${index + 1}`;
}


export default function WorkspaceChatPanel() {
  const [messages, setMessages] = useState([]);
  const [draft, setDraft] = useState("");
  const [isSending, setIsSending] = useState(false);
  const [error, setError] = useState("");
  const [warning, setWarning] = useState("");
  const [responseMeta, setResponseMeta] = useState(null);
  const scrollAnchorRef = useRef(null);

  useEffect(() => {
    if (!scrollAnchorRef.current) {
      return;
    }

    scrollAnchorRef.current.scrollIntoView({ block: "end", behavior: "smooth" });
  }, [messages, isSending]);

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
      const response = await orchestratorChat(trimmedDraft, nextMessages);
      setMessages((currentMessages) => [
        ...currentMessages,
        { role: "assistant", content: response.reply }
      ]);
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
        knowledgeTruncated: Boolean(response.knowledge_truncated)
      });
      setWarning(response.warning || "");
    } catch (workspaceError) {
      setError(getFriendlyWorkspaceChatErrorMessage(workspaceError));
    } finally {
      setIsSending(false);
    }
  }

  function handleClearChat() {
    setMessages([]);
    setDraft("");
    setError("");
    setWarning("");
    setResponseMeta(null);
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
            Chat history stays in React state for this session.
          </p>
        </div>
        <span className="rounded-full border border-[rgba(163,106,88,0.2)] bg-[rgba(163,106,88,0.1)] px-3 py-1 text-[11px] uppercase tracking-[0.14em] text-[#A36A58]">
          Orchestrator
        </span>
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
            History workspace hanya ada di state React dan hilang saat refresh.
          </p>
          <div className="flex flex-wrap gap-2">
            <button
              type="button"
              onClick={handleClearChat}
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
