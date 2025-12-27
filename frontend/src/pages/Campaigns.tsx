import { useState, useEffect, useRef } from "react";
import { DashboardLayout } from "@/components/layout/DashboardLayout";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Textarea } from "@/components/ui/textarea";
import { Slider } from "@/components/ui/slider";
import {
    Table,
    TableBody,
    TableCell,
    TableHead,
    TableHeader,
    TableRow,
} from "@/components/ui/table";
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogHeader,
    DialogTitle,
    DialogFooter,
} from "@/components/ui/dialog";
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from "@/components/ui/select";
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
    Play,
    Pause,
    Trash2,
    Upload,
    Users,
    Clock,
    Bot,
    Loader2,
    Calendar,
    FileSpreadsheet,
    X,
} from "lucide-react";
import { toast } from "sonner";
import { campaignsApi, assistantsApi } from "@/lib/api";
import { format } from "date-fns";

interface Campaign {
    campaign_id: string;
    name: string;
    description: string | null;
    assistant_id: string;
    status: string;
    total_contacts: number;
    calls_completed: number;
    calls_answered: number;
    calls_failed: number;
    max_concurrent_calls: number;
    scheduled_at: string | null;
    started_at: string | null;
    created_at: string;
}

interface Assistant {
    assistant_id: string;
    name: string;
}

interface Contact {
    phone_number: string;
    name?: string;
    variables?: Record<string, string>;
}

export default function Campaigns() {
    const [campaigns, setCampaigns] = useState<Campaign[]>([]);
    const [assistants, setAssistants] = useState<Assistant[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [searchQuery, setSearchQuery] = useState("");
    const [createDialogOpen, setCreateDialogOpen] = useState(false);
    const [isSubmitting, setIsSubmitting] = useState(false);
    const fileInputRef = useRef<HTMLInputElement>(null);

    // Form state
    const [formData, setFormData] = useState({
        name: "",
        description: "",
        assistant_id: "",
        max_concurrent_calls: 1,
        scheduled_at: "",
    });
    const [contacts, setContacts] = useState<Contact[]>([]);
    const [csvFileName, setCsvFileName] = useState("");

    const fetchData = async () => {
        setIsLoading(true);
        try {
            const [campaignsData, assistantsData] = await Promise.all([
                campaignsApi.list(),
                assistantsApi.list(),
            ]);
            setCampaigns(campaignsData.campaigns as Campaign[]);
            setAssistants(assistantsData.assistants as Assistant[]);
        } catch (error) {
            toast.error("Failed to load data");
            console.error(error);
        } finally {
            setIsLoading(false);
        }
    };

    useEffect(() => {
        fetchData();
    }, []);

    const filteredCampaigns = campaigns.filter(
        (campaign) =>
            campaign.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
            campaign.description?.toLowerCase().includes(searchQuery.toLowerCase())
    );

    const handleCreateCampaign = () => {
        setFormData({
            name: "",
            description: "",
            assistant_id: "",
            max_concurrent_calls: 1,
            scheduled_at: "",
        });
        setContacts([]);
        setCsvFileName("");
        setCreateDialogOpen(true);
    };

    const handleCsvUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
        const file = event.target.files?.[0];
        if (!file) return;

        setCsvFileName(file.name);
        const reader = new FileReader();
        reader.onload = (e) => {
            const text = e.target?.result as string;
            const lines = text.split("\n").filter((line) => line.trim());
            const headers = lines[0].split(",").map((h) => h.trim().toLowerCase());

            const phoneIndex = headers.findIndex((h) =>
                h.includes("phone") || h.includes("number") || h.includes("mobile")
            );
            const nameIndex = headers.findIndex((h) =>
                h.includes("name") || h.includes("contact")
            );

            if (phoneIndex === -1) {
                toast.error("CSV must have a phone/number column");
                return;
            }

            const parsedContacts: Contact[] = [];
            for (let i = 1; i < lines.length; i++) {
                const values = lines[i].split(",").map((v) => v.trim());
                const phone = values[phoneIndex];
                if (phone) {
                    parsedContacts.push({
                        phone_number: phone.startsWith("+") ? phone : `+${phone}`,
                        name: nameIndex !== -1 ? values[nameIndex] : undefined,
                    });
                }
            }

            setContacts(parsedContacts);
            toast.success(`Loaded ${parsedContacts.length} contacts from CSV`);
        };
        reader.readAsText(file);
    };

    const handleSubmit = async () => {
        if (!formData.name) {
            toast.error("Campaign name is required");
            return;
        }
        if (!formData.assistant_id) {
            toast.error("Please select an agent");
            return;
        }
        if (contacts.length === 0) {
            toast.error("Please upload contacts or add at least one phone number");
            return;
        }

        setIsSubmitting(true);
        try {
            await campaignsApi.create({
                name: formData.name,
                description: formData.description || null,
                assistant_id: formData.assistant_id,
                contacts: contacts.map((c) => ({
                    phone_number: c.phone_number,
                    name: c.name,
                    variables: c.variables || {},
                })),
                max_concurrent_calls: formData.max_concurrent_calls,
            });
            toast.success("Campaign created successfully");
            setCreateDialogOpen(false);
            await fetchData();
        } catch (error) {
            toast.error("Failed to create campaign");
            console.error(error);
        } finally {
            setIsSubmitting(false);
        }
    };

    const handleStartCampaign = async (campaignId: string) => {
        try {
            await campaignsApi.start(campaignId);
            toast.success("Campaign started");
            await fetchData();
        } catch (error) {
            toast.error("Failed to start campaign");
        }
    };

    const handlePauseCampaign = async (campaignId: string) => {
        try {
            await campaignsApi.pause(campaignId);
            toast.success("Campaign paused");
            await fetchData();
        } catch (error) {
            toast.error("Failed to pause campaign");
        }
    };

    const handleDeleteCampaign = async (campaignId: string) => {
        try {
            await campaignsApi.delete(campaignId);
            toast.success("Campaign deleted");
            await fetchData();
        } catch (error) {
            toast.error("Failed to delete campaign");
        }
    };

    const getStatusColor = (status: string) => {
        switch (status) {
            case "running":
                return "bg-emerald-500/20 text-emerald-400 border-emerald-500/30";
            case "completed":
                return "bg-blue-500/20 text-blue-400 border-blue-500/30";
            case "paused":
                return "bg-amber-500/20 text-amber-400 border-amber-500/30";
            case "cancelled":
                return "bg-destructive/20 text-destructive border-destructive/30";
            case "draft":
            case "scheduled":
            default:
                return "bg-muted text-muted-foreground border-border";
        }
    };

    const addManualContact = () => {
        setContacts([...contacts, { phone_number: "", name: "" }]);
    };

    const updateContact = (index: number, field: keyof Contact, value: string) => {
        const updated = [...contacts];
        updated[index] = { ...updated[index], [field]: value };
        setContacts(updated);
    };

    const removeContact = (index: number) => {
        setContacts(contacts.filter((_, i) => i !== index));
    };

    return (
        <DashboardLayout>
            <div className="space-y-6">
                {/* Header */}
                <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
                    <div>
                        <h1 className="text-2xl font-semibold text-foreground">Campaigns</h1>
                        <p className="text-sm text-muted-foreground">
                            Create and manage batch calling campaigns
                        </p>
                    </div>
                    <Button onClick={handleCreateCampaign}>
                        <Plus className="mr-2 h-4 w-4" />
                        Create Campaign
                    </Button>
                </div>

                {/* Search */}
                <div className="relative max-w-sm">
                    <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                    <Input
                        placeholder="Search campaigns..."
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                        className="pl-10"
                    />
                </div>

                {/* Campaigns Table */}
                <div className="rounded-lg border border-border bg-card">
                    <Table>
                        <TableHeader>
                            <TableRow className="hover:bg-transparent border-border">
                                <TableHead className="text-muted-foreground">Campaign</TableHead>
                                <TableHead className="text-muted-foreground">Contacts</TableHead>
                                <TableHead className="text-muted-foreground">Progress</TableHead>
                                <TableHead className="text-muted-foreground">Status</TableHead>
                                <TableHead className="text-muted-foreground">Created</TableHead>
                                <TableHead className="w-12"></TableHead>
                            </TableRow>
                        </TableHeader>
                        <TableBody>
                            {isLoading ? (
                                <TableRow>
                                    <TableCell colSpan={6} className="h-32 text-center">
                                        <div className="flex flex-col items-center gap-2">
                                            <Loader2 className="h-8 w-8 text-muted-foreground animate-spin" />
                                            <p className="text-muted-foreground">Loading campaigns...</p>
                                        </div>
                                    </TableCell>
                                </TableRow>
                            ) : filteredCampaigns.length === 0 ? (
                                <TableRow>
                                    <TableCell colSpan={6} className="h-32 text-center">
                                        <div className="flex flex-col items-center gap-2">
                                            <Users className="h-8 w-8 text-muted-foreground" />
                                            <p className="text-muted-foreground">No campaigns found</p>
                                            <Button variant="outline" size="sm" onClick={handleCreateCampaign}>
                                                Create your first campaign
                                            </Button>
                                        </div>
                                    </TableCell>
                                </TableRow>
                            ) : (
                                filteredCampaigns.map((campaign) => (
                                    <TableRow key={campaign.campaign_id} className="border-border">
                                        <TableCell>
                                            <div>
                                                <p className="font-medium text-foreground">{campaign.name}</p>
                                                {campaign.description && (
                                                    <p className="text-sm text-muted-foreground line-clamp-1">
                                                        {campaign.description}
                                                    </p>
                                                )}
                                            </div>
                                        </TableCell>
                                        <TableCell>
                                            <div className="flex items-center gap-2">
                                                <Users className="h-4 w-4 text-muted-foreground" />
                                                <span className="text-foreground">{campaign.total_contacts}</span>
                                            </div>
                                        </TableCell>
                                        <TableCell>
                                            <div className="w-24">
                                                <div className="flex items-center justify-between text-sm mb-1">
                                                    <span className="text-muted-foreground">
                                                        {campaign.calls_completed}/{campaign.total_contacts}
                                                    </span>
                                                </div>
                                                <div className="h-2 bg-muted rounded-full overflow-hidden">
                                                    <div
                                                        className="h-full bg-primary transition-all"
                                                        style={{
                                                            width: `${(campaign.calls_completed / campaign.total_contacts) * 100}%`,
                                                        }}
                                                    />
                                                </div>
                                            </div>
                                        </TableCell>
                                        <TableCell>
                                            <Badge variant="outline" className={getStatusColor(campaign.status)}>
                                                {campaign.status}
                                            </Badge>
                                        </TableCell>
                                        <TableCell className="text-muted-foreground">
                                            {format(new Date(campaign.created_at), "MMM d, yyyy")}
                                        </TableCell>
                                        <TableCell>
                                            <DropdownMenu>
                                                <DropdownMenuTrigger asChild>
                                                    <Button variant="ghost" size="icon" className="h-8 w-8">
                                                        <MoreHorizontal className="h-4 w-4" />
                                                    </Button>
                                                </DropdownMenuTrigger>
                                                <DropdownMenuContent align="end">
                                                    {campaign.status === "draft" || campaign.status === "paused" ? (
                                                        <DropdownMenuItem onClick={() => handleStartCampaign(campaign.campaign_id)}>
                                                            <Play className="mr-2 h-4 w-4" />
                                                            Start Campaign
                                                        </DropdownMenuItem>
                                                    ) : campaign.status === "running" ? (
                                                        <DropdownMenuItem onClick={() => handlePauseCampaign(campaign.campaign_id)}>
                                                            <Pause className="mr-2 h-4 w-4" />
                                                            Pause
                                                        </DropdownMenuItem>
                                                    ) : null}
                                                    <DropdownMenuItem
                                                        className="text-destructive"
                                                        onClick={() => handleDeleteCampaign(campaign.campaign_id)}
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

            {/* Create Campaign Dialog */}
            <Dialog open={createDialogOpen} onOpenChange={setCreateDialogOpen}>
                <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
                    <DialogHeader>
                        <DialogTitle>Create New Campaign</DialogTitle>
                        <DialogDescription>
                            Set up a batch calling campaign with your contacts
                        </DialogDescription>
                    </DialogHeader>

                    <div className="space-y-6 py-4">
                        {/* Campaign Details */}
                        <div className="space-y-4">
                            <div className="space-y-2">
                                <Label htmlFor="name">Campaign Name *</Label>
                                <Input
                                    id="name"
                                    placeholder="e.g., Sales Outreach Q1"
                                    value={formData.name}
                                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                                />
                            </div>

                            <div className="space-y-2">
                                <Label htmlFor="description">Description</Label>
                                <Textarea
                                    id="description"
                                    placeholder="Brief description of this campaign..."
                                    value={formData.description}
                                    onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                                />
                            </div>
                        </div>

                        {/* Agent Selection */}
                        <div className="space-y-2">
                            <Label>Select Agent *</Label>
                            <Select
                                value={formData.assistant_id}
                                onValueChange={(value) => setFormData({ ...formData, assistant_id: value })}
                            >
                                <SelectTrigger>
                                    <SelectValue placeholder="Choose an agent for calls" />
                                </SelectTrigger>
                                <SelectContent>
                                    {assistants.map((agent) => (
                                        <SelectItem key={agent.assistant_id} value={agent.assistant_id}>
                                            <div className="flex items-center gap-2">
                                                <Bot className="h-4 w-4" />
                                                {agent.name}
                                            </div>
                                        </SelectItem>
                                    ))}
                                </SelectContent>
                            </Select>
                            {assistants.length === 0 && (
                                <p className="text-sm text-muted-foreground">
                                    No agents found. Create an agent first.
                                </p>
                            )}
                        </div>

                        {/* Concurrent Calls */}
                        <div className="space-y-3">
                            <div className="flex items-center justify-between">
                                <Label>Max Concurrent Calls</Label>
                                <span className="text-sm font-medium text-foreground">
                                    {formData.max_concurrent_calls}
                                </span>
                            </div>
                            <Slider
                                value={[formData.max_concurrent_calls]}
                                onValueChange={([value]) =>
                                    setFormData({ ...formData, max_concurrent_calls: value })
                                }
                                max={5}
                                min={1}
                                step={1}
                            />
                            <p className="text-xs text-muted-foreground">
                                How many calls to make simultaneously (1-5)
                            </p>
                        </div>

                        {/* CSV Upload */}
                        <div className="space-y-3">
                            <Label>Contacts</Label>
                            <div className="flex items-center gap-3">
                                <Button
                                    variant="outline"
                                    onClick={() => fileInputRef.current?.click()}
                                    className="gap-2"
                                >
                                    <Upload className="h-4 w-4" />
                                    Upload CSV
                                </Button>
                                <Button variant="ghost" onClick={addManualContact}>
                                    <Plus className="mr-2 h-4 w-4" />
                                    Add Manually
                                </Button>
                                <input
                                    ref={fileInputRef}
                                    type="file"
                                    accept=".csv"
                                    onChange={handleCsvUpload}
                                    className="hidden"
                                />
                            </div>
                            {csvFileName && (
                                <div className="flex items-center gap-2 text-sm text-muted-foreground">
                                    <FileSpreadsheet className="h-4 w-4" />
                                    {csvFileName} - {contacts.length} contacts loaded
                                </div>
                            )}
                        </div>

                        {/* Contacts List */}
                        {contacts.length > 0 && (
                            <div className="space-y-2 max-h-48 overflow-y-auto">
                                <Label>Contacts ({contacts.length})</Label>
                                {contacts.slice(0, 10).map((contact, index) => (
                                    <div key={index} className="flex items-center gap-2">
                                        <Input
                                            placeholder="Phone number"
                                            value={contact.phone_number}
                                            onChange={(e) => updateContact(index, "phone_number", e.target.value)}
                                            className="flex-1"
                                        />
                                        <Input
                                            placeholder="Name (optional)"
                                            value={contact.name || ""}
                                            onChange={(e) => updateContact(index, "name", e.target.value)}
                                            className="flex-1"
                                        />
                                        <Button
                                            variant="ghost"
                                            size="icon"
                                            onClick={() => removeContact(index)}
                                        >
                                            <X className="h-4 w-4" />
                                        </Button>
                                    </div>
                                ))}
                                {contacts.length > 10 && (
                                    <p className="text-sm text-muted-foreground text-center">
                                        ...and {contacts.length - 10} more contacts
                                    </p>
                                )}
                            </div>
                        )}

                        {/* Schedule (Optional) */}
                        <div className="space-y-2">
                            <Label htmlFor="schedule">Schedule (Optional)</Label>
                            <Input
                                id="schedule"
                                type="datetime-local"
                                value={formData.scheduled_at}
                                onChange={(e) => setFormData({ ...formData, scheduled_at: e.target.value })}
                            />
                            <p className="text-xs text-muted-foreground">
                                Leave empty to start manually, or set a time to auto-start
                            </p>
                        </div>
                    </div>

                    <DialogFooter>
                        <Button variant="outline" onClick={() => setCreateDialogOpen(false)}>
                            Cancel
                        </Button>
                        <Button onClick={handleSubmit} disabled={isSubmitting}>
                            {isSubmitting ? (
                                <>
                                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                                    Creating...
                                </>
                            ) : (
                                <>
                                    <Plus className="mr-2 h-4 w-4" />
                                    Create Campaign
                                </>
                            )}
                        </Button>
                    </DialogFooter>
                </DialogContent>
            </Dialog>
        </DashboardLayout>
    );
}
