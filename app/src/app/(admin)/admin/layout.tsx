import type { ReactNode } from 'react';
import { redirect } from 'next/navigation';
import { AdminShell } from '../../../components/layout/admin-shell';
import { fetchAppSession } from '../../../lib/session';

export default async function AdminLayout({ children }: { children: ReactNode }) {
  const session = await fetchAppSession();

  if (!session.authenticated) {
    redirect('/login');
  }

  if (!session.isAdmin) {
    redirect('/dashboard');
  }

  return <AdminShell session={session}>{children}</AdminShell>;
}
