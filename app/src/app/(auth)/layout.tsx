import type { ReactNode } from 'react';
import { redirect } from 'next/navigation';
import { fetchAppSession, resolveHomePath } from '../../lib/session';

export default async function AuthLayout({ children }: { children: ReactNode }) {
  const session = await fetchAppSession();

  if (session.authenticated) {
    redirect(resolveHomePath(session));
  }

  return children;
}
