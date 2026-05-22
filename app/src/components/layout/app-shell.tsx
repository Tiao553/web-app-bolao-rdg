'use client';

import { AppShell, Box, Burger, Button, Divider, Group, NavLink, Stack, Text } from '@mantine/core';
import { useDisclosure } from '@mantine/hooks';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import type { ReactNode } from 'react';
import { BrandLogo } from '../brand/brand-logo';

const navItems = [
  { href: '/dashboard',   label: 'Dashboard' },
  { href: '/predictions', label: 'Palpites' },
  { href: '/ranking',     label: 'Ranking' },
  { href: '/explore',     label: 'Explore' },
];

type RdgAppShellProps = {
  children: ReactNode;
  userName?: string;
};

export function RdgAppShell({ children, userName }: RdgAppShellProps) {
  const [opened, { toggle, close }] = useDisclosure();
  const pathname = usePathname();

  return (
    <AppShell
      header={{ height: 52 }}
      navbar={{ width: 200, breakpoint: 'sm', collapsed: { mobile: !opened } }}
      padding="md"
      styles={{
        root:   { '--app-shell-border-color': 'var(--rdg-bd)' },
        header: { background: 'var(--rdg-s0)', borderBottom: '1px solid var(--rdg-bd)' },
        navbar: { background: 'var(--rdg-s0)', borderRight: '1px solid var(--rdg-bd)' },
        main:   { background: 'var(--mantine-color-body)' },
      }}
    >
      <AppShell.Header>
        <Group h="100%" px="md" justify="space-between">
          <Group gap="sm">
            <Burger opened={opened} onClick={toggle} hiddenFrom="sm" size="sm" color="var(--rdg-tx2)" />
            <BrandLogo size="sm" />
          </Group>

          <Group gap={2} visibleFrom="sm">
            {navItems.map((item) => (
              <NavLink
                key={item.href}
                component={Link}
                href={item.href}
                label={item.label}
                active={pathname.startsWith(item.href)}
                color="rdg-orange"
                style={{ borderRadius: 'var(--mantine-radius-sm)', padding: '6px 12px' }}
                onClick={close}
              />
            ))}
          </Group>

          <Group gap="sm" visibleFrom="sm">
            {userName && (
              <Text size="xs" c="dimmed" ff="monospace">{userName.split(' ')[0]}</Text>
            )}
            <form method="POST" action="/api/auth/logout">
              <Button type="submit" variant="subtle" size="xs" color="gray" ff="monospace">
                Sair
              </Button>
            </form>
          </Group>
        </Group>
      </AppShell.Header>

      <AppShell.Navbar p="sm">
        <Stack gap={2} style={{ flex: 1 }}>
          {navItems.map((item) => (
            <NavLink
              key={item.href}
              component={Link}
              href={item.href}
              label={item.label}
              active={pathname.startsWith(item.href)}
              color="rdg-orange"
              style={{ borderRadius: 'var(--mantine-radius-sm)' }}
              onClick={close}
            />
          ))}
        </Stack>
        <Box>
          <Divider mb="sm" color="var(--rdg-bd)" />
          {userName && (
            <Text size="xs" c="dimmed" ff="monospace" px="xs" mb={4}>{userName}</Text>
          )}
          <form method="POST" action="/api/auth/logout">
            <Button
              type="submit"
              variant="subtle"
              size="xs"
              color="gray"
              ff="monospace"
              fullWidth
              style={{ justifyContent: 'flex-start' }}
            >
              Sair →
            </Button>
          </form>
        </Box>
      </AppShell.Navbar>

      <AppShell.Main>{children}</AppShell.Main>
    </AppShell>
  );
}
