import { NextRequest, NextResponse } from 'next/server';
import { API_URL, buildProxyHeaders, readCsrfTokenFromRequest } from '../../../../../../lib/security';

export async function PUT(req: NextRequest, { params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const csrfToken = readCsrfTokenFromRequest(req);
  const body = await req.json();

  const res = await fetch(`${API_URL}/api/admin/matches/${id}/manual-override`, {
    method: 'PUT',
    headers: buildProxyHeaders(req, csrfToken, 'application/json'),
    body: JSON.stringify(body),
  });

  const data = await res.json().catch(() => ({}));
  return NextResponse.json(data, { status: res.status });
}

export async function DELETE(req: NextRequest, { params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const csrfToken = readCsrfTokenFromRequest(req);

  const res = await fetch(`${API_URL}/api/admin/matches/${id}`, {
    method: 'DELETE',
    headers: buildProxyHeaders(req, csrfToken),
  });

  if (res.status === 204 || res.status === 404) {
    return new NextResponse(null, { status: 204 });
  }
  const data = await res.json().catch(() => ({}));
  return NextResponse.json(data, { status: res.status });
}
