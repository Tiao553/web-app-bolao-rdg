import Link from 'next/link';
import { CsrfInit, PasswordField } from '../../../components/auth/login-client';
import { getServerCsrfToken } from '../../../lib/security';

const errorMap: Record<string, string> = {
  email_taken: 'Este e-mail já está em uso.',
  email_already_registered: 'Este e-mail já está em uso.',
  server_error: 'Não foi possível conectar ao servidor.',
  unknown: 'Não foi possível criar a conta.',
};

export default async function CreateAccountPage({ searchParams }: { searchParams?: Promise<Record<string, string | string[] | undefined>> }) {
  const params = searchParams ? await searchParams : {};
  const errorCode = typeof params.error === 'string' ? params.error : undefined;
  const csrfToken = await getServerCsrfToken();

  return (
    <main className="auth-page">
      <CsrfInit />
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
          <h1>Crie sua conta. Faça seus <span>palpites</span>. Suba no ranking.</h1>
          <p>Cadastre-se agora, aguarde a aprovação do administrador e entre no bolão oficial.</p>
        </div>

        <div className="feature-cards">
          <div className="feature-card"><div className="feature-card-title">Cadastro simples</div><div className="feature-card-text">Nome, e-mail e senha.</div></div>
          <div className="feature-card"><div className="feature-card-title">Aprovação rápida</div><div className="feature-card-text">Admin libera o acesso.</div></div>
          <div className="feature-card"><div className="feature-card-title">Palpites abertos</div><div className="feature-card-text">Registre antes do fechamento.</div></div>
        </div>
      </section>

      {/* ── Form panel ── */}
      <section className="form-panel" aria-label="Criar conta">
        <form className="form-card" action="/api/auth/register" method="POST">
          <input type="hidden" name="csrf_token" value={csrfToken} />
          <div className="form-top">
            <div>
              <h2 className="form-title">Criar conta</h2>
              <p className="form-subtitle">Preencha os dados para se cadastrar no bolão.</p>
            </div>
            <div className="brand-mark" style={{ width: 34, height: 34, borderRadius: 10, fontSize: 12 }}>R</div>
          </div>

          {errorCode && <div className="alert-error">{errorMap[errorCode] ?? errorMap.unknown}</div>}

          <div className="field-group">
            <label className="field-label" htmlFor="name">Nome completo</label>
            <input id="name" name="name" type="text" className="field-input" placeholder="Ex: João Silva" required />
          </div>

          <div className="field-group">
            <label className="field-label" htmlFor="email">Email</label>
            <input id="email" name="email" type="email" className="field-input" placeholder="Ex: joao@email.com" required />
          </div>

          <div className="field-group">
            <label className="field-label" htmlFor="password">Senha</label>
            <PasswordField name="password" placeholder="Mínimo 8 caracteres" />
          </div>

          <div className="field-group" style={{ marginBottom: 20 }}>
            <label className="field-label" style={{ display: 'flex', alignItems: 'flex-start', gap: 10, cursor: 'pointer', fontWeight: 400, textTransform: 'none' }}>
              <input type="checkbox" required style={{ marginTop: 2, accentColor: 'var(--or)', width: 15, height: 15 }} />
              <span style={{ fontSize: 12, color: '#52525B' }}>
                Ao criar uma conta, aceito os{' '}
                <a href="#" style={{ color: '#18181B', fontWeight: 700, textDecoration: 'none' }}>Termos &amp; Condições</a>.
              </span>
            </label>
          </div>

          <button type="submit" className="btn-primary full">Criar conta →</button>

          <div className="form-divider">
            <span>Já tem uma conta?</span>
            <Link href="/login" className="btn-light">Entrar</Link>
          </div>
        </form>
      </section>
    </main>
  );
}
