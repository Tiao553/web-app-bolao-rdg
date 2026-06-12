'use client';
import { useState, useTransition, useMemo } from 'react';
import type { AdminMatchRowContract } from '../../lib/contracts';
import { TeamBadge } from '../ui/team-badge';

const phaseLabel: Record<string, string> = {
  GROUP_STAGE: 'Grupos', ROUND_OF_32: '16 avos', ROUND_OF_16: 'Oitavas',
  QUARTER_FINAL: 'Quartas', SEMI_FINAL: 'Semi', THIRD_PLACE: '3º lugar', FINAL: 'Final',
};

interface Props {
  matches: AdminMatchRowContract[];
  csrfToken: string;
}

export function AdminMatchList({ matches, csrfToken }: Props) {
  // Filter state
  const [search, setSearch] = useState('');
  const [phaseFilter, setPhaseFilter] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [sourceFilter, setSourceFilter] = useState('');

  // Edit modal state
  const [editMatch, setEditMatch] = useState<AdminMatchRowContract | null>(null);
  const [homeGoals, setHomeGoals] = useState('');
  const [awayGoals, setAwayGoals] = useState('');
  const [editStatus, setEditStatus] = useState('');
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [isPending, startTransition] = useTransition();
  const [removeTarget, setRemoveTarget] = useState<AdminMatchRowContract | null>(null);

  const filtered = useMemo(() => {
    const q = search.toLowerCase();
    return matches.filter(m => {
      if (phaseFilter && m.phase !== phaseFilter) return false;
      if (statusFilter && m.status !== statusFilter) return false;
      if (sourceFilter === 'API' && (m.hasManualOverride || m.externalProvider === 'SEED')) return false;
      if (sourceFilter === 'Manual' && !m.hasManualOverride) return false;
      if (sourceFilter === 'Seed' && m.externalProvider !== 'SEED') return false;
      if (q && !m.homeTeam.toLowerCase().includes(q) && !m.awayTeam.toLowerCase().includes(q)
        && !(m.groupName ?? '').toLowerCase().includes(q)) return false;
      return true;
    });
  }, [matches, search, phaseFilter, statusFilter, sourceFilter]);

  function openEdit(m: AdminMatchRowContract) {
    setEditMatch(m);
    setHomeGoals(m.officialHomeGoals !== null ? String(m.officialHomeGoals) : '');
    setAwayGoals(m.officialAwayGoals !== null ? String(m.officialAwayGoals) : '');
    setEditStatus(m.status);
    setError('');
    setSuccess('');
  }

  function closeEdit() {
    setEditMatch(null);
    setError('');
    setSuccess('');
  }

  function saveEdit() {
    if (!editMatch) return;
    const home = homeGoals !== '' ? parseInt(homeGoals, 10) : null;
    const away = awayGoals !== '' ? parseInt(awayGoals, 10) : null;
    if ((home !== null && isNaN(home)) || (away !== null && isNaN(away))) {
      setError('Placar inválido.'); return;
    }
    setError('');
    startTransition(async () => {
      try {
        const body: Record<string, unknown> = { status: editStatus, has_manual_override: true };
        if (home !== null) body.official_home_goals = home;
        if (away !== null) body.official_away_goals = away;
        const res = await fetch(`/api/admin/matches/${editMatch.id}/manual-override`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json', 'x-csrf-token': csrfToken },
          body: JSON.stringify(body),
        });
        if (!res.ok) {
          const b = await res.json().catch(() => ({}));
          setError(b?.error?.message || b?.detail?.message || b?.detail || `Erro ${res.status}`);
          return;
        }
        setSuccess('Salvo. Recálculo executado.');
        setTimeout(() => { closeEdit(); window.location.reload(); }, 1200);
      } catch {
        setError('Falha de rede.');
      }
    });
  }

  function confirmRemove() {
    if (!removeTarget) return;
    startTransition(async () => {
      try {
        const res = await fetch(`/api/admin/matches/${removeTarget.id}/manual-override`, {
          method: 'DELETE',
          headers: { 'x-csrf-token': csrfToken },
        });
        if (!res.ok && res.status !== 404 && res.status !== 204) {
          setRemoveTarget(null);
          return;
        }
        setRemoveTarget(null);
        window.location.reload();
      } catch {
        setRemoveTarget(null);
      }
    });
  }

  const phases = Array.from(new Set(matches.map(m => m.phase)));

  return (
    <>
      {/* Filters — functional */}
      <div className="filters" style={{ marginBottom: 16 }}>
        <input
          className="admin-input"
          placeholder="Buscar seleção, grupo..."
          value={search}
          onChange={e => setSearch(e.target.value)}
        />
        <select className="admin-select" value={phaseFilter} onChange={e => setPhaseFilter(e.target.value)}>
          <option value="">Fase: todas</option>
          {phases.map(p => <option key={p} value={p}>{phaseLabel[p] ?? p}</option>)}
        </select>
        <select className="admin-select" value={statusFilter} onChange={e => setStatusFilter(e.target.value)}>
          <option value="">Status: todos</option>
          <option value="SCHEDULED">Agendado</option>
          <option value="FINISHED">Finalizado</option>
          <option value="IN_PLAY">Ao vivo</option>
          <option value="CANCELLED">Cancelado</option>
        </select>
        <select className="admin-select" value={sourceFilter} onChange={e => setSourceFilter(e.target.value)}>
          <option value="">Fonte: todas</option>
          <option value="API">API</option>
          <option value="Manual">Manual</option>
          <option value="Seed">Seed</option>
        </select>
      </div>

      <div style={{ fontSize: 11, color: 'var(--tx3)', marginBottom: 10, fontFamily: 'Fira Code, monospace' }}>
        {filtered.length} partida{filtered.length !== 1 ? 's' : ''} {filtered.length < matches.length ? `(de ${matches.length})` : ''}
      </div>

      <div className="match-list">
        {/* Header */}
        <div className="match-row-admin header">
          <div className="th">Código</div>
          <div className="th">Partida</div>
          <div className="th">Data</div>
          <div className="th">Fonte</div>
          <div className="th" style={{ textAlign: 'right' }}>Ações</div>
        </div>

        {filtered.map((m, i) => (
          <div key={m.id} className="match-row-admin">
            <div className="admin-date">J{String(i + 1).padStart(2, '0')}</div>
            <div className="admin-teams">
              <div className="admin-team"><TeamBadge name={m.homeTeam} flag={m.homeFlag} iso2={m.homeIso2} code={m.homeCode} compact /></div>
              <span className="admin-vs">vs</span>
              <div className="admin-team"><TeamBadge name={m.awayTeam} flag={m.awayFlag} iso2={m.awayIso2} code={m.awayCode} compact /></div>
              {m.groupName && <span style={{ fontSize: 10, color: 'var(--tx3)', marginLeft: 4 }}>Gr.{m.groupName}</span>}
            </div>
            <div className="admin-date">{m.startsAt ? new Date(m.startsAt).toLocaleDateString('pt-BR') : '—'}</div>
            <div>
              <div className={`pill ${m.hasManualOverride ? 'orange' : m.externalProvider === 'SEED' ? 'neutral' : 'ok'}`}>
                <span className="dot" />{m.hasManualOverride ? 'manual' : m.externalProvider === 'SEED' ? 'seed' : 'API'}
              </div>
              <div className="admin-source">{m.status?.toLowerCase()}</div>
            </div>
            <div className="row-actions">
              <button className="btn-ghost" style={{ height: 32, fontSize: 11, padding: '0 10px' }} onClick={() => openEdit(m)}>
                Editar
              </button>
              <button
                className="btn-danger"
                style={{ height: 32, fontSize: 11, padding: '0 10px' }}
                onClick={() => setRemoveTarget(m)}
              >
                Remover
              </button>
            </div>
          </div>
        ))}

        {filtered.length === 0 && (
          <div style={{ textAlign: 'center', padding: 32, color: 'var(--tx3)', fontSize: 14 }}>
            {matches.length === 0 ? 'Nenhuma partida importada ainda.' : 'Nenhuma partida para os filtros selecionados.'}
          </div>
        )}
      </div>

      {/* Edit modal */}
      {editMatch && (
        <div className="modal-overlay" onClick={e => { if (e.target === e.currentTarget) closeEdit(); }}>
          <div className="modal-box">
            <div className="modal-header">
              <div className="modal-title">Editar partida</div>
              <button className="modal-close" onClick={closeEdit}>✕</button>
            </div>
            <div className="modal-body">
              <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 4 }}>
                <TeamBadge name={editMatch.homeTeam} flag={editMatch.homeFlag} iso2={editMatch.homeIso2} code={editMatch.homeCode} compact />
                <span style={{ color: 'var(--tx3)', fontSize: 12 }}>×</span>
                <TeamBadge name={editMatch.awayTeam} flag={editMatch.awayFlag} iso2={editMatch.awayIso2} code={editMatch.awayCode} compact />
                <span style={{ marginLeft: 'auto', fontSize: 11, color: 'var(--tx3)' }}>{phaseLabel[editMatch.phase] ?? editMatch.phase}{editMatch.groupName ? ` · Gr.${editMatch.groupName}` : ''}</span>
              </div>

              <div className="field-admin">
                <div className="field-label-admin">Status</div>
                <select className="admin-select" style={{ width: '100%' }} value={editStatus} onChange={e => setEditStatus(e.target.value)}>
                  <option value="SCHEDULED">SCHEDULED</option>
                  <option value="IN_PLAY">IN_PLAY</option>
                  <option value="FT">FT</option>
                  <option value="CANCELLED">CANCELLED</option>
                  <option value="POSTPONED">POSTPONED</option>
                </select>
              </div>

              <div className="field-admin">
                <div className="field-label-admin">Placar oficial</div>
                <div className="score-editor">
                  <div className="score-box">
                    <div className="score-team">{editMatch.homeTeam}</div>
                    <input className="score-input-admin" type="number" min={0} max={50} value={homeGoals} onChange={e => setHomeGoals(e.target.value)} placeholder="—" />
                  </div>
                  <div className="score-sep">×</div>
                  <div className="score-box">
                    <div className="score-team">{editMatch.awayTeam}</div>
                    <input className="score-input-admin" type="number" min={0} max={50} value={awayGoals} onChange={e => setAwayGoals(e.target.value)} placeholder="—" />
                  </div>
                </div>
              </div>

              {error && <div className="modal-error">{error}</div>}
              {success && <div className="modal-success">{success}</div>}
            </div>
            <div className="modal-footer">
              <button className="btn-ghost" style={{ height: 36, fontSize: 12 }} onClick={closeEdit} disabled={isPending}>Cancelar</button>
              <button className="btn-primary" style={{ height: 36, fontSize: 12, padding: '0 20px' }} onClick={saveEdit} disabled={isPending}>
                {isPending ? 'Salvando…' : 'Salvar →'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Confirm remove */}
      {removeTarget && (
        <div className="modal-overlay" onClick={e => { if (e.target === e.currentTarget) setRemoveTarget(null); }}>
          <div className="modal-box" style={{ maxWidth: 400 }}>
            <div className="modal-header">
              <div className="modal-title">Remover partida?</div>
              <button className="modal-close" onClick={() => setRemoveTarget(null)}>✕</button>
            </div>
            <div className="modal-body">
              <p style={{ fontSize: 14, color: 'var(--tx2)' }}>
                Confirma a remoção de <strong>{removeTarget.homeTeam} × {removeTarget.awayTeam}</strong>? Esta ação não pode ser desfeita.
              </p>
            </div>
            <div className="modal-footer">
              <button className="btn-ghost" style={{ height: 36, fontSize: 12 }} onClick={() => setRemoveTarget(null)} disabled={isPending}>Cancelar</button>
              <button className="btn-danger" style={{ height: 36, fontSize: 12, padding: '0 20px' }} onClick={confirmRemove} disabled={isPending}>
                {isPending ? 'Removendo…' : 'Remover'}
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
