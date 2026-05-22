import type { PhaseScreenContract } from '../../../lib/contracts';
import { fetchBackendData } from '../../../lib/session';
import { PhasePredictionsClient } from './client';

export default async function PhasePredictionsPage() {
  const { data } = await fetchBackendData<PhaseScreenContract>('/api/member/phase-screen');
  const rounds = data?.rounds ?? [];

  return <PhasePredictionsClient rounds={rounds} />;
}
