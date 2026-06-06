'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { postJson } from '../../../lib/api-client';

interface ResetPasswordClientProps {
  token: string;
}

export function ResetPasswordClient({ token }: ResetPasswordClientProps) {
  const router = useRouter();
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [status, setStatus] = useState<'idle' | 'loading' | 'success' | 'error'>('idle');
  const [errorMessage, setErrorMessage] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (password !== confirmPassword) {
      setErrorMessage('As senhas não coincidem');
      return;
    }

    if (password.length < 8) {
      setErrorMessage('A senha deve ter pelo menos 8 caracteres');
      return;
    }

    setStatus('loading');
    setErrorMessage('');

    try {
      await postJson('/api/auth/reset-password', { token, password });
      setStatus('success');
      setTimeout(() => router.push('/login'), 2000);
    } catch (err) {
      setStatus('error');
      setErrorMessage(err instanceof Error ? err.message : 'Erro ao redefinir senha');
    }
  };

  if (status === 'success') {
    return (
      <div className="alert-info">
        <strong style={{ color: '#22c55e' }}>✓ Senha redefinida!</strong>
        <p style={{ marginTop: 12 }}>Redirecionando para o login...</p>
      </div>
    );
  }

  return (
    <form onSubmit={handleSubmit}>
      <div className="field-group">
        <label className="field-label" htmlFor="password">Nova senha</label>
        <div className="input-wrap">
          <input
            id="password"
            name="password"
            type={showPassword ? 'text' : 'password'}
            className="field-input"
            placeholder="Mínimo 8 caracteres"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            minLength={8}
            autoFocus
          />
          <button
            type="button"
            className="password-eye"
            onClick={() => setShowPassword(!showPassword)}
            aria-label={showPassword ? 'Ocultar senha' : 'Mostrar senha'}
          >
            {showPassword ? '🙈' : '👁️'}
          </button>
        </div>
      </div>

      <div className="field-group">
        <label className="field-label" htmlFor="confirmPassword">Confirmar nova senha</label>
        <div className="input-wrap">
          <input
            id="confirmPassword"
            name="confirmPassword"
            type={showPassword ? 'text' : 'password'}
            className="field-input"
            placeholder="Repita a senha"
            value={confirmPassword}
            onChange={(e) => setConfirmPassword(e.target.value)}
            required
            minLength={8}
          />
        </div>
      </div>

      {status === 'error' && (
        <div className="alert-error">{errorMessage}</div>
      )}

      <button type="submit" className="btn-primary full" disabled={status === 'loading'}>
        {status === 'loading' ? 'Salvando...' : 'Salvar nova senha →'}
      </button>

      <p style={{ marginTop: 16, fontSize: 12, color: 'var(--tx3)', textAlign: 'center' }}>
        <Link href="/forgot-password" style={{ color: 'var(--or)', fontWeight: 600 }}>
          Solicitar novo link
        </Link>
        {' • '}
        <Link href="/login" style={{ color: 'var(--tx2)' }}>
          Voltar ao login
        </Link>
      </p>
    </form>
  );
}
