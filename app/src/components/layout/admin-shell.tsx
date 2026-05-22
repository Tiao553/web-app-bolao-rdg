'use client';

import type { ReactNode } from 'react';
import { AppShell, Box, Burger, Button, Group, NavLink, Stack, Text } from '@mantine/core';
import { useDisclosure } from '@mantine/hooks';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { BrandLogo } from '../brand/brand-logo';
import type { AppSession } from '../../lib/session';

const adminNav = [
  { href: '/admin/dashboard', label: 'Dashboard', icon: '◈' },
  { href: '/admin/users', label: 'Usuários', icon: '👥' },
  { href: '/admin/integration', label: 'Integração', icon: '⛓' },
  { href: '/admin/matches', label: 'Partidas', icon: '▦' }
];

const operationNav = [
  { href: '/admin/results', label: 'Resultados', icon: '◆' },
  { href: '/admin/players', label: 'Jogadores', icon: '⚽' },
  { href: '/admin/settings', label: 'Configurações', icon: '⚙' }
];

function ShellNav({ items, pathname, close }: { items: typeof adminNav; pathname: string; close: () => void; }) {
  return (
    <Stack gap={4}>
      {items.map((item) => (
        <NavLink
          key={item.href}
          component={Link}
          href={item.href}
          active={pathname === item.href}
          onClick={close}
          label={item.label}
          leftSection={<Text span c="inherit">{item.icon}</Text>}
          color="orange"
          styles={{ root: { borderRadius: 13, color: 'var(--rdg-tx2)' } }}
        />
      ))}
    </Stack>
  );
}

export function AdminShell({ session, children }: { session: AppSession; children: ReactNode; }) {
  const pathname = usePathname();
  const [opened, { toggle, close }] = useDisclosure(false);
  const initials = session.user?.name?.split(' ').map((part) => part[0]).slice(0, 2).join('').toUpperCase() || 'AD';

  return (
    <AppShell
      navbar={{ width: 270, breakpoint: 'md', collapsed: { mobile: !opened } }}
      padding="md"
      styles={{
        header: { background: 'rgba(9,9,11,.92)', borderBottom: '1px solid var(--rdg-bd)' },
        navbar: { background: 'rgba(15,15,18,.88)', borderRight: '1px solid var(--rdg-bd)' },
        main: { background: 'var(--mantine-color-body)' }
      }}
      header={{ height: 72 }}
    >
      <AppShell.Header>
        <Group h="100%" px="lg" justify="space-between">
          <Group>
            <Burger opened={opened} onClick={toggle} hiddenFrom="md" color="var(--rdg-tx2)" />
            <BrandLogo />
          </Group>
          <form method="POST" action="/api/auth/logout">
            <Button type="submit" variant="subtle" color="gray">Sair</Button>
          </form>
        </Group>
      </AppShell.Header>
      <AppShell.Navbar p="lg">
        <BrandLogo />
        <Text mt="xl" mb="xs" size="xs" c="dimmed" ff="monospace" tt="uppercase" style={{ letterSpacing: '0.14em' }}>
          Admin
        </Text>
        <ShellNav items={adminNav} pathname={pathname} close={close} />
        <Text mt="xl" mb="xs" size="xs" c="dimmed" ff="monospace" tt="uppercase" style={{ letterSpacing: '0.14em' }}>
          Operação
        </Text>
        <ShellNav items={operationNav} pathname={pathname} close={close} />
        <Box mt="auto" p="md" style={{ border: '1px solid var(--rdg-bd)', borderRadius: 18, background: 'var(--rdg-s1)' }}>
          <Group align="center" wrap="nowrap">
            <Box w={36} h={36} style={{ borderRadius: '50%', display: 'grid', placeItems: 'center', background: 'var(--rdg-or-g)', border: '1px solid var(--rdg-or-r)', color: 'var(--mantine-color-rdg-orange-5)', fontWeight: 900 }}>
              {initials}
            </Box>
            <div>
              <Text size="sm" fw={800}>{session.user?.name || 'Admin RDG'}</Text>
              <Text size="xs" ff="monospace" c="dimmed" tt="uppercase" style={{ letterSpacing: '0.08em' }}>
                Governança
              </Text>
            </div>
          </Group>
        </Box>
      </AppShell.Navbar>
      <AppShell.Main>{children}</AppShell.Main>
    </AppShell>
  );
}
