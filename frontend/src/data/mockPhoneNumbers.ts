export interface PhoneNumber {
  id: string;
  number: string;
  country: string;
  countryCode: string;
  type: "local" | "toll-free";
  assignedAgentId?: string;
  status: "active" | "inactive" | "pending";
  monthlyPrice: number;
  recordingEnabled: boolean;
  businessHours?: {
    start: string;
    end: string;
    timezone: string;
  };
  voicemailEnabled: boolean;
  createdAt: string;
  updatedAt: string;
}

export const countryOptions = [
  { code: "US", name: "United States", flag: "🇺🇸" },
  { code: "GB", name: "United Kingdom", flag: "🇬🇧" },
  { code: "CA", name: "Canada", flag: "🇨🇦" },
  { code: "AU", name: "Australia", flag: "🇦🇺" },
  { code: "DE", name: "Germany", flag: "🇩🇪" },
  { code: "FR", name: "France", flag: "🇫🇷" },
];

export const mockPhoneNumbers: PhoneNumber[] = [
  {
    id: "phone-1",
    number: "+1 (555) 123-4567",
    country: "United States",
    countryCode: "US",
    type: "local",
    assignedAgentId: "agent-1",
    status: "active",
    monthlyPrice: 2.99,
    recordingEnabled: true,
    businessHours: {
      start: "09:00",
      end: "17:00",
      timezone: "America/New_York",
    },
    voicemailEnabled: true,
    createdAt: "2024-01-05T10:00:00Z",
    updatedAt: "2024-01-15T14:30:00Z",
  },
  {
    id: "phone-2",
    number: "+1 (800) 555-0199",
    country: "United States",
    countryCode: "US",
    type: "toll-free",
    assignedAgentId: "agent-2",
    status: "active",
    monthlyPrice: 9.99,
    recordingEnabled: true,
    voicemailEnabled: false,
    createdAt: "2024-01-08T09:00:00Z",
    updatedAt: "2024-01-12T11:20:00Z",
  },
  {
    id: "phone-3",
    number: "+44 20 7946 0958",
    country: "United Kingdom",
    countryCode: "GB",
    type: "local",
    status: "inactive",
    monthlyPrice: 3.99,
    recordingEnabled: false,
    voicemailEnabled: true,
    createdAt: "2024-01-10T16:00:00Z",
    updatedAt: "2024-01-10T16:00:00Z",
  },
];

export const availableNumbers = [
  { number: "+1 (555) 234-5678", type: "local" as const, price: 2.99 },
  { number: "+1 (555) 345-6789", type: "local" as const, price: 2.99 },
  { number: "+1 (800) 555-0123", type: "toll-free" as const, price: 9.99 },
  { number: "+1 (888) 555-0456", type: "toll-free" as const, price: 9.99 },
];
