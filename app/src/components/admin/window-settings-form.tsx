'use client';

import { useState, useTransition } from 'react';
import { Button, Group, SimpleGrid, Stack, TextInput } from '@mantine/core';
import { notifications } from '@mantine/notifications';
import { putJson } from '../../lib/api-client';
import type { AdminCompetitionWindowContract } from '../../lib/contracts';

function toLocalInput(value: string) {
  const date = new Date(value);
  const iso = new Date(date.getTime() - date.getTimezoneOffset() * 60000).toISOString();
  return iso.slice(0, 16);
}

export function WindowSettingsForm({ window }: { window: AdminCompetitionWindowContract; }) {
  const [predictionCloseAt, setPredictionCloseAt] = useState(toLocalInput(window.prediction_close_at));
  const [exploreReleaseAt, setExploreReleaseAt] = useState(toLocalInput(window.explore_release_at));
  const [isPending, startTransition] = useTransition();

  const save = () => {
    startTransition(async () => {
      try {
        await putJson('/api/admin/competition/window', {
          name: window.name,
          prediction_close_at: new Date(predictionCloseAt).toISOString(),
          explore_release_at: new Date(exploreReleaseAt).toISOString()
        });
        notifications.show({ color: 'green', message: 'Janela da competição atualizada.' });
      } catch (error) {
        const message = error instanceof Error ? error.message : 'Não foi possível salvar a configuração.';
        notifications.show({ color: 'red', message });
      }
    });
  };

  return (
    <Stack>
      <SimpleGrid cols={{ base: 1, md: 2 }}>
        <TextInput type="datetime-local" label="Fechamento dos palpites" value={predictionCloseAt} onChange={(event) => setPredictionCloseAt(event.currentTarget.value)} />
        <TextInput type="datetime-local" label="Liberação do Explore" value={exploreReleaseAt} onChange={(event) => setExploreReleaseAt(event.currentTarget.value)} />
      </SimpleGrid>
      <Group justify="flex-end">
        <Button onClick={save} loading={isPending}>Salvar janela</Button>
      </Group>
    </Stack>
  );
}
