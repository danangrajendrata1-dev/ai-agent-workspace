"use client";

import { useEffect, useState } from "react";
import { usePathname, useRouter } from "next/navigation";

import { getToken } from "../lib/auth";
import { getCurrentUser } from "../lib/apiClient";

function buildLoginTarget(pathname) {
  return `/login?next=${encodeURIComponent(pathname || "/dashboard")}`;
}


export default function ProtectedRoute({ children }) {
  const router = useRouter();
  const pathname = usePathname();
  const [isChecking, setIsChecking] = useState(true);
  const [isAllowed, setIsAllowed] = useState(false);

  useEffect(() => {
    let isMounted = true;

    async function validateSession() {
      const token = getToken();

      if (!token) {
        setIsAllowed(false);
        setIsChecking(false);
        router.replace(buildLoginTarget(pathname));
        return;
      }

      try {
        await getCurrentUser();

        if (!isMounted) {
          return;
        }

        setIsAllowed(true);
      } catch {
        if (!isMounted) {
          return;
        }

        setIsAllowed(false);
        router.replace(buildLoginTarget(pathname));
      } finally {
        if (isMounted) {
          setIsChecking(false);
        }
      }
    }

    setIsChecking(true);
    validateSession();

    return () => {
      isMounted = false;
    };
  }, [pathname, router]);

  if (isChecking) {
    return (
      <main className="app-grid flex min-h-screen items-center justify-center px-6">
        <div className="rounded-3xl border border-[var(--border)] bg-white px-6 py-5 text-sm text-[color:var(--muted)] shadow-panel">
          Validating secure workspace session...
        </div>
      </main>
    );
  }

  if (!isAllowed) {
    return null;
  }

  return children;
}
