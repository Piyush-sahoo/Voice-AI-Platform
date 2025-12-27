export interface AnalyticsData {
  overview: {
    totalCalls: number;
    completedCalls: number;
    avgDuration: number;
    totalCost: number;
    answerRate: number;
    avgCostPerCall: number;
  };
  callsOverTime: { date: string; calls: number; completed: number; missed: number }[];
  callsByStatus: { status: string; count: number; color: string }[];
  agentPerformance: {
    agentId: string;
    agentName: string;
    calls: number;
    avgDuration: number;
    successRate: number;
    sentiment: number;
  }[];
  peakHours: { hour: string; calls: number }[];
  sentimentDistribution: { sentiment: string; count: number; color: string }[];
  topIntents: { intent: string; count: number; percentage: number }[];
}

export const mockAnalyticsData: AnalyticsData = {
  overview: {
    totalCalls: 1247,
    completedCalls: 1089,
    avgDuration: 185,
    totalCost: 156.32,
    answerRate: 87.3,
    avgCostPerCall: 0.13,
  },
  callsOverTime: [
    { date: "Jan 14", calls: 45, completed: 40, missed: 5 },
    { date: "Jan 15", calls: 52, completed: 48, missed: 4 },
    { date: "Jan 16", calls: 38, completed: 35, missed: 3 },
    { date: "Jan 17", calls: 65, completed: 58, missed: 7 },
    { date: "Jan 18", calls: 71, completed: 64, missed: 7 },
    { date: "Jan 19", calls: 48, completed: 42, missed: 6 },
    { date: "Jan 20", calls: 82, completed: 75, missed: 7 },
  ],
  callsByStatus: [
    { status: "Completed", count: 1089, color: "hsl(var(--chart-1))" },
    { status: "Missed", count: 98, color: "hsl(var(--chart-2))" },
    { status: "Failed", count: 42, color: "hsl(var(--chart-3))" },
    { status: "In Progress", count: 18, color: "hsl(var(--chart-4))" },
  ],
  agentPerformance: [
    {
      agentId: "agent-1",
      agentName: "Sales Assistant",
      calls: 523,
      avgDuration: 210,
      successRate: 92,
      sentiment: 78,
    },
    {
      agentId: "agent-2",
      agentName: "Support Bot",
      calls: 412,
      avgDuration: 180,
      successRate: 88,
      sentiment: 65,
    },
    {
      agentId: "agent-3",
      agentName: "Appointment Scheduler",
      calls: 312,
      avgDuration: 95,
      successRate: 94,
      sentiment: 82,
    },
  ],
  peakHours: [
    { hour: "8 AM", calls: 45 },
    { hour: "9 AM", calls: 78 },
    { hour: "10 AM", calls: 112 },
    { hour: "11 AM", calls: 134 },
    { hour: "12 PM", calls: 89 },
    { hour: "1 PM", calls: 76 },
    { hour: "2 PM", calls: 98 },
    { hour: "3 PM", calls: 121 },
    { hour: "4 PM", calls: 145 },
    { hour: "5 PM", calls: 132 },
    { hour: "6 PM", calls: 67 },
  ],
  sentimentDistribution: [
    { sentiment: "Positive", count: 687, color: "hsl(142, 76%, 36%)" },
    { sentiment: "Neutral", count: 412, color: "hsl(48, 96%, 53%)" },
    { sentiment: "Negative", count: 148, color: "hsl(0, 84%, 60%)" },
  ],
  topIntents: [
    { intent: "Pricing Inquiry", count: 312, percentage: 25 },
    { intent: "Technical Support", count: 256, percentage: 21 },
    { intent: "Schedule Appointment", count: 198, percentage: 16 },
    { intent: "Product Information", count: 167, percentage: 13 },
    { intent: "Account Issues", count: 134, percentage: 11 },
    { intent: "Billing Questions", count: 98, percentage: 8 },
    { intent: "Other", count: 82, percentage: 6 },
  ],
};
