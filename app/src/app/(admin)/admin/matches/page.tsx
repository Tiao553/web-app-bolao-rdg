import { AdminMatchList } from '../../../../components/admin/match-edit-modal';
import type { AdminMatchesContract } from '../../../../lib/contracts';
import { getServerCsrfToken } from '../../../../lib/security';
import { fetchBackendData } from '../../../../lib/session';

export default async function AdminMatchesPage() {
  const csrfToken = await getServerCsrfToken();
  const { data } = await fetchBackendData<AdminMatchesContract>('/api/admin/matches');
  const matches = data?.matches ?? [];
  const summary = data?.summary ?? { total: 0, scheduled: 0, finished: 0, overridden: 0 };

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

      {/* Stats row */}
      <div className="stat-grid-admin" style={{ gridTemplateColumns: 'repeat(4, 1fr)', marginBottom: 16 }}>
        <div className="stat-admin"><div className="stat-value-admin">{summary.total}</div><div className="stat-label-admin">total</div></div>
        <div className="stat-admin"><div className="stat-value-admin">{summary.scheduled}</div><div className="stat-label-admin">agendadas</div></div>
        <div className="stat-admin"><div className="stat-value-admin">{summary.finished}</div><div className="stat-label-admin">finalizadas</div></div>
        <div className="stat-admin"><div className="stat-value-admin">{summary.overridden}</div><div className="stat-label-admin">overrides</div></div>
      </div>

      {/* Full-width match list with built-in filters */}
      <div className="card">
        <div className="card-header">
          <div><div className="card-title">Lista de partidas</div><div className="card-subtitle">Importadas, manuais e corrigidas</div></div>
          <div className="pill orange"><span className="dot" />editável</div>
        </div>
        <div className="card-body">
          <AdminMatchList matches={matches} csrfToken={csrfToken} />
        </div>
      </div>

      <div className="warning-admin" style={{ marginTop: 16 }}>
        <div className="warning-title-admin">Cuidado operacional</div>
        <div className="warning-text-admin">Alterar uma partida depois dos palpites pode exigir auditoria e recalcular dependências do chaveamento.</div>
      </div>
    </>
  );
}
