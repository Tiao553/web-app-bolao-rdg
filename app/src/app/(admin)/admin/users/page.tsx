import { SimpleGrid, Stack } from '@mantine/core';
import { UserModerationTable } from '../../../../components/admin/user-moderation-table';
import { HeroPanel, EmptyPanel, MetricCard, SurfaceCard } from '../../../../components/layout/page-primitives';
import type { AdminUserContract } from '../../../../lib/contracts';
import { fetchBackendData } from '../../../../lib/session';

export default async function AdminUsersPage() {
  const { data, error } = await fetchBackendData<AdminUserContract[]>('/api/admin/users');
  const users = data ?? [];

  return (
    <Stack gap="lg">
      <HeroPanel
        eyebrow="Controle de acesso"
        title="Aprove quem pode"
        highlight="participar"
        description="O fluxo de aprovação, rejeição e bloqueio já usa o endpoint administrativo existente e mantém a regra principal fora do cliente."
        side={<SurfaceCard title="Revisão pendente" subtitle="Governança"><MetricCard value={users.filter((user) => user.access_status === 'PENDING').length} label="aguardando aprovação" color="var(--mantine-color-rdg-orange-5)" /></SurfaceCard>}
      />
      <SurfaceCard title="Participantes cadastrados" subtitle="Aprovação, bloqueio e auditoria">
        {error && !data ? <EmptyPanel title="Não foi possível carregar usuários" description={error} /> : <UserModerationTable initialUsers={users} />}
      </SurfaceCard>
    </Stack>
  );
}
