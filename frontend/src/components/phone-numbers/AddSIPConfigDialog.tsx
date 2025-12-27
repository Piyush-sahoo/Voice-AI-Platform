import { useState } from "react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Phone, Server } from "lucide-react";
import { toast } from "sonner";

interface SIPConfig {
  name: string;
  sipTerminalUri: string;
  username: string;
  password: string;
  phoneNumber: string;
}

interface AddSIPConfigDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onAdd: (config: SIPConfig) => void;
}

export function AddSIPConfigDialog({
  open,
  onOpenChange,
  onAdd,
}: AddSIPConfigDialogProps) {
  const [formData, setFormData] = useState<SIPConfig>({
    name: "",
    sipTerminalUri: "",
    username: "",
    password: "",
    phoneNumber: "",
  });

  const handleSubmit = () => {
    if (!formData.name.trim()) {
      toast.error("Please enter a configuration name");
      return;
    }
    if (!formData.sipTerminalUri.trim()) {
      toast.error("Please enter a SIP Terminal URI");
      return;
    }
    if (!formData.username.trim()) {
      toast.error("Please enter a username");
      return;
    }
    if (!formData.password.trim()) {
      toast.error("Please enter a password");
      return;
    }
    if (!formData.phoneNumber.trim()) {
      toast.error("Please enter a phone number");
      return;
    }

    onAdd(formData);

    // Reset form
    setFormData({
      name: "",
      sipTerminalUri: "",
      username: "",
      password: "",
      phoneNumber: "",
    });
    onOpenChange(false);
  };

  const handleClose = () => {
    setFormData({
      name: "",
      sipTerminalUri: "",
      username: "",
      password: "",
      phoneNumber: "",
    });
    onOpenChange(false);
  };

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2 text-foreground">
            <Server className="h-5 w-5 text-primary" />
            Add SIP Configuration
          </DialogTitle>
          <DialogDescription>
            Configure your SIP trunk connection details
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="name" className="text-foreground">Configuration Name *</Label>
            <Input
              id="name"
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              placeholder="e.g., Main Office Line"
              className="bg-background border-border text-foreground"
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="sipUri" className="text-foreground">SIP Terminal URI *</Label>
            <Input
              id="sipUri"
              value={formData.sipTerminalUri}
              onChange={(e) => setFormData({ ...formData, sipTerminalUri: e.target.value })}
              placeholder="sip:user@domain.com"
              className="bg-background border-border text-foreground"
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="username" className="text-foreground">Username *</Label>
            <Input
              id="username"
              value={formData.username}
              onChange={(e) => setFormData({ ...formData, username: e.target.value })}
              placeholder="Enter username"
              className="bg-background border-border text-foreground"
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="password" className="text-foreground">Password *</Label>
            <Input
              id="password"
              type="password"
              value={formData.password}
              onChange={(e) => setFormData({ ...formData, password: e.target.value })}
              placeholder="Enter password"
              className="bg-background border-border text-foreground"
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="phoneNumber" className="text-foreground">Phone Number *</Label>
            <div className="relative">
              <Phone className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
              <Input
                id="phoneNumber"
                value={formData.phoneNumber}
                onChange={(e) => setFormData({ ...formData, phoneNumber: e.target.value })}
                placeholder="+1 (555) 123-4567"
                className="bg-background border-border text-foreground pl-10"
              />
            </div>
          </div>

          <div className="flex gap-3 pt-4">
            <Button variant="outline" className="flex-1" onClick={handleClose}>
              Cancel
            </Button>
            <Button className="flex-1" onClick={handleSubmit}>
              Add Configuration
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}
