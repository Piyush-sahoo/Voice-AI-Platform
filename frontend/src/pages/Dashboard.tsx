import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { Bot, Phone, History, BarChart3, Plus, ArrowUpRight, Users, Loader2 } from "lucide-react";
import { Link } from "react-router-dom";
import { DashboardLayout } from "@/components/layout/DashboardLayout";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useAuth } from "@/contexts/AuthContext";
import { assistantsApi, callsApi, campaignsApi } from "@/lib/api";
import { format } from "date-fns";

interface DashboardStats {
  activeAgents: number;
  totalCalls: number;
  activeCampaigns: number;
  successRate: number;
}

interface RecentCall {
  call_id: string;
  phone_number: string;
  status: string;
  duration_seconds: number;
  created_at: string;
}

export default function Dashboard() {
  const { user } = useAuth();
  const [stats, setStats] = useState<DashboardStats>({
    activeAgents: 0,
    totalCalls: 0,
    activeCampaigns: 0,
    successRate: 0,
  });
  const [recentCalls, setRecentCalls] = useState<RecentCall[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const fetchDashboardData = async () => {
      setIsLoading(true);
      try {
        const [assistantsData, callsData, campaignsData] = await Promise.all([
          assistantsApi.list().catch(() => ({ assistants: [], count: 0 })),
          callsApi.list().catch(() => ({ calls: [], count: 0 })),
          campaignsApi.list().catch(() => ({ campaigns: [], count: 0 })),
        ]);

        const calls = callsData.calls as RecentCall[];
        const completedCalls = calls.filter((c) => c.status === "completed" || c.status === "answered").length;
        const successRate = calls.length > 0 ? Math.round((completedCalls / calls.length) * 100) : 0;
        const runningCampaigns = (campaignsData.campaigns as any[]).filter((c) => c.status === "running").length;

        setStats({
          activeAgents: (assistantsData.assistants as any[]).filter((a) => a.is_active).length,
          totalCalls: callsData.count,
          activeCampaigns: runningCampaigns,
          successRate,
        });

        setRecentCalls(calls.slice(0, 5));
      } catch (error) {
        console.error("Failed to fetch dashboard data:", error);
      } finally {
        setIsLoading(false);
      }
    };

    fetchDashboardData();
  }, []);

  const statCards = [
    { name: "Active Agents", value: stats.activeAgents.toString(), icon: Bot, href: "/agents" },
    { name: "Active Campaigns", value: stats.activeCampaigns.toString(), icon: Users, href: "/campaigns" },
    { name: "Total Calls", value: stats.totalCalls.toLocaleString(), icon: History, href: "/calls" },
    { name: "Success Rate", value: `${stats.successRate}%`, icon: BarChart3, href: "/analytics" },
  ];

  const formatDuration = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, "0")}`;
  };

  const getTimeAgo = (dateStr: string) => {
    const date = new Date(dateStr);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);

    if (diffMins < 1) return "just now";
    if (diffMins < 60) return `${diffMins} min ago`;
    const diffHours = Math.floor(diffMins / 60);
    if (diffHours < 24) return `${diffHours} hour${diffHours > 1 ? "s" : ""} ago`;
    return format(date, "MMM d");
  };

  return (
    <DashboardLayout>
      <div className="p-6 lg:p-8">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-8"
        >
          <h1 className="text-2xl font-bold text-foreground lg:text-3xl">
            Welcome back, {user?.name || "User"}
          </h1>
          <p className="mt-1 text-muted-foreground">
            Here's what's happening with your voice agents today.
          </p>
        </motion.div>

        {/* Stats Grid */}
        <div className="mb-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {statCards.map((stat, index) => (
            <motion.div
              key={stat.name}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.1 }}
            >
              <Link to={stat.href}>
                <Card className="group cursor-pointer transition-colors hover:bg-accent/50">
                  <CardHeader className="flex flex-row items-center justify-between pb-2">
                    <CardTitle className="text-sm font-medium text-muted-foreground">
                      {stat.name}
                    </CardTitle>
                    <stat.icon className="h-5 w-5 text-muted-foreground" />
                  </CardHeader>
                  <CardContent>
                    <div className="flex items-center justify-between">
                      {isLoading ? (
                        <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
                      ) : (
                        <span className="text-2xl font-bold text-foreground">{stat.value}</span>
                      )}
                      <ArrowUpRight className="h-4 w-4 text-muted-foreground opacity-0 transition-opacity group-hover:opacity-100" />
                    </div>
                  </CardContent>
                </Card>
              </Link>
            </motion.div>
          ))}
        </div>

        {/* Quick Actions & Recent Calls */}
        <div className="grid gap-6 lg:grid-cols-2">
          {/* Quick Actions */}
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.4 }}
          >
            <Card>
              <CardHeader>
                <CardTitle>Quick Actions</CardTitle>
              </CardHeader>
              <CardContent className="grid gap-3">
                <Button asChild className="w-full justify-start">
                  <Link to="/agents">
                    <Plus className="mr-2 h-4 w-4" />
                    Create New Agent
                  </Link>
                </Button>
                <Button asChild variant="outline" className="w-full justify-start">
                  <Link to="/campaigns">
                    <Users className="mr-2 h-4 w-4" />
                    Create Campaign
                  </Link>
                </Button>
                <Button asChild variant="outline" className="w-full justify-start">
                  <Link to="/phone-numbers">
                    <Phone className="mr-2 h-4 w-4" />
                    Add Phone Number
                  </Link>
                </Button>
              </CardContent>
            </Card>
          </motion.div>

          {/* Recent Calls */}
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.5 }}
          >
            <Card>
              <CardHeader className="flex flex-row items-center justify-between">
                <CardTitle>Recent Calls</CardTitle>
                <Button asChild variant="ghost" size="sm">
                  <Link to="/calls">View all</Link>
                </Button>
              </CardHeader>
              <CardContent>
                {isLoading ? (
                  <div className="flex h-32 items-center justify-center">
                    <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
                  </div>
                ) : recentCalls.length === 0 ? (
                  <div className="flex h-32 flex-col items-center justify-center text-center">
                    <Phone className="h-8 w-8 text-muted-foreground mb-2" />
                    <p className="text-muted-foreground">No calls yet</p>
                    <p className="text-sm text-muted-foreground">Create a campaign to start calling</p>
                  </div>
                ) : (
                  <div className="space-y-4">
                    {recentCalls.map((call) => (
                      <div
                        key={call.call_id}
                        className="flex items-center justify-between rounded-lg border border-border p-3"
                      >
                        <div>
                          <p className="font-medium text-foreground">{call.phone_number}</p>
                          <p className="text-sm text-muted-foreground">
                            {formatDuration(call.duration_seconds)}
                          </p>
                        </div>
                        <div className="text-right">
                          <span
                            className={`inline-block rounded-full px-2 py-1 text-xs font-medium ${call.status === "completed" || call.status === "answered"
                                ? "bg-emerald-500/10 text-emerald-400"
                                : "bg-amber-500/10 text-amber-400"
                              }`}
                          >
                            {call.status}
                          </span>
                          <p className="mt-1 text-xs text-muted-foreground">
                            {getTimeAgo(call.created_at)}
                          </p>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </motion.div>
        </div>
      </div>
    </DashboardLayout>
  );
}
