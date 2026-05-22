import { NextRequest, NextResponse } from 'next/server';
import { API_URL, buildProxyHeaders, readCsrfTokenFromRequest } from '../../../../../lib/security';

export async function POST(req: NextRequest) {
  const form = await req.formData();
  const csrfToken = readCsrfTokenFromRequest(req, form);

  const name = (form.get('name') as string | null)?.trim() || 'default';
  const prediction_close_at = form.get('prediction_close_at') as string | null;
  const explore_release_at = form.get('explore_release_at') as string | null;

  if (!prediction_close_at || !explore_release_at) {
    return NextResponse.redirect(new URL('/admin/settings?error=missing_dates', req.url));
  }

  const res = await fetch(`${API_URL}/api/admin/competition/window`, {
    method: 'PUT',
    headers: buildProxyHeaders(req, csrfToken, 'application/json'),
    body: JSON.stringify({
      name,
      prediction_close_at: new Date(prediction_close_at).toISOString(),
      explore_release_at: new Date(explore_release_at).toISOString(),
    }),
  });

  if (!res.ok) {
    return NextResponse.redirect(new URL('/admin/settings?error=save_failed', req.url));
  }

  return NextResponse.redirect(new URL('/admin/settings?saved=1', req.url));
}
