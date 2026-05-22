import type { AdminMatchesContract } from '../../../../lib/contracts';
import { fetchBackendData } from '../../../../lib/session';

export default async function AdminResultsPage() {
  const { data } = await fetchBackendData<AdminMatchesContract>('/api/admin/matches');
  const matches = data?.matches ?? [];
  const finished = matches.filter(m => m.status === 'FINISHED');
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
          <div className="score-card-admin">
            <div className="score-num-admin">{finished.length}</div>
            <div className="score-label-admin">resultados processados</div>
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
            {overrides.length > 0 && <div className="pill warn"><span className="dot" />{overrides.length} override</div>}
          </div>
          <div className="card-body">
            <div className="result-list">
              {/* Header */}
              <div className="result-row-admin header">
                <div className="th">Código</div>
                <div className="th">Partida</div>
                <div className="th">Placar</div>
                <div className="th">Fonte</div>
                <div className="th" style={{ textAlign: 'right' }}>Ações</div>
              </div>

              {finished.slice(0, 20).map((m, i) => (
                <div key={m.id} className="result-row-admin">
                  <div className="admin-date">J{String(i + 1).padStart(2, '0')}</div>
                  <div className="admin-teams">
                    <div className="admin-team">{m.homeTeam}</div>
                    <span className="admin-vs">×</span>
                    <div className="admin-team">{m.awayTeam}</div>
                  </div>
                  <div>
                    <div style={{ fontFamily: 'Fira Code', fontWeight: 900, color: 'var(--or)' }}>
                      {m.officialHomeGoals ?? '—'} × {m.officialAwayGoals ?? '—'}
                    </div>
                    <div className="admin-source">finalizado</div>
                  </div>
                  <div>
                    <div className={`pill ${m.hasManualOverride ? 'orange' : 'ok'}`}><span className="dot" />{m.hasManualOverride ? 'manual' : 'API'}</div>
                    <div className="admin-source">{m.hasManualOverride ? 'override' : m.externalProvider ?? '—'}</div>
                  </div>
                  <div className="row-actions">
                    <button className="btn-ghost" style={{ height: 32, fontSize: 11, padding: '0 10px' }}>Editar</button>
                    <button className="btn-ok" style={{ height: 32, fontSize: 11, padding: '0 10px' }}>Recalcular</button>
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

          <div className="card">
            <div className="card-header"><div><div className="card-title">Editor rápido</div><div className="card-subtitle">Partida selecionada</div></div></div>
            <div className="card-body">
              <div className="editor-admin">
                <div className="editor-summary">
                  <div className="editor-title-admin">Selecione uma partida</div>
                  <div className="editor-sub-admin">Clique em "Editar" para carregar</div>
                </div>
                <div className="field-admin">
                  <div className="field-label-admin">Placar oficial</div>
                  <div className="score-editor">
                    <div className="score-box">
                      <div className="score-team">Casa</div>
                      <input className="score-input-admin" defaultValue="—" />
                    </div>
                    <div className="score-sep">×</div>
                    <div className="score-box">
                      <div className="score-team">Fora</div>
                      <input className="score-input-admin" defaultValue="—" />
                    </div>
                  </div>
                </div>
                <div className="field-admin">
                  <div className="field-label-admin">Motivo do override</div>
                  <input className="admin-input" placeholder="Ex: Correção após divergência da API" />
                </div>
                <div style={{ display: 'grid', gap: 8 }}>
                  <button className="btn-primary full" disabled style={{ opacity: .5 }}>Salvar e recalcular</button>
                  <button className="btn-ghost full" disabled style={{ opacity: .5 }}>Ver impacto no ranking</button>
                </div>
              </div>
            </div>
          </div>

          <div className="warning-admin">
            <div className="warning-title-admin">Impacto automático</div>
            <div className="warning-text-admin">Salvar um resultado recalcula pontos por placar, resultado, Brasil ×2, ranking e Explore.</div>
          </div>
        </div>
      </div>
    </>
  );
}
