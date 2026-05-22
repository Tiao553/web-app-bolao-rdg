import { NextRequest, NextResponse } from 'next/server';
import { API_URL, buildProxyHeaders, readCsrfTokenFromRequest } from '../../../../../../lib/security';

export async function POST(req: NextRequest, { params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const form = await req.formData();
  const csrfToken = readCsrfTokenFromRequest(req, form);

  const res = await fetch(`${API_URL}/api/admin/users/${id}/moderation`, {
    method: 'PUT',
    headers: buildProxyHeaders(req, csrfToken, 'application/json'),
    body: JSON.stringify({ access_status: 'APPROVED' }),
  });

  if (!res.ok) {
    return NextResponse.redirect(new URL('/admin/users?error=approve_failed', req.url), 303);
  }
  return NextResponse.redirect(new URL('/admin/users', req.url));
}
