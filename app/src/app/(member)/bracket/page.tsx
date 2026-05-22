import { Badge, Group, SimpleGrid, Stack, Text } from '@mantine/core';
import { HeroPanel, EmptyPanel, SurfaceCard } from '../../../components/layout/page-primitives';
import type { MemberBracketContract } from '../../../lib/contracts';
import { fetchBackendData } from '../../../lib/session';

export default async function BracketPage() {
  const { data, error } = await fetchBackendData<MemberBracketContract>('/api/member/bracket');

  return (
    <Stack gap="lg">
      <HeroPanel
        eyebrow="Mata-mata oficial"
        title="Chaveamento da Copa com"
        highlight="16 avos"
        description="A composição segue o mock com árvore por slot, feeders, destaque para alocações de terceiros e conexão direta com o contrato oficial do backend."
        side={<SurfaceCard title="Campeão projetado" subtitle="Seu palpite"><Text>{data?.championPrediction ?? 'Sem campeão definido'}</Text></SurfaceCard>}
      />
      <SimpleGrid cols={{ base: 1, xl: 3 }}>
        <div style={{ gridColumn: 'span 2' }}>
          <SurfaceCard title="Árvore eliminatória" subtitle="SVG conectado · oficial">
            {!data ? <EmptyPanel title="Contrato backend indisponível" description={error ?? 'Não foi possível carregar o chaveamento.'} /> : (
              <Stack gap="sm">
                {data.matches.map((match) => (
                  <Group key={match.slot} justify="space-between" p="md" style={{ border: '1px solid var(--rdg-bd)', borderRadius: 18, background: 'var(--rdg-s2)' }}>
                    <div>
                      <Text fw={800}>{match.slot} · {match.phase}</Text>
                      <Text>{match.homeTeam ?? 'TBD'} × {match.awayTeam ?? 'TBD'}</Text>
                      <Text size="sm" c="dimmed">{match.feederHomeKey ?? 'seed'} → {match.feederAwayKey ?? 'seed'}</Text>
                    </div>
                    <Stack gap={6} align="flex-end">
                      {match.winnerTeam ? <Badge color="green" variant="light">{match.winnerTeam}</Badge> : <Badge color="gray" variant="outline">Aguardando</Badge>}
                      {match.hasManualOverride ? <Badge color="orange" variant="outline">override</Badge> : null}
                    </Stack>
                  </Group>
                ))}
              </Stack>
            )}
          </SurfaceCard>
        </div>
        <SurfaceCard title="Governança" subtitle="Regra crítica">
          {data?.thirdPlaceSlots.length ? data.thirdPlaceSlots.map((slot) => <Text key={slot.slot}>{slot.slot}: {slot.assignedGroup ?? 'TBD'} {slot.assignedTeam ? `· ${slot.assignedTeam}` : ''}</Text>) : <Text c="dimmed">O chaveamento continua protegido: palpites dos usuários nunca alteram a árvore oficial.</Text>}
        </SurfaceCard>
      </SimpleGrid>
    </Stack>
  );
}
