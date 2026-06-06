import Link from 'next/link';
import { TeamBadge } from '../../../components/ui/team-badge';
import { Countdown } from '../../../components/ui/countdown';
import { ScoreGauge } from '../../../components/ui/score-gauge';
import type { MemberDashboardContract, RankingContract } from '../../../lib/contracts';
import { fetchBackendData, fetchAppSession } from '../../../lib/session';

function initials(name: string) {
  return name.split(' ').slice(0, 2).map(w => w[0]).join('').toUpperCase();
}

function fmtMatchDate(iso: string) {
  const d = new Date(iso);
  const options = { timeZone: 'America/Sao_Paulo' } as const;
  return d.toLocaleDateString('pt-BR', { day: '2-digit', month: 'short', ...options }) + ' · ' +
    d.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit', ...options });
}

export default async function DashboardPage() {
  const [{ data }, { data: rankingData }, session] = await Promise.all([
    fetchBackendData<MemberDashboardContract>('/api/member/dashboard'),
    fetchBackendData<RankingContract>('/api/member/ranking'),
    fetchAppSession(),
  ]);

  const closeAt = data?.nextLockAt ?? null;
  const pts = data?.totalPoints ?? 0;
  const rank = data?.rankingPosition;
  const nextMatches = data?.nextMatches ?? [];
  const rankRows = (rankingData?.rows ?? []).slice(0, 4);
  const myRank = rankingData?.currentUserRank;
  const exploreOpen = Boolean(
    session.now && session.competition.exploreReleaseAt && Date.parse(session.now) >= Date.parse(session.competition.exploreReleaseAt)
  );

  return (
    <>
      {/* ── Hero ── */}
      <section className="hero">
        <div className="hero-content">
          <div>
            <div className="eyebrow"><span className="dot" />Copa do Mundo 2026</div>
            <h1>Bem-vindo de volta, <span>{data?.user.name?.split(' ')[0] ?? 'Participante'}</span>.</h1>
            <p>Acompanhe sua pontuação, veja as fases abertas, registre palpites antes do fechamento e compare sua posição no ranking do bolão.</p>
          </div>
          {closeAt && (
            <Countdown closeAt={closeAt} note="Depois desse horário, seus palpites não poderão mais ser alterados." />
          )}
        </div>
      </section>

      {/* ── Metric cards ── */}
      <div className="grid-4">
        <div className="metric-card"><div className="metric-value">{pts}</div><div className="metric-note">pontos totais</div></div>
        <div className="metric-card"><div className="metric-value neutral">{data?.savedMatchPredictions ?? 0}</div><div className="metric-note">palpites por partida</div></div>
        <div className="metric-card"><div className="metric-value neutral">{data?.savedBonusPredictions ?? 0}</div><div className="metric-note">palpites iniciais</div></div>
        <div className="metric-card"><div className="metric-value">{rank ?? '—'}</div><div className="metric-note">posição no ranking</div></div>
      </div>

      {/* ── Score + Breakdown ── */}
      <div className="grid-2">
        <div className="card">
          <div className="card-header">
            <div><div className="card-title">Sua pontuação</div><div className="card-subtitle">Total acumulado</div></div>
          </div>
          <div className="card-body">
            <ScoreGauge points={pts} max={200} rank={rank} />
          </div>
        </div>

        <div className="card">
          <div className="card-header">
            <div><div className="card-title">Breakdown</div><div className="card-subtitle">Origem dos pontos</div></div>
          </div>
          <div className="card-body">
            <div className="bar-list">
              <div className="bar-row"><div className="bar-label">Placar exato</div><div className="bar-track"><div className="bar-fill" style={{ width: '0%' }} /></div><div className="bar-value">—</div></div>
              <div className="bar-row"><div className="bar-label">Resultado</div><div className="bar-track"><div className="bar-fill" style={{ width: '0%' }} /></div><div className="bar-value">—</div></div>
              <div className="bar-row"><div className="bar-label">Bônus Brasil</div><div className="bar-track"><div className="bar-fill" style={{ width: '0%' }} /></div><div className="bar-value">—</div></div>
              <div className="bar-row"><div className="bar-label">Campeão</div><div className="bar-track"><div className="bar-fill" style={{ width: '0%' }} /></div><div className="bar-value">—</div></div>
              <div className="bar-row"><div className="bar-label">Artilheiro</div><div className="bar-track"><div className="bar-fill" style={{ width: '0%' }} /></div><div className="bar-value">—</div></div>
            </div>
          </div>
        </div>
      </div>

      {/* ── Mini ranking + Next matches ── */}
      <div className="grid-2">
        <div className="card">
          <div className="card-header">
            <div><div className="card-title">Ranking</div><div className="card-subtitle">Top participantes</div></div>
            <Link href="/ranking" className="ghost-button">Ver todos</Link>
          </div>
          <div className="card-body">
            {rankRows.length === 0 ? (
              <div style={{ fontSize: 13, color: 'var(--tx3)' }}>Nenhum participante ainda.</div>
            ) : (
              <div className="mini-leaderboard">
                {rankRows.map(row => (
                  <div key={row.userId} className={`leader-row${row.rank === 1 ? ' top' : ''}${row.rank === myRank ? ' me' : ''}`}>
                    <div className="pos">{row.rank}</div>
                    <div className="small-avatar">{initials(row.fullName)}</div>
                    <div className="leader-name">{row.fullName.split(' ')[0]}</div>
                    <div className="leader-points">{row.totalPoints}</div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        <div className="card">
          <div className="card-header">
            <div><div className="card-title">Próximos jogos</div><div className="card-subtitle">Palpites abertos</div></div>
            <Link href="/phase-predictions" className="ghost-button">Ver todos</Link>
          </div>
          <div className="card-body">
            {nextMatches.length === 0 ? (
              <div style={{ fontSize: 13, color: 'var(--tx3)' }}>Nenhum jogo agendado.</div>
            ) : (
              <div className="match-list">
                {nextMatches.map(m => (
                  <div key={m.id} className="next-match-row">
                    <div className="next-match-date">{fmtMatchDate(m.startsAt)}</div>
                    <div className="next-teams">
                      <div className="next-team"><TeamBadge name={m.homeTeam} flag={m.homeFlag} iso2={m.homeIso2} code={m.homeCode} compact /></div>
                      <div className="next-versus">vs</div>
                      <div className="next-team"><TeamBadge name={m.awayTeam} flag={m.awayFlag} iso2={m.awayIso2} code={m.awayCode} compact /></div>
                    </div>
                    <div className={`match-badge ${m.involvesBrazil ? 'brazil' : 'open'}`}>
                      <span className="dot" />{m.involvesBrazil ? 'Brasil ×2' : 'Aberto'}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* ── Phases + Quick actions ── */}
      <div className="grid-2">
        <div className="card">
          <div className="card-header">
            <div><div className="card-title">Fases do bolão</div><div className="card-subtitle">Status de preenchimento</div></div>
          </div>
          <div className="card-body">
            <div className="phase-list">
              <div className="phase-row">
                <div><div className="phase-name">Palpites iniciais</div><div className="phase-meta">Campeão e artilheiro</div></div>
                <div className={`phase-status${(data?.savedBonusPredictions ?? 0) >= 2 ? ' open' : ''}`}>{(data?.savedBonusPredictions ?? 0) >= 2 ? 'Concluído' : 'Pendente'}</div>
              </div>
              <div className="phase-row">
                <div><div className="phase-name">Fase de grupos</div><div className="phase-meta">{data?.savedMatchPredictions ?? 0} palpites preenchidos</div></div>
                <div className="phase-status">Aberto</div>
              </div>
              <div className="phase-row">
                <div><div className="phase-name">16 avos de final</div><div className="phase-meta">Aguardando chaveamento oficial</div></div>
                <div className="phase-status">Pendente</div>
              </div>
              <div className="phase-row">
                <div><div className="phase-name">Explore</div><div className="phase-meta">Libera após fechamento</div></div>
                <div className={`phase-status${exploreOpen ? ' open' : ''}`}>{exploreOpen ? 'Aberto' : 'Bloqueado'}</div>
              </div>
            </div>
          </div>
        </div>

        <div className="card">
          <div className="card-header">
            <div><div className="card-title">Ações rápidas</div><div className="card-subtitle">Continue de onde parou</div></div>
          </div>
          <div className="card-body">
            <div className="quick-grid">
              <Link href="/initial-predictions" className="quick-link"><div className="quick-icon">★</div><div><div className="quick-title">Palpites iniciais</div><div className="quick-text">Escolha campeão e artilheiro da Copa.</div></div></Link>
              <Link href="/phase-predictions" className="quick-link"><div className="quick-icon">▦</div><div><div className="quick-title">Palpites por fase</div><div className="quick-text">Preencha placares por grupos e mata-mata.</div></div></Link>
              <Link href="/ranking" className="quick-link"><div className="quick-icon">#</div><div><div className="quick-title">Ranking</div><div className="quick-text">Veja sua posição contra os participantes.</div></div></Link>
              <Link href="/bracket" className="quick-link"><div className="quick-icon">⌁</div><div><div className="quick-title">Chaveamento</div><div className="quick-text">Acompanhe 16 avos, oitavas e final.</div></div></Link>
            </div>
          </div>
        </div>
      </div>
    </>
  );
}
