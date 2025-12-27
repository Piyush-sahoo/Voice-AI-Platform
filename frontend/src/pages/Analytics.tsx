import { useState } from "react";
import { DashboardLayout } from "@/components/layout/DashboardLayout";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  AreaChart,
  Area,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from "recharts";
import {
  Phone,
  Clock,
  DollarSign,
  TrendingUp,
  Download,
  Bot,
  MessageSquare,
  ThumbsUp,
  ThumbsDown,
  Minus,
} from "lucide-react";
import { mockAnalyticsData } from "@/data/mockAnalytics";
import { toast } from "sonner";

export default function Analytics() {
  const [timeRange, setTimeRange] = useState("7d");
  const data = mockAnalyticsData;

  const formatDuration = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, "0")}`;
  };

  const handleExport = (format: string) => {
    toast.success(`Exporting analytics as ${format.toUpperCase()}...`);
  };

  const metrics = [
    {
      title: "Total Calls",
      value: data.overview.totalCalls.toLocaleString(),
      change: "+12.5%",
      positive: true,
      icon: Phone,
    },
    {
      title: "Avg Duration",
      value: formatDuration(data.overview.avgDuration),
      change: "+8.2%",
      positive: true,
      icon: Clock,
    },
    {
      title: "Answer Rate",
      value: `${data.overview.answerRate}%`,
      change: "+2.1%",
      positive: true,
      icon: TrendingUp,
    },
    {
      title: "Avg Cost/Call",
      value: `$${data.overview.avgCostPerCall.toFixed(2)}`,
      change: "-5.3%",
      positive: true,
      icon: DollarSign,
    },
  ];

  return (
    <DashboardLayout>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h1 className="text-2xl font-semibold">Analytics</h1>
            <p className="text-sm text-muted-foreground">
              Track performance and gain insights from your calls
            </p>
          </div>
          <div className="flex items-center gap-3">
            <Select value={timeRange} onValueChange={setTimeRange}>
              <SelectTrigger className="w-[140px]">
                <SelectValue placeholder="Time range" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="24h">Last 24 hours</SelectItem>
                <SelectItem value="7d">Last 7 days</SelectItem>
                <SelectItem value="30d">Last 30 days</SelectItem>
                <SelectItem value="90d">Last 90 days</SelectItem>
              </SelectContent>
            </Select>
            <Button variant="outline" onClick={() => handleExport("csv")}>
              <Download className="mr-2 h-4 w-4" />
              Export
            </Button>
          </div>
        </div>

        {/* Metrics Cards */}
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {metrics.map((metric) => (
            <Card key={metric.title}>
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10">
                    <metric.icon className="h-5 w-5 text-primary" />
                  </div>
                  <Badge
                    variant="outline"
                    className={
                      metric.positive
                        ? "border-emerald-500/30 bg-emerald-500/10 text-emerald-400"
                        : "border-destructive/30 bg-destructive/10 text-destructive"
                    }
                  >
                    {metric.change}
                  </Badge>
                </div>
                <div className="mt-4">
                  <p className="text-2xl font-bold">{metric.value}</p>
                  <p className="text-sm text-muted-foreground">{metric.title}</p>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>

        {/* Charts Row 1 */}
        <div className="grid gap-6 lg:grid-cols-2">
          {/* Calls Over Time */}
          <Card>
            <CardHeader>
              <CardTitle>Calls Over Time</CardTitle>
              <CardDescription>Daily call volume and completion rate</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="h-[300px]">
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={data.callsOverTime}>
                    <defs>
                      <linearGradient id="colorCompleted" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="hsl(var(--primary))" stopOpacity={0.3} />
                        <stop offset="95%" stopColor="hsl(var(--primary))" stopOpacity={0} />
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                    <XAxis
                      dataKey="date"
                      stroke="hsl(var(--muted-foreground))"
                      fontSize={12}
                    />
                    <YAxis stroke="hsl(var(--muted-foreground))" fontSize={12} />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: "hsl(var(--card))",
                        border: "1px solid hsl(var(--border))",
                        borderRadius: "8px",
                      }}
                    />
                    <Area
                      type="monotone"
                      dataKey="completed"
                      stroke="hsl(var(--primary))"
                      fill="url(#colorCompleted)"
                      strokeWidth={2}
                    />
                    <Area
                      type="monotone"
                      dataKey="missed"
                      stroke="hsl(var(--destructive))"
                      fill="hsl(var(--destructive))"
                      fillOpacity={0.1}
                      strokeWidth={2}
                    />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            </CardContent>
          </Card>

          {/* Peak Hours */}
          <Card>
            <CardHeader>
              <CardTitle>Peak Call Times</CardTitle>
              <CardDescription>Call volume by hour of day</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="h-[300px]">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={data.peakHours}>
                    <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                    <XAxis
                      dataKey="hour"
                      stroke="hsl(var(--muted-foreground))"
                      fontSize={12}
                    />
                    <YAxis stroke="hsl(var(--muted-foreground))" fontSize={12} />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: "hsl(var(--card))",
                        border: "1px solid hsl(var(--border))",
                        borderRadius: "8px",
                      }}
                    />
                    <Bar
                      dataKey="calls"
                      fill="hsl(var(--primary))"
                      radius={[4, 4, 0, 0]}
                    />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Charts Row 2 */}
        <div className="grid gap-6 lg:grid-cols-3">
          {/* Sentiment Distribution */}
          <Card>
            <CardHeader>
              <CardTitle>Sentiment Analysis</CardTitle>
              <CardDescription>Call sentiment breakdown</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="h-[200px]">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={data.sentimentDistribution}
                      cx="50%"
                      cy="50%"
                      innerRadius={50}
                      outerRadius={80}
                      paddingAngle={4}
                      dataKey="count"
                    >
                      {data.sentimentDistribution.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.color} />
                      ))}
                    </Pie>
                    <Tooltip
                      contentStyle={{
                        backgroundColor: "hsl(var(--card))",
                        border: "1px solid hsl(var(--border))",
                        borderRadius: "8px",
                      }}
                    />
                  </PieChart>
                </ResponsiveContainer>
              </div>
              <div className="mt-4 flex justify-center gap-4">
                {data.sentimentDistribution.map((item) => (
                  <div key={item.sentiment} className="flex items-center gap-2">
                    <div
                      className="h-3 w-3 rounded-full"
                      style={{ backgroundColor: item.color }}
                    />
                    <span className="text-sm text-muted-foreground">
                      {item.sentiment}
                    </span>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Agent Performance */}
          <Card className="lg:col-span-2">
            <CardHeader>
              <CardTitle>Agent Performance</CardTitle>
              <CardDescription>Performance metrics by agent</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-6">
                {data.agentPerformance.map((agent) => (
                  <div key={agent.agentId} className="space-y-3">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-primary/10">
                          <Bot className="h-4 w-4 text-primary" />
                        </div>
                        <div>
                          <p className="font-medium">{agent.agentName}</p>
                          <p className="text-sm text-muted-foreground">
                            {agent.calls} calls · {formatDuration(agent.avgDuration)} avg
                          </p>
                        </div>
                      </div>
                      <div className="flex items-center gap-4 text-sm">
                        <div className="text-right">
                          <p className="font-medium text-emerald-400">
                            {agent.successRate}%
                          </p>
                          <p className="text-xs text-muted-foreground">Success</p>
                        </div>
                        <div className="text-right">
                          <p className="font-medium">{agent.sentiment}%</p>
                          <p className="text-xs text-muted-foreground">Sentiment</p>
                        </div>
                      </div>
                    </div>
                    <Progress value={agent.successRate} className="h-2" />
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Conversation Insights */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <MessageSquare className="h-5 w-5" />
              Conversation Insights
            </CardTitle>
            <CardDescription>Top intents and conversation patterns</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid gap-6 md:grid-cols-2">
              {/* Top Intents */}
              <div className="space-y-4">
                <h4 className="font-medium">Top Intents</h4>
                <div className="space-y-3">
                  {data.topIntents.map((intent) => (
                    <div key={intent.intent} className="space-y-1">
                      <div className="flex items-center justify-between text-sm">
                        <span>{intent.intent}</span>
                        <span className="text-muted-foreground">
                          {intent.count} ({intent.percentage}%)
                        </span>
                      </div>
                      <Progress value={intent.percentage} className="h-1.5" />
                    </div>
                  ))}
                </div>
              </div>

              {/* Quick Stats */}
              <div className="space-y-4">
                <h4 className="font-medium">Quick Stats</h4>
                <div className="grid grid-cols-2 gap-4">
                  <div className="rounded-lg border border-border bg-muted/50 p-4">
                    <div className="flex items-center gap-2">
                      <ThumbsUp className="h-4 w-4 text-emerald-400" />
                      <span className="text-sm text-muted-foreground">Positive</span>
                    </div>
                    <p className="mt-2 text-2xl font-bold">55%</p>
                  </div>
                  <div className="rounded-lg border border-border bg-muted/50 p-4">
                    <div className="flex items-center gap-2">
                      <Minus className="h-4 w-4 text-amber-400" />
                      <span className="text-sm text-muted-foreground">Neutral</span>
                    </div>
                    <p className="mt-2 text-2xl font-bold">33%</p>
                  </div>
                  <div className="rounded-lg border border-border bg-muted/50 p-4">
                    <div className="flex items-center gap-2">
                      <ThumbsDown className="h-4 w-4 text-destructive" />
                      <span className="text-sm text-muted-foreground">Negative</span>
                    </div>
                    <p className="mt-2 text-2xl font-bold">12%</p>
                  </div>
                  <div className="rounded-lg border border-border bg-muted/50 p-4">
                    <div className="flex items-center gap-2">
                      <TrendingUp className="h-4 w-4 text-primary" />
                      <span className="text-sm text-muted-foreground">Escalation</span>
                    </div>
                    <p className="mt-2 text-2xl font-bold">8%</p>
                  </div>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </DashboardLayout>
  );
}
