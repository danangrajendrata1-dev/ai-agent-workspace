"use client";

export default function WorkspacePanel({ open, title, description, children, onClose }) {
  return (
    <div
      className={`pointer-events-none fixed inset-0 z-40 transition ${open ? "opacity-100" : "opacity-0"}`}
      aria-hidden={!open}
    >
      <div
        className={`absolute inset-0 bg-[#10243b]/28 backdrop-blur-sm transition ${open ? "opacity-100" : "opacity-0"}`}
        onClick={onClose}
      />
      <aside
        className={`pointer-events-auto absolute right-0 top-0 h-full w-full max-w-[560px] border-l border-[var(--border)] bg-[rgba(248,251,253,0.97)] shadow-2xl transition duration-300 ${open ? "translate-x-0" : "translate-x-full"}`}
      >
        <div className="flex h-full flex-col">
          <div className="flex items-start justify-between gap-4 border-b border-[var(--border)] px-5 py-5 md:px-6">
            <div>
              <p className="text-xs uppercase tracking-[0.18em] text-[color:var(--muted)]">Workspace panel</p>
              <h2 className="mt-2 text-2xl text-ink">{title}</h2>
              <p className="mt-2 text-sm leading-7 text-[color:var(--muted)]">{description}</p>
            </div>
            <button
              type="button"
              onClick={onClose}
              className="rounded-full border border-[var(--border)] bg-white px-4 py-2 text-sm font-medium text-ink transition hover:border-[color:var(--accent)]"
            >
              Close
            </button>
          </div>
          <div className="flex-1 overflow-y-auto px-5 py-5 md:px-6">
            {children}
          </div>
        </div>
      </aside>
    </div>
  );
}
