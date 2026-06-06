import Link from 'next/link';
import { ResetPasswordClient } from './client';

interface ResetPasswordPageProps {
  searchParams?: Promise<{ token?: string }>;
}

export default async function ResetPasswordPage({ searchParams }: ResetPasswordPageProps) {
  const params = searchParams ? await searchParams : {};
  const token = typeof params.token === 'string' ? params.token : null;

  // Token ausente ou inválido
  if (!token || token.trim() === '') {
    return (
      <main className="auth-page">
        <section className="form-panel" aria-label="Link inválido" style={{ display: 'grid', placeItems: 'center' }}>
          <div className="form-card" style={{ textAlign: 'center' }}>
            <div style={{ fontSize: 48, marginBottom: 16 }}>🔗</div>
            <h2 className="form-title">Link inválido</h2>
            <p className="form-subtitle" style={{ marginBottom: 24 }}>
              Este link de recuperação é inválido ou já foi utilizado.
            </p>
            <Link href="/forgot-password" className="btn-primary full">
              Solicitar novo link →
            </Link>
            <div style={{ marginTop: 16 }}>
              <Link href="/login" className="btn-ghost">
                Voltar ao login
              </Link>
            </div>
          </div>
        </section>
      </main>
    );
  }

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
          <div className="eyebrow"><span className="dot" />Segurança</div>
          <h1>Nova <span>senha</span></h1>
          <p>Crie uma senha forte para proteger sua conta do Bolão Copa RDG.</p>
        </div>

        <div className="feature-cards">
          <div className="feature-card">
            <div className="feature-card-title">🔐 Mínimo 8 caracteres</div>
            <div className="feature-card-text">Use letras, números e símbolos.</div>
          </div>
          <div className="feature-card">
            <div className="feature-card-title">🚪 Sessões encerradas</div>
            <div className="feature-card-text">Por segurança, você será desconectado de todos os dispositivos.</div>
          </div>
          <div className="feature-card">
            <div className="feature-card-title">✅ Link único</div>
            <div className="feature-card-text">Este link só pode ser usado uma vez.</div>
          </div>
        </div>
      </section>

      {/* ── Form panel ── */}
      <section className="form-panel" aria-label="Redefinir senha">
        <div className="form-card">
          <div className="form-top">
            <div>
              <h2 className="form-title">Criar nova senha</h2>
              <p className="form-subtitle">Digite e confirme sua nova senha abaixo.</p>
            </div>
            <div className="brand-mark" style={{ width: 34, height: 34, borderRadius: 10, fontSize: 12 }}>R</div>
          </div>

          <ResetPasswordClient token={token} />

          <div className="form-divider">
            <span>Lembrou sua senha antiga?</span>
            <Link href="/login" className="btn-light">Fazer login</Link>
          </div>
        </div>
      </section>
    </main>
  );
}
