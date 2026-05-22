import { SimpleGrid, Stack, Text } from '@mantine/core';
import { WindowSettingsForm } from '../../../../components/admin/window-settings-form';
import { HeroPanel, EmptyPanel, SurfaceCard } from '../../../../components/layout/page-primitives';
import type { AdminSettingsContract } from '../../../../lib/contracts';
import { fetchBackendData } from '../../../../lib/session';

export default async function AdminSettingsPage() {
  const { data, error } = await fetchBackendData<AdminSettingsContract>('/api/admin/settings');

  return (
    <Stack gap="lg">
      <HeroPanel
        eyebrow="Regras e governança"
        title="Defina prazos, bloqueios e"
        highlight="pontuação"
        description="A página agora combina janela ativa, pesos de pontuação e regras operacionais mínimas em um contrato único orientado à tela."
        side={<SurfaceCard title="Janela atual" subtitle="Explore"><Text>{data ? new Date(data.competitionWindow.explore_release_at).toLocaleString('pt-BR') : 'Sem janela ativa'}</Text></SurfaceCard>}
      />
      <SimpleGrid cols={{ base: 1, xl: 3 }}>
        <div style={{ gridColumn: 'span 2' }}>
          <SurfaceCard title="Configurações principais" subtitle="Prazos, bloqueios e regras do bolão">
            {data ? <WindowSettingsForm window={data.competitionWindow} /> : <EmptyPanel title="Janela não encontrada" description={error ?? 'O backend não retornou a configuração ativa.'} />}
          </SurfaceCard>
        </div>
        <SurfaceCard title="Regras aplicadas" subtitle="Resumo funcional">
          <Text>Placar exato: {data?.scoring.exact_points ?? 3} pts</Text>
          <Text>Resultado correto: {data?.scoring.result_points ?? 1} pt</Text>
          <Text>Brasil ×{data?.scoring.brazil_multiplier ?? 2}</Text>
          <Text c="dimmed" mt="md">Sync pós-jogo: {data?.sync.post_match_offset_minutes ?? 115} min · limite {data?.sync.max_runs_per_day ?? 3}/dia</Text>
        </SurfaceCard>
      </SimpleGrid>
    </Stack>
  );
}
