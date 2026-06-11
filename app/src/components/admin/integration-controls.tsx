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

export function AdminIntegrationControls({ csrfToken, initialData }: Props) {
  const [data, setData] = useState(initialData);
  const [enabled, setEnabled] = useState(initialData.autoSyncEnabled);
  const [interval, setInterval] = useState(String(initialData.autoSyncIntervalMinutes));
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');
  const [isSaving, startSaving] = useTransition();
  const [isRunning, startRunning] = useTransition();

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
          body: JSON.stringify({ provider: 'THE_SPORTS_DB', include_top_scorers: false }),
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
            <div className="eyebrow"><span className="dot" />TheSportsDB v1</div>
            <h1>Automatize resultados com <span>heartbeat externo</span>.</h1>
            <p>
              O backend recebe um cron externo a cada minuto, decide se o intervalo configurado venceu
              e sincroniza resultados do TheSportsDB sem depender de alguém com a tela aberta.
            </p>
          </div>
          <div className="connection-card">
            <div className="conn-label">Provedor ativo</div>
            <div className="conn-title">{data.activeProvider}</div>
            <div className="conn-text">
              {data.apiConfigured
                ? 'TheSportsDB livre ativo para sync automático de resultados.'
                : 'Provedor indisponível.'}
            </div>
          </div>
        </div>
      </section>

      <div className="grid-2">
        <div className="card">
          <div className="card-header">
            <div>
              <div className="card-title">Configuração da integração</div>
              <div className="card-subtitle">Fonte ativa, cron e cadência</div>
            </div>
            <div className={`pill ${data.autoSyncEnabled ? 'ok' : 'warn'}`}>
              <span className="dot" />{data.autoSyncEnabled ? 'auto ligado' : 'auto desligado'}
            </div>
          </div>
          <div className="card-body">
            <div className="config-grid">
              {[
                { label: 'Provider ativo', value: data.activeProvider },
                { label: 'Fallback', value: data.fallbackProvider },
                { label: 'Base URL', value: 'https://www.thesportsdb.com/api/v1/json/123' },
                { label: 'Endpoint principal', value: '/eventsseason.php?id=4429&s=2026' },
                { label: 'Scheduler', value: data.schedulerMode },
                { label: 'Cron token', value: data.cronTokenConfigured ? 'Configurado' : 'Ausente' },
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
              <div className="card-subtitle">Liga/desliga e intervalo persistido</div>
            </div>
          </div>
          <div className="card-body">
            <div className="toggle-list" style={{ marginBottom: 16 }}>
              <div className="toggle-row">
                <div>
                  <div className="toggle-title">Habilitar sync automático</div>
                  <div className="toggle-text">Cron externo bate todo minuto; o backend filtra pela cadência.</div>
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
                  <div className="toggle-text">{formatDate(data.lastAutoSyncAt)}</div>
                </div>
              </div>
              <div className="toggle-row">
                <div>
                  <div className="toggle-title">Próximo elegível</div>
                  <div className="toggle-text">{formatDate(data.nextAutoSyncAt)}</div>
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
                { num: '01', title: 'Cron externo', text: 'Um scheduler externo chama /api/internal/sync/auto a cada minuto.' },
                { num: '02', title: 'Gate interno', text: 'O backend valida token, intervalo configurado e lock concorrente.' },
                { num: '03', title: 'TheSportsDB', text: 'Busca eventos da temporada e mapeia apenas partidas locais com alta confiança.' },
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
                      <div className="log-row-text">{sync.message || '—'} · {new Date(sync.createdAt).toLocaleString('pt-BR')}</div>
                    </div>
                    <div className={`pill ${sync.status === 'SUCCESS' ? 'ok' : sync.status === 'SKIPPED' ? 'orange' : 'warn'}`}>
                      <span className="dot" />{sync.status}
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
