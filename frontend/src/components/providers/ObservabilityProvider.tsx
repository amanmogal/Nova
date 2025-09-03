"use client";

import { ReactNode, useEffect } from "react";
import * as Sentry from "@sentry/react";
import posthog from "posthog-js";

interface Props { children: ReactNode }

export function ObservabilityProvider({ children }: Props) {
  useEffect(() => {
    const sentryDsn = process.env.NEXT_PUBLIC_SENTRY_DSN;
    if (typeof window !== "undefined" && sentryDsn && !(window as any).__sentryInitialised) {
      try {
        Sentry.init({ dsn: sentryDsn, tracesSampleRate: 1.0 });
        (window as any).__sentryInitialised = true;
      } catch {}
    }

    const phKey = process.env.NEXT_PUBLIC_POSTHOG_KEY;
    const phHost = process.env.NEXT_PUBLIC_POSTHOG_HOST || "https://app.posthog.com";
    if (typeof window !== "undefined" && phKey && !(window as any).__posthogInitialised) {
      try {
        posthog.init(phKey, { api_host: phHost, capture_pageview: true });
        (window as any).__posthogInitialised = true;
      } catch {}
    }
  }, []);

  return <>{children}</>;
}


