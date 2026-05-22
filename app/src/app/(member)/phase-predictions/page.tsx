import { SimpleGrid, Stack, Text } from '@mantine/core';
import { HeroPanel, EmptyPanel, SurfaceCard } from '../../../components/layout/page-primitives';
import { PhasePredictionsForm } from '../../../components/member/phase-predictions-form';
import type { MemberPredictionsContract } from '../../../lib/contracts';
import { fetchBackendData } from '../../../lib/session';

export default async function PhasePredictionsPage() {
  const { data, error } = await fetchBackendData<MemberPredictionsContract>('/api/member/predictions');
  const predictions = data?.matchPredictions ?? [];

  return (
    <Stack gap="lg">
      <HeroPanel
        eyebrow="Palpites por fase"
        title="Preencha os placares"
        highlight="jogo a jogo"
        description="Como o backend atual ainda não expõe o catálogo completo de partidas para esta tela, a grade usa os palpites já existentes e sinaliza claramente quando o contrato estiver incompleto."
        side={<SurfaceCard title="Progresso da fase" subtitle="Predições disponíveis"><Text>{predictions.length} partidas carregadas</Text></SurfaceCard>}
      />
      <SimpleGrid cols={{ base: 1, xl: 3 }}>
        <SurfaceCard title="Rodadas" subtitle="Navegação mock-driven">
          <Text>Grupo A · aberto</Text>
          <Text c="dimmed">Grupo B · aberto</Text>
          <Text c="dimmed">Grupo C · aberto</Text>
          <Text c="dimmed">Mata-mata · aguardando chaveamento</Text>
        </SurfaceCard>
        <div style={{ gridColumn: 'span 2' }}>
          <SurfaceCard title="Partidas editáveis" subtitle="Placares salvos">
            {data ? <PhasePredictionsForm predictions={predictions} competition={data.competition} /> : <EmptyPanel title="Não foi possível montar a fase" description={error ?? 'Sem dados de palpites disponíveis.'} />}
          </SurfaceCard>
        </div>
      </SimpleGrid>
    </Stack>
  );
}
