import { NextRequest, NextResponse } from 'next/server';
import { API_URL, SESSION_COOKIE_NAME, buildProxyHeaders, readCsrfTokenFromRequest } from '../../../../lib/security';

export async function POST(req: NextRequest) {
  const formData = await req.formData();
  const csrfToken = readCsrfTokenFromRequest(req, formData);

  await fetch(`${API_URL}/api/auth/logout`, {
    method: 'POST',
    headers: buildProxyHeaders(req, csrfToken),
  }).catch(() => null);

  const res = NextResponse.redirect(new URL('/login', req.url), 303);
  res.cookies.delete(SESSION_COOKIE_NAME);
  return res;
}
