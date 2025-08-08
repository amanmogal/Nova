import NotionProvider from "next-auth/providers/notion";

export { NotionProvider };

import type { OAuthConfig } from "next-auth/providers";

interface NotionUser {
  id: string;
  name?: string;
  avatar_url?: string;
  person?: { email?: string };
  workspace_id?: string;
  workspace_name?: string;
  bot?: {
    owner?: { user?: { name?: string } };
    workspace_id?: string;
  };
}

// Custom NextAuth OAuth provider for Notion
export const NotionProvider: OAuthConfig<NotionUser> = {
  id: "notion",
  name: "Notion",
  type: "oauth",
  authorization: {
    url: "https://api.notion.com/v1/oauth/authorize",
    params: { owner: "user", response_type: "code" },
  },
  token: "https://api.notion.com/v1/oauth/token",
  userinfo: "https://api.notion.com/v1/users/me",
  checks: ["pkce", "state"],
  clientId: process.env.NOTION_CLIENT_ID,
  clientSecret: process.env.NOTION_CLIENT_SECRET,
  headers: {
    "Notion-Version": "2022-06-28",
  },
  profile(profile: NotionUser) {
    return {
      id: profile.id,
      name: profile.name || profile.bot?.owner?.user?.name || null,
      email: profile.person?.email || null,
      image: profile.avatar_url || null,
      workspace_id: profile.workspace_id ?? profile.bot?.workspace_id,
      workspace_name: profile.workspace_name ?? null,
    };
  },
};

