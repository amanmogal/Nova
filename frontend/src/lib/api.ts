"use client";

import { ensureBackendRegistration, getBackendToken } from "@/lib/backendAuth";

const apiBase = process.env.NEXT_PUBLIC_API_BASE_URL as string | undefined;

async function authHeaders(): Promise<Record<string, string>> {
  const token = getBackendToken() || (await ensureBackendRegistration());
  const headers: Record<string, string> = {};
  if (token) headers["Authorization"] = `Bearer ${token}`;
  return headers;
}

export async function getUsageSummary() {
  if (!apiBase) throw new Error("NEXT_PUBLIC_API_BASE_URL not set");
  const headers = await authHeaders();
  const res = await fetch(`${apiBase}/usage/summary`, { headers: headers as HeadersInit });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function getUsageLogs(limit = 50, offset = 0) {
  if (!apiBase) throw new Error("NEXT_PUBLIC_API_BASE_URL not set");
  const headers = await authHeaders();
  const url = new URL(`${apiBase}/usage/logs`);
  url.searchParams.set("limit", String(limit));
  url.searchParams.set("offset", String(offset));
  const res = await fetch(url.toString(), { headers: headers as HeadersInit });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function listNotionDatabases(query?: string) {
  if (!apiBase) throw new Error("NEXT_PUBLIC_API_BASE_URL not set");
  const headers = { ...(await authHeaders()), "Content-Type": "application/json" } as Record<string, string>;
  const res = await fetch(`${apiBase}/notion/databases`, {
    method: "POST",
    headers: headers as HeadersInit,
    body: JSON.stringify({ query, limit: 20 }),
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function getUserConfig() {
  if (!apiBase) throw new Error("NEXT_PUBLIC_API_BASE_URL not set");
  const headers = await authHeaders();
  const res = await fetch(`${apiBase}/user/config`, { headers: headers as HeadersInit });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function updateUserConfig(payload: Record<string, unknown>) {
  if (!apiBase) throw new Error("NEXT_PUBLIC_API_BASE_URL not set");
  const headers = { ...(await authHeaders()), "Content-Type": "application/json" } as Record<string, string>;
  const res = await fetch(`${apiBase}/user/config`, { method: "PUT", headers: headers as HeadersInit, body: JSON.stringify(payload) });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function triggerRagSync() {
  if (!apiBase) throw new Error("NEXT_PUBLIC_API_BASE_URL not set");
  const headers = { ...(await authHeaders()), "Content-Type": "application/json" } as Record<string, string>;
  const res = await fetch(`${apiBase}/agent/sync`, { method: "POST", headers: headers as HeadersInit });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function createTask(taskData: { title: string }) {
  if (!apiBase) throw new Error("NEXT_PUBLIC_API_BASE_URL not set");
  const headers = { ...(await authHeaders()), "Content-Type": "application/json" } as Record<string, string>;
  const res = await fetch(`${apiBase}/tasks`, { method: "POST", headers: headers as HeadersInit, body: JSON.stringify({ task_data: taskData }) });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function runAgent(goal: string, query?: string, context?: Record<string, unknown>) {
  if (!apiBase) throw new Error("NEXT_PUBLIC_API_BASE_URL not set");
  const headers = { ...(await authHeaders()), "Content-Type": "application/json" } as Record<string, string>;
  const res = await fetch(`${apiBase}/agent/run`, { method: "POST", headers: headers as HeadersInit, body: JSON.stringify({ goal, query, context }) });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

// removed legacy apiFetch helper
