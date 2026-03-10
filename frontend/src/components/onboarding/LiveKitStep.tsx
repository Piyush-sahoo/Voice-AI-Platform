import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

export interface LiveKitFormState {
  url: string;
  api_key: string;
  api_secret: string;
  apiKeyConfigured: boolean;
  apiSecretConfigured: boolean;
}

interface LiveKitStepProps {
  data: LiveKitFormState;
  onChange: (update: Partial<LiveKitFormState>) => void;
}

export function LiveKitStep({ data, onChange }: LiveKitStepProps) {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-semibold text-foreground">LiveKit Configuration</h2>
        <p className="mt-1 text-sm text-muted-foreground">
          Connect your LiveKit project so the platform can create rooms, SIP trunks, and dispatch agents.
        </p>
      </div>

      <div className="space-y-4">
        <div className="space-y-2">
          <Label htmlFor="livekit-url">LiveKit Project URL *</Label>
          <Input
            id="livekit-url"
            value={data.url}
            onChange={(e) => onChange({ url: e.target.value })}
            placeholder="wss://your-project.livekit.cloud"
            className="bg-background border-border text-foreground"
          />
        </div>

        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <Label htmlFor="livekit-api-key">API Key</Label>
            {data.apiKeyConfigured && (
              <span className="text-xs text-emerald-400">Configured ✓</span>
            )}
          </div>
          <Input
            id="livekit-api-key"
            type="password"
            value={data.api_key}
            onChange={(e) => onChange({ api_key: e.target.value, apiKeyConfigured: false })}
            placeholder={data.apiKeyConfigured ? "Enter to update existing key" : "Enter LiveKit API key"}
            className="bg-background border-border text-foreground"
          />
        </div>

        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <Label htmlFor="livekit-api-secret">API Secret</Label>
            {data.apiSecretConfigured && (
              <span className="text-xs text-emerald-400">Configured ✓</span>
            )}
          </div>
          <Input
            id="livekit-api-secret"
            type="password"
            value={data.api_secret}
            onChange={(e) => onChange({ api_secret: e.target.value, apiSecretConfigured: false })}
            placeholder={data.apiSecretConfigured ? "Enter to update existing secret" : "Enter LiveKit API secret"}
            className="bg-background border-border text-foreground"
          />
        </div>
      </div>
    </div>
  );
}

