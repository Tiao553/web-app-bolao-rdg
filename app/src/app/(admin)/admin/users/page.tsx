import { ResetPasswordBtn } from '../../../../components/admin/reset-password-btn';
import type { AdminUserContract } from '../../../../lib/contracts';
import { fetchBackendData } from '../../../../lib/session';
import { getServerCsrfToken } from '../../../../lib/security';
import Link from 'next/link';

const statusPill: Record<string, string> = {
  APPROVED: 'ok', PENDING: 'warn', REJECTED: 'neutral', BLOCKED: 'neutral',
};
const statusLabel: Record<string, string> = {
  APPROVED: 'Aprovado', PENDING: 'Pendente', REJECTED: 'Rejeitado', BLOCKED: 'Bloqueado',
};

function initials(name: string): string {
  return name.split(' ').slice(0, 2).map(w => w[0]).join('').toUpperCase();
}

export default async function AdminUsersPage({ searchParams }: { searchParams?: Promise<Record<string, string | string[] | undefined>> }) {
  const params = searchParams ? await searchParams : {};
  const csrfToken = await getServerCsrfToken();
  const scopeParam = typeof params.scope === 'string' ? params.scope : undefined;
  const scope = scopeParam === 'deleted' ? 'deleted' : 'active';
  const { data } = await fetchBackendData<AdminUserContract[]>(`/api/admin/users?scope=${scope}`);
  const users = data ?? [];
  const pending = users.filter(u => u.access_status === 'PENDING');
  const approved = users.filter(u => u.access_status === 'APPROVED');
  const showingDeleted = scope === 'deleted';
  const headlineCount = showingDeleted ? users.length : approved.length;

  return (
    <>
      {/* Hero */}
      <section className="hero">
        <div className="hero-content">
          <div>
            <div className="eyebrow"><span className="dot" />Gestão de acesso</div>
            <h1>Usuários do <span>bolão</span>.</h1>
            <p>{showingDeleted
              ? 'Consulte contas inativadas pelo soft delete. Elas ficam fora da lista principal e perdem acesso ao sistema.'
              : 'Aprove, rejeite, bloqueie ou inative participantes. Apenas usuários aprovados e ativos aparecem no ranking e podem fazer palpites.'}</p>
          </div>
          <div style={{ display: 'flex', gap: 12 }}>
            <div className="match-health" style={{ minWidth: 120 }}>
              <div className="health-num">{pending.length}</div>
              <div className="health-label" style={{ color: 'var(--am)', borderColor: 'rgba(245,158,11,.24)' }}>
                {showingDeleted ? 'pendentes hist.' : 'pendentes'}
              </div>
            </div>
            <div className="health-card" style={{ minWidth: 120 }}>
              <div className="health-label">{showingDeleted ? 'deletados' : 'aprovados'}</div>
              <div style={{ fontSize: 52, fontWeight: 900, color: 'var(--g5)', lineHeight: 1 }}>{headlineCount}</div>
            </div>
          </div>
        </div>
      </section>

      {/* Users table */}
      <div className="card">
        <div className="card-header">
          <div><div className="card-title">Lista de usuários</div><div className="card-subtitle">Todos os cadastros</div></div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10, flexWrap: 'wrap', justifyContent: 'flex-end' }}>
            <Link href="/admin/users" className={`pill ${showingDeleted ? 'neutral' : 'orange'}`} style={{ textDecoration: 'none' }}>
              <span className="dot" />Ativos
            </Link>
            <Link href="/admin/users?scope=deleted" className={`pill ${showingDeleted ? 'orange' : 'neutral'}`} style={{ textDecoration: 'none' }}>
              <span className="dot" />Deletados
            </Link>
            <div className={`pill ${pending.length > 0 && !showingDeleted ? 'warn' : 'ok'}`}><span className="dot" />{users.length} total</div>
          </div>
        </div>
        <div className="card-body">
          {/* Header row */}
          <div className="users-table">
            <div className="user-table-row header">
              <div className="th" />
              <div className="th">Nome</div>
              <div className="th">Email</div>
              <div className="th">Status</div>
              <div className="th">Admin</div>
              <div className="th">Ações</div>
            </div>

            {users.map(u => (
              <div key={u.id} className="user-table-row">
                <div className="avatar">{initials(u.full_name)}</div>
                <div>
                  <div className="user-full-name">{u.full_name}</div>
                  <div className="user-date">{new Date(u.created_at).toLocaleDateString('pt-BR')}</div>
                </div>
                <div className="user-email">{u.email}</div>
                <div>
                  <div className={`pill ${showingDeleted ? 'neutral' : (statusPill[u.access_status] ?? 'neutral')}`}>
                    <span className="dot" />{showingDeleted ? 'Inativo' : (statusLabel[u.access_status] ?? u.access_status)}
                  </div>
                </div>
                <div>{u.is_admin ? <div className="pill orange"><span className="dot" />Sim</div> : <span style={{ color: 'var(--tx3)', fontSize: 12 }}>—</span>}</div>
                <div className="row-actions" style={{ gap: 6 }}>
                  {!showingDeleted ? (
                    <>
                      {u.access_status !== 'APPROVED' && (
                        <form action={`/api/admin/users/${u.id}/approve`} method="POST" style={{ display: 'inline' }}>
                          <input type="hidden" name="csrf_token" value={csrfToken} />
                          <button type="submit" className="btn-ok" style={{ height: 32, fontSize: 11, padding: '0 10px' }}>Aprovar</button>
                        </form>
                      )}
                      {u.access_status !== 'REJECTED' && (
                        <form action={`/api/admin/users/${u.id}/reject`} method="POST" style={{ display: 'inline' }}>
                          <input type="hidden" name="csrf_token" value={csrfToken} />
                          <button type="submit" className="btn-danger" style={{ height: 32, fontSize: 11, padding: '0 10px' }}>Rejeitar</button>
                        </form>
                      )}
                      <form action={`/api/admin/users/${u.id}/toggle-admin`} method="POST" style={{ display: 'inline' }}>
                        <input type="hidden" name="csrf_token" value={csrfToken} />
                        <input type="hidden" name="is_admin" value={u.is_admin ? 'false' : 'true'} />
                        <input type="hidden" name="access_status" value={u.access_status} />
                        <button type="submit" className={u.is_admin ? 'btn-danger' : 'btn-ok'} style={{ height: 32, fontSize: 11, padding: '0 10px' }}>
                          {u.is_admin ? 'Remover Admin' : 'Tornar Admin'}
                        </button>
                      </form>
                      <form action={`/api/admin/users/${u.id}/soft-delete`} method="POST" style={{ display: 'inline' }}>
                        <input type="hidden" name="csrf_token" value={csrfToken} />
                        <input type="hidden" name="scope" value={scope} />
                        <button type="submit" className="btn-danger" style={{ height: 32, fontSize: 11, padding: '0 10px' }}>
                          Deletar
                        </button>
                      </form>
                      <ResetPasswordBtn userId={u.id} userName={u.full_name} csrfToken={csrfToken} />
                    </>
                  ) : (
                    <span style={{ color: 'var(--tx3)', fontSize: 12 }}>Visível apenas no filtro de deletados.</span>
                  )}
                </div>
              </div>
            ))}

            {users.length === 0 && (
              <div style={{ textAlign: 'center', padding: '32px', color: 'var(--tx3)', fontSize: 14 }}>
                {showingDeleted ? 'Nenhum usuário deletado encontrado.' : 'Nenhum usuário cadastrado ainda.'}
              </div>
            )}
          </div>
        </div>
      </div>
    </>
  );
}
