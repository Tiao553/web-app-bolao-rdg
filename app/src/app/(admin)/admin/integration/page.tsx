import { AdminIntegrationControls } from '../../../../components/admin/integration-controls';
import type { AdminIntegrationContract } from '../../../../lib/contracts';
import { getServerCsrfToken } from '../../../../lib/security';
import { fetchBackendData } from '../../../../lib/session';

const FALLBACK_DATA: AdminIntegrationContract = {
  primaryProvider: 'THE_SPORTS_DB',
  fallbackProvider: 'API_FOOTBALL',
  activeProvider: 'THE_SPORTS_DB',
  apiConfigured: true,
  dailyRunLimit: 0,
  allowedTerminalStatuses: [],
  autoSyncEnabled: false,
  autoSyncIntervalMinutes: 60,
  autoSyncIntervalOptions: [1, 5, 15, 60],
  schedulerMode: 'EXTERNAL_TRIGGER_ONLY',
  cronTokenConfigured: false,
  lastAutoSyncAt: null,
  nextAutoSyncAt: null,
  autoSyncStatus: 'disabled',
  lastSyncs: [],
};

export default async function AdminIntegrationPage() {
  const csrfToken = await getServerCsrfToken();
  const { data } = await fetchBackendData<AdminIntegrationContract>('/api/admin/integration');

  return <AdminIntegrationControls csrfToken={csrfToken} initialData={data ?? FALLBACK_DATA} />;
}
