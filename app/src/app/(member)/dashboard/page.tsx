import { SimpleGrid, Stack, Text } from '@mantine/core';
import { HeroPanel, MetricCard, ProgressList, SurfaceCard } from '../../../components/layout/page-primitives';
import type { MemberDashboardContract } from '../../../lib/contracts';
import { fetchBackendData } from '../../../lib/session';

export default async function DashboardPage() {
  const { data, error } = await fetchBackendData<MemberDashboardContract>('/api/member/dashboard');

  return (
    <Stack gap="lg">
      <HeroPanel
        eyebrow="Painel do participante"
        title="Seu jogo começa no"
        highlight="dashboard"
        description="Acompanhe posição, progresso dos palpites e a janela oficial de bloqueio sem mover regras sensíveis para o cliente."
        side={
          <SurfaceCard title="Status operacional" subtitle="Resumo pessoal">
            <SimpleGrid cols={2}>
              <MetricCard value={data?.rankingPosition ?? '—'} label="posição" color="var(--mantine-color-rdg-orange-5)" />
              <MetricCard value={data?.totalPoints ?? 0} label="pontos totais" />
            </SimpleGrid>
          </SurfaceCard>
        }
      />
      <SimpleGrid cols={{ base: 1, md: 4 }}>
        <MetricCard value={data?.totalPoints ?? 0} label="pontuação acumulada" color="var(--mantine-color-rdg-orange-5)" />
        <MetricCard value={data?.savedMatchPredictions ?? 0} label="palpites por partida" />
        <MetricCard value={data?.savedBonusPredictions ?? 0} label="palpites iniciais" />
        <MetricCard value={data?.rankingPosition ?? '—'} label="posição no ranking" />
      </SimpleGrid>
      <SimpleGrid cols={{ base: 1, lg: 2 }}>
        <SurfaceCard title="Janela da competição" subtitle="Bloqueios e liberação">
          <ProgressList
            items={[
              { label: 'Palpites salvos', value: Math.min(100, ((data?.savedMatchPredictions ?? 0) / 12) * 100) },
              { label: 'Bônus salvos', value: Math.min(100, ((data?.savedBonusPredictions ?? 0) / 2) * 100) },
              { label: 'Explore liberado', value: data?.competition.exploreReleased ? 100 : 0 }
            ]}
          />
        </SurfaceCard>
        <SurfaceCard title="Resumo da conta" subtitle="Sessão atual">
          <Text fw={800}>{data?.user.name ?? 'Participante'}</Text>
          <Text c="dimmed">{data?.user.email ?? 'Sem dados do backend.'}</Text>
          <Text mt="md">Fechamento: {data ? new Date(data.competition.predictionCloseAt).toLocaleString('pt-BR') : '—'}</Text>
          <Text>Explore: {data ? new Date(data.competition.exploreReleaseAt).toLocaleString('pt-BR') : '—'}</Text>
          {error ? <Text c="red.4" mt="md">{error}</Text> : null}
        </SurfaceCard>
      </SimpleGrid>
    </Stack>
  );
}
