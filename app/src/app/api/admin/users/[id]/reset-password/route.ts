import { NextRequest, NextResponse } from 'next/server';
import { API_URL, buildProxyHeaders, readCsrfTokenFromRequest } from '../../../../../../lib/security';

export async function POST(req: NextRequest, { params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const csrfToken = readCsrfTokenFromRequest(req);

  const res = await fetch(`${API_URL}/api/admin/users/${id}/reset-password`, {
    method: 'POST',
    headers: buildProxyHeaders(req, csrfToken),
  });

  const body = await res.json().catch(() => ({}));
  return NextResponse.json(body, { status: res.status });
}
