import Link from 'next/link';

export default function ForgotPasswordPage() {
  return (
    <main className="auth-page">
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
          <p>Informe seu e-mail cadastrado e enviaremos as instruções para redefinir sua senha.</p>
        </div>

        <div className="feature-cards">
          <div className="feature-card"><div className="feature-card-title">E-mail seguro</div><div className="feature-card-text">Link enviado com validade de 1h.</div></div>
          <div className="feature-card"><div className="feature-card-title">Sem perda de dados</div><div className="feature-card-text">Palpites e pontos são preservados.</div></div>
          <div className="feature-card"><div className="feature-card-title">Suporte admin</div><div className="feature-card-text">Contate o admin se não receber.</div></div>
        </div>
      </section>

      <section className="form-panel" aria-label="Esqueci minha senha">
        <div className="form-card">
          <div className="form-top">
            <div>
              <h2 className="form-title">Forget Password?</h2>
              <p className="form-subtitle">Digite seu e-mail para receber o link de redefinição.</p>
            </div>
            <div className="brand-mark" style={{ width: 34, height: 34, borderRadius: 10, fontSize: 12 }}>R</div>
          </div>

          <form action="#" method="POST">
            <div className="field-group">
              <label className="field-label" htmlFor="email">Email</label>
              <input id="email" name="email" type="email" className="field-input" placeholder="Ex: sebastiao@rdg.com" required />
            </div>

            <button type="submit" className="btn-primary full" style={{ marginBottom: 0 }}>Enviar link →</button>
          </form>

          <div className="form-divider">
            <span>Lembrou a senha?</span>
            <Link href="/login" className="btn-light">Voltar ao login</Link>
          </div>
        </div>
      </section>
    </main>
  );
}
