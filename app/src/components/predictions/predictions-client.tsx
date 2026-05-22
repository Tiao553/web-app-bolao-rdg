'use client';

import { Select, SimpleGrid, Stack, Text } from '@mantine/core';
import { useState } from 'react';
import { MatchCard } from '../match/match-card';

type Match = {
  matchId: string;
  phase: string;
  homeTeam: string;
  awayTeam: string;
  homeFlag?: string;
  awayFlag?: string;
  homeGoals?: number | null;
  awayGoals?: number | null;
  result?: 'exact' | 'correct' | 'wrong' | null;
};

const CHAMPION_OPTIONS = [
  'Brasil', 'Argentina', 'França', 'Espanha', 'Alemanha',
  'Inglaterra', 'Portugal', 'Holanda', 'Uruguai', 'Colômbia',
];

const SCORER_OPTIONS = [
  'Vinicius Jr.', 'Mbappé', 'Haaland', 'Lewandowski', 'Kane',
  'Pedri', 'Bellingham', 'Osimhen', 'Darwin Núñez', 'Rodrygo',
];

const PHASE_ORDER = [
  'Fase de Grupos',
  'Oitavas de Final',
  'Quartas de Final',
  'Semifinal',
  'Final',
];

type PredictionsClientProps = {
  matches: Match[];
  locked: boolean;
};

export function PredictionsClient({ matches: initial, locked }: PredictionsClientProps) {
  const [matches, setMatches] = useState(initial);
  const [champion, setChampion] = useState<string | null>('Brasil');
  const [scorer, setScorer] = useState<string | null>('Vinicius Jr.');

  function handleSave(matchId: string, home: number, away: number) {
    setMatches((prev) =>
      prev.map((m) => (m.matchId === matchId ? { ...m, homeGoals: home, awayGoals: away } : m))
    );
  }

  const byPhase = matches.reduce<Record<string, Match[]>>((acc, m) => {
    (acc[m.phase] ??= []).push(m);
    return acc;
  }, {});

  const sortedPhases = Object.keys(byPhase).sort((a, b) => {
    const ai = PHASE_ORDER.findIndex((p) => a.startsWith(p));
    const bi = PHASE_ORDER.findIndex((p) => b.startsWith(p));
    return (ai === -1 ? 99 : ai) - (bi === -1 ? 99 : bi);
  });

  const inputStyle = { background: 'var(--rdg-s2)', borderColor: locked ? 'var(--rdg-bd)' : 'var(--mantine-color-rdg-orange-5)' };
  const dropdownStyle = { background: 'var(--rdg-s1)', borderColor: 'var(--rdg-bd)' };

  return (
    <Stack gap="xl">
      <Stack gap="sm">
        <Text size="xs" c="dimmed" ff="monospace" style={{ letterSpacing: '0.12em', textTransform: 'uppercase' }}>
          Palpites especiais
        </Text>
        <SimpleGrid cols={{ base: 1, sm: 2 }} spacing="md">
          <Select
            label="Campeão da Copa"
            data={CHAMPION_OPTIONS}
            value={champion}
            onChange={setChampion}
            disabled={locked}
            styles={{ input: inputStyle, dropdown: dropdownStyle }}
          />
          <Select
            label="Artilheiro do torneio"
            data={SCORER_OPTIONS}
            value={scorer}
            onChange={setScorer}
            disabled={locked}
            styles={{ input: inputStyle, dropdown: dropdownStyle }}
          />
        </SimpleGrid>
      </Stack>

      {sortedPhases.map((phase) => (
        <Stack key={phase} gap="sm">
          <Text size="xs" c="dimmed" ff="monospace" style={{ letterSpacing: '0.12em', textTransform: 'uppercase' }}>
            {phase}
          </Text>
          <SimpleGrid cols={{ base: 1, sm: 2 }} spacing="md">
            {byPhase[phase].map((m) => (
              <MatchCard
                key={m.matchId}
                {...m}
                locked={locked}
                onSave={locked ? undefined : handleSave}
              />
            ))}
          </SimpleGrid>
        </Stack>
      ))}
    </Stack>
  );
}
