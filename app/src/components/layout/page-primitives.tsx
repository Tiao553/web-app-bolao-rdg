import type { ReactNode } from 'react';
import { Alert, Badge, Box, Card, Group, Progress, SimpleGrid, Stack, Text, Title } from '@mantine/core';

export function MonoBadge({ children, color = 'orange', variant = 'light' }: { children: ReactNode; color?: string; variant?: 'light' | 'outline' | 'filled'; }) {
  return (
    <Badge color={color} variant={variant} radius="xl" tt="uppercase" style={{ letterSpacing: '0.12em' }}>
      {children}
    </Badge>
  );
}

export function HeroPanel({ eyebrow, title, highlight, description, side }: { eyebrow: ReactNode; title: string; highlight?: string; description: string; side?: ReactNode; }) {
  return (
    <Card radius={30} p="xl" style={{ background: 'linear-gradient(135deg, rgba(249,115,22,.18), rgba(20,20,24,.64) 42%, rgba(15,15,18,.96))', border: '1px solid var(--rdg-bd)' }}>
      <SimpleGrid cols={{ base: 1, lg: 2 }} spacing="xl">
        <Stack gap="md">
          <MonoBadge>{eyebrow}</MonoBadge>
          <Title order={1} fz={{ base: 34, md: 52 }} lh={0.95} maw={700}>
            {title} {highlight ? <Text component="span" c="rdg-orange.5" inherit>{highlight}</Text> : null}
          </Title>
          <Text c="dimmed" maw={680}>{description}</Text>
        </Stack>
        {side ? <Box>{side}</Box> : <div />}
      </SimpleGrid>
    </Card>
  );
}

export function SurfaceCard({ title, subtitle, action, children }: { title: string; subtitle?: string; action?: ReactNode; children: ReactNode; }) {
  return (
    <Card radius={24} p={0} style={{ background: 'rgba(20,20,24,.88)', border: '1px solid var(--rdg-bd)', overflow: 'hidden' }}>
      <Group justify="space-between" align="flex-start" p="lg" style={{ borderBottom: '1px solid var(--rdg-bd)', background: 'rgba(26,26,31,.72)' }}>
        <div>
          <Text fw={800} size="md">{title}</Text>
          {subtitle ? <Text size="xs" c="dimmed" ff="monospace" tt="uppercase" style={{ letterSpacing: '0.12em' }}>{subtitle}</Text> : null}
        </div>
        {action}
      </Group>
      <Box p="lg">{children}</Box>
    </Card>
  );
}

export function MetricCard({ value, label, color = 'white' }: { value: ReactNode; label: string; color?: string; }) {
  return (
    <Card radius={24} p="lg" style={{ background: 'rgba(20,20,24,.88)', border: '1px solid var(--rdg-bd)' }}>
      <Text fw={900} fz={36} c={color} lh={1}>{value}</Text>
      <Text size="sm" c="dimmed">{label}</Text>
    </Card>
  );
}

export function EmptyPanel({ title, description }: { title: string; description: string; }) {
  return (
    <Alert radius="lg" color="gray" variant="light" title={title}>
      {description}
    </Alert>
  );
}

export function ErrorPanel({ message }: { message: string; }) {
  return (
    <Alert radius="lg" color="red" title="Não foi possível carregar esta área">
      {message}
    </Alert>
  );
}

export function ProgressList({ items }: { items: Array<{ label: string; value: number; suffix?: string }>; }) {
  return (
    <Stack gap="sm">
      {items.map((item) => (
        <div key={item.label}>
          <Group justify="space-between" mb={6}>
            <Text size="sm" fw={700}>{item.label}</Text>
            <Text size="xs" ff="monospace" c="rdg-orange.5">{item.value}{item.suffix ?? ''}</Text>
          </Group>
          <Progress value={Math.max(0, Math.min(100, item.value))} color="orange" radius="xl" />
        </div>
      ))}
    </Stack>
  );
}
