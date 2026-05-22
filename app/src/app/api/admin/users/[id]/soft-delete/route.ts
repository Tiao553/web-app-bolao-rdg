import { NextRequest, NextResponse } from 'next/server';
import { API_URL, buildProxyHeaders, readCsrfTokenFromRequest } from '../../../../../../lib/security';

export async function POST(req: NextRequest, { params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const form = await req.formData();
  const csrfToken = readCsrfTokenFromRequest(req, form);
  const scope = form.get('scope') === 'deleted' ? 'deleted' : 'active';

  const res = await fetch(`${API_URL}/api/admin/users/${id}/soft-delete`, {
    method: 'POST',
    headers: buildProxyHeaders(req, csrfToken),
  });

  const destination = scope === 'deleted' ? '/admin/users?scope=deleted' : '/admin/users';
  if (!res.ok) {
    return NextResponse.redirect(new URL(`${destination}${destination.includes('?') ? '&' : '?'}error=delete_failed`, req.url), 303);
  }
  return NextResponse.redirect(new URL(destination, req.url));
}
