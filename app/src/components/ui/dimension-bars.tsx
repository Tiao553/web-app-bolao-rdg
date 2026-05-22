import { Group, Paper, Progress, Stack, Text } from '@mantine/core';

export type DimensionEntry = {
  label: string;
  value: number;
  max: number;
};

type DimensionBarsProps = {
  breakdown: DimensionEntry[];
};

export function DimensionBars({ breakdown }: DimensionBarsProps) {
  return (
    <Paper p="md" radius="md" style={{ background: 'var(--rdg-s2)', border: '1px solid var(--rdg-bd)' }}>
      <Text size="xs" c="dimmed" ff="monospace" style={{ letterSpacing: '0.12em', textTransform: 'uppercase' }} mb="sm">
        Detalhamento
      </Text>
      <Stack gap={8}>
        {breakdown.map(({ label, value, max }) => (
          <Group key={label} gap="sm" wrap="nowrap">
            <Text size="xs" style={{ width: 130, flexShrink: 0 }} truncate>
              {label}
            </Text>
            <Progress
              value={max > 0 ? (value / max) * 100 : 0}
              color="rdg-orange"
              size="sm"
              radius="xl"
              style={{ flex: 1 }}
            />
            <Text size="xs" c="rdg-orange" fw={600} ff="monospace" style={{ width: 28, textAlign: 'right', flexShrink: 0 }}>
              {value}
            </Text>
          </Group>
        ))}
      </Stack>
    </Paper>
  );
}
