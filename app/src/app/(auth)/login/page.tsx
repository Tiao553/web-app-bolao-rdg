import Link from 'next/link';
import { PasswordField } from '../../../components/auth/login-client';

const errorMap: Record<string, string> = {
  invalid_credentials: 'Email ou senha inválidos.',
  server_error: 'Não foi possível conectar ao servidor.',
  unknown: 'Não foi possível concluir o login.',
};

export default async function LoginPage({ searchParams }: { searchParams?: Promise<Record<string, string | string[] | undefined>> }) {
  const params = searchParams ? await searchParams : {};
  const errorCode = typeof params.error === 'string' ? params.error : undefined;

  return (
    <main className="auth-page">
      {/* ── Brand panel ── */}
      <section className="brand-panel" aria-label="Copa RDG">
        <div className="brand-logo">
          <div className="brand-mark lg">RDG</div>
          <div>
            <div className="brand-name">Copa RDG</div>
            <div className="brand-kicker">Bolão oficial</div>
          </div>
        </div>

        <div className="hero-copy">
          <div className="eyebrow"><span className="dot" />Copa do Mundo 2026</div>
          <h1>Entre no bolão e acompanhe seus <span>palpites</span>.</h1>
          <p>Um bolão feito para a Copa do Mundo 2026 — palpites, resultados e ranking num só lugar.</p>
        </div>

        <div className="mock-illustration" aria-hidden="true">
          <div className="floating-card one">
            <div className="float-label">Pontuação</div>
            <div className="float-value">127 pts</div>
            <div className="float-line"><span /></div>
          </div>
          <div className="floating-card two">
            <div className="float-label">Status</div>
            <div className="float-value">#02</div>
            <div className="float-line"><span style={{ width: '82%' }} /></div>
          </div>
          <div className="person">
            <div className="head"><div className="hair" /><div className="glasses" /></div>
            <div className="neck" />
            <div className="torso" />
            <div className="shirt" />
            <div className="arm-left" />
            <div className="arm-right" />
            <div className="leg-left" />
            <div className="leg-right" />
            <div className="shoe-left" />
            <div className="shoe-right" />
          </div>
        </div>

        <div className="feature-cards">
          <div className="feature-card"><div className="feature-card-title">Acesso aprovado</div><div className="feature-card-text">Rotas protegidas por sessão.</div></div>
          <div className="feature-card"><div className="feature-card-title">Palpites bloqueáveis</div><div className="feature-card-text">A regra continua no backend.</div></div>
          <div className="feature-card"><div className="feature-card-title">Explore liberado</div><div className="feature-card-text">Somente após o fechamento oficial.</div></div>
        </div>
      </section>

      {/* ── Form panel ── */}
      <section className="form-panel" aria-label="Login">
        <form className="form-card" action="/api/auth/login" method="POST">
          <input type="hidden" name="_intent" value="participant" />

          <div className="form-top">
            <div>
              <h2 className="form-title">Bem-vindo de volta</h2>
              <p className="form-subtitle">Entre com seu e-mail e senha para continuar.</p>
            </div>
            <div className="brand-mark" style={{ width: 34, height: 34, borderRadius: 10, fontSize: 12 }}>R</div>
          </div>

          {errorCode && <div className="alert-error">{errorMap[errorCode] ?? errorMap.unknown}</div>}

          <div className="field-group">
            <label className="field-label" htmlFor="email">Email</label>
            <input id="email" name="email" type="email" className="field-input" placeholder="seu@email.com" required />
          </div>

          <div className="field-group">
            <label className="field-label" htmlFor="password">Senha</label>
            <PasswordField name="password" placeholder="Sua senha" />
          </div>

          <Link href="/forgot-password" className="forgot-link">Esqueceu a senha?</Link>

          <button type="submit" className="btn-primary full">Entrar →</button>

          <div className="form-divider">
            <span>Ainda não tem conta?</span>
            <Link href="/create-account" className="btn-light">Criar conta</Link>
          </div>

          <div className="form-divider" style={{ marginTop: 0, paddingTop: 0, borderTop: 'none' }}>
            <span style={{ fontSize: '0.75rem', color: 'var(--tx3)' }}>Área administrativa?</span>
            <Link href="/admin/login" className="btn-ghost" style={{ fontSize: '0.75rem', padding: '6px 12px' }}>Acesso admin →</Link>
          </div>
        </form>
      </section>
    </main>
  );
}
