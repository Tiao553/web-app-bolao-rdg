import { TeamBadge } from '../../../components/ui/team-badge';
import type { ExploreContract } from '../../../lib/contracts';
import { fetchBackendData } from '../../../lib/session';

export default async function ExplorePage() {
  const { data } = await fetchBackendData<ExploreContract>('/api/member/explore');
  const exploreReleased = data?.exploreReleased ?? false;

  // Group competition predictions by user; only shown after Explore opens
  const grouped = new Map<string, {
    name: string;
    champion?: { label: string; teamName?: string | null; teamCode?: string | null; teamFlag?: string | null; teamIso2?: string | null };
    scorer?: { label: string; teamName?: string | null; teamCode?: string | null; teamFlag?: string | null; teamIso2?: string | null };
  }>();
  (data?.competitionPredictions ?? []).forEach(item => {
    const entry = grouped.get(item.userId) ?? { name: item.userName };
    const selection = {
      label: item.selectionLabel,
      teamName: item.selectionTeamName,
      teamCode: item.selectionTeamCode,
      teamFlag: item.selectionTeamFlag,
      teamIso2: item.selectionTeamIso2,
    };
    if (item.predictionType === 'CHAMPION') entry.champion = selection;
    else entry.scorer = selection;
    grouped.set(item.userId, entry);
  });

  const entries = Array.from(grouped.entries());

  return (
    <>
      <section className="hero">
        <div className="hero-content">
        <div>
            <div className="eyebrow"><span className="dot" />Explore</div>
            <h1>Palpites de <span>campeão e artilheiro</span>.</h1>
            <p>Os palpites iniciais abrem no primeiro bloqueio e os resultados de partidas aparecem de forma cumulativa por fase.</p>
          </div>
          <div className={`pill ${exploreReleased ? 'ok' : 'warn'}`} style={{ alignSelf: 'flex-start', marginTop: 4 }}>
            <span className="dot" />{exploreReleased ? 'Resultados liberados' : 'Resultados bloqueados'}
          </div>
        </div>
      </section>

      {/* Competition predictions — gated by Explore */}
      <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: 20 }}>
        <div className="card">
          <div className="card-header">
            <div><div className="card-title">Campeão e artilheiro</div><div className="card-subtitle">Liberado junto com o Explore inicial</div></div>
            <div className={`pill ${exploreReleased ? 'ok' : 'warn'}`}><span className="dot" />{exploreReleased ? 'público' : 'bloqueado'}</div>
          </div>
          <div className="card-body">
            {!exploreReleased ? (
              <div style={{ textAlign: 'center', padding: 24, color: 'var(--tx3)', fontSize: 13 }}>
                <div style={{ fontSize: 20, marginBottom: 8 }}>🔒</div>
                Os palpites iniciais só ficam visíveis após o primeiro bloqueio da competição.
              </div>
            ) : entries.length === 0 ? (
              <div style={{ textAlign: 'center', padding: 32, color: 'var(--tx3)', fontSize: 14 }}>Nenhum palpite registrado ainda.</div>
            ) : (
              <div className="explore-grid">
                {entries.map(([uid, entry]) => (
                  <div key={uid} className="explore-card">
                    <div className="explore-card-name">{entry.name}</div>
                    <div className="prediction-row">
                      <div className="prediction-label">Campeão</div>
                      <div className="prediction-value">
                        {entry.champion
                          ? <TeamBadge name={entry.champion.teamName ?? entry.champion.label} flag={entry.champion.teamFlag} iso2={entry.champion.teamIso2} code={entry.champion.teamCode} compact />
                          : <span style={{ color: 'var(--tx3)' }}>—</span>}
                      </div>
                      <div className="points">{entry.champion ? '+10' : '—'}</div>
                    </div>
                    <div className="prediction-row">
                      <div className="prediction-label">Artilheiro</div>
                      <div className="prediction-value">
                        {entry.scorer ? (
                          <span className="player-team-inline">
                            <span>{entry.scorer.label}</span>
                            {entry.scorer.teamName && <TeamBadge name={entry.scorer.teamName} flag={entry.scorer.teamFlag} iso2={entry.scorer.teamIso2} code={entry.scorer.teamCode} compact />}
                          </span>
                        ) : <span style={{ color: 'var(--tx3)' }}>—</span>}
                      </div>
                      <div className="points">{entry.scorer ? '+15' : '—'}</div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
          {/* Match results section */}
          <div className="card">
            <div className="card-header">
              <div><div className="card-title">Resultados de partidas</div><div className="card-subtitle">Palpites de placar</div></div>
              <div className={`pill ${exploreReleased ? 'ok' : 'warn'}`}><span className="dot" />{exploreReleased ? 'liberado' : 'bloqueado'}</div>
            </div>
            <div className="card-body">
              {!exploreReleased ? (
                <div style={{ textAlign: 'center', padding: 24, color: 'var(--tx3)', fontSize: 13 }}>
                  <div style={{ fontSize: 20, marginBottom: 8 }}>🔒</div>
                  Os palpites de placar ficam visíveis após o fechamento oficial configurado pelo admin.
                </div>
              ) : (data?.matchPredictions ?? []).length === 0 ? (
                <div style={{ textAlign: 'center', padding: 24, color: 'var(--tx3)', fontSize: 13 }}>Nenhum palpite de partida registrado.</div>
              ) : (
                <div style={{ fontSize: 13, color: 'var(--tx2)' }}>
                  {(data?.matchPredictions ?? []).length} palpites de partidas disponíveis.
                </div>
              )}
            </div>
          </div>

          <div className="card">
            <div className="card-header"><div><div className="card-title">Insights</div><div className="card-subtitle">Comparativo geral</div></div></div>
            <div className="card-body">
              {!exploreReleased ? (
                <div style={{ textAlign: 'center', padding: 24, color: 'var(--tx3)', fontSize: 13 }}>
                  <div style={{ fontSize: 20, marginBottom: 8 }}>🔒</div>
                  Os comparativos só aparecem depois da liberação cumulativa do Explore.
                </div>
              ) : (
                <div className="insight-list">
                  <div className="insight"><div className="insight-icon">🏆</div><div><div className="insight-title">Campeão mais escolhido</div><div className="insight-text">{entries.length > 0 ? (() => { const counts: Record<string, number> = {}; entries.forEach(([, e]) => { if (e.champion) counts[e.champion.label] = (counts[e.champion.label] || 0) + 1; }); const top = Object.entries(counts).sort((a, b) => b[1] - a[1])[0]; return top ? `${top[0]} (${top[1]}x)` : '—'; })() : '—'}</div></div></div>
                  <div className="insight"><div className="insight-icon">⚽</div><div><div className="insight-title">Artilheiro favorito</div><div className="insight-text">{entries.length > 0 ? (() => { const counts: Record<string, number> = {}; entries.forEach(([, e]) => { if (e.scorer) counts[e.scorer.label] = (counts[e.scorer.label] || 0) + 1; }); const top = Object.entries(counts).sort((a, b) => b[1] - a[1])[0]; return top ? `${top[0]} (${top[1]}x)` : '—'; })() : '—'}</div></div></div>
                  <div className="insight"><div className="insight-icon">#</div><div><div className="insight-title">Participantes</div><div className="insight-text">{entries.length} com palpites registrados</div></div></div>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </>
  );
}
