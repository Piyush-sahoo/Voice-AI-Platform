export interface KnowledgeItem {
  id: string;
  name: string;
  type: "file" | "url" | "text";
  size: number;
  tokenCount: number;
  assignedAgents: string[];
  status: "processing" | "ready" | "error";
  createdAt: string;
  lastSyncedAt?: string;
  errorMessage?: string;
}

export interface KnowledgeDocumentApi {
  id: string;
  name: string;
  source_type: "file" | "url" | "text";
  file_size?: number;
  token_count?: number;
  assigned_assistant_ids?: string[];
  status: "processing" | "ready" | "error";
  created_at: string;
  last_synced_at?: string;
  error_message?: string;
}

export function toKnowledgeItem(doc: KnowledgeDocumentApi): KnowledgeItem {
  return {
    id: doc.id,
    name: doc.name,
    type: doc.source_type,
    size: doc.file_size || 0,
    tokenCount: doc.token_count || 0,
    assignedAgents: doc.assigned_assistant_ids || [],
    status: doc.status,
    createdAt: doc.created_at,
    lastSyncedAt: doc.last_synced_at,
    errorMessage: doc.error_message,
  };
}

export function formatFileSize(bytes: number): string {
  if (bytes === 0) return "0 B";
  const k = 1024;
  const sizes = ["B", "KB", "MB", "GB"];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + " " + sizes[i];
}
