import { NextRequest, NextResponse } from 'next/server';
import { API_URL, buildProxyHeaders, readCsrfTokenFromRequest } from '../../../../../lib/security';

export async function POST(req: NextRequest) {
  const form = await req.formData();
  const csrfToken = readCsrfTokenFromRequest(req, form);

  const errors: string[] = [];
  const saves: Promise<Response>[] = [];

  for (const [key, value] of form.entries()) {
    // keys: home_{matchId} or away_{matchId}
    const homeMatch = /^home_(.+)$/.exec(key);
    if (!homeMatch) continue;
    const matchId = homeMatch[1];
    const homeGoals = parseInt(String(value), 10);
    const awayGoals = parseInt(String(form.get(`away_${matchId}`) ?? '0'), 10);

    if (isNaN(homeGoals) || isNaN(awayGoals)) continue;

    saves.push(
      fetch(`${API_URL}/api/member/predictions/matches/${matchId}`, {
        method: 'PUT',
        headers: buildProxyHeaders(req, csrfToken, 'application/json'),
        body: JSON.stringify({ home_goals: homeGoals, away_goals: awayGoals }),
      })
    );
  }

  const results = await Promise.all(saves);
  for (const r of results) {
    if (!r.ok) errors.push(await r.text());
  }

  const redirectUrl = new URL('/phase-predictions', req.url);
  if (errors.length) redirectUrl.searchParams.set('error', 'partial');
  else redirectUrl.searchParams.set('saved', '1');

  return NextResponse.redirect(redirectUrl);
}
