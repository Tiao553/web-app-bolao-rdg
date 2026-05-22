import { AdminPlayerList } from '../../../../components/admin/player-edit-modal';
import { TeamBadge } from '../../../../components/ui/team-badge';
import type { AdminPlayersContract } from '../../../../lib/contracts';
import { getServerCsrfToken } from '../../../../lib/security';
import { fetchBackendData } from '../../../../lib/session';

export default async function AdminPlayersPage() {
  const csrfToken = await getServerCsrfToken();
  const { data } = await fetchBackendData<AdminPlayersContract>('/api/admin/players');
  const leaders = data?.leaders ?? [];
  const topScorer = leaders[0];

  return (
    <>
      {/* Hero */}
      <section className="hero">
        <div className="hero-content">
          <div>
            <div className="eyebrow"><span className="dot" />Artilharia e assistências</div>
            <h1>Controle o desempate de <span>artilheiros</span>.</h1>
            <p>Se a Copa terminar com 2 ou 3 artilheiros empatados em gols, o desempate considera assistências.</p>
          </div>
          <div className="top-scorer-card">
            <div className="top-name">{topScorer?.selectionLabel ?? 'Sem dados'}</div>
            {topScorer?.teamName && <div style={{ marginTop: 4 }}><TeamBadge name={topScorer.teamName} flag={topScorer.teamFlag} iso2={topScorer.teamIso2} code={topScorer.teamCode} compact /></div>}
            <div className="top-meta">{topScorer ? `${topScorer.predictionCount} palpites · líder atual` : 'Aguardando palpites'}</div>
          </div>
        </div>
      </section>

      {/* Stat summary */}
      <div className="stat-grid-admin" style={{ gridTemplateColumns: 'repeat(4, 1fr)', marginBottom: 16 }}>
        <div className="stat-admin"><div className="stat-value-admin">{leaders.length}</div><div className="stat-label-admin">jogadores</div></div>
        <div className="stat-admin"><div className="stat-value-admin">{topScorer?.goals ?? '—'}</div><div className="stat-label-admin">gols líder</div></div>
        <div className="stat-admin"><div className="stat-value-admin">{topScorer?.assists ?? '—'}</div><div className="stat-label-admin">assist. líder</div></div>
        <div className="stat-admin"><div className="stat-value-admin">{leaders.filter(l => l.goals === (topScorer?.goals ?? -1) && l.goals > 0).length}</div><div className="stat-label-admin">empatados</div></div>
      </div>

      {/* Full-width player list */}
      <div className="card">
        <div className="card-header">
          <div><div className="card-title">Artilheiros escolhidos</div><div className="card-subtitle">Gols, assistências e desempate</div></div>
          <div className="pill" style={{ color: 'var(--gold)', background: 'var(--gold-g)', border: '1px solid rgba(234,179,8,.24)' }}><span className="dot" />critério ativo</div>
        </div>
        <div className="card-body">
          {leaders.length === 0 ? (
            <div style={{ textAlign: 'center', padding: 32, color: 'var(--tx3)', fontSize: 14 }}>Nenhum palpite de artilheiro registrado ainda.</div>
          ) : (
            <AdminPlayerList leaders={leaders} csrfToken={csrfToken} />
          )}
        </div>
      </div>

      <div className="rule-box-admin" style={{ marginTop: 16 }}>
        <div className="rule-title-admin">Regra de desempate</div>
        <div className="rule-text-admin">Se houver 2 ou 3 artilheiros com o mesmo número de gols, vence para o bolão quem tiver mais assistências.</div>
      </div>
    </>
  );
}
