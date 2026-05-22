'use client';

import { useTransition } from 'react';
import { Button, Group } from '@mantine/core';
import { notifications } from '@mantine/notifications';
import { postJson } from '../../lib/api-client';
import type { AdminSyncRunContract } from '../../lib/contracts';

export function SyncControls() {
  const [isPending, startTransition] = useTransition();

  const runSync = () => {
    startTransition(async () => {
      try {
        const response = await postJson<AdminSyncRunContract>('/api/admin/sync/run', {});
        notifications.show({ color: response.status === 'success' ? 'green' : 'yellow', message: response.message });
      } catch (error) {
        const message = error instanceof Error ? error.message : 'Não foi possível executar a sincronização.';
        notifications.show({ color: 'red', message });
      }
    });
  };

  return (
    <Group>
      <Button variant="light" onClick={runSync} loading={isPending}>Testar endpoint</Button>
      <Button onClick={runSync} loading={isPending}>Sincronizar agora</Button>
    </Group>
  );
}
