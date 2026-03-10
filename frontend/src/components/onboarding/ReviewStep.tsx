import { Card, CardContent } from "@/components/ui/card";

import type { LiveKitFormState } from "./LiveKitStep";
import type { AIProvidersFormState } from "./AIProvidersStep";
import type { TelephonyFormState } from "./TelephonyStep";

interface ReviewStepProps {
  livekit: LiveKitFormState;
  aiProviders: AIProvidersFormState;
  telephony: TelephonyFormState;
}

const secretDisplay = (configured: boolean, value: string) => {
  if (configured || value.trim().length > 0) {
    return "********";
  }
  return "Not configured";
};

export function ReviewStep({ livekit, aiProviders, telephony }: ReviewStepProps) {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-semibold text-foreground">Review Configuration</h2>
        <p className="mt-1 text-sm text-muted-foreground">
          Confirm your integration settings before finishing onboarding. Secret values are masked for security.
        </p>
      </div>

      <div className="space-y-4">
        <Card className="border-border bg-muted/40">
          <CardContent className="space-y-2 pt-4">
            <h3 className="text-sm font-semibold text-foreground">LiveKit</h3>
            <p className="text-xs text-muted-foreground break-all">
              <span className="font-medium">Project URL:</span> {livekit.url || "Not configured"}
            </p>
            <p className="text-xs text-muted-foreground">
              <span className="font-medium">API Key:</span>{" "}
              {secretDisplay(livekit.apiKeyConfigured, livekit.api_key)}
            </p>
            <p className="text-xs text-muted-foreground">
              <span className="font-medium">API Secret:</span>{" "}
              {secretDisplay(livekit.apiSecretConfigured, livekit.api_secret)}
            </p>
          </CardContent>
        </Card>

        <Card className="border-border bg-muted/40">
          <CardContent className="space-y-2 pt-4">
            <h3 className="text-sm font-semibold text-foreground">AI Providers</h3>
            <p className="text-xs text-muted-foreground">
              <span className="font-medium">OpenAI:</span>{" "}
              {secretDisplay(aiProviders.configured.openai, aiProviders.openai_key)}
            </p>
            <p className="text-xs text-muted-foreground">
              <span className="font-medium">Deepgram:</span>{" "}
              {secretDisplay(aiProviders.configured.deepgram, aiProviders.deepgram_key)}
            </p>
            <p className="text-xs text-muted-foreground">
              <span className="font-medium">Google:</span>{" "}
              {secretDisplay(aiProviders.configured.google, aiProviders.google_key)}
            </p>
            <p className="text-xs text-muted-foreground">
              <span className="font-medium">ElevenLabs:</span>{" "}
              {secretDisplay(aiProviders.configured.elevenlabs, aiProviders.elevenlabs_key)}
            </p>
            <p className="text-xs text-muted-foreground">
              <span className="font-medium">Cartesia:</span>{" "}
              {secretDisplay(aiProviders.configured.cartesia, aiProviders.cartesia_key)}
            </p>
            <p className="text-xs text-muted-foreground">
              <span className="font-medium">Anthropic:</span>{" "}
              {secretDisplay(aiProviders.configured.anthropic, aiProviders.anthropic_key)}
            </p>
            <p className="text-xs text-muted-foreground">
              <span className="font-medium">AssemblyAI:</span>{" "}
              {secretDisplay(aiProviders.configured.assemblyai, aiProviders.assemblyai_key)}
            </p>
          </CardContent>
        </Card>

        <Card className="border-border bg-muted/40">
          <CardContent className="space-y-2 pt-4">
            <h3 className="text-sm font-semibold text-foreground">Telephony</h3>
            <p className="text-xs text-muted-foreground break-all">
              <span className="font-medium">SIP Domain:</span> {telephony.sip_domain || "Not configured"}
            </p>
            <p className="text-xs text-muted-foreground">
              <span className="font-medium">SIP Username:</span> {telephony.sip_username || "Not configured"}
            </p>
            <p className="text-xs text-muted-foreground">
              <span className="font-medium">SIP Password:</span>{" "}
              {secretDisplay(telephony.sipPasswordConfigured, telephony.sip_password)}
            </p>
            <p className="text-xs text-muted-foreground break-all">
              <span className="font-medium">Outbound Number:</span> {telephony.outbound_number || "Not configured"}
            </p>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

