const TOKEN_KEY = 'access_token';

export function getAccessToken(): string {
  return localStorage.getItem(TOKEN_KEY) || '';
}

export function hasAccessToken(): boolean {
  return Boolean(localStorage.getItem(TOKEN_KEY));
}

export function setAccessToken(token: string): void {
  localStorage.setItem(TOKEN_KEY, token);
}

export function clearAccessToken(): void {
  localStorage.removeItem(TOKEN_KEY);
}