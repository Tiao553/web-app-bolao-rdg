'use client';
import { useEffect, useState } from 'react';

function getCsrfCookie(): string {
  const entry = document.cookie.split('; ').find((c) => c.startsWith('bolao_csrf='));
  return entry ? decodeURIComponent(entry.slice('bolao_csrf='.length)) : '';
}

export function CsrfInit() {
  useEffect(() => {
    async function init() {
      if (!getCsrfCookie()) {
        await fetch('/api/auth/csrf').catch(() => {});
      }
      // update all hidden csrf_token inputs on this page
      document.querySelectorAll<HTMLInputElement>('input[name="csrf_token"]').forEach((el) => {
        el.value = getCsrfCookie();
      });
    }
    init();
  }, []);
  return null;
}

export function TypeSwitch() {
  const [active, setActive] = useState<'member' | 'admin'>('member');
  return (
    <div className="type-switch">
      <button className={`type-btn${active === 'member' ? ' active' : ''}`} type="button" onClick={() => setActive('member')}>Participante</button>
      <button className={`type-btn${active === 'admin' ? ' active' : ''}`} type="button" onClick={() => setActive('admin')}>Administrador</button>
    </div>
  );
}

export function PasswordField({ name, placeholder }: { name: string; placeholder: string }) {
  const [show, setShow] = useState(false);
  return (
    <div className="input-wrap">
      <input name={name} type={show ? 'text' : 'password'} className="field-input" placeholder={placeholder} required />
      <button type="button" className="password-eye" onClick={() => setShow(v => !v)} aria-label="Mostrar senha">
        {show ? '○' : '◉'}
      </button>
    </div>
  );
}
