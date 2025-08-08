"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { FileText, Settings, BarChart3, Calendar } from "lucide-react";

export function SideNav() {
  const pathname = usePathname();

  const linkClass = (href: string): string =>
    `flex items-center gap-2 rounded-lg px-4 py-2 text-sm font-medium ${
      pathname === href || pathname.startsWith(href)
        ? "bg-gray-100 text-gray-700"
        : "text-gray-500 hover:bg-gray-100 hover:text-gray-700"
    }`;

  return (
    <aside className="fixed left-0 top-0 h-screen w-64 border-r bg-white">
      <div className="px-4 py-6">
        <Link href="/dashboard" className="flex items-center gap-2">
          <FileText className="h-8 w-8 text-blue-600" />
          <span className="text-xl font-bold text-gray-900">Notion Agent</span>
        </Link>

        <ul className="mt-6 space-y-1">
          <li>
            <Link href="/dashboard" className={linkClass("/dashboard")}>
              <BarChart3 className="h-5 w-5" />
              <span>Dashboard</span>
            </Link>
          </li>
          <li>
            <Link href="/dashboard/integration" className={linkClass("/dashboard/integration")}>
              <Calendar className="h-5 w-5" />
              <span>Integration</span>
            </Link>
          </li>
          <li>
            <Link href="/dashboard/subscription" className={linkClass("/dashboard/subscription")}>
              <BarChart3 className="h-5 w-5" />
              <span>Subscription</span>
            </Link>
          </li>
          <li>
            <Link href="/dashboard/analytics" className={linkClass("/dashboard/analytics")}>
              <BarChart3 className="h-5 w-5" />
              <span>Analytics</span>
            </Link>
          </li>
          <li>
            <Link href="/dashboard/settings" className={linkClass("/dashboard/settings")}>
              <Settings className="h-5 w-5" />
              <span>Settings</span>
            </Link>
          </li>
        </ul>
      </div>
    </aside>
  );
}

