"use client";

import { useState } from "react";
import Link from "next/link";

import { post } from "../../lib/apiClient";

const INITIAL_FORM = {
  email: "",
  display_name: "",
  password: "",
};


export default function RegisterPage() {
  const [form, setForm] = useState(INITIAL_FORM);
  const [error, setError] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [successMessage, setSuccessMessage] = useState("");

  async function handleSubmit(event) {
    event.preventDefault();
    setError("");
    setSuccessMessage("");
    setIsSubmitting(true);

    try {
      const payload = {
        email: form.email.trim(),
        password: form.password,
        display_name: form.display_name.trim()
      };

      await post("/auth/register", payload, { includeAuth: false });
      setForm(INITIAL_FORM);
      setSuccessMessage(
        "Account created. New accounts start on the Free plan with up to 5 agents and no n8n access yet."
      );
    } catch (submitError) {
      setError(submitError.message || "Registration failed. Please review the form and try again.");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <main className="app-grid min-h-screen px-6 py-10">
      <div className="mx-auto flex min-h-screen w-full max-w-6xl items-center justify-center">
        <section className="relative w-full overflow-hidden rounded-[36px] border border-[var(--border)] bg-[#e5e0d3] shadow-panel">
          <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_top,rgba(255,255,255,0.42),transparent_34%),radial-gradient(circle_at_bottom_right,rgba(163,106,88,0.14),transparent_26%)]" />
          <div className="relative grid gap-0 md:grid-cols-[1.15fr_0.85fr]">
            <div className="space-y-8 px-8 py-10 md:px-12 md:py-14">
              <div className="space-y-4">
                <Link
                  href="/"
                  className="inline-flex rounded-full border border-[rgba(62,54,46,0.12)] bg-[#f5f1e6] px-3 py-1.5 text-[11px] uppercase tracking-[0.24em] text-[rgba(62,54,46,0.66)] transition hover:bg-[#d5cfbf] hover:text-[#3e362e]"
                >
                  Workspace
                </Link>
                <div className="space-y-3">
                  <h1 className="text-3xl font-medium text-[#3e362e] md:text-4xl">Create your account</h1>
                  <p className="max-w-xl text-sm leading-7 text-[rgba(62,54,46,0.7)]">
                    New accounts start on the Free plan. The Free plan allows up to 5 agents and does not
                    include n8n access yet.
                  </p>
                </div>
              </div>

              {successMessage ? (
                <div className="rounded-[22px] border border-[rgba(93,130,85,0.22)] bg-[rgba(93,130,85,0.08)] px-4 py-3 text-sm leading-7 text-[#3c5e36]">
                  {successMessage}
                </div>
              ) : null}

              <form className="space-y-5" onSubmit={handleSubmit}>
                <label className="block space-y-2">
                  <span className="text-sm font-medium text-[#3e362e]">Display name</span>
                  <input
                    type="text"
                    value={form.display_name}
                    onChange={(event) => setForm({ ...form, display_name: event.target.value })}
                    className="w-full rounded-[18px] border border-[rgba(62,54,46,0.12)] bg-[#f5f1e6] px-4 py-3 text-[#3e362e] outline-none transition placeholder:text-[rgba(62,54,46,0.42)] focus:border-[#a36a58] focus:bg-white"
                    placeholder="Your name"
                    autoComplete="name"
                    required
                  />
                </label>

                <label className="block space-y-2">
                  <span className="text-sm font-medium text-[#3e362e]">Email</span>
                  <input
                    type="email"
                    value={form.email}
                    onChange={(event) => setForm({ ...form, email: event.target.value })}
                    className="w-full rounded-[18px] border border-[rgba(62,54,46,0.12)] bg-[#f5f1e6] px-4 py-3 text-[#3e362e] outline-none transition placeholder:text-[rgba(62,54,46,0.42)] focus:border-[#a36a58] focus:bg-white"
                    placeholder="you@example.com"
                    autoComplete="email"
                    required
                  />
                </label>

                <label className="block space-y-2">
                  <span className="text-sm font-medium text-[#3e362e]">Password</span>
                  <input
                    type="password"
                    value={form.password}
                    onChange={(event) => setForm({ ...form, password: event.target.value })}
                    className="w-full rounded-[18px] border border-[rgba(62,54,46,0.12)] bg-[#f5f1e6] px-4 py-3 text-[#3e362e] outline-none transition placeholder:text-[rgba(62,54,46,0.42)] focus:border-[#a36a58] focus:bg-white"
                    placeholder="Create a password"
                    autoComplete="new-password"
                    required
                  />
                </label>

                {error ? (
                  <div className="rounded-[18px] border border-[rgba(255,140,140,0.22)] bg-[rgba(255,140,140,0.08)] px-4 py-3 text-sm text-[color:var(--danger)]">
                    {error}
                  </div>
                ) : null}

                <button
                  type="submit"
                  disabled={isSubmitting || Boolean(successMessage)}
                  className="w-full rounded-full bg-[#a36a58] px-5 py-3 text-sm font-semibold text-white transition hover:bg-[#8f5d4d] disabled:cursor-not-allowed disabled:opacity-60"
                >
                  {isSubmitting ? "Creating account..." : "Create account"}
                </button>
              </form>

              <div className="flex items-center justify-between gap-4 text-sm text-[rgba(62,54,46,0.68)]">
                <span>Already have an account?</span>
                <Link href="/login" className="font-semibold text-[#3e362e] underline decoration-[rgba(62,54,46,0.22)] underline-offset-4">
                  Sign in
                </Link>
              </div>
            </div>

            <aside className="border-t border-[rgba(62,54,46,0.08)] bg-[rgba(245,241,230,0.72)] px-8 py-10 md:border-l md:border-t-0 md:px-10 md:py-14">
              <div className="space-y-6">
                <div className="space-y-3">
                  <p className="text-[11px] uppercase tracking-[0.24em] text-[rgba(62,54,46,0.56)]">Plan start</p>
                  <h2 className="text-2xl font-medium text-[#3e362e]">Free plan by default</h2>
                  <p className="text-sm leading-7 text-[rgba(62,54,46,0.68)]">
                    Role and subscription are separate. Registration keeps accounts in user role with the Free
                    subscription plan until an upgrade flow is added later.
                  </p>
                </div>

                <div className="space-y-3 rounded-[24px] border border-[rgba(62,54,46,0.12)] bg-[#f5f1e6] p-5">
                  <div className="flex items-center justify-between gap-4">
                    <span className="text-sm font-medium text-[#3e362e]">Free plan</span>
                    <span className="rounded-full bg-[rgba(163,106,88,0.12)] px-3 py-1 text-[11px] uppercase tracking-[0.2em] text-[#8f5d4d]">
                      Active default
                    </span>
                  </div>
                  <ul className="space-y-2 text-sm leading-6 text-[rgba(62,54,46,0.72)]">
                    <li>Up to 5 agents</li>
                    <li>No n8n access</li>
                    <li>0 saved workflows</li>
                  </ul>
                </div>

                <div className="rounded-[24px] border border-[rgba(62,54,46,0.12)] bg-[#f5f1e6] p-5 text-sm leading-7 text-[rgba(62,54,46,0.72)]">
                  Imported skills and privileged actions stay inactive until reviewed elsewhere in the workspace.
                </div>
              </div>
            </aside>
          </div>
        </section>
      </div>
    </main>
  );
}
