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
        </nav>

        <div className="sidebar-footer">
          <div className="user-row">
            <div className="avatar">{initials}</div>
            <div>
              <div className="user-name">{session.user?.name || 'Participante'}</div>
              <div className="user-role">Participante</div>
            </div>
          </div>
          <div className="status-pill"><span className="dot" />Approved</div>
        </div>
      </aside>

      <div className="main">
        <header className="topbar">
          <div>
            <div className="breadcrumbs">Copa RDG / {primaryNav.concat(competitionNav).find(n => n.href === pathname)?.label ?? 'Área do membro'}</div>
          </div>
          <div className="top-actions">
            <form action="/api/auth/logout" method="POST">
              <button type="submit" className="btn-ghost">Sair</button>
            </form>
          </div>
        </header>
        <div className="content">{children}</div>
      </div>
    </div>
  );
}
