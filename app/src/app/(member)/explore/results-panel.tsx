'use client';

import { useDeferredValue, useEffect, useState } from 'react';

import { TeamBadge } from '../../../components/ui/team-badge';
import type { ExploreMatchPredictionContract } from '../../../lib/contracts';

type ExploreResultsPanelProps = {
  exploreReleased: boolean;
  releasedParticipantCount: number;
  matchPredictions: ExploreMatchPredictionContract[];
};

type FilterMode = 'all' | 'participant' | 'match' | 'live';

const LIVE_WINDOW_MS = 3 * 60 * 60 * 1000;
const LIVE_STATUSES = new Set(['LIVE', '1H', 'HT', '2H', 'ET', 'BT', 'P', 'INT']);
const FINISHED_STATUSES = new Set(['FT', 'AET', 'PEN', 'CANC', 'ABD', 'AWD', 'WO']);

function formatPoints(pointsAwarded: number | null): { label: string; className: string } {
  if (pointsAwarded == null) {
    return { label: 'pend.', className: 'points pending' };
  }
  if (pointsAwarded === 0) {
    return { label: '+0', className: 'points zero' };
  }
  return { label: `+${pointsAwarded}`, className: 'points' };
}

function formatKickoff(startsAt: string | null): string {
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

function isMatchLive(prediction: ExploreMatchPredictionContract, nowMs: number): boolean {
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

function buildMatchText(prediction: ExploreMatchPredictionContract): string {
  return `${prediction.homeTeam} ${prediction.awayTeam}`.toLowerCase();
}

export function ExploreResultsPanel({
  exploreReleased,
  releasedParticipantCount,
  matchPredictions,
}: ExploreResultsPanelProps) {
  const [searchText, setSearchText] = useState('');
  const [filterMode, setFilterMode] = useState<FilterMode>('all');
  const [nowMs, setNowMs] = useState(() => Date.now());
  const deferredSearchText = useDeferredValue(searchText.trim().toLowerCase());

  useEffect(() => {
    const timer = window.setInterval(() => {
      setNowMs(Date.now());
    }, 60_000);

    return () => window.clearInterval(timer);
  }, []);

  const filteredPredictions = matchPredictions.filter((prediction) => {
    if (filterMode === 'live' && !isMatchLive(prediction, nowMs)) {
      return false;
    }

    if (!deferredSearchText) {
      return true;
    }

    if (filterMode === 'participant') {
      return prediction.userName.toLowerCase().includes(deferredSearchText);
    }

    if (filterMode === 'match' || filterMode === 'live') {
      return buildMatchText(prediction).includes(deferredSearchText);
    }

    return (
      prediction.userName.toLowerCase().includes(deferredSearchText)
      || buildMatchText(prediction).includes(deferredSearchText)
    );
  });

  const livePredictionCount = matchPredictions.filter((prediction) => isMatchLive(prediction, nowMs)).length;
  const placeholder = filterMode === 'participant'
    ? 'Buscar participante...'
    : filterMode === 'match' || filterMode === 'live'
      ? 'Buscar partida...'
      : 'Buscar participante ou partida...';

  return (
    <div className="card">
      <div className="card-header">
        <div><div className="card-title">Resultados de partidas</div><div className="card-subtitle">Palpites de placar</div></div>
        <div className={`pill ${exploreReleased ? 'ok' : 'warn'}`}><span className="dot" />{exploreReleased ? 'liberado' : 'bloqueado'}</div>
      </div>
      <div className="card-body">
        {!exploreReleased ? (
          <div style={{ textAlign: 'center', padding: 24, color: 'var(--tx3)', fontSize: 13 }}>
            <div style={{ fontSize: 20, marginBottom: 8 }}>🔒</div>
            Os palpites de placar ficam visíveis após o fechamento oficial configurado pelo admin.
          </div>
        ) : matchPredictions.length === 0 ? (
          <div style={{ textAlign: 'center', padding: 24, color: 'var(--tx3)', fontSize: 13 }}>Nenhum palpite de partida registrado.</div>
        ) : (
          <div className="explore-results-panel">
            <div className="explore-results-meta">
              {matchPredictions.length} palpites de partidas visíveis entre {releasedParticipantCount} participantes.
            </div>

            <div className="explore-results-filters">
              <button
                type="button"
                className={`explore-filter-chip${filterMode === 'all' ? ' active' : ''}`}
                onClick={() => setFilterMode('all')}
              >
                Tudo
              </button>
              <button
                type="button"
                className={`explore-filter-chip${filterMode === 'participant' ? ' active' : ''}`}
                onClick={() => setFilterMode('participant')}
              >
                Participante
              </button>
              <button
                type="button"
                className={`explore-filter-chip${filterMode === 'match' ? ' active' : ''}`}
                onClick={() => setFilterMode('match')}
              >
                Partida
              </button>
              <button
                type="button"
                className={`explore-filter-chip${filterMode === 'live' ? ' active' : ''}`}
                onClick={() => setFilterMode('live')}
              >
                Ao vivo agora {livePredictionCount > 0 ? `(${livePredictionCount})` : ''}
              </button>
            </div>

            <div className="input-wrap">
              <span className="input-icon">⌕</span>
              <input
                type="text"
                value={searchText}
                onChange={(event) => setSearchText(event.target.value)}
                className="field-input with-icon"
                placeholder={placeholder}
              />
            </div>

            <div className="explore-results-summary">
              {filteredPredictions.length} resultado{filteredPredictions.length !== 1 ? 's' : ''} encontrado{filteredPredictions.length !== 1 ? 's' : ''}
            </div>

            {filteredPredictions.length === 0 ? (
              <div className="explore-results-empty">
                Nenhum palpite encontrado para o filtro atual.
              </div>
            ) : (
              <div className="explore-results-scroll">
                {filteredPredictions.map((prediction) => {
                  const badge = formatPoints(prediction.pointsAwarded);
                  const isLive = isMatchLive(prediction, nowMs);

                  return (
                    <div key={`${prediction.userId}-${prediction.matchId}`} className="explore-results-row">
                      <div className="explore-results-user">
                        <div className="explore-results-user-name">{prediction.userName}</div>
                        <div className="explore-results-user-meta">
                          {formatKickoff(prediction.startsAt)}
                          {isLive ? ' · em andamento' : ''}
                        </div>
                      </div>

                      <div className="explore-results-match">
                        <span className="player-team-inline">
                          <TeamBadge name={prediction.homeTeam} flag={prediction.homeFlag} iso2={prediction.homeIso2} code={prediction.homeCode} compact />
                          <span style={{ color: 'var(--tx3)' }}>×</span>
                          <TeamBadge name={prediction.awayTeam} flag={prediction.awayFlag} iso2={prediction.awayIso2} code={prediction.awayCode} compact />
                        </span>
                        <span className="explore-results-score">
                          {prediction.homeGoals} × {prediction.awayGoals}
                        </span>
                      </div>

                      <div className="explore-results-side">
                        {isLive ? <span className="badge orange">ao vivo</span> : null}
                        <div className={badge.className}>{badge.label}</div>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
