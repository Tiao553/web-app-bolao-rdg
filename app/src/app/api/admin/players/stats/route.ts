import { NextRequest, NextResponse } from 'next/server';
import { API_URL, buildProxyHeaders, readCsrfTokenFromRequest } from '../../../../../lib/security';

export async function PUT(req: NextRequest) {
  const csrfToken = readCsrfTokenFromRequest(req);
  const body = await req.json();

  const res = await fetch(`${API_URL}/api/admin/players/stats`, {
    method: 'PUT',
    headers: buildProxyHeaders(req, csrfToken, 'application/json'),
    body: JSON.stringify(body),
  });

  const data = await res.json().catch(() => ({}));
  return NextResponse.json(data, { status: res.status });
}
