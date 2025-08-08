"use client";

import { ensureBackendRegistration, getBackendToken } from "@/lib/backendAuth";

const apiBase = process.env.NEXT_PUBLIC_API_BASE_URL as string | undefined;

async function authHeaders() {
  const token = getBackendToken() || (await ensureBackendRegistration());
  return token ? { Authorization: `Bearer ${token}` } : {};
}

export async function getUsageSummary() {
  if (!apiBase) throw new Error("NEXT_PUBLIC_API_BASE_URL not set");
  const headers = await authHeaders();
  const res = await fetch(`${apiBase}/usage/summary`, { headers });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function getUsageLogs(limit = 50, offset = 0) {
  if (!apiBase) throw new Error("NEXT_PUBLIC_API_BASE_URL not set");
  const headers = await authHeaders();
  const url = new URL(`${apiBase}/usage/logs`);
  url.searchParams.set("limit", String(limit));
  url.searchParams.set("offset", String(offset));
  const res = await fetch(url.toString(), { headers });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function listNotionDatabases(query?: string) {
  if (!apiBase) throw new Error("NEXT_PUBLIC_API_BASE_URL not set");
  const headers = { ...(await authHeaders()), "Content-Type": "application/json" } as Record<string, string>;
  const res = await fetch(`${apiBase}/notion/databases`, {
    method: "POST",
    headers,
    body: JSON.stringify({ query, limit: 20 }),
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function getUserConfig() {
  if (!apiBase) throw new Error("NEXT_PUBLIC_API_BASE_URL not set");
  const headers = await authHeaders();
  const res = await fetch(`${apiBase}/user/config`, { headers });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function updateUserConfig(payload: any) {
  if (!apiBase) throw new Error("NEXT_PUBLIC_API_BASE_URL not set");
  const headers = { ...(await authHeaders()), "Content-Type": "application/json" } as Record<string, string>;
  const res = await fetch(`${apiBase}/user/config`, { method: "PUT", headers, body: JSON.stringify(payload) });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function triggerRagSync() {
  if (!apiBase) throw new Error("NEXT_PUBLIC_API_BASE_URL not set");
  const headers = { ...(await authHeaders()), "Content-Type": "application/json" } as Record<string, string>;
  const res = await fetch(`${apiBase}/agent/sync`, { method: "POST", headers });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function createTask(taskData: any) {
  if (!apiBase) throw new Error("NEXT_PUBLIC_API_BASE_URL not set");
  const headers = { ...(await authHeaders()), "Content-Type": "application/json" } as Record<string, string>;
  const res = await fetch(`${apiBase}/tasks`, { method: "POST", headers, body: JSON.stringify({ task_data: taskData }) });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function runAgent(goal: string, query?: string, context?: any) {
  if (!apiBase) throw new Error("NEXT_PUBLIC_API_BASE_URL not set");
  const headers = { ...(await authHeaders()), "Content-Type": "application/json" } as Record<string, string>;
  const res = await fetch(`${apiBase}/agent/run`, { method: "POST", headers, body: JSON.stringify({ goal, query, context }) });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

"use client";

import { getSession } from "next-auth/react";

export const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const session = await getSession();
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(init?.headers as Record<string, string> | undefined),
  };

  // Attempt to send access token if present (may be Notion OAuth token)
  if (session?.accessToken && !headers["Authorization"]) {
    headers["Authorization"] = `Bearer ${session.accessToken}`;
  }

  const res = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers,
  });

  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(`API ${res.status}: ${text || res.statusText}`);
  }

  // Try to parse JSON, allow empty responses
  const contentType = res.headers.get("content-type") || "";
  if (contentType.includes("application/json")) {
    return (await res.json()) as T;
  }
  return undefined as unknown as T;
}

