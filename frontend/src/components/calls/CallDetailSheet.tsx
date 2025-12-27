import { useState, useRef, useEffect } from "react";
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Slider } from "@/components/ui/slider";
import {
  Phone,
  PhoneIncoming,
  PhoneOutgoing,
  Play,
  Pause,
  Download,
  Bot,
  User,
  Clock,
  DollarSign,
  FileText,
} from "lucide-react";

// Match the API response structure
interface Call {
  call_id: string;
  phone_number: string;
  from_number: string | null;
  status: string;
  duration_seconds: number;
  created_at: string;
  started_at: string | null;
  ended_at: string | null;
  transcript: string | Array<{ role: string; content: string }> | null;
  recording_url: string | null;
  analysis: { sentiment: string; summary: string } | null;
  assistant_id: string | null;
  cost?: number; // Optional in case not populated
  direction?: string; // Optional, might be inferred
}

interface CallDetailSheetProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  call: Call | null;
}

export function CallDetailSheet({ open, onOpenChange, call }: CallDetailSheetProps) {
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const intervalRef = useRef<NodeJS.Timeout | null>(null);
  const audioRef = useRef<HTMLAudioElement | null>(null);

  useEffect(() => {
    if (!open) {
      setIsPlaying(false);
      setCurrentTime(0);
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
      if (audioRef.current) {
        audioRef.current.pause();
        audioRef.current.currentTime = 0;
      }
    }
  }, [open]);

  useEffect(() => {
    // Only try to play http/https URLs natively
    if (call?.recording_url && call.recording_url.startsWith('http') && !audioRef.current) {
      audioRef.current = new Audio(call.recording_url);
      audioRef.current.addEventListener('ended', () => setIsPlaying(false));
      audioRef.current.addEventListener('timeupdate', () => {
        if (audioRef.current) setCurrentTime(audioRef.current.currentTime);
      });
    }
  }, [call]);

  useEffect(() => {
    if (audioRef.current) {
      if (isPlaying) {
        audioRef.current.play().catch(e => console.error("Audio play failed", e));
      } else {
        audioRef.current.pause();
      }
    }
  }, [isPlaying]);

  // Format duration helper
  const formatDuration = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  if (!call) return null;

  const getStatusColor = (status: string) => {
    switch (status) {
      case "completed":
        return "bg-emerald-500/20 text-emerald-400 border-emerald-500/30";
      case "missed":
      case "no_answer":
        return "bg-amber-500/20 text-amber-400 border-amber-500/30";
      case "failed":
        return "bg-destructive/20 text-destructive border-destructive/30";
      case "in-progress":
      case "answered":
        return "bg-blue-500/20 text-blue-400 border-blue-500/30";
      default:
        return "bg-muted text-muted-foreground border-border";
    }
  };

  const getSentimentColor = (sentiment?: string) => {
    switch (sentiment) {
      case "positive":
        return "text-emerald-400";
      case "neutral":
        return "text-muted-foreground";
      case "negative":
        return "text-destructive";
      default:
        return "text-muted-foreground";
    }
  };

  const togglePlayback = () => {
    setIsPlaying(!isPlaying);
  };

  const direction = call.direction || "outbound"; // Default to outbound if missing
  const cost = call.cost || (call.duration_seconds * 0.05); // Estimate if missing

  // normalize transcript
  let transcriptItems: Array<{ role: string; content: string }> = [];
  if (Array.isArray(call.transcript)) {
    transcriptItems = call.transcript;
  } else if (typeof call.transcript === 'string') {
    // If it's a raw string, allow displaying it simply or try parsing if it looks like JSON
    try {
      const parsed = JSON.parse(call.transcript);
      if (Array.isArray(parsed)) transcriptItems = parsed;
    } catch {
      // Treat as single system message or agent message
      transcriptItems = [{ role: 'system', content: call.transcript }];
    }
  }

  const isPlayable = call.recording_url && call.recording_url.startsWith('http');

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent className="w-full sm:max-w-xl">
        <SheetHeader>
          <SheetTitle className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10">
              {direction === "inbound" ? (
                <PhoneIncoming className="h-5 w-5 text-primary" />
              ) : (
                <PhoneOutgoing className="h-5 w-5 text-primary" />
              )}
            </div>
            <div>
              <span className="capitalize">{direction} Call</span>
              <p className="text-sm font-normal text-muted-foreground">
                {new Date(call.created_at).toLocaleString()}
              </p>
            </div>
          </SheetTitle>
          <SheetDescription className="sr-only">Call details and transcript</SheetDescription>
        </SheetHeader>

        <ScrollArea className="h-[calc(100vh-120px)] pr-4">
          <div className="mt-6 space-y-6">
            {/* Call Info */}
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-1">
                <span className="text-xs text-muted-foreground">From</span>
                <p className="font-mono text-sm">{call.from_number || "Unknown"}</p>
              </div>
              <div className="space-y-1">
                <span className="text-xs text-muted-foreground">To</span>
                <p className="font-mono text-sm">{call.phone_number}</p>
              </div>
            </div>

            <div className="flex flex-wrap gap-2">
              <Badge variant="outline" className={getStatusColor(call.status)}>
                {call.status}
              </Badge>
              {call.assistant_id && (
                <Badge variant="outline" className="gap-1">
                  <Bot className="h-3 w-3" />
                  Agent
                </Badge>
              )}
              {call.analysis?.sentiment && (
                <Badge variant="outline" className={`capitalize ${getSentimentColor(call.analysis.sentiment)}`}>
                  {call.analysis.sentiment}
                </Badge>
              )}
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="flex items-center gap-2 rounded-lg border border-border p-3">
                <Clock className="h-4 w-4 text-muted-foreground" />
                <div>
                  <p className="text-xs text-muted-foreground">Duration</p>
                  <p className="font-medium">{formatDuration(call.duration_seconds)}</p>
                </div>
              </div>
              <div className="flex items-center gap-2 rounded-lg border border-border p-3">
                <DollarSign className="h-4 w-4 text-muted-foreground" />
                <div>
                  <p className="text-xs text-muted-foreground">Cost (Est.)</p>
                  <p className="font-medium">${cost.toFixed(2)}</p>
                </div>
              </div>
            </div>

            {/* Audio Player */}
            {call.recording_url && isPlayable && (
              <>
                <Separator />
                <div className="space-y-4">
                  <h3 className="flex items-center gap-2 font-medium">
                    <Phone className="h-4 w-4" />
                    Recording
                  </h3>

                  <div className="rounded-lg border border-border bg-muted/50 p-4">
                    <div className="flex items-center gap-4">
                      <Button
                        variant="outline"
                        size="icon"
                        className="h-10 w-10 shrink-0"
                        onClick={togglePlayback}
                      >
                        {isPlaying ? (
                          <Pause className="h-4 w-4" />
                        ) : (
                          <Play className="h-4 w-4" />
                        )}
                      </Button>
                      <div className="flex-1 space-y-2">
                        <Slider
                          value={[currentTime]}
                          max={call.duration_seconds || 100}
                          step={1}
                          onValueChange={([value]) => {
                            setCurrentTime(value);
                            if (audioRef.current) audioRef.current.currentTime = value;
                          }}
                          className="cursor-pointer"
                        />
                        <div className="flex justify-between text-xs text-muted-foreground">
                          <span>{formatDuration(currentTime)}</span>
                          <span>{formatDuration(call.duration_seconds)}</span>
                        </div>
                      </div>
                      <Button variant="ghost" size="icon" className="h-8 w-8 shrink-0" asChild>
                        <a href={call.recording_url} download target="_blank" rel="noopener noreferrer">
                          <Download className="h-4 w-4" />
                        </a>
                      </Button>
                    </div>
                  </div>
                </div>
              </>
            )}

            {/* Summary */}
            {call.analysis?.summary && (
              <>
                <Separator />
                <div className="space-y-3">
                  <h3 className="flex items-center gap-2 font-medium">
                    <FileText className="h-4 w-4" />
                    Summary
                  </h3>
                  <p className="text-sm text-muted-foreground leading-relaxed">
                    {call.analysis.summary}
                  </p>
                </div>
              </>
            )}

            {/* Transcript */}
            {transcriptItems.length > 0 && (
              <>
                <Separator />
                <div className="space-y-4">
                  <h3 className="font-medium">Transcript</h3>
                  <div className="space-y-4">
                    {transcriptItems.map((entry, index) => (
                      <div
                        key={index}
                        className={`flex gap-3 ${entry.role === "agent" || entry.role === "assistant" ? "" : "flex-row-reverse"
                          }`}
                      >
                        <div
                          className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-full ${entry.role === "agent" || entry.role === "assistant"
                            ? "bg-primary/10"
                            : "bg-accent"
                            }`}
                        >
                          {entry.role === "agent" || entry.role === "assistant" ? (
                            <Bot className="h-4 w-4 text-primary" />
                          ) : (
                            <User className="h-4 w-4" />
                          )}
                        </div>
                        <div
                          className={`flex-1 rounded-lg p-3 ${entry.role === "agent" || entry.role === "assistant"
                            ? "bg-primary/10 mr-8"
                            : "bg-accent ml-8"
                            }`}
                        >
                          <p className="text-sm">{entry.content}</p>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </>
            )}
          </div>
        </ScrollArea>
      </SheetContent>
    </Sheet>
  );
}
