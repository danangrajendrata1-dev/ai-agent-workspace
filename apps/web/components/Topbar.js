"use client";

import StatusBadge from "./StatusBadge";

export default function Topbar({ currentUser = null, onLogout = null }) {
  return (
    <header className="flex items-center justify-between gap-4 border-b border-[rgba(62,54,46,0.12)] bg-[#eee6d6]/95 px-4 py-3 backdrop-blur">
      <div className="flex min-w-0 items-center gap-3">
        <div className="font-serif text-[22px] italic tracking-[-0.05em] text-[#3E362E]">
          workspace
        </div>
        <div className="flex h-7 w-7 items-center justify-center rounded-full border border-[rgba(163,106,88,0.24)] bg-[#f5e8de] text-[11px] font-semibold text-[#a36a58]">
          {String(currentUser?.display_name || currentUser?.username || "u").slice(0, 1).toUpperCase()}
        </div>
        <div className="min-w-0">
          <p className="truncate text-[13px] font-medium text-[#3E362E]">
            {currentUser?.display_name || currentUser?.username || "nama user"}
          </p>
        </div>
        <span className="inline-flex rounded-full border border-[rgba(163,106,88,0.18)] bg-[#f7eee4] px-2 py-0.5 text-[10px] font-medium uppercase tracking-[0.16em] text-[#c28b6c]">
          {(currentUser?.subscription_plan || "free").toUpperCase()}
        </span>
      </div>

      <div className="flex items-center gap-2">
        {typeof onLogout === "function" ? (
          <button
            type="button"
            onClick={onLogout}
            className="rounded-[12px] border border-[rgba(62,54,46,0.12)] bg-[#f5efe2] px-4 py-2 text-[13px] font-medium text-[#3E362E] transition hover:bg-[#efe2cf]"
          >
            Logout
          </button>
        ) : null}
      </div>
    </header>
  );
}
