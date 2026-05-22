import { NextRequest, NextResponse } from 'next/server';
import { API_URL, CSRF_COOKIE_NAME } from './app/src/lib/security';

function createCsrfToken(): string {
  return crypto.randomUUID().replace(/-/g, '');
}

function buildCsp(request: NextRequest): string {
  const directives = [
    "default-src 'self'",
    `script-src 'self' 'unsafe-inline'${process.env.NODE_ENV === 'development' ? " 'unsafe-eval'" : ''}`,
    "style-src 'self' 'unsafe-inline'",
    "img-src 'self' data: blob: https:",
    "font-src 'self' data: https:",
    `connect-src 'self' ${new URL(API_URL).origin}`,
    "object-src 'none'",
    "base-uri 'self'",
    "form-action 'self'",
    "frame-ancestors 'none'",
  ];
  if (request.nextUrl.protocol === 'https:') {
    directives.push('upgrade-insecure-requests');
  }
  return directives.join('; ');
}

function applySecurityHeaders(response: NextResponse, request: NextRequest) {
  response.headers.set('Content-Security-Policy', buildCsp(request));
  response.headers.set('Referrer-Policy', 'strict-origin-when-cross-origin');
  response.headers.set('X-Content-Type-Options', 'nosniff');
  response.headers.set('X-Frame-Options', 'DENY');
  response.headers.set('Permissions-Policy', 'camera=(), geolocation=(), microphone=()');
  if (process.env.NODE_ENV !== 'development' && request.nextUrl.protocol === 'https:') {
    response.headers.set('Strict-Transport-Security', 'max-age=31536000; includeSubDomains; preload');
  }
}

export function middleware(request: NextRequest) {
  const csrfToken = request.cookies.get(CSRF_COOKIE_NAME)?.value ?? createCsrfToken();
  const requestHeaders = new Headers(request.headers);
  requestHeaders.set('x-csrf-token', csrfToken);

  const response = NextResponse.next({
    request: {
      headers: requestHeaders,
    },
  });

  if (!request.cookies.get(CSRF_COOKIE_NAME)) {
    response.cookies.set(CSRF_COOKIE_NAME, csrfToken, {
      httpOnly: false,
      sameSite: 'lax',
      secure: process.env.NODE_ENV !== 'development',
      path: '/',
    });
  }

  applySecurityHeaders(response, request);
  return response;
}

export const config = {
  matcher: ['/((?!_next/static|_next/image|favicon.ico).*)'],
};
