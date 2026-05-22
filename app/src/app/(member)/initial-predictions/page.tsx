import type { MemberPredictionsContract } from '../../../lib/contracts';
import { getServerCsrfToken } from '../../../lib/security';
import { fetchBackendData } from '../../../lib/session';
import { InitialPredictionsClient } from './client';

type Team = { id: string; name: string; code: string; iso2: string; flag?: string; group: string };
type Player = { id: string; name: string; teamCode: string; position: string; club: string; nationality: string };

export default async function InitialPredictionsPage() {
  const csrfToken = await getServerCsrfToken();
  const [{ data }, teamsRes, playersRes] = await Promise.all([
    fetchBackendData<MemberPredictionsContract>('/api/member/predictions'),
    fetchBackendData<Team[]>('/api/member/available-teams'),
    fetchBackendData<Player[]>('/api/member/available-players'),
  ]);

  const bonus = data?.competitionPredictions ?? [];
  const champion = bonus.find(b => b.predictionType === 'CHAMPION') ?? null;
  const scorer = bonus.find(b => b.predictionType === 'TOP_SCORER') ?? null;
  const locked = data?.competition.predictionLocked ?? false;
  const teams: Team[] = Array.isArray(teamsRes.data) ? teamsRes.data : [];
  const players: Player[] = Array.isArray(playersRes.data) ? playersRes.data : [];

  return (
    <InitialPredictionsClient
      teams={teams}
      players={players}
      champion={champion}
      scorer={scorer}
      locked={locked}
      csrfToken={csrfToken}
    />
  );
}
