import { cookies, headers } from 'next/headers';
import { NextRequest, NextResponse } from 'next/server';

export const API_URL = process.env.API_BASE_URL || 'http://localhost:8000';
export const SESSION_COOKIE_NAME = 'bolao_session';
export const CSRF_COOKIE_NAME = 'bolao_csrf';
export const CSRF_HEADER_NAME = 'x-csrf-token';

export function isSecureRequest(req?: NextRequest): boolean {
  if (process.env.NODE_ENV !== 'development') return true;
  if (!req) return false;
  return req.headers.get('x-forwarded-proto') === 'https' || req.nextUrl.protocol === 'https:';
}

export function extractCookieValue(setCookieHeader: string | null, cookieName: string): string | null {
  if (!setCookieHeader) return null;
  const match = setCookieHeader.match(new RegExp(`${cookieName}=([^;]+)`));
  return match?.[1] ?? null;
}

export function cookieMaxAge(setCookieHeader: string | null): number | undefined {
  if (!setCookieHeader) return undefined;
  const maxAgeMatch = setCookieHeader.match(/Max-Age=(\d+)/i);
  if (maxAgeMatch) return Number(maxAgeMatch[1]);
  const expiresMatch = setCookieHeader.match(/Expires=([^;]+)/i);
  if (!expiresMatch) return undefined;
  const ms = Date.parse(expiresMatch[1]) - Date.now();
  return ms > 0 ? Math.floor(ms / 1000) : undefined;
}

export function readCsrfTokenFromRequest(req: NextRequest, formData?: FormData): string | null {
  const headerToken = req.headers.get(CSRF_HEADER_NAME);
  if (headerToken) return headerToken;
  const formToken = formData?.get('csrf_token');
  return typeof formToken === 'string' && formToken.trim() ? formToken.trim() : null;
}

export function buildProxyHeaders(req: NextRequest, csrfToken?: string | null, contentType?: string): Headers {
  const outbound = new Headers();
  const cookie = req.headers.get('cookie');
  if (cookie) outbound.set('cookie', cookie);
  if (csrfToken) outbound.set(CSRF_HEADER_NAME, csrfToken);
  if (contentType) outbound.set('content-type', contentType);
  outbound.set('accept', 'application/json');
  return outbound;
}

export async function getServerCsrfToken(): Promise<string> {
  const headerStore = await headers();
  const headerToken = headerStore.get(CSRF_HEADER_NAME);
  if (headerToken) return headerToken;
  const cookieStore = await cookies();
  return cookieStore.get(CSRF_COOKIE_NAME)?.value ?? '';
}

export function getBrowserCsrfToken(): string {
  if (typeof document === 'undefined') return '';
  const prefix = `${CSRF_COOKIE_NAME}=`;
  const entry = document.cookie.split('; ').find((value) => value.startsWith(prefix));
  return entry ? decodeURIComponent(entry.slice(prefix.length)) : '';
}

export function applySessionCookieFromBackend(res: NextResponse, backendRes: Response, req: NextRequest): void {
  const setCookieHeader = backendRes.headers.get('set-cookie');
  const tokenValue = extractCookieValue(setCookieHeader, SESSION_COOKIE_NAME);
  if (!tokenValue) return;
  res.cookies.set(SESSION_COOKIE_NAME, tokenValue, {
    httpOnly: true,
    secure: isSecureRequest(req),
    sameSite: 'lax',
    path: '/',
    maxAge: cookieMaxAge(setCookieHeader),
  });
}

export function getBackendErrorCode(body: unknown): string {
  if (!body || typeof body !== 'object') return 'unknown';
  const candidate = body as Record<string, unknown>;
  const nested = candidate.error;
  if (nested && typeof nested === 'object' && typeof (nested as Record<string, unknown>).code === 'string') {
    return String((nested as Record<string, unknown>).code);
  }
  if (typeof candidate.code === 'string') return candidate.code;
  return 'unknown';
}
