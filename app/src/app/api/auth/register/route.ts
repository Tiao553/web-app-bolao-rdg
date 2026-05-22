import { NextRequest, NextResponse } from 'next/server';
import {
  API_URL,
  applySessionCookieFromBackend,
  buildProxyHeaders,
  getBackendErrorCode,
  readCsrfTokenFromRequest,
} from '../../../../lib/security';

export async function POST(req: NextRequest) {
  const formData = await req.formData();
  const csrfToken = readCsrfTokenFromRequest(req, formData);
  const name = formData.get('name');
  const email = formData.get('email');
  const password = formData.get('password');

  let backendRes: Response;
  try {
    backendRes = await fetch(`${API_URL}/api/auth/register`, {
      method: 'POST',
      headers: buildProxyHeaders(req, csrfToken, 'application/json'),
      body: JSON.stringify({ full_name: name, email, password }),
    });
  } catch {
    return NextResponse.redirect(new URL('/create-account?error=server_error', req.url), 303);
  }

  if (!backendRes.ok) {
    const code = await backendRes.json().then((d) => getBackendErrorCode(d)).catch(() => 'unknown');
    return NextResponse.redirect(new URL(`/create-account?error=${code}`, req.url), 303);
  }

  const session = await backendRes.json();
  const dest = session?.user?.accessStatus === 'APPROVED'
    ? session?.user?.isAdmin
      ? '/admin/dashboard'
      : '/dashboard'
    : '/waiting';

  const res = NextResponse.redirect(new URL(dest, req.url), 303);
  applySessionCookieFromBackend(res, backendRes, req);
  return res;
}
