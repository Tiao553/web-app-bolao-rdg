import Link from 'next/link';
import { ForgotPasswordClient } from './client';

export default function ForgotPasswordPage() {
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
          <div className="eyebrow"><span className="dot" />Recuperação de acesso</div>
          <h1>Esqueceu sua <span>senha</span>?</h1>
          <p>Não se preocupe! Digite seu email cadastrado e enviaremos um link para você criar uma nova senha.</p>
        </div>

        <div className="feature-cards">
          <div className="feature-card">
            <div className="feature-card-title">🔒 Link seguro</div>
            <div className="feature-card-text">Token único com validade de 1h.</div>
          </div>
          <div className="feature-card">
            <div className="feature-card-title">💾 Dados preservados</div>
            <div className="feature-card-text">Palpites e pontos são mantidos.</div>
          </div>
          <div className="feature-card">
            <div className="feature-card-title">🛟 Suporte admin</div>
            <div className="feature-card-text">Contate o admin se precisar.</div>
          </div>
        </div>
      </section>

      {/* ── Form panel ── */}
      <section className="form-panel" aria-label="Esqueci minha senha">
        <div className="form-card">
          <div className="form-top">
            <div>
              <h2 className="form-title">Recuperar senha</h2>
              <p className="form-subtitle">Enviaremos um link para seu email.</p>
            </div>
            <div className="brand-mark" style={{ width: 34, height: 34, borderRadius: 10, fontSize: 12 }}>R</div>
          </div>

          <ForgotPasswordClient />

          <div className="form-divider">
            <span>Não tem uma conta?</span>
            <Link href="/create-account" className="btn-light">Criar conta</Link>
          </div>
        </div>
      </section>
    </main>
  );
}
