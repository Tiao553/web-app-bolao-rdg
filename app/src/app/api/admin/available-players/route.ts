import { NextRequest, NextResponse } from 'next/server';

const API_URL = process.env.API_BASE_URL || 'http://localhost:8000';

export async function GET(req: NextRequest) {
  const cookie = req.headers.get('cookie') ?? '';
  const res = await fetch(`${API_URL}/api/member/available-players`, {
    headers: { cookie },
  });
  const data = await res.json().catch(() => []);
  return NextResponse.json(data, { status: res.status });
}
