"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useSession } from "next-auth/react";
import { useMutation, useQuery } from "@tanstack/react-query";
import { getUserConfig, listNotionDatabases, updateUserConfig, triggerRagSync } from "@/lib/api";
import toast from "react-hot-toast";
import { Card, CardHeader, CardTitle, CardContent, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";

export default function OnboardingPage() {
  const router = useRouter();
  const { status } = useSession();
  const [step, setStep] = useState<number>(1);
  const [tasksDb, setTasksDb] = useState("");
  const [routinesDb, setRoutinesDb] = useState("");

  useEffect(() => {
    if (status === "unauthenticated") router.push("/auth/signin");
  }, [status, router]);

  const { data: config } = useQuery({ queryKey: ["userConfig"], queryFn: getUserConfig, enabled: status === "authenticated" });
  const { data: dbs } = useQuery({ queryKey: ["notionDatabases"], queryFn: () => listNotionDatabases(), enabled: status === "authenticated" });

  useEffect(() => {
    if (config && (config.notion_tasks_db_id && config.notion_routines_db_id)) {
      router.push("/dashboard");
    }
  }, [config, router]);

  const saveMutation = useMutation({
    mutationFn: async (): Promise<unknown> => {
      const res = await updateUserConfig({ notion_tasks_db_id: tasksDb || null, notion_routines_db_id: routinesDb || null });
      try { await triggerRagSync(); } catch {}
      return res;
    },
    onSuccess: () => { toast.success("Setup complete! Sync started"); router.push("/dashboard"); },
    onError: (e: unknown) => {
      const message = e instanceof Error ? e.message : String(e);
      toast.error(`Failed to complete setup: ${message}`);
    },
  });

  const databases = (dbs?.databases || []) as Array<{ id: string; title: string }>;

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <main className="max-w-2xl mx-auto px-4 sm:px-6 lg:px-8">
        <Card>
          <CardHeader>
            <CardTitle>Welcome to Notion Agent</CardTitle>
            <CardDescription>Let’s connect your Notion databases to get started.</CardDescription>
          </CardHeader>
          <CardContent>
            {step === 1 && (
              <div className="space-y-4">
                <div>
                  <div className="text-sm font-medium mb-2">Select your Tasks database</div>
                  <select className="w-full border rounded-md p-2" value={tasksDb} onChange={(e) => setTasksDb(e.target.value)}>
                    <option value="">Select a database...</option>
                    {databases.map((db) => (
                      <option key={db.id} value={db.id}>{db.title}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <div className="text-sm font-medium mb-2">Select your Routines database</div>
                  <select className="w-full border rounded-md p-2" value={routinesDb} onChange={(e) => setRoutinesDb(e.target.value)}>
                    <option value="">Select a database...</option>
                    {databases.map((db) => (
                      <option key={db.id} value={db.id}>{db.title}</option>
                    ))}
                  </select>
                </div>
                <div className="flex gap-3">
                  <Button onClick={() => setStep(2)} disabled={!tasksDb || !routinesDb}>Continue</Button>
                </div>
              </div>
            )}

            {step === 2 && (
              <div className="space-y-4">
                <div className="text-sm text-gray-700">Review your selections and finish setup.</div>
                <ul className="list-disc pl-5 text-sm text-gray-700">
                  <li>Tasks DB: {tasksDb || "Not selected"}</li>
                  <li>Routines DB: {routinesDb || "Not selected"}</li>
                </ul>
                <div className="flex gap-3">
                  <Button variant="outline" onClick={() => setStep(1)}>Back</Button>
                  <Button onClick={() => saveMutation.mutate()} disabled={saveMutation.isPending}>{saveMutation.isPending ? "Saving..." : "Finish"}</Button>
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      </main>
    </div>
  );
}


