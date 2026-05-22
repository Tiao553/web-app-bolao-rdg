import { NextRequest, NextResponse } from 'next/server';

const API_URL = process.env.API_BASE_URL || 'http://localhost:8000';
const COOKIE_NAME = 'bolao_session';

export async function POST(req: NextRequest) {
  const sessionCookie = req.cookies.get(COOKIE_NAME)?.value;

  await fetch(`${API_URL}/api/auth/logout`, {
    method: 'POST',
    headers: sessionCookie ? { cookie: `${COOKIE_NAME}=${sessionCookie}` } : {},
  }).catch(() => null);

  const res = NextResponse.redirect(new URL('/login', req.url), 303);
  res.cookies.delete(COOKIE_NAME);
  return res;
}
