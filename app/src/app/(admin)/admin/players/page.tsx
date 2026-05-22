import { SimpleGrid, Stack, Text } from '@mantine/core';
import { HeroPanel, EmptyPanel, SurfaceCard } from '../../../../components/layout/page-primitives';
import type { AdminPlayersContract } from '../../../../lib/contracts';
import { fetchBackendData } from '../../../../lib/session';

export default async function AdminPlayersPage() {
  const { data, error } = await fetchBackendData<AdminPlayersContract>('/api/admin/players');

  return (
    <Stack gap="lg">
      <HeroPanel
        eyebrow="Artilharia e assistências"
        title="Controle o desempate de"
        highlight="artilheiros"
        description="A área usa um contrato enxuto para mostrar os artilheiros mais previstos no bolão enquanto a regra canônica continua protegida no backend."
        side={<SurfaceCard title="Regra ativa" subtitle="Pontuação"><Text>{data?.topScorerPoints ?? 15} pontos para acerto de artilheiro.</Text></SurfaceCard>}
      />
      <SimpleGrid cols={{ base: 1, xl: 3 }}>
        <div style={{ gridColumn: 'span 2' }}>
          <SurfaceCard title="Ranking de jogadores" subtitle="Gols, assistências e desempate">
            {!data ? <EmptyPanel title="Contrato backend indisponível" description={error ?? 'Não foi possível carregar a auditoria de jogadores.'} /> : data.leaders.length === 0 ? <EmptyPanel title="Sem palpites cadastrados" description="Os palpites de artilheiro aparecerão aqui conforme os participantes forem preenchendo a tela inicial." /> : (
              <Stack gap="sm">
                {data.leaders.map((player) => (
                  <Text key={player.selectionKey}>{player.selectionLabel} · {player.predictionCount} palpites · {player.pointsAwardedTotal} pts</Text>
                ))}
              </Stack>
            )}
          </SurfaceCard>
        </div>
        <SurfaceCard title="Editor rápido" subtitle="Jogador selecionado">
          <Text c="dimmed">A liderança acima ajuda a revisar impacto potencial antes de qualquer ajuste manual de estatística.</Text>
        </SurfaceCard>
      </SimpleGrid>
    </Stack>
  );
}
