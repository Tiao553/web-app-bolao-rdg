import { redirect } from 'next/navigation';
import { fetchAppSession, resolveHomePath } from '../lib/session';

export default async function HomePage() {
  const session = await fetchAppSession();
  redirect(resolveHomePath(session));
}
