"use client";

import { useEffect, useRef, useState } from "react";

import { chatWithAgent } from "../lib/apiClient";


function getFriendlyChatErrorMessage(error) {
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

  if (message === "Provider not supported") {
    return "Provider not supported";
  }

  if (message === "Invalid API key or unauthorized") {
    return message;
  }

  return message || "Failed to send message.";
}


function buildMessageId(role, index) {
  return `${role}-${index + 1}`;
}


export default function AgentChatPanel({ agent, providerLabel }) {
  const [messages, setMessages] = useState([]);
  const [draft, setDraft] = useState("");
  const [isSending, setIsSending] = useState(false);
  const [error, setError] = useState("");
  const [warning, setWarning] = useState("");
  const [responseMeta, setResponseMeta] = useState(null);
  const scrollAnchorRef = useRef(null);

  useEffect(() => {
    setMessages([]);
    setDraft("");
    setIsSending(false);
    setError("");
    setWarning("");
    setResponseMeta(null);
  }, [agent?.id]);

  useEffect(() => {
    if (!scrollAnchorRef.current) {
      return;
    }

    scrollAnchorRef.current.scrollIntoView({ block: "end", behavior: "smooth" });
  }, [messages, isSending]);

  async function handleSubmit(event) {
    event.preventDefault();

    if (!agent?.id || isSending) {
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
      const response = await chatWithAgent(agent.id, nextMessages);
      setMessages((currentMessages) => [
        ...currentMessages,
        { role: "assistant", content: response.reply }
      ]);
      setResponseMeta({
        provider: response.provider,
        model: response.model,
        promptSkillsUsed: Array.isArray(response.prompt_skills_used)
          ? response.prompt_skills_used
          : []
      });
      setWarning(response.warning || "");
    } catch (chatError) {
      setError(getFriendlyChatErrorMessage(chatError));
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

  const canSend = Boolean(agent?.id) && Boolean(draft.trim()) && !isSending;

  return (
    <div className="rounded-[18px] border border-[rgba(62,54,46,0.14)] bg-[#F5F1E6] p-4">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="min-w-0">
          <p className="text-[11px] uppercase tracking-[0.18em] text-[rgba(62,54,46,0.56)]">
            Agent Chat
          </p>
          <p className="mt-1 text-sm font-semibold text-[#3E362E]">
            {agent?.name || "Select an active agent"}
          </p>
          <p className="mt-1 text-sm leading-6 text-[rgba(62,54,46,0.64)]">
            Prompt skill only. Chat history stays in React state for this session.
          </p>
        </div>
        <span className="rounded-full border border-[rgba(163,106,88,0.2)] bg-[rgba(163,106,88,0.1)] px-3 py-1 text-[11px] uppercase tracking-[0.14em] text-[#A36A58]">
          Prompt skill only
        </span>
      </div>

      <div className="mt-3 flex flex-wrap gap-2">
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
        {providerLabel ? (
          <span className="rounded-full border border-[rgba(62,54,46,0.12)] bg-white px-3 py-1 text-[11px] text-[rgba(62,54,46,0.72)]">
            Config: {providerLabel}
          </span>
        ) : null}
      </div>

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
            Mulai percakapan setelah memilih agent aktif dari sidebar.
          </div>
        )}
        <div ref={scrollAnchorRef} />
      </div>

      <form onSubmit={handleSubmit} className="mt-4 space-y-3">
        <label className="grid gap-2">
          <span className="text-xs uppercase tracking-[0.14em] text-[rgba(62,54,46,0.52)]">
            Pesan
          </span>
          <textarea
            value={draft}
            onChange={(event) => setDraft(event.target.value)}
            rows={4}
            placeholder="Tulis pesan ke agent..."
            className="resize-none rounded-[14px] border border-[rgba(62,54,46,0.14)] bg-white px-4 py-3 text-sm leading-6 text-[#3E362E] outline-none transition placeholder:text-[rgba(62,54,46,0.42)] focus:border-[#A36A58]"
          />
        </label>

        <div className="flex flex-wrap items-center justify-between gap-3">
          <p className="text-xs leading-6 text-[rgba(62,54,46,0.58)]">
            History chat hanya ada di state React dan hilang saat refresh.
          </p>
          <div className="flex flex-wrap gap-2">
            <button
              type="button"
              onClick={handleClearChat}
              disabled={isSending && !messages.length}
              className="rounded-full border border-[rgba(62,54,46,0.14)] bg-[#F5F1E6] px-4 py-2.5 text-sm font-medium text-[#3E362E] transition hover:bg-[#efe7d6] disabled:cursor-not-allowed disabled:opacity-70"
            >
              Clear Chat
            </button>
            <button
              type="submit"
              disabled={!canSend}
              className="rounded-full bg-[#A36A58] px-4 py-2.5 text-sm font-medium text-white transition hover:bg-[#94604f] disabled:cursor-not-allowed disabled:opacity-70"
            >
              {isSending ? "Mengirim..." : "Kirim"}
            </button>
          </div>
        </div>
      </form>
    </div>
  );
}
