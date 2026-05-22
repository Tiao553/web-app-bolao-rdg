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
  const email = formData.get('email');
  const password = formData.get('password');
  const intent = formData.get('_intent') === 'admin' ? 'admin' : 'participant';

  const errorBase = intent === 'admin' ? '/admin/login' : '/login';

  let backendRes: Response;
  try {
    backendRes = await fetch(`${API_URL}/api/auth/login`, {
      method: 'POST',
      headers: buildProxyHeaders(req, csrfToken, 'application/json'),
      body: JSON.stringify({ email, password }),
    });
  } catch {
    return NextResponse.redirect(new URL(`${errorBase}?error=server_error`, req.url), 303);
  }

  if (!backendRes.ok) {
    const code = await backendRes.json().then((d) => getBackendErrorCode(d)).catch(() => 'unknown');
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

  const res = NextResponse.redirect(new URL(dest, req.url), 303);
  applySessionCookieFromBackend(res, backendRes, req);
  return res;
}
