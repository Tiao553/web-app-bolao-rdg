import { NextRequest, NextResponse } from 'next/server';

const API_URL = process.env.API_BASE_URL || 'http://localhost:8000';

export async function POST(req: NextRequest) {
  const cookie = req.headers.get('cookie') ?? '';
  const form = await req.formData();
  const roundKey = form.get('roundKey');
  const locked = form.get('locked') === 'true';

  const res = await fetch(`${API_URL}/api/admin/phase-lock`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', cookie },
    body: JSON.stringify({ roundKey, locked }),
  });

  if (!res.ok) {
    return NextResponse.redirect(new URL('/admin/settings?error=lock', req.url));
  }

  return NextResponse.redirect(new URL('/admin/settings?saved=lock', req.url));
}
