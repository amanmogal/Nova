import { NextAuthOptions } from "next-auth";
import { NotionProvider } from "next-auth/providers/notion";

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
        token.notionWorkspaceId = profile.workspace_id;
        token.notionWorkspaceName = profile.workspace_name;
      }
      
      return token;
    },
    async session({ session, token }) {
      // Send properties to the client, like an access_token and user id from a provider.
      session.accessToken = token.accessToken;
      session.notionWorkspaceId = token.notionWorkspaceId;
      session.notionWorkspaceName = token.notionWorkspaceName;
      
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