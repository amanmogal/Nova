import { ReactNode } from "react";
import { SideNav } from "@/components/navigation/SideNav";
import { AuthGuard } from "@/components/auth/AuthGuard";

export default function DashboardLayout({ children }: { children: ReactNode }) {
  return (
    <AuthGuard>
      <div className="min-h-screen bg-gray-50">
        <SideNav />
        <div className="ml-64 p-6">{children}</div>
      </div>
    </AuthGuard>
  );
}

