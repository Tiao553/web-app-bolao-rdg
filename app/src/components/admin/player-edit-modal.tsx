'use client';
import { useState, useTransition } from 'react';
import type { AdminPlayersContract } from '../../lib/contracts';
import { TeamBadge } from '../ui/team-badge';

type Leader = AdminPlayersContract['leaders'][0];

interface Props {
  leaders: Leader[];
  csrfToken: string;
}

export function AdminPlayerList({ leaders, csrfToken }: Props) {
  const [search, setSearch] = useState('');
  const [editPlayer, setEditPlayer] = useState<Leader | null>(null);
  const [goals, setGoals] = useState('0');
  const [assists, setAssists] = useState('0');
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [isPending, startTransition] = useTransition();

  const filtered = leaders.filter(l =>
    !search || l.selectionLabel.toLowerCase().includes(search.toLowerCase()) ||
    (l.teamName ?? '').toLowerCase().includes(search.toLowerCase())
  );

  function openEdit(l: Leader) {
    setEditPlayer(l);
    setGoals(String(l.goals));
    setAssists(String(l.assists));
    setError('');
    setSuccess('');
  }

  function closeEdit() {
    setEditPlayer(null);
    setError('');
    setSuccess('');
  }

  function save() {
    if (!editPlayer) return;
    const g = parseInt(goals, 10);
    const a = parseInt(assists, 10);
    if (isNaN(g) || isNaN(a) || g < 0 || a < 0) {
      setError('Valores inválidos.'); return;
    }
    setError('');
    startTransition(async () => {
      try {
        const res = await fetch('/api/admin/players/stats', {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json', 'x-csrf-token': csrfToken },
          body: JSON.stringify({ selection_key: editPlayer.selectionKey, goals: g, assists: a }),
        });
        if (!res.ok) {
          const b = await res.json().catch(() => ({}));
          setError(b?.error?.message || b?.detail?.message || `Erro ${res.status}`);
          return;
        }
        setSuccess('Estatísticas salvas.');
        setTimeout(() => { closeEdit(); window.location.reload(); }, 1000);
      } catch {
        setError('Falha de rede.');
      }
    });
  }

  return (
    <>
      <div className="filters" style={{ marginBottom: 14 }}>
        <input
          className="admin-input"
          placeholder="Buscar jogador ou seleção..."
          value={search}
          onChange={e => setSearch(e.target.value)}
        />
      </div>

      <div className="player-list-admin">
        <div className="player-row-admin header">
          <div className="th">#</div>
          <div className="th">Jogador</div>
          <div className="th">Gols</div>
          <div className="th">Assist.</div>
          <div className="th">Status</div>
          <div className="th" style={{ textAlign: 'right' }}>Ações</div>
        </div>
        {filtered.map((l, i) => (
          <div key={l.selectionKey} className="player-row-admin">
            <div className="avatar" style={{ width: 36, height: 36, fontSize: 12 }}>{i + 1}</div>
            <div>
              <div className="player-name-admin">{l.selectionLabel}</div>
              <div className="player-detail-admin">
                {l.teamName ? <><TeamBadge name={l.teamName} flag={l.teamFlag} iso2={l.teamIso2} code={l.teamCode} compact /> · </> : null}
                {l.predictionCount} palpiteiro{l.predictionCount !== 1 ? 's' : ''}
              </div>
            </div>
            <div className="num-admin gold">{l.goals > 0 ? l.goals : '—'}</div>
            <div className="num-admin">{l.assists > 0 ? l.assists : '—'}</div>
            <div className={`pill ${i === 0 ? 'warn' : 'ok'}`}><span className="dot" />{i === 0 ? 'líder' : 'ativo'}</div>
            <div className="row-actions">
              <button className="btn-ghost" style={{ height: 32, fontSize: 11, padding: '0 10px' }} onClick={() => openEdit(l)}>Editar</button>
            </div>
          </div>
        ))}
        {filtered.length === 0 && (
          <div style={{ textAlign: 'center', padding: 32, color: 'var(--tx3)', fontSize: 14 }}>Nenhum resultado para a busca.</div>
        )}
      </div>

      {editPlayer && (
        <div className="modal-overlay" onClick={e => { if (e.target === e.currentTarget) closeEdit(); }}>
          <div className="modal-box" style={{ maxWidth: 420 }}>
            <div className="modal-header">
              <div className="modal-title">Editar artilheiro</div>
              <button className="modal-close" onClick={closeEdit}>✕</button>
            </div>
            <div className="modal-body">
              <div style={{ marginBottom: 6 }}>
                <div style={{ fontWeight: 700, fontSize: 15, color: '#fff' }}>{editPlayer.selectionLabel}</div>
                {editPlayer.teamName && (
                  <div style={{ marginTop: 4 }}>
                    <TeamBadge name={editPlayer.teamName} flag={editPlayer.teamFlag} iso2={editPlayer.teamIso2} code={editPlayer.teamCode} compact />
                  </div>
                )}
                <div style={{ fontSize: 12, color: 'var(--tx3)', marginTop: 4 }}>
                  {editPlayer.predictionCount} palpiteiro{editPlayer.predictionCount !== 1 ? 's' : ''}
                </div>
              </div>

              <div className="field-admin">
                <div className="field-label-admin">Estatísticas oficiais</div>
                <div className="stat-editor-admin">
                  <div>
                    <div className="stat-input-title">Gols</div>
                    <input className="stat-input-admin" type="number" min={0} max={100} value={goals} onChange={e => setGoals(e.target.value)} />
                  </div>
                  <div>
                    <div className="stat-input-title">Assistências</div>
                    <input className="stat-input-admin" type="number" min={0} max={100} value={assists} onChange={e => setAssists(e.target.value)} />
                  </div>
                </div>
              </div>

              {error && <div className="modal-error">{error}</div>}
              {success && <div className="modal-success">{success}</div>}
            </div>
            <div className="modal-footer">
              <button className="btn-ghost" style={{ height: 36, fontSize: 12 }} onClick={closeEdit} disabled={isPending}>Cancelar</button>
              <button className="btn-primary" style={{ height: 36, fontSize: 12, padding: '0 20px' }} onClick={save} disabled={isPending}>
                {isPending ? 'Salvando…' : 'Salvar e recalcular →'}
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
