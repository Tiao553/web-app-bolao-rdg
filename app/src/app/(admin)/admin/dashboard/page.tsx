import type { AdminDashboardContract } from '../../../../lib/contracts';
import { fetchBackendData } from '../../../../lib/session';

export default async function AdminDashboardPage() {
  const { data } = await fetchBackendData<AdminDashboardContract>('/api/admin/dashboard');

  const syncs = data?.latestSyncs ?? [];
  const total = data?.users.total ?? 0;
  const approved = data?.users.approved ?? 0;
  const pending = data?.users.pending ?? 0;
  const matchTotal = data?.matches.total ?? 0;
  const matchFinished = data?.matches.finished ?? 0;

  return (
    <>
      {/* Hero */}
      <section className="hero">
        <div className="hero-content">
          <div>
            <div className="eyebrow"><span className="dot" />Painel administrativo</div>
            <h1>Controle do <span>Bolão da Copa</span>.</h1>
            <p>Monitore usuários, integração automática, jogos, resultados oficiais e regras críticas de bloqueio/liberação do Explore.</p>
          </div>
          <div className="health-card">
            <div className="health-label">Status operacional</div>
            <div className="health-main">
              <div className="health-icon">✓</div>
              <div>
                <div className="health-title">Tudo saudável</div>
                <div className="health-text">{pending} pendências de aprovação e {matchTotal} partidas cadastradas.</div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* 4 metrics */}
      <div className="grid-12" style={{ marginBottom: 18 }}>
        <div className="card col-span-3"><div className="card-body"><div className="metric-value" style={{ color: 'var(--or)' }}>{total}</div><div className="metric-note">usuários cadastrados</div></div></div>
        <div className="card col-span-3"><div className="card-body"><div className="metric-value">{approved}</div><div className="metric-note">participantes aprovados</div></div></div>
        <div className="card col-span-3"><div className="card-body"><div className="metric-value">{matchTotal}</div><div className="metric-note">partidas importadas</div></div></div>
        <div className="card col-span-3"><div className="card-body"><div className="metric-value" style={{ color: pending > 0 ? 'var(--or)' : undefined }}>{pending}</div><div className="metric-note">ações críticas pendentes</div></div></div>
      </div>

      {/* Main grid */}
      <div className="grid-12">
        {/* Governance queue */}
        <div className="card col-span-8">
          <div className="card-header">
            <div><div className="card-title">Fila de governança</div><div className="card-subtitle">Ações que exigem admin</div></div>
            <div className={`pill ${pending > 0 ? 'warn' : 'ok'}`}><span className="dot" />{pending} pendentes</div>
          </div>
          <div className="card-body">
            <div className="task-list">
              <div className="task-row">
                <div className="task-icon">👥</div>
                <div>
                  <div className="task-title">{pending} usuários aguardando aprovação</div>
                  <div className="task-text">Evita múltiplas contas e garante controle de participação.</div>
                </div>
                <a href="/admin/users" className={`pill ${pending > 0 ? 'warn' : 'ok'}`} style={{ textDecoration: 'none' }}><span className="dot" />revisar</a>
              </div>
              <div className="task-row">
                <div className="task-icon">◆</div>
                <div>
                  <div className="task-title">{matchFinished} partidas finalizadas</div>
                  <div className="task-text">Verifique se algum resultado precisa de override manual.</div>
                </div>
                <a href="/admin/results" className="pill orange" style={{ textDecoration: 'none' }}><span className="dot" />auditar</a>
              </div>
              <div className="task-row">
                <div className="task-icon">⛓</div>
                <div>
                  <div className="task-title">Sincronização com API-SPORTS v3</div>
                  <div className="task-text">Jogos e resultados verificados automaticamente a cada 30 min.</div>
                </div>
                <a href="/admin/integration" className="pill ok" style={{ textDecoration: 'none' }}><span className="dot" />ver</a>
              </div>
            </div>
          </div>
        </div>

        {/* Tournament progress */}
        <div className="card col-span-4">
          <div className="card-header"><div><div className="card-title">Progresso do torneio</div><div className="card-subtitle">Cobertura operacional</div></div></div>
          <div className="card-body">
            <div className="progress-list-admin">
              {[
                { label: 'Jogos', val: matchTotal, max: 104 },
                { label: 'Resultados', val: matchFinished, max: 104 },
                { label: 'Usuários', val: approved, max: Math.max(total, 1) },
              ].map(({ label, val, max }) => (
                <div key={label} className="bar-row">
                  <div className="bar-label">{label}</div>
                  <div className="bar-track"><div className="bar-fill" style={{ width: `${Math.round((val / max) * 100)}%` }} /></div>
                  <div className="bar-value">{val}</div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Recent activity */}
        <div className="card col-span-8">
          <div className="card-header"><div><div className="card-title">Atividade recente</div><div className="card-subtitle">Auditoria</div></div></div>
          <div className="card-body">
            {syncs.length === 0 ? (
              <div style={{ fontSize: 13, color: 'var(--tx3)' }}>Nenhuma atividade registrada ainda.</div>
            ) : (
              <div className="activity-list">
                {syncs.slice(0, 5).map(s => (
                  <div key={s.id} className="activity-row">
                    <div className="avatar">API</div>
                    <div>
                      <div className="activity-title">{s.operation}</div>
                      <div className="activity-text">{s.message ?? '—'}</div>
                    </div>
                    <div className={`pill ${s.status === 'SUCCESS' ? 'ok' : 'warn'}`}><span className="dot" />{s.status}</div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Shortcuts */}
        <div className="card col-span-4">
          <div className="card-header"><div><div className="card-title">Atalhos</div><div className="card-subtitle">Operação rápida</div></div></div>
          <div className="card-body">
            <div className="task-list">
              <a href="/admin/matches" className="task-row" style={{ textDecoration: 'none' }}>
                <div className="task-icon">▦</div>
                <div><div className="task-title">Gerenciar partidas</div><div className="task-text">Importar ou criar manualmente.</div></div>
              </a>
              <a href="/admin/results" className="task-row" style={{ textDecoration: 'none' }}>
                <div className="task-icon">↻</div>
                <div><div className="task-title">Recalcular ranking</div><div className="task-text">Após correção de resultado.</div></div>
              </a>
              <a href="/admin/settings" className="task-row" style={{ textDecoration: 'none' }}>
                <div className="task-icon">⚙</div>
                <div><div className="task-title">Configurações</div><div className="task-text">Prazos e regras do bolão.</div></div>
              </a>
            </div>
          </div>
        </div>
      </div>
    </>
  );
}
