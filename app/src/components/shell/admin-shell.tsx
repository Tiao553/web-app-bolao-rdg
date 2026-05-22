'use client';
import type { ReactNode } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import type { AppSession } from '../../lib/session';

const adminNav = [
  { href: '/admin/dashboard', label: 'Dashboard', icon: '◈' },
  { href: '/admin/users', label: 'Usuários', icon: '◎' },
  { href: '/admin/matches', label: 'Partidas', icon: '▦' },
  { href: '/admin/players', label: 'Artilheiros', icon: '★' },
  { href: '/admin/results', label: 'Resultados', icon: '◆' },
  { href: '/admin/integration', label: 'Integração', icon: '⌁' },
  { href: '/admin/settings', label: 'Configurações', icon: '⚙' },
];

export function AdminShell({ session, children }: { session: AppSession; children: ReactNode }) {
  const pathname = usePathname();
  return (
    <div className="app">
      <aside className="sidebar">
        <Link href="/admin/dashboard" className="brand-logo">
          <div className="brand-mark">RDG</div>
          <div>
            <div className="brand-name">Copa RDG</div>
            <div className="brand-kicker">Admin</div>
          </div>
        </Link>

        <nav>
          <div className="nav-section">
            <div className="nav-title">Administração</div>
            {adminNav.map(item => (
              <Link key={item.href} href={item.href} className={`nav-item${pathname === item.href ? ' active' : ''}`}>
                <span className="nav-icon">{item.icon}</span>{item.label}
              </Link>
            ))}
          </div>
        </nav>

        <div className="sidebar-footer">
          <div className="user-row">
            <div className="avatar">AD</div>
            <div>
              <div className="user-name">{session.user?.name || 'Admin'}</div>
              <div className="user-role">Governança</div>
            </div>
          </div>
        </div>
      </aside>

      <div className="main">
        <header className="topbar">
          <div>
            <div className="breadcrumbs">Copa RDG / Admin / {adminNav.find(n => n.href === pathname)?.label ?? 'Painel'}</div>
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
