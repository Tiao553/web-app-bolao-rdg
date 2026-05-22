'use client';
import type { ReactNode } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import type { AppSession } from '../../lib/session';

const primaryNav = [
  { href: '/dashboard', label: 'Dashboard', icon: '◈' },
  { href: '/initial-predictions', label: 'Palpites iniciais', icon: '★' },
  { href: '/phase-predictions', label: 'Palpites por fase', icon: '▦' },
  { href: '/results', label: 'Resultados', icon: '◆' },
];
const competitionNav = [
  { href: '/ranking', label: 'Ranking', icon: '#' },
  { href: '/standings', label: 'Classificação', icon: '≡' },
  { href: '/bracket', label: 'Chaveamento', icon: '⌁' },
  { href: '/explore', label: 'Explore', icon: '◎' },
];

export function MemberShell({ session, children }: { session: AppSession; children: ReactNode }) {
  const pathname = usePathname();
  const initials = session.user?.name?.split(' ').map(p => p[0]).slice(0, 2).join('').toUpperCase() || 'RD';
  const csrfToken = session.csrfToken;

  return (
    <div className="app">
      <aside className="sidebar">
        <Link href="/dashboard" className="brand-logo">
          <div className="brand-mark">RDG</div>
          <div>
            <div className="brand-name">Copa RDG</div>
            <div className="brand-kicker">Bolão da Copa</div>
          </div>
        </Link>

        <nav>
          <div className="nav-section">
            <div className="nav-title">Principal</div>
            {primaryNav.map(item => (
              <Link key={item.href} href={item.href} className={`nav-item${pathname === item.href ? ' active' : ''}`}>
                <span className="nav-icon">{item.icon}</span>{item.label}
              </Link>
            ))}
          </div>
          <div className="nav-section">
            <div className="nav-title">Competição</div>
            {competitionNav.map(item => (
              <Link key={item.href} href={item.href} className={`nav-item${pathname === item.href ? ' active' : ''}`}>
                <span className="nav-icon">{item.icon}</span>{item.label}
              </Link>
            ))}
          </div>
          {session.isAdmin ? (
            <div className="nav-section">
              <div className="nav-title">Alternar área</div>
              <Link href="/admin/dashboard" className="nav-item">
                <span className="nav-icon">⇄</span>Ir para Admin
              </Link>
            </div>
          ) : null}
        </nav>

        <div className="sidebar-footer">
          <div className="user-row">
            <div className="avatar">{initials}</div>
            <div>
              <div className="user-name">{session.user?.name || 'Participante'}</div>
              <div className="user-role">Participante</div>
            </div>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginTop: 10 }}>
            <div className="status-pill"><span className="dot" />Approved</div>
            <form action="/api/auth/logout" method="POST">
              <input type="hidden" name="csrf_token" value={csrfToken} />
              <button type="submit" className="btn-ghost" style={{ fontSize: 12, padding: '5px 10px' }}>Sair</button>
            </form>
          </div>
        </div>
      </aside>

      <div className="main">
        <div className="page-breadcrumb">
          <span>Copa RDG</span>
          <span className="bc-sep">/</span>
          <span>{primaryNav.concat(competitionNav).find(n => n.href === pathname)?.label ?? 'Área do membro'}</span>
        </div>
        <div className="content">{children}</div>
      </div>
    </div>
  );
}
