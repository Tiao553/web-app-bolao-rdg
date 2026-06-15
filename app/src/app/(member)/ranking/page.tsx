import type { RankingContract } from '../../../lib/contracts';
import { fetchBackendData } from '../../../lib/session';

export default async function RankingPage() {
  const { data } = await fetchBackendData<RankingContract>('/api/member/ranking');
  const rows = data?.rows ?? [];
  const myRank = data?.currentUserRank;
  const breakdown = data?.currentUserBreakdown;
  const podium = rows.slice(0, 3);

  const maxPts = rows[0]?.totalPoints ?? 200;
  const barPct = (n: number, max = maxPts) => Math.min(100, max > 0 ? (n / max) * 100 : 0);

  return (
    <>
      <section className="hero">
        <div className="hero-content">
          <div>
            <div className="eyebrow"><span className="dot" />Apenas usuários aprovados</div>
            <h1>Ranking geral do <span>bolão</span>.</h1>
            <p>Classificação atualizada com pontos totais, critérios de desempate e movimentação da última rodada.</p>
          </div>
          <div className="deadline-card" style={{ minWidth: 200 }}>
            <div className="deadline-label">Sua posição</div>
            <div style={{ fontSize: 48, fontWeight: 900, color: 'var(--or)', letterSpacing: '-.04em', lineHeight: 1, margin: '10px 0 6px' }}>{myRank ?? '—'}<span style={{ fontSize: 20 }}>º</span></div>
            <div className="pill ok" style={{ width: 'fit-content' }}><span className="dot" />no ranking</div>
          </div>
        </div>
      </section>

      {/* Pódio */}
      {podium.length > 0 && (
        <div className="card">
          <div className="card-header">
            <div><div className="card-title">Classificação geral</div><div className="card-subtitle">Pontos totais e critérios de desempate</div></div>
            <div className="pill ok"><span className="dot" />atualizado</div>
          </div>
          <div className="card-body">
            <div className="podium">
              {podium[1] && (
                <div className="podium-card second">
                  <div className="podium-pos">#2</div>
                  <div className="podium-avatar">{podium[1].fullName.split(' ').map((p: string) => p[0]).slice(0,2).join('')}</div>
                  <div className="podium-name">{podium[1].fullName.split(' ')[0]}</div>
                  <div className="podium-points">{podium[1].totalPoints}</div>
                  <div className="podium-meta">{podium[1].matchPoints} partidas · {podium[1].bonusPoints} bônus</div>
                </div>
              )}
              {podium[0] && (
                <div className="podium-card first">
                  <div className="podium-pos">#1</div>
                  <div className="podium-avatar">{podium[0].fullName.split(' ').map((p: string) => p[0]).slice(0,2).join('')}</div>
                  <div className="podium-name">{podium[0].fullName.split(' ')[0]}</div>
                  <div className="podium-points">{podium[0].totalPoints}</div>
                  <div className="podium-meta">{podium[0].matchPoints} partidas · {podium[0].bonusPoints} bônus</div>
                </div>
              )}
              {podium[2] && (
                <div className="podium-card third">
                  <div className="podium-pos">#3</div>
                  <div className="podium-avatar">{podium[2].fullName.split(' ').map((p: string) => p[0]).slice(0,2).join('')}</div>
                  <div className="podium-name">{podium[2].fullName.split(' ')[0]}</div>
                  <div className="podium-points">{podium[2].totalPoints}</div>
                  <div className="podium-meta">{podium[2].matchPoints} partidas · {podium[2].bonusPoints} bônus</div>
                </div>
              )}
            </div>

            {/* Tabela */}
            <div className="ranking-table">
              <div className="rank-row header">
                <div className="th">Pos</div><div />
                <div className="th">Participante</div>
                <div className="th hide-sm">Jogos</div>
                <div className="th hide-sm">Exatos</div>
                <div className="th hide-md">Brasil</div>
                <div className="th hide-md">Camp.</div>
                <div className="th">Total</div>
              </div>
              {rows.map(row => (
                <div key={row.userId} className={`rank-row${row.rank === 1 ? ' top1' : ''}${row.rank === myRank ? ' me' : ''}`}>
                  <div className="rank-pos">{row.rank}</div>
                  <div className="mini-avatar">{row.fullName.split(' ').map((p: string) => p[0]).slice(0,2).join('')}</div>
                  <div><div className="rank-name">{row.fullName}{row.rank === myRank ? ' (você)' : ''}</div></div>
                  <div className="metric hide-sm">{row.matchPoints}</div>
                  <div className="metric good hide-sm">—</div>
                  <div className="metric hide-md">—</div>
                  <div className="metric gold hide-md">{row.bonusPoints}</div>
                  <div className="metric total">{row.totalPoints}</div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      <div className="grid-2">
        {/* Breakdown */}
        <div className="card">
          <div className="card-header"><div><div className="card-title">Seus pontos</div><div className="card-subtitle">Breakdown geral</div></div></div>
          <div className="card-body">
            {breakdown ? (
              <div className="ranking-breakdown">
                <div className="ranking-total">
                  <div className="ranking-total-label">Pontuação total</div>
                  <div className="ranking-total-value">{breakdown.totalPoints}</div>
                  <div className="ranking-total-meta">{breakdown.matchPoints} pontos em jogos · {breakdown.bonusPoints} em bônus</div>
                </div>
                <div className="bar-list">
                  <div className="bar-row"><div className="bar-label">Exatos</div><div className="bar-track"><div className="bar-fill" style={{ width: `${barPct(breakdown.exactPoints, breakdown.totalPoints)}%` }} /></div><div className="bar-value">{breakdown.exactPoints}</div></div>
                  <div className="bar-row"><div className="bar-label">Resultado</div><div className="bar-track"><div className="bar-fill" style={{ width: `${barPct(breakdown.resultPoints, breakdown.totalPoints)}%` }} /></div><div className="bar-value">{breakdown.resultPoints}</div></div>
                  <div className="bar-row"><div className="bar-label">Brasil ×2</div><div className="bar-track"><div className="bar-fill" style={{ width: `${barPct(breakdown.brazilPoints, breakdown.totalPoints)}%` }} /></div><div className="bar-value">{breakdown.brazilPoints}</div></div>
                  <div className="bar-row"><div className="bar-label">Campeão</div><div className="bar-track"><div className="bar-fill" style={{ width: `${barPct(breakdown.championPoints, breakdown.totalPoints)}%` }} /></div><div className="bar-value">{breakdown.championPoints}</div></div>
                  <div className="bar-row"><div className="bar-label">Artilheiro</div><div className="bar-track"><div className="bar-fill" style={{ width: `${barPct(breakdown.topScorerPoints, breakdown.totalPoints)}%` }} /></div><div className="bar-value">{breakdown.topScorerPoints}</div></div>
                </div>
              </div>
            ) : <div style={{ fontSize: 13, color: 'var(--tx3)' }}>Dados indisponíveis.</div>}
          </div>
        </div>

        {/* Desempate */}
        <div className="card">
          <div className="card-header"><div><div className="card-title">Desempate</div><div className="card-subtitle">Ordem aplicada</div></div></div>
          <div className="card-body">
            <div className="rules-list">
              <div className="rule-row"><div className="rule-icon">1</div><div><div className="rule-title">Placares exatos</div><div className="rule-text">Quem acertar mais placares exatos fica à frente.</div></div></div>
              <div className="rule-row"><div className="rule-icon">2</div><div><div className="rule-title">Vencedor ou empate</div><div className="rule-text">Mais acertos de resultado sem placar exato.</div></div></div>
              <div className="rule-row"><div className="rule-icon">3</div><div><div className="rule-title">Jogos do Brasil</div><div className="rule-text">Maior pontuação em partidas com multiplicador.</div></div></div>
              <div className="rule-row"><div className="rule-icon">4</div><div><div className="rule-title">Mata-mata</div><div className="rule-text">Maior pontuação nas fases eliminatórias.</div></div></div>
            </div>
          </div>
        </div>
      </div>
    </>
  );
}
