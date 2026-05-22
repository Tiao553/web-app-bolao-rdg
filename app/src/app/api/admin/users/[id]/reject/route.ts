import { NextRequest, NextResponse } from 'next/server';

const API_URL = process.env.API_BASE_URL || 'http://localhost:8000';

export async function POST(req: NextRequest, { params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const cookie = req.headers.get('cookie') ?? '';

  await fetch(`${API_URL}/api/admin/users/${id}/moderation`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json', cookie },
    body: JSON.stringify({ access_status: 'REJECTED' }),
  });

  return NextResponse.redirect(new URL('/admin/users', req.url));
}
