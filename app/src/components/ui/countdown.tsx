'use client';
import { useEffect, useState } from 'react';

function calc(target: string) {
  const diff = Math.max(0, new Date(target).getTime() - Date.now());
  return {
    d: Math.floor(diff / 86400000),
    h: Math.floor((diff % 86400000) / 3600000),
    m: Math.floor((diff % 3600000) / 60000),
    s: Math.floor((diff % 60000) / 1000),
  };
}

export function Countdown({ closeAt, note }: { closeAt: string; note?: string }) {
  const [t, setT] = useState(calc(closeAt));
  useEffect(() => {
    const id = setInterval(() => setT(calc(closeAt)), 1000);
    return () => clearInterval(id);
  }, [closeAt]);
  const pad = (n: number) => String(n).padStart(2, '0');
  return (
    <div className="deadline-card">
      <div className="deadline-label">Fechamento dos palpites</div>
      <div className="deadline-time">
        <div className="time-box"><div className="time-num">{pad(t.d)}</div><div className="time-label">dias</div></div>
        <div className="time-box"><div className="time-num">{pad(t.h)}</div><div className="time-label">horas</div></div>
        <div className="time-box"><div className="time-num">{pad(t.m)}</div><div className="time-label">min</div></div>
        <div className="time-box"><div className="time-num">{pad(t.s)}</div><div className="time-label">seg</div></div>
      </div>
      {note && <div className="deadline-note">{note}</div>}
    </div>
  );
}
