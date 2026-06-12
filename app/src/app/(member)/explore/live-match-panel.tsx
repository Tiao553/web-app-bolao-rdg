'use client';

import { useEffect, useState } from 'react';

import { TeamBadge } from '../../../components/ui/team-badge';
import type { ExploreMatchPredictionContract } from '../../../lib/contracts';
import { formatMatchLabel, formatPoints, getHighlightedMatchGroup } from './live-utils';

type ExploreLiveMatchPanelProps = {
  exploreReleased: boolean;
  matchPredictions: ExploreMatchPredictionContract[];
};

export function ExploreLiveMatchPanel({
  exploreReleased,
  matchPredictions,
}: ExploreLiveMatchPanelProps) {
  const [nowMs, setNowMs] = useState(() => Date.now());

  useEffect(() => {
    const timer = window.setInterval(() => {
      setNowMs(Date.now());
    }, 60_000);

    return () => window.clearInterval(timer);
  }, []);

  const highlightedMatch = getHighlightedMatchGroup(matchPredictions, nowMs);
  const highlightedMode = highlightedMatch?.mode ?? 'next';
  const highlightedPredictions = highlightedMatch?.predictions ?? [];
  const highlightedMatchData = highlightedPredictions[0] ?? null;
  const title = highlightedMode === 'live' ? 'Jogo ao vivo agora' : 'Próximo jogo';
  const subtitle = highlightedMode === 'live'
    ? 'Palpites do confronto em andamento'
    : 'Palpites do próximo confronto';
  const badgeLabel = highlightedMode === 'live' ? 'ao vivo' : 'próximo';
  const badgeTone = highlightedMode === 'live' ? 'orange' : 'ok';

  return (
    <div className="card">
      <div className="card-header">
        <div><div className="card-title">{title}</div><div className="card-subtitle">{subtitle}</div></div>
        <div className={`pill ${highlightedMatchData ? badgeTone : 'neutral'}`}><span className="dot" />{highlightedMatchData ? badgeLabel : 'sem jogo'}</div>
      </div>
      <div className="card-body">
        {!exploreReleased ? (
          <div style={{ textAlign: 'center', padding: 20, color: 'var(--tx3)', fontSize: 13 }}>
            Acompanhe este bloco quando o Explore estiver liberado.
          </div>
        ) : !highlightedMatchData ? (
          <div className="explore-live-empty">
            Nenhum jogo disponível neste momento. Quando houver uma partida ao vivo, este bloco destaca os palpites do confronto atual; fora disso, mostra o próximo confronto liberado.
          </div>
        ) : (
          <div className="explore-live-panel">
            <div className="explore-live-match-head">
              <div className="explore-live-match-meta">
                <span className={`badge ${badgeTone}`}>{highlightedMode === 'live' ? 'agora' : 'seguinte'}</span>
                <span className="badge neutral">{formatMatchLabel(highlightedMatchData)}</span>
              </div>
              <div className="player-team-inline">
                <TeamBadge name={highlightedMatchData.homeTeam} flag={highlightedMatchData.homeFlag} iso2={highlightedMatchData.homeIso2} code={highlightedMatchData.homeCode} compact />
                <span style={{ color: 'var(--tx3)' }}>×</span>
                <TeamBadge name={highlightedMatchData.awayTeam} flag={highlightedMatchData.awayFlag} iso2={highlightedMatchData.awayIso2} code={highlightedMatchData.awayCode} compact />
              </div>
              <div className="explore-live-summary">
                {highlightedPredictions.length} palpite{highlightedPredictions.length !== 1 ? 's' : ''} do {highlightedMode === 'live' ? 'jogo em andamento' : 'próximo jogo'}
              </div>
            </div>

            <div className="explore-live-scroll">
              {highlightedPredictions.map((prediction) => {
                const badge = formatPoints(prediction.pointsAwarded);
                return (
                  <div key={`${prediction.userId}-${prediction.matchId}`} className="explore-live-row">
                    <div className="explore-live-user">{prediction.userName}</div>
                    <div className="explore-live-score">{prediction.homeGoals} × {prediction.awayGoals}</div>
                    <div className={badge.className}>{badge.label}</div>
                  </div>
                );
              })}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
