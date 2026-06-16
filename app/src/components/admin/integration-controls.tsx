'use client';

import { useState, useTransition } from 'react';

import type { AdminIntegrationContract } from '../../lib/contracts';

type Props = {
  csrfToken: string;
  initialData: AdminIntegrationContract;
};

function formatDate(value: string | null): string {
  if (!value) {
    return '—';
  }
  return new Date(value).toLocaleString('pt-BR');
}

function formatScheduler(mode: string): string {
  if (mode.startsWith('INTERNAL_RUNTIME_')) {
    const seconds = Number(mode.replace('INTERNAL_RUNTIME_', '').replace('s', ''));
    if (Number.isFinite(seconds) && seconds > 0) {
      return `Worker interno a cada ${seconds}s`;
    }
    return 'Worker interno';
  }
  if (mode === 'EXTERNAL_TRIGGER_ONLY') {
    return 'Trigger externo';
  }
  return mode;
}

function formatProviderLabel(value: string): string {
  const labels: Record<string, string> = {
    THE_SPORTS_DB: 'FIFA live scrape',
    API_FOOTBALL: 'API-Football',
    GOOGLE_SHEETS: 'Google Sheets',
    ADMIN: 'Admin',
    SEED: 'Seed',
  };
  return labels[value] ?? value;
}

export function AdminIntegrationControls({ csrfToken, initialData }: Props) {
  const [data, setData] = useState(initialData);
  const [enabled, setEnabled] = useState(initialData.autoSyncEnabled);
  const [interval, setInterval] = useState(String(initialData.autoSyncIntervalMinutes));
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');
  const [isSaving, startSaving] = useTransition();
  const [isRunning, startRunning] = useTransition();
  const schedulerLabel = formatScheduler(data.schedulerMode);
  const syncStatusTone = data.autoSyncEnabled ? 'ok' : 'warn';
  const nextRunLabel = data.nextAutoSyncAt ? formatDate(data.nextAutoSyncAt) : 'Habilite o auto sync';
  const lastRunLabel = formatDate(data.lastAutoSyncAt);
  const activeProviderLabel = formatProviderLabel(data.activeProvider);
  const primaryProviderLabel = formatProviderLabel(data.primaryProvider);
  const fallbackProviderLabel = formatProviderLabel(data.fallbackProvider);

  function saveSettings() {
    setMessage('');
    setError('');
    startSaving(async () => {
      try {
        const res = await fetch('/api/admin/integration/settings', {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json', 'x-csrf-token': csrfToken },
          body: JSON.stringify({
            auto_sync_enabled: enabled,
            auto_sync_interval_minutes: Number(interval),
          }),
        });
        const body = await res.json().catch(() => ({}));
        if (!res.ok) {
          setError(body?.error?.message || body?.detail?.message || body?.detail || `Erro ${res.status}`);
          return;
        }
        setData(body);
        setEnabled(body.autoSyncEnabled);
        setInterval(String(body.autoSyncIntervalMinutes));
        setMessage('Configurações salvas.');
      } catch {
        setError('Falha de rede ao salvar.');
      }
    });
  }

  function runSyncNow() {
    setMessage('');
    setError('');
    startRunning(async () => {
      try {
        const res = await fetch('/api/admin/sync/run', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json', 'x-csrf-token': csrfToken },
          body: JSON.stringify({ provider: 'THE_SPORTS_DB', include_top_scorers: false, mode: 'LATEST_RESULT_ONLY' }),
        });
        const body = await res.json().catch(() => ({}));
        if (!res.ok) {
          setError(body?.error?.message || body?.detail?.message || body?.detail || `Erro ${res.status}`);
          return;
        }
        setMessage(body?.message || 'Sync executado.');
        window.location.reload();
      } catch {
        setError('Falha de rede ao executar sync.');
      }
    });
  }

  const syncs = data.lastSyncs ?? [];

  return (
    <>
      {(message || error) && (
        <div
          className={error ? 'modal-error' : 'modal-success'}
          style={{ margin: '0 0 16px', padding: '10px 16px', borderRadius: 10, fontSize: 13 }}
        >
          {error || message}
        </div>
      )}

      <section className="hero">
        <div className="hero-content">
          <div>
            <div className="eyebrow"><span className="dot" />Integrations</div>
            <h1>Resultados quase em tempo real sem depender do delay da API.</h1>
            <p>
              O run now usa o scraper FIFA primeiro, o backend salva no mesmo fluxo do ranking
              e a automação pode rodar no worker interno sem depender só de cron externo.
            </p>
          </div>
          <div className="connection-card">
            <div className="conn-label">Provedor ativo</div>
            <div className="conn-title">{activeProviderLabel}</div>
            <div className="conn-text">
              {data.apiConfigured
                ? 'Scrape FIFA ativo para resultados e Explore.'
                : 'Provedor indisponível.'}
            </div>
            <div className="stat-grid-admin" style={{ marginTop: 16 }}>
              <div className="stat-admin">
                <div className="stat-value-admin">{schedulerLabel}</div>
                <div className="stat-label-admin">scheduler</div>
              </div>
              <div className="stat-admin">
                <div className="stat-value-admin">{data.cronTokenConfigured ? 'OK' : 'Ausente'}</div>
                <div className="stat-label-admin">token</div>
              </div>
              <div className="stat-admin">
                <div className="stat-value-admin">{data.autoSyncEnabled ? 'Ligado' : 'Desligado'}</div>
                <div className="stat-label-admin">auto sync</div>
              </div>
              <div className="stat-admin">
                <div className="stat-value-admin">{data.autoSyncStatus}</div>
                <div className="stat-label-admin">estado</div>
              </div>
            </div>
          </div>
        </div>
      </section>

      <div className="grid-2">
        <div className="card">
            <div className="card-header">
            <div>
              <div className="card-title">Configuração da integração</div>
              <div className="card-subtitle">Fonte ativa, gate e intervalo salvo</div>
            </div>
            <div className={`pill ${syncStatusTone}`}>
              <span className="dot" />{data.autoSyncEnabled ? 'auto ligado' : 'auto desligado'}
            </div>
          </div>
            <div className="card-body">
            <div className="config-grid">
              {[
                { label: 'Provider ativo', value: activeProviderLabel },
                { label: 'Primário', value: primaryProviderLabel },
                { label: 'Fallback', value: fallbackProviderLabel },
                { label: 'Scheduler', value: schedulerLabel },
                { label: 'Cron token', value: data.cronTokenConfigured ? 'Configurado' : 'Ausente' },
                { label: 'Intervalo', value: `${data.autoSyncIntervalMinutes} minuto${data.autoSyncIntervalMinutes > 1 ? 's' : ''}` },
                { label: 'Estados terminais', value: String(data.allowedTerminalStatuses.length) },
              ].map(({ label, value }) => (
                <div key={label} className="field-admin">
                  <div className="field-label-admin">{label}</div>
                  <div className="field-value-admin">{value}</div>
                </div>
              ))}
            </div>
          </div>
        </div>

        <div className="card">
          <div className="card-header">
            <div>
              <div className="card-title">Auto sync</div>
              <div className="card-subtitle">Liga/desliga e intervalo persistido no backend</div>
            </div>
          </div>
          <div className="card-body">
            <div className="toggle-list" style={{ marginBottom: 16 }}>
              <div className="toggle-row">
                <div>
                  <div className="toggle-title">Habilitar sync automático</div>
                  <div className="toggle-text">O backend verifica a fila no worker interno e o endpoint interno continua disponível para trigger externo.</div>
                </div>
                <button
                  type="button"
                  className={`switch ${enabled ? 'on' : ''}`}
                  aria-pressed={enabled}
                  onClick={() => setEnabled((value) => !value)}
                />
              </div>
            </div>

            <div className="field-admin" style={{ marginBottom: 16 }}>
              <div className="field-label-admin">Intervalo</div>
              <select className="admin-select" value={interval} onChange={(e) => setInterval(e.target.value)}>
                {data.autoSyncIntervalOptions.map((option) => (
                  <option key={option} value={option}>{option} minuto{option > 1 ? 's' : ''}</option>
                ))}
              </select>
              </div>

            <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
              <button className="btn-ok" style={{ height: 36, padding: '0 14px' }} onClick={saveSettings} disabled={isSaving}>
                {isSaving ? 'Salvando…' : 'Salvar'}
              </button>
              <button className="btn-primary" style={{ height: 36, padding: '0 14px' }} onClick={runSyncNow} disabled={isRunning}>
                {isRunning ? 'Rodando…' : 'Rodar agora'}
              </button>
            </div>
          </div>
        </div>

        <div className="card">
          <div className="card-header">
            <div>
              <div className="card-title">Estado operacional</div>
              <div className="card-subtitle">Pronto, esperando ou desligado</div>
            </div>
          </div>
          <div className="card-body">
            <div className="stat-grid-admin">
              <div className="stat-admin"><div className="stat-value-admin">{data.autoSyncStatus}</div><div className="stat-label-admin">status</div></div>
              <div className="stat-admin"><div className="stat-value-admin">{data.autoSyncIntervalMinutes}</div><div className="stat-label-admin">minutos</div></div>
              <div className="stat-admin"><div className="stat-value-admin">{data.allowedTerminalStatuses.length}</div><div className="stat-label-admin">status term.</div></div>
              <div className="stat-admin"><div className="stat-value-admin">{data.dailyRunLimit}</div><div className="stat-label-admin">limite legado</div></div>
            </div>
            <div className="toggle-list" style={{ marginTop: 14 }}>
              <div className="toggle-row">
                <div>
                  <div className="toggle-title">Último auto sync</div>
                  <div className="toggle-text">{lastRunLabel}</div>
                </div>
              </div>
              <div className="toggle-row">
                <div>
                  <div className="toggle-title">Próximo elegível</div>
                  <div className="toggle-text">{nextRunLabel}</div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div className="card">
          <div className="card-header">
            <div>
              <div className="card-title">Fluxo</div>
              <div className="card-subtitle">Pipeline do automatic sync</div>
            </div>
          </div>
          <div className="card-body">
            <div className="timeline-admin">
              {[
                { num: '01', title: 'Worker interno', text: 'O backend acorda a cada 60 segundos e tenta rodar o sync automático.' },
                { num: '02', title: 'Gate interno', text: 'O backend aplica intervalo configurado, lock concorrente e mantém o endpoint interno para trigger externo.' },
                { num: '03', title: 'Scraper FIFA', text: 'Busca resultados ao vivo/encerrados e mapeia apenas partidas locais com alta confiança.' },
                { num: '04', title: 'Recalcular', text: 'Atualiza resultados, ranking, Explore e demais derivados da competição.' },
              ].map((step) => (
                <div key={step.num} className="step-admin">
                  <div className="step-num-admin">{step.num}</div>
                  <div>
                    <div className="step-title-admin">{step.title}</div>
                    <div className="step-text-admin">{step.text}</div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        <div className="card" style={{ gridColumn: 'span 2' }}>
          <div className="card-header">
            <div>
              <div className="card-title">Logs recentes</div>
              <div className="card-subtitle">automatic_sync, scheduled_sync e match_sync</div>
            </div>
          </div>
          <div className="card-body">
            {syncs.length === 0 ? (
              <div style={{ fontSize: 13, color: 'var(--tx3)' }}>Nenhuma sincronização registrada.</div>
            ) : (
              <div className="log-list">
                {syncs.map((sync) => (
                  <div key={sync.id} className="log-row">
                    <div className="log-icon">{sync.provider === 'THE_SPORTS_DB' ? 'TSD' : 'API'}</div>
                    <div>
                      <div className="log-row-title">{sync.operation}</div>
                      <div className="log-row-text">
                        {sync.message || '—'}
                        {sync.resultCode ? ` · ${sync.resultCode}` : ''}
                        {' · '}
                        {new Date(sync.createdAt).toLocaleString('pt-BR')}
                      </div>
                    </div>
                    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: 6 }}>
                      <div className={`pill ${sync.status === 'SUCCESS' ? 'ok' : sync.status === 'SKIPPED' ? 'orange' : 'warn'}`}>
                        <span className="dot" />{sync.status}
                      </div>
                      {sync.resultCode ? <div className="pill neutral">{sync.resultCode}</div> : null}
                    </div>
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
