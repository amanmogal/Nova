"use client";

import { useSession } from "next-auth/react";
import { useRouter } from "next/navigation";
import { useEffect } from "react";
import { getUserConfig } from "@/lib/api";

export default function HomePage() {
  const { data: session, status } = useSession();
  const router = useRouter();

  useEffect(() => {
    if (status === "loading") return;
    (async () => {
      if (!session) {
        router.push("/auth/signin");
        return;
      }
      try {
        const cfg = await getUserConfig();
        if (!cfg?.notion_tasks_db_id || !cfg?.notion_routines_db_id) {
          router.push("/onboarding");
        } else {
          router.push("/dashboard");
        }
      } catch {
        router.push("/dashboard");
      }
    })();
  }, [session, status, router]);

  return (
    <div className="min-h-screen flex items-center justify-center">
      <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-600"></div>
    </div>
  );
}
