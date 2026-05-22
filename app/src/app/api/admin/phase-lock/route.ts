import { NextRequest, NextResponse } from 'next/server';
import { API_URL, buildProxyHeaders, readCsrfTokenFromRequest } from '../../../../lib/security';

export async function POST(req: NextRequest) {
  const form = await req.formData();
  const csrfToken = readCsrfTokenFromRequest(req, form);
  const roundKey = form.get('roundKey');
  const locked = form.get('locked') === 'true';

  const res = await fetch(`${API_URL}/api/admin/phase-lock`, {
    method: 'POST',
    headers: buildProxyHeaders(req, csrfToken, 'application/json'),
    body: JSON.stringify({ roundKey, locked }),
  });

  if (!res.ok) {
    return NextResponse.redirect(new URL('/admin/settings?error=lock', req.url));
  }

  return NextResponse.redirect(new URL('/admin/settings?saved=lock', req.url));
}
