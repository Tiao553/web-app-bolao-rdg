import { SimpleGrid, Stack, Text } from '@mantine/core';
import { HeroPanel, EmptyPanel, SurfaceCard } from '../../../../components/layout/page-primitives';
import type { AdminMatchesContract } from '../../../../lib/contracts';
import { fetchBackendData } from '../../../../lib/session';

export default async function AdminMatchesPage() {
  const { data, error } = await fetchBackendData<AdminMatchesContract>('/api/admin/matches');

  return (
    <Stack gap="lg">
      <HeroPanel
        eyebrow="Gestão de partidas"
        title="Corrija jogos antes de afetar"
        highlight="palpites"
        description="A tela lista partidas, status e overrides diretamente do backend para sustentar os fluxos previstos nos mocks administrativos."
        side={<SurfaceCard title="Editor rápido" subtitle="Estado operacional"><Text>{data?.summary.overridden ?? 0} partidas com override manual.</Text></SurfaceCard>}
      />
      <SimpleGrid cols={{ base: 1, xl: 3 }}>
        <div style={{ gridColumn: 'span 2' }}>
          <SurfaceCard title="Lista de partidas" subtitle="Importadas, manuais e corrigidas">
            {!data ? <EmptyPanel title="Não foi possível carregar partidas" description={error ?? 'Sem dados disponíveis.'} /> : (
              <Stack gap="sm">
                {data.matches.slice(0, 20).map((match) => (
                  <Text key={match.id}>{match.phase} · {match.homeTeam} × {match.awayTeam} · {match.status}{match.hasManualOverride ? ' · override' : ''}</Text>
                ))}
              </Stack>
            )}
          </SurfaceCard>
        </div>
        <SurfaceCard title="Resumo" subtitle="Cadastro de jogos">
          <Text>Total: {data?.summary.total ?? 0}</Text>
          <Text>Finalizadas: {data?.summary.finished ?? 0}</Text>
          <Text c="dimmed">Pendências: {data?.summary.scheduled ?? 0}</Text>
        </SurfaceCard>
      </SimpleGrid>
    </Stack>
  );
}
