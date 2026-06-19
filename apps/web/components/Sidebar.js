"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

import { clearToken } from "../lib/auth";

const NAV_ITEMS = [
  { key: "create", label: "Create Agent", href: "/dashboard" },
  { key: "importSkill", label: "Import Skill", href: "/dashboard" },
  { key: "librarySkill", label: "Library Skill", href: "/dashboard" },
  { key: "libraryWorkflow", label: "Library Workflow", href: "/dashboard" },
  { key: "workflowN8n", label: "Workflow n8n", href: "/dashboard" },
  { key: "activityLog", label: "Activity Log", href: "/dashboard" }
];

function NavBtn({ icon, label, onClick }) {
  const [hovered, setHovered] = useState(false);

  return (
    <button
      type="button"
      onClick={onClick}
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
      className="w-full text-left"
      style={{
        display: "flex",
        alignItems: "center",
        gap: 10,
        padding: "10px 12px",
        borderRadius: 12,
        width: "100%",
        textAlign: "left",
        border: `1px solid ${hovered ? "rgba(90,65,35,0.15)" : "transparent"}`,
        background: hovered ? "#FDFAF5" : "none",
        color: hovered ? "#2C2217" : "#5C4E3E",
        fontSize: 13,
        cursor: "pointer"
      }}
    >
      <span style={{ color: "#8A7A68", display: "flex" }}>{icon}</span>
      {label}
    </button>
  );
}

export default function Sidebar({ activeItem = "overview", onAction, variant = "default" }) {
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
      <aside className="flex w-full shrink-0 flex-col border-b border-[rgba(62,54,46,0.12)] bg-[#EDE6D8] px-4 py-4 lg:sticky lg:top-0 lg:h-[100dvh] lg:w-[196px] lg:border-b-0 lg:border-r xl:w-[196px]">
        <div className="flex items-center gap-3 px-1 pb-5 pt-1">
          <div className="font-serif text-[22px] italic tracking-[-0.05em] text-[#3E362E]">
            workspace
          </div>
          <div className="flex h-7 w-7 items-center justify-center rounded-full border border-[rgba(163,106,88,0.24)] bg-[#f5e8de] text-[11px] font-semibold text-[#a36a58]">
            U
          </div>
          <div className="min-w-0">
            <p className="truncate text-[13px] font-medium text-[#3E362E]">nama user</p>
            <p className="mt-1 inline-flex rounded-full border border-[rgba(163,106,88,0.18)] bg-[#f7eee4] px-2 py-0.5 text-[10px] font-medium uppercase tracking-[0.16em] text-[#c28b6c]">
              free
            </p>
          </div>
        </div>

        <nav className="space-y-1.5">
          {NAV_ITEMS.map((item) => (
            <NavBtn
              key={item.key}
              icon={<span className="text-[16px] leading-none">+</span>}
              label={item.label}
              onClick={() => handleItemClick(item)}
            />
          ))}
        </nav>

        <div className="mt-auto pt-4">
          <NavBtn
            icon={<span className="text-[16px] leading-none">{'\u2699'}</span>}
            label="Settings"
            onClick={() => handleItemClick({ key: "settings", href: "/dashboard" })}
          />
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
                active ? "bg-[color:var(--accent)] text-white shadow-panel" : "text-ink hover:bg-white"
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
