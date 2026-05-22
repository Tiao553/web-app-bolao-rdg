'use client';
import { useState, useTransition } from 'react';

interface Props {
  userId: string;
  userName: string;
  csrfToken: string;
}

export function ResetPasswordBtn({ userId, userName, csrfToken }: Props) {
  const [result, setResult] = useState<{ resetAt: string; email: string } | null>(null);
  const [error, setError] = useState('');
  const [isPending, startTransition] = useTransition();

  function handleReset() {
    setError('');
    startTransition(async () => {
      try {
        const res = await fetch(`/api/admin/users/${userId}/reset-password`, {
          method: 'POST',
          headers: { 'x-csrf-token': csrfToken },
        });
        if (!res.ok) {
          const b = await res.json().catch(() => ({}));
          setError(b?.error?.message || b?.detail?.message || b?.detail || `Erro ${res.status}`);
          return;
        }
        const data = await res.json();
        setResult({ resetAt: data.reset_at, email: data.email });
      } catch {
        setError('Falha de rede.');
      }
    });
  }

  if (result) {
    return (
      <div className="modal-overlay" onClick={() => setResult(null)}>
        <div className="modal-box" style={{ maxWidth: 420 }} onClick={e => e.stopPropagation()}>
          <div className="modal-header">
            <div className="modal-title">Senha redefinida</div>
            <button className="modal-close" onClick={() => setResult(null)}>✕</button>
          </div>
          <div className="modal-body" style={{ gap: 10 }}>
            <p style={{ fontSize: 13, color: 'var(--tx2)' }}>
              A senha de <strong>{userName}</strong> ({result.email}) foi redefinida e todas as sessões ativas foram revogadas.
            </p>
            <div style={{ background: 'var(--s0)', border: '1px solid var(--bd2)', borderRadius: 10, padding: '12px 16px', fontSize: 13, color: 'var(--tx2)' }}>
              Horário do reset: {new Date(result.resetAt).toLocaleString('pt-BR')}
            </div>
          </div>
          <div className="modal-footer">
            <button className="btn-primary" style={{ height: 36, fontSize: 12, padding: '0 20px' }} onClick={() => setResult(null)}>
              Entendido
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <>
      <button
        className="btn-ghost"
        style={{ height: 32, fontSize: 11, padding: '0 10px' }}
        onClick={handleReset}
        disabled={isPending}
        title="Redefinir a senha e revogar sessões ativas"
      >
        {isPending ? '…' : 'Reset senha'}
      </button>
      {error && <span style={{ fontSize: 11, color: '#f43f5e' }}>{error}</span>}
    </>
  );
}
