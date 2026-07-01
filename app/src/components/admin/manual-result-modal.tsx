'use client';
import { useState, useTransition, useEffect, useRef } from 'react';
import type { AdminMatchRowContract } from '../../lib/contracts';

type GoalEntry = { name: string; team: string; goals: number; playerId?: string };
type PlayerOption = { id: string; name: string; teamCode?: string | null };

interface Props {
  matches: AdminMatchRowContract[];
  csrfToken: string;
}

const KNOCKOUT_PHASES = new Set([
  'ROUND_OF_32',
  'ROUND_OF_16',
  'QUARTER_FINAL',
  'SEMI_FINAL',
  'THIRD_PLACE',
  'FINAL',
]);

export function ManualResultModal({ matches, csrfToken }: Props) {
  const [open, setOpen] = useState(false);
  const [selectedId, setSelectedId] = useState('');
  const [homeGoals, setHomeGoals] = useState('0');
  const [awayGoals, setAwayGoals] = useState('0');
  const [advancedTeam, setAdvancedTeam] = useState('');
  const [scorers, setScorers] = useState<GoalEntry[]>([]);
  const [scorerSearch, setScorerSearch] = useState('');
  const [scorerTeam, setScorerTeam] = useState('');
  const [scorerGoals, setScorerGoals] = useState('1');
  const [suggestions, setSuggestions] = useState<PlayerOption[]>([]);
  const [allPlayers, setAllPlayers] = useState<PlayerOption[]>([]);
  const [showSugg, setShowSugg] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [isPending, startTransition] = useTransition();
  const inputRef = useRef<HTMLInputElement>(null);

  const selected = matches.find(m => m.id === selectedId);
  const parsedHomeGoals = parseInt(homeGoals, 10);
  const parsedAwayGoals = parseInt(awayGoals, 10);
  const needsAdvancedTeam = Boolean(
    selected
      && KNOCKOUT_PHASES.has(selected.phase)
      && !Number.isNaN(parsedHomeGoals)
      && !Number.isNaN(parsedAwayGoals)
      && parsedHomeGoals === parsedAwayGoals,
  );

  // Load players once when modal opens
  useEffect(() => {
    if (!open || allPlayers.length > 0) return;
    fetch('/api/admin/available-players')
      .then(r => r.json())
      .then((data: PlayerOption[]) => setAllPlayers(data))
      .catch(() => {});
  }, [open, allPlayers.length]);

  // Filter suggestions as user types
  useEffect(() => {
    const q = scorerSearch.trim().toLowerCase();
    if (q.length < 2) { setSuggestions([]); setShowSugg(false); return; }
    const hits = allPlayers.filter(p => p.name.toLowerCase().includes(q)).slice(0, 8);
    setSuggestions(hits);
    setShowSugg(hits.length > 0);
  }, [scorerSearch, allPlayers]);

  useEffect(() => {
    setAdvancedTeam('');
  }, [selectedId]);

  function selectSuggestion(p: PlayerOption) {
    setScorerSearch(p.name);
    setScorerTeam(p.teamCode ?? '');
    setShowSugg(false);
  }

  async function addScorer() {
    const name = scorerSearch.trim();
    if (!name) return;
    const goals = Number(scorerGoals) || 1;

    // Check if player exists in allPlayers
    const existing = allPlayers.find(p => p.name.toLowerCase() === name.toLowerCase());
    let playerId = existing?.id;

    if (!existing) {
      // Register new player
      try {
        const res = await fetch('/api/admin/players/register', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json', 'x-csrf-token': csrfToken },
          body: JSON.stringify({ name, team_code: scorerTeam || null }),
        });
        if (res.ok) {
          const data = await res.json();
          playerId = data.id;
          setAllPlayers(prev => [...prev, { id: data.id, name: data.name, teamCode: data.teamCode }]);
        }
      } catch { /* continue even if registration fails */ }
    }

    setScorers(prev => [...prev, { name, team: scorerTeam.trim(), goals, playerId }]);
    setScorerSearch('');
    setScorerTeam('');
    setScorerGoals('1');
    setShowSugg(false);
  }

  function removeScorer(idx: number) {
    setScorers(prev => prev.filter((_, i) => i !== idx));
  }

  function close() {
    setOpen(false);
    setSelectedId('');
    setHomeGoals('0');
    setAwayGoals('0');
    setAdvancedTeam('');
    setScorers([]);
    setScorerSearch('');
    setScorerTeam('');
    setScorerGoals('1');
    setShowSugg(false);
    setError('');
    setSuccess('');
  }

  function submit() {
    if (!selectedId) { setError('Selecione uma partida.'); return; }
    const home = parseInt(homeGoals, 10);
    const away = parseInt(awayGoals, 10);
    if (isNaN(home) || isNaN(away) || home < 0 || away < 0) {
      setError('Placar inválido.'); return;
    }
    if (needsAdvancedTeam && !advancedTeam) {
      setError('Selecione quem avançou no mata-mata.'); return;
    }
    setError('');
    startTransition(async () => {
      try {
        const status = needsAdvancedTeam ? 'PEN' : 'FT';
        const res = await fetch(`/api/admin/matches/${selectedId}/manual-override`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json', 'x-csrf-token': csrfToken },
          body: JSON.stringify({
            status,
            official_home_goals: home,
            official_away_goals: away,
            winner_team_name: needsAdvancedTeam ? advancedTeam : null,
            has_manual_override: true,
            goal_scorers: scorers.map(s => ({ name: s.name, team: s.team || null, goals: s.goals })),
          }),
        });
        if (!res.ok) {
          const body = await res.json().catch(() => ({}));
          setError(body?.error?.message || body?.detail?.message || body?.detail || `Erro ${res.status}`);
          return;
        }
        setSuccess('Resultado salvo com sucesso. Recálculo executado.');
        setTimeout(() => { close(); window.location.reload(); }, 1500);
      } catch {
        setError('Falha de rede. Tente novamente.');
      }
    });
  }

  const teamOptions = selected
    ? [selected.homeTeam, selected.awayTeam]
    : [];

  return (
    <>
      <button className="btn-primary" style={{ height: 36, fontSize: 12, padding: '0 16px' }} onClick={() => setOpen(true)}>
        + Inserir resultado
      </button>

      {open && (
        <div className="modal-overlay" onClick={e => { if (e.target === e.currentTarget) close(); }}>
          <div className="modal-box">
            <div className="modal-header">
              <div className="modal-title">Inserir resultado manual</div>
              <button className="modal-close" onClick={close}>✕</button>
            </div>

            <div className="modal-body">
              {/* Match picker */}
              <div className="field-admin">
                <div className="field-label-admin">Partida</div>
                <select
                  className="admin-select"
                  style={{ width: '100%' }}
                  value={selectedId}
                  onChange={e => setSelectedId(e.target.value)}
                >
                  <option value="">Selecione uma partida…</option>
                  {matches.map(m => (
                    <option key={m.id} value={m.id}>
                      {m.homeTeam} × {m.awayTeam}
                      {m.groupName ? ` — Grupo ${m.groupName}` : ''}
                      {m.startsAt ? ` (${new Date(m.startsAt).toLocaleDateString('pt-BR')})` : ''}
                      {m.hasManualOverride ? ' [override]' : ''}
                    </option>
                  ))}
                </select>
              </div>

              {/* Score */}
              <div className="field-admin">
                <div className="field-label-admin">Placar</div>
                <div className="score-editor">
                  <div className="score-box">
                    <div className="score-team">{selected?.homeTeam ?? 'Casa'}</div>
                    <input className="score-input-admin" type="number" min={0} max={50} value={homeGoals} onChange={e => setHomeGoals(e.target.value)} />
                  </div>
                  <div className="score-sep">×</div>
                  <div className="score-box">
                    <div className="score-team">{selected?.awayTeam ?? 'Fora'}</div>
                    <input className="score-input-admin" type="number" min={0} max={50} value={awayGoals} onChange={e => setAwayGoals(e.target.value)} />
                  </div>
                </div>
              </div>

              {needsAdvancedTeam && selected && (
                <div className="field-admin">
                  <div className="field-label-admin">Classificado</div>
                  <select
                    className="admin-select"
                    style={{ width: '100%' }}
                    value={advancedTeam}
                    onChange={e => setAdvancedTeam(e.target.value)}
                  >
                    <option value="">Selecione quem passou…</option>
                    <option value={selected.homeTeam}>{selected.homeTeam}</option>
                    <option value={selected.awayTeam}>{selected.awayTeam}</option>
                  </select>
                  <div style={{ marginTop: 6, color: 'var(--tx3)', fontSize: 11, lineHeight: 1.5 }}>
                    O placar continua valendo para os pontos dos 90 minutos. Esta seleção só atualiza o chaveamento.
                  </div>
                </div>
              )}

              {/* Goalscorers with autocomplete */}
              <div className="field-admin">
                <div className="field-label-admin">Artilheiros / marcadores</div>
                <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginBottom: 8 }}>
                  <div style={{ flex: '2 1 140px', position: 'relative' }}>
                    <input
                      ref={inputRef}
                      className="admin-input"
                      style={{ width: '100%' }}
                      placeholder="Nome do jogador"
                      value={scorerSearch}
                      onChange={e => setScorerSearch(e.target.value)}
                      onKeyDown={e => { if (e.key === 'Enter') { e.preventDefault(); addScorer(); } if (e.key === 'Escape') setShowSugg(false); }}
                      onFocus={() => suggestions.length > 0 && setShowSugg(true)}
                      autoComplete="off"
                    />
                    {showSugg && (
                      <div className="scorer-suggestions">
                        {suggestions.map(p => (
                          <div
                            key={p.id}
                            className="scorer-suggestion-item"
                            onMouseDown={e => { e.preventDefault(); selectSuggestion(p); }}
                          >
                            <span className="scorer-sugg-name">{p.name}</span>
                            {p.teamCode && <span className="scorer-sugg-team">{p.teamCode}</span>}
                          </div>
                        ))}
                        {allPlayers.length > 0 && !suggestions.some(p => p.name.toLowerCase() === scorerSearch.trim().toLowerCase()) && (
                          <div className="scorer-suggestion-new">
                            <span>+ Cadastrar "{scorerSearch.trim()}" como novo</span>
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                  <select
                    className="admin-select"
                    style={{ flex: '1 1 100px' }}
                    value={scorerTeam}
                    onChange={e => setScorerTeam(e.target.value)}
                  >
                    <option value="">Equipe</option>
                    {teamOptions.map(t => <option key={t} value={t}>{t}</option>)}
                  </select>
                  <input
                    className="score-input-admin"
                    type="number" min={1} max={20}
                    value={scorerGoals}
                    onChange={e => setScorerGoals(e.target.value)}
                    style={{ width: 52 }}
                    title="Gols"
                  />
                  <button type="button" className="btn-ok" style={{ height: 36, fontSize: 12, padding: '0 12px' }} onClick={addScorer}>
                    + Add
                  </button>
                </div>

                {scorers.length > 0 && (
                  <div className="scorer-list">
                    {scorers.map((s, i) => (
                      <div key={i} className="scorer-row">
                        <div className="scorer-info">
                          <span className="scorer-name">{s.name}</span>
                          {s.team && <span className="scorer-team">{s.team}</span>}
                          <span className="scorer-goals">{s.goals}g</span>
                          {!s.playerId && <span style={{ fontSize: 10, color: 'var(--am)', marginLeft: 4 }}>novo</span>}
                        </div>
                        <button type="button" className="scorer-remove" onClick={() => removeScorer(i)}>✕</button>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {error && <div className="modal-error">{error}</div>}
              {success && <div className="modal-success">{success}</div>}
            </div>

            <div className="modal-footer">
              <button className="btn-ghost" style={{ height: 36, fontSize: 12 }} onClick={close} disabled={isPending}>Cancelar</button>
              <button
                className="btn-primary"
                style={{ height: 36, fontSize: 12, padding: '0 20px' }}
                onClick={submit}
                disabled={isPending || !selectedId}
              >
                {isPending ? 'Salvando…' : 'Salvar e recalcular →'}
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
