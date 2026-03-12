import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import { Bot, Loader2 } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useToast } from "@/hooks/use-toast";
import {
  workspaceIntegrationsApi,
  type WorkspaceIntegrationsResponse,
  type WorkspaceIntegrationsPayload,
} from "@/lib/api";
import { LiveKitStep, type LiveKitFormState } from "@/components/onboarding/LiveKitStep";
import { AIProvidersStep, type AIProvidersFormState } from "@/components/onboarding/AIProvidersStep";
import { TelephonyStep, type TelephonyFormState } from "@/components/onboarding/TelephonyStep";
import { ReviewStep } from "@/components/onboarding/ReviewStep";

interface OnboardingFormState {
  livekit: LiveKitFormState;
  ai_providers: AIProvidersFormState;
  telephony: TelephonyFormState;
}

const MASK = "****";

export default function Onboarding() {
  const [currentStep, setCurrentStep] = useState(1);
  const [isLoading, setIsLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [hasExisting, setHasExisting] = useState(false);
  const [form, setForm] = useState<OnboardingFormState>({
    livekit: {
      url: "",
      api_key: "",
      api_secret: "",
      apiKeyConfigured: false,
      apiSecretConfigured: false,
    },
    ai_providers: {
      openai_key: "",
      deepgram_key: "",
      google_key: "",
      elevenlabs_key: "",
      cartesia_key: "",
      anthropic_key: "",
      assemblyai_key: "",
      configured: {
        openai: false,
        deepgram: false,
        google: false,
        elevenlabs: false,
        cartesia: false,
        anthropic: false,
        assemblyai: false,
      },
    },
    telephony: {
      sip_domain: "",
      sip_username: "",
      sip_password: "",
      outbound_number: "",
      sipPasswordConfigured: false,
    },
  });

  const { toast } = useToast();
  const navigate = useNavigate();

  useEffect(() => {
    const loadIntegrations = async () => {
      setIsLoading(true);
      try {
        const data = await workspaceIntegrationsApi.get().catch((error: any) => {
          if (error?.status === 404) {
            return null;
          }
          throw error;
        });

        if (data) {
          setHasExisting(true);
          localStorage.setItem("workspace_onboarding_completed", "true");
          hydrateFormFromResponse(data);
        }
      } catch (error) {
        const message = error instanceof Error ? error.message : "Failed to load workspace integrations";
        toast({
          title: "Error",
          description: message,
          variant: "destructive",
        });
      } finally {
        setIsLoading(false);
      }
    };

    loadIntegrations();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const hydrateFormFromResponse = (data: WorkspaceIntegrationsResponse) => {
    setForm((prev) => ({
      livekit: {
        url: data.livekit?.url || "",
        api_key: "",
        api_secret: "",
        apiKeyConfigured: data.livekit?.api_key === MASK,
        apiSecretConfigured: data.livekit?.api_secret === MASK,
      },
      ai_providers: {
        ...prev.ai_providers,
        openai_key: "",
        deepgram_key: "",
        google_key: "",
        elevenlabs_key: "",
        cartesia_key: "",
        anthropic_key: "",
        assemblyai_key: "",
        configured: {
          openai: data.ai_providers?.openai_key === MASK,
          deepgram: data.ai_providers?.deepgram_key === MASK,
          google: data.ai_providers?.google_key === MASK,
          elevenlabs: data.ai_providers?.elevenlabs_key === MASK,
          cartesia: data.ai_providers?.cartesia_key === MASK,
          anthropic: data.ai_providers?.anthropic_key === MASK,
          assemblyai: data.ai_providers?.assemblyai_key === MASK,
        },
      },
      telephony: {
        sip_domain: data.telephony?.sip_domain || "",
        sip_username: data.telephony?.sip_username || "",
        outbound_number: data.telephony?.outbound_number || "",
        sip_password: "",
        sipPasswordConfigured: data.telephony?.sip_password === MASK,
      },
    }));
  };

  const totalSteps = 4;

  const handleNext = () => {
    if (currentStep === 1) {
      if (!form.livekit.url.trim()) {
        toast({
          title: "LiveKit URL required",
          description: "Please enter your LiveKit project URL to continue.",
          variant: "destructive",
        });
        return;
      }
    }

    if (currentStep === 3) {
      if (!form.telephony.sip_domain.trim() || !form.telephony.sip_username.trim()) {
        toast({
          title: "Missing telephony details",
          description: "SIP Domain and SIP Username are required.",
          variant: "destructive",
        });
        return;
      }
    }

    setCurrentStep((step) => Math.min(step + 1, totalSteps));
  };

  const handleBack = () => {
    setCurrentStep((step) => Math.max(step - 1, 1));
  };

  const buildPayload = (): WorkspaceIntegrationsPayload => {
    const payload: WorkspaceIntegrationsPayload = {};

    if (form.livekit.url.trim() || form.livekit.api_key.trim() || form.livekit.api_secret.trim()) {
      payload.livekit = {};
      if (form.livekit.url.trim()) payload.livekit.url = form.livekit.url.trim();
      if (form.livekit.api_key.trim()) payload.livekit.api_key = form.livekit.api_key.trim();
      if (form.livekit.api_secret.trim()) payload.livekit.api_secret = form.livekit.api_secret.trim();
    }

    const ai = form.ai_providers;
    const aiPayload: WorkspaceIntegrationsPayload["ai_providers"] = {};
    if (ai.openai_key.trim()) aiPayload.openai_key = ai.openai_key.trim();
    if (ai.deepgram_key.trim()) aiPayload.deepgram_key = ai.deepgram_key.trim();
    if (ai.google_key.trim()) aiPayload.google_key = ai.google_key.trim();
    if (ai.elevenlabs_key.trim()) aiPayload.elevenlabs_key = ai.elevenlabs_key.trim();
    if (ai.cartesia_key.trim()) aiPayload.cartesia_key = ai.cartesia_key.trim();
    if (ai.anthropic_key.trim()) aiPayload.anthropic_key = ai.anthropic_key.trim();
    if (ai.assemblyai_key.trim()) aiPayload.assemblyai_key = ai.assemblyai_key.trim();
    if (Object.keys(aiPayload).length > 0) {
      payload.ai_providers = aiPayload;
    }

    const tel = form.telephony;
    if (
      tel.sip_domain.trim() ||
      tel.sip_username.trim() ||
      tel.sip_password.trim() ||
      tel.outbound_number.trim()
    ) {
      payload.telephony = {};
      if (tel.sip_domain.trim()) payload.telephony.sip_domain = tel.sip_domain.trim();
      if (tel.sip_username.trim()) payload.telephony.sip_username = tel.sip_username.trim();
      if (tel.sip_password.trim()) payload.telephony.sip_password = tel.sip_password.trim();
      if (tel.outbound_number.trim()) payload.telephony.outbound_number = tel.outbound_number.trim();
    }

    return payload;
  };

  const handleFinish = async () => {
    const payload = buildPayload();

    if (!payload.livekit || !payload.livekit.url) {
      toast({
        title: "LiveKit URL required",
        description: "Please provide at least a LiveKit project URL before finishing.",
        variant: "destructive",
      });
      setCurrentStep(1);
      return;
    }

    setIsSubmitting(true);
    try {
      if (hasExisting) {
        await workspaceIntegrationsApi.update(payload);
      } else {
        await workspaceIntegrationsApi.create(payload);
      }

      toast({
        title: "Workspace configured",
        description: "Your integrations have been saved successfully.",
      });

      localStorage.setItem("workspace_onboarding_completed", "true");
      localStorage.removeItem("onboarding_prompt_dismissed");

      navigate("/dashboard", { replace: true });
    } catch (error) {
      const message = error instanceof Error ? error.message : "Failed to save workspace integrations";
      toast({
        title: "Error",
        description: message,
        variant: "destructive",
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  const renderStep = () => {
    switch (currentStep) {
      case 1:
        return (
          <LiveKitStep
            data={form.livekit}
            onChange={(update) => setForm((prev) => ({ ...prev, livekit: { ...prev.livekit, ...update } }))}
          />
        );
      case 2:
        return (
          <AIProvidersStep
            data={form.ai_providers}
            onChange={(update) =>
              setForm((prev) => ({ ...prev, ai_providers: { ...prev.ai_providers, ...update } }))
            }
          />
        );
      case 3:
        return (
          <TelephonyStep
            data={form.telephony}
            onChange={(update) => setForm((prev) => ({ ...prev, telephony: { ...prev.telephony, ...update } }))}
          />
        );
      case 4:
      default:
        return <ReviewStep livekit={form.livekit} aiProviders={form.ai_providers} telephony={form.telephony} />;
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-background px-4 py-8">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3 }}
        className="w-full max-w-3xl"
      >
        <Card className="border-border bg-card text-foreground shadow-xl">
          <CardHeader className="flex flex-row items-center justify-between border-b border-border">
            <div className="flex items-center gap-3">
              <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-primary/10">
                <Bot className="h-5 w-5 text-primary" />
              </div>
              <div>
                <CardTitle className="text-lg font-semibold">Workspace Onboarding</CardTitle>
                <p className="text-xs text-muted-foreground">
                  Step {currentStep} of {totalSteps}
                </p>
              </div>
            </div>
          </CardHeader>

          <CardContent className="space-y-6 pt-6">
            {isLoading ? (
              <div className="flex h-40 items-center justify-center">
                <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
              </div>
            ) : (
              <>
                {renderStep()}

                <div className="mt-6 flex items-center justify-between border-t border-border pt-4">
                  <div className="text-xs text-muted-foreground">
                    You can update these settings later from the settings area.
                  </div>
                  <div className="flex gap-3">
                    <Button
                      variant="outline"
                      onClick={handleBack}
                      disabled={currentStep === 1 || isSubmitting}
                    >
                      Back
                    </Button>
                    {currentStep < totalSteps && (
                      <Button onClick={handleNext} disabled={isSubmitting}>
                        Next
                      </Button>
                    )}
                    {currentStep === totalSteps && (
                      <Button onClick={handleFinish} disabled={isSubmitting}>
                        {isSubmitting ? (
                          <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                        ) : (
                          "Finish"
                        )}
                      </Button>
                    )}
                  </div>
                </div>
              </>
            )}
          </CardContent>
        </Card>
      </motion.div>
    </div>
  );
}

