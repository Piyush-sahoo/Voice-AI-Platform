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
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Plus, Search, MoreHorizontal, Bot, Copy, Trash2, Play, Edit, Loader2 } from "lucide-react";
import { AgentDrawer } from "@/components/agents/AgentDrawer";
import { toast } from "sonner";
import { assistantsApi } from "@/lib/api";

interface Assistant {
  assistant_id: string;
  name: string;
  description: string | null;
  instructions: string;
  first_message: string | null;
  voice: { provider: string; voice_id: string };
  model_provider: string;
  model_name: string;
  temperature: number;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export default function Agents() {
  const [agents, setAgents] = useState<Assistant[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [selectedAgent, setSelectedAgent] = useState<Assistant | null>(null);

  // Fetch agents from API
  const fetchAgents = async () => {
    setIsLoading(true);
    try {
      const data = await assistantsApi.list();
      setAgents(data.assistants as Assistant[]);
    } catch (error) {
      toast.error("Failed to load agents");
      console.error(error);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchAgents();
  }, []);

  const filteredAgents = agents.filter(
    (agent) =>
      agent.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      agent.description?.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const handleCreateAgent = () => {
    setSelectedAgent(null);
    setDrawerOpen(true);
  };

  const handleEditAgent = (agent: Assistant) => {
    setSelectedAgent(agent);
    setDrawerOpen(true);
  };

  const handleSaveAgent = async (agentData: Partial<Assistant>) => {
    try {
      if (selectedAgent) {
        // Update existing agent
        await assistantsApi.update(selectedAgent.assistant_id, agentData);
        toast.success("Agent updated successfully");
      } else {
        // Create new agent
        await assistantsApi.create({
          name: agentData.name || "New Agent",
          description: agentData.description,
          instructions: agentData.instructions || "You are a helpful voice assistant.",
          first_message: agentData.first_message,
          temperature: agentData.temperature ?? 0.8,
        });
        toast.success("Agent created successfully");
      }
      await fetchAgents(); // Refresh list
      setDrawerOpen(false);
    } catch (error) {
      toast.error("Failed to save agent");
      console.error(error);
    }
  };

  const handleDuplicateAgent = async (agent: Assistant) => {
    try {
      await assistantsApi.create({
        name: `${agent.name} (Copy)`,
        description: agent.description,
        instructions: agent.instructions,
        first_message: agent.first_message,
        temperature: agent.temperature,
      });
      toast.success("Agent duplicated");
      await fetchAgents();
    } catch (error) {
      toast.error("Failed to duplicate agent");
    }
  };

  const handleDeleteAgent = async (agentId: string) => {
    try {
      await assistantsApi.delete(agentId);
      toast.success("Agent deleted");
      await fetchAgents();
    } catch (error) {
      toast.error("Failed to delete agent");
    }
  };

  const handleTestAgent = (agent: Assistant) => {
    toast.info(`Testing ${agent.name}... Create a call to test this agent.`);
  };

  return (
    <DashboardLayout>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h1 className="text-2xl font-semibold text-foreground">Agents</h1>
            <p className="text-sm text-muted-foreground">
              Create and manage your AI voice agents
            </p>
          </div>
          <Button onClick={handleCreateAgent}>
            <Plus className="mr-2 h-4 w-4" />
            Create Agent
          </Button>
        </div>

        {/* Search */}
        <div className="relative max-w-sm">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            placeholder="Search agents..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-10"
          />
        </div>

        {/* Agents Table */}
        <div className="rounded-lg border border-border bg-card">
          <Table>
            <TableHeader>
              <TableRow className="hover:bg-transparent border-border">
                <TableHead className="text-muted-foreground">Agent</TableHead>
                <TableHead className="text-muted-foreground">Model</TableHead>
                <TableHead className="text-muted-foreground">Voice</TableHead>
                <TableHead className="text-muted-foreground">Status</TableHead>
                <TableHead className="text-muted-foreground">Last Updated</TableHead>
                <TableHead className="w-12"></TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {isLoading ? (
                <TableRow>
                  <TableCell colSpan={6} className="h-32 text-center">
                    <div className="flex flex-col items-center gap-2">
                      <Loader2 className="h-8 w-8 text-muted-foreground animate-spin" />
                      <p className="text-muted-foreground">Loading agents...</p>
                    </div>
                  </TableCell>
                </TableRow>
              ) : filteredAgents.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={6} className="h-32 text-center">
                    <div className="flex flex-col items-center gap-2">
                      <Bot className="h-8 w-8 text-muted-foreground" />
                      <p className="text-muted-foreground">No agents found</p>
                      <Button variant="outline" size="sm" onClick={handleCreateAgent}>
                        Create your first agent
                      </Button>
                    </div>
                  </TableCell>
                </TableRow>
              ) : (
                filteredAgents.map((agent) => (
                  <TableRow key={agent.assistant_id} className="cursor-pointer border-border" onClick={() => handleEditAgent(agent)}>
                    <TableCell>
                      <div className="flex items-center gap-3">
                        <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-primary/10">
                          <Bot className="h-4 w-4 text-primary" />
                        </div>
                        <div>
                          <p className="font-medium text-foreground">{agent.name}</p>
                          {agent.description && (
                            <p className="text-sm text-muted-foreground line-clamp-1">
                              {agent.description}
                            </p>
                          )}
                        </div>
                      </div>
                    </TableCell>
                    <TableCell>
                      <Badge variant="secondary" className="font-mono text-xs">
                        {agent.model_name}
                      </Badge>
                    </TableCell>
                    <TableCell className="capitalize text-foreground">{agent.voice?.voice_id || "alloy"}</TableCell>
                    <TableCell>
                      <Badge
                        variant="outline"
                        className={agent.is_active
                          ? "bg-emerald-500/20 text-emerald-400 border-emerald-500/30"
                          : "bg-muted text-muted-foreground border-border"
                        }
                      >
                        {agent.is_active ? "active" : "inactive"}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-muted-foreground">
                      {new Date(agent.updated_at).toLocaleDateString()}
                    </TableCell>
                    <TableCell>
                      <DropdownMenu>
                        <DropdownMenuTrigger asChild onClick={(e) => e.stopPropagation()}>
                          <Button variant="ghost" size="icon" className="h-8 w-8">
                            <MoreHorizontal className="h-4 w-4" />
                          </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="end">
                          <DropdownMenuItem onClick={(e) => { e.stopPropagation(); handleEditAgent(agent); }}>
                            <Edit className="mr-2 h-4 w-4" />
                            Edit
                          </DropdownMenuItem>
                          <DropdownMenuItem onClick={(e) => { e.stopPropagation(); handleTestAgent(agent); }}>
                            <Play className="mr-2 h-4 w-4" />
                            Test Agent
                          </DropdownMenuItem>
                          <DropdownMenuItem onClick={(e) => { e.stopPropagation(); handleDuplicateAgent(agent); }}>
                            <Copy className="mr-2 h-4 w-4" />
                            Duplicate
                          </DropdownMenuItem>
                          <DropdownMenuItem
                            className="text-destructive"
                            onClick={(e) => { e.stopPropagation(); handleDeleteAgent(agent.assistant_id); }}
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

      <AgentDrawer
        open={drawerOpen}
        onOpenChange={setDrawerOpen}
        agent={selectedAgent as any}
        onSave={handleSaveAgent as any}
      />
    </DashboardLayout>
  );
}
