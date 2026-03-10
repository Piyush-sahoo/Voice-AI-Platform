import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

export interface AIProvidersFormState {
  openai_key: string;
  deepgram_key: string;
  google_key: string;
  elevenlabs_key: string;
  cartesia_key: string;
  anthropic_key: string;
  assemblyai_key: string;
  configured: {
    openai: boolean;
    deepgram: boolean;
    google: boolean;
    elevenlabs: boolean;
    cartesia: boolean;
    anthropic: boolean;
    assemblyai: boolean;
  };
}

interface AIProvidersStepProps {
  data: AIProvidersFormState;
  onChange: (update: Partial<AIProvidersFormState>) => void;
}

export function AIProvidersStep({ data, onChange }: AIProvidersStepProps) {
  const handleKeyChange = (field: keyof Omit<AIProvidersFormState, "configured">, value: string) => {
    const configuredUpdate: Partial<AIProvidersFormState["configured"]> = {};
    if (field === "openai_key") configuredUpdate.openai = false;
    if (field === "deepgram_key") configuredUpdate.deepgram = false;
    if (field === "google_key") configuredUpdate.google = false;
    if (field === "elevenlabs_key") configuredUpdate.elevenlabs = false;
    if (field === "cartesia_key") configuredUpdate.cartesia = false;
    if (field === "anthropic_key") configuredUpdate.anthropic = false;
    if (field === "assemblyai_key") configuredUpdate.assemblyai = false;

    onChange({
      [field]: value,
      configured: { ...data.configured, ...configuredUpdate },
    } as Partial<AIProvidersFormState>);
  };

  const renderField = (
    id: string,
    label: string,
    field: keyof Omit<AIProvidersFormState, "configured">,
    configuredFlag: keyof AIProvidersFormState["configured"],
    placeholder: string,
  ) => (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <Label htmlFor={id}>{label}</Label>
        {data.configured[configuredFlag] && (
          <span className="text-xs text-emerald-400">Configured ✓</span>
        )}
      </div>
      <Input
        id={id}
        type="password"
        value={data[field] as string}
        onChange={(e) => handleKeyChange(field, e.target.value)}
        placeholder={data.configured[configuredFlag] ? "Enter to update existing key" : placeholder}
        className="bg-background border-border text-foreground"
      />
    </div>
  );

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-semibold text-foreground">AI Provider Keys</h2>
        <p className="mt-1 text-sm text-muted-foreground">
          Configure the AI providers your workspace will use. At least one provider is recommended so your agents can
          process and generate speech.
        </p>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        {renderField(
          "openai-key",
          "OpenAI API Key",
          "openai_key",
          "openai",
          "Enter OpenAI API key",
        )}
        {renderField(
          "deepgram-key",
          "Deepgram API Key",
          "deepgram_key",
          "deepgram",
          "Enter Deepgram API key",
        )}
        {renderField(
          "google-key",
          "Google API Key",
          "google_key",
          "google",
          "Enter Google API key",
        )}
        {renderField(
          "elevenlabs-key",
          "ElevenLabs API Key",
          "elevenlabs_key",
          "elevenlabs",
          "Enter ElevenLabs API key",
        )}
        {renderField(
          "cartesia-key",
          "Cartesia API Key",
          "cartesia_key",
          "cartesia",
          "Enter Cartesia API key",
        )}
        {renderField(
          "anthropic-key",
          "Anthropic API Key",
          "anthropic_key",
          "anthropic",
          "Enter Anthropic API key",
        )}
        {renderField(
          "assemblyai-key",
          "AssemblyAI API Key",
          "assemblyai_key",
          "assemblyai",
          "Enter AssemblyAI API key",
        )}
      </div>

      <p className="text-xs text-muted-foreground">
        You can configure multiple providers and select which one each assistant uses in their voice settings later.
      </p>
    </div>
  );
}

