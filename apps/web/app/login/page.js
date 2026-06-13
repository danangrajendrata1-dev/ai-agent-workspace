"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";

import { post } from "../../lib/apiClient";
import { setToken } from "../../lib/auth";

function getSafeNextTarget(value) {
  if (!value || typeof value !== "string") {
    return "/dashboard";
  }

  if (!value.startsWith("/") || value.startsWith("//")) {
    return "/dashboard";
  }

  return value;
}


export default function LoginPage() {
  const router = useRouter();
  const [form, setForm] = useState({ email: "", password: "" });
  const [error, setError] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleSubmit(event) {
    event.preventDefault();
    setError("");
    setIsSubmitting(true);

    try {
      const response = await post("/auth/login", form, { includeAuth: false });
      if (!response?.access_token) {
        throw new Error("Login response did not include an access token.");
      }

      setToken(response.access_token);
      const nextTarget =
        typeof window === "undefined"
          ? "/dashboard"
          : getSafeNextTarget(new URLSearchParams(window.location.search).get("next"));
      router.replace(nextTarget);
    } catch (submitError) {
      setError(submitError.message || "Login failed. Please check your credentials.");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <main className="app-grid min-h-screen px-6 py-10">
      <div className="mx-auto flex min-h-screen w-full max-w-5xl items-center justify-center">
        <section className="relative w-full max-w-md overflow-hidden rounded-[32px] border border-[var(--border)] bg-[#e5e0d3] p-8 shadow-panel md:p-10">
          <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_top,rgba(255,255,255,0.4),transparent_34%),radial-gradient(circle_at_bottom,rgba(163,106,88,0.12),transparent_26%)]" />
          <div className="relative space-y-8">
            <div className="space-y-4">
              <Link
                href="/"
                className="inline-flex rounded-full border border-[rgba(62,54,46,0.12)] bg-[#f5f1e6] px-3 py-1.5 text-[11px] uppercase tracking-[0.24em] text-[rgba(62,54,46,0.66)] transition hover:bg-[#d5cfbf] hover:text-[#3e362e]"
              >
                Workspace
              </Link>
              <div className="space-y-3">
                <h1 className="text-3xl font-medium text-[#3e362e] md:text-4xl">Welcome back</h1>
                <p className="text-sm leading-7 text-[rgba(62,54,46,0.7)]">
                  Sign in to your private workspace.
                </p>
              </div>
            </div>

            <form className="space-y-5" onSubmit={handleSubmit}>
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
                  placeholder="Enter your password"
                  autoComplete="current-password"
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
                disabled={isSubmitting}
                className="w-full rounded-full bg-[#a36a58] px-5 py-3 text-sm font-semibold text-white transition hover:bg-[#8f5d4d] disabled:cursor-not-allowed disabled:opacity-60"
              >
                {isSubmitting ? "Signing in..." : "Sign in"}
              </button>
            </form>

            <p className="text-center text-xs uppercase tracking-[0.2em] text-[rgba(62,54,46,0.5)]">
              Personal AI Agent Workspace v2.1
            </p>
          </div>
        </section>
      </div>
    </main>
  );
}
