import type { AdminSettingsContract } from '../../../../lib/contracts';
import { fetchBackendData } from '../../../../lib/session';
import { getServerCsrfToken } from '../../../../lib/security';

const ROUND_KEYS = ['initial_predictions', 'round1', 'round2', 'round3', 'roundOf32', 'roundOf16', 'quarterFinal', 'semiFinal', 'final'];

export default async function AdminSettingsPage({ searchParams }: { searchParams?: Promise<Record<string, string | string[] | undefined>> }) {
  const params = searchParams ? await searchParams : {};
  const csrfToken = await getServerCsrfToken();
  const saved = params.saved === '1';
  const saveError = typeof params.error === 'string' ? params.error : undefined;
  const { data } = await fetchBackendData<AdminSettingsContract>('/api/admin/settings');
  const w = data?.competitionWindow;
  const sc = data?.scoring;
  const phaseConfigs = data?.phaseConfigs ?? [];
  const forceLockedPhases = data?.forceLockedPhases ?? 0;

  function isRoundLocked(key: string): boolean {
    const config = phaseConfigs.find((phase) => phase.phaseKey === key);
    if (config) return config.forceLocked;
    const idx = ROUND_KEYS.indexOf(key);
    if (idx < 0) return false;
    return ((forceLockedPhases >> idx) & 1) === 1;
  }

  const phaseRows = (phaseConfigs.length > 0
    ? phaseConfigs
    : [
        { phaseKey: 'initial_predictions', label: 'Palpites iniciais', forceLocked: isRoundLocked('initial_predictions') },
        { phaseKey: 'round1', label: 'Grupos · Rodada 1', forceLocked: isRoundLocked('round1') },
        { phaseKey: 'round2', label: 'Grupos · Rodada 2', forceLocked: isRoundLocked('round2') },
        { phaseKey: 'round3', label: 'Grupos · Rodada 3', forceLocked: isRoundLocked('round3') },
        { phaseKey: 'roundOf32', label: '16 avos', forceLocked: isRoundLocked('roundOf32') },
        { phaseKey: 'roundOf16', label: 'Oitavas', forceLocked: isRoundLocked('roundOf16') },
        { phaseKey: 'quarterFinal', label: 'Quartas', forceLocked: isRoundLocked('quarterFinal') },
        { phaseKey: 'semiFinal', label: 'Semifinal', forceLocked: isRoundLocked('semiFinal') },
        { phaseKey: 'final', label: 'Final', forceLocked: isRoundLocked('final') },
      ]) as Array<{ phaseKey: string; label: string; forceLocked: boolean }>;

  return (
    <>
      {saved && <div className="modal-success" style={{ margin: '0 0 16px', padding: '10px 16px', borderRadius: 10, fontSize: 13 }}>Configurações salvas com sucesso.</div>}
      {saveError && <div className="modal-error" style={{ margin: '0 0 16px', padding: '10px 16px', borderRadius: 10, fontSize: 13 }}>Erro ao salvar: {saveError === 'missing_dates' ? 'Preencha os campos de data.' : 'Tente novamente.'}</div>}

      {/* Hero */}
      <section className="hero">
        <div className="hero-content">
          <div>
            <div className="eyebrow"><span className="dot" />Regras e governança</div>
            <h1>Defina prazos, bloqueios e <span>pontuação</span>.</h1>
            <p>Configurações por fase controlam o fechamento dos palpites, a liberação cumulativa do Explore, os pesos da pontuação, a regra Brasil ×2 e as permissões administrativas.</p>
          </div>
          <div className="lock-card">
            <div className="lock-title">{w?.is_active ? 'Competição ativa' : 'Inativa'}</div>
            <div className="lock-meta">
              {w?.explore_release_at ? `Explore após ${new Date(w.explore_release_at).toLocaleDateString('pt-BR')}` : 'Explore não configurado'}
            </div>
          </div>
        </div>
      </section>

      <div className="grid-2">
        {/* Main settings summary */}
        <div className="card">
          <div className="card-header">
            <div><div className="card-title">Configurações por fase</div><div className="card-subtitle">Fonte de verdade: competition_phase_configs</div></div>
            <div className="pill orange"><span className="dot" />{phaseConfigs.length} fases</div>
          </div>
          <div className="card-body">
            <div className="toggle-list">
              {phaseConfigs.map((phase) => (
                <div key={phase.phaseKey} className="toggle-row" style={{ gap: 10, alignItems: 'flex-start' }}>
                  <div style={{ flex: 1 }}>
                    <div className="toggle-title">{phase.label}</div>
                    <div className="toggle-text">
                      {phase.lockAt ? `Lock: ${new Date(phase.lockAt).toLocaleString('pt-BR')}` : 'Lock não configurado'} ·{' '}
                      {phase.exploreAt ? `Explore: ${new Date(phase.exploreAt).toLocaleString('pt-BR')}` : 'Explore não configurado'}
                    </div>
                  </div>
                  <div className={`pill ${phase.forceLocked ? 'warn' : 'ok'}`} style={{ fontSize: 11, whiteSpace: 'nowrap' }}>
                    <span className="dot" />{phase.forceLocked ? 'Travado' : 'Automático'}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Right column */}
        <div className="side-list">
          {/* Toggles */}
          <div className="card">
            <div className="card-header"><div><div className="card-title">Chaves rápidas</div><div className="card-subtitle">Ativação de regras</div></div></div>
            <div className="card-body">
              <div className="toggle-list">
                <div className="toggle-row">
                  <div>
                    <div className="toggle-title">Brasil ×{sc?.brazil_multiplier ?? 2}</div>
                    <div className="toggle-text">Dobrar pontos em jogos do Brasil.</div>
                  </div>
                  <div className={`switch ${(sc?.brazil_multiplier ?? 2) > 1 ? 'on' : ''}`} />
                </div>
                <div className="toggle-row">
                  <div>
                    <div className="toggle-title">Explore automático</div>
                    <div className="toggle-text">Liberar após fechamento.</div>
                  </div>
                  <div className="switch on" />
                </div>
                <div className="toggle-row">
                  <div>
                    <div className="toggle-title">Aprovação manual</div>
                    <div className="toggle-text">Admin precisa liberar usuários.</div>
                  </div>
                  <div className="switch on" />
                </div>
              </div>
            </div>
          </div>

          {/* Force lock por rodada */}
          <div className="card">
            <div className="card-header"><div><div className="card-title">Controle de bloqueio</div><div className="card-subtitle">Force lock / unlock por fase</div></div></div>
            <div className="card-body">
              <div className="toggle-list">
                {phaseRows.map(r => {
                  const locked = r.forceLocked;
                  return (
                    <div key={r.phaseKey} className="toggle-row" style={{ gap: 10 }}>
                      <div style={{ flex: 1 }}>
                        <div className="toggle-title">{r.label}</div>
                        <div className="toggle-text">Bloqueio automático 30 min antes do 1º jogo</div>
                      </div>
                      <div className={`pill ${locked ? 'warn' : 'ok'}`} style={{ fontSize: 11, whiteSpace: 'nowrap' }}>
                        <span className="dot" />{locked ? 'Travado' : 'Aberto'}
                      </div>
                      <form action="/api/admin/phase-lock" method="POST">
                        <input type="hidden" name="csrf_token" value={csrfToken} />
                        <input type="hidden" name="roundKey" value={r.phaseKey} />
                        <input type="hidden" name="locked" value="true" />
                        <button type="submit" className="btn-danger" style={{ height: 30, fontSize: 11, padding: '0 10px' }}>Travar</button>
                      </form>
                      <form action="/api/admin/phase-lock" method="POST">
                        <input type="hidden" name="csrf_token" value={csrfToken} />
                        <input type="hidden" name="roundKey" value={r.phaseKey} />
                        <input type="hidden" name="locked" value="false" />
                        <button type="submit" className="btn-ok" style={{ height: 30, fontSize: 11, padding: '0 10px' }}>Abrir</button>
                      </form>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>

          {/* Danger zone */}
          <div className="danger-zone">
            <div className="danger-zone-title">Zona crítica</div>
            <div className="danger-zone-text">Alterações nessas regras podem mudar ranking e pontuações já calculadas.</div>
            <button className="btn-danger full">Bloquear alterações</button>
          </div>

          {/* Pontuação visual */}
          <div className="card">
            <div className="card-header"><div><div className="card-title">Pontuação atual</div><div className="card-subtitle">Resumo funcional</div></div></div>
            <div className="card-body">
              <div className="bar-list">
                <div className="bar-row"><div className="bar-label">Placar exato</div><div className="bar-track"><div className="bar-fill" style={{ width: `${Math.min(100, (sc?.exact_points ?? 0) * 10)}%` }} /></div><div className="bar-value">{sc?.exact_points ?? 0}pts</div></div>
                <div className="bar-row"><div className="bar-label">Resultado</div><div className="bar-track"><div className="bar-fill" style={{ width: `${Math.min(100, (sc?.result_points ?? 0) * 10)}%` }} /></div><div className="bar-value">{sc?.result_points ?? 0}pts</div></div>
                <div className="bar-row"><div className="bar-label">Mult. Brasil</div><div className="bar-track"><div className="bar-fill" style={{ width: `${Math.min(100, (sc?.brazil_multiplier ?? 1) * 50)}%` }} /></div><div className="bar-value">×{sc?.brazil_multiplier ?? 1}</div></div>
                <div className="bar-row"><div className="bar-label">Campeão</div><div className="bar-track"><div className="bar-fill" style={{ width: `${Math.min(100, (sc?.champion_points ?? 0) * 10)}%` }} /></div><div className="bar-value">{sc?.champion_points ?? 0}pts</div></div>
                <div className="bar-row"><div className="bar-label">Artilheiro</div><div className="bar-track"><div className="bar-fill" style={{ width: `${Math.min(100, (sc?.top_scorer_points ?? 0) * 10)}%` }} /></div><div className="bar-value">{sc?.top_scorer_points ?? 0}pts</div></div>
              </div>
            </div>
          </div>
        </div>

        {/* Rules applied */}
        <div className="card" style={{ gridColumn: 'span 2' }}>
          <div className="card-header"><div><div className="card-title">Regras aplicadas</div><div className="card-subtitle">Resumo funcional</div></div></div>
          <div className="card-body">
            <div className="rule-card-list" style={{ gridTemplateColumns: 'repeat(2, 1fr)', display: 'grid', gap: 10 }}>
              {[
                { icon: '×2', title: 'Jogos do Brasil', text: 'Se o usuário acertar placar ou resultado em jogo do Brasil, os pontos são dobrados.' },
                { icon: '⚽', title: 'Artilheiro com assistências', text: 'Em empate de gols entre 2 ou 3 jogadores, assistências definem o vencedor para pontuação.' },
                { icon: '🔒', title: 'Palpites imutáveis', text: 'Após o horário de fechamento, participantes não podem alterar palpites e o Explore é liberado.' },
                { icon: '👥', title: 'Acesso governado', text: 'Todo mundo pode se cadastrar, mas somente aprovados entram no bolão.' },
              ].map(r => (
                <div key={r.title} className="rule-card-admin">
                  <div className="rule-icon-admin">{r.icon}</div>
                  <div>
                    <div className="rule-card-title">{r.title}</div>
                    <div className="rule-card-text">{r.text}</div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </>
  );
}
