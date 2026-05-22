import { TeamBadge } from '../../../../components/ui/team-badge';
import type { AdminPlayersContract } from '../../../../lib/contracts';
import { fetchBackendData } from '../../../../lib/session';

export default async function AdminPlayersPage() {
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
            <p>Se a Copa terminar com 2 ou 3 artilheiros empatados em gols, o desempate considera assistências. Esta tela permite auditar gols, assistências e pontuação dos palpites iniciais.</p>
          </div>
          <div className="top-scorer-card">
            <div className="top-name">{topScorer?.selectionLabel ?? 'Sem dados'}</div>
            {topScorer?.teamName && <div style={{ marginTop: 4 }}><TeamBadge name={topScorer.teamName} flag={topScorer.teamFlag} code={topScorer.teamCode} compact /></div>}
            <div className="top-meta">{topScorer ? `${topScorer.predictionCount} palpites · líder atual` : 'Aguardando palpites'}</div>
          </div>
        </div>
      </section>

      {/* Filters */}
      <div className="filters-3">
        <input className="admin-input" placeholder="Buscar jogador ou seleção..." readOnly />
        <select className="admin-select"><option>Seleção: todas</option><option>Brasil</option><option>França</option><option>Argentina</option></select>
        <select className="admin-select"><option>Ordenar: palpites</option><option>Gols</option><option>Assistências</option></select>
      </div>

      {/* 2-col grid */}
      <div className="admin-grid">
        {/* Player list */}
        <div className="card">
          <div className="card-header">
            <div><div className="card-title">Artilheiros escolhidos</div><div className="card-subtitle">Gols, assistências e desempate</div></div>
            <div className="pill" style={{ color: 'var(--gold)', background: 'var(--gold-g)', border: '1px solid rgba(234,179,8,.24)' }}><span className="dot" />critério ativo</div>
          </div>
          <div className="card-body">
            {leaders.length === 0 ? (
              <div style={{ textAlign: 'center', padding: 32, color: 'var(--tx3)', fontSize: 14 }}>Nenhum palpite de artilheiro registrado ainda.</div>
            ) : (
              <div className="player-list-admin">
                <div className="player-row-admin header">
                  <div className="th">#</div>
                  <div className="th">Jogador</div>
                  <div className="th">Gols</div>
                  <div className="th">Assist.</div>
                  <div className="th">Status</div>
                  <div className="th" style={{ textAlign: 'right' }}>Ações</div>
                </div>
                {leaders.map((l, i) => (
                  <div key={l.selectionKey} className="player-row-admin">
                    <div className="avatar" style={{ width: 36, height: 36, fontSize: 12 }}>{i + 1}</div>
                    <div>
                      <div className="player-name-admin">{l.selectionLabel}</div>
                      <div className="player-detail-admin">
                        {l.teamName ? <><TeamBadge name={l.teamName} flag={l.teamFlag} code={l.teamCode} compact /> · </> : null}
                        escolhido por {l.predictionCount} palpiteiro{l.predictionCount !== 1 ? 's' : ''}
                      </div>
                    </div>
                    <div className="num-admin gold">—</div>
                    <div className="num-admin">—</div>
                    <div className={`pill ${i === 0 ? 'warn' : 'ok'}`}><span className="dot" />{i === 0 ? 'líder' : 'ativo'}</div>
                    <div className="row-actions">
                      <button className="btn-ghost" style={{ height: 32, fontSize: 11, padding: '0 10px' }}>Editar</button>
                      <button className="btn-ok" style={{ height: 32, fontSize: 11, padding: '0 10px' }}>Validar</button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Sidebar */}
        <div className="side-list">
          <div className="card">
            <div className="card-header"><div><div className="card-title">Resumo</div><div className="card-subtitle">Estatísticas</div></div></div>
            <div className="card-body">
              <div className="stat-grid-admin">
                <div className="stat-admin"><div className="stat-value-admin">{leaders.length}</div><div className="stat-label-admin">jogadores</div></div>
                <div className="stat-admin"><div className="stat-value-admin">—</div><div className="stat-label-admin">gols</div></div>
                <div className="stat-admin"><div className="stat-value-admin">—</div><div className="stat-label-admin">assist.</div></div>
                <div className="stat-admin"><div className="stat-value-admin">0</div><div className="stat-label-admin">empatados</div></div>
              </div>
            </div>
          </div>

          <div className="rule-box-admin">
            <div className="rule-title-admin">Regra de desempate</div>
            <div className="rule-text-admin">Se houver 2 ou 3 artilheiros com o mesmo número de gols, vence para o bolão quem tiver mais assistências.</div>
          </div>

          <div className="card">
            <div className="card-header"><div><div className="card-title">Editor rápido</div><div className="card-subtitle">Jogador selecionado</div></div></div>
            <div className="card-body">
              <div className="editor-admin">
                <div className="editor-summary">
                  <div className="editor-title-admin">{topScorer?.selectionLabel ?? 'Selecione um jogador'}</div>
                  {topScorer?.teamName && <div style={{ marginTop: 4 }}><TeamBadge name={topScorer.teamName} flag={topScorer.teamFlag} code={topScorer.teamCode} compact /></div>}
                  <div className="editor-sub-admin">{topScorer ? `líder atual · ${topScorer.predictionCount} palpites` : 'Clique em Editar para carregar'}</div>
                </div>
                <div className="field-admin">
                  <div className="field-label-admin">Estatísticas oficiais</div>
                  <div className="stat-editor-admin">
                    <div>
                      <div className="stat-input-title">Gols</div>
                      <input className="stat-input-admin" defaultValue="0" />
                    </div>
                    <div>
                      <div className="stat-input-title">Assistências</div>
                      <input className="stat-input-admin" defaultValue="0" />
                    </div>
                  </div>
                </div>
                <div className="field-admin">
                  <div className="field-label-admin">Fonte</div>
                  <div className="source-box">
                    <div className="source-text-admin">API-SPORTS v3 /players/statistics</div>
                    <div className="pill ok">sync</div>
                  </div>
                </div>
                <div style={{ display: 'grid', gap: 8 }}>
                  <button className="btn-primary full" disabled style={{ opacity: .5 }}>Salvar e recalcular</button>
                  <button className="btn-ghost full" disabled style={{ opacity: .5 }}>Ver palpites afetados</button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </>
  );
}
