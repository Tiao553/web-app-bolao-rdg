'use client';

import { Box, Group, Paper, Stack, Text } from '@mantine/core';

type ScoreGaugeProps = {
  score: number;
  max: number;
  rank?: number;
};

export function ScoreGauge({ score, max, rank }: ScoreGaugeProps) {
  const radius = 34;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (score / max) * circumference;

  return (
    <Paper p="md" radius="md" style={{ background: 'var(--rdg-s2)', border: '1px solid var(--rdg-bd)' }}>
      <Group gap="lg" wrap="nowrap">
        <Box style={{ position: 'relative', width: 80, height: 80, flexShrink: 0 }}>
          <svg
            width={80}
            height={80}
            viewBox="0 0 80 80"
            style={{ transform: 'rotate(-90deg)' }}
          >
            <circle
              cx={40} cy={40} r={radius}
              fill="none"
              stroke="var(--rdg-s3)"
              strokeWidth={6}
            />
            <circle
              cx={40} cy={40} r={radius}
              fill="none"
              stroke="var(--mantine-color-rdg-orange-5)"
              strokeWidth={6}
              strokeLinecap="round"
              strokeDasharray={circumference}
              strokeDashoffset={offset}
            />
          </svg>
          <Box
            style={{
              position: 'absolute', inset: 0,
              display: 'flex', flexDirection: 'column',
              alignItems: 'center', justifyContent: 'center',
            }}
          >
            <Text fw={700} size="xl" c="rdg-orange" lh={1} ff="monospace">
              {score}
            </Text>
            <Text size="xs" c="dimmed" ff="monospace">/{max}</Text>
          </Box>
        </Box>

        <Stack gap={4}>
          <Text fw={600} size="sm">Pontuação Geral</Text>
          {rank != null && (
            <Text size="xs" c="rdg-orange" fw={600} ff="monospace" style={{ letterSpacing: '0.06em' }}>
              {rank}° LUGAR
            </Text>
          )}
        </Stack>
      </Group>
    </Paper>
  );
}
