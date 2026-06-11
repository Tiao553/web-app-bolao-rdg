import { NextRequest, NextResponse } from 'next/server';
import { API_URL, buildProxyHeaders, readCsrfTokenFromRequest } from '../../../../../lib/security';

export async function POST(req: NextRequest) {
  const csrfToken = readCsrfTokenFromRequest(req);
  const body = await req.json().catch(() => ({}));

  const res = await fetch(`${API_URL}/api/admin/sync/run`, {
    method: 'POST',
    headers: buildProxyHeaders(req, csrfToken, 'application/json'),
    body: JSON.stringify(body),
  });

  const data = await res.json().catch(() => ({}));
  return NextResponse.json(data, { status: res.status });
}
