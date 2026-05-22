import Link from 'next/link';
import { CsrfInit, PasswordField } from '../../../../components/auth/login-client';
import { getServerCsrfToken } from '../../../../lib/security';

const errorMap: Record<string, string> = {
  invalid_credentials: 'Email ou senha inválidos.',
  not_admin: 'Esta conta não tem permissão de administrador.',
  server_error: 'Não foi possível conectar ao servidor.',
  unknown: 'Não foi possível concluir o login.',
};

export default async function AdminLoginPage({ searchParams }: { searchParams?: Promise<Record<string, string | string[] | undefined>> }) {
  const params = searchParams ? await searchParams : {};
  const errorCode = typeof params.error === 'string' ? params.error : undefined;
  const csrfToken = await getServerCsrfToken();

  return (
    <main className="auth-page">
      <CsrfInit />
      {/* ── Brand panel ── */}
      <section className="brand-panel admin-brand-panel" aria-label="Painel Administrativo">
        <div className="brand-logo">
          <div className="brand-mark lg">RDG</div>
          <div>
            <div className="brand-name">Copa RDG</div>
            <div className="brand-kicker">Painel administrativo</div>
          </div>
        </div>

        <div className="hero-copy">
          <div className="eyebrow"><span className="dot" />Acesso restrito</div>
          <h1>Gerencie o bolão com <span>controle total</span>.</h1>
          <p>Configure partidas, resultados, pontuações e aprovação de participantes em um só lugar.</p>
        </div>

        <div className="admin-features">
          <div className="admin-feature-row">
            <div className="admin-feature-icon">▦</div>
            <div>
              <div className="admin-feature-title">Dashboard centralizado</div>
              <div className="admin-feature-text">Visão geral de participantes, pontuações e status.</div>
            </div>
          </div>
          <div className="admin-feature-row">
            <div className="admin-feature-icon">◈</div>
            <div>
              <div className="admin-feature-title">Gestão de partidas</div>
              <div className="admin-feature-text">Cadastre resultados e atualize o ranking em tempo real.</div>
            </div>
          </div>
          <div className="admin-feature-row">
            <div className="admin-feature-icon">◉</div>
            <div>
              <div className="admin-feature-title">Aprovação de usuários</div>
              <div className="admin-feature-text">Controle quem participa do bolão.</div>
            </div>
          </div>
        </div>
      </section>

      {/* ── Form panel ── */}
      <section className="form-panel" aria-label="Login Administrativo">
        <form className="form-card" action="/api/auth/login" method="POST">
          <input type="hidden" name="_intent" value="admin" />
          <input type="hidden" name="csrf_token" value={csrfToken} />

          <div className="form-top">
            <div>
              <h2 className="form-title">Acesso administrativo</h2>
              <p className="form-subtitle">Apenas administradores autorizados.</p>
            </div>
            <div className="brand-mark" style={{ width: 34, height: 34, borderRadius: 10, fontSize: 12, background: 'var(--s3)', border: '1px solid var(--bd2)' }}>A</div>
          </div>

          {errorCode && <div className="alert-error">{errorMap[errorCode] ?? errorMap.unknown}</div>}

          <div className="field-group">
            <label className="field-label" htmlFor="email">Email</label>
            <input id="email" name="email" type="email" className="field-input" placeholder="admin@rdg.com" required />
          </div>

          <div className="field-group">
            <label className="field-label" htmlFor="password">Senha</label>
            <PasswordField name="password" placeholder="Senha de administrador" />
          </div>

          <button type="submit" className="btn-primary full" style={{ marginTop: 8 }}>Entrar como admin →</button>

          <div className="form-divider">
            <span>Não é administrador?</span>
            <Link href="/login" className="btn-ghost">Voltar ao login →</Link>
          </div>
        </form>
      </section>
    </main>
  );
}
