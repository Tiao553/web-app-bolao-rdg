import type { PhaseScreenContract } from '../../../lib/contracts';
import { getServerCsrfToken } from '../../../lib/security';
import { fetchBackendData } from '../../../lib/session';
import { PhasePredictionsClient } from './client';

export default async function PhasePredictionsPage() {
  const csrfToken = await getServerCsrfToken();
  const { data } = await fetchBackendData<PhaseScreenContract>('/api/member/phase-screen');
  const rounds = data?.rounds ?? [];

  return <PhasePredictionsClient rounds={rounds} csrfToken={csrfToken} />;
}
