'use client';

import { useState } from 'react';
import Link from 'next/link';
import { postJson } from '../../../lib/api-client';

export function ForgotPasswordClient() {
  const [email, setEmail] = useState('');
  const [status, setStatus] = useState<'idle' | 'loading' | 'success' | 'error'>('idle');
  const [errorMessage, setErrorMessage] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setStatus('loading');
    setErrorMessage('');

    try {
      await postJson('/api/auth/forgot-password', { email });
      setStatus('success');
    } catch (err) {
      setStatus('error');
      setErrorMessage(err instanceof Error ? err.message : 'Erro ao enviar email');
    }
  };

  if (status === 'success') {
    return (
      <div className="alert-info">
        <strong style={{ color: '#22c55e' }}>✓ Email enviado!</strong>
        <p style={{ marginTop: 12, lineHeight: 1.6 }}>
          Se o email existir em nossa base, você receberá instruções para redefinir sua senha em instantes.
        </p>
        <p style={{ marginTop: 8, fontSize: 12, color: 'var(--tx3)' }}>
          Verifique também a caixa de spam.
        </p>
        <Link href="/login" className="btn-light" style={{ marginTop: 20, display: 'inline-block' }}>
          Voltar ao login
        </Link>
      </div>
    );
  }

  return (
    <form onSubmit={handleSubmit}>
      <div className="field-group">
        <label className="field-label" htmlFor="email">Email cadastrado</label>
        <input
          id="email"
          name="email"
          type="email"
          className="field-input"
          placeholder="seu@email.com"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          required
          autoFocus
        />
      </div>

      {status === 'error' && (
        <div className="alert-error">{errorMessage}</div>
      )}

      <button type="submit" className="btn-primary full" disabled={status === 'loading'}>
        {status === 'loading' ? 'Enviando...' : 'Enviar link de recuperação →'}
      </button>

      <p style={{ marginTop: 16, fontSize: 12, color: 'var(--tx3)', textAlign: 'center' }}>
        Lembrou sua senha?{' '}
        <Link href="/login" style={{ color: 'var(--or)', fontWeight: 600 }}>
          Fazer login
        </Link>
      </p>
    </form>
  );
}
