import { NextRequest, NextResponse } from 'next/server';
import { API_URL, buildProxyHeaders, readCsrfTokenFromRequest } from '../../../../../lib/security';

export async function POST(req: NextRequest) {
  const form = await req.formData();
  const csrfToken = readCsrfTokenFromRequest(req, form);
  const champion = form.get('champion');

  if (!champion) {
    return NextResponse.redirect(new URL('/initial-predictions?error=missing', req.url));
  }

  // Find team label from the teams API
  const teamsRes = await fetch(`${API_URL}/api/member/available-teams`, {
    headers: buildProxyHeaders(req),
  });
  const teams: Array<{ code: string; name: string }> = teamsRes.ok ? await teamsRes.json() : [];
  const team = teams.find(t => t.code === champion);

  const res = await fetch(`${API_URL}/api/member/predictions/champion`, {
    method: 'PUT',
    headers: buildProxyHeaders(req, csrfToken, 'application/json'),
    body: JSON.stringify({
      selection_key: champion,
      selection_label: team?.name ?? String(champion),
    }),
  });

  if (!res.ok) {
    return NextResponse.redirect(new URL('/initial-predictions?error=save', req.url));
  }

  return NextResponse.redirect(new URL('/initial-predictions?saved=champion', req.url));
}
