import { getAccessToken } from './authToken';

const API_BASE_URL = '/api';

export interface UserPublic {
  id: number;
  username: string;
  avatar_url?: string | null;
}

export const DEFAULT_AVATAR_URL =
  'data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 64 64"><circle cx="32" cy="32" r="32" fill="%23e5e7eb"/><circle cx="32" cy="24" r="12" fill="%239ca3af"/><path d="M10 58c4-12 16-18 22-18s18 6 22 18" fill="%239ca3af"/></svg>';

export interface TokenResponse {
  access_token: string;
  token_type: string;
}

async function fetchJson<T>(path: string, init: RequestInit): Promise<T> {
  const token = getAccessToken();
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...(init.headers as Record<string, string> | undefined),
  };

  const res = await fetch(`${API_BASE_URL}${path}`, { ...init, headers });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || `HTTP ${res.status}`);
  }
  return (await res.json()) as T;
}

export async function register(
  username: string,
  password: string,
  avatarUrl?: string | null
): Promise<UserPublic> {
  return fetchJson<UserPublic>('/auth/register', {
    method: 'POST',
    body: JSON.stringify({ username, password, avatar_url: avatarUrl ?? null }),
  });
}

export async function login(username: string, password: string): Promise<TokenResponse> {
  return fetchJson<TokenResponse>('/auth/login', {
    method: 'POST',
    body: JSON.stringify({ username, password }),
  });
}

export async function me(): Promise<UserPublic> {
  return fetchJson<UserPublic>('/auth/me', { method: 'GET' });
}