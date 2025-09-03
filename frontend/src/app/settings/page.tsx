"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useSession } from "next-auth/react";
import { useMutation, useQuery } from "@tanstack/react-query";
import { listNotionDatabases, getUserConfig, updateUserConfig, triggerRagSync } from "@/lib/api";
import toast from "react-hot-toast";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";

export default function SettingsPage() {
  const router = useRouter();
  const { status } = useSession();
  const [selectedTasksDb, setSelectedTasksDb] = useState<string>("");
  const [selectedRoutinesDb, setSelectedRoutinesDb] = useState<string>("");
  const [dailyPlanningTime, setDailyPlanningTime] = useState<string>("08:00");
  const [enableCostOptimization, setEnableCostOptimization] = useState<boolean>(true);
  const [enablePerformanceMonitoring, setEnablePerformanceMonitoring] = useState<boolean>(true);
  const [ragSyncInterval, setRagSyncInterval] = useState<number>(60);

  useEffect(() => {
    if (status === "unauthenticated") {
      router.push("/auth/signin");
    }
  }, [status, router]);

  const { data: config, isLoading: configLoading } = useQuery({
    queryKey: ["userConfig"],
    queryFn: getUserConfig,
    enabled: status === "authenticated",
  });

  useEffect(() => {
    if (config) {
      setSelectedTasksDb(config.notion_tasks_db_id || "");
      setSelectedRoutinesDb(config.notion_routines_db_id || "");
      setDailyPlanningTime(config.daily_planning_time || "08:00");
      setEnableCostOptimization(Boolean(config.enable_cost_optimization));
      setEnablePerformanceMonitoring(Boolean(config.enable_performance_monitoring));
      setRagSyncInterval(Number(config.rag_sync_interval_min ?? 60));
    }
  }, [config]);

  const { data: dbs, isLoading: dbLoading, refetch } = useQuery({
    queryKey: ["notionDatabases"],
    queryFn: () => listNotionDatabases(),
    enabled: status === "authenticated",
  });

  const saveMutation = useMutation({
    mutationFn: async (payload: Record<string, unknown>) => {
      const res = await updateUserConfig(payload);
      try { await triggerRagSync(); } catch {}
      return res;
    },
    onSuccess: () => {
      toast.success("Settings saved and sync started");
      router.push("/dashboard");
    },
    onError: (e: unknown) => {
      const message = e instanceof Error ? e.message : String(e);
      toast.error(`Failed to save settings: ${message}`);
    },
  });

  if (configLoading || dbLoading || status === "loading") {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-600" />
      </div>
    );
  }

  const databases = (dbs?.databases || []) as Array<{ id: string; title: string; url: string }>;

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <main className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8">
        <Card>
          <CardHeader>
            <CardTitle>Workspace Configuration</CardTitle>
            <CardDescription>Select your Notion databases for tasks and routines</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-6">
              <div>
                <label className="block text-sm font-medium mb-2">Tasks Database</label>
                <select
                  className="w-full border rounded-md p-2"
                  value={selectedTasksDb}
                  onChange={(e) => setSelectedTasksDb(e.target.value)}
                >
                  <option value="">Select a database...</option>
                  {databases.map((db) => (
                    <option key={db.id} value={db.id}>
                      {db.title}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium mb-2">Routines Database</label>
                <select
                  className="w-full border rounded-md p-2"
                  value={selectedRoutinesDb}
                  onChange={(e) => setSelectedRoutinesDb(e.target.value)}
                >
                  <option value="">Select a database...</option>
                  {databases.map((db) => (
                    <option key={db.id} value={db.id}>
                      {db.title}
                    </option>
                  ))}
                </select>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium mb-2">Daily Planning Time</label>
                  <input
                    type="time"
                    className="w-full border rounded-md p-2"
                    value={dailyPlanningTime}
                    onChange={(e) => setDailyPlanningTime(e.target.value)}
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-2">RAG Sync Interval (minutes)</label>
                  <input
                    type="number"
                    min={5}
                    step={5}
                    className="w-full border rounded-md p-2"
                    value={ragSyncInterval}
                    onChange={(e) => setRagSyncInterval(Number(e.target.value))}
                  />
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <label className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={enableCostOptimization}
                    onChange={(e) => setEnableCostOptimization(e.target.checked)}
                  />
                  <span className="text-sm">Enable Cost Optimization</span>
                </label>
                <label className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={enablePerformanceMonitoring}
                    onChange={(e) => setEnablePerformanceMonitoring(e.target.checked)}
                  />
                  <span className="text-sm">Enable Performance Monitoring</span>
                </label>
              </div>

              <div className="flex gap-3">
                <Button
                  onClick={() =>
                    saveMutation.mutate({
                      notion_tasks_db_id: selectedTasksDb || null,
                      notion_routines_db_id: selectedRoutinesDb || null,
                      daily_planning_time: dailyPlanningTime,
                      rag_sync_interval_min: ragSyncInterval,
                      enable_cost_optimization: enableCostOptimization,
                      enable_performance_monitoring: enablePerformanceMonitoring,
                    })
                  }
                  disabled={saveMutation.isPending}
                >
                  {saveMutation.isPending ? "Saving..." : "Save Settings"}
                </Button>
                <Button variant="outline" onClick={() => refetch()}>Refresh Databases</Button>
              </div>
            </div>
          </CardContent>
        </Card>
      </main>
    </div>
  );
}


