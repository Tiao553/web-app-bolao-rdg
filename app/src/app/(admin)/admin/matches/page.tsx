import { TeamBadge } from '../../../../components/ui/team-badge';
import type { AdminMatchesContract } from '../../../../lib/contracts';
import { fetchBackendData } from '../../../../lib/session';

const phaseLabel: Record<string, string> = {
  GROUP_STAGE: 'Grupos', ROUND_OF_32: '16 avos', ROUND_OF_16: 'Oitavas',
  QUARTER_FINAL: 'Quartas', SEMI_FINAL: 'Semi', THIRD_PLACE: '3º lugar', FINAL: 'Final',
};

export default async function AdminMatchesPage() {
  const { data } = await fetchBackendData<AdminMatchesContract>('/api/admin/matches');
  const matches = data?.matches ?? [];
  const summary = data?.summary ?? { total: 0, scheduled: 0, finished: 0, overridden: 0 };
  const apiCount = matches.filter(m => m.externalProvider && m.externalProvider !== 'SEED' && m.externalProvider !== 'ADMIN').length;
  const seedCount = matches.filter(m => m.externalProvider === 'SEED').length;

  return (
    <>
      {/* Hero */}
      <section className="hero">
        <div className="hero-content">
          <div>
            <div className="eyebrow"><span className="dot" />Gestão de partidas</div>
            <h1>Corrija jogos antes de afetar <span>palpites</span>.</h1>
            <p>Visualize partidas importadas automaticamente, altere horários, seleções, fase, grupo ou crie jogos manualmente quando a API trouxer dados incorretos.</p>
          </div>
          <div className="match-health">
            <div className="health-num">{summary.total}</div>
            <div className="health-label">partidas cadastradas</div>
          </div>
        </div>
      </section>

      {/* Filters */}
      <div className="filters">
        <input className="admin-input" placeholder="Buscar seleção ou código da partida..." readOnly />
        <select className="admin-select"><option>Fase: todas</option>{Object.entries(phaseLabel).map(([k, v]) => <option key={k} value={k}>{v}</option>)}</select>
        <select className="admin-select"><option>Status: todos</option><option>SCHEDULED</option><option>FINISHED</option></select>
        <select className="admin-select"><option>Fonte: todas</option><option>API</option><option>Manual</option><option>Seed</option></select>
      </div>

      {/* 2-col grid */}
      <div className="admin-grid">
        {/* Match list */}
        <div className="card">
          <div className="card-header">
            <div><div className="card-title">Lista de partidas</div><div className="card-subtitle">Importadas, manuais e corrigidas</div></div>
            <div className="pill orange"><span className="dot" />editável</div>
          </div>
          <div className="card-body">
            <div className="match-list">
              {/* Header */}
              <div className="match-row-admin header">
                <div className="th">Código</div>
                <div className="th">Partida</div>
                <div className="th">Data</div>
                <div className="th">Fonte</div>
                <div className="th" style={{ textAlign: 'right' }}>Ações</div>
              </div>

              {matches.slice(0, 20).map((m, i) => (
                <div key={m.id} className="match-row-admin">
                  <div className="admin-date">J{String(i + 1).padStart(2, '0')}</div>
                  <div className="admin-teams">
                    <div className="admin-team"><TeamBadge name={m.homeTeam} flag={m.homeFlag} code={m.homeCode} compact /></div>
                    <span className="admin-vs">vs</span>
                    <div className="admin-team"><TeamBadge name={m.awayTeam} flag={m.awayFlag} code={m.awayCode} compact /></div>
                  </div>
                  <div className="admin-date">{m.startsAt ? new Date(m.startsAt).toLocaleDateString('pt-BR') : '—'}</div>
                  <div>
                    <div className={`pill ${m.hasManualOverride ? 'orange' : m.externalProvider === 'SEED' ? 'neutral' : 'ok'}`}>
                      <span className="dot" />{m.hasManualOverride ? 'manual' : m.externalProvider === 'SEED' ? 'seed' : 'API'}
                    </div>
                    <div className="admin-source">{m.status?.toLowerCase()}</div>
                  </div>
                  <div className="row-actions">
                    <button className="btn-ghost" style={{ height: 32, fontSize: 11, padding: '0 10px' }}>Editar</button>
                    {m.status === 'FINISHED' ? (
                      <button className="btn-ok" style={{ height: 32, fontSize: 11, padding: '0 10px' }}>Validar</button>
                    ) : (
                      <button className="btn-danger" style={{ height: 32, fontSize: 11, padding: '0 10px' }}>Remover</button>
                    )}
                  </div>
                </div>
              ))}

              {matches.length === 0 && (
                <div style={{ textAlign: 'center', padding: 32, color: 'var(--tx3)', fontSize: 14 }}>Nenhuma partida importada ainda.</div>
              )}
            </div>
          </div>
        </div>

        {/* Sidebar */}
        <div className="side-list">
          {/* Summary stats */}
          <div className="card">
            <div className="card-header"><div><div className="card-title">Resumo</div><div className="card-subtitle">Cadastro de jogos</div></div></div>
            <div className="card-body">
              <div className="stat-grid-admin">
                <div className="stat-admin"><div className="stat-value-admin">{summary.total}</div><div className="stat-label-admin">total</div></div>
                <div className="stat-admin"><div className="stat-value-admin">{apiCount}</div><div className="stat-label-admin">API</div></div>
                <div className="stat-admin"><div className="stat-value-admin">{seedCount}</div><div className="stat-label-admin">seed</div></div>
                <div className="stat-admin"><div className="stat-value-admin">{summary.overridden}</div><div className="stat-label-admin">overrides</div></div>
              </div>
            </div>
          </div>

          {/* Quick editor */}
          <div className="card">
            <div className="card-header"><div><div className="card-title">Editor rápido</div><div className="card-subtitle">Partida selecionada</div></div></div>
            <div className="card-body">
              <div className="edit-panel">
                <div className="field-admin"><div className="field-label-admin">Partida</div><div className="field-value-admin">Selecione uma partida</div></div>
                <div className="field-admin"><div className="field-label-admin">Fase</div><div className="field-value-admin">—</div></div>
                <div className="field-admin"><div className="field-label-admin">Data/Hora</div><div className="field-value-admin">—</div></div>
                <button className="btn-primary full" disabled style={{ opacity: .5 }}>Salvar alterações</button>
              </div>
            </div>
          </div>

          {/* Warning */}
          <div className="warning-admin">
            <div className="warning-title-admin">Cuidado operacional</div>
            <div className="warning-text-admin">Alterar uma partida depois dos palpites pode exigir auditoria e recalcular dependências do chaveamento.</div>
          </div>
        </div>
      </div>
    </>
  );
}
