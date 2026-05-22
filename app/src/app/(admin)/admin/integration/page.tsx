import { SimpleGrid, Stack, Text } from '@mantine/core';
import { SyncControls } from '../../../../components/admin/sync-controls';
import { HeroPanel, SurfaceCard } from '../../../../components/layout/page-primitives';
import type { AdminIntegrationContract } from '../../../../lib/contracts';
import { fetchBackendData } from '../../../../lib/session';

export default async function AdminIntegrationPage() {
  const { data } = await fetchBackendData<AdminIntegrationContract>('/api/admin/integration');

  return (
    <Stack gap="lg">
      <HeroPanel
        eyebrow="API-SPORTS Football v3"
        title="Integração com"
        highlight="v3.football.api-sports.io"
        description="A tela segue o mock com foco em saúde operacional, fluxo de sync e logs, usando o gatilho real de sincronização já exposto pelo backend."
        side={<SurfaceCard title="Conexão ativa" subtitle="Operação"><SyncControls /></SurfaceCard>}
      />
      <SimpleGrid cols={{ base: 1, lg: 2 }}>
        <SurfaceCard title="Configuração da integração" subtitle="Fonte oficial e agenda">
          <Text>Provider: {data?.primaryProvider ?? 'API_FOOTBALL'}</Text>
          <Text>Fallback: {data?.fallbackProvider ?? 'GOOGLE_SHEETS'}</Text>
          <Text>Chave configurada: {data?.apiConfigured ? 'sim' : 'não'}</Text>
        </SurfaceCard>
        <SurfaceCard title="Fluxo de sincronização" subtitle="Pipeline operacional">
          <Text>Runs/dia: {data?.dailyRunLimit ?? 0}</Text>
          <Text>Status terminais: {data?.allowedTerminalStatuses.join(', ') ?? '—'}</Text>
          <Text>Últimos eventos: {data?.lastSyncs.length ?? 0}</Text>
          <Text>Recalcular ranking e Explore após cada sync elegível.</Text>
        </SurfaceCard>
      </SimpleGrid>
    </Stack>
  );
}
