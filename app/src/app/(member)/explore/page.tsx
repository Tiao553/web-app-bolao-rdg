import type { ExploreContract } from '../../../lib/contracts';
import { fetchBackendData } from '../../../lib/session';
import { ExploreClient } from './explore-client';

const FALLBACK_DATA: ExploreContract = {
  exploreState: 'locked',
  exploreReleased: false,
  matchGroups: [],
  matchPredictions: [],
  competitionPredictions: [],
};

export default async function ExplorePage() {
  const { data, error } = await fetchBackendData<ExploreContract>('/api/member/explore');
  return (
    <ExploreClient
      exploreState={data?.exploreState ?? FALLBACK_DATA.exploreState}
      matchGroups={data?.matchGroups ?? FALLBACK_DATA.matchGroups}
      competitionPredictions={data?.competitionPredictions ?? FALLBACK_DATA.competitionPredictions}
      loadError={error}
    />
  );
}
