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
import {
  Plus,
  Search,
  MoreHorizontal,
  Phone,
  Trash2,
  Settings,
  Bot,
  Server,
  Loader2,
} from "lucide-react";
import { AddSIPConfigDialog } from "@/components/phone-numbers/AddSIPConfigDialog";
import { toast } from "sonner";
import { phoneNumbersApi, sipConfigsApi, assistantsApi } from "@/lib/api";

interface PhoneNumber {
  id: string; // phone_id or sip_id
  number: string;
  type: "local" | "toll-free" | "mobile" | "sip";
  status: "active" | "inactive" | "pending";
  assigned_agent_id?: string;
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
        number: p.phone_number,
        type: "local", // default to local for bought numbers
        status: "active",
        assigned_agent_id: p.assistant_id,
        created_at: p.created_at,
      }));

      const mappedSips: PhoneNumber[] = (sipsData.sip_configs as any[]).map((s) => ({
        id: s.sip_id,
        number: s.phone_number || "SIP Endpoint",
        type: "sip",
        status: "active",
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
    (num.number || "").toLowerCase().includes(searchQuery.toLowerCase())
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

  const getStatusColor = (status: PhoneNumber["status"]) => {
    switch (status) {
      case "active":
        return "bg-emerald-500/20 text-emerald-400 border-emerald-500/30";
      case "inactive":
        return "bg-muted text-muted-foreground border-border";
      case "pending":
        return "bg-amber-500/20 text-amber-400 border-amber-500/30";
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
              Manage your SIP configurations and assign agents
            </p>
          </div>
          <Button onClick={() => setAddDialogOpen(true)}>
            <Plus className="mr-2 h-4 w-4" />
            Add SIP Configuration
          </Button>
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
                <TableHead className="text-muted-foreground">Type</TableHead>
                <TableHead className="text-muted-foreground">Assigned Agent</TableHead>
                <TableHead className="text-muted-foreground">Status</TableHead>
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
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => setAddDialogOpen(true)}
                      >
                        Add your first SIP configuration
                      </Button>
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
                        <span className="font-mono font-medium text-foreground">{num.number}</span>
                      </div>
                    </TableCell>
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
                      <Badge variant="outline" className={getStatusColor(num.status)}>
                        {num.status}
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
                            className="text-destructive"
                            onClick={(e) => {
                              e.stopPropagation();
                              handleDelete(num);
                            }}
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

      <AddSIPConfigDialog
        open={addDialogOpen}
        onOpenChange={setAddDialogOpen}
        onAdd={handleAddSIPConfig}
      />
    </DashboardLayout>
  );
}
