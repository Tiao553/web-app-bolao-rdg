'use client';
import { useState, useMemo } from 'react';

type Team = { id: string; name: string; code: string; iso2: string; group: string };
type Player = { id: string; name: string; teamCode: string; position: string; club: string; nationality: string };
type Prediction = { predictionType: string; selectionKey: string; selectionLabel: string; pointsAwarded: number | null; lockedAt: string | null };

function iso2Flag(iso2: string) {
  return iso2.toUpperCase().replace(/./g, c => String.fromCodePoint(c.charCodeAt(0) + 127397));
}
function initials(name: string) {
  return name.split(' ').slice(0, 2).map(w => w[0]).join('').toUpperCase();
}

export function InitialPredictionsClient({
  teams, players, champion, scorer, locked,
}: {
  teams: Team[];
  players: Player[];
  champion: Prediction | null;
  scorer: Prediction | null;
  locked: boolean;
}) {
  const [teamSearch, setTeamSearch] = useState('');
  const [playerSearch, setPlayerSearch] = useState('');
  const [selectedChampion, setSelectedChampion] = useState<string | null>(champion?.selectionKey ?? null);
  const [selectedScorer, setSelectedScorer] = useState<string | null>(scorer?.selectionKey ?? null);
  const [editingChampion, setEditingChampion] = useState(!champion?.selectionKey);
  const [editingScorer, setEditingScorer] = useState(!scorer?.selectionKey);

  const filteredTeams = useMemo(() =>
    teamSearch.trim()
      ? teams.filter(t => t.name.toLowerCase().includes(teamSearch.toLowerCase()))
      : teams,
    [teams, teamSearch]);

  const filteredPlayers = useMemo(() =>
    playerSearch.trim()
      ? players.filter(p =>
          p.name.toLowerCase().includes(playerSearch.toLowerCase()) ||
          p.nationality.toLowerCase().includes(playerSearch.toLowerCase()))
      : players,
    [players, playerSearch]);

  const championTeam = teams.find(t => t.code === selectedChampion);
  const scorerPlayer = players.find(p => p.id === selectedScorer);

  return (
    <>
      <section className="hero">
        <div className="hero-content">
          <div>
            <div className="eyebrow"><span className="dot" />Valem até 25 pontos</div>
            <h1>Escolha seu <span>campeão</span> e artilheiro.</h1>
            <p>Esses palpites só podem ser alterados até o bloqueio da primeira fase. O campeão vale 10 pontos e o artilheiro vale 15 pontos, considerando gols e assistências como critério de desempate.</p>
          </div>
          <div className="deadline-card" style={{ minWidth: 200 }}>
            <div className="deadline-label">Status dos palpites</div>
            <div className={`pill ${locked ? 'warn' : 'ok'}`} style={{ marginTop: 8 }}>
              <span className="dot" />{locked ? 'Bloqueado' : 'Aberto para edição'}
            </div>
          </div>
        </div>
      </section>

      <div className="grid-2">
        {/* Campeão */}
        <div className="card">
          <div className="card-header">
            <div><div className="card-title">Palpite de campeão</div><div className="card-subtitle">10 pontos</div></div>
            <div className={`badge ${locked ? 'warn' : 'open'}`}><span className="dot" />{locked ? 'Bloqueado' : 'Aberto'}</div>
          </div>
          <div className="card-body">
            {/* Selected state */}
            {!editingChampion && championTeam && (
              <div>
                <div className="pick-selected-card">
                  <div className="flag" style={{ fontSize: 28 }}>{iso2Flag(championTeam.iso2)}</div>
                  <div style={{ flex: 1 }}>
                    <div style={{ fontSize: 11, color: 'var(--tx3)', fontFamily: 'Fira Code', textTransform: 'uppercase', letterSpacing: '.08em' }}>Campeão selecionado</div>
                    <div style={{ fontSize: 16, fontWeight: 800 }}>{championTeam.name}</div>
                    <div style={{ fontSize: 12, color: 'var(--tx3)' }}>Grupo {championTeam.group}</div>
                  </div>
                  <div className="pick-points">10 pts</div>
                </div>
                {!locked && (
                  <button type="button" className="btn-ghost full" style={{ marginTop: 12 }} onClick={() => setEditingChampion(true)}>
                    Editar seleção
                  </button>
                )}
              </div>
            )}

            {/* Editing state */}
            {(editingChampion || !championTeam) && (
              <form action="/api/member/predictions/champion" method="POST">
                <div className="pick-search">
                  <span className="search-icon">⌕</span>
                  <input
                    type="text"
                    placeholder="Buscar seleção..."
                    value={teamSearch}
                    onChange={e => setTeamSearch(e.target.value)}
                    disabled={locked}
                    autoFocus
                  />
                </div>
                <div className="option-grid">
                  {filteredTeams.length === 0 && (
                    <div style={{ fontSize: 13, color: 'var(--tx3)', padding: '12px 0' }}>Nenhuma seleção encontrada.</div>
                  )}
                  {filteredTeams.map(t => {
                    const sel = selectedChampion === t.code;
                    return (
                      <label key={t.code} className={`option-card${sel ? ' selected' : ''}`}>
                        <input
                          type="radio"
                          name="champion"
                          value={t.code}
                          checked={sel}
                          onChange={() => setSelectedChampion(t.code)}
                          disabled={locked}
                          style={{ display: 'none' }}
                        />
                        <div className="flag" style={{ fontSize: 22 }}>{iso2Flag(t.iso2)}</div>
                        <div>
                          <div className="option-name">{t.name}</div>
                          <div className="option-meta">Grupo {t.group}</div>
                        </div>
                        <div className="check">✓</div>
                      </label>
                    );
                  })}
                </div>
                {!locked && (
                  <div style={{ display: 'flex', gap: 8, marginTop: 16 }}>
                    {champion?.selectionKey && (
                      <button type="button" className="btn-ghost" style={{ flex: 1 }} onClick={() => { setSelectedChampion(champion.selectionKey); setEditingChampion(false); }}>
                        Cancelar
                      </button>
                    )}
                    <button type="submit" className="btn-primary" style={{ flex: 2 }} suppressHydrationWarning>
                      Salvar campeão →
                    </button>
                  </div>
                )}
              </form>
            )}
          </div>
        </div>

        {/* Coluna direita */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
          {/* Artilheiro */}
          <div className="card">
            <div className="card-header">
              <div><div className="card-title">Palpite de artilheiro</div><div className="card-subtitle">15 pontos · gols + assistências</div></div>
              <div className={`badge ${locked ? 'warn' : 'open'}`}><span className="dot" />{locked ? 'Bloqueado' : 'Aberto'}</div>
            </div>
            <div className="card-body">
              {/* Selected state */}
              {!editingScorer && scorerPlayer && (
                <div>
                  <div className="pick-selected-card">
                    <div className="player-face" style={{ width: 44, height: 44, fontSize: 15 }}>{initials(scorerPlayer.name)}</div>
                    <div style={{ flex: 1 }}>
                      <div style={{ fontSize: 11, color: 'var(--tx3)', fontFamily: 'Fira Code', textTransform: 'uppercase', letterSpacing: '.08em' }}>Artilheiro selecionado</div>
                      <div style={{ fontSize: 16, fontWeight: 800 }}>{scorerPlayer.name}</div>
                      <div style={{ fontSize: 12, color: 'var(--tx3)' }}>{scorerPlayer.nationality} · {scorerPlayer.position === 'FW' ? 'atacante' : scorerPlayer.position}</div>
                    </div>
                    <div className="pick-points">15 pts</div>
                  </div>
                  {!locked && (
                    <button type="button" className="btn-ghost full" style={{ marginTop: 12 }} onClick={() => setEditingScorer(true)}>
                      Editar artilheiro
                    </button>
                  )}
                </div>
              )}

              {/* Editing state */}
              {(editingScorer || !scorerPlayer) && (
                <form action="/api/member/predictions/scorer" method="POST">
                  <div className="pick-search">
                    <span className="search-icon">⌕</span>
                    <input
                      type="text"
                      placeholder="Buscar jogador ou seleção..."
                      value={playerSearch}
                      onChange={e => setPlayerSearch(e.target.value)}
                      disabled={locked}
                      autoFocus
                    />
                  </div>
                  <div className="option-grid">
                    {filteredPlayers.length === 0 && (
                      <div style={{ fontSize: 13, color: 'var(--tx3)', padding: '12px 0' }}>Nenhum jogador encontrado.</div>
                    )}
                    {filteredPlayers.map(p => {
                      const sel = selectedScorer === p.id;
                      return (
                        <label key={p.id} className={`option-card${sel ? ' selected' : ''}`}>
                          <input
                            type="radio"
                            name="scorer"
                            value={p.id}
                            checked={sel}
                            onChange={() => setSelectedScorer(p.id)}
                            disabled={locked}
                            style={{ display: 'none' }}
                          />
                          <div className="player-face">{initials(p.name)}</div>
                          <div>
                            <div className="option-name">{p.name}</div>
                            <div className="option-meta">{p.nationality} · {p.position === 'FW' ? 'atacante' : p.position}</div>
                          </div>
                          <div className="pick-points">15 pts</div>
                        </label>
                      );
                    })}
                  </div>
                  {!locked && (
                    <div style={{ display: 'flex', gap: 8, marginTop: 16 }}>
                      {scorer?.selectionKey && (
                        <button type="button" className="btn-ghost" style={{ flex: 1 }} onClick={() => { setSelectedScorer(scorer.selectionKey); setEditingScorer(false); }}>
                          Cancelar
                        </button>
                      )}
                      <button type="submit" className="btn-primary" style={{ flex: 2 }} suppressHydrationWarning>
                        Salvar artilheiro →
                      </button>
                    </div>
                  )}
                </form>
              )}
            </div>
          </div>

          {/* Resumo */}
          <div className="card">
            <div className="card-header">
              <div><div className="card-title">Resumo dos palpites</div><div className="card-subtitle">Antes de salvar</div></div>
              <div className={`badge ${selectedChampion && selectedScorer ? 'ok' : 'orange'}`}><span className="dot" />{selectedChampion && selectedScorer ? 'Completo' : 'Rascunho'}</div>
            </div>
            <div className="card-body">
              <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                <div style={{ display: 'grid', gridTemplateColumns: '42px 1fr auto', gap: 12, alignItems: 'center', padding: '12px 14px', borderRadius: 12, background: 'var(--s2)', border: '1px solid var(--bd)' }}>
                  <div className="flag" style={{ fontSize: 22 }}>{championTeam ? iso2Flag(championTeam.iso2) : '🏆'}</div>
                  <div>
                    <div style={{ fontSize: 11, color: 'var(--tx3)', fontFamily: 'Fira Code', textTransform: 'uppercase', letterSpacing: '.08em' }}>Campeão escolhido</div>
                    <div style={{ fontSize: 14, fontWeight: 800 }}>{championTeam?.name ?? champion?.selectionLabel ?? 'Não definido'}</div>
                  </div>
                  <div className="pick-points">10 pts</div>
                </div>
                <div style={{ display: 'grid', gridTemplateColumns: '42px 1fr auto', gap: 12, alignItems: 'center', padding: '12px 14px', borderRadius: 12, background: 'var(--s2)', border: '1px solid var(--bd)' }}>
                  <div className="player-face">{scorerPlayer ? initials(scorerPlayer.name) : scorer ? initials(scorer.selectionLabel) : '⚽'}</div>
                  <div>
                    <div style={{ fontSize: 11, color: 'var(--tx3)', fontFamily: 'Fira Code', textTransform: 'uppercase', letterSpacing: '.08em' }}>Artilheiro escolhido</div>
                    <div style={{ fontSize: 14, fontWeight: 800 }}>{scorerPlayer?.name ?? scorer?.selectionLabel ?? 'Não definido'}</div>
                  </div>
                  <div className="pick-points">15 pts</div>
                </div>
              </div>
            </div>
          </div>

          {/* Regras */}
          <div className="card">
            <div className="card-header"><div><div className="card-title">Regras rápidas</div><div className="card-subtitle">Pontuação inicial</div></div></div>
            <div className="card-body">
              <div className="rules-list">
                <div className="rule-row"><div className="rule-icon">🏆</div><div><div className="rule-title">Campeão correto</div><div className="rule-text">Acertar a seleção campeã vale 10 pontos.</div></div></div>
                <div className="rule-row"><div className="rule-icon">⚽</div><div><div className="rule-title">Artilheiro correto</div><div className="rule-text">Acertar o artilheiro vale 15 pontos após aplicar o critério de assistências.</div></div></div>
                <div className="rule-row"><div className="rule-icon">🔒</div><div><div className="rule-title">Bloqueio na fase 1</div><div className="rule-text">Quando a primeira fase for bloqueada, campeão e artilheiro não podem mais ser alterados.</div></div></div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </>
  );
}
