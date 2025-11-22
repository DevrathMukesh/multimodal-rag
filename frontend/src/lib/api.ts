import { Document, Source, Message } from "@/types";

const API_BASE = import.meta.env.VITE_API_BASE || "http://localhost:8000";

// Debug: Log API base URL
console.log("🔧 API Configuration:");
console.log("  VITE_API_BASE (env):", import.meta.env.VITE_API_BASE);
console.log("  API_BASE (used):", API_BASE);
console.log("  Current origin:", window.location.origin);

export class ApiError extends Error {
  constructor(
    public status: number,
    message: string
  ) {
    super(message);
    this.name = "ApiError";
  }
}

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const errorText = await response.text().catch(() => "Unknown error");
    throw new ApiError(response.status, errorText);
  }
  return response.json();
}

export async function fetchDocuments(): Promise<{ documents: Document[] }> {
  const response = await fetch(`${API_BASE}/api/documents`);
  return handleResponse(response);
}

export async function deleteDocumentById(id: string): Promise<{ ok: boolean }> {
  const response = await fetch(`${API_BASE}/api/documents/${id}`, {
    method: "DELETE",
  });
  return handleResponse(response);
}

export async function uploadDocument(file: File): Promise<Document> {
  const formData = new FormData();
  formData.append("file", file);

  const response = await fetch(`${API_BASE}/api/upload`, {
    method: "POST",
    body: formData,
  });

  return handleResponse(response);
    }

export async function getUploadStatus(documentId: string): Promise<Document> {
  const response = await fetch(`${API_BASE}/api/upload/status/${documentId}`);
    return handleResponse(response);
}

export interface ChatRequest {
  question: string;
  sessionId: string;
  documentId?: string;
  includeImages?: boolean;
  stream?: boolean;
}

export interface ChatResponse {
  answer: string;
  sources: Source[];
}

export async function sendChatMessage(request: ChatRequest): Promise<ChatResponse> {
  const response = await fetch(`${API_BASE}/api/chat`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(request),
  });

  return handleResponse(response);
}

export async function getChatMessages(sessionId: string): Promise<Message[]> {
  const response = await fetch(`${API_BASE}/api/chat/messages/${sessionId}`);
  const data = await handleResponse(response);
  return (data.messages || []).map((msg: any) => ({
    id: msg.id,
    role: msg.role as "user" | "assistant",
    content: msg.content,
    sources: msg.sources || undefined,  // Include sources if available
    timestamp: msg.timestamp ? new Date(msg.timestamp) : new Date(),
  }));
}

export function buildStreamUrl(params: {
  question: string;
  sessionId: string;
  documentId?: string;
  includeImages?: boolean;
}): string {
  const base = API_BASE;
  const url = new URL(`${base}/api/chat/stream`);
  url.searchParams.set("question", params.question);
  url.searchParams.set("sessionId", params.sessionId);
  if (params.documentId) url.searchParams.set("documentId", params.documentId);
  if (params.includeImages !== undefined) url.searchParams.set("includeImages", String(params.includeImages));
  return url.toString();
}

// Generate a unique session ID
export function generateSessionId(): string {
  return `session-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
}

// Session storage helpers
const SESSION_KEY = "rag-chatbot-session-id";

export function getSessionId(): string {
  let sessionId = localStorage.getItem(SESSION_KEY);
  if (!sessionId) {
    sessionId = generateSessionId();
    localStorage.setItem(SESSION_KEY, sessionId);
  }
  return sessionId;
}

export function clearSession(): void {
  localStorage.removeItem(SESSION_KEY);
}

export function setSessionId(sessionId: string): void {
  localStorage.setItem(SESSION_KEY, sessionId);
}

export interface ChatSession {
  id: string;
  title: string;
  last_activity: string;
  created_at: string;
  message_count: number;
}

export async function fetchChatSessions(): Promise<{ sessions: ChatSession[] }> {
  const response = await fetch(`${API_BASE}/api/chat/sessions`);
  return handleResponse(response);
}

export async function deleteChatSession(sessionId: string): Promise<{ ok: boolean; message: string }> {
  const response = await fetch(`${API_BASE}/api/chat/sessions/${sessionId}`, {
    method: "DELETE",
  });
  return handleResponse(response);
}
