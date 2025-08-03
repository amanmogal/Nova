"use client";

import { signIn, getSession } from "next-auth/react";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { FileText, Loader2 } from "lucide-react";

export default function SignInPage() {
  const router = useRouter();
  const [isLoading, setIsLoading] = useState(false);
  const [isCheckingSession, setIsCheckingSession] = useState(true);

  useEffect(() => {
    // Check if user is already signed in
    getSession().then((session) => {
      if (session) {
        router.push("/dashboard");
      } else {
        setIsCheckingSession(false);
      }
    });
  }, [router]);

  const handleSignIn = async () => {
    setIsLoading(true);
    try {
      await signIn("notion", { callbackUrl: "/dashboard" });
    } catch (error) {
      console.error("Sign in error:", error);
      setIsLoading(false);
    }
  };

  if (isCheckingSession) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin" />
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-100 p-4">
      <Card className="w-full max-w-md">
        <CardHeader className="text-center">
          <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-blue-100">
            <FileText className="h-8 w-8 text-blue-600" />
          </div>
          <CardTitle className="text-2xl font-bold">Welcome to Notion Agent</CardTitle>
          <CardDescription>
            Connect your Notion workspace to get started with AI-powered task management
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Button
            onClick={handleSignIn}
            disabled={isLoading}
            className="w-full"
            size="lg"
          >
            {isLoading ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Connecting...
              </>
            ) : (
              <>
                <FileText className="mr-2 h-4 w-4" />
                Connect with Notion
              </>
            )}
          </Button>
          
          <div className="mt-6 text-center text-sm text-gray-600">
            <p>By connecting, you agree to our Terms of Service and Privacy Policy</p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
} 