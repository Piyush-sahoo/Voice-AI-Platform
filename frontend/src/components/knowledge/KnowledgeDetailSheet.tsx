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
import { KnowledgeItem, formatFileSize } from "@/data/mockKnowledge";
import { mockAgents } from "@/data/mockAgents";
import { RefreshCw, Trash2, FileText, Globe, AlignLeft, Bot } from "lucide-react";
import { toast } from "sonner";

interface KnowledgeDetailSheetProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  knowledge: KnowledgeItem | null;
  onDelete: (id: string) => void;
  onResync: (id: string) => void;
}

export function KnowledgeDetailSheet({
  open,
  onOpenChange,
  knowledge,
  onDelete,
  onResync,
}: KnowledgeDetailSheetProps) {
  if (!knowledge) return null;

  const getTypeIcon = () => {
    switch (knowledge.type) {
      case "url":
        return <Globe className="h-5 w-5" />;
      case "text":
        return <AlignLeft className="h-5 w-5" />;
      default:
        return <FileText className="h-5 w-5" />;
    }
  };

  const getStatusColor = (status: KnowledgeItem["status"]) => {
    switch (status) {
      case "ready":
        return "bg-emerald-500/20 text-emerald-400 border-emerald-500/30";
      case "processing":
        return "bg-amber-500/20 text-amber-400 border-amber-500/30";
      case "error":
        return "bg-destructive/20 text-destructive border-destructive/30";
    }
  };

  const assignedAgentNames = knowledge.assignedAgents
    .map((id) => mockAgents.find((a) => a.id === id)?.name)
    .filter(Boolean);

  const handleResync = () => {
    onResync(knowledge.id);
    toast.success("Re-sync started");
  };

  const handleDelete = () => {
    onDelete(knowledge.id);
    onOpenChange(false);
    toast.success("Knowledge deleted");
  };

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent className="w-full sm:max-w-md">
        <SheetHeader>
          <SheetTitle className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10">
              {getTypeIcon()}
            </div>
            <span className="line-clamp-1">{knowledge.name}</span>
          </SheetTitle>
          <SheetDescription>Knowledge base details</SheetDescription>
        </SheetHeader>

        <div className="mt-6 space-y-6">
          {/* Status */}
          <div className="flex items-center justify-between">
            <span className="text-sm text-muted-foreground">Status</span>
            <Badge variant="outline" className={getStatusColor(knowledge.status)}>
              {knowledge.status}
            </Badge>
          </div>

          <Separator />

          {/* Details */}
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <span className="text-sm text-muted-foreground">Type</span>
              <span className="text-sm font-medium uppercase">{knowledge.type}</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-muted-foreground">Size</span>
              <span className="text-sm font-medium">{formatFileSize(knowledge.size)}</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-muted-foreground">Token Count</span>
              <span className="text-sm font-medium">
                {knowledge.tokenCount.toLocaleString()}
              </span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-muted-foreground">Created</span>
              <span className="text-sm font-medium">
                {new Date(knowledge.createdAt).toLocaleDateString()}
              </span>
            </div>
            {knowledge.lastSyncedAt && (
              <div className="flex items-center justify-between">
                <span className="text-sm text-muted-foreground">Last Synced</span>
                <span className="text-sm font-medium">
                  {new Date(knowledge.lastSyncedAt).toLocaleDateString()}
                </span>
              </div>
            )}
          </div>

          <Separator />

          {/* Assigned Agents */}
          <div className="space-y-3">
            <span className="text-sm text-muted-foreground">Assigned Agents</span>
            {assignedAgentNames.length > 0 ? (
              <div className="space-y-2">
                {assignedAgentNames.map((name) => (
                  <div
                    key={name}
                    className="flex items-center gap-2 rounded-lg border border-border bg-muted/50 px-3 py-2"
                  >
                    <Bot className="h-4 w-4 text-primary" />
                    <span className="text-sm">{name}</span>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-sm text-muted-foreground">No agents assigned</p>
            )}
          </div>

          <Separator />

          {/* Actions */}
          <div className="space-y-3">
            <Button
              variant="outline"
              className="w-full justify-start gap-2"
              onClick={handleResync}
              disabled={knowledge.status === "processing"}
            >
              <RefreshCw className="h-4 w-4" />
              Re-sync Knowledge
            </Button>
            <Button
              variant="outline"
              className="w-full justify-start gap-2 text-destructive hover:bg-destructive/10 hover:text-destructive"
              onClick={handleDelete}
            >
              <Trash2 className="h-4 w-4" />
              Delete Knowledge
            </Button>
          </div>
        </div>
      </SheetContent>
    </Sheet>
  );
}
