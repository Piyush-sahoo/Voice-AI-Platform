import { useState } from "react";
import { DashboardLayout } from "@/components/layout/DashboardLayout";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { Separator } from "@/components/ui/separator";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from "@/components/ui/alert-dialog";
import {
  Building2,
  Key,
  Bot,
  Users,
  Copy,
  Eye,
  EyeOff,
  RefreshCw,
  Trash2,
  Plus,
  Shield,
} from "lucide-react";
import { voiceOptions, modelOptions } from "@/data/mockAgents";
import { toast } from "sonner";

interface ApiKey {
  id: string;
  name: string;
  key: string;
  createdAt: string;
  lastUsed?: string;
}

interface TeamMember {
  id: string;
  email: string;
  name: string;
  role: "owner" | "admin" | "editor" | "viewer";
  joinedAt: string;
}

const mockApiKeys: ApiKey[] = [
  {
    id: "key-1",
    name: "Production",
    key: "vk_live_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
    createdAt: "2024-01-05T10:00:00Z",
    lastUsed: "2024-01-20T14:30:00Z",
  },
  {
    id: "key-2",
    name: "Development",
    key: "vk_test_yyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyy",
    createdAt: "2024-01-10T09:00:00Z",
    lastUsed: "2024-01-19T16:45:00Z",
  },
];

const mockTeamMembers: TeamMember[] = [
  {
    id: "user-1",
    email: "owner@example.com",
    name: "John Doe",
    role: "owner",
    joinedAt: "2024-01-01T00:00:00Z",
  },
  {
    id: "user-2",
    email: "admin@example.com",
    name: "Jane Smith",
    role: "admin",
    joinedAt: "2024-01-05T10:00:00Z",
  },
  {
    id: "user-3",
    email: "editor@example.com",
    name: "Bob Wilson",
    role: "editor",
    joinedAt: "2024-01-10T14:00:00Z",
  },
];

export default function Settings() {
  const [workspaceName, setWorkspaceName] = useState("My Workspace");
  const [apiKeys, setApiKeys] = useState<ApiKey[]>(mockApiKeys);
  const [teamMembers] = useState<TeamMember[]>(mockTeamMembers);
  const [visibleKeys, setVisibleKeys] = useState<Record<string, boolean>>({});
  const [inviteEmail, setInviteEmail] = useState("");

  // Agent defaults
  const [defaultModel, setDefaultModel] = useState("gpt-4");
  const [defaultVoice, setDefaultVoice] = useState("alloy");
  const [defaultRecording, setDefaultRecording] = useState(true);
  const [defaultTranscription, setDefaultTranscription] = useState(true);

  const toggleKeyVisibility = (keyId: string) => {
    setVisibleKeys((prev) => ({ ...prev, [keyId]: !prev[keyId] }));
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    toast.success("Copied to clipboard");
  };

  const regenerateKey = (keyId: string) => {
    const newKey = `vk_${keyId.includes("live") ? "live" : "test"}_${Math.random().toString(36).substring(2, 34)}`;
    setApiKeys((prev) =>
      prev.map((k) =>
        k.id === keyId ? { ...k, key: newKey, createdAt: new Date().toISOString() } : k
      )
    );
    toast.success("API key regenerated");
  };

  const deleteKey = (keyId: string) => {
    setApiKeys((prev) => prev.filter((k) => k.id !== keyId));
    toast.success("API key deleted");
  };

  const createNewKey = () => {
    const newKey: ApiKey = {
      id: `key-${Date.now()}`,
      name: "New Key",
      key: `vk_test_${Math.random().toString(36).substring(2, 34)}`,
      createdAt: new Date().toISOString(),
    };
    setApiKeys((prev) => [...prev, newKey]);
    toast.success("New API key created");
  };

  const handleInvite = () => {
    if (!inviteEmail.trim()) {
      toast.error("Please enter an email address");
      return;
    }
    toast.success(`Invitation sent to ${inviteEmail}`);
    setInviteEmail("");
  };

  const handleSaveWorkspace = () => {
    toast.success("Workspace settings saved");
  };

  const handleSaveDefaults = () => {
    toast.success("Agent defaults saved");
  };

  const getRoleBadgeColor = (role: TeamMember["role"]) => {
    switch (role) {
      case "owner":
        return "bg-primary/20 text-primary border-primary/30";
      case "admin":
        return "bg-amber-500/20 text-amber-400 border-amber-500/30";
      case "editor":
        return "bg-emerald-500/20 text-emerald-400 border-emerald-500/30";
      case "viewer":
        return "bg-muted text-muted-foreground border-border";
    }
  };

  return (
    <DashboardLayout>
      <div className="space-y-6">
        {/* Header */}
        <div>
          <h1 className="text-2xl font-semibold text-foreground">Settings</h1>
          <p className="text-sm text-muted-foreground">
            Manage your workspace, API keys, and preferences
          </p>
        </div>

        <Tabs defaultValue="workspace" className="space-y-6">
          <TabsList>
            <TabsTrigger value="workspace" className="gap-2">
              <Building2 className="h-4 w-4" />
              Workspace
            </TabsTrigger>
            <TabsTrigger value="api-keys" className="gap-2">
              <Key className="h-4 w-4" />
              API Keys
            </TabsTrigger>
            <TabsTrigger value="team" className="gap-2">
              <Users className="h-4 w-4" />
              Team
            </TabsTrigger>
            <TabsTrigger value="defaults" className="gap-2">
              <Bot className="h-4 w-4" />
              Agent Defaults
            </TabsTrigger>
          </TabsList>

          {/* Workspace Settings */}
          <TabsContent value="workspace">
            <Card>
              <CardHeader>
                <CardTitle>Workspace Settings</CardTitle>
                <CardDescription>
                  Manage your workspace name and general settings
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="max-w-md space-y-2">
                  <Label htmlFor="workspace-name">Workspace Name</Label>
                  <Input
                    id="workspace-name"
                    value={workspaceName}
                    onChange={(e) => setWorkspaceName(e.target.value)}
                  />
                </div>

                <Separator />

                <div className="space-y-4">
                  <h4 className="font-medium text-foreground">Billing</h4>
                  <div className="flex items-center justify-between rounded-lg border border-border p-4">
                    <div>
                      <p className="font-medium text-foreground">Pro Plan</p>
                      <p className="text-sm text-muted-foreground">
                        $79/month · Renews Jan 28, 2024
                      </p>
                    </div>
                    <Button variant="outline">Manage Billing</Button>
                  </div>
                </div>

                <Separator />

                <div className="space-y-4">
                  <h4 className="font-medium text-foreground">Usage This Month</h4>
                  <div className="grid gap-4 sm:grid-cols-3">
                    <div className="rounded-lg border border-border p-4">
                      <p className="text-2xl font-bold text-foreground">1,247</p>
                      <p className="text-sm text-muted-foreground">Calls</p>
                    </div>
                    <div className="rounded-lg border border-border p-4">
                      <p className="text-2xl font-bold text-foreground">68.4 hrs</p>
                      <p className="text-sm text-muted-foreground">Call Time</p>
                    </div>
                    <div className="rounded-lg border border-border p-4">
                      <p className="text-2xl font-bold text-foreground">$156.32</p>
                      <p className="text-sm text-muted-foreground">Total Cost</p>
                    </div>
                  </div>
                </div>

                <div className="flex justify-end">
                  <Button onClick={handleSaveWorkspace}>Save Changes</Button>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* API Keys */}
          <TabsContent value="api-keys">
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div>
                    <CardTitle>API Keys</CardTitle>
                    <CardDescription>
                      Manage your API keys for programmatic access
                    </CardDescription>
                  </div>
                  <Button onClick={createNewKey}>
                    <Plus className="mr-2 h-4 w-4" />
                    Create Key
                  </Button>
                </div>
              </CardHeader>
              <CardContent>
                <div className="rounded-lg border border-border">
                  <Table>
                    <TableHeader>
                      <TableRow className="hover:bg-transparent">
                        <TableHead>Name</TableHead>
                        <TableHead>Key</TableHead>
                        <TableHead>Created</TableHead>
                        <TableHead>Last Used</TableHead>
                        <TableHead className="w-32"></TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {apiKeys.map((apiKey) => (
                        <TableRow key={apiKey.id}>
                          <TableCell className="font-medium text-foreground">{apiKey.name}</TableCell>
                          <TableCell>
                            <div className="flex items-center gap-2">
                              <code className="rounded bg-muted px-2 py-1 font-mono text-sm">
                                {visibleKeys[apiKey.id]
                                  ? apiKey.key
                                  : `${apiKey.key.substring(0, 12)}${"•".repeat(20)}`}
                              </code>
                              <Button
                                variant="ghost"
                                size="icon"
                                className="h-8 w-8"
                                onClick={() => toggleKeyVisibility(apiKey.id)}
                              >
                                {visibleKeys[apiKey.id] ? (
                                  <EyeOff className="h-4 w-4" />
                                ) : (
                                  <Eye className="h-4 w-4" />
                                )}
                              </Button>
                              <Button
                                variant="ghost"
                                size="icon"
                                className="h-8 w-8"
                                onClick={() => copyToClipboard(apiKey.key)}
                              >
                                <Copy className="h-4 w-4" />
                              </Button>
                            </div>
                          </TableCell>
                          <TableCell className="text-muted-foreground">
                            {new Date(apiKey.createdAt).toLocaleDateString()}
                          </TableCell>
                          <TableCell className="text-muted-foreground">
                            {apiKey.lastUsed
                              ? new Date(apiKey.lastUsed).toLocaleDateString()
                              : "Never"}
                          </TableCell>
                          <TableCell>
                            <div className="flex items-center gap-1">
                              <Button
                                variant="ghost"
                                size="icon"
                                className="h-8 w-8"
                                onClick={() => regenerateKey(apiKey.id)}
                              >
                                <RefreshCw className="h-4 w-4" />
                              </Button>
                              <AlertDialog>
                                <AlertDialogTrigger asChild>
                                  <Button
                                    variant="ghost"
                                    size="icon"
                                    className="h-8 w-8 text-destructive hover:text-destructive"
                                  >
                                    <Trash2 className="h-4 w-4" />
                                  </Button>
                                </AlertDialogTrigger>
                                <AlertDialogContent>
                                  <AlertDialogHeader>
                                    <AlertDialogTitle>Delete API Key</AlertDialogTitle>
                                    <AlertDialogDescription>
                                      Are you sure you want to delete this API key? Any
                                      applications using this key will stop working
                                      immediately.
                                    </AlertDialogDescription>
                                  </AlertDialogHeader>
                                  <AlertDialogFooter>
                                    <AlertDialogCancel>Cancel</AlertDialogCancel>
                                    <AlertDialogAction
                                      onClick={() => deleteKey(apiKey.id)}
                                      className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
                                    >
                                      Delete
                                    </AlertDialogAction>
                                  </AlertDialogFooter>
                                </AlertDialogContent>
                              </AlertDialog>
                            </div>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </div>

                <div className="mt-4 flex items-start gap-2 rounded-lg border border-amber-500/30 bg-amber-500/10 p-4">
                  <Shield className="h-5 w-5 shrink-0 text-amber-400" />
                  <div className="text-sm">
                    <p className="font-medium text-amber-400">Keep your keys secure</p>
                    <p className="text-muted-foreground">
                      Never share your API keys or commit them to version control. Use
                      environment variables instead.
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Team */}
          <TabsContent value="team">
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div>
                    <CardTitle>Team Members</CardTitle>
                    <CardDescription>
                      Manage who has access to this workspace
                    </CardDescription>
                  </div>
                </div>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="flex gap-3">
                  <Input
                    placeholder="Enter email to invite..."
                    value={inviteEmail}
                    onChange={(e) => setInviteEmail(e.target.value)}
                    className="max-w-sm"
                  />
                  <Button onClick={handleInvite}>
                    <Plus className="mr-2 h-4 w-4" />
                    Invite
                  </Button>
                </div>

                <div className="rounded-lg border border-border">
                  <Table>
                    <TableHeader>
                      <TableRow className="hover:bg-transparent">
                        <TableHead>Member</TableHead>
                        <TableHead>Role</TableHead>
                        <TableHead>Joined</TableHead>
                        <TableHead className="w-12"></TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {teamMembers.map((member) => (
                        <TableRow key={member.id}>
                          <TableCell>
                            <div>
                              <p className="font-medium text-foreground">{member.name}</p>
                              <p className="text-sm text-muted-foreground">
                                {member.email}
                              </p>
                            </div>
                          </TableCell>
                          <TableCell>
                            <Badge
                              variant="outline"
                              className={`capitalize ${getRoleBadgeColor(member.role)}`}
                            >
                              {member.role}
                            </Badge>
                          </TableCell>
                          <TableCell className="text-muted-foreground">
                            {new Date(member.joinedAt).toLocaleDateString()}
                          </TableCell>
                          <TableCell>
                            {member.role !== "owner" && (
                              <Button
                                variant="ghost"
                                size="icon"
                                className="h-8 w-8 text-destructive hover:text-destructive"
                              >
                                <Trash2 className="h-4 w-4" />
                              </Button>
                            )}
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Agent Defaults */}
          <TabsContent value="defaults">
            <Card>
              <CardHeader>
                <CardTitle>Agent Defaults</CardTitle>
                <CardDescription>
                  Set default configuration for new agents
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="grid gap-6 sm:grid-cols-2">
                  <div className="space-y-2">
                    <Label>Default Model</Label>
                    <Select value={defaultModel} onValueChange={setDefaultModel}>
                      <SelectTrigger>
                        <SelectValue placeholder="Select model" />
                      </SelectTrigger>
                      <SelectContent>
                        {modelOptions.map((model) => (
                          <SelectItem key={model.id} value={model.id}>
                            {model.name}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>

                  <div className="space-y-2">
                    <Label>Default Voice</Label>
                    <Select value={defaultVoice} onValueChange={setDefaultVoice}>
                      <SelectTrigger>
                        <SelectValue placeholder="Select voice" />
                      </SelectTrigger>
                      <SelectContent>
                        {voiceOptions.map((voice) => (
                          <SelectItem key={voice.id} value={voice.id}>
                            {voice.name} ({voice.gender})
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                </div>

                <Separator />

                <div className="space-y-4">
                  <h4 className="font-medium text-foreground">Recording & Transcription</h4>

                  <div className="flex items-center justify-between rounded-lg border border-border p-4">
                    <div>
                      <p className="font-medium text-foreground">Enable Call Recording</p>
                      <p className="text-sm text-muted-foreground">
                        Record all calls by default for new agents
                      </p>
                    </div>
                    <Switch
                      checked={defaultRecording}
                      onCheckedChange={setDefaultRecording}
                    />
                  </div>

                  <div className="flex items-center justify-between rounded-lg border border-border p-4">
                    <div>
                      <p className="font-medium text-foreground">Enable Transcription</p>
                      <p className="text-sm text-muted-foreground">
                        Automatically transcribe all calls
                      </p>
                    </div>
                    <Switch
                      checked={defaultTranscription}
                      onCheckedChange={setDefaultTranscription}
                    />
                  </div>
                </div>

                <div className="flex justify-end">
                  <Button onClick={handleSaveDefaults}>Save Defaults</Button>
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </DashboardLayout>
  );
}
