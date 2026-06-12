import type { ExploreMatchPredictionContract } from '../../../lib/contracts';

export const LIVE_WINDOW_MS = 3 * 60 * 60 * 1000;
const LIVE_STATUSES = new Set(['LIVE', '1H', 'HT', '2H', 'ET', 'BT', 'P', 'INT']);
const FINISHED_STATUSES = new Set(['FT', 'AET', 'PEN', 'CANC', 'ABD', 'AWD', 'WO']);

export function formatPoints(pointsAwarded: number | null): { label: string; className: string } {
  if (pointsAwarded == null) {
    return { label: 'pend.', className: 'points pending' };
  }
  if (pointsAwarded === 0) {
    return { label: '+0', className: 'points zero' };
  }
  return { label: `+${pointsAwarded}`, className: 'points' };
}

export function formatMatchLabel(prediction: ExploreMatchPredictionContract): string {
  if (prediction.groupName) {
    return `Grupo ${prediction.groupName}`;
  }
  if (prediction.stageRound) {
    return `Rodada ${prediction.stageRound}`;
  }
  return prediction.phase.replaceAll('_', ' ');
}

export function formatKickoff(startsAt: string | null): string {
  if (!startsAt) {
    return 'Sem horário';
  }

  const parsed = Date.parse(startsAt);
  if (Number.isNaN(parsed)) {
    return 'Sem horário';
  }

  return new Intl.DateTimeFormat('pt-BR', {
    day: '2-digit',
    month: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  }).format(parsed);
}

export function isMatchLive(prediction: ExploreMatchPredictionContract, nowMs: number): boolean {
  if (LIVE_STATUSES.has(prediction.status)) {
    return true;
  }
  if (FINISHED_STATUSES.has(prediction.status)) {
    return false;
  }
  if (!prediction.startsAt) {
    return false;
  }

  const kickoffMs = Date.parse(prediction.startsAt);
  if (Number.isNaN(kickoffMs)) {
    return false;
  }

  return kickoffMs <= nowMs && nowMs <= kickoffMs + LIVE_WINDOW_MS;
}

export function buildMatchText(prediction: ExploreMatchPredictionContract): string {
  return `${prediction.homeTeam} ${prediction.awayTeam}`.toLowerCase();
}

type MatchGroup = {
  matchId: string;
  predictions: ExploreMatchPredictionContract[];
  startsAtMs: number;
  status: string;
};

function sortPredictions(
  left: ExploreMatchPredictionContract,
  right: ExploreMatchPredictionContract,
): number {
  return left.userName.localeCompare(right.userName, 'pt-BR');
}

function collectMatchGroups(
  matchPredictions: ExploreMatchPredictionContract[],
): MatchGroup[] {
  const groups = new Map<string, ExploreMatchPredictionContract[]>();

  matchPredictions.forEach((prediction) => {
    const group = groups.get(prediction.matchId) ?? [];
    group.push(prediction);
    groups.set(prediction.matchId, group);
  });

  return Array.from(groups.entries()).map(([matchId, predictions]) => {
    const orderedPredictions = [...predictions].sort(sortPredictions);
    const parsedStartsAt = predictions
      .map((prediction) => (prediction.startsAt ? Date.parse(prediction.startsAt) : Number.NaN))
      .find((value) => !Number.isNaN(value)) ?? Number.POSITIVE_INFINITY;

    return {
      matchId,
      predictions: orderedPredictions,
      startsAtMs: parsedStartsAt,
      status: orderedPredictions[0]?.status ?? '',
    };
  });
}

function sortMatchGroups(left: MatchGroup, right: MatchGroup): number {
  if (left.startsAtMs !== right.startsAtMs) {
    return left.startsAtMs - right.startsAtMs;
  }

  return left.matchId.localeCompare(right.matchId);
}

export function getLiveMatchGroups(
  matchPredictions: ExploreMatchPredictionContract[],
  nowMs: number,
): ExploreMatchPredictionContract[][] {
  return collectMatchGroups(matchPredictions)
    .filter((group) => group.predictions.some((prediction) => isMatchLive(prediction, nowMs)))
    .sort(sortMatchGroups)
    .map((group) => group.predictions);
}

export function getHighlightedMatchGroup(
  matchPredictions: ExploreMatchPredictionContract[],
  nowMs: number,
): { mode: 'live' | 'next'; predictions: ExploreMatchPredictionContract[] } | null {
  const groups = collectMatchGroups(matchPredictions).sort(sortMatchGroups);
  if (groups.length === 0) {
    return null;
  }

  const liveGroup = groups.find((group) => group.predictions.some((prediction) => isMatchLive(prediction, nowMs)));

  if (liveGroup) {
    return { mode: 'live', predictions: liveGroup.predictions };
  }

  const lastFinishedIndex = groups.reduce((latestIndex, group, index) => {
    if (FINISHED_STATUSES.has(group.status)) {
      return index;
    }
    return latestIndex;
  }, -1);

  const nextGroup = groups.find((group, index) => {
    if (FINISHED_STATUSES.has(group.status)) {
      return false;
    }
    return index > lastFinishedIndex;
  });

  return nextGroup ? { mode: 'next', predictions: nextGroup.predictions } : null;
}
