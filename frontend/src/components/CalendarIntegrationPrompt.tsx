import { useEffect, useMemo, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { Calendar, Sparkles } from "lucide-react";

import { Button } from "@/components/ui/button";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";

const DISMISS_KEY = "google_calendar_prompt_dismissed";
const CONNECTED_KEY = "google_calendar_connected";
const ONBOARDING_COMPLETE_KEY = "workspace_onboarding_completed";

export function CalendarIntegrationPrompt() {
  const location = useLocation();
  const navigate = useNavigate();

  const [open, setOpen] = useState(false);
  const [dismissed, setDismissed] = useState(false);
  const [connected, setConnected] = useState(false);
  const [onboardingComplete, setOnboardingComplete] = useState(false);

  const shouldRender = useMemo(() => {
    if (location.pathname === "/settings") return false;
    return onboardingComplete && !dismissed && !connected;
  }, [location.pathname, onboardingComplete, dismissed, connected]);

  useEffect(() => {
    const isDismissed = localStorage.getItem(DISMISS_KEY) === "true";
    const isConnected = localStorage.getItem(CONNECTED_KEY) === "true";
    const isOnboardingComplete = localStorage.getItem(ONBOARDING_COMPLETE_KEY) === "true";

    setDismissed(isDismissed);
    setConnected(isConnected);
    setOnboardingComplete(isOnboardingComplete);
    setOpen(isOnboardingComplete && !isDismissed && !isConnected);
  }, []);

  useEffect(() => {
    const syncConnectionState = () => {
      const isConnected = localStorage.getItem(CONNECTED_KEY) === "true";
      const isOnboardingComplete = localStorage.getItem(ONBOARDING_COMPLETE_KEY) === "true";
      setConnected(isConnected);
      setOnboardingComplete(isOnboardingComplete);
      if (isConnected || !isOnboardingComplete) {
        setOpen(false);
      }
    };

    window.addEventListener("storage", syncConnectionState);
    return () => window.removeEventListener("storage", syncConnectionState);
  }, []);

  if (!shouldRender) return null;

  const handleNotNow = () => {
    localStorage.setItem(DISMISS_KEY, "true");
    setDismissed(true);
    setOpen(false);
  };

  const handleGoToSettings = () => {
    setOpen(false);
    navigate("/settings?highlight=google-calendar");
  };

  return (
    <div className="fixed bottom-6 right-6 z-50">
      <Popover open={open} onOpenChange={setOpen}>
        <PopoverTrigger asChild>
          <Button
            size="icon"
            className="h-11 w-11 rounded-full shadow-lg"
            aria-label="Google Calendar integration suggestion"
          >
            <Sparkles className="h-5 w-5" />
          </Button>
        </PopoverTrigger>
        <PopoverContent side="top" align="end" className="w-80 space-y-3">
          <div className="flex items-start gap-3">
            <div className="mt-0.5 rounded-md bg-primary/10 p-2 text-primary">
              <Calendar className="h-4 w-4" />
            </div>
            <div className="space-y-1">
              <p className="text-sm font-semibold text-foreground">
                Connect Google Calendar?
              </p>
              <p className="text-xs text-muted-foreground">
                Enable the AI agent to book meetings automatically during calls.
              </p>
            </div>
          </div>

          <div className="flex items-center justify-end gap-2">
            <Button variant="ghost" size="sm" onClick={handleNotNow}>
              Not now
            </Button>
            <Button size="sm" onClick={handleGoToSettings}>
              Yes, take me there
            </Button>
          </div>
        </PopoverContent>
      </Popover>
    </div>
  );
}
