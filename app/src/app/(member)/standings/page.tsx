import type { StandingsContract } from '../../../lib/contracts';
import { fetchBackendData } from '../../../lib/session';

export default async function StandingsPage() {
  const { data } = await fetchBackendData<StandingsContract>('/api/member/standings');
  const groups = data?.groups ?? [];

  return (
    <>
      <section className="hero">
        <div className="hero-content">
          <div>
            <div className="eyebrow"><span className="dot" />Classificação</div>
            <h1>Pontuação por <span>grupo</span>.</h1>
            <p>Pontos, gols marcados, sofridos e saldo — base para o chaveamento a partir das oitavas.</p>
          </div>
          <div className="deadline-card" style={{ minWidth: 200 }}>
            <div className="deadline-label">Grupos</div>
            <div style={{ fontSize: 40, fontWeight: 900, color: 'var(--or)', letterSpacing: '-.04em', lineHeight: 1, margin: '10px 0 6px' }}>{groups.length}</div>
            <div className="pill ok" style={{ width: 'fit-content' }}><span className="dot" />12 grupos</div>
          </div>
        </div>
      </section>

      {groups.length > 0 && (
        <div style={{ display: 'flex', gap: 16, marginBottom: 4, flexWrap: 'wrap' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 12, color: 'var(--tx3)' }}>
            <div style={{ width: 12, height: 12, borderRadius: 4, background: 'rgba(249,115,22,.15)', border: '1px solid rgba(249,115,22,.4)' }} />
            <span>Classificado diretamente (1º e 2º)</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 12, color: 'var(--tx3)' }}>
            <div style={{ width: 12, height: 12, borderRadius: 4, background: 'rgba(234,179,8,.08)', border: '1px solid rgba(234,179,8,.3)' }} />
            <span>3º lugar · pode classificar (8 melhores)</span>
          </div>
        </div>
      )}

      {groups.length === 0 ? (
        <div className="card">
          <div className="card-body" style={{ textAlign: 'center', padding: 40, color: 'var(--tx3)', fontSize: 14 }}>
            Nenhuma partida finalizada ainda. A classificação aparecerá conforme os resultados forem registrados.
          </div>
        </div>
      ) : (
        <div className="standings-grid">
          {groups.map(g => (
            <div key={g.group} className="card">
              <div className="card-header">
                <div>
                  <div className="card-title">Grupo {g.group}</div>
                  <div className="card-subtitle">{g.entries.length} seleções</div>
                </div>
                <div className="pill ok"><span className="dot" />{g.entries.filter(e => e.played > 0).length} jogos</div>
              </div>
              <div className="card-body">
                <div className="standings-table">
                  <div className="standings-row header">
                    <div className="st-pos">#</div>
                    <div className="st-team">Seleção</div>
                    <div className="st-num">J</div>
                    <div className="st-num">V</div>
                    <div className="st-num">E</div>
                    <div className="st-num">D</div>
                    <div className="st-num">GF</div>
                    <div className="st-num">GC</div>
                    <div className="st-num">SG</div>
                    <div className="st-pts">Pts</div>
                  </div>
                  {g.entries.map((e, i) => (
                    <div key={e.teamCode} className={`standings-row${i < 2 ? ' qualify' : i === 2 ? ' qualify-3rd' : ''}`}>
                      <div className="st-pos">{i + 1}</div>
                      <div className="st-team">{e.teamName}</div>
                      <div className="st-num">{e.played}</div>
                      <div className="st-num">{e.won}</div>
                      <div className="st-num">{e.drawn}</div>
                      <div className="st-num">{e.lost}</div>
                      <div className="st-num">{e.goalsFor}</div>
                      <div className="st-num">{e.goalsAgainst}</div>
                      <div className={`st-num ${e.goalDiff > 0 ? 'good' : e.goalDiff < 0 ? 'bad' : ''}`}>
                        {e.goalDiff > 0 ? `+${e.goalDiff}` : e.goalDiff}
                      </div>
                      <div className="st-pts">{e.points}</div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </>
  );
}
