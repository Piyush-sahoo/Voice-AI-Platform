export interface Agent {
  id: string;
  name: string;
  description?: string;
  model: string;
  voice: string;
  language: string;
  status: "active" | "inactive" | "error";
  systemPrompt?: string;
  greeting?: string;
  temperature: number;
  maxTokens: number;
  interruptible: boolean;
  silenceTimeout: number;
  fallbackMessage?: string;
  createdAt: string;
  updatedAt: string;
}

export const voiceOptions = [
  { id: "alloy", name: "Alloy", gender: "Neutral", language: "English" },
  { id: "echo", name: "Echo", gender: "Male", language: "English" },
  { id: "fable", name: "Fable", gender: "Female", language: "English" },
  { id: "onyx", name: "Onyx", gender: "Male", language: "English" },
  { id: "nova", name: "Nova", gender: "Female", language: "English" },
  { id: "shimmer", name: "Shimmer", gender: "Female", language: "English" },
];

export const modelOptions = [
  { id: "gpt-4", name: "GPT-4", description: "Most capable model" },
  { id: "gpt-4-turbo", name: "GPT-4 Turbo", description: "Faster, cost-effective" },
  { id: "gpt-3.5-turbo", name: "GPT-3.5 Turbo", description: "Fast and affordable" },
  { id: "claude-3", name: "Claude 3", description: "Anthropic's latest" },
];

export const languageOptions = [
  { id: "en-US", name: "English (US)" },
  { id: "en-GB", name: "English (UK)" },
  { id: "es-ES", name: "Spanish" },
  { id: "fr-FR", name: "French" },
  { id: "de-DE", name: "German" },
  { id: "ja-JP", name: "Japanese" },
  { id: "zh-CN", name: "Chinese (Simplified)" },
];

// Voice AI Mode Options
export const modeOptions = [
  { id: "realtime", name: "Realtime (Speech-to-Speech)", description: "Lowest latency, OpenAI/Gemini" },
  { id: "pipeline", name: "Pipeline (STT→LLM→TTS)", description: "More flexible, mix providers" },
];

// STT Provider Options
export const sttProviderOptions = [
  { id: "deepgram", name: "Deepgram", models: ["nova-2", "nova-3", "enhanced"] },
  { id: "openai", name: "OpenAI", models: ["whisper-1", "gpt-4o-transcribe"] },
  { id: "assemblyai", name: "AssemblyAI", models: ["universal"] },
];

// LLM Provider Options
export const llmProviderOptions = [
  { id: "openai", name: "OpenAI", models: ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo"] },
  { id: "anthropic", name: "Anthropic", models: ["claude-3-5-sonnet", "claude-3-opus"] },
  { id: "google", name: "Google", models: ["gemini-1.5-pro", "gemini-1.5-flash"] },
  { id: "groq", name: "Groq", models: ["llama-3.1-70b", "mixtral-8x7b"] },
];

// TTS Provider Options
export const ttsProviderOptions = [
  { id: "openai", name: "OpenAI", models: ["tts-1", "tts-1-hd"] },
  { id: "elevenlabs", name: "ElevenLabs", models: ["eleven_turbo_v2_5", "eleven_multilingual_v2"] },
  { id: "cartesia", name: "Cartesia", models: ["sonic-3"] },
  { id: "deepgram", name: "Deepgram", models: ["aura-asteria-en"] },
];

// Realtime Provider Options
export const realtimeProviderOptions = [
  { id: "openai", name: "OpenAI Realtime", models: ["gpt-4o-realtime-preview"] },
  { id: "google", name: "Gemini Live", models: ["gemini-2.0-flash-live"] },
];

export const mockAgents: Agent[] = [
  {
    id: "agent-1",
    name: "Sales Assistant",
    description: "Handles inbound sales inquiries and qualifies leads",
    model: "gpt-4",
    voice: "nova",
    language: "en-US",
    status: "active",
    systemPrompt: "You are a helpful sales assistant for a SaaS company...",
    greeting: "Hi! Thanks for calling. How can I help you today?",
    temperature: 0.7,
    maxTokens: 150,
    interruptible: true,
    silenceTimeout: 5,
    fallbackMessage: "I apologize, I didn't quite catch that. Could you repeat?",
    createdAt: "2024-01-15T10:30:00Z",
    updatedAt: "2024-01-20T14:45:00Z",
  },
  {
    id: "agent-2",
    name: "Support Bot",
    description: "Provides technical support and troubleshooting",
    model: "gpt-4-turbo",
    voice: "alloy",
    language: "en-US",
    status: "active",
    systemPrompt: "You are a technical support specialist...",
    greeting: "Hello! I'm here to help with any technical issues.",
    temperature: 0.5,
    maxTokens: 200,
    interruptible: true,
    silenceTimeout: 7,
    fallbackMessage: "Let me connect you with a human agent.",
    createdAt: "2024-01-10T09:00:00Z",
    updatedAt: "2024-01-18T11:20:00Z",
  },
  {
    id: "agent-3",
    name: "Appointment Scheduler",
    description: "Books and manages appointments",
    model: "gpt-3.5-turbo",
    voice: "shimmer",
    language: "en-US",
    status: "inactive",
    systemPrompt: "You are an appointment scheduling assistant...",
    greeting: "Hi! I can help you schedule an appointment.",
    temperature: 0.3,
    maxTokens: 100,
    interruptible: false,
    silenceTimeout: 10,
    createdAt: "2024-01-05T16:00:00Z",
    updatedAt: "2024-01-12T08:30:00Z",
  },
];
