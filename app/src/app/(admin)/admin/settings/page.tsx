import type { AdminSettingsContract } from '../../../../lib/contracts';
import { fetchBackendData } from '../../../../lib/session';

export default async function AdminSettingsPage() {
  const { data } = await fetchBackendData<AdminSettingsContract>('/api/admin/settings');
  const w = data?.competitionWindow;
  const sc = data?.scoring;

  const fmt = (v: string | undefined) =>
    v ? new Date(v).toISOString().slice(0, 16) : '';

  return (
    <>
      {/* Hero */}
      <section className="hero">
        <div className="hero-content">
          <div>
            <div className="eyebrow"><span className="dot" />Regras e governança</div>
            <h1>Defina prazos, bloqueios e <span>pontuação</span>.</h1>
            <p>Configurações globais controlam horário de fechamento dos palpites, liberação do Explore, pesos da pontuação, regra Brasil ×2 e permissões administrativas.</p>
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
        {/* Main settings form */}
        <div className="card">
          <div className="card-header">
            <div><div className="card-title">Configurações principais</div><div className="card-subtitle">Prazos, bloqueios e regras do bolão</div></div>
            <div className="pill orange"><span className="dot" />editável</div>
          </div>
          <div className="card-body">
            <form action="/api/admin/settings/window" method="POST">
              <div className="settings-grid">
                <div className="field-admin full">
                  <div className="field-label-admin">Nome da competição</div>
                  <input name="name" type="text" className="admin-input" defaultValue={w?.name ?? ''} />
                </div>
                <div className="field-admin">
                  <div className="field-label-admin">Fechamento dos palpites</div>
                  <input name="prediction_close_at" type="datetime-local" className="admin-input" defaultValue={fmt(w?.prediction_close_at)} />
                </div>
                <div className="field-admin">
                  <div className="field-label-admin">Liberação do Explore</div>
                  <input name="explore_release_at" type="datetime-local" className="admin-input" defaultValue={fmt(w?.explore_release_at)} />
                </div>
                <div className="field-admin">
                  <div className="field-label-admin">Placar exato</div>
                  <input type="number" className="admin-input" defaultValue={sc?.exact_points ?? 5} min={0} />
                </div>
                <div className="field-admin">
                  <div className="field-label-admin">Resultado correto</div>
                  <input type="number" className="admin-input" defaultValue={sc?.result_points ?? 3} min={0} />
                </div>
                <div className="field-admin">
                  <div className="field-label-admin">Pontos campeão</div>
                  <input type="number" className="admin-input" defaultValue={sc?.champion_points ?? 10} min={0} />
                </div>
                <div className="field-admin">
                  <div className="field-label-admin">Pontos artilheiro</div>
                  <input type="number" className="admin-input" defaultValue={sc?.top_scorer_points ?? 15} min={0} />
                </div>
                <div className="field-admin full">
                  <div className="field-label-admin">Mensagem de bloqueio</div>
                  <input type="text" className="admin-input" defaultValue="Os palpites foram bloqueados pelo horário oficial definido pelo administrador." />
                </div>
              </div>
              <button type="submit" className="btn-primary full" style={{ marginTop: 18 }}>Salvar configurações →</button>
            </form>
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
            <div className="card-header"><div><div className="card-title">Controle de bloqueio</div><div className="card-subtitle">Force lock / unlock por rodada</div></div></div>
            <div className="card-body">
              <div className="toggle-list">
                {[
                  { key: 'round1', label: 'Grupos · Rodada 1' },
                  { key: 'round2', label: 'Grupos · Rodada 2' },
                  { key: 'round3', label: 'Grupos · Rodada 3' },
                  { key: 'roundOf32', label: '16 avos' },
                  { key: 'roundOf16', label: 'Oitavas' },
                  { key: 'quarterFinal', label: 'Quartas' },
                  { key: 'semiFinal', label: 'Semifinal' },
                  { key: 'final', label: 'Final' },
                ].map(r => (
                  <div key={r.key} className="toggle-row" style={{ gap: 12 }}>
                    <div style={{ flex: 1 }}>
                      <div className="toggle-title">{r.label}</div>
                      <div className="toggle-text">Bloqueio automático 1h antes do 1º jogo</div>
                    </div>
                    <form action="/api/admin/phase-lock" method="POST" style={{ display: 'flex', gap: 6 }}>
                      <input type="hidden" name="roundKey" value={r.key} />
                      <input type="hidden" name="locked" value="true" />
                      <button type="submit" className="btn-danger" style={{ height: 30, fontSize: 11, padding: '0 10px' }}>🔒 Travar</button>
                    </form>
                    <form action="/api/admin/phase-lock" method="POST" style={{ display: 'flex', gap: 6 }}>
                      <input type="hidden" name="roundKey" value={r.key} />
                      <input type="hidden" name="locked" value="false" />
                      <button type="submit" className="btn-ok" style={{ height: 30, fontSize: 11, padding: '0 10px' }}>🔓 Abrir</button>
                    </form>
                  </div>
                ))}
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
