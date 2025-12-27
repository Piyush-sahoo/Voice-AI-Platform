export interface KnowledgeItem {
  id: string;
  name: string;
  type: "pdf" | "docx" | "txt" | "url" | "text";
  size: number; // in bytes
  tokenCount: number;
  assignedAgents: string[];
  status: "processing" | "ready" | "error";
  createdAt: string;
  updatedAt: string;
  lastSyncedAt?: string;
}

export const mockKnowledge: KnowledgeItem[] = [
  {
    id: "kb-1",
    name: "Product Documentation",
    type: "pdf",
    size: 2500000,
    tokenCount: 45000,
    assignedAgents: ["agent-1", "agent-2"],
    status: "ready",
    createdAt: "2024-01-10T10:00:00Z",
    updatedAt: "2024-01-15T14:30:00Z",
    lastSyncedAt: "2024-01-15T14:30:00Z",
  },
  {
    id: "kb-2",
    name: "FAQ Responses",
    type: "txt",
    size: 50000,
    tokenCount: 8500,
    assignedAgents: ["agent-1"],
    status: "ready",
    createdAt: "2024-01-08T09:00:00Z",
    updatedAt: "2024-01-12T11:20:00Z",
    lastSyncedAt: "2024-01-12T11:20:00Z",
  },
  {
    id: "kb-3",
    name: "Company Website",
    type: "url",
    size: 150000,
    tokenCount: 22000,
    assignedAgents: ["agent-2", "agent-3"],
    status: "ready",
    createdAt: "2024-01-05T16:00:00Z",
    updatedAt: "2024-01-18T08:45:00Z",
    lastSyncedAt: "2024-01-18T08:45:00Z",
  },
  {
    id: "kb-4",
    name: "Training Manual",
    type: "docx",
    size: 1200000,
    tokenCount: 0,
    assignedAgents: [],
    status: "processing",
    createdAt: "2024-01-20T10:30:00Z",
    updatedAt: "2024-01-20T10:30:00Z",
  },
];

export function formatFileSize(bytes: number): string {
  if (bytes === 0) return "0 B";
  const k = 1024;
  const sizes = ["B", "KB", "MB", "GB"];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + " " + sizes[i];
}

export function getFileTypeIcon(type: KnowledgeItem["type"]): string {
  switch (type) {
    case "pdf":
      return "FileText";
    case "docx":
      return "FileText";
    case "txt":
      return "FileText";
    case "url":
      return "Globe";
    case "text":
      return "AlignLeft";
    default:
      return "File";
  }
}
