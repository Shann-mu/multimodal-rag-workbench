import type { ChatMessageRecord, ChatSession } from './types';

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

export async function listSessions(): Promise<ChatSession[]> {
  return fetchAuthed<ChatSession[]>('/chat/sessions', { method: 'GET' });
}

export async function createSession(payload: {
  title: string;
  mode?: string;
  is_default?: boolean;
}): Promise<ChatSession> {
  return fetchAuthed<ChatSession>('/chat/sessions', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
}

export async function listMessages(sessionId: number, limit: number = 100): Promise<ChatMessageRecord[]> {
  return fetchAuthed<ChatMessageRecord[]>(`/chat/sessions/${sessionId}/messages?limit=${limit}`, { method: 'GET' });
}