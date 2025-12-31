import { useState, useEffect } from "react";
import { DashboardLayout } from "@/components/layout/DashboardLayout";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
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
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Plus,
  Search,
  MoreHorizontal,
  Phone,
  PhoneIncoming,
  PhoneOutgoing,
  Trash2,
  Server,
  Loader2,
  Bot,
} from "lucide-react";
import { AddSIPConfigDialog } from "@/components/phone-numbers/AddSIPConfigDialog";
import { toast } from "sonner";
import { phoneNumbersApi, sipConfigsApi, assistantsApi } from "@/lib/api";

interface PhoneNumber {
  id: string;
  number: string;
  label?: string;
  direction: "inbound" | "outbound" | "both";
  type: "local" | "toll-free" | "mobile" | "sip";
  status: "active" | "inactive" | "pending";
  assigned_agent_id?: string;
  inbound_trunk_id?: string;
  created_at: string;
}

interface Assistant {
  assistant_id: string;
  name: string;
}

export default function PhoneNumbers() {
  const [phoneNumbers, setPhoneNumbers] = useState<PhoneNumber[]>([]);
  const [assistants, setAssistants] = useState<Assistant[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");
  const [addDialogOpen, setAddDialogOpen] = useState(false);
  const [inboundDialogOpen, setInboundDialogOpen] = useState(false);

  // Inbound form state
  const [inboundForm, setInboundForm] = useState({
    number: "",
    label: "",
    assistant_id: "",
    krisp_enabled: true,
  });
  const [isCreatingInbound, setIsCreatingInbound] = useState(false);

  const fetchData = async () => {
    setIsLoading(true);
    try {
      const [phonesData, sipsData, assistantsData] = await Promise.all([
        phoneNumbersApi.list().catch(() => ({ phone_numbers: [] })),
        sipConfigsApi.list().catch(() => ({ sip_configs: [] })),
        assistantsApi.list().catch(() => ({ assistants: [] })),
      ]);

      const mappedPhones: PhoneNumber[] = (phonesData.phone_numbers as any[]).map((p) => ({
        id: p.phone_id,
        number: p.number || p.phone_number,
        label: p.label,
        direction: p.direction || "outbound",
        type: "local",
        status: p.is_active ? "active" : "inactive",
        assigned_agent_id: p.assistant_id,
        inbound_trunk_id: p.inbound_trunk_id,
        created_at: p.created_at,
      }));

      const mappedSips: PhoneNumber[] = (sipsData.sip_configs as any[]).map((s) => ({
        id: s.sip_id,
        number: s.from_number || s.phone_number || "SIP Endpoint",
        label: s.name,
        direction: "outbound" as const,
        type: "sip",
        status: s.is_active ? "active" : "inactive",
        created_at: s.created_at,
      }));

      setPhoneNumbers([...mappedPhones, ...mappedSips]);
      setAssistants(assistantsData.assistants as Assistant[]);
    } catch (error) {
      toast.error("Failed to load phone numbers");
      console.error(error);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const filteredNumbers = phoneNumbers.filter((num) =>
    (num.number || "").toLowerCase().includes(searchQuery.toLowerCase()) ||
    (num.label || "").toLowerCase().includes(searchQuery.toLowerCase())
  );

  const handleAddSIPConfig = async (config: {
    name: string;
    sipTerminalUri: string;
    username: string;
    password: string;
    phoneNumber: string;
  }) => {
    try {
      await sipConfigsApi.create({
        phone_number: config.phoneNumber,
        username: config.username,
        password: config.password,
        label: config.name,
      });
      toast.success("SIP configuration added successfully");
      fetchData();
    } catch (error) {
      toast.error("Failed to add SIP configuration");
    }
  };

  const handleAddInbound = async () => {
    if (!inboundForm.number.startsWith("+")) {
      toast.error("Phone number must be in E.164 format (e.g., +912271264190)");
      return;
    }
    if (!inboundForm.assistant_id) {
      toast.error("Please select an agent to answer calls");
      return;
    }

    setIsCreatingInbound(true);
    try {
      const data: any = await phoneNumbersApi.createInbound({
        number: inboundForm.number,
        label: inboundForm.label || undefined,
        assistant_id: inboundForm.assistant_id,
        krisp_enabled: inboundForm.krisp_enabled,
      });
      toast.success(data.message || "Inbound number configured!");
      setInboundDialogOpen(false);
      setInboundForm({ number: "", label: "", assistant_id: "", krisp_enabled: true });
      fetchData();
    } catch (error: any) {
      toast.error(error.message || "Failed to create inbound number");
    } finally {
      setIsCreatingInbound(false);
    }
  };

  const handleDelete = async (num: PhoneNumber) => {
    try {
      if (num.type === "sip") {
        await sipConfigsApi.delete(num.id);
      } else {
        await phoneNumbersApi.delete(num.id);
      }
      toast.success("Phone number removed");
      fetchData();
    } catch (error) {
      toast.error("Failed to remove phone number");
    }
  };

  const getDirectionBadge = (direction: PhoneNumber["direction"]) => {
    switch (direction) {
      case "inbound":
        return (
          <Badge variant="outline" className="bg-blue-500/20 text-blue-400 border-blue-500/30 gap-1">
            <PhoneIncoming className="h-3 w-3" />
            Inbound
          </Badge>
        );
      case "outbound":
        return (
          <Badge variant="outline" className="bg-green-500/20 text-green-400 border-green-500/30 gap-1">
            <PhoneOutgoing className="h-3 w-3" />
            Outbound
          </Badge>
        );
      case "both":
        return (
          <Badge variant="outline" className="bg-purple-500/20 text-purple-400 border-purple-500/30">
            Both
          </Badge>
        );
    }
  };

  const getAgentName = (agentId?: string) => {
    if (!agentId) return null;
    return assistants.find((a) => a.assistant_id === agentId)?.name;
  };

  return (
    <DashboardLayout>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h1 className="text-2xl font-semibold text-foreground">Phone Numbers</h1>
            <p className="text-sm text-muted-foreground">
              Configure inbound and outbound phone numbers
            </p>
          </div>
          <div className="flex gap-2">
            <Button variant="outline" onClick={() => setInboundDialogOpen(true)}>
              <PhoneIncoming className="mr-2 h-4 w-4" />
              Add Inbound
            </Button>
            <Button onClick={() => setAddDialogOpen(true)}>
              <Plus className="mr-2 h-4 w-4" />
              Add Outbound
            </Button>
          </div>
        </div>

        {/* Search */}
        <div className="relative max-w-sm">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            placeholder="Search numbers..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-10"
          />
        </div>

        {/* Phone Numbers Table */}
        <div className="rounded-lg border border-border bg-card">
          <Table>
            <TableHeader>
              <TableRow className="hover:bg-transparent border-border">
                <TableHead className="text-muted-foreground">Phone Number</TableHead>
                <TableHead className="text-muted-foreground">Direction</TableHead>
                <TableHead className="text-muted-foreground">Type</TableHead>
                <TableHead className="text-muted-foreground">Agent</TableHead>
                <TableHead className="w-12"></TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {isLoading ? (
                <TableRow>
                  <TableCell colSpan={5} className="h-32 text-center">
                    <div className="flex flex-col items-center gap-2">
                      <Loader2 className="h-8 w-8 text-muted-foreground animate-spin" />
                      <p className="text-muted-foreground">Loading phone numbers...</p>
                    </div>
                  </TableCell>
                </TableRow>
              ) : filteredNumbers.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={5} className="h-32 text-center">
                    <div className="flex flex-col items-center gap-2">
                      <Server className="h-8 w-8 text-muted-foreground" />
                      <p className="text-muted-foreground">No phone numbers found</p>
                      <div className="flex gap-2">
                        <Button variant="outline" size="sm" onClick={() => setInboundDialogOpen(true)}>
                          Add Inbound
                        </Button>
                        <Button variant="outline" size="sm" onClick={() => setAddDialogOpen(true)}>
                          Add Outbound
                        </Button>
                      </div>
                    </div>
                  </TableCell>
                </TableRow>
              ) : (
                filteredNumbers.map((num) => (
                  <TableRow key={num.id} className="border-border">
                    <TableCell>
                      <div className="flex items-center gap-3">
                        <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-primary/10">
                          <Phone className="h-4 w-4 text-primary" />
                        </div>
                        <div>
                          <span className="font-mono font-medium text-foreground">{num.number}</span>
                          {num.label && (
                            <p className="text-xs text-muted-foreground">{num.label}</p>
                          )}
                        </div>
                      </div>
                    </TableCell>
                    <TableCell>{getDirectionBadge(num.direction)}</TableCell>
                    <TableCell>
                      <Badge variant="secondary" className="capitalize">
                        {num.type}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      {getAgentName(num.assigned_agent_id) ? (
                        <Badge variant="outline" className="gap-1">
                          <Bot className="h-3 w-3" />
                          {getAgentName(num.assigned_agent_id)}
                        </Badge>
                      ) : (
                        <span className="text-sm text-muted-foreground">—</span>
                      )}
                    </TableCell>
                    <TableCell>
                      <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                          <Button variant="ghost" size="icon" className="h-8 w-8">
                            <MoreHorizontal className="h-4 w-4" />
                          </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="end">
                          <DropdownMenuItem
                            className="text-destructive"
                            onClick={() => handleDelete(num)}
                          >
                            <Trash2 className="mr-2 h-4 w-4" />
                            Remove
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

      {/* Add SIP Config (Outbound) Dialog */}
      <AddSIPConfigDialog
        open={addDialogOpen}
        onOpenChange={setAddDialogOpen}
        onAdd={handleAddSIPConfig}
      />

      {/* Add Inbound Number Dialog */}
      <Dialog open={inboundDialogOpen} onOpenChange={setInboundDialogOpen}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>Set Up Inbound Number</DialogTitle>
            <DialogDescription>
              Configure a phone number to receive incoming calls. The selected agent will automatically answer.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label htmlFor="inbound-number">Phone Number *</Label>
              <Input
                id="inbound-number"
                placeholder="+912271264190"
                value={inboundForm.number}
                onChange={(e) => setInboundForm({ ...inboundForm, number: e.target.value })}
              />
              <p className="text-xs text-muted-foreground">E.164 format (include country code)</p>
            </div>
            <div className="space-y-2">
              <Label htmlFor="inbound-label">Label (Optional)</Label>
              <Input
                id="inbound-label"
                placeholder="Customer Support Line"
                value={inboundForm.label}
                onChange={(e) => setInboundForm({ ...inboundForm, label: e.target.value })}
              />
            </div>
            <div className="space-y-2">
              <Label>Agent to Answer Calls *</Label>
              <Select
                value={inboundForm.assistant_id}
                onValueChange={(value) => setInboundForm({ ...inboundForm, assistant_id: value })}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select an agent" />
                </SelectTrigger>
                <SelectContent>
                  {assistants.map((agent) => (
                    <SelectItem key={agent.assistant_id} value={agent.assistant_id}>
                      {agent.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="flex items-center justify-between">
              <div>
                <Label htmlFor="krisp">Noise Cancellation</Label>
                <p className="text-xs text-muted-foreground">Remove background noise</p>
              </div>
              <Switch
                id="krisp"
                checked={inboundForm.krisp_enabled}
                onCheckedChange={(checked) => setInboundForm({ ...inboundForm, krisp_enabled: checked })}
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setInboundDialogOpen(false)}>
              Cancel
            </Button>
            <Button onClick={handleAddInbound} disabled={isCreatingInbound}>
              {isCreatingInbound && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
              Create Inbound
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </DashboardLayout>
  );
}
