import Link from "next/link";


export default function HomePage() {
  return (
    <main className="app-grid min-h-screen px-6 py-10">
      <div className="mx-auto flex min-h-screen w-full max-w-5xl items-center justify-center">
        <section className="relative w-full overflow-hidden rounded-[36px] border border-[var(--border)] bg-[#e5e0d3] px-8 py-12 shadow-panel md:px-12 md:py-16">
          <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_top,rgba(255,255,255,0.38),transparent_32%),radial-gradient(circle_at_bottom_left,rgba(163,106,88,0.12),transparent_28%)]" />
          <div className="relative mx-auto max-w-2xl text-center">
            <div className="inline-flex rounded-full border border-[rgba(62,54,46,0.12)] bg-[#f5f1e6] px-4 py-2 text-[11px] uppercase tracking-[0.28em] text-[rgba(62,54,46,0.64)]">
              Private workspace
            </div>
            <h1 className="mt-6 text-4xl font-medium leading-tight text-[#3e362e] md:text-6xl">
              Personal AI Agent Workspace
            </h1>
            <p className="mx-auto mt-5 max-w-xl text-base leading-8 text-[rgba(62,54,46,0.72)] md:text-lg">
              Private command center for creating and managing your own AI agents.
            </p>
            <p className="mt-4 text-sm text-[rgba(62,54,46,0.62)]">
              Safe MVP mode. Runtime execution is disabled.
            </p>
            <div className="mt-8 flex flex-col items-center justify-center gap-3 sm:flex-row">
              <Link
                href="/dashboard"
                className="inline-flex min-w-[210px] items-center justify-center rounded-full bg-[#a36a58] px-6 py-3 text-sm font-semibold text-white transition hover:bg-[#8f5d4d]"
              >
                Enter Workspace
              </Link>
              <Link
                href="/login"
                className="inline-flex min-w-[210px] items-center justify-center rounded-full border border-[rgba(62,54,46,0.14)] bg-[#f5f1e6] px-6 py-3 text-sm font-semibold text-[#3e362e] transition hover:bg-[#d5cfbf]"
              >
                Open Login
              </Link>
            </div>
          </div>
        </section>
      </div>
    </main>
  );
}
