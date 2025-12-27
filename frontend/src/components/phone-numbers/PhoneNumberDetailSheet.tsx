import { useState, useEffect } from "react";
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Switch } from "@/components/ui/switch";
import { Label } from "@/components/ui/label";
import { Separator } from "@/components/ui/separator";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { PhoneNumber, countryOptions } from "@/data/mockPhoneNumbers";
import { mockAgents } from "@/data/mockAgents";
import { Phone, Trash2, Bot } from "lucide-react";
import { toast } from "sonner";

interface PhoneNumberDetailSheetProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  phoneNumber: PhoneNumber | null;
  onUpdate: (id: string, updates: Partial<PhoneNumber>) => void;
  onDelete: (id: string) => void;
}

export function PhoneNumberDetailSheet({
  open,
  onOpenChange,
  phoneNumber,
  onUpdate,
  onDelete,
}: PhoneNumberDetailSheetProps) {
  const [assignedAgent, setAssignedAgent] = useState<string>("");
  const [recordingEnabled, setRecordingEnabled] = useState(false);
  const [voicemailEnabled, setVoicemailEnabled] = useState(false);

  useEffect(() => {
    if (phoneNumber) {
      setAssignedAgent(phoneNumber.assignedAgentId || "");
      setRecordingEnabled(phoneNumber.recordingEnabled);
      setVoicemailEnabled(phoneNumber.voicemailEnabled);
    }
  }, [phoneNumber]);

  if (!phoneNumber) return null;

  const country = countryOptions.find((c) => c.code === phoneNumber.countryCode);

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

  const handleSave = () => {
    onUpdate(phoneNumber.id, {
      assignedAgentId: assignedAgent || undefined,
      recordingEnabled,
      voicemailEnabled,
    });
    toast.success("Phone number updated");
    onOpenChange(false);
  };

  const handleDelete = () => {
    onDelete(phoneNumber.id);
    toast.success("Phone number deleted");
    onOpenChange(false);
  };

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent className="w-full sm:max-w-md">
        <SheetHeader>
          <SheetTitle className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10">
              <Phone className="h-5 w-5 text-primary" />
            </div>
            <span className="font-mono">{phoneNumber.number}</span>
          </SheetTitle>
          <SheetDescription>Phone number settings</SheetDescription>
        </SheetHeader>

        <div className="mt-6 space-y-6">
          {/* Status & Info */}
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <span className="text-sm text-muted-foreground">Status</span>
              <Badge variant="outline" className={getStatusColor(phoneNumber.status)}>
                {phoneNumber.status}
              </Badge>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-muted-foreground">Country</span>
              <span className="flex items-center gap-2 text-sm font-medium">
                <span>{country?.flag}</span>
                {phoneNumber.country}
              </span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-muted-foreground">Type</span>
              <Badge variant="secondary" className="capitalize">
                {phoneNumber.type}
              </Badge>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-muted-foreground">Monthly Price</span>
              <span className="text-sm font-medium">${phoneNumber.monthlyPrice}/mo</span>
            </div>
          </div>

          <Separator />

          {/* Agent Assignment */}
          <div className="space-y-3">
            <Label>Assigned Agent</Label>
            <Select value={assignedAgent} onValueChange={setAssignedAgent}>
              <SelectTrigger>
                <SelectValue placeholder="Select an agent" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="">No agent</SelectItem>
                {mockAgents.map((agent) => (
                  <SelectItem key={agent.id} value={agent.id}>
                    <span className="flex items-center gap-2">
                      <Bot className="h-4 w-4" />
                      {agent.name}
                    </span>
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <p className="text-xs text-muted-foreground">
              This agent will handle all calls to this number
            </p>
          </div>

          <Separator />

          {/* Settings */}
          <div className="space-y-4">
            <div className="flex items-center justify-between rounded-lg border border-border p-4">
              <div>
                <p className="font-medium">Call Recording</p>
                <p className="text-sm text-muted-foreground">
                  Record all conversations
                </p>
              </div>
              <Switch
                checked={recordingEnabled}
                onCheckedChange={setRecordingEnabled}
              />
            </div>

            <div className="flex items-center justify-between rounded-lg border border-border p-4">
              <div>
                <p className="font-medium">Voicemail</p>
                <p className="text-sm text-muted-foreground">
                  Enable voicemail when agent unavailable
                </p>
              </div>
              <Switch
                checked={voicemailEnabled}
                onCheckedChange={setVoicemailEnabled}
              />
            </div>
          </div>

          <Separator />

          {/* Actions */}
          <div className="space-y-3">
            <Button className="w-full" onClick={handleSave}>
              Save Changes
            </Button>
            <Button
              variant="outline"
              className="w-full justify-start gap-2 text-destructive hover:bg-destructive/10 hover:text-destructive"
              onClick={handleDelete}
            >
              <Trash2 className="h-4 w-4" />
              Release Number
            </Button>
          </div>
        </div>
      </SheetContent>
    </Sheet>
  );
}
