import { NextRequest, NextResponse } from 'next/server';

const API_URL = process.env.API_BASE_URL || 'http://localhost:8000';

export async function POST(req: NextRequest) {
  const cookie = req.headers.get('cookie') ?? '';
  const form = await req.formData();
  const champion = form.get('champion');

  if (!champion) {
    return NextResponse.redirect(new URL('/initial-predictions?error=missing', req.url));
  }

  // Find team label from the teams API
  const teamsRes = await fetch(`${API_URL}/api/member/available-teams`, {
    headers: { cookie },
  });
  const teams: Array<{ code: string; name: string }> = teamsRes.ok ? await teamsRes.json() : [];
  const team = teams.find(t => t.code === champion);

  const res = await fetch(`${API_URL}/api/member/predictions/champion`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json', cookie },
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
