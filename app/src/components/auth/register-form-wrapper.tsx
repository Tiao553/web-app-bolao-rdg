'use client';

import dynamic from 'next/dynamic';

const RegisterForm = dynamic(
  () => import('./register-form').then((m) => ({ default: m.RegisterForm })),
  { ssr: false }
);

export function RegisterFormWrapper({ error }: { error?: string }) {
  return <RegisterForm error={error} />;
}
