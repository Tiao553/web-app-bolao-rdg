'use client';

import dynamic from 'next/dynamic';

const LoginForm = dynamic(
  () => import('./login-form').then((m) => ({ default: m.LoginForm })),
  { ssr: false }
);

export function LoginFormWrapper({ error }: { error?: string }) {
  return <LoginForm error={error} />;
}
