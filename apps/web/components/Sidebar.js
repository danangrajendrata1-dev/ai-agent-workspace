"use client";

import { useRouter } from "next/navigation";

import AgentCard from "./AgentCard";
import { clearToken } from "../lib/auth";

const NAV_ITEMS = [
  { key: "overview", label: "Command Center / Profile", href: "/dashboard" },
  { key: "agents", label: "Agents +", href: "/agents" },
  { key: "skills", label: "Import Skills", href: "/settings" },
  { key: "settings", label: "Settings", href: "/settings" }
];

export default function Sidebar({
  activeItem = "overview",
  onAction,
  variant = "default",
  pinnedAgents = [],
  activeAgentId = null,
  onPinnedAgentSelect,
  onPinnedAgentUnpin
}) {
  const router = useRouter();

  function handleLogout() {
    clearToken();
    router.replace("/login");
  }

  function handleItemClick(item) {
    if (typeof onAction === "function") {
      onAction(item.key);
      return;
    }

    router.push(item.href);
  }

  if (variant === "workspace") {
    return (
      <aside className="w-full shrink-0 border-b border-[rgba(62,54,46,0.14)] bg-[#E5E0D3] lg:h-screen lg:w-72 lg:border-b-0 lg:border-r xl:w-80">
        <div className="flex h-full min-h-0 flex-col overflow-hidden p-4">
          <div className="pb-4">
            <p className="text-[28px] font-semibold tracking-[-0.03em] text-[#3E362E]">Workspace</p>
            <p className="mt-1 text-sm text-[rgba(62,54,46,0.68)]">Private workspace</p>
          </div>

          <div className="space-y-3">
            <button
              type="button"
              onClick={() => onAction?.("create")}
              className="w-full rounded-lg bg-[#A36A58] px-4 py-3 text-left text-sm font-semibold text-white transition hover:bg-[#94604f]"
            >
              + Create Agent
            </button>

            <button
              type="button"
              onClick={() => onAction?.("skills")}
              className="w-full rounded-lg border border-[rgba(62,54,46,0.14)] bg-[#F5F1E6] px-4 py-3 text-left text-sm font-medium text-[#3E362E] transition hover:bg-[#D5CFBF]"
            >
              Import Skill
            </button>

            <button
              type="button"
              onClick={() => onAction?.("workflow")}
              className="w-full rounded-lg border border-[rgba(62,54,46,0.14)] bg-[#F5F1E6] px-4 py-3 text-left text-sm font-medium text-[#3E362E] transition hover:bg-[#D5CFBF]"
            >
              Workflow n8n
            </button>
          </div>

          <div className="mt-6">
            <p className="text-xs uppercase tracking-[0.18em] text-[rgba(62,54,46,0.64)]">
              Active Associates
            </p>
          </div>

          <div className="scrollbar-thin mt-3 min-h-0 flex-1 overflow-y-auto pr-1">
            <div className="space-y-3">
              {pinnedAgents.map((agent) => (
                <div
                  key={agent.id}
                  className={`relative rounded-[18px] transition ${
                    activeAgentId === agent.id
                      ? "ring-2 ring-[#A36A58] ring-offset-2 ring-offset-[#E5E0D3]"
                      : ""
                  }`}
                >
                  <button
                    type="button"
                    onClick={(event) => {
                      event.stopPropagation();
                      onPinnedAgentUnpin?.(agent.id);
                    }}
                    className="absolute right-3 top-3 z-10 flex h-7 w-7 shrink-0 items-center justify-center rounded-full border border-[rgba(62,54,46,0.14)] bg-[#E5E0D3] text-[18px] leading-none text-[rgba(62,54,46,0.72)] transition hover:bg-[#D5CFBF] hover:text-[#3E362E]"
                    aria-label="Unpin agent"
                    title="Unpin agent"
                  >
                    ×
                  </button>
                  <AgentCard
                    agent={agent}
                    onSelect={() => onPinnedAgentSelect?.(agent.id)}
                    onUnpin={() => onPinnedAgentUnpin?.(agent.id)}
                  />
                </div>
              ))}
              {!pinnedAgents.length ? (
                <div className="rounded-2xl border border-dashed border-[rgba(62,54,46,0.18)] bg-[#F5F1E6] px-4 py-5 text-sm text-[rgba(62,54,46,0.62)]">
                  Pin agent dari workspace untuk tampil di sini.
                </div>
              ) : null}
            </div>
          </div>

          <div className="mt-auto space-y-3 pt-5">
            <button
              type="button"
              onClick={() => onAction?.("settings")}
              className="w-full rounded-lg border border-[rgba(62,54,46,0.14)] bg-[#F5F1E6] px-4 py-3 text-left text-sm font-medium text-[#3E362E] transition hover:bg-[#D5CFBF]"
            >
              Settings
            </button>

            <button
              type="button"
              onClick={handleLogout}
              className="w-full rounded-lg border border-[rgba(62,54,46,0.14)] bg-transparent px-4 py-3 text-left text-sm font-medium text-[rgba(62,54,46,0.72)] transition hover:bg-[#D5CFBF] hover:text-[#3E362E]"
            >
              Logout
            </button>
          </div>
        </div>
      </aside>
    );
  }

  return (
    <aside className="border-b border-[var(--border)] bg-[rgba(255,255,255,0.78)] px-5 py-5 backdrop-blur lg:sticky lg:top-0 lg:flex lg:min-h-screen lg:w-[290px] lg:flex-col lg:border-b-0 lg:border-r lg:py-6">
      <div className="rounded-[30px] border border-[var(--border)] bg-[linear-gradient(180deg,#10243b,#17365b)] p-5 text-white shadow-panel">
        <p className="text-xs uppercase tracking-[0.22em] text-white/65">Private MVP</p>
        <h2 className="mt-3 text-2xl leading-tight">Agent Workspace</h2>
        <p className="mt-3 text-sm leading-7 text-white/75">
          Single-screen command center untuk owner dengan panel aman dan read-only data fetch.
        </p>
      </div>

      <nav className="mt-6 flex flex-wrap gap-2 lg:flex-1 lg:flex-col">
        {NAV_ITEMS.map((item) => {
          const active = activeItem === item.key;
          return (
            <button
              key={item.key}
              type="button"
              onClick={() => handleItemClick(item)}
              className={`rounded-2xl px-4 py-3 text-sm transition lg:w-full ${
                active
                  ? "bg-[color:var(--accent)] text-white shadow-panel"
                  : "text-ink hover:bg-white"
              }`}
            >
              {item.label}
            </button>
          );
        })}
      </nav>

      <button
        type="button"
        onClick={handleLogout}
        className="mt-4 rounded-2xl border border-[var(--border)] bg-white px-4 py-3 text-left text-sm font-medium text-ink transition hover:border-[color:var(--accent)]"
      >
        Logout
      </button>
    </aside>
  );
}
