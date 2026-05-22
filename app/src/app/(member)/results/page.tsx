import { Badge, Group, SimpleGrid, Stack, Text } from '@mantine/core';
import { HeroPanel, EmptyPanel, SurfaceCard } from '../../../components/layout/page-primitives';
import type { MemberResultsContract } from '../../../lib/contracts';
import { fetchBackendData } from '../../../lib/session';

export default async function ResultsPage() {
  const { data, error } = await fetchBackendData<MemberResultsContract>('/api/member/results');

  return (
    <Stack gap="lg">
      <HeroPanel
        eyebrow="Resultados oficiais"
        title="Confira seus pontos por"
        highlight="partida"
        description="A tela segue o mock aprovado com breakdown por regra, lista de partidas e leitura direta do backend orientada à tela."
        side={<SurfaceCard title="Resumo da fase" subtitle="Pontos acumulados"><Text>{data?.summary.totalPoints ?? 0} pontos no total</Text></SurfaceCard>}
      />
      <SimpleGrid cols={{ base: 1, xl: 3 }}>
        <div style={{ gridColumn: 'span 2' }}>
          <SurfaceCard title="Partidas finalizadas" subtitle="Resultado oficial × seu palpite">
            {!data ? <EmptyPanel title="Contrato backend indisponível" description={error ?? 'Não foi possível carregar os resultados.'} /> : data.matches.length === 0 ? <EmptyPanel title="Sem partidas pontuadas" description="Seus resultados aparecerão aqui assim que houver jogos com placar oficial e palpite salvo." /> : (
              <Stack gap="sm">
                {data.matches.map((match) => (
                  <Group key={match.matchId} justify="space-between" align="flex-start" p="md" style={{ border: '1px solid var(--rdg-bd)', borderRadius: 18, background: 'var(--rdg-s2)' }}>
                    <div>
                      <Text fw={800}>{match.homeTeam} × {match.awayTeam}</Text>
                      <Text size="sm" c="dimmed">{match.phase}{match.groupName ? ` · Grupo ${match.groupName}` : ''}{match.slot ? ` · ${match.slot}` : ''}</Text>
                      <Text size="sm">Oficial: {match.officialHomeGoals ?? '—'} × {match.officialAwayGoals ?? '—'} · Seu palpite: {match.predictedHomeGoals ?? '—'} × {match.predictedAwayGoals ?? '—'}</Text>
                    </div>
                    <Stack gap={6} align="flex-end">
                      <Badge color={match.pointsAwarded ? 'green' : 'gray'} variant="light">{match.pointsAwarded ?? 0} pts</Badge>
                      {match.involvesBrazil ? <Badge color="orange" variant="outline">Brasil ×2</Badge> : null}
                    </Stack>
                  </Group>
                ))}
              </Stack>
            )}
          </SurfaceCard>
        </div>
        <SurfaceCard title="Breakdown" subtitle="Pontos por regra">
          <Text>Exatos: {data?.summary.exactHits ?? 0}</Text>
          <Text>Resultados corretos: {data?.summary.correctOutcomes ?? 0}</Text>
          <Text>Bônus Brasil ×2: {data?.summary.brazilBonusHits ?? 0}</Text>
          <Text>Campeão: {data?.summary.championPoints ?? 0} pts</Text>
          <Text>Artilheiro: {data?.summary.topScorerPoints ?? 0} pts</Text>
        </SurfaceCard>
      </SimpleGrid>
    </Stack>
  );
}
