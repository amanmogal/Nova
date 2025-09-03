// Minimal Notion OAuth provider compatible with NextAuth v4
// Avoids importing provider types to prevent type resolution issues in build

type NotionRawProfile = {
  id: string;
  name?: string;
  avatar_url?: string;
  person?: { email?: string };
  workspace_id?: string;
  workspace_name?: string;
  bot?: { owner?: { user?: { name?: string } } ; workspace_id?: string };
};

export function NotionProvider(options: Record<string, unknown> = {}): any {
  const provider: any = {
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
    profile(profile: NotionRawProfile) {
      return {
        id: profile.id,
        name: profile?.name || profile?.bot?.owner?.user?.name || null,
        email: profile?.person?.email || null,
        image: profile?.avatar_url || null,
        workspace_id: profile?.workspace_id ?? profile?.bot?.workspace_id,
        workspace_name: profile?.workspace_name ?? null,
      } as Record<string, unknown>;
    },
    ...options,
  };
  return provider;
}


