import { NextRequest, NextResponse } from 'next/server';
import { API_URL, CSRF_COOKIE_NAME, isSecureRequest } from '../../../../lib/security';

export async function GET(req: NextRequest) {
  const existingCsrf = req.cookies.get(CSRF_COOKIE_NAME)?.value;
  if (existingCsrf) {
    return NextResponse.json({ ok: true });
  }

  let backendRes: Response;
  try {
    backendRes = await fetch(`${API_URL}/healthz`, {
      method: 'GET',
      headers: { accept: 'application/json' },
    });
  } catch {
    return NextResponse.json({ ok: false }, { status: 502 });
  }

  const res = NextResponse.json({ ok: true });
  const setCookie = backendRes.headers.get('set-cookie');
  if (setCookie) {
    const match = setCookie.match(new RegExp(`${CSRF_COOKIE_NAME}=([^;]+)`));
    if (match) {
      res.cookies.set(CSRF_COOKIE_NAME, match[1], {
        httpOnly: false,
        secure: isSecureRequest(req),
        sameSite: 'lax',
        path: '/',
      });
    }
  }
  return res;
}
