'use client';

import { useState, useTransition } from 'react';
import { Button, Group, Stack, TextInput } from '@mantine/core';
import { notifications } from '@mantine/notifications';
import { putJson } from '../../lib/api-client';
import type { CompetitionPredictionContract, MemberCompetitionWindowContract } from '../../lib/contracts';

function getPrediction(predictions: CompetitionPredictionContract[], kind: 'CHAMPION' | 'TOP_SCORER') {
  return predictions.find((item) => item.predictionType === kind);
}

export function InitialPredictionsForm({ predictions, competition }: { predictions: CompetitionPredictionContract[]; competition: MemberCompetitionWindowContract; }) {
  const champion = getPrediction(predictions, 'CHAMPION');
  const scorer = getPrediction(predictions, 'TOP_SCORER');
  const [championValue, setChampionValue] = useState(champion?.selectionLabel ?? 'Brasil');
  const [scorerValue, setScorerValue] = useState(scorer?.selectionLabel ?? 'Mbappé');
  const [isPending, startTransition] = useTransition();
  const locked = competition.predictionLocked;

  const save = () => {
    startTransition(async () => {
      try {
        await Promise.all([
          putJson('/api/member/predictions/champion', { selection_key: championValue, selection_label: championValue }),
          putJson('/api/member/predictions/top-scorer', { selection_key: scorerValue, selection_label: scorerValue })
        ]);
        notifications.show({ color: 'green', message: 'Palpites iniciais salvos.' });
      } catch (error) {
        const message = error instanceof Error ? error.message : 'Não foi possível salvar os palpites.';
        notifications.show({ color: 'red', message });
      }
    });
  };

  return (
    <Stack>
      <TextInput label="Campeão" value={championValue} onChange={(event) => setChampionValue(event.currentTarget.value)} disabled={locked || isPending} />
      <TextInput label="Artilheiro" value={scorerValue} onChange={(event) => setScorerValue(event.currentTarget.value)} disabled={locked || isPending} />
      <Group justify="flex-end">
        <Button onClick={save} loading={isPending} disabled={locked}>Salvar palpites</Button>
      </Group>
    </Stack>
  );
}
