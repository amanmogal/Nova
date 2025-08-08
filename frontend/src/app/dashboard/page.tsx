"use client";

import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { FileText, Settings, BarChart3, Calendar, CheckCircle, Clock } from "lucide-react";
import { useSession } from "next-auth/react";
import { useRouter } from "next/navigation";
import { useEffect } from "react";
import { useQuery } from "@tanstack/react-query";
import { getUsageSummary } from "@/lib/api";

export default function DashboardPage() {
  const { data: session, status } = useSession();
  const router = useRouter();

  useEffect(() => {
    if (status === "unauthenticated") {
      router.push("/auth/signin");
    }
  }, [status, router]);

  const { data: usage, isLoading } = useQuery({
    queryKey: ["usageSummary"],
    queryFn: getUsageSummary,
    enabled: status === "authenticated",
    retry: 1,
  });

  if (status === "loading" || isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (!session) {
    return null;
  }

  const totalTokens = usage?.total_tokens ?? 0;
  const monthlyRequests = usage?.monthly_requests ?? 0;
  const completionRate = 87; // placeholder

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Welcome Section */}
        <div className="mb-8">
          <h2 className="text-2xl font-bold text-gray-900 mb-2">
            Welcome back!
          </h2>
          <p className="text-gray-600">
            Your Notion workspace: {(session as any).notionWorkspaceName || "Connected Workspace"}
          </p>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Monthly Requests</CardTitle>
              <CheckCircle className="h-4 w-4 text-green-600" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{monthlyRequests}</div>
              <p className="text-xs text-muted-foreground">From usage summary</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Total Tokens</CardTitle>
              <Clock className="h-4 w-4 text-blue-600" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{totalTokens.toLocaleString()}</div>
              <p className="text-xs text-muted-foreground">Used this month</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Completion Rate</CardTitle>
              <BarChart3 className="h-4 w-4 text-purple-600" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{completionRate}%</div>
              <p className="text-xs text-muted-foreground">Agent action success</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">This Month</CardTitle>
              <Calendar className="h-4 w-4 text-orange-600" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{new Date().toISOString().slice(0,7)}</div>
              <p className="text-xs text-muted-foreground">Usage period</p>
            </CardContent>
          </Card>
        </div>

        {/* Quick Actions */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <Card>
            <CardHeader>
              <CardTitle>Quick Actions</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <Button className="w-full justify-start" variant="outline">
                <FileText className="h-4 w-4 mr-2" />
                Create New Task
              </Button>
              <Button className="w-full justify-start" variant="outline">
                <Clock className="h-4 w-4 mr-2" />
                Schedule Routine
              </Button>
              <Button className="w-full justify-start" variant="outline" onClick={() => router.push("/usage") }>
                <BarChart3 className="h-4 w-4 mr-2" />
                Usage
              </Button>
              <Button className="w-full justify-start" variant="outline" onClick={() => router.push("/settings") }>
                <BarChart3 className="h-4 w-4 mr-2" />
                Configure Databases
              </Button>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Recent Activity</CardTitle>
              <CardDescription>
                Your latest interactions with the agent
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="flex items-center space-x-3">
                  <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                  <div className="flex-1">
                    <p className="text-sm font-medium">Task completed</p>
                    <p className="text-xs text-gray-500">"Review project proposal" marked as done</p>
                  </div>
                  <span className="text-xs text-gray-400">2h ago</span>
                </div>
                
              </div>
            </CardContent>
          </Card>
        </div>
      </main>
    </div>
  );
} 