"use client";

import Sidebar from "./Sidebar";
import Topbar from "./Topbar";

export default function AppShell({
  title,
  description,
  children,
  sidebarActive,
  onSidebarAction,
  panel,
  minimal = false,
  sidebar = null
}) {
  if (minimal) {
    return (
      <div className="min-h-screen w-screen overflow-hidden bg-[#F5F1E6] text-[#3E362E]">
        <div className="flex min-h-screen w-full">
          {sidebar}
          <main className="min-w-0 flex-1">{children}</main>
          {panel}
        </div>
      </div>
    );
  }

  return (
    <div className="app-grid min-h-screen">
      <div className="mx-auto flex min-h-screen w-full max-w-[1680px] flex-col lg:flex-row">
        <Sidebar activeItem={sidebarActive} onAction={onSidebarAction} />
        <div className="relative flex min-h-screen flex-1 flex-col">
          <Topbar />
          <main className="flex-1 px-5 py-6 md:px-8 md:py-8">
            <div className="mx-auto max-w-7xl space-y-6">
              <header className="rounded-[30px] border border-[var(--border)] bg-[color:var(--panel)] px-6 py-6 shadow-panel">
                <p className="text-sm uppercase tracking-[0.2em] text-[color:var(--muted)]">
                  Workspace
                </p>
                <h1 className="mt-3 text-3xl text-ink">{title}</h1>
                <p className="mt-2 max-w-3xl text-sm leading-7 text-[color:var(--muted)]">
                  {description}
                </p>
              </header>
              {children}
            </div>
          </main>
          {panel}
        </div>
      </div>
    </div>
  );
}
