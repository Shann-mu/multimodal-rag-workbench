import type { KnowledgeBase, KnowledgeDocument } from './types';
import { getAccessToken } from './authToken';

const API_BASE_URL = '/api';

async function fetchAuthed<T>(path: string, init?: RequestInit): Promise<T> {
  const token = getAccessToken();
  const headers: Record<string, string> = {
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...(init?.headers as Record<string, string> | undefined),
  };

  const res = await fetch(`${API_BASE_URL}${path}`, { ...init, headers });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || `HTTP ${res.status}`);
  }
  return (await res.json()) as T;
}

export async function listKnowledgeBases(): Promise<KnowledgeBase[]> {
  return fetchAuthed<KnowledgeBase[]>('/kb', { method: 'GET' });
}

export async function createKnowledgeBase(payload: {
  name: string;
  description: string;
}): Promise<KnowledgeBase> {
  return fetchAuthed<KnowledgeBase>('/kb', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
}

export async function listKnowledgeDocuments(kbId: number): Promise<KnowledgeDocument[]> {
  return fetchAuthed<KnowledgeDocument[]>(`/kb/${kbId}/documents`, { method: 'GET' });
}

export async function uploadKnowledgeDocument(kbId: number, file: File): Promise<KnowledgeDocument> {
  const formData = new FormData();
  formData.append('pdf_file', file);

  return fetchAuthed<KnowledgeDocument>(`/kb/${kbId}/documents`, {
    method: 'POST',
    body: formData,
  });
}
