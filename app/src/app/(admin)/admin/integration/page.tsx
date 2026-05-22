import type { AdminIntegrationContract } from '../../../../lib/contracts';
import { fetchBackendData } from '../../../../lib/session';

export default async function AdminIntegrationPage() {
  const { data } = await fetchBackendData<AdminIntegrationContract>('/api/admin/integration');
  const syncs = data?.lastSyncs ?? [];

  return (
    <>
      {/* Hero */}
      <section className="hero">
        <div className="hero-content">
          <div>
            <div className="eyebrow"><span className="dot" />API-SPORTS Football v3</div>
            <h1>Integração com <span>v3.football.api-sports.io</span>.</h1>
            <p>A integração busca fixtures, teams, standings, events, lineups, players/statistics e resultados oficiais pela API-SPORTS Football v3. O administrador ainda pode corrigir manualmente qualquer divergência.</p>
          </div>
          <div className="connection-card">
            <div className="conn-label">Conexão</div>
            <div className="conn-title">{data?.apiConfigured ? 'API-SPORTS v3 OK' : 'Não configurada'}</div>
            <div className="conn-text">
              {data?.apiConfigured
                ? 'API-SPORTS v3 conectada via v3.football.api-sports.io.'
                : 'Configure a chave API nas variáveis de ambiente.'}
            </div>
          </div>
        </div>
      </section>

      {/* Main grid */}
      <div className="grid-2">
        {/* Config */}
        <div className="card">
          <div className="card-header">
            <div><div className="card-title">Configuração da integração</div><div className="card-subtitle">Fonte oficial e agenda</div></div>
            <div className={`pill ${data?.apiConfigured ? 'ok' : 'warn'}`}><span className="dot" />{data?.apiConfigured ? 'conectado' : 'offline'}</div>
          </div>
          <div className="card-body">
            <div className="config-grid">
              {[
                { label: 'Provider', value: data?.primaryProvider ?? 'API-SPORTS Football API' },
                { label: 'Base URL', value: 'v3.football.api-sports.io' },
                { label: 'Endpoints principais', value: '/fixtures · /teams · /standings · /players' },
                { label: 'Headers', value: 'x-apisports-key · x-rapidapi-host' },
                { label: 'Intervalo de sync', value: 'A cada 30 minutos' },
                { label: 'Fallback', value: data?.fallbackProvider ?? 'Override manual por administrador' },
              ].map(({ label, value }) => (
                <div key={label} className="field-admin">
                  <div className="field-label-admin">{label}</div>
                  <div className="field-value-admin">{value}</div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Coverage stats */}
        <div className="card">
          <div className="card-header"><div><div className="card-title">Cobertura</div><div className="card-subtitle">Dados importados</div></div></div>
          <div className="card-body">
            <div className="stat-grid-admin">
              <div className="stat-admin"><div className="stat-value-admin">{data?.allowedTerminalStatuses?.length ?? 0}</div><div className="stat-label-admin">status term.</div></div>
              <div className="stat-admin"><div className="stat-value-admin">48</div><div className="stat-label-admin">teams</div></div>
              <div className="stat-admin"><div className="stat-value-admin">{data?.dailyRunLimit ?? 0}</div><div className="stat-label-admin">runs/dia</div></div>
              <div className="stat-admin"><div className="stat-value-admin">0</div><div className="stat-label-admin">erros atuais</div></div>
            </div>
          </div>
        </div>

        {/* Sync flow timeline */}
        <div className="card">
          <div className="card-header"><div><div className="card-title">Fluxo de sincronização</div><div className="card-subtitle">Pipeline operacional</div></div></div>
          <div className="card-body">
            <div className="timeline-admin">
              {[
                { num: '01', title: 'Buscar fixtures', text: 'Consulta /fixtures por league, season, date e status.' },
                { num: '02', title: 'Normalizar teams', text: 'Mapeia nomes, bandeiras, país, grupo e IDs externos da API.' },
                { num: '03', title: 'Atualizar results e events', text: 'Persiste placares, status, gols, cartões e eventos relevantes.' },
                { num: '04', title: 'Recalcular pontuação', text: 'Atualiza placares, ranking, artilharia, assistências e Explore.' },
              ].map(s => (
                <div key={s.num} className="step-admin">
                  <div className="step-num-admin">{s.num}</div>
                  <div>
                    <div className="step-title-admin">{s.title}</div>
                    <div className="step-text-admin">{s.text}</div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Quick actions */}
        <div className="card">
          <div className="card-header"><div><div className="card-title">Ações rápidas</div><div className="card-subtitle">Operação</div></div></div>
          <div className="card-body">
            <div className="sync-list">
              <div className="sync-row">
                <div className="sync-icon">↻</div>
                <div><div className="sync-row-title">Sync completo</div><div className="sync-row-text">Reprocessa fixtures, teams, standings e players.</div></div>
                <button className="btn-ok">Rodar</button>
              </div>
              <div className="sync-row">
                <div className="sync-icon">◆</div>
                <div><div className="sync-row-title">Apenas fixtures</div><div className="sync-row-text">Busca jogos e resultados recentes.</div></div>
                <button className="btn-ok">Rodar</button>
              </div>
              <div className="sync-row">
                <div className="sync-icon">!</div>
                <div><div className="sync-row-title">Resetar cache</div><div className="sync-row-text">Força nova leitura da API-SPORTS v3.</div></div>
                <button className="btn-danger">Reset</button>
              </div>
            </div>
          </div>
        </div>

        {/* Logs */}
        <div className="card" style={{ gridColumn: 'span 2' }}>
          <div className="card-header">
            <div><div className="card-title">Logs recentes</div><div className="card-subtitle">Auditoria da integração</div></div>
            <div className="pill ok">sem erros</div>
          </div>
          <div className="card-body">
            {syncs.length === 0 ? (
              <div style={{ fontSize: 13, color: 'var(--tx3)' }}>Nenhuma sincronização registrada.</div>
            ) : (
              <div className="log-list">
                {syncs.slice(0, 8).map(s => (
                  <div key={s.id} className="log-row">
                    <div className="log-icon">API</div>
                    <div>
                      <div className="log-row-title">{s.operation}</div>
                      <div className="log-row-text">{s.message ?? '—'} · {new Date(s.createdAt).toLocaleString('pt-BR')}</div>
                    </div>
                    <div className={`pill ${s.status === 'SUCCESS' ? 'ok' : 'warn'}`}><span className="dot" />{s.status === 'SUCCESS' ? '200' : 'err'}</div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </>
  );
}
