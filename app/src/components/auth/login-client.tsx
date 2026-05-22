'use client';
import { useState } from 'react';

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
