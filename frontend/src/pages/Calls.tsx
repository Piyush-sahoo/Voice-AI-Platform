import { useState, useEffect } from "react";
import { DashboardLayout } from "@/components/layout/DashboardLayout";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Search,
  PhoneOutgoing,
  Phone,
  Filter,
  Bot,
  ArrowRight,
  Loader2,
} from "lucide-react";
import { CallDetailSheet } from "@/components/calls/CallDetailSheet";
import { format } from "date-fns";
import { toast } from "sonner";
import { callsApi } from "@/lib/api";

interface Call {
  call_id: string;
  phone_number: string;
  from_number: string | null;
  status: string;
  duration_seconds: number;
  created_at: string;
  started_at: string | null;
  ended_at: string | null;
  transcript: Array<{ role: string; content: string }>;
  recording_url: string | null;
  analysis: { sentiment: string; summary: string } | null;
  assistant_id: string | null;
}

function formatDuration(seconds: number): string {
  const mins = Math.floor(seconds / 60);
  const secs = seconds % 60;
  return `${mins}:${secs.toString().padStart(2, '0')}`;
}

export default function Calls() {
  const [calls, setCalls] = useState<Call[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState<string>("all");
  const [selectedCall, setSelectedCall] = useState<Call | null>(null);
  const [detailSheetOpen, setDetailSheetOpen] = useState(false);

  const fetchCalls = async () => {
    setIsLoading(true);
    try {
      const data = await callsApi.list();
      setCalls(data.calls as Call[]);
    } catch (error) {
      toast.error("Failed to load calls");
      console.error(error);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchCalls();
  }, []);

  const filteredCalls = calls.filter((call) => {
    const searchMatch =
      (call.phone_number || "").toLowerCase().includes(searchQuery.toLowerCase()) ||
      (call.from_number?.toLowerCase().includes(searchQuery.toLowerCase()) ?? false);
    const statusMatch = statusFilter === "all" || call.status === statusFilter;
    return searchMatch && statusMatch;
  });

  const getStatusColor = (status: string) => {
    switch (status) {
      case "completed":
        return "bg-emerald-500/20 text-emerald-400 border-emerald-500/30";
      case "answered":
        return "bg-blue-500/20 text-blue-400 border-blue-500/30";
      case "failed":
        return "bg-destructive/20 text-destructive border-destructive/30";
      case "no_answer":
        return "bg-amber-500/20 text-amber-400 border-amber-500/30";
      case "initiated":
      case "ringing":
        return "bg-purple-500/20 text-purple-400 border-purple-500/30";
      default:
        return "bg-muted text-muted-foreground border-border";
    }
  };

  const getSentimentIndicator = (sentiment?: string) => {
    switch (sentiment) {
      case "positive":
        return "🟢";
      case "neutral":
        return "🟡";
      case "negative":
        return "🔴";
      default:
        return "⚪";
    }
  };

  const clearFilters = () => {
    setStatusFilter("all");
  };

  const hasActiveFilters = statusFilter !== "all";

  return (
    <DashboardLayout>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h1 className="text-2xl font-semibold text-foreground">Call History</h1>
            <p className="text-sm text-muted-foreground">
              View and analyze all your conversations
            </p>
          </div>
          <Button onClick={fetchCalls} variant="outline">
            Refresh
          </Button>
        </div>

        {/* Filters */}
        <div className="flex flex-wrap items-center gap-3">
          <div className="relative flex-1 min-w-[200px] max-w-sm">
            <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
            <Input
              placeholder="Search by phone number..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-10"
            />
          </div>

          <Select value={statusFilter} onValueChange={setStatusFilter}>
            <SelectTrigger className="w-[140px]">
              <SelectValue placeholder="Status" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Status</SelectItem>
              <SelectItem value="completed">Completed</SelectItem>
              <SelectItem value="answered">Answered</SelectItem>
              <SelectItem value="failed">Failed</SelectItem>
              <SelectItem value="no_answer">No Answer</SelectItem>
              <SelectItem value="initiated">Initiated</SelectItem>
            </SelectContent>
          </Select>

          {hasActiveFilters && (
            <Button variant="ghost" size="sm" onClick={clearFilters}>
              <Filter className="mr-2 h-4 w-4" />
              Clear filters
            </Button>
          )}
        </div>

        {/* Calls Table */}
        <div className="rounded-lg border border-border bg-card">
          <Table>
            <TableHeader>
              <TableRow className="hover:bg-transparent border-border">
                <TableHead className="text-muted-foreground">Time</TableHead>
                <TableHead className="text-muted-foreground">Phone Number</TableHead>
                <TableHead className="text-muted-foreground">Duration</TableHead>
                <TableHead className="text-muted-foreground">Sentiment</TableHead>
                <TableHead className="text-muted-foreground">Status</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {isLoading ? (
                <TableRow>
                  <TableCell colSpan={5} className="h-32 text-center">
                    <div className="flex flex-col items-center gap-2">
                      <Loader2 className="h-8 w-8 text-muted-foreground animate-spin" />
                      <p className="text-muted-foreground">Loading calls...</p>
                    </div>
                  </TableCell>
                </TableRow>
              ) : filteredCalls.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={5} className="h-32 text-center">
                    <div className="flex flex-col items-center gap-2">
                      <Phone className="h-8 w-8 text-muted-foreground" />
                      <p className="text-muted-foreground">No calls found</p>
                    </div>
                  </TableCell>
                </TableRow>
              ) : (
                filteredCalls.map((call) => (
                  <TableRow
                    key={call.call_id}
                    className="cursor-pointer border-border"
                    onClick={() => {
                      setSelectedCall(call);
                      setDetailSheetOpen(true);
                    }}
                  >
                    <TableCell>
                      <div className="flex items-center gap-2">
                        <PhoneOutgoing className="h-4 w-4 text-blue-400" />
                        <div>
                          <p className="text-sm text-foreground">
                            {format(new Date(call.created_at), "MMM d, h:mm a")}
                          </p>
                        </div>
                      </div>
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center gap-2 font-mono text-sm text-foreground">
                        <span className="max-w-[150px] truncate">{call.phone_number}</span>
                      </div>
                    </TableCell>
                    <TableCell className="text-muted-foreground">
                      {formatDuration(call.duration_seconds)}
                    </TableCell>
                    <TableCell>
                      <span title={call.analysis?.sentiment || "unknown"}>
                        {getSentimentIndicator(call.analysis?.sentiment)}
                      </span>
                    </TableCell>
                    <TableCell>
                      <Badge variant="outline" className={getStatusColor(call.status)}>
                        {call.status}
                      </Badge>
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </div>

        {/* Stats Summary */}
        <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
          <div className="rounded-lg border border-border bg-card p-4">
            <p className="text-sm text-muted-foreground">Total Calls</p>
            <p className="text-2xl font-semibold text-foreground">{filteredCalls.length}</p>
          </div>
          <div className="rounded-lg border border-border bg-card p-4">
            <p className="text-sm text-muted-foreground">Completed</p>
            <p className="text-2xl font-semibold text-emerald-400">
              {filteredCalls.filter((c) => c.status === "completed").length}
            </p>
          </div>
          <div className="rounded-lg border border-border bg-card p-4">
            <p className="text-sm text-muted-foreground">Answered</p>
            <p className="text-2xl font-semibold text-blue-400">
              {filteredCalls.filter((c) => c.status === "answered").length}
            </p>
          </div>
          <div className="rounded-lg border border-border bg-card p-4">
            <p className="text-sm text-muted-foreground">Total Duration</p>
            <p className="text-2xl font-semibold text-foreground">
              {formatDuration(filteredCalls.reduce((acc, c) => acc + c.duration_seconds, 0))}
            </p>
          </div>
        </div>
      </div>

      <CallDetailSheet
        open={detailSheetOpen}
        onOpenChange={setDetailSheetOpen}
        call={selectedCall as any}
      />
    </DashboardLayout>
  );
}
