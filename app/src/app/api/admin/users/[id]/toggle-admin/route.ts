import { NextRequest, NextResponse } from 'next/server';
import { API_URL, buildProxyHeaders, readCsrfTokenFromRequest } from '../../../../../../lib/security';

export async function POST(req: NextRequest, { params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const form = await req.formData();
  const csrfToken = readCsrfTokenFromRequest(req, form);
  const is_admin = form.get('is_admin') === 'true';
  const access_status = form.get('access_status') as string;

  const res = await fetch(`${API_URL}/api/admin/users/${id}/moderation`, {
    method: 'PUT',
    headers: buildProxyHeaders(req, csrfToken, 'application/json'),
    body: JSON.stringify({ is_admin, access_status }),
  });

  if (!res.ok) {
    return NextResponse.redirect(new URL('/admin/users?error=toggle_admin_failed', req.url), 303);
  }
  return NextResponse.redirect(new URL('/admin/users', req.url));
}
