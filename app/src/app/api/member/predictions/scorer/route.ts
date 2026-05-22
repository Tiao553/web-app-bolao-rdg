import { NextRequest, NextResponse } from 'next/server';
import { API_URL, buildProxyHeaders, readCsrfTokenFromRequest } from '../../../../../lib/security';

export async function POST(req: NextRequest) {
  const form = await req.formData();
  const csrfToken = readCsrfTokenFromRequest(req, form);
  const scorerId = form.get('scorer');

  if (!scorerId) {
    return NextResponse.redirect(new URL('/initial-predictions?error=missing', req.url));
  }

  // Find player label from the players API
  const playersRes = await fetch(`${API_URL}/api/member/available-players`, {
    headers: buildProxyHeaders(req),
  });
  const players: Array<{ id: string; name: string }> = playersRes.ok ? await playersRes.json() : [];
  const player = players.find(p => p.id === scorerId);

  const res = await fetch(`${API_URL}/api/member/predictions/top-scorer`, {
    method: 'PUT',
    headers: buildProxyHeaders(req, csrfToken, 'application/json'),
    body: JSON.stringify({
      selection_key: String(scorerId),
      selection_label: player?.name ?? String(scorerId),
    }),
  });

  if (!res.ok) {
    return NextResponse.redirect(new URL('/initial-predictions?error=save', req.url));
  }

  return NextResponse.redirect(new URL('/initial-predictions?saved=scorer', req.url));
}
