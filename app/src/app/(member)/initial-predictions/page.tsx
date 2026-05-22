import { SimpleGrid, Stack, Text } from '@mantine/core';
import { InitialPredictionsForm } from '../../../components/member/initial-predictions-form';
import { HeroPanel, EmptyPanel, SurfaceCard } from '../../../components/layout/page-primitives';
import type { MemberPredictionsContract } from '../../../lib/contracts';
import { fetchBackendData } from '../../../lib/session';

export default async function InitialPredictionsPage() {
  const { data, error } = await fetchBackendData<MemberPredictionsContract>('/api/member/predictions');
  const bonusPredictions = data?.competitionPredictions ?? [];

  return (
    <Stack gap="lg">
      <HeroPanel
        eyebrow="Palpites iniciais"
        title="Defina campeão e"
        highlight="artilheiro"
        description="A composição segue o mock aprovado, mas as escolhas continuam sendo validadas e pontuadas apenas pelo backend."
        side={<SurfaceCard title="Janela de edição" subtitle="Status atual"><Text>{data?.competition.predictionLocked ? 'Palpites bloqueados' : 'Palpites abertos'}</Text></SurfaceCard>}
      />
      <SimpleGrid cols={{ base: 1, lg: 2 }}>
        <SurfaceCard title="Seu formulário" subtitle="Campeão + artilheiro">
          {data ? <InitialPredictionsForm predictions={bonusPredictions} competition={data.competition} /> : <EmptyPanel title="Sem contrato disponível" description={error ?? 'Ainda não foi possível carregar seus palpites iniciais.'} />}
        </SurfaceCard>
        <SurfaceCard title="Resumo salvo" subtitle="Estado atual">
          {bonusPredictions.length === 0 ? <EmptyPanel title="Nenhum palpite inicial salvo" description="Use o formulário ao lado para registrar campeão e artilheiro." /> : bonusPredictions.map((item) => <Text key={item.id}>{item.predictionType === 'CHAMPION' ? 'Campeão' : 'Artilheiro'}: {item.selectionLabel}</Text>)}
        </SurfaceCard>
      </SimpleGrid>
    </Stack>
  );
}
