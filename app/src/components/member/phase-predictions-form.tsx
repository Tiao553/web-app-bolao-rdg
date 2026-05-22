'use client';

import { useMemo, useState, useTransition } from 'react';
import { Button, Group, NumberInput, SimpleGrid, Stack, Text } from '@mantine/core';
import { notifications } from '@mantine/notifications';
import { putJson } from '../../lib/api-client';
import type { MatchPredictionContract, MemberCompetitionWindowContract } from '../../lib/contracts';

type DraftMap = Record<string, { homeGoals: number; awayGoals: number }>;

export function PhasePredictionsForm({ predictions, competition }: { predictions: MatchPredictionContract[]; competition: MemberCompetitionWindowContract; }) {
  const [isPending, startTransition] = useTransition();
  const [drafts, setDrafts] = useState<DraftMap>(() => Object.fromEntries(predictions.map((item) => [item.matchId, { homeGoals: item.homeGoals, awayGoals: item.awayGoals }])));
  const locked = competition.predictionLocked;
  const completed = useMemo(() => Object.values(drafts).filter((item) => Number.isFinite(item.homeGoals) && Number.isFinite(item.awayGoals)).length, [drafts]);

  const updateDraft = (matchId: string, side: 'homeGoals' | 'awayGoals', value: string | number) => {
    setDrafts((current) => ({
      ...current,
      [matchId]: {
        homeGoals: current[matchId]?.homeGoals ?? 0,
        awayGoals: current[matchId]?.awayGoals ?? 0,
        [side]: typeof value === 'number' ? value : Number(value) || 0
      }
    }));
  };

  const save = () => {
    startTransition(async () => {
      try {
        await Promise.all(predictions.map((prediction) => putJson(`/api/member/predictions/matches/${prediction.matchId}`, drafts[prediction.matchId])));
        notifications.show({ color: 'green', message: 'Palpites por fase salvos.' });
      } catch (error) {
        const message = error instanceof Error ? error.message : 'Não foi possível salvar os palpites.';
        notifications.show({ color: 'red', message });
      }
    });
  };

  return (
    <Stack>
      <Text size="sm" c="dimmed">{completed}/{predictions.length} partidas com placar salvo.</Text>
      <SimpleGrid cols={{ base: 1, md: 2 }}>
        {predictions.map((prediction, index) => (
          <Stack key={prediction.id} p="md" style={{ border: '1px solid var(--rdg-bd)', borderRadius: 20, background: 'var(--rdg-s2)' }}>
            <Text fw={800}>Partida {String(index + 1).padStart(2, '0')}</Text>
            <Text size="xs" c="dimmed" ff="monospace">ID {prediction.matchId.slice(0, 8)}</Text>
            <Group grow>
              <NumberInput label="Mandante" min={0} max={50} value={drafts[prediction.matchId]?.homeGoals ?? 0} onChange={(value) => updateDraft(prediction.matchId, 'homeGoals', value)} disabled={locked || isPending} />
              <NumberInput label="Visitante" min={0} max={50} value={drafts[prediction.matchId]?.awayGoals ?? 0} onChange={(value) => updateDraft(prediction.matchId, 'awayGoals', value)} disabled={locked || isPending} />
            </Group>
          </Stack>
        ))}
      </SimpleGrid>
      <Group justify="flex-end">
        <Button onClick={save} loading={isPending} disabled={locked || predictions.length === 0}>Salvar fase</Button>
      </Group>
    </Stack>
  );
}
