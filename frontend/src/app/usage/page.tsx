"use client";

import { useQuery } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import { useEffect } from "react";
import { useSession } from "next-auth/react";
import { getUsageLogs, getUsageSummary } from "@/lib/api";
import { Card, CardHeader, CardTitle, CardContent, CardDescription } from "@/components/ui/card";

export default function UsagePage() {
  const router = useRouter();
  const { status } = useSession();

  useEffect(() => {
    if (status === "unauthenticated") router.push("/auth/signin");
  }, [status, router]);

  const { data: summary } = useQuery({ queryKey: ["usageSummary"], queryFn: getUsageSummary, enabled: status === "authenticated" });
  const { data: logs, isLoading } = useQuery({ queryKey: ["usageLogs"], queryFn: () => getUsageLogs(100, 0), enabled: status === "authenticated" });

  if (status === "loading" || isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-600" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <main className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8">
        <Card>
          <CardHeader>
            <CardTitle>Usage</CardTitle>
            <CardDescription>Monthly totals and recent operations</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
              <div>
                <div className="text-xs text-gray-500">Month</div>
                <div className="text-lg font-semibold">{summary?.month}</div>
              </div>
              <div>
                <div className="text-xs text-gray-500">Total Tokens</div>
                <div className="text-lg font-semibold">{summary?.total_tokens?.toLocaleString?.() ?? summary?.total_tokens}</div>
              </div>
              <div>
                <div className="text-xs text-gray-500">Total Cost</div>
                <div className="text-lg font-semibold">${summary?.total_cost_usd}</div>
              </div>
            </div>

            <div className="mt-4">
              <div className="text-sm font-medium mb-2">Recent Logs</div>
              <div className="overflow-x-auto border rounded-md">
                <table className="min-w-full text-sm">
                  <thead className="bg-gray-100 text-gray-600">
                    <tr>
                      <th className="text-left px-3 py-2">Time</th>
                      <th className="text-left px-3 py-2">Operation</th>
                      <th className="text-left px-3 py-2">Tokens</th>
                      <th className="text-left px-3 py-2">Cost</th>
                      <th className="text-left px-3 py-2">Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {(logs || []).map((row: any) => (
                      <tr key={row.id} className="border-t">
                        <td className="px-3 py-2">{new Date(row.created_at).toLocaleString()}</td>
                        <td className="px-3 py-2">{row.operation_type}</td>
                        <td className="px-3 py-2">{row.tokens_used}</td>
                        <td className="px-3 py-2">${row.cost_usd}</td>
                        <td className="px-3 py-2">{row.success ? "Success" : "Failed"}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </CardContent>
        </Card>
      </main>
    </div>
  );
}


