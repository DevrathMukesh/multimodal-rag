export interface Source {
  parent_id: string;
  type: "text" | "table" | "image";
  page_number?: number;
  source?: string;
  summary: string;
  score?: number;
  text?: string;
  table_html?: string;
  image_b64?: string;
}

export interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  sources?: Source[];
  timestamp: Date;
}

export interface Document {
  id: string;
  name: string;
  pages: number;
  status?: string; // processing, completed, failed
  progress?: number; // 0-100 percentage
  createdAt: string;
}

export interface ChatSettings {
  autoShowSources: boolean;
  includeImages: boolean;
  streamResponses: boolean;
}
