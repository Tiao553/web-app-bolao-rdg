import type { MemberBracketContract } from '../../../lib/contracts';
import { fetchBackendData } from '../../../lib/session';

export default async function BracketPage() {
  const { data } = await fetchBackendData<MemberBracketContract>('/api/member/bracket');
  const matches = data?.matches ?? [];

  const phases = ['R16', 'QF', 'SF', 'F'];
  const phaseLabel: Record<string, string> = { R16: '16 avos', QF: 'Oitavas', SF: 'Quartas', F: 'Semi/Final' };

  return (
    <>
      <section className="hero">
        <div className="hero-content">
          <div>
            <div className="eyebrow"><span className="dot" />Mata-mata oficial</div>
            <h1>Chaveamento da Copa com <span>16 avos</span>.</h1>
            <p>Árvore eliminatória oficial. Os resultados vêm do backend — palpites não alteram o chaveamento.</p>
          </div>
          <div className="deadline-card" style={{ minWidth: 200 }}>
            <div className="deadline-label">Seu palpite</div>
            <div style={{ fontSize: 14, fontWeight: 800, marginTop: 8 }}>{data?.championPrediction ?? 'Não definido'}</div>
            <div style={{ fontSize: 11, color: 'var(--tx3)', marginTop: 4 }}>campeão escolhido</div>
          </div>
        </div>
      </section>

      <div className="card">
        <div className="card-header">
          <div><div className="card-title">Árvore eliminatória</div><div className="card-subtitle">SVG conectado · vencedores destacados</div></div>
          <div className="pill orange"><span className="dot" />oficial</div>
        </div>
        <div className="card-body">
          {matches.length === 0 ? (
            <div style={{ textAlign: 'center', padding: 40, color: 'var(--tx3)', fontSize: 14 }}>O chaveamento será gerado automaticamente após a fase de grupos.</div>
          ) : (
            <div className="bracket-wrapper">
              <div style={{ display: 'flex', gap: 24, minWidth: 800 }}>
                {phases.map(ph => {
                  const phMatches = matches.filter(m => m.phase === ph);
                  if (phMatches.length === 0) return null;
                  return (
                    <div key={ph} style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: 12 }}>
                      <div style={{ fontFamily: 'Fira Code', fontSize: 10, color: 'var(--tx3)', textTransform: 'uppercase', letterSpacing: '.12em', marginBottom: 4 }}>{phaseLabel[ph] ?? ph}</div>
                      {phMatches.map(m => (
                        <div key={m.slot} style={{ border: `1px solid ${m.winnerTeam ? 'var(--or-r)' : 'var(--bd)'}`, borderRadius: 14, background: 'var(--s2)', overflow: 'hidden' }}>
                          <div style={{ padding: '8px 12px', background: 'var(--s3)', fontFamily: 'Fira Code', fontSize: 10, color: 'var(--tx3)', textTransform: 'uppercase' }}>{m.slot}</div>
                          <div style={{ padding: '10px 12px', display: 'flex', flexDirection: 'column', gap: 6 }}>
                            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', fontSize: 13, fontWeight: m.winnerTeam === m.homeTeam ? 800 : 400, color: m.winnerTeam === m.homeTeam ? 'var(--or)' : 'var(--tx2)' }}>
                              <span>{m.homeTeam ?? 'TBD'}</span>
                            </div>
                            <div style={{ height: 1, background: 'var(--bd)' }} />
                            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', fontSize: 13, fontWeight: m.winnerTeam === m.awayTeam ? 800 : 400, color: m.winnerTeam === m.awayTeam ? 'var(--or)' : 'var(--tx2)' }}>
                              <span>{m.awayTeam ?? 'TBD'}</span>
                            </div>
                          </div>
                          {m.winnerTeam && <div style={{ padding: '6px 12px', background: 'var(--or-g)', borderTop: '1px solid var(--or-r)', fontSize: 11, color: 'var(--or)', fontFamily: 'Fira Code' }}>✓ {m.winnerTeam}</div>}
                        </div>
                      ))}
                    </div>
                  );
                })}
              </div>
            </div>
          )}
        </div>
      </div>

      {data?.thirdPlaceSlots && data.thirdPlaceSlots.length > 0 && (
        <div className="card">
          <div className="card-header"><div><div className="card-title">Governança</div><div className="card-subtitle">Alocação de terceiros colocados</div></div></div>
          <div className="card-body">
            <div className="table-list">
              {data.thirdPlaceSlots.map(s => (
                <div key={s.slot} className="player-row">
                  <div className="player-pos">{s.slot}</div>
                  <div className="player-name">{s.assignedGroup ?? 'TBD'}</div>
                  <div className="player-stat">{s.assignedTeam ?? '—'}</div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </>
  );
}
