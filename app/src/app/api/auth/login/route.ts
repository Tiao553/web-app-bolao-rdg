import { NextRequest, NextResponse } from 'next/server';

const API_URL = process.env.API_BASE_URL || 'http://localhost:8000';
const COOKIE_NAME = 'bolao_session';

function extractCookieValue(setCookieHeader: string | null): string | null {
  if (!setCookieHeader) return null;
  const match = setCookieHeader.match(new RegExp(`${COOKIE_NAME}=([^;]+)`));
  return match?.[1] ?? null;
}

function cookieMaxAge(setCookieHeader: string | null): number | undefined {
  if (!setCookieHeader) return undefined;
  const match = setCookieHeader.match(/Expires=([^;]+)/i);
  if (!match) return undefined;
  const ms = Date.parse(match[1]) - Date.now();
  return ms > 0 ? Math.floor(ms / 1000) : undefined;
}

export async function POST(req: NextRequest) {
  const formData = await req.formData();
  const email = formData.get('email');
  const password = formData.get('password');
  const intent = formData.get('_intent') === 'admin' ? 'admin' : 'participant';

  const errorBase = intent === 'admin' ? '/admin/login' : '/login';

  let backendRes: Response;
  try {
    backendRes = await fetch(`${API_URL}/api/auth/login`, {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify({ email, password }),
    });
  } catch {
    return NextResponse.redirect(new URL(`${errorBase}?error=server_error`, req.url), 303);
  }

  if (!backendRes.ok) {
    const code = await backendRes.json().then((d) => d?.error?.code ?? d?.code ?? 'unknown').catch(() => 'unknown');
    return NextResponse.redirect(new URL(`${errorBase}?error=${code}`, req.url), 303);
  }

  const session = await backendRes.json();
  const isAdmin: boolean = session?.user?.isAdmin === true;
  const isApproved: boolean = session?.user?.accessStatus === 'APPROVED';

  let dest: string;
  if (intent === 'admin') {
    dest = isAdmin ? '/admin/dashboard' : `${errorBase}?error=not_admin`;
  } else {
    dest = isApproved ? '/dashboard' : '/waiting';
  }

  const setCookieHeader = backendRes.headers.get('set-cookie');
  const tokenValue = extractCookieValue(setCookieHeader);

  const res = NextResponse.redirect(new URL(dest, req.url), 303);

  if (tokenValue) {
    res.cookies.set(COOKIE_NAME, tokenValue, {
      httpOnly: true,
      secure: false,
      sameSite: 'lax',
      path: '/',
      maxAge: cookieMaxAge(setCookieHeader),
    });
  }

  return res;
}
