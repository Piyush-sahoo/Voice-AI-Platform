export interface CallRecord {
  id: string;
  fromNumber: string;
  toNumber: string;
  direction: "inbound" | "outbound";
  agentId: string;
  agentName: string;
  duration: number; // in seconds
  cost: number;
  status: "completed" | "missed" | "failed" | "in-progress";
  sentiment: "positive" | "neutral" | "negative";
  recordingUrl?: string;
  transcript?: TranscriptEntry[];
  summary?: string;
  createdAt: string;
}

export interface TranscriptEntry {
  speaker: "agent" | "caller";
  text: string;
  timestamp: number; // seconds from start
}

export const mockCalls: CallRecord[] = [
  {
    id: "call-1",
    fromNumber: "+1 (555) 987-6543",
    toNumber: "+1 (555) 123-4567",
    direction: "inbound",
    agentId: "agent-1",
    agentName: "Sales Assistant",
    duration: 245,
    cost: 0.12,
    status: "completed",
    sentiment: "positive",
    recordingUrl: "/mock-recording.wav",
    transcript: [
      { speaker: "agent", text: "Hi! Thanks for calling. How can I help you today?", timestamp: 0 },
      { speaker: "caller", text: "Hi, I'm interested in learning more about your pricing plans.", timestamp: 4 },
      { speaker: "agent", text: "Of course! We have three main plans: Starter at $29/month, Pro at $79/month, and Enterprise with custom pricing. Which one would you like to know more about?", timestamp: 8 },
      { speaker: "caller", text: "The Pro plan sounds interesting. What's included?", timestamp: 18 },
      { speaker: "agent", text: "The Pro plan includes unlimited calls, 10 AI agents, advanced analytics, priority support, and API access. It's our most popular option for growing businesses.", timestamp: 22 },
      { speaker: "caller", text: "That sounds great. Can I start a free trial?", timestamp: 35 },
      { speaker: "agent", text: "Absolutely! I can set that up for you right now. You'll get 14 days free with full access to all Pro features. What email should I use?", timestamp: 40 },
    ],
    summary: "Customer inquired about pricing plans, showed interest in Pro plan, and signed up for a 14-day free trial.",
    createdAt: "2024-01-20T14:30:00Z",
  },
  {
    id: "call-2",
    fromNumber: "+1 (555) 123-4567",
    toNumber: "+1 (555) 234-5678",
    direction: "outbound",
    agentId: "agent-2",
    agentName: "Support Bot",
    duration: 180,
    cost: 0.09,
    status: "completed",
    sentiment: "neutral",
    recordingUrl: "/mock-recording.wav",
    transcript: [
      { speaker: "agent", text: "Hello, this is the support team following up on your recent ticket.", timestamp: 0 },
      { speaker: "caller", text: "Oh yes, about the login issue?", timestamp: 5 },
      { speaker: "agent", text: "Exactly. I wanted to confirm that your password reset worked correctly.", timestamp: 8 },
      { speaker: "caller", text: "Yes, everything is working now. Thank you!", timestamp: 14 },
    ],
    summary: "Follow-up call regarding login issue. Customer confirmed the password reset resolved their problem.",
    createdAt: "2024-01-20T11:15:00Z",
  },
  {
    id: "call-3",
    fromNumber: "+1 (555) 345-6789",
    toNumber: "+1 (555) 123-4567",
    direction: "inbound",
    agentId: "agent-1",
    agentName: "Sales Assistant",
    duration: 0,
    cost: 0,
    status: "missed",
    sentiment: "neutral",
    createdAt: "2024-01-20T09:45:00Z",
  },
  {
    id: "call-4",
    fromNumber: "+1 (555) 456-7890",
    toNumber: "+1 (800) 555-0199",
    direction: "inbound",
    agentId: "agent-2",
    agentName: "Support Bot",
    duration: 320,
    cost: 0.16,
    status: "completed",
    sentiment: "negative",
    recordingUrl: "/mock-recording.wav",
    transcript: [
      { speaker: "agent", text: "Hello! I'm here to help with any technical issues.", timestamp: 0 },
      { speaker: "caller", text: "I've been trying to integrate your API for hours and nothing works!", timestamp: 4 },
      { speaker: "agent", text: "I'm sorry to hear you're having trouble. Let me help you troubleshoot. What error message are you seeing?", timestamp: 10 },
      { speaker: "caller", text: "It says 'Invalid API key' but I copied it exactly.", timestamp: 18 },
      { speaker: "agent", text: "That usually happens when there's a trailing space. Can you try regenerating the key from your dashboard?", timestamp: 24 },
    ],
    summary: "Customer frustrated with API integration. Issue was an invalid API key - advised to regenerate. Escalated to human support for follow-up.",
    createdAt: "2024-01-19T16:20:00Z",
  },
  {
    id: "call-5",
    fromNumber: "+1 (555) 567-8901",
    toNumber: "+1 (555) 123-4567",
    direction: "inbound",
    agentId: "agent-3",
    agentName: "Appointment Scheduler",
    duration: 95,
    cost: 0.05,
    status: "completed",
    sentiment: "positive",
    recordingUrl: "/mock-recording.wav",
    transcript: [
      { speaker: "agent", text: "Hi! I can help you schedule an appointment. When works best for you?", timestamp: 0 },
      { speaker: "caller", text: "Do you have anything available next Tuesday afternoon?", timestamp: 5 },
      { speaker: "agent", text: "Let me check... Yes! I have 2 PM, 3 PM, and 4:30 PM available.", timestamp: 10 },
      { speaker: "caller", text: "3 PM works perfectly.", timestamp: 16 },
      { speaker: "agent", text: "Great! I've booked you for Tuesday at 3 PM. You'll receive a confirmation email shortly.", timestamp: 19 },
    ],
    summary: "Successfully scheduled appointment for Tuesday at 3 PM. Confirmation email sent.",
    createdAt: "2024-01-19T10:05:00Z",
  },
  {
    id: "call-6",
    fromNumber: "+1 (555) 123-4567",
    toNumber: "+1 (555) 678-9012",
    direction: "outbound",
    agentId: "agent-1",
    agentName: "Sales Assistant",
    duration: 0,
    cost: 0,
    status: "failed",
    sentiment: "neutral",
    createdAt: "2024-01-18T14:30:00Z",
  },
];

export function formatDuration(seconds: number): string {
  if (seconds === 0) return "—";
  const mins = Math.floor(seconds / 60);
  const secs = seconds % 60;
  return `${mins}:${secs.toString().padStart(2, "0")}`;
}

export function formatPhoneNumber(number: string): string {
  return number;
}
