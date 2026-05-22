import { SimpleGrid, Stack, Text } from '@mantine/core';
import { SyncControls } from '../../../../components/admin/sync-controls';
import { HeroPanel, MetricCard, ProgressList, SurfaceCard } from '../../../../components/layout/page-primitives';
import type { AdminDashboardContract } from '../../../../lib/contracts';
import { fetchBackendData } from '../../../../lib/session';

export default async function AdminDashboardPage() {
  const { data } = await fetchBackendData<AdminDashboardContract>('/api/admin/dashboard');

  return (
    <Stack gap="lg">
      <HeroPanel
        eyebrow="Painel administrativo"
        title="Controle do"
        highlight="Bolão da Copa"
        description="A visão principal reúne governança de usuários, janela operacional e acionamento de sincronização, mantendo no cliente apenas composição e interação."
        side={<SurfaceCard title="Status operacional" subtitle="Ações rápidas"><SyncControls /></SurfaceCard>}
      />
      <SimpleGrid cols={{ base: 1, md: 4 }}>
        <MetricCard value={data?.users.total ?? 0} label="usuários cadastrados" color="var(--mantine-color-rdg-orange-5)" />
        <MetricCard value={data?.users.approved ?? 0} label="participantes aprovados" />
        <MetricCard value={data?.users.pending ?? 0} label="pendentes de revisão" />
        <MetricCard value={data?.matches.finished ?? 0} label="jogos finalizados" />
      </SimpleGrid>
      <SimpleGrid cols={{ base: 1, lg: 2 }}>
        <SurfaceCard title="Fila de governança" subtitle="Ações que exigem admin">
          <Text>{data?.users.pending ?? 0} usuários aguardando aprovação.</Text>
          <Text c="dimmed">Última janela: {data ? new Date(data.predictionCloseAt).toLocaleString('pt-BR') : '—'}.</Text>
        </SurfaceCard>
        <SurfaceCard title="Cobertura operacional" subtitle="Janela oficial">
          <ProgressList items={[
            { label: 'Aprovados', value: data?.users.total ? ((data.users.approved / data.users.total) * 100) : 0 },
            { label: 'Pendentes', value: data?.users.total ? ((data.users.pending / data.users.total) * 100) : 0 },
            { label: 'Overrides', value: data?.matches.total ? ((data.matches.overridden / data.matches.total) * 100) : 0 }
          ]} />
        </SurfaceCard>
      </SimpleGrid>
    </Stack>
  );
}
