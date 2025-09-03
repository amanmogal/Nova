"use client";

import { getSession } from "next-auth/react";

const TOKEN_KEY = "backendToken";

export function getBackendToken(): string | null {
  if (typeof window === "undefined") return null;
  return window.localStorage.getItem(TOKEN_KEY);
}

export async function ensureBackendRegistration(): Promise<string | null> {
  if (typeof window === "undefined") return null;
  const existing = getBackendToken();
  if (existing) return existing;

  const session = await getSession();
  if (!session?.user?.email) return null;

  const apiBase = process.env.NEXT_PUBLIC_API_BASE_URL;
  if (!apiBase) {
    console.error("NEXT_PUBLIC_API_BASE_URL not set");
    return null;
  }

  try {
    const res = await fetch(`${apiBase}/auth/register`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        email: session.user.email,
        notion_access_token: (session as unknown as { accessToken?: string })?.accessToken,
        notion_workspace_id: (session as unknown as { notionWorkspaceId?: string })?.notionWorkspaceId,
      }),
    });
    if (!res.ok) {
      console.error("Registration failed", await res.text());
      return null;
    }
    const data = await res.json();
    const token = data?.token as string | undefined;
    if (token) {
      window.localStorage.setItem(TOKEN_KEY, token);
      return token;
    }
    return null;
  } catch (err) {
    console.error("Registration error", err);
    return null;
  }
}


