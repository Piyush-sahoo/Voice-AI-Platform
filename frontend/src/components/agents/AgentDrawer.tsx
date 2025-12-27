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
import { voiceOptions, modelOptions, languageOptions } from "@/data/mockAgents";
import { Volume2, Loader2 } from "lucide-react";
import { toast } from "sonner";

// Compatible with backend Assistant model
interface Agent {
  assistant_id?: string;
  name: string;
  description?: string;
  instructions: string; // The "Prompt"
  model_provider?: string;
  model_name?: string; // e.g. gpt-4
  voice?: { provider: string; voice_id: string }; // We'll simplify this for UI state
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
  model: string;
  voice: string;
  language: string;
  first_message: string;
  temperature: number;
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
    model: "gpt-4o",
    voice: "alloy",
    language: "en-US",
    first_message: "",
    temperature: 0.8,
  });

  useEffect(() => {
    if (agent) {
      // Map API response to form data
      setFormData({
        name: agent.name || "",
        description: agent.description || "",
        instructions: agent.instructions || "",
        model: agent.model_name || "gpt-4o",
        voice: agent.voice?.voice_id || "alloy",
        language: agent.language || "en-US",
        first_message: agent.first_message || "",
        temperature: agent.temperature ?? 0.8,
      });
    } else {
      // Reset to defaults
      setFormData({
        name: "",
        description: "",
        instructions: "You are a helpful voice assistant.", // Default prompt
        model: "gpt-4o",
        voice: "alloy",
        language: "en-US",
        first_message: "Hello! How can I help you today?",
        temperature: 0.8,
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
      model_name: formData.model,
      // For now we assume verify voice provider is openai for simplicity or derive it
      voice: { provider: "openai", voice_id: formData.voice },
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
            <TabsList className="grid w-full grid-cols-3 bg-muted">
              <TabsTrigger value="basics" className="data-[state=active]:bg-background">Basics</TabsTrigger>
              <TabsTrigger value="conversation" className="data-[state=active]:bg-background">Conversation</TabsTrigger>
              <TabsTrigger value="advanced" className="data-[state=active]:bg-background">Advanced</TabsTrigger>
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

            {/* Advanced Tab */}
            <TabsContent value="advanced" className="mt-6 space-y-6">
              <div className="space-y-2">
                <Label htmlFor="model" className="text-foreground">Model</Label>
                <Select
                  value={formData.model}
                  onValueChange={(value) => setFormData({ ...formData, model: value })}
                >
                  <SelectTrigger className="bg-background border-border text-foreground">
                    <SelectValue placeholder="Select model" />
                  </SelectTrigger>
                  <SelectContent>
                    {modelOptions.map((model) => (
                      <SelectItem key={model.id} value={model.id}>
                        <div className="flex flex-col">
                          <span>{model.name}</span>
                          <span className="text-xs text-muted-foreground">
                            {model.description}
                          </span>
                        </div>
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

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
