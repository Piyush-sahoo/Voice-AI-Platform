import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

export interface TelephonyFormState {
  sip_domain: string;
  sip_username: string;
  sip_password: string;
  outbound_number: string;
  sipPasswordConfigured: boolean;
}

interface TelephonyStepProps {
  data: TelephonyFormState;
  onChange: (update: Partial<TelephonyFormState>) => void;
}

export function TelephonyStep({ data, onChange }: TelephonyStepProps) {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-semibold text-foreground">Telephony Configuration</h2>
        <p className="mt-1 text-sm text-muted-foreground">
          Connect your SIP provider (e.g. Vobiz) so the platform can place and receive phone calls on your behalf.
        </p>
      </div>

      <div className="space-y-4">
        <div className="space-y-2">
          <Label htmlFor="sip-domain">SIP Domain *</Label>
          <Input
            id="sip-domain"
            value={data.sip_domain}
            onChange={(e) => onChange({ sip_domain: e.target.value })}
            placeholder="e.g., abc123.sip.vobiz.ai"
            className="bg-background border-border text-foreground"
          />
        </div>

        <div className="space-y-2">
          <Label htmlFor="sip-username">SIP Username *</Label>
          <Input
            id="sip-username"
            value={data.sip_username}
            onChange={(e) => onChange({ sip_username: e.target.value })}
            placeholder="Your SIP username"
            className="bg-background border-border text-foreground"
          />
        </div>

        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <Label htmlFor="sip-password">SIP Password</Label>
            {data.sipPasswordConfigured && (
              <span className="text-xs text-emerald-400">Configured ✓</span>
            )}
          </div>
          <Input
            id="sip-password"
            type="password"
            value={data.sip_password}
            onChange={(e) => onChange({ sip_password: e.target.value, sipPasswordConfigured: false })}
            placeholder={data.sipPasswordConfigured ? "Enter to update existing password" : "Enter SIP password"}
            className="bg-background border-border text-foreground"
          />
        </div>

        <div className="space-y-2">
          <Label htmlFor="outbound-number">Outbound Phone Number</Label>
          <Input
            id="outbound-number"
            value={data.outbound_number}
            onChange={(e) => onChange({ outbound_number: e.target.value })}
            placeholder="e.g., +1 (555) 123-4567"
            className="bg-background border-border text-foreground"
          />
        </div>
      </div>

      <p className="text-xs text-muted-foreground">
        The outbound phone number will be used as your caller ID when placing outbound calls through your SIP trunk.
      </p>
    </div>
  );
}

