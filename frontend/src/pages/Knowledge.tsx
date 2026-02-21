import { useEffect, useMemo, useState } from "react";
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
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  Plus,
  Search,
  MoreHorizontal,
  FileText,
  Globe,
  AlignLeft,
  Trash2,
  RefreshCw,
  BookOpen,
  Bot,
  Loader2,
} from "lucide-react";
import { UploadKnowledgeDialog } from "@/components/knowledge/UploadKnowledgeDialog";
import { KnowledgeDetailSheet } from "@/components/knowledge/KnowledgeDetailSheet";
import { formatFileSize, KnowledgeDocumentApi, KnowledgeItem, toKnowledgeItem } from "@/types/knowledge";
import { toast } from "sonner";

import { assistantsApi, knowledgeApi } from "@/lib/api";

interface AssistantOption {
  id: string;
  name: string;
}
export default function Knowledge() {
  const [knowledgeItems, setKnowledgeItems] = useState<KnowledgeItem[]>([]);
  const [assistants, setAssistants] = useState<AssistantOption[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [uploadDialogOpen, setUploadDialogOpen] = useState(false);
  const [selectedKnowledge, setSelectedKnowledge] = useState<KnowledgeItem | null>(null);
  const [detailSheetOpen, setDetailSheetOpen] = useState(false);

  const assistantNamesById = useMemo(
    () => assistants.reduce<Record<string, string>>((acc, agent) => {
      acc[agent.id] = agent.name;
      return acc;
    }, {}),
    [assistants]
  );

  const fetchKnowledge = async () => {
    setIsLoading(true);
    setLoadError(null);

    try {
      const response = await knowledgeApi.list();
      const documents = (response.documents as KnowledgeDocumentApi[]).map(toKnowledgeItem);
      setKnowledgeItems(documents);
    } catch (error) {
      const message = error instanceof Error ? error.message : "Failed to load knowledge";
      setLoadError(message);
      toast.error(message);
    } finally {
      setIsLoading(false);
    }
  };

  const fetchAssistants = async () => {
    try {
      const response = await assistantsApi.list();
      const mapped = (response.assistants || []).map((assistant) => ({
        id: assistant.assistant_id,
        name: assistant.name,
      }));
      setAssistants(mapped);
    } catch {
      setAssistants([]);
    }
  };

  useEffect(() => {
    fetchKnowledge();
    fetchAssistants();
  }, []);

  const filteredItems = knowledgeItems.filter((item) =>
    item.name.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const handleDelete = async (id: string) => {
    try {
      await knowledgeApi.delete(id);
      setKnowledgeItems((prev) => prev.filter((item) => item.id !== id));
      setSelectedKnowledge((prev) => (prev?.id === id ? null : prev));
      toast.success("Knowledge deleted");
    } catch (error) {
      const message = error instanceof Error ? error.message : "Failed to delete knowledge";
      toast.error(message);
    }
  };

  const handleResync = async (id: string) => {
    setKnowledgeItems((prev) =>
      prev.map((item) =>
        item.id === id ? { ...item, status: "processing" as const } : item
      )
    );

    setSelectedKnowledge((prev) =>
      prev && prev.id === id ? { ...prev, status: "processing" } : prev
    );

    try {
      await knowledgeApi.resync(id);
      toast.success("Re-sync started");
    } catch (error) {
      const message = error instanceof Error ? error.message : "Failed to re-sync knowledge";
      toast.error(message);
      await fetchKnowledge();
    }
  };

  const handleUploaded = async () => {
    await fetchKnowledge();
  };

  const getTypeIcon = (type: KnowledgeItem["type"]) => {
    switch (type) {
      case "url":
        return <Globe className="h-4 w-4" />;
      case "text":
        return <AlignLeft className="h-4 w-4" />;
      default:
        return <FileText className="h-4 w-4" />;
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

  const getAgentNames = (agentIds: string[]) => {
    return agentIds
      .map((id) => assistantNamesById[id])
      .filter(Boolean)
      .slice(0, 2);
  };

  return (
    <DashboardLayout>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h1 className="text-2xl font-semibold text-foreground">Knowledge Base</h1>
            <p className="text-sm text-muted-foreground">
              Upload documents and data to train your agents
            </p>
          </div>
          <Button onClick={() => setUploadDialogOpen(true)}>
            <Plus className="mr-2 h-4 w-4" />
            Upload Knowledge
          </Button>
        </div>

        {/* Search */}
        <div className="relative max-w-sm">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            placeholder="Search knowledge..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-10"
          />
        </div>

        {/* Knowledge Table */}
        <div className="rounded-lg border border-border bg-card">
          <Table>
            <TableHeader>
              <TableRow className="hover:bg-transparent">
                <TableHead>Name</TableHead>
                <TableHead>Type</TableHead>
                <TableHead>Size</TableHead>
                <TableHead>Tokens</TableHead>
                <TableHead>Assigned Agents</TableHead>
                <TableHead>Status</TableHead>
                <TableHead className="w-12"></TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {isLoading ? (
                <TableRow>
                  <TableCell colSpan={7} className="h-32 text-center">
                    <div className="flex flex-col items-center gap-2">
                      <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
                      <p className="text-muted-foreground">Loading knowledge...</p>
                    </div>
                  </TableCell>
                </TableRow>
              ) : loadError ? (
                <TableRow>
                  <TableCell colSpan={7} className="h-32 text-center">
                    <div className="flex flex-col items-center gap-2">
                      <BookOpen className="h-8 w-8 text-muted-foreground" />
                      <p className="text-muted-foreground">{loadError}</p>
                      <Button variant="outline" size="sm" onClick={fetchKnowledge}>
                        Retry
                      </Button>
                    </div>
                  </TableCell>
                </TableRow>
              ) : filteredItems.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={7} className="h-32 text-center">
                    <div className="flex flex-col items-center gap-2">
                      <BookOpen className="h-8 w-8 text-muted-foreground" />
                      <p className="text-muted-foreground">No knowledge found</p>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => setUploadDialogOpen(true)}
                      >
                        Upload your first document
                      </Button>
                    </div>
                  </TableCell>
                </TableRow>
              ) : (
                filteredItems.map((item) => (
                  <TableRow
                    key={item.id}
                    className="cursor-pointer"
                    onClick={() => {
                      setSelectedKnowledge(item);
                      setDetailSheetOpen(true);
                    }}
                  >
                    <TableCell>
                      <div className="flex items-center gap-3">
                        <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-primary/10">
                          {getTypeIcon(item.type)}
                        </div>
                        <span className="font-medium text-foreground">{item.name}</span>
                      </div>
                    </TableCell>
                    <TableCell>
                      <Badge variant="secondary" className="font-mono text-xs uppercase">
                        {item.type}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-muted-foreground">
                      {formatFileSize(item.size)}
                    </TableCell>
                    <TableCell className="text-muted-foreground">
                      {item.tokenCount.toLocaleString()}
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center gap-1">
                        {getAgentNames(item.assignedAgents).length > 0 ? (
                          <>
                            {getAgentNames(item.assignedAgents).map((name) => (
                              <Badge
                                key={name}
                                variant="outline"
                                className="gap-1 text-xs"
                              >
                                <Bot className="h-3 w-3" />
                                {name}
                              </Badge>
                            ))}
                            {item.assignedAgents.length > 2 && (
                              <Badge variant="outline" className="text-xs">
                                +{item.assignedAgents.length - 2}
                              </Badge>
                            )}
                          </>
                        ) : (
                          <span className="text-sm text-muted-foreground">—</span>
                        )}
                      </div>
                    </TableCell>
                    <TableCell>
                      <Badge variant="outline" className={getStatusColor(item.status)}>
                        {item.status}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      <DropdownMenu>
                        <DropdownMenuTrigger asChild onClick={(e) => e.stopPropagation()}>
                          <Button variant="ghost" size="icon" className="h-8 w-8">
                            <MoreHorizontal className="h-4 w-4" />
                          </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="end">
                          <DropdownMenuItem
                            onClick={(e) => {
                              e.stopPropagation();
                              handleResync(item.id);
                            }}
                            disabled={item.status === "processing"}
                          >
                            <RefreshCw className="mr-2 h-4 w-4" />
                            Re-sync
                          </DropdownMenuItem>
                          <DropdownMenuItem
                            className="text-destructive"
                            onClick={(e) => {
                              e.stopPropagation();
                              handleDelete(item.id);
                            }}
                          >
                            <Trash2 className="mr-2 h-4 w-4" />
                            Delete
                          </DropdownMenuItem>
                        </DropdownMenuContent>
                      </DropdownMenu>
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </div>
      </div>

      <UploadKnowledgeDialog
        open={uploadDialogOpen}
        onOpenChange={setUploadDialogOpen}
        assistants={assistants}
        onUploaded={handleUploaded}
      />

      <KnowledgeDetailSheet
        open={detailSheetOpen}
        onOpenChange={setDetailSheetOpen}
        knowledge={selectedKnowledge}
        onDelete={handleDelete}
        onResync={handleResync}
        assistantNamesById={assistantNamesById}
      />
    </DashboardLayout>
  );
}
