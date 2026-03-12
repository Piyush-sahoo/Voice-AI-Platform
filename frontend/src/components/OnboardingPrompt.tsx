import { useEffect, useMemo, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { Rocket, Sparkles } from "lucide-react";

import { Button } from "@/components/ui/button";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import { workspaceIntegrationsApi } from "@/lib/api";

const ONBOARDING_DISMISS_KEY = "onboarding_prompt_dismissed";
const ONBOARDING_COMPLETE_KEY = "workspace_onboarding_completed";

export function OnboardingPrompt() {
  const location = useLocation();
  const navigate = useNavigate();

  const [open, setOpen] = useState(false);
  const [dismissed, setDismissed] = useState(false);
  const [onboardingComplete, setOnboardingComplete] = useState(false);

  const shouldRender = useMemo(() => {
    if (location.pathname === "/onboarding") return false;
    return !dismissed && !onboardingComplete;
  }, [location.pathname, dismissed, onboardingComplete]);

  useEffect(() => {
    const isDismissed = localStorage.getItem(ONBOARDING_DISMISS_KEY) === "true";
    const isCompleted = localStorage.getItem(ONBOARDING_COMPLETE_KEY) === "true";

    setDismissed(isDismissed);
    setOnboardingComplete(isCompleted);
    setOpen(!isDismissed && !isCompleted);
  }, []);

  useEffect(() => {
    let cancelled = false;

    const validateOnboardingStatus = async () => {
      const isCompleted = localStorage.getItem(ONBOARDING_COMPLETE_KEY) === "true";
      if (isCompleted) return;

      try {
        const integrations = await workspaceIntegrationsApi.get();
        if (cancelled) return;

        const hasLiveKitUrl = Boolean(integrations?.livekit?.url);
        if (hasLiveKitUrl) {
          localStorage.setItem(ONBOARDING_COMPLETE_KEY, "true");
          setOnboardingComplete(true);
          setOpen(false);
        }
      } catch (error: any) {
        // 404 means onboarding not completed yet; keep prompt visible.
        if (cancelled) return;
        if (error?.status !== 404) {
          // For transient errors we keep the prompt available.
          setOpen(true);
        }
      }
    };

    validateOnboardingStatus();

    return () => {
      cancelled = true;
    };
  }, []);

  if (!shouldRender) return null;

  const handleNotNow = () => {
    localStorage.setItem(ONBOARDING_DISMISS_KEY, "true");
    setDismissed(true);
    setOpen(false);
  };

  const handleStartOnboarding = () => {
    setOpen(false);
    navigate("/onboarding");
  };

  return (
    <div className="fixed bottom-20 right-6 z-50">
      <Popover open={open} onOpenChange={setOpen}>
        <PopoverTrigger asChild>
          <Button
            size="icon"
            variant="secondary"
            className="h-11 w-11 rounded-full shadow-lg"
            aria-label="Onboarding setup suggestion"
          >
            <Sparkles className="h-5 w-5" />
          </Button>
        </PopoverTrigger>
        <PopoverContent side="top" align="end" className="w-80 space-y-3">
          <div className="flex items-start gap-3">
            <div className="mt-0.5 rounded-md bg-primary/10 p-2 text-primary">
              <Rocket className="h-4 w-4" />
            </div>
            <div className="space-y-1">
              <p className="text-sm font-semibold text-foreground">
                Complete workspace onboarding?
              </p>
              <p className="text-xs text-muted-foreground">
                Configure LiveKit and providers so calling works end-to-end.
              </p>
            </div>
          </div>

          <div className="flex items-center justify-end gap-2">
            <Button variant="ghost" size="sm" onClick={handleNotNow}>
              Not now
            </Button>
            <Button size="sm" onClick={handleStartOnboarding}>
              Start onboarding
            </Button>
          </div>
        </PopoverContent>
      </Popover>
    </div>
  );
}
