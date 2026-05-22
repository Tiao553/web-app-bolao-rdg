import { redirect } from 'next/navigation';
import Link from 'next/link';
import { fetchAppSession, resolveHomePath } from '../../../lib/session';

const copyByStatus = {
  PENDING:  { title: 'Sua conta está quase liberada.', description: 'O cadastro foi recebido com status pendente. Aguarde a revisão do administrador.' },
  REJECTED: { title: 'Seu cadastro não foi liberado.', description: 'Procure um administrador se quiser revisar os dados enviados.' },
  BLOCKED:  { title: 'Sua conta está bloqueada.', description: 'O acesso ao bolão foi suspenso até nova revisão administrativa.' },
};

export default async function WaitingPage() {
  const session = await fetchAppSession();
  if (!session.authenticated || !session.user) redirect('/login');
  if (session.accessStatus === 'APPROVED') redirect(resolveHomePath(session));

  const status = session.accessStatus === 'REJECTED' || session.accessStatus === 'BLOCKED'
    ? session.accessStatus : 'PENDING';
  const copy = copyByStatus[status];

  return (
    <main className="auth-page">
      {/* ── Brand panel ── */}
      <section className="brand-panel" aria-label="Copa RDG">
        <div className="brand-logo">
          <div className="brand-mark lg">RDG</div>
          <div>
            <div className="brand-name">Copa RDG</div>
            <div className="brand-kicker">Controle de acesso</div>
          </div>
        </div>

        <div className="hero-copy">
          <div className="eyebrow"><span className="dot" />Controle de acesso</div>
          <h1>Sua conta está quase <span>liberada</span>.</h1>
          <p>Enquanto isso, o fluxo de aprovação garante governança e mantém o ranking restrito a participantes realmente liberados.</p>
        </div>

        <div className="steps">
          <div className="step-card">
            <div className="step-num">01</div>
            <div><div className="step-title">Cadastro enviado</div><div className="step-text">Sua conta foi criada com status pendente.</div></div>
          </div>
          <div className="step-card">
            <div className="step-num">02</div>
            <div><div className="step-title">Admin revisa</div><div className="step-text">O administrador confirma se você participa do bolão.</div></div>
          </div>
          <div className="step-card">
            <div className="step-num">03</div>
            <div><div className="step-title">Acesso liberado</div><div className="step-text">Após aprovação, você poderá registrar seus palpites.</div></div>
          </div>
        </div>
      </section>

      {/* ── Status panel ── */}
      <section className="form-panel" aria-label="Aguardando aprovação">
        <div className="form-card" style={{ textAlign: 'center' }}>
          <div style={{ fontSize: 48, marginBottom: 16 }}>⌛</div>
          <div className="pill orange" style={{ margin: '0 auto 16px' }}><span className="dot" />{status}</div>
          <h2 className="form-title" style={{ marginBottom: 10 }}>{copy.title}</h2>
          <p className="form-subtitle" style={{ marginBottom: 24 }}>{copy.description}</p>

          <div style={{ padding: 20, borderRadius: 16, background: '#F9F9FA', border: '1px solid #E4E4E7', textAlign: 'left', marginBottom: 24 }}>
            <div style={{ fontSize: 12, fontWeight: 700, color: '#71717A', marginBottom: 8, textTransform: 'uppercase', letterSpacing: '.06em' }}>Sua conta</div>
            <div style={{ fontSize: 15, fontWeight: 800, color: '#18181B' }}>{session.user?.name}</div>
            <div style={{ fontSize: 13, color: '#71717A' }}>{session.user?.email}</div>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
            <div style={{ padding: '10px 14px', borderRadius: 12, background: '#F4F4F5', display: 'flex', alignItems: 'center', gap: 10 }}>
              <span style={{ color: '#22c55e' }}>✓</span>
              <span style={{ fontSize: 13, color: '#52525B' }}>Cadastro recebido com sucesso</span>
            </div>
            <div style={{ padding: '10px 14px', borderRadius: 12, background: '#F4F4F5', display: 'flex', alignItems: 'center', gap: 10 }}>
              <span style={{ color: '#22c55e' }}>✓</span>
              <span style={{ fontSize: 13, color: '#52525B' }}>Sessão autenticada e ativa</span>
            </div>
            <div style={{ padding: '10px 14px', borderRadius: 12, background: '#FEF9EC', border: '1px solid #FDE68A', display: 'flex', alignItems: 'center', gap: 10 }}>
              <span>⌛</span>
              <span style={{ fontSize: 13, color: '#78350F' }}>Aguardando aprovação do admin</span>
            </div>
          </div>

          <div className="form-divider" style={{ marginTop: 24 }}>
            <span>Conta errada?</span>
            <form action="/api/auth/logout" method="POST" style={{ display: 'inline' }}>
              <button type="submit" className="btn-light">Sair</button>
            </form>
          </div>
        </div>
      </section>
    </main>
  );
}
