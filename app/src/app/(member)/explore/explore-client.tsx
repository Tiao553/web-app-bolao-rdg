'use client';

import { useDeferredValue, useEffect, useState } from 'react';

import { TeamBadge } from '../../../components/ui/team-badge';
import type {
  ExploreCompetitionPredictionContract,
  ExploreMatchGroupContract,
  ExploreStateContract,
} from '../../../lib/contracts';
import { formatKickoff, formatMatchLabel, formatPoints, isMatchLive } from './live-utils';

type FilterMode = 'all' | 'participant' | 'match' | 'live';

const FINISHED_STATUSES = new Set(['FT', 'AET', 'PEN', 'FINISHED']);

type Props = {
  exploreState: ExploreStateContract;
  exploreReleased: boolean;
  matchGroups: ExploreMatchGroupContract[];
  competitionPredictions: ExploreCompetitionPredictionContract[];
};

function stateLabel(state: ExploreStateContract): string {
  if (state === 'released') {
    return 'Liberado';
  }
  if (state === 'partial') {
    return 'Parcial';
  }
  return 'Bloqueado';
}

function stateTone(state: ExploreStateContract): string {
  if (state === 'released') {
    return 'ok';
  }
  if (state === 'partial') {
    return 'warn';
  }
  return 'neutral';
}

function groupSearchText(group: ExploreMatchGroupContract): string {
  return [
    group.homeTeam,
    group.awayTeam,
    group.groupName ?? '',
    group.phase,
    group.status,
    ...group.predictions.map((prediction) => prediction.userName),
  ]
    .join(' ')
    .toLowerCase();
}

function isGroupLive(group: ExploreMatchGroupContract, nowMs: number): boolean {
  return group.predictions.some((prediction) => isMatchLive(prediction, nowMs));
}

function isGroupUpcoming(group: ExploreMatchGroupContract, nowMs: number): boolean {
  if (FINISHED_STATUSES.has(group.status)) {
    return false;
  }
  if (!group.startsAt) {
    return false;
  }
  const kickoffMs = Date.parse(group.startsAt);
  return !Number.isNaN(kickoffMs) && kickoffMs > nowMs;
}

function getSortedGroups(groups: ExploreMatchGroupContract[], nowMs: number): ExploreMatchGroupContract[] {
  return [...groups].sort((left, right) => {
    const leftRank = isGroupLive(left, nowMs) ? 0 : isGroupUpcoming(left, nowMs) ? 1 : 2;
    const rightRank = isGroupLive(right, nowMs) ? 0 : isGroupUpcoming(right, nowMs) ? 1 : 2;
    if (leftRank !== rightRank) {
      return leftRank - rightRank;
    }

    const leftStartsAt = left.startsAt ? Date.parse(left.startsAt) : Number.POSITIVE_INFINITY;
    const rightStartsAt = right.startsAt ? Date.parse(right.startsAt) : Number.POSITIVE_INFINITY;
    if (leftStartsAt !== rightStartsAt) {
      return leftStartsAt - rightStartsAt;
    }

    return left.matchId.localeCompare(right.matchId);
  });
}

function buildSelectionSummary(
  predictions: ExploreCompetitionPredictionContract[],
  kind: 'CHAMPION' | 'TOP_SCORER',
): { title: string; selection: ExploreCompetitionPredictionContract | null; count: number } {
  const filtered = predictions.filter((prediction) => prediction.predictionType === kind);
  const counts = new Map<string, { item: ExploreCompetitionPredictionContract; count: number }>();
  filtered.forEach((prediction) => {
    const entry = counts.get(prediction.selectionLabel) ?? { item: prediction, count: 0 };
    entry.count += 1;
    counts.set(prediction.selectionLabel, entry);
  });
  const top = [...counts.values()].sort((left, right) => right.count - left.count)[0] ?? null;
  return {
    title: kind === 'CHAMPION' ? 'Campeão' : 'Artilheiro',
    selection: top?.item ?? null,
    count: top?.count ?? 0,
  };
}

function getGroupLabel(group: ExploreMatchGroupContract): string {
  const firstPrediction = group.predictions[0];
  if (firstPrediction) {
    return formatMatchLabel(firstPrediction);
  }
  if (group.groupName) {
    return `Grupo ${group.groupName}`;
  }
  if (group.stageRound) {
    return `Rodada ${group.stageRound}`;
  }
  return group.phase.replaceAll('_', ' ');
}

function MatchCard({
  group,
  nowMs,
}: {
  group: ExploreMatchGroupContract;
  nowMs: number;
}) {
  const live = isGroupLive(group, nowMs);
  const upcoming = isGroupUpcoming(group, nowMs);
  const badgeClass = live ? 'orange' : upcoming ? 'ok' : 'neutral';
  const badgeLabel = live ? 'ao vivo' : upcoming ? 'próximo' : 'encerrado';
  const label = getGroupLabel(group);

  return (
    <div className="explore-feature-card">
      <div className="explore-feature-top">
        <div>
          <div className="card-title">{live ? 'Jogo ao vivo agora' : 'Próximo jogo público'}</div>
          <div className="card-subtitle">{live ? 'Palpites já liberados para o confronto em andamento' : 'O próximo confronto visível para a comunidade'}</div>
        </div>
        <div className={`pill ${badgeClass}`}><span className="dot" />{badgeLabel}</div>
      </div>

      <div className="explore-match-meta">
        <span className="badge neutral">{label}</span>
        <span className="explore-feature-kickoff">{formatKickoff(group.startsAt)}</span>
      </div>

      <div className="player-team-inline">
        <TeamBadge name={group.homeTeam} flag={group.homeFlag} iso2={group.homeIso2} code={group.homeCode} compact />
        <span style={{ color: 'var(--tx3)' }}>×</span>
        <TeamBadge name={group.awayTeam} flag={group.awayFlag} iso2={group.awayIso2} code={group.awayCode} compact />
      </div>

      <div className="explore-feature-summary">
        {group.predictions.length} palpites públicos neste jogo
      </div>

      <div className="explore-feature-list">
        {group.predictions.slice(0, 4).map((prediction) => {
          const badge = formatPoints(prediction.pointsAwarded);
          return (
            <div key={`${prediction.userId}-${prediction.matchId}`} className="explore-feature-row">
              <div>
                <div className="explore-feature-user">{prediction.userName}</div>
                <div className="explore-feature-score">{prediction.homeGoals} × {prediction.awayGoals}</div>
              </div>
              <div className={badge.className}>{badge.label}</div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

export function ExploreClient({
  exploreState,
  exploreReleased,
  matchGroups,
  competitionPredictions,
}: Props) {
  const [nowMs, setNowMs] = useState(() => Date.now());
  const [searchOpen, setSearchOpen] = useState(false);
  const [searchText, setSearchText] = useState('');
  const [filterMode, setFilterMode] = useState<FilterMode>('all');
  const deferredSearchText = useDeferredValue(searchText.trim().toLowerCase());

  useEffect(() => {
    const timer = window.setInterval(() => {
      setNowMs(Date.now());
    }, 60_000);
    return () => window.clearInterval(timer);
  }, []);

  const orderedGroups = getSortedGroups(matchGroups, nowMs);
  const featuredGroup = orderedGroups[0] ?? null;
  const championSummary = buildSelectionSummary(competitionPredictions, 'CHAMPION');
  const scorerSummary = buildSelectionSummary(competitionPredictions, 'TOP_SCORER');

  const filteredGroups = orderedGroups.filter((group) => {
    const text = groupSearchText(group);
    const search = deferredSearchText;

    if (filterMode === 'live' && !isGroupLive(group, nowMs)) {
      return false;
    }
    if (!search) {
      return true;
    }
    if (filterMode === 'participant') {
      return group.predictions.some((prediction) => prediction.userName.toLowerCase().includes(search));
    }
    if (filterMode === 'match') {
      return text.includes(search);
    }
    return text.includes(search) || group.predictions.some((prediction) => prediction.userName.toLowerCase().includes(search));
  });

  return (
    <>
      <section className="hero explore-hero">
        <div className="hero-content explore-hero-content">
          <div>
            <div className="eyebrow"><span className="dot" />Explore</div>
            <h1>Palpites públicos, sem ruído.</h1>
            <p>
              Campeão e artilheiro ficam sempre públicos. Os palpites de jogo aparecem por partida,
              ordenados pela data, com o próximo jogo ou o ao vivo destacado no topo.
            </p>
          </div>
          <div className="explore-hero-actions">
            <div className={`pill ${stateTone(exploreState)}`}><span className="dot" />{stateLabel(exploreState)}</div>
            <button type="button" className="btn-secondary" onClick={() => setSearchOpen(true)}>
              Pesquisar palpites
            </button>
            <div className={`pill ${exploreReleased ? 'ok' : 'warn'}`}><span className="dot" />{exploreReleased ? 'público' : 'parcial'}</div>
          </div>
        </div>
      </section>

      <div className="grid-2 explore-layout">
        <div className="card">
          <div className="card-header">
            <div>
              <div className="card-title">Jogo em destaque</div>
              <div className="card-subtitle">Ao vivo primeiro, depois o próximo confronto público</div>
            </div>
            <button type="button" className="btn-ghost" onClick={() => setSearchOpen(true)}>
              Abrir busca
            </button>
          </div>
          <div className="card-body">
            {featuredGroup ? (
              <MatchCard group={featuredGroup} nowMs={nowMs} />
            ) : (
              <div className="explore-empty">
                Nenhuma partida pública disponível agora. Os jogos entram aqui conforme a janela pública abre.
              </div>
            )}
          </div>
        </div>

        <div className="card">
          <div className="card-header">
            <div>
              <div className="card-title">Campeão e artilheiro</div>
              <div className="card-subtitle">Somente os dois bonus públicos</div>
            </div>
          </div>
          <div className="card-body">
            <div className="explore-picks">
              {[
                championSummary,
                scorerSummary,
              ].map((summary) => (
                <div key={summary.title} className="explore-pick-card">
                  <div className="explore-pick-head">
                    <div>
                      <div className="explore-pick-title">{summary.title}</div>
                      <div className="explore-pick-sub">{summary.count} escolha{summary.count === 1 ? '' : 's'} pública{summary.count === 1 ? '' : 's'}</div>
                    </div>
                    <div className="pill neutral"><span className="dot" />público</div>
                  </div>
                  {summary.selection ? (
                    <div className="explore-pick-body">
                      <div className="explore-pick-name">{summary.selection.selectionLabel}</div>
                      {summary.selection.selectionTeamCode || summary.selection.selectionTeamName ? (
                        <TeamBadge
                          name={summary.selection.selectionTeamName ?? summary.selection.selectionLabel}
                          code={summary.selection.selectionTeamCode}
                          iso2={summary.selection.selectionTeamIso2}
                          flag={summary.selection.selectionTeamFlag ?? undefined}
                          compact
                        />
                      ) : null}
                    </div>
                  ) : (
                    <div className="explore-empty explore-empty-soft">Nenhum palpite público registrado.</div>
                  )}
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {searchOpen ? (
        <div className="modal-overlay explore-sheet-overlay" onClick={() => setSearchOpen(false)}>
          <div
            className="explore-sheet"
            onClick={(event) => event.stopPropagation()}
            role="dialog"
            aria-modal="true"
            aria-label="Pesquisar palpites públicos"
          >
            <div className="explore-sheet-header">
              <div>
                <div className="modal-title">Pesquisar palpites</div>
                <div className="card-subtitle">Busca sobre os jogos públicos ordenados por data</div>
              </div>
              <button type="button" className="modal-close" onClick={() => setSearchOpen(false)}>
                Fechar
              </button>
            </div>
            <div className="explore-sheet-body">
              <div className="explore-filters">
                {[
                  ['all', 'Tudo'],
                  ['participant', 'Participante'],
                  ['match', 'Partida'],
                  ['live', 'Ao vivo'],
                ].map(([key, label]) => (
                  <button
                    key={key}
                    type="button"
                    className={`explore-chip${filterMode === key ? ' active' : ''}`}
                    onClick={() => setFilterMode(key as FilterMode)}
                  >
                    {label}
                  </button>
                ))}
              </div>
              <div className="input-wrap">
                <span className="input-icon">⌕</span>
                <input
                  type="text"
                  value={searchText}
                  onChange={(event) => setSearchText(event.target.value)}
                  className="field-input with-icon"
                  placeholder="Buscar participante, jogo ou grupo..."
                />
              </div>
              <div className="explore-results-summary">
                {filteredGroups.length} jogo{filteredGroups.length === 1 ? '' : 's'} encontrado{filteredGroups.length === 1 ? '' : 's'}
              </div>
              <div className="explore-sheet-list">
                {filteredGroups.length === 0 ? (
                  <div className="explore-empty explore-empty-soft">Nenhum resultado encontrado para o filtro atual.</div>
                ) : (
                  filteredGroups.map((group) => {
                    const live = isGroupLive(group, nowMs);
                    const upcoming = isGroupUpcoming(group, nowMs);
                    const badgeClass = live ? 'orange' : upcoming ? 'ok' : 'neutral';
                    const badgeLabel = live ? 'ao vivo' : upcoming ? 'próximo' : 'encerrado';
                    return (
                      <div key={group.matchId} className="explore-sheet-card">
                        <div className="explore-sheet-top">
                          <div className="explore-sheet-meta">
                            <span className={`badge ${badgeClass}`}>{badgeLabel}</span>
                            <span className="badge neutral">{getGroupLabel(group)}</span>
                            <span className="explore-feature-kickoff">{formatKickoff(group.startsAt)}</span>
                          </div>
                          <div className="player-team-inline">
                            <TeamBadge name={group.homeTeam} flag={group.homeFlag} iso2={group.homeIso2} code={group.homeCode} compact />
                            <span style={{ color: 'var(--tx3)' }}>×</span>
                            <TeamBadge name={group.awayTeam} flag={group.awayFlag} iso2={group.awayIso2} code={group.awayCode} compact />
                          </div>
                        </div>

                        <div className="explore-sheet-predictions">
                          {group.predictions
                            .filter((prediction) => {
                              const search = deferredSearchText;
                              if (!search) {
                                return true;
                              }
                              if (filterMode === 'participant') {
                                return prediction.userName.toLowerCase().includes(search);
                              }
                              if (filterMode === 'match') {
                                return [
                                  group.homeTeam,
                                  group.awayTeam,
                                  group.groupName ?? '',
                                  group.phase,
                                  group.status,
                                ]
                                  .join(' ')
                                  .toLowerCase()
                                  .includes(search);
                              }
                              return prediction.userName.toLowerCase().includes(search)
                                || group.homeTeam.toLowerCase().includes(search)
                                || group.awayTeam.toLowerCase().includes(search);
                            })
                            .map((prediction) => {
                              const badge = formatPoints(prediction.pointsAwarded);
                              return (
                                <div key={`${prediction.userId}-${prediction.matchId}`} className="explore-sheet-row">
                                  <div>
                                    <div className="explore-sheet-user">{prediction.userName}</div>
                                    <div className="explore-sheet-score">{prediction.homeGoals} × {prediction.awayGoals}</div>
                                  </div>
                                  <div className={badge.className}>{badge.label}</div>
                                </div>
                              );
                            })}
                        </div>
                      </div>
                    );
                  })
                )}
              </div>
            </div>
          </div>
        </div>
      ) : null}
    </>
  );
}
