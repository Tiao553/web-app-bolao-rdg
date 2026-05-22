import { TeamBadge } from '../../../components/ui/team-badge';
import type { ExploreContract } from '../../../lib/contracts';
import { fetchBackendData } from '../../../lib/session';

export default async function ExplorePage() {
  const { data } = await fetchBackendData<ExploreContract>('/api/member/explore');

  if (!data?.exploreReleased) {
    return (
      <>
        <section className="hero">
          <div className="hero-content">
            <div>
              <div className="eyebrow"><span className="dot" />Explore</div>
              <h1>Veja os palpites dos <span>outros participantes</span>.</h1>
              <p>Esta área fica disponível apenas após o horário oficial de fechamento dos palpites.</p>
            </div>
          </div>
        </section>
        <div className="card">
          <div className="card-header"><div><div className="card-title">Estado bloqueado</div><div className="card-subtitle">Exemplo antes do fechamento</div></div></div>
          <div className="card-body">
            <div className="locked-preview">
              <div className="blur-lines">
                <div className="blur-line" /><div className="blur-line short" /><div className="blur-line" /><div className="blur-line short" />
              </div>
              <div className="locked-text">
                <div><strong>Explore bloqueado</strong><span>Disponível somente após fechamento dos palpites.</span></div>
              </div>
            </div>
          </div>
        </div>
      </>
    );
  }

  const grouped = new Map<string, {
    name: string;
    champion?: { label: string; teamName?: string | null; teamCode?: string | null; teamFlag?: string | null };
    scorer?: { label: string; teamName?: string | null; teamCode?: string | null; teamFlag?: string | null };
    exact?: number;
    brazil?: number;
    similarity?: number;
  }>();
  data.competitionPredictions.forEach(item => {
    const entry = grouped.get(item.userId) ?? { name: item.userName };
    const selection = {
      label: item.selectionLabel,
      teamName: item.selectionTeamName,
      teamCode: item.selectionTeamCode,
      teamFlag: item.selectionTeamFlag,
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
            <div className="eyebrow"><span className="dot" />Palpites liberados</div>
            <h1>Veja os palpites dos <span>outros participantes</span>.</h1>
            <p>Após o fechamento, o Explore publica os palpites de todos os participantes aprovados.</p>
          </div>
          <div className="pill ok" style={{ alignSelf: 'flex-start', marginTop: 4 }}><span className="dot" />público</div>
        </div>
      </section>

      <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: 20 }}>
        <div className="card">
          <div className="card-header"><div><div className="card-title">Palpites dos participantes</div><div className="card-subtitle">Visão liberada após fechamento</div></div></div>
          <div className="card-body">
            {entries.length === 0 ? (
              <div style={{ textAlign: 'center', padding: 32, color: 'var(--tx3)', fontSize: 14 }}>Nenhum palpite público disponível ainda.</div>
            ) : (
              <div className="explore-grid">
                {entries.map(([uid, entry]) => (
                  <div key={uid} className="explore-card">
                    <div className="explore-card-name">{entry.name}</div>
                    <div className="prediction-row">
                      <div className="prediction-label">Campeão</div>
                      <div className="prediction-value">
                        {entry.champion ? <TeamBadge name={entry.champion.teamName ?? entry.champion.label} flag={entry.champion.teamFlag} code={entry.champion.teamCode} compact /> : '—'}
                      </div>
                      <div className="points">{entry.champion ? '+10' : '—'}</div>
                    </div>
                    <div className="prediction-row">
                      <div className="prediction-label">Artilheiro</div>
                      <div className="prediction-value">
                        {entry.scorer ? (
                          <span className="player-team-inline">
                            <span>{entry.scorer.label}</span>
                            {entry.scorer.teamName && <TeamBadge name={entry.scorer.teamName} flag={entry.scorer.teamFlag} code={entry.scorer.teamCode} compact />}
                          </span>
                        ) : '—'}
                      </div>
                      <div className="points">{entry.scorer ? '+15' : '—'}</div>
                    </div>
                    <div className="compare-strip">
                      <div className="mini-stat"><div className="mini-num">—</div><div className="mini-label">exatos</div></div>
                      <div className="mini-stat"><div className="mini-num">—</div><div className="mini-label">Brasil</div></div>
                      <div className="mini-stat"><div className="mini-num">—%</div><div className="mini-label">igual a você</div></div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
          <div className="card">
            <div className="card-header"><div><div className="card-title">Insights</div><div className="card-subtitle">Comparativo geral</div></div></div>
            <div className="card-body">
              <div className="insight-list">
                <div className="insight"><div className="insight-icon">🇧🇷</div><div><div className="insight-title">Campeão mais escolhido</div><div className="insight-text">Disponível quando o backend expuser agregações do Explore.</div></div></div>
                <div className="insight"><div className="insight-icon">⚽</div><div><div className="insight-title">Artilheiro favorito</div><div className="insight-text">A seleção mais votada aparecerá aqui após os dados.</div></div></div>
                <div className="insight"><div className="insight-icon">≠</div><div><div className="insight-title">Participante mais diferente</div><div className="insight-text">Menor similaridade com seus palpites.</div></div></div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </>
  );
}
