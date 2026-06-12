import { TeamBadge } from '../../../../components/ui/team-badge';
import { ManualResultModal } from '../../../../components/admin/manual-result-modal';
import type { AdminMatchesContract } from '../../../../lib/contracts';
import { getServerCsrfToken } from '../../../../lib/security';
import { fetchBackendData } from '../../../../lib/session';

const FINISHED_STATUSES = new Set(['FT', 'AET', 'PEN', 'FINISHED']);

export default async function AdminResultsPage() {
  const csrfToken = await getServerCsrfToken();
  const { data } = await fetchBackendData<AdminMatchesContract>('/api/admin/matches');
  const matches = data?.matches ?? [];
  const finished = matches.filter(m => FINISHED_STATUSES.has(m.status));
  const live = matches.filter(m => m.status === 'LIVE' || m.status === 'IN_PLAY');
  const overrides = matches.filter(m => m.hasManualOverride);

  return (
    <>
      {/* Hero */}
      <section className="hero">
        <div className="hero-content">
          <div>
            <div className="eyebrow"><span className="dot" />Resultados oficiais</div>
            <h1>Altere placares com <span>rastreabilidade</span>.</h1>
            <p>Resultados vêm da API-SPORTS v3, mas o administrador pode aplicar override manual. Toda alteração recalcula pontuação, ranking, Explore e chaveamento.</p>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: 10 }}>
            <div className="score-card-admin">
              <div className="score-num-admin">{finished.length}</div>
              <div className="score-label-admin">resultados processados</div>
            </div>
            <ManualResultModal matches={matches} csrfToken={csrfToken} />
          </div>
        </div>
      </section>

      {/* Filters */}
      <div className="filters">
        <input className="admin-input" placeholder="Buscar partida, seleção ou código..." readOnly />
        <select className="admin-select"><option>Fase: todas</option><option>Grupos</option><option>16 avos</option><option>Oitavas</option></select>
        <select className="admin-select"><option>Fonte: todas</option><option>API</option><option>Manual</option></select>
        <select className="admin-select"><option>Status: todos</option><option>Finalizado</option><option>Ao vivo</option><option>Pendente</option></select>
      </div>

      {/* 2-col grid */}
      <div className="admin-grid">
        {/* Result list */}
        <div className="card">
          <div className="card-header">
            <div><div className="card-title">Resultados das partidas</div><div className="card-subtitle">API, manual override e recalculação</div></div>
            {overrides.length > 0 && <div className="pill warn"><span className="dot" />{overrides.length} override{overrides.length > 1 ? 's' : ''}</div>}
          </div>
          <div className="card-body">
            <div className="result-list">
              {/* Header */}
              <div className="result-row-admin header">
                <div className="th">Código</div>
                <div className="th">Partida</div>
                <div className="th">Placar</div>
                <div className="th">Fonte</div>
              </div>

              {finished.slice(0, 30).map((m, i) => (
                <div key={m.id} className={`result-row-admin${m.hasManualOverride ? ' manual-override-row' : ''}`}>
                  <div className="admin-date">J{String(i + 1).padStart(2, '0')}</div>
                  <div className="admin-teams">
                    <div className="admin-team"><TeamBadge name={m.homeTeam} flag={m.homeFlag} iso2={m.homeIso2} code={m.homeCode} compact /></div>
                    <span className="admin-vs">×</span>
                    <div className="admin-team"><TeamBadge name={m.awayTeam} flag={m.awayFlag} iso2={m.awayIso2} code={m.awayCode} compact /></div>
                    {m.goalScorers && m.goalScorers.length > 0 && (
                      <div className="match-scorers-inline">
                        {m.goalScorers.map((s, si) => (
                          <span key={si} className="scorer-chip">{s.name}{s.goals > 1 ? ` ×${s.goals}` : ''}</span>
                        ))}
                      </div>
                    )}
                  </div>
                  <div>
                    <div style={{ fontFamily: 'Fira Code', fontWeight: 900, color: 'var(--or)' }}>
                      {m.officialHomeGoals ?? '—'} × {m.officialAwayGoals ?? '—'}
                    </div>
                    <div className="admin-source">finalizado</div>
                  </div>
                  <div>
                    {m.hasManualOverride ? (
                      <div className="pill orange" title="Resultado inserido manualmente pelo admin"><span className="dot" />manual</div>
                    ) : (
                      <div className="pill ok"><span className="dot" />API</div>
                    )}
                    <div className="admin-source">{m.hasManualOverride ? 'override admin' : (m.externalProvider ?? '—')}</div>
                  </div>
                </div>
              ))}

              {finished.length === 0 && (
                <div style={{ textAlign: 'center', padding: 32, color: 'var(--tx3)', fontSize: 14 }}>Nenhuma partida finalizada ainda.</div>
              )}
            </div>
          </div>
        </div>

        {/* Sidebar */}
        <div className="side-list">
          <div className="card">
            <div className="card-header"><div><div className="card-title">Resumo</div><div className="card-subtitle">Pontuação</div></div></div>
            <div className="card-body">
              <div className="stat-grid-admin">
                <div className="stat-admin"><div className="stat-value-admin">{finished.length}</div><div className="stat-label-admin">finalizados</div></div>
                <div className="stat-admin"><div className="stat-value-admin">{overrides.length}</div><div className="stat-label-admin">manual</div></div>
                <div className="stat-admin"><div className="stat-value-admin">{live.length}</div><div className="stat-label-admin">ao vivo</div></div>
                <div className="stat-admin"><div className="stat-value-admin">0</div><div className="stat-label-admin">erros</div></div>
              </div>
            </div>
          </div>

          {overrides.length > 0 && (
            <div className="card">
              <div className="card-header">
                <div><div className="card-title">Overrides manuais</div><div className="card-subtitle">Inseridos pelo admin</div></div>
                <div className="pill orange"><span className="dot" />{overrides.length}</div>
              </div>
              <div className="card-body">
                <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                  {overrides.map(m => (
                    <div key={m.id} style={{ fontSize: 12, color: 'var(--tx2)', borderLeft: '2px solid var(--or)', paddingLeft: 10 }}>
                      <div style={{ fontWeight: 600 }}>{m.homeTeam} × {m.awayTeam}</div>
                      <div style={{ color: 'var(--tx3)' }}>
                        {m.officialHomeGoals ?? '—'} × {m.officialAwayGoals ?? '—'}
                        {m.goalScorers && m.goalScorers.length > 0 && ` · ${m.goalScorers.map(s => s.name).join(', ')}`}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          <div className="warning-admin">
            <div className="warning-title-admin">Impacto automático</div>
            <div className="warning-text-admin">Salvar um resultado recalcula pontos por placar, resultado, Brasil ×2, ranking e Explore.</div>
          </div>
        </div>
      </div>
    </>
  );
}
