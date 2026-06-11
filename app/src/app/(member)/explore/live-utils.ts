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

export function getLiveMatchGroups(
  matchPredictions: ExploreMatchPredictionContract[],
  nowMs: number,
): ExploreMatchPredictionContract[][] {
  const groups = new Map<string, ExploreMatchPredictionContract[]>();

  matchPredictions.forEach((prediction) => {
    if (!isMatchLive(prediction, nowMs)) {
      return;
    }

    const group = groups.get(prediction.matchId) ?? [];
    group.push(prediction);
    groups.set(prediction.matchId, group);
  });

  return Array.from(groups.values()).sort((left, right) => {
    const leftStartsAt = left[0]?.startsAt ? Date.parse(left[0].startsAt) : Number.POSITIVE_INFINITY;
    const rightStartsAt = right[0]?.startsAt ? Date.parse(right[0].startsAt) : Number.POSITIVE_INFINITY;

    const leftDistance = Number.isNaN(leftStartsAt) ? Number.POSITIVE_INFINITY : Math.abs(nowMs - leftStartsAt);
    const rightDistance = Number.isNaN(rightStartsAt) ? Number.POSITIVE_INFINITY : Math.abs(nowMs - rightStartsAt);

    if (leftDistance !== rightDistance) {
      return leftDistance - rightDistance;
    }

    return right.length - left.length;
  });
}
