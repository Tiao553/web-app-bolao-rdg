'use client';
import { useState } from 'react';

const PHASES = [
  { key: 'g1', label: 'Grupos · Rodada 1', locked: false },
  { key: 'g2', label: 'Grupos · Rodada 2', locked: false },
  { key: 'g3', label: 'Grupos · Rodada 3', locked: false },
  { key: 'r16', label: '16 avos', locked: true },
  { key: 'r8', label: 'Oitavas', locked: true },
  { key: 'qf', label: 'Quartas', locked: true },
  { key: 'sf', label: 'Semi', locked: true },
  { key: 'f', label: 'Final', locked: true },
];

export function PhaseTabs({ onPhase }: { onPhase?: (key: string) => void }) {
  const [active, setActive] = useState('g1');
  return (
    <div className="phase-tabs">
      {PHASES.map(p => (
        <button
          key={p.key}
          type="button"
          className={`phase-tab${p.locked ? ' locked' : ''}${active === p.key ? ' active' : ''}`}
          disabled={p.locked}
          onClick={() => { if (!p.locked) { setActive(p.key); onPhase?.(p.key); } }}
        >
          {!p.locked && <span className="dot" />}
          {p.label}
        </button>
      ))}
    </div>
  );
}
