'use client';

import { useState, useTransition } from 'react';
import { ActionIcon, Badge, Button, Group, SimpleGrid, Stack, Text } from '@mantine/core';
import { notifications } from '@mantine/notifications';
import { putJson } from '../../lib/api-client';
import type { AdminUserContract } from '../../lib/contracts';

const colorByStatus: Record<AdminUserContract['access_status'], string> = {
  APPROVED: 'green',
  PENDING: 'yellow',
  REJECTED: 'red',
  BLOCKED: 'gray'
};

export function UserModerationTable({ initialUsers }: { initialUsers: AdminUserContract[]; }) {
  const [users, setUsers] = useState(initialUsers);
  const [isPending, startTransition] = useTransition();

  const updateUser = (userId: string, access_status: AdminUserContract['access_status']) => {
    startTransition(async () => {
      try {
        const current = users.find((user) => user.id === userId);
        if (!current) {
          return;
        }
        const updated = await putJson<AdminUserContract>(`/api/admin/users/${userId}/moderation`, {
          access_status,
          is_admin: current.is_admin
        });
        setUsers((value) => value.map((user) => (user.id === userId ? updated : user)));
        notifications.show({ color: 'green', message: 'Usuário atualizado.' });
      } catch (error) {
        const message = error instanceof Error ? error.message : 'Não foi possível atualizar o usuário.';
        notifications.show({ color: 'red', message });
      }
    });
  };

  return (
    <Stack gap="sm">
      {users.map((user) => (
        <SimpleGrid key={user.id} cols={{ base: 1, lg: 5 }} spacing="md" p="md" style={{ border: '1px solid var(--rdg-bd)', borderRadius: 18, background: 'var(--rdg-s2)' }}>
          <div>
            <Text fw={800}>{user.full_name}</Text>
            <Text size="sm" c="dimmed">{user.email}</Text>
          </div>
          <div>
            <Badge color={colorByStatus[user.access_status]} radius="xl" variant="light">{user.access_status}</Badge>
          </div>
          <div>
            <Text size="sm" c="dimmed">Criado em</Text>
            <Text fw={700}>{new Date(user.created_at).toLocaleString('pt-BR')}</Text>
          </div>
          <div>
            <Text size="sm" c="dimmed">Último login</Text>
            <Text fw={700}>{user.last_login_at ? new Date(user.last_login_at).toLocaleString('pt-BR') : 'Nunca'}</Text>
          </div>
          <Group justify="flex-end">
            <Button size="xs" variant="light" color="green" disabled={isPending} onClick={() => updateUser(user.id, 'APPROVED')}>Aprovar</Button>
            <Button size="xs" variant="light" color="red" disabled={isPending} onClick={() => updateUser(user.id, 'REJECTED')}>Rejeitar</Button>
            <ActionIcon size="lg" variant="light" color="gray" disabled={isPending} onClick={() => updateUser(user.id, 'BLOCKED')}>⛔</ActionIcon>
          </Group>
        </SimpleGrid>
      ))}
    </Stack>
  );
}
