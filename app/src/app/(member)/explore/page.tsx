import { SimpleGrid, Stack, Text } from '@mantine/core';
import { AccessGate } from '../../../components/access/access-gate';
import { HeroPanel, EmptyPanel, SurfaceCard } from '../../../components/layout/page-primitives';
import type { ExploreContract } from '../../../lib/contracts';
import { fetchBackendData } from '../../../lib/session';

export default async function ExplorePage() {
  const { data, error } = await fetchBackendData<ExploreContract>('/api/member/explore');
  const grouped = new Map<string, { champion?: string; scorer?: string; sample?: string }>();

  data?.competitionPredictions.forEach((item) => {
    const entry = grouped.get(item.userId) ?? {};
    if (item.predictionType === 'CHAMPION') {
      entry.champion = item.selectionLabel;
    } else {
      entry.scorer = item.selectionLabel;
    }
    grouped.set(item.userId, entry);
  });

  data?.matchPredictions.forEach((item) => {
    const entry = grouped.get(item.userId) ?? {};
    entry.sample = `${item.homeGoals} × ${item.awayGoals}`;
    grouped.set(item.userId, entry);
  });

  return (
    <Stack gap="lg">
      <HeroPanel
        eyebrow="Palpites liberados"
        title="Veja os palpites dos"
        highlight="outros participantes"
        description="Antes do fechamento, esta área permanece bloqueada. Depois, o Explore mostra somente usuários aprovados e publica os palpites com segurança."
        side={<SurfaceCard title="Explore disponível" subtitle="Janela de liberação"><Text>{data?.exploreReleased ? 'Fechamento concluído' : 'Ainda bloqueado'}</Text></SurfaceCard>}
      />
      <AccessGate
        released={data?.exploreReleased}
        loading={!data && !error}
        error={error}
        lockedFallback={<EmptyPanel title="Explore bloqueado" description="Disponível somente após o horário de fechamento dos palpites." />}
        errorFallback={<EmptyPanel title="Não foi possível abrir o Explore" description={error ?? 'Tente novamente depois.'} />}
      >
        <SimpleGrid cols={{ base: 1, xl: 3 }}>
          <div style={{ gridColumn: 'span 2' }}>
            <SurfaceCard title="Palpites dos participantes" subtitle="Visão liberada após fechamento">
              {grouped.size === 0 ? <EmptyPanel title="Sem palpites públicos" description="Nenhum participante aprovado teve palpites liberados até agora." /> : (
                <SimpleGrid cols={{ base: 1, md: 2 }}>
                  {Array.from(grouped.entries()).map(([userId, entry], index) => (
                    <SurfaceCard key={userId} title={`#${index + 1}`} subtitle={data?.competitionPredictions.find((item) => item.userId === userId)?.userName ?? 'Participante'}>
                      <Text>Campeão: {entry.champion ?? '—'}</Text>
                      <Text>Artilheiro: {entry.scorer ?? '—'}</Text>
                      <Text>Amostra: {entry.sample ?? 'Sem partida liberada'}</Text>
                    </SurfaceCard>
                  ))}
                </SimpleGrid>
              )}
            </SurfaceCard>
          </div>
          <SurfaceCard title="Insights" subtitle="Comparativo geral">
            <Text c="dimmed">Quando o backend expuser agregações específicas do Explore, esta coluna poderá refletir campeões mais escolhidos, artilheiros líderes e proximidade com seus palpites.</Text>
          </SurfaceCard>
        </SimpleGrid>
      </AccessGate>
    </Stack>
  );
}
