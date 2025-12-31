import { useEffect, useState } from "react";
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Switch } from "@/components/ui/switch";
import { Slider } from "@/components/ui/slider";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { ScrollArea } from "@/components/ui/scroll-area";
import { voiceOptions, languageOptions, modeOptions, sttProviderOptions, llmProviderOptions, ttsProviderOptions, realtimeProviderOptions } from "@/data/mockAgents";
import { Volume2, Loader2 } from "lucide-react";
import { toast } from "sonner";

// Extended voice configuration for backend
interface VoiceConfig {
  provider: string;
  voice_id: string;
  mode?: string;
  realtime_provider?: string;
  realtime_model?: string;
  stt_provider?: string;
  stt_model?: string;
  stt_language?: string;
  llm_provider?: string;
  llm_model?: string;
  tts_provider?: string;
  tts_model?: string;
}

// Compatible with backend Assistant model
interface Agent {
  assistant_id?: string;
  name: string;
  description?: string;
  instructions: string;
  model_provider?: string;
  model_name?: string;
  voice?: VoiceConfig;
  language?: string;
  temperature?: number;
  first_message?: string;
  is_active?: boolean;
}

// UI State Interface (flattened for easier handling)
interface AgentFormData {
  name: string;
  description: string;
  instructions: string;
  voice: string;
  language: string;
  first_message: string;
  temperature: number;
  // Voice AI Mode
  mode: string;
  // Realtime mode
  realtime_provider: string;
  realtime_model: string;
  // Pipeline mode
  stt_provider: string;
  stt_model: string;
  llm_provider: string;
  llm_model: string;
  tts_provider: string;
  tts_model: string;
}

interface AgentDrawerProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  agent: any | null; // Using any to handle mismatch between mock/real types temporarily
  onSave: (agent: Partial<Agent>) => void;
}

export function AgentDrawer({ open, onOpenChange, agent, onSave }: AgentDrawerProps) {
  const [formData, setFormData] = useState<AgentFormData>({
    name: "",
    description: "",
    instructions: "",
    voice: "alloy",
    language: "en-US",
    first_message: "",
    temperature: 0.8,
    // Voice AI Mode
    mode: "realtime",
    realtime_provider: "openai",
    realtime_model: "gpt-4o-realtime-preview",
    stt_provider: "deepgram",
    stt_model: "nova-2",
    llm_provider: "openai",
    llm_model: "gpt-4o-mini",
    tts_provider: "openai",
    tts_model: "tts-1",
  });

  useEffect(() => {
    if (agent) {
      // Map API response to form data
      const voice = agent.voice || {};
      setFormData({
        name: agent.name || "",
        description: agent.description || "",
        instructions: agent.instructions || "",
        voice: voice.voice_id || "alloy",
        language: agent.language || "en-US",
        first_message: agent.first_message || "",
        temperature: agent.temperature ?? 0.8,
        mode: voice.mode || "realtime",
        realtime_provider: voice.realtime_provider || "openai",
        realtime_model: voice.realtime_model || "gpt-4o-realtime-preview",
        stt_provider: voice.stt_provider || "deepgram",
        stt_model: voice.stt_model || "nova-2",
        llm_provider: voice.llm_provider || "openai",
        llm_model: voice.llm_model || "gpt-4o-mini",
        tts_provider: voice.tts_provider || "openai",
        tts_model: voice.tts_model || "tts-1",
      });
    } else {
      // Reset to defaults
      setFormData({
        name: "",
        description: "",
        instructions: "You are a helpful voice assistant.",
        voice: "alloy",
        language: "en-US",
        first_message: "Hello! How can I help you today?",
        temperature: 0.8,
        mode: "realtime",
        realtime_provider: "openai",
        realtime_model: "gpt-4o-realtime-preview",
        stt_provider: "deepgram",
        stt_model: "nova-2",
        llm_provider: "openai",
        llm_model: "gpt-4o-mini",
        tts_provider: "openai",
        tts_model: "tts-1",
      });
    }
  }, [agent, open]);

  const handleSubmit = () => {
    if (!formData.name?.trim()) {
      toast.error("Agent name is required");
      return;
    }
    if (!formData.instructions?.trim()) {
      toast.error("Agent prompt is required");
      return;
    }

    // Transform back to API format
    const payload: Partial<Agent> = {
      name: formData.name,
      description: formData.description,
      instructions: formData.instructions,
      // Full voice configuration with mode and providers
      voice: {
        provider: formData.mode === "realtime" ? formData.realtime_provider : formData.tts_provider,
        voice_id: formData.voice,
        mode: formData.mode,
        // Realtime mode settings
        realtime_provider: formData.realtime_provider,
        realtime_model: formData.realtime_model,
        // Pipeline mode settings
        stt_provider: formData.stt_provider,
        stt_model: formData.stt_model,
        stt_language: formData.language.split("-")[0],
        llm_provider: formData.llm_provider,
        llm_model: formData.llm_model,
        tts_provider: formData.tts_provider,
        tts_model: formData.tts_model,
      },
      first_message: formData.first_message,
      temperature: formData.temperature,
    };

    onSave(payload);
  };

  const handlePreviewVoice = () => {
    toast.info("Voice preview is a mock feature");
  };

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent className="w-full sm:max-w-xl">
        <SheetHeader>
          <SheetTitle className="text-foreground">{agent ? "Edit Agent" : "Create Agent"}</SheetTitle>
          <SheetDescription>
            Configure your AI voice agent's personality and behavior
          </SheetDescription>
        </SheetHeader>

        <ScrollArea className="h-[calc(100vh-180px)] pr-4">
          <Tabs defaultValue="basics" className="mt-6">
            <TabsList className="grid w-full grid-cols-4 bg-muted">
              <TabsTrigger value="basics" className="data-[state=active]:bg-background">Basics</TabsTrigger>
              <TabsTrigger value="conversation" className="data-[state=active]:bg-background">Voice</TabsTrigger>
              <TabsTrigger value="models" className="data-[state=active]:bg-background">Models</TabsTrigger>
              <TabsTrigger value="advanced" className="data-[state=active]:bg-background">Settings</TabsTrigger>
            </TabsList>

            {/* Basics Tab */}
            <TabsContent value="basics" className="mt-6 space-y-6">
              <div className="space-y-2">
                <Label htmlFor="name" className="text-foreground">Agent Name *</Label>
                <Input
                  id="name"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  placeholder="e.g., Sales Assistant"
                  className="bg-background border-border text-foreground"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="instructions" className="text-foreground text-lg font-medium">
                  Agent Prompt / System Instructions *
                </Label>
                <p className="text-xs text-muted-foreground mb-2">
                  Define exactly how your agent should behave, what it knows, and its personality.
                </p>
                <Textarea
                  id="instructions"
                  value={formData.instructions}
                  onChange={(e) => setFormData({ ...formData, instructions: e.target.value })}
                  placeholder="You are a helpful customer support agent for..."
                  rows={10}
                  className="bg-background border-border text-foreground font-mono text-sm leading-relaxed"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="description" className="text-foreground">
                  Internal Description (Optional)
                </Label>
                <Input
                  id="description"
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  placeholder="Internal notes about this agent..."
                  className="bg-background border-border text-foreground"
                />
              </div>
            </TabsContent>

            {/* Conversation Tab */}
            <TabsContent value="conversation" className="mt-6 space-y-6">
              <div className="space-y-2">
                <Label htmlFor="first_message" className="text-foreground">First Message / Greeting</Label>
                <Textarea
                  id="first_message"
                  value={formData.first_message}
                  onChange={(e) => setFormData({ ...formData, first_message: e.target.value })}
                  placeholder="Hi! Thanks for calling. How can I help you today?"
                  rows={3}
                  className="bg-background border-border text-foreground"
                />
              </div>

              <div className="space-y-3">
                <Label className="text-foreground">Voice</Label>
                <div className="grid grid-cols-2 gap-3">
                  {voiceOptions.map((voice) => (
                    <button
                      key={voice.id}
                      type="button"
                      onClick={() => setFormData({ ...formData, voice: voice.id })}
                      className={`flex items-center justify-between rounded-lg border p-3 text-left transition-colors ${formData.voice === voice.id
                        ? "border-primary bg-primary/10"
                        : "border-border bg-muted/50 hover:bg-accent"
                        }`}
                    >
                      <div>
                        <p className="font-medium text-foreground">{voice.name}</p>
                        <p className="text-xs text-muted-foreground">{voice.gender}</p>
                      </div>
                      <Button
                        type="button"
                        variant="ghost"
                        size="icon"
                        className="h-8 w-8"
                        onClick={(e) => {
                          e.stopPropagation();
                          handlePreviewVoice();
                        }}
                      >
                        <Volume2 className="h-4 w-4" />
                      </Button>
                    </button>
                  ))}
                </div>
              </div>
            </TabsContent>

            {/* Models Tab */}
            <TabsContent value="models" className="mt-6 space-y-6">
              <div className="space-y-2">
                <Label className="text-foreground">Voice AI Mode</Label>
                <div className="grid grid-cols-2 gap-3">
                  {modeOptions.map((mode) => (
                    <button
                      key={mode.id}
                      type="button"
                      onClick={() => setFormData({ ...formData, mode: mode.id })}
                      className={`flex flex-col rounded-lg border p-3 text-left transition-colors ${formData.mode === mode.id
                        ? "border-primary bg-primary/10"
                        : "border-border bg-muted/50 hover:bg-accent"
                        }`}
                    >
                      <p className="font-medium text-foreground">{mode.name}</p>
                      <p className="text-xs text-muted-foreground">{mode.description}</p>
                    </button>
                  ))}
                </div>
              </div>

              {formData.mode === "realtime" ? (
                // Realtime Mode Settings
                <div className="space-y-4 rounded-lg border border-border p-4">
                  <p className="text-sm font-medium text-foreground">Realtime Provider</p>
                  <Select
                    value={formData.realtime_provider}
                    onValueChange={(value) => {
                      const provider = realtimeProviderOptions.find(p => p.id === value);
                      setFormData({
                        ...formData,
                        realtime_provider: value,
                        realtime_model: provider?.models[0] || "gpt-4o-realtime-preview"
                      });
                    }}
                  >
                    <SelectTrigger className="bg-background border-border text-foreground">
                      <SelectValue placeholder="Select provider" />
                    </SelectTrigger>
                    <SelectContent>
                      {realtimeProviderOptions.map((p) => (
                        <SelectItem key={p.id} value={p.id}>{p.name}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              ) : (
                // Pipeline Mode Settings
                <div className="space-y-4">
                  {/* STT Provider */}
                  <div className="rounded-lg border border-border p-4 space-y-3">
                    <p className="text-sm font-medium text-foreground">🎙️ Speech-to-Text (STT)</p>
                    <div className="grid grid-cols-2 gap-3">
                      <Select
                        value={formData.stt_provider}
                        onValueChange={(value) => {
                          const provider = sttProviderOptions.find(p => p.id === value);
                          setFormData({
                            ...formData,
                            stt_provider: value,
                            stt_model: provider?.models[0] || "nova-2"
                          });
                        }}
                      >
                        <SelectTrigger className="bg-background border-border text-foreground">
                          <SelectValue placeholder="Provider" />
                        </SelectTrigger>
                        <SelectContent>
                          {sttProviderOptions.map((p) => (
                            <SelectItem key={p.id} value={p.id}>{p.name}</SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                      <Select
                        value={formData.stt_model}
                        onValueChange={(value) => setFormData({ ...formData, stt_model: value })}
                      >
                        <SelectTrigger className="bg-background border-border text-foreground">
                          <SelectValue placeholder="Model" />
                        </SelectTrigger>
                        <SelectContent>
                          {sttProviderOptions.find(p => p.id === formData.stt_provider)?.models.map((m) => (
                            <SelectItem key={m} value={m}>{m}</SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                  </div>

                  {/* LLM Provider */}
                  <div className="rounded-lg border border-border p-4 space-y-3">
                    <p className="text-sm font-medium text-foreground">🧠 Large Language Model (LLM)</p>
                    <div className="grid grid-cols-2 gap-3">
                      <Select
                        value={formData.llm_provider}
                        onValueChange={(value) => {
                          const provider = llmProviderOptions.find(p => p.id === value);
                          setFormData({
                            ...formData,
                            llm_provider: value,
                            llm_model: provider?.models[0] || "gpt-4o-mini"
                          });
                        }}
                      >
                        <SelectTrigger className="bg-background border-border text-foreground">
                          <SelectValue placeholder="Provider" />
                        </SelectTrigger>
                        <SelectContent>
                          {llmProviderOptions.map((p) => (
                            <SelectItem key={p.id} value={p.id}>{p.name}</SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                      <Select
                        value={formData.llm_model}
                        onValueChange={(value) => setFormData({ ...formData, llm_model: value })}
                      >
                        <SelectTrigger className="bg-background border-border text-foreground">
                          <SelectValue placeholder="Model" />
                        </SelectTrigger>
                        <SelectContent>
                          {llmProviderOptions.find(p => p.id === formData.llm_provider)?.models.map((m) => (
                            <SelectItem key={m} value={m}>{m}</SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                  </div>

                  {/* TTS Provider */}
                  <div className="rounded-lg border border-border p-4 space-y-3">
                    <p className="text-sm font-medium text-foreground">🔊 Text-to-Speech (TTS)</p>
                    <div className="grid grid-cols-2 gap-3">
                      <Select
                        value={formData.tts_provider}
                        onValueChange={(value) => {
                          const provider = ttsProviderOptions.find(p => p.id === value);
                          setFormData({
                            ...formData,
                            tts_provider: value,
                            tts_model: provider?.models[0] || "tts-1"
                          });
                        }}
                      >
                        <SelectTrigger className="bg-background border-border text-foreground">
                          <SelectValue placeholder="Provider" />
                        </SelectTrigger>
                        <SelectContent>
                          {ttsProviderOptions.map((p) => (
                            <SelectItem key={p.id} value={p.id}>{p.name}</SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                      <Select
                        value={formData.tts_model}
                        onValueChange={(value) => setFormData({ ...formData, tts_model: value })}
                      >
                        <SelectTrigger className="bg-background border-border text-foreground">
                          <SelectValue placeholder="Model" />
                        </SelectTrigger>
                        <SelectContent>
                          {ttsProviderOptions.find(p => p.id === formData.tts_provider)?.models.map((m) => (
                            <SelectItem key={m} value={m}>{m}</SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                  </div>
                </div>
              )}
            </TabsContent>

            {/* Advanced Tab */}
            <TabsContent value="advanced" className="mt-6 space-y-6">

              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <Label className="text-foreground">Temperature: {formData.temperature}</Label>
                </div>
                <Slider
                  value={[formData.temperature]}
                  onValueChange={([value]) => setFormData({ ...formData, temperature: value })}
                  max={1}
                  min={0}
                  step={0.1}
                />
                <p className="text-xs text-muted-foreground">
                  Lower = more focused, Higher = more creative
                </p>
              </div>

              <div className="space-y-2">
                <Label htmlFor="language" className="text-foreground">Language</Label>
                <Select
                  value={formData.language}
                  onValueChange={(value) => setFormData({ ...formData, language: value })}
                >
                  <SelectTrigger className="bg-background border-border text-foreground">
                    <SelectValue placeholder="Select language" />
                  </SelectTrigger>
                  <SelectContent>
                    {languageOptions.map((lang) => (
                      <SelectItem key={lang.id} value={lang.id}>
                        {lang.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </TabsContent>
          </Tabs>
        </ScrollArea>

        <div className="mt-6 flex gap-3">
          <Button variant="outline" className="flex-1" onClick={() => onOpenChange(false)}>
            Cancel
          </Button>
          <Button className="flex-1" onClick={handleSubmit}>
            {agent ? "Save Changes" : "Create Agent"}
          </Button>
        </div>
      </SheetContent>
    </Sheet>
  );
}
