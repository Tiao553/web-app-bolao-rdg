import { SimpleGrid, Stack, Text } from '@mantine/core';
import { HeroPanel, EmptyPanel, SurfaceCard } from '../../../../components/layout/page-primitives';
import type { AdminMatchesContract } from '../../../../lib/contracts';
import { fetchBackendData } from '../../../../lib/session';

export default async function AdminResultsPage() {
  const { data, error } = await fetchBackendData<AdminMatchesContract>('/api/admin/results');

  return (
    <Stack gap="lg">
      <HeroPanel
        eyebrow="Resultados oficiais"
        title="Altere placares com"
        highlight="rastreabilidade"
        description="O contrato administrativo agora entrega partidas finalizadas e metadados de override para o fluxo de correção manual previsto nos mocks."
        side={<SurfaceCard title="Impacto automático" subtitle="Recalcular"><Text>Salvar um resultado deve recalcular pontos, ranking, Explore e chaveamento.</Text></SurfaceCard>}
      />
      <SimpleGrid cols={{ base: 1, xl: 3 }}>
        <div style={{ gridColumn: 'span 2' }}>
          <SurfaceCard title="Resultados das partidas" subtitle="API, manual override e recalculação">
            {!data ? <EmptyPanel title="Listagem indisponível" description={error ?? 'Não foi possível carregar os resultados.'} /> : (
              <Stack gap="sm">
                {data.matches.slice(0, 20).map((match) => (
                  <Text key={match.id}>{match.homeTeam} {match.officialHomeGoals ?? '—'} × {match.officialAwayGoals ?? '—'} {match.awayTeam} · {match.status}</Text>
                ))}
              </Stack>
            )}
          </SurfaceCard>
        </div>
        <SurfaceCard title="Editor rápido" subtitle="Partida selecionada">
          <Text c="dimmed">Resultados com override: {data?.summary.overridden ?? 0}. Use a listagem para escolher a partida a corrigir.</Text>
        </SurfaceCard>
      </SimpleGrid>
    </Stack>
  );
}
