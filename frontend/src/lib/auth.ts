import { NextAuthOptions } from "next-auth";
import { NotionProvider } from "@/lib/providers/notion";

export const authOptions: NextAuthOptions = {
  providers: [
    NotionProvider({
      clientId: process.env.NOTION_CLIENT_ID!,
      clientSecret: process.env.NOTION_CLIENT_SECRET!,
    }),
  ],
  callbacks: {
    async jwt({ token, account, profile }) {
      // Persist the OAuth access_token and or the user id to the token right after signin
      if (account) {
        token.accessToken = account.access_token;
        token.refreshToken = account.refresh_token;
        token.expiresAt = account.expires_at;
      }

      if (profile) {
        const p: any = profile as any;
        token.notionWorkspaceId = p?.workspace_id ?? p?.bot?.workspace_id ?? undefined;
        token.notionWorkspaceName = p?.workspace_name ?? undefined
      }

      return token;
    },
    async session({ session, token }) {
      // Send properties to the client, like an access_token and user id from a provider.
      session.accessToken = (token.accessToken as string | undefined);
      session.notionWorkspaceId = (token.notionWorkspaceId as string | undefined);
      session.notionWorkspaceName = (token.notionWorkspaceName as string | undefined);

      return session;
    },
  },
  pages: {
    signIn: '/auth/signin',
    signOut: '/auth/signout',
    error: '/auth/error',
  },
  session: {
    strategy: "jwt",
  },
  secret: process.env.NEXTAUTH_SECRET,
};

declare module "next-auth" {
  interface Session {
    accessToken?: string;
    notionWorkspaceId?: string;
    notionWorkspaceName?: string;
  }

  interface JWT {
    accessToken?: string;
    refreshToken?: string;
    expiresAt?: number;
    notionWorkspaceId?: string;
    notionWorkspaceName?: string;
  }
} 