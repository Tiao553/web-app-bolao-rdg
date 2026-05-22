'use client';
import { useState } from 'react';
import { TeamBadge } from '../../../components/ui/team-badge';
import type { PhaseRoundContract, PhaseMatchContract } from '../../../lib/contracts';

function fmtMatchDate(iso: string) {
  const d = new Date(iso);
  return (
    d.toLocaleDateString('pt-BR', { day: '2-digit', month: 'short' }).replace('.', '') +
    ' · ' +
    d.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' })
  );
}

function predictedResult(m: PhaseMatchContract): string {
  const h = m.predictedHomeGoals;
  const a = m.predictedAwayGoals;
  if (h === null || a === null) return 'pendente';
  if (h > a) return `${m.homeTeam} vence`;
  if (a > h) return `${m.awayTeam} vence`;
  return 'Empate';
}

function filled(m: PhaseMatchContract) {
  return m.predictedHomeGoals !== null && m.predictedAwayGoals !== null;
}

function MatchCard({ m, locked }: { m: PhaseMatchContract; locked: boolean }) {
  const tbd = m.homeTeam === 'TBD' || m.awayTeam === 'TBD';
  const isFilled = filled(m);
  const result = predictedResult(m);

  return (
    <div className={`pp-match-card${tbd ? ' pp-tbd' : ''}`}>
      {/* Card top */}
      <div className="pp-card-top">
        <span className="pp-match-date">{fmtMatchDate(m.startsAt)}</span>
        {m.involvesBrazil
          ? <span className="pp-badge-brazil">BRASIL ×2</span>
          : m.groupName
            ? <span className="pp-badge-group">GRUPO {m.groupName}</span>
            : null
        }
      </div>

      {/* Teams */}
      <div className="pp-teams">
        <div className="pp-team-row">
          <div className="pp-team-info">
            <div>
              <TeamBadge name={m.homeTeam} flag={m.homeFlag} code={m.homeCode} />
              <div className="pp-team-role">Mandante</div>
            </div>
          </div>
          <input
            name={`home_${m.id}`}
            className="pp-score-input"
            type="number"
            min="0"
            max="99"
            defaultValue={m.predictedHomeGoals ?? ''}
            disabled={locked || tbd}
            placeholder="—"
          />
        </div>
        <div className="pp-team-row">
          <div className="pp-team-info">
            <div>
              <TeamBadge name={m.awayTeam} flag={m.awayFlag} code={m.awayCode} />
              <div className="pp-team-role">Visitante</div>
            </div>
          </div>
          <input
            name={`away_${m.id}`}
            className="pp-score-input"
            type="number"
            min="0"
            max="99"
            defaultValue={m.predictedAwayGoals ?? ''}
            disabled={locked || tbd}
            placeholder="—"
          />
        </div>
      </div>

      {/* Card footer */}
      <div className="pp-card-footer">
        <span className="pp-result-text">
          Resultado previsto: <strong>{result}</strong>
        </span>
        {!isFilled && !tbd && (
          <span className="pp-status-missing">● FALTA PREENCHER</span>
        )}
        {isFilled && m.involvesBrazil && (
          <span className="pp-status-mult">MULTIPLICADOR ×2</span>
        )}
        {isFilled && !m.involvesBrazil && (
          <span className="pp-status-ok">● PREENCHIDO</span>
        )}
      </div>
    </div>
  );
}

export function PhasePredictionsClient({ rounds }: { rounds: PhaseRoundContract[] }) {
  const [activeKey, setActiveKey] = useState(
    rounds.find(r => !r.locked && r.matches.length > 0)?.key ?? rounds[0]?.key ?? 'round1'
  );

  const activeRound = rounds.find(r => r.key === activeKey);
  const matches = activeRound?.matches ?? [];
  const locked = activeRound?.locked ?? true;

  const filledCount = matches.filter(m => filled(m)).length;
  const pendingCount = matches.length - filledCount;

  return (
    <div className="pp-layout">
      {/* ── Left sidebar ── */}
      <aside className="pp-sidebar-left">
        <div className="pp-sidebar-header">
          <div className="pp-sidebar-title">Rodadas</div>
          <div className="pp-sidebar-eyebrow">NAVEGAÇÃO</div>
        </div>

        <nav className="pp-nav">
          {rounds.map(r => {
            const hasMatches = r.matches.length > 0;
            const rFilled = r.matches.filter(m => filled(m)).length;
            const isActive = activeKey === r.key;

            return (
              <button
                key={r.key}
                type="button"
                className={`pp-nav-item${isActive ? ' active' : ''}${!hasMatches ? ' disabled' : ''}`}
                disabled={!hasMatches}
                onClick={() => hasMatches && setActiveKey(r.key)}
              >
                <div className="pp-nav-item-content">
                  <div>
                    <div className="pp-nav-label">{r.label}</div>
                    <div className="pp-nav-sub">
                      {!hasMatches ? 'Aguardando chaveamento' : r.locked ? 'bloqueado' : 'aberto'}
                    </div>
                  </div>
                  {hasMatches && (
                    <div className={`pp-nav-count${isActive ? ' active' : ''}`}>
                      {rFilled}/{r.matches.length}
                    </div>
                  )}
                </div>
              </button>
            );
          })}
        </nav>

        {/* Resumo Geral */}
        <div className="pp-resumo">
          <div className="pp-resumo-title">RESUMO GERAL</div>
          {rounds.filter(r => r.matches.length > 0).map(r => {
            const rFilled = r.matches.filter(m => filled(m)).length;
            const pct = r.matches.length > 0 ? (rFilled / r.matches.length) * 100 : 0;
            return (
              <div key={r.key} className="pp-resumo-row">
                <div className="pp-resumo-label">{r.label}</div>
                <div className="pp-resumo-bar-track">
                  <div className="pp-resumo-bar-fill" style={{ width: `${pct}%` }} />
                </div>
                <div className="pp-resumo-count">{rFilled}/{r.matches.length}</div>
              </div>
            );
          })}
        </div>
      </aside>

      {/* ── Center ── */}
      <main className="pp-main">
        <div className="pp-main-header">
          <div>
            <div className="pp-main-title">{activeRound?.label ?? '—'}</div>
            <div className="pp-main-sub">
              {matches.length} PARTIDAS · {locked ? 'BLOQUEADO' : 'PLACARES EDITÁVEIS'}
            </div>
          </div>
          <div className={`pill ${locked ? 'warn' : 'ok'}`}>
            <span className="dot" />{locked ? 'Bloqueado' : 'Aberto'}
          </div>
        </div>

        {matches.length === 0 ? (
          <div className="pp-empty">Partidas desta fase ainda não foram definidas.</div>
        ) : (
          <form id="phase-form" action="/api/member/predictions/match" method="POST">
            <div className="pp-match-grid">
              {matches.map(m => (
                <MatchCard key={m.id} m={m} locked={locked} />
              ))}
            </div>
          </form>
        )}
      </main>

      {/* ── Right sidebar ── */}
      <aside className="pp-sidebar-right">
        {/* Rules */}
        <div className="pp-right-card">
          <div className="pp-right-card-title">Regras da fase</div>
          <div className="pp-right-card-sub">PONTUAÇÃO POR PARTIDA</div>

          <div className="pp-info-box">
            <div className="pp-info-box-title">
              {locked ? '🔒 Palpites bloqueados' : 'Palpites editáveis'}
            </div>
            <div className="pp-info-box-text">
              {locked
                ? 'Esta fase foi bloqueada. Você pode visualizar seus palpites.'
                : 'Você pode alterar os placares até o horário de fechamento configurado pelo administrador.'}
            </div>
          </div>

          <div className="pp-rules-list">
            <div className="pp-rule-row">
              <span className="pp-rule-label">Placar exato</span>
              <span className="pp-rule-pts">3 pts</span>
            </div>
            <div className="pp-rule-row">
              <span className="pp-rule-label">Vencedor ou empate</span>
              <span className="pp-rule-pts">1 pt</span>
            </div>
            <div className="pp-rule-row">
              <span className="pp-rule-label">Erro do resultado</span>
              <span className="pp-rule-pts zero">0 pts</span>
            </div>
            <div className="pp-rule-row">
              <span className="pp-rule-label">Jogo do Brasil</span>
              <span className="pp-rule-pts mult">×2</span>
            </div>
          </div>
        </div>

        {/* Save */}
        {!locked && matches.length > 0 && (
          <div className="pp-right-card">
            <div className="pp-right-card-title">Salvar alterações</div>
            <div className="pp-save-meta">
              {matches.length} partidas nesta visualização.{' '}
              {filledCount} preenchida{filledCount !== 1 ? 's' : ''} e {pendingCount} pendente{pendingCount !== 1 ? 's' : ''}.
            </div>
            <button type="submit" form="phase-form" className="btn-primary full" style={{ marginTop: 12 }} suppressHydrationWarning>
              Salvar {activeRound?.label} →
            </button>
            <button type="button" className="pp-clear-btn" style={{ marginTop: 8 }}>
              Limpar pendentes
            </button>
          </div>
        )}

        {/* Explore */}
        <div className="pp-right-card">
          <div className="pp-right-card-title">Explore</div>
          <div className="pp-right-card-sub">
            {activeRound?.exploreOpen ? 'LIBERADO' : 'BLOQUEADO POR HORÁRIO'}
          </div>
          <div className="pp-explore-rows">
            <div className="pp-explore-row">
              <span className="pp-explore-label">Seus palpites</span>
              <span className="pp-explore-val ok">visíveis</span>
            </div>
            <div className="pp-explore-row">
              <span className="pp-explore-label">Palpites dos outros</span>
              <span className={`pp-explore-val ${activeRound?.exploreOpen ? 'ok' : 'blocked'}`}>
                {activeRound?.exploreOpen ? 'visíveis' : 'bloqueados'}
              </span>
            </div>
            <div className="pp-explore-row">
              <span className="pp-explore-label">Liberação</span>
              <span className="pp-explore-val muted">
                {activeRound?.exploreOpen ? 'disponível' : 'após fechamento'}
              </span>
            </div>
          </div>
        </div>
      </aside>
    </div>
  );
}
