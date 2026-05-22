import type { MemberResultsContract } from '../../../lib/contracts';
import { fetchBackendData } from '../../../lib/session';

export default async function ResultsPage() {
  const { data } = await fetchBackendData<MemberResultsContract>('/api/member/results');
  const matches = data?.matches ?? [];
  const s = data?.summary;

  const barPct = (n: number, max: number) => Math.min(100, max > 0 ? (n / max) * 100 : 0);

  return (
    <>
      <section className="hero">
        <div className="hero-content">
          <div>
            <div className="eyebrow"><span className="dot" />Resultados oficiais</div>
            <h1>Confira seus pontos por <span>partida</span>.</h1>
            <p>Resultado oficial versus seu palpite, com breakdown de pontos por regra.</p>
          </div>
          <div className="deadline-card" style={{ minWidth: 200 }}>
            <div className="deadline-label">Pontuação total</div>
            <div style={{ fontSize: 36, fontWeight: 900, color: 'var(--or)', letterSpacing: '-.04em', marginTop: 8 }}>{s?.totalPoints ?? 0}</div>
            <div style={{ fontSize: 11, color: 'var(--tx3)', fontFamily: 'Fira Code', textTransform: 'uppercase', letterSpacing: '.08em' }}>pontos acumulados</div>
          </div>
        </div>
      </section>

      <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: 20 }}>
        {/* Partidas */}
        <div className="card">
          <div className="card-header">
            <div><div className="card-title">Partidas finalizadas</div><div className="card-subtitle">Resultado oficial × seu palpite</div></div>
            <div className="pill ok"><span className="dot" />atualizado</div>
          </div>
          <div className="card-body">
            {matches.length === 0 ? (
              <div style={{ textAlign: 'center', padding: 32, color: 'var(--tx3)', fontSize: 14 }}>Seus resultados aparecerão aqui assim que houver jogos com placar oficial e palpite salvo.</div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
                {matches.map(m => (
                  <div key={m.matchId} className="result-card">
                    <div className="result-head">
                      <span>{m.startsAt ? new Date(m.startsAt).toLocaleDateString('pt-BR', { day: '2-digit', month: 'short' }) : '—'} · {m.phase}{m.groupName ? ` Grupo ${m.groupName}` : ''}</span>
                      <span>{m.involvesBrazil ? 'Brasil ×2' : ''}</span>
                    </div>
                    <div className="result-body">
                      <div className="scoreline">
                        <div className="team"><span className="flag">🏳️</span><div className="team-name">{m.homeTeam}</div></div>
                        <div className="score">
                          <span>{m.officialHomeGoals ?? '—'}</span>
                          <span className="score-sep">×</span>
                          <span>{m.officialAwayGoals ?? '—'}</span>
                        </div>
                        <div className="team right"><span className="flag">🏳️</span><div className="team-name">{m.awayTeam}</div></div>
                      </div>
                      <div className="comparison">
                        <div className="compare-box">
                          <div className="compare-label">Seu palpite</div>
                          <div className="compare-value">{m.predictedHomeGoals ?? '—'} × {m.predictedAwayGoals ?? '—'}</div>
                        </div>
                        <div className={`points-earned ${(m.pointsAwarded ?? 0) > 0 ? 'good' : 'zero'}`}>
                          +{m.pointsAwarded ?? 0}<small>pts</small>
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Breakdown + Artilharia */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
          <div className="card">
            <div className="card-header"><div><div className="card-title">Breakdown</div><div className="card-subtitle">Pontos por regra</div></div></div>
            <div className="card-body">
              <div className="bar-list">
                <div className="bar-row"><div className="bar-label">Exatos</div><div className="bar-track"><div className="bar-fill" style={{ width: `${barPct(s?.exactHits ?? 0, 48)}%` }} /></div><div className="bar-value">{s?.exactHits ?? 0}</div></div>
                <div className="bar-row"><div className="bar-label">Resultado</div><div className="bar-track"><div className="bar-fill" style={{ width: `${barPct(s?.correctOutcomes ?? 0, 48)}%` }} /></div><div className="bar-value">{s?.correctOutcomes ?? 0}</div></div>
                <div className="bar-row"><div className="bar-label">Brasil ×2</div><div className="bar-track"><div className="bar-fill" style={{ width: `${barPct(s?.brazilBonusHits ?? 0, 20)}%` }} /></div><div className="bar-value">{s?.brazilBonusHits ?? 0}</div></div>
                <div className="bar-row"><div className="bar-label">Campeão</div><div className="bar-track"><div className="bar-fill" style={{ width: `${barPct(s?.championPoints ?? 0, 10)}%` }} /></div><div className="bar-value">{s?.championPoints ?? 0}</div></div>
                <div className="bar-row"><div className="bar-label">Artilheiro</div><div className="bar-track"><div className="bar-fill" style={{ width: `${barPct(s?.topScorerPoints ?? 0, 15)}%` }} /></div><div className="bar-value">{s?.topScorerPoints ?? 0}</div></div>
              </div>
            </div>
          </div>

          <div className="card">
            <div className="card-header"><div><div className="card-title">Artilharia</div><div className="card-subtitle">Gols + assistências</div></div></div>
            <div className="card-body">
              <div className="official-box" style={{ marginBottom: 16 }}>
                <div className="official-label">critério oficial</div>
                <div className="official-title">Gols, depois assistências</div>
                <div className="official-text">Em caso de empate em gols, vence quem tiver mais assistências.</div>
              </div>
              <div style={{ fontSize: 13, color: 'var(--tx3)', textAlign: 'center', padding: 12 }}>Tabela disponível após início da competição.</div>
            </div>
          </div>
        </div>
      </div>
    </>
  );
}
