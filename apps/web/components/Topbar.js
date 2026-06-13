"use client";

export default function Topbar() {
  return (
    <header className="border-b border-[var(--border)] bg-[rgba(255,255,255,0.72)] px-5 py-4 backdrop-blur md:px-8">
      <div className="mx-auto flex max-w-7xl items-center justify-between gap-4">
        <div>
          <p className="text-xs uppercase tracking-[0.2em] text-[color:var(--muted)]">
            Personal AI Agent Workspace
          </p>
          <p className="mt-1 text-sm text-ink">Protected command center workspace with read-only safe data boundaries</p>
        </div>
        <div className="rounded-full border border-[var(--border)] bg-white px-4 py-2 text-xs uppercase tracking-[0.18em] text-[color:var(--muted)]">
          Owner mode
        </div>
      </div>
    </header>
  );
}
