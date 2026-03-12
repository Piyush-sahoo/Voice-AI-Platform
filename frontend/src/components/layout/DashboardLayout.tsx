import { ReactNode } from "react";
import { AppSidebar } from "./AppSidebar";
import { CalendarIntegrationPrompt } from "@/components/CalendarIntegrationPrompt";
import { OnboardingPrompt } from "@/components/OnboardingPrompt";

interface DashboardLayoutProps {
  children: ReactNode;
}

export function DashboardLayout({ children }: DashboardLayoutProps) {
  return (
    <div className="flex min-h-screen w-full bg-background">
      <AppSidebar />
      <main className="flex-1 overflow-auto">
        {children}
      </main>
      <OnboardingPrompt />
      <CalendarIntegrationPrompt />
    </div>
  );
}
