import type { ReactNode } from 'react';
import './globals.css';

export const metadata = { title: 'Copa RDG — Bolão Oficial', description: 'Bolão oficial da Copa do Mundo 2026' };

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="pt-BR" suppressHydrationWarning>
      <body>{children}</body>
    </html>
  );
}
