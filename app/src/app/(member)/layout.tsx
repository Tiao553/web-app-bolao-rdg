import type { ReactNode } from 'react';
import { redirect } from 'next/navigation';
import { MemberShell } from '../../components/shell/member-shell';
import { fetchAppSession, isApprovedSession, resolveHomePath } from '../../lib/session';

export default async function MemberLayout({ children }: { children: ReactNode }) {
  const session = await fetchAppSession();
  if (!session.authenticated) redirect('/login');
  if (!isApprovedSession(session)) redirect(resolveHomePath(session));
  return <MemberShell session={session}>{children}</MemberShell>;
}
