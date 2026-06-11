import { TeamBadge } from '../../../components/ui/team-badge';
import type { ExploreContract, ExploreMatchPredictionContract } from '../../../lib/contracts';
import { fetchBackendData } from '../../../lib/session';
import { ExploreLiveMatchPanel } from './live-match-panel';
import { ExploreResultsPanel } from './results-panel';

type ParticipantEntry = {
  name: string;
  champion?: {
    label: string;
    teamName?: string | null;
    teamCode?: string | null;
    teamFlag?: string | null;
    teamIso2?: string | null;
  };
  scorer?: {
    label: string;
    teamName?: string | null;
    teamCode?: string | null;
    teamFlag?: string | null;
    teamIso2?: string | null;
  };
  matches: ExploreMatchPredictionContract[];
};

function createParticipantEntry(name: string): ParticipantEntry {
  return { name, matches: [] };
}

function formatMatchLabel(prediction: ExploreMatchPredictionContract): string {
  if (prediction.groupName) {
    return `Grupo ${prediction.groupName}`;
  }
  if (prediction.stageRound) {
    return `Rodada ${prediction.stageRound}`;
  }
  return prediction.phase.replaceAll('_', ' ');
}

function formatPoints(pointsAwarded: number | null): { label: string; className: string } {
  if (pointsAwarded == null) {
    return { label: 'pend.', className: 'points pending' };
  }
  if (pointsAwarded === 0) {
    return { label: '+0', className: 'points zero' };
  }
  return { label: `+${pointsAwarded}`, className: 'points' };
}

export default async function ExplorePage() {
  const { data } = await fetchBackendData<ExploreContract>('/api/member/explore');
  const exploreReleased = data?.exploreReleased ?? false;
  const competitionPredictions = data?.competitionPredictions ?? [];
  const matchPredictions = data?.matchPredictions ?? [];

  const grouped = new Map<string, ParticipantEntry>();
  competitionPredictions.forEach((item) => {
    const entry = grouped.get(item.userId) ?? createParticipantEntry(item.userName);
    const selection = {
      label: item.selectionLabel,
      teamName: item.selectionTeamName,
      teamCode: item.selectionTeamCode,
      teamFlag: item.selectionTeamFlag,
      teamIso2: item.selectionTeamIso2,
    };
    if (item.predictionType === 'CHAMPION') {
      entry.champion = selection;
    } else {
      entry.scorer = selection;
    }
    grouped.set(item.userId, entry);
  });
  matchPredictions.forEach((item) => {
    const entry = grouped.get(item.userId) ?? createParticipantEntry(item.userName);
    entry.matches.push(item);
    grouped.set(item.userId, entry);
  });

  const entries = Array.from(grouped.entries()).sort(([, left], [, right]) => {
    if (right.matches.length !== left.matches.length) {
      return right.matches.length - left.matches.length;
    }
    return left.name.localeCompare(right.name, 'pt-BR');
  });
  const releasedParticipantCount = entries.filter(([, entry]) => entry.matches.length > 0).length;
  const championInsight = (() => {
    const counts: Record<string, number> = {};
    entries.forEach(([, entry]) => {
      if (entry.champion) {
        counts[entry.champion.label] = (counts[entry.champion.label] || 0) + 1;
      }
    });
    const top = Object.entries(counts).sort((a, b) => b[1] - a[1])[0];
    return top ? `${top[0]} (${top[1]}x)` : '—';
  })();

  const scorerInsight = (() => {
    const counts: Record<string, number> = {};
    entries.forEach(([, entry]) => {
      if (entry.scorer) {
        counts[entry.scorer.label] = (counts[entry.scorer.label] || 0) + 1;
      }
    });
    const top = Object.entries(counts).sort((a, b) => b[1] - a[1])[0];
    return top ? `${top[0]} (${top[1]}x)` : '—';
  })();

  const scorelineInsight = (() => {
    const counts: Record<string, number> = {};
    matchPredictions.forEach((item) => {
      const key = `${item.homeGoals} × ${item.awayGoals}`;
      counts[key] = (counts[key] || 0) + 1;
    });
    const top = Object.entries(counts).sort((a, b) => b[1] - a[1])[0];
    return top ? `${top[0]} (${top[1]}x)` : '—';
  })();

  return (
    <>
      <section className="hero">
        <div className="hero-content">
          <div>
            <div className="eyebrow"><span className="dot" />Explore</div>
            <h1>Palpites de <span>campeão e artilheiro</span>.</h1>
            <p>Campeão e artilheiro são sempre públicos. Os resultados de partidas aparecem de forma cumulativa por fase.</p>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 12, alignItems: 'flex-start' }}>
            <div className={`pill ${exploreReleased ? 'ok' : 'warn'}`} style={{ alignSelf: 'flex-start', marginTop: 4 }}>
              <span className="dot" />{exploreReleased ? 'Resultados liberados' : 'Resultados bloqueados'}
            </div>
            {exploreReleased ? (
              <a href="#released-predictions" className="ghost-button">
                Ver palpites dos participantes
              </a>
            ) : null}
          </div>
        </div>
      </section>

      <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: 20 }}>
        <div className="card" id="released-predictions">
          <div className="card-header">
            <div><div className="card-title">Palpites dos participantes</div><div className="card-subtitle">Campeão, artilheiro e placares liberados</div></div>
            <div className={`pill ${exploreReleased ? 'ok' : 'warn'}`}><span className="dot" />{exploreReleased ? 'público' : 'bloqueado'}</div>
          </div>
          <div className="card-body">
            {entries.length === 0 ? (
              <div style={{ textAlign: 'center', padding: 32, color: 'var(--tx3)', fontSize: 14 }}>Nenhum palpite registrado ainda.</div>
            ) : (
              <div className="explore-grid">
                {entries.map(([uid, entry]) => (
                  <div key={uid} className="explore-card">
                    <div className="explore-card-name">{entry.name}</div>
                    <div className="prediction-row">
                      <div className="prediction-label">Campeão</div>
                      <div className="prediction-value">
                        {entry.champion
                          ? <TeamBadge name={entry.champion.teamName ?? entry.champion.label} flag={entry.champion.teamFlag} iso2={entry.champion.teamIso2} code={entry.champion.teamCode} compact />
                          : <span style={{ color: 'var(--tx3)' }}>—</span>}
                      </div>
                      <div className="points">{entry.champion ? '+10' : '—'}</div>
                    </div>
                    <div className="prediction-row">
                      <div className="prediction-label">Artilheiro</div>
                      <div className="prediction-value">
                        {entry.scorer ? (
                          <span className="player-team-inline">
                            <span>{entry.scorer.label}</span>
                            {entry.scorer.teamName
                              ? <TeamBadge name={entry.scorer.teamName} flag={entry.scorer.teamFlag} iso2={entry.scorer.teamIso2} code={entry.scorer.teamCode} compact />
                              : null}
                          </span>
                        ) : <span style={{ color: 'var(--tx3)' }}>—</span>}
                      </div>
                      <div className="points">{entry.scorer ? '+15' : '—'}</div>
                    </div>
                    {exploreReleased ? (
                      entry.matches.length > 0 ? (
                        entry.matches.slice(0, 3).map((prediction) => {
                          const badge = formatPoints(prediction.pointsAwarded);
                          return (
                            <div key={`${uid}-${prediction.matchId}`} className="prediction-row">
                              <div className="prediction-label">{formatMatchLabel(prediction)}</div>
                              <div className="prediction-value" style={{ flexDirection: 'column', alignItems: 'flex-start', gap: 4 }}>
                                <span className="player-team-inline">
                                  <TeamBadge name={prediction.homeTeam} flag={prediction.homeFlag} iso2={prediction.homeIso2} code={prediction.homeCode} compact />
                                  <span style={{ color: 'var(--tx3)' }}>×</span>
                                  <TeamBadge name={prediction.awayTeam} flag={prediction.awayFlag} iso2={prediction.awayIso2} code={prediction.awayCode} compact />
                                </span>
                                <span style={{ fontFamily: 'Fira Code, monospace', color: 'var(--or)', fontSize: 12 }}>
                                  {prediction.homeGoals} × {prediction.awayGoals}
                                </span>
                              </div>
                              <div className={badge.className}>{badge.label}</div>
                            </div>
                          );
                        })
                      ) : (
                        <div className="prediction-row">
                          <div className="prediction-label">Partidas</div>
                          <div className="prediction-value"><span style={{ color: 'var(--tx3)' }}>Nenhum placar liberado</span></div>
                          <div className="points pending">—</div>
                        </div>
                      )
                    ) : null}
                    {exploreReleased ? (
                      <div className="compare-strip">
                        <div className="mini-stat">
                          <div className="mini-num">{entry.matches.length}</div>
                          <div className="mini-label">palpites</div>
                        </div>
                        <div className="mini-stat">
                          <div className="mini-num">{entry.matches.filter((item) => item.pointsAwarded === 3 || item.pointsAwarded === 6).length}</div>
                          <div className="mini-label">acertos fortes</div>
                        </div>
                        <div className="mini-stat">
                          <div className="mini-num">{entry.matches.reduce((acc, item) => acc + (item.pointsAwarded ?? 0), 0)}</div>
                          <div className="mini-label">pts soma</div>
                        </div>
                      </div>
                    ) : null}
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
          <ExploreLiveMatchPanel
            exploreReleased={exploreReleased}
            matchPredictions={matchPredictions}
          />

          <ExploreResultsPanel
            exploreReleased={exploreReleased}
            releasedParticipantCount={releasedParticipantCount}
            matchPredictions={matchPredictions}
          />

          <div className="card">
            <div className="card-header"><div><div className="card-title">Insights</div><div className="card-subtitle">Comparativo geral</div></div></div>
            <div className="card-body">
              <div className="insight-list">
                <div className="insight"><div className="insight-icon">🏆</div><div><div className="insight-title">Campeão mais escolhido</div><div className="insight-text">{championInsight}</div></div></div>
                <div className="insight"><div className="insight-icon">⚽</div><div><div className="insight-title">Artilheiro favorito</div><div className="insight-text">{scorerInsight}</div></div></div>
                <div className="insight"><div className="insight-icon">#</div><div><div className="insight-title">Participantes</div><div className="insight-text">{entries.length} com palpites registrados</div></div></div>
                <div className="insight"><div className="insight-icon">≡</div><div><div className="insight-title">Placar mais apostado</div><div className="insight-text">{scorelineInsight}</div></div></div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </>
  );
}
