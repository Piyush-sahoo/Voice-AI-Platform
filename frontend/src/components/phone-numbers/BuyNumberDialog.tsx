import { useState } from "react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { PhoneNumber, countryOptions, availableNumbers } from "@/data/mockPhoneNumbers";
import { Phone, Check } from "lucide-react";
import { toast } from "sonner";

interface BuyNumberDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onPurchase: (number: Partial<PhoneNumber>) => void;
}

export function BuyNumberDialog({
  open,
  onOpenChange,
  onPurchase,
}: BuyNumberDialogProps) {
  const [selectedCountry, setSelectedCountry] = useState("US");
  const [selectedType, setSelectedType] = useState<"local" | "toll-free">("local");
  const [selectedNumber, setSelectedNumber] = useState<string | null>(null);
  const [step, setStep] = useState<"select" | "confirm">("select");

  const filteredNumbers = availableNumbers.filter((n) => n.type === selectedType);

  const handlePurchase = () => {
    if (!selectedNumber) {
      toast.error("Please select a phone number");
      return;
    }

    const numberData = filteredNumbers.find((n) => n.number === selectedNumber);
    const country = countryOptions.find((c) => c.code === selectedCountry);

    onPurchase({
      number: selectedNumber,
      country: country?.name || "United States",
      countryCode: selectedCountry,
      type: selectedType,
      monthlyPrice: numberData?.price || 2.99,
      status: "pending",
      recordingEnabled: false,
      voicemailEnabled: false,
    });

    // Reset
    setStep("select");
    setSelectedNumber(null);
    onOpenChange(false);
  };

  const handleClose = () => {
    setStep("select");
    setSelectedNumber(null);
    onOpenChange(false);
  };

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Buy Phone Number</DialogTitle>
          <DialogDescription>
            {step === "select"
              ? "Choose a country and number type"
              : "Confirm your purchase"}
          </DialogDescription>
        </DialogHeader>

        {step === "select" ? (
          <div className="space-y-6">
            <div className="space-y-2">
              <Label>Country</Label>
              <Select value={selectedCountry} onValueChange={setSelectedCountry}>
                <SelectTrigger>
                  <SelectValue placeholder="Select country" />
                </SelectTrigger>
                <SelectContent>
                  {countryOptions.map((country) => (
                    <SelectItem key={country.code} value={country.code}>
                      <span className="flex items-center gap-2">
                        <span>{country.flag}</span>
                        <span>{country.name}</span>
                      </span>
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-3">
              <Label>Number Type</Label>
              <RadioGroup
                value={selectedType}
                onValueChange={(v) => {
                  setSelectedType(v as "local" | "toll-free");
                  setSelectedNumber(null);
                }}
                className="grid grid-cols-2 gap-3"
              >
                <label
                  className={`flex cursor-pointer flex-col rounded-lg border p-4 transition-colors ${
                    selectedType === "local"
                      ? "border-primary bg-primary/10"
                      : "border-border hover:bg-accent"
                  }`}
                >
                  <RadioGroupItem value="local" className="sr-only" />
                  <span className="font-medium">Local</span>
                  <span className="text-sm text-muted-foreground">$2.99/mo</span>
                </label>
                <label
                  className={`flex cursor-pointer flex-col rounded-lg border p-4 transition-colors ${
                    selectedType === "toll-free"
                      ? "border-primary bg-primary/10"
                      : "border-border hover:bg-accent"
                  }`}
                >
                  <RadioGroupItem value="toll-free" className="sr-only" />
                  <span className="font-medium">Toll-Free</span>
                  <span className="text-sm text-muted-foreground">$9.99/mo</span>
                </label>
              </RadioGroup>
            </div>

            <div className="space-y-3">
              <Label>Available Numbers</Label>
              <div className="space-y-2">
                {filteredNumbers.map((num) => (
                  <button
                    key={num.number}
                    onClick={() => setSelectedNumber(num.number)}
                    className={`flex w-full items-center justify-between rounded-lg border p-3 text-left transition-colors ${
                      selectedNumber === num.number
                        ? "border-primary bg-primary/10"
                        : "border-border hover:bg-accent"
                    }`}
                  >
                    <div className="flex items-center gap-3">
                      <Phone className="h-4 w-4 text-muted-foreground" />
                      <span className="font-mono">{num.number}</span>
                    </div>
                    {selectedNumber === num.number && (
                      <Check className="h-4 w-4 text-primary" />
                    )}
                  </button>
                ))}
              </div>
            </div>

            <div className="flex gap-3">
              <Button variant="outline" className="flex-1" onClick={handleClose}>
                Cancel
              </Button>
              <Button
                className="flex-1"
                onClick={() => setStep("confirm")}
                disabled={!selectedNumber}
              >
                Continue
              </Button>
            </div>
          </div>
        ) : (
          <div className="space-y-6">
            <div className="rounded-lg border border-border bg-muted/50 p-4">
              <div className="flex items-center gap-4">
                <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-primary/10">
                  <Phone className="h-6 w-6 text-primary" />
                </div>
                <div>
                  <p className="font-mono text-lg font-medium">{selectedNumber}</p>
                  <div className="flex items-center gap-2">
                    <Badge variant="secondary" className="text-xs">
                      {selectedType}
                    </Badge>
                    <span className="text-sm text-muted-foreground">
                      {countryOptions.find((c) => c.code === selectedCountry)?.name}
                    </span>
                  </div>
                </div>
              </div>
            </div>

            <div className="space-y-2 rounded-lg border border-border p-4">
              <div className="flex items-center justify-between">
                <span className="text-muted-foreground">Monthly fee</span>
                <span className="font-medium">
                  ${selectedType === "toll-free" ? "9.99" : "2.99"}
                </span>
              </div>
              <div className="flex items-center justify-between border-t border-border pt-2">
                <span className="font-medium">Total today</span>
                <span className="text-lg font-semibold text-primary">
                  ${selectedType === "toll-free" ? "9.99" : "2.99"}
                </span>
              </div>
            </div>

            <div className="flex gap-3">
              <Button variant="outline" className="flex-1" onClick={() => setStep("select")}>
                Back
              </Button>
              <Button className="flex-1" onClick={handlePurchase}>
                Confirm Purchase
              </Button>
            </div>
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}
