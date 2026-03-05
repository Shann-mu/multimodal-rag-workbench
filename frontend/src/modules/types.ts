export interface ContentBlock {
  type: 'text' | 'image' | 'audio';
  content: string; // text content or base64 data url
}

export interface Reference {
  id: number;
  text: string;
  source: string;
  page: number;
  chunk_id: number;
  source_info: string;
  document_id?: number;
}

export interface KnowledgeBase {
  id: number;
  name: string;
  description: string;
  is_default: boolean;
  created_at: string;
  updated_at: string;
}

export interface KnowledgeDocument {
  id: number;
  kb_id: number;
  filename: string;
  title: string;
  mime_type: string;
  sha256: string;
  page_count: number;
  created_at: string;
}

export interface Message {
  role: 'user' | 'assistant';
  content: string; // Display text
  content_blocks?: ContentBlock[]; // For sending to backend
  id?: string;
  timestamp?: string;
  references?: Reference[];
}

export interface StreamEvent {
  type: 'session' | 'content_delta' | 'message_complete' | 'error';
  session_id?: number;
  content?: string;
  full_content?: string;
  error?: string;
  timestamp?: string;
  references?: Reference[];
}

export interface ChatRequest {
  session_id?: number;
  content_blocks: ContentBlock[];
  history: Message[];
  image_file?: File;
  audio_file?: File;
  pdf_file?: File;
  kb_id?: number;
  document_ids?: number[];
}

export interface ChatSession {
  id: number;
  title: string;
  mode: string;
  is_default: boolean;
  created_at: string;
  updated_at: string;
}

export interface ChatMessageRecord {
  id: number;
  role: 'user' | 'assistant';
  content: string;
  content_blocks?: ContentBlock[] | null;
  references?: Reference[] | null;
  created_at: string;
}
