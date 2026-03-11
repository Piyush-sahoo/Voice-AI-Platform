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
import { Checkbox } from "@/components/ui/checkbox";
import { Phone, Server } from "lucide-react";
import { toast } from "sonner";

interface SIPConfig {
  name: string;
  from_number: string;
  is_default: boolean;
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
    from_number: "",
    is_default: false,
  });

  const handleSubmit = () => {
    if (!formData.name.trim()) {
      toast.error("Please enter a configuration name");
      return;
    }
    if (!formData.from_number.trim()) {
      toast.error("Please enter a phone number");
      return;
    }

    onAdd(formData);

    // Reset form
    setFormData({
      name: "",
      from_number: "",
      is_default: false,
    });
    onOpenChange(false);
  };

  const handleClose = () => {
    setFormData({
      name: "",
      from_number: "",
      is_default: false,
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
            SIP provider credentials are configured in Workspace Integrations. This form only creates a trunk configuration.
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
            <Label htmlFor="fromNumber" className="text-foreground">Phone Number (Caller ID) *</Label>
            <div className="relative">
              <Phone className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
              <Input
                id="fromNumber"
                value={formData.from_number}
                onChange={(e) => setFormData({ ...formData, from_number: e.target.value })}
                placeholder="+1 (555) 123-4567"
                className="bg-background border-border text-foreground pl-10"
              />
            </div>
          </div>

          <div className="flex items-center gap-2 pt-1">
            <Checkbox
              id="isDefault"
              checked={formData.is_default}
              onCheckedChange={(checked) => setFormData({ ...formData, is_default: Boolean(checked) })}
            />
            <Label htmlFor="isDefault" className="text-foreground">
              Set as default
            </Label>
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
