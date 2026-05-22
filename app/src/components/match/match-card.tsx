'use client';

import { Badge, Card, Group, NumberInput, Stack, Text } from '@mantine/core';

type MatchResult = 'exact' | 'correct' | 'wrong' | null;

type MatchCardProps = {
  matchId: string;
  phase: string;
  round?: string;
  homeTeam: string;
  awayTeam: string;
  homeFlag?: string;
  awayFlag?: string;
  homeGoals?: number | null;
  awayGoals?: number | null;
  locked: boolean;
  result?: MatchResult;
  onSave?: (matchId: string, home: number, away: number) => void;
};

const borderByResult: Record<NonNullable<MatchResult>, string> = {
  exact: 'var(--mantine-color-green-6)',
  correct: 'var(--mantine-color-yellow-5)',
  wrong: 'var(--mantine-color-red-6)',
};

const resultLabel: Record<NonNullable<MatchResult>, { label: string; color: string }> = {
  exact: { label: 'Exato', color: 'green' },
  correct: { label: 'Resultado', color: 'yellow' },
  wrong: { label: 'Errado', color: 'red' },
};

export function MatchCard({
  matchId,
  phase,
  round,
  homeTeam,
  awayTeam,
  homeFlag,
  awayFlag,
  homeGoals,
  awayGoals,
  locked,
  result,
  onSave,
}: MatchCardProps) {
  const borderColor = result ? borderByResult[result] : 'var(--rdg-bd)';

  return (
    <Card
      padding="md"
      radius="md"
      style={{
        background: 'var(--rdg-s1)',
        border: `1px solid ${borderColor}`,
        transition: 'border-color 0.2s',
      }}
    >
      <Stack gap="xs">
        <Group justify="space-between" wrap="nowrap">
          <Text size="xs" c="dimmed" ff="monospace" style={{ letterSpacing: '0.1em', textTransform: 'uppercase' }}>
            {phase}{round ? ` · ${round}` : ''}
          </Text>
          {result && (
            <Badge
              color={resultLabel[result].color}
              variant="light"
              size="xs"
              radius="sm"
              ff="monospace"
            >
              {resultLabel[result].label}
            </Badge>
          )}
          {locked && !result && (
            <Badge color="gray" variant="outline" size="xs" radius="sm" ff="monospace">
              Fechado
            </Badge>
          )}
        </Group>

        <Group justify="space-between" align="center" gap="xs" wrap="nowrap">
          <Stack gap={4} align="center" style={{ flex: 1, minWidth: 0 }}>
            {homeFlag && <Text style={{ fontSize: 24, lineHeight: 1 }}>{homeFlag}</Text>}
            <Text fw={600} size="xs" style={{ textTransform: 'uppercase', textAlign: 'center' }} truncate="end">
              {homeTeam}
            </Text>
          </Stack>

          <Group gap={4} align="center" wrap="nowrap">
            <NumberInput
              value={homeGoals ?? ''}
              onChange={(v) => {
                if (!locked && onSave && typeof v === 'number') {
                  onSave(matchId, v, awayGoals ?? 0);
                }
              }}
              disabled={locked}
              min={0}
              max={99}
              hideControls
              size="sm"
              ff="monospace"
              fw={700}
              style={{ width: 44 }}
              styles={{
                input: {
                  textAlign: 'center',
                  background: 'var(--rdg-s2)',
                  borderColor: locked ? 'var(--rdg-bd)' : 'var(--mantine-color-rdg-orange-5)',
                  color: 'var(--mantine-color-rdg-orange-5)',
                },
              }}
            />
            <Text c="dimmed" fw={700} size="sm">×</Text>
            <NumberInput
              value={awayGoals ?? ''}
              onChange={(v) => {
                if (!locked && onSave && typeof v === 'number') {
                  onSave(matchId, homeGoals ?? 0, v);
                }
              }}
              disabled={locked}
              min={0}
              max={99}
              hideControls
              size="sm"
              ff="monospace"
              fw={700}
              style={{ width: 44 }}
              styles={{
                input: {
                  textAlign: 'center',
                  background: 'var(--rdg-s2)',
                  borderColor: locked ? 'var(--rdg-bd)' : 'var(--mantine-color-rdg-orange-5)',
                  color: 'var(--mantine-color-rdg-orange-5)',
                },
              }}
            />
          </Group>

          <Stack gap={4} align="center" style={{ flex: 1, minWidth: 0 }}>
            {awayFlag && <Text style={{ fontSize: 24, lineHeight: 1 }}>{awayFlag}</Text>}
            <Text fw={600} size="xs" style={{ textTransform: 'uppercase', textAlign: 'center' }} truncate="end">
              {awayTeam}
            </Text>
          </Stack>
        </Group>
      </Stack>
    </Card>
  );
}
