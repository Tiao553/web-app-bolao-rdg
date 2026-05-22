import { Badge, SimpleGrid, Stack, Text } from '@mantine/core';
import { HeroPanel, EmptyPanel, MetricCard, SurfaceCard } from '../../../components/layout/page-primitives';
import type { RankingContract } from '../../../lib/contracts';
import { fetchBackendData } from '../../../lib/session';

export default async function RankingPage() {
  const { data, error } = await fetchBackendData<RankingContract>('/api/member/ranking');
  const podium = data?.rows.slice(0, 3) ?? [];

  return (
    <Stack gap="lg">
      <HeroPanel
        eyebrow="Apenas usuários aprovados"
        title="Ranking geral do"
        highlight="bolão"
        description="A classificação já usa somente aprovados, preservando a regra canônica no backend e refletindo o visual do mock com pódio, tabela e critérios de desempate."
        side={
          <SurfaceCard title="Sua posição" subtitle="Resumo pessoal">
            <MetricCard value={data?.currentUserRank ?? '—'} label="posição atual" color="var(--mantine-color-rdg-orange-5)" />
          </SurfaceCard>
        }
      />
      <SimpleGrid cols={{ base: 1, md: 3 }}>
        {podium.map((row) => (
          <SurfaceCard key={row.userId} title={`#${row.rank}`} subtitle={row.fullName}>
            <Text fw={900} fz={32} c="rdg-orange.5">{row.totalPoints}</Text>
            <Text c="dimmed">Partidas {row.matchPoints} · bônus {row.bonusPoints}</Text>
          </SurfaceCard>
        ))}
      </SimpleGrid>
      <SurfaceCard title="Classificação geral" subtitle="Pontos totais e critérios de desempate" action={<Badge color="green" variant="light">atualizado</Badge>}>
        {error && !data ? <EmptyPanel title="Não foi possível carregar o ranking" description={error} /> : (
          <Stack gap="sm">
            {data?.rows.map((row) => (
              <SimpleGrid key={row.userId} cols={{ base: 1, md: 5 }} p="md" style={{ border: '1px solid var(--rdg-bd)', borderRadius: 17, background: row.rank === data.currentUserRank ? 'var(--rdg-or-g)' : 'var(--rdg-s2)' }}>
                <Text ff="monospace" fw={900}>{row.rank}</Text>
                <Text fw={800}>{row.fullName}</Text>
                <Text c="dimmed">Partidas: {row.matchPoints}</Text>
                <Text c="dimmed">Bônus: {row.bonusPoints}</Text>
                <Text ff="monospace" fw={900} c="rdg-orange.5">{row.totalPoints}</Text>
              </SimpleGrid>
            ))}
          </Stack>
        )}
      </SurfaceCard>
    </Stack>
  );
}
