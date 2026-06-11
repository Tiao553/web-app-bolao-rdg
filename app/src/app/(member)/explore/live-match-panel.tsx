'use client';

import { useEffect, useState } from 'react';

import { TeamBadge } from '../../../components/ui/team-badge';
import type { ExploreMatchPredictionContract } from '../../../lib/contracts';
import { formatKickoff, formatPoints, getLiveMatchGroups } from './live-utils';

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

  const liveGroups = getLiveMatchGroups(matchPredictions, nowMs);
  const currentMatchPredictions = liveGroups[0] ?? [];
  const currentMatch = currentMatchPredictions[0] ?? null;

  return (
    <div className="card">
      <div className="card-header">
        <div><div className="card-title">Jogo ao vivo agora</div><div className="card-subtitle">Palpites do confronto em andamento</div></div>
        <div className={`pill ${currentMatch ? 'orange' : 'neutral'}`}><span className="dot" />{currentMatch ? 'ao vivo' : 'sem jogo agora'}</div>
      </div>
      <div className="card-body">
        {!exploreReleased ? (
          <div style={{ textAlign: 'center', padding: 20, color: 'var(--tx3)', fontSize: 13 }}>
            Acompanhe este bloco quando o Explore estiver liberado.
          </div>
        ) : !currentMatch ? (
          <div className="explore-live-empty">
            Nenhuma partida em andamento neste momento. Quando houver jogo ao vivo, este bloco vai destacar todos os palpites do confronto atual.
          </div>
        ) : (
          <div className="explore-live-panel">
            <div className="explore-live-match-head">
              <div className="explore-live-match-meta">
                <span className="badge orange">agora</span>
                <span className="explore-live-kickoff">{formatKickoff(currentMatch.startsAt)}</span>
              </div>
              <div className="player-team-inline">
                <TeamBadge name={currentMatch.homeTeam} flag={currentMatch.homeFlag} iso2={currentMatch.homeIso2} code={currentMatch.homeCode} compact />
                <span style={{ color: 'var(--tx3)' }}>×</span>
                <TeamBadge name={currentMatch.awayTeam} flag={currentMatch.awayFlag} iso2={currentMatch.awayIso2} code={currentMatch.awayCode} compact />
              </div>
              <div className="explore-live-summary">
                {currentMatchPredictions.length} palpite{currentMatchPredictions.length !== 1 ? 's' : ''} liberado{currentMatchPredictions.length !== 1 ? 's' : ''}
              </div>
            </div>

            <div className="explore-live-scroll">
              {currentMatchPredictions.map((prediction) => {
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
