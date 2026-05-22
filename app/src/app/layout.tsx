import '@mantine/core/styles.css';
import '@mantine/notifications/styles.css';
import './globals.css';

import type { ReactNode } from 'react';
import { ColorSchemeScript, MantineProvider } from '@mantine/core';
import { Notifications } from '@mantine/notifications';
import { theme } from '../lib/theme';

export const metadata = {
  title: {
    default: 'Bolão Copa RDG',
    template: '%s | Bolão Copa RDG',
  },
  description:
    'Aplicação web do Bolão Copa RDG com autenticação, acesso por aprovação e áreas separadas para participantes e administração.',
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="pt-BR" suppressHydrationWarning>
      <head>
        <ColorSchemeScript defaultColorScheme="dark" />
      </head>
      <body suppressHydrationWarning>
        <MantineProvider theme={theme} defaultColorScheme="dark">
          <Notifications />
          {children}
        </MantineProvider>
      </body>
    </html>
  );
}
