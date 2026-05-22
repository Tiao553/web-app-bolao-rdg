export function ScoreGauge({ points, max, rank, label }: { points: number; max: number; rank?: number | string | null; label?: string }) {
  const pct = Math.min(1, points / max);
  const r = 46;
  const circ = 2 * Math.PI * r;
  const dash = circ * pct;
  return (
    <div className="score-wrap">
      <div className="score-gauge">
        <svg viewBox="0 0 110 110">
          <circle cx="55" cy="55" r={r} fill="none" stroke="var(--s3)" strokeWidth="10" />
          <circle cx="55" cy="55" r={r} fill="none" stroke="var(--or)" strokeWidth="10"
            strokeDasharray={`${dash} ${circ}`} strokeLinecap="round" />
        </svg>
        <div className="score-val">
          <div className="score-num">{points}</div>
          <div className="score-max">/{max} pts</div>
        </div>
      </div>
      <div className="score-meta">
        <h3>{(pct * 100).toFixed(1)}%</h3>
        <p>{label ?? 'Você está no grupo de cima do ranking.'}</p>
        {rank != null && <div className="pill orange"><span className="dot" />{rank}º lugar</div>}
      </div>
    </div>
  );
}
