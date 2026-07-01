import type { CSSProperties } from 'react';

import { TeamBadge } from '../../../components/ui/team-badge';
import type { BracketMatchContract, MemberBracketContract } from '../../../lib/contracts';
import { fetchBackendData } from '../../../lib/session';

const ROUND_CONFIG = [
  { phase: 'ROUND_OF_32', label: '16 avos' },
  { phase: 'ROUND_OF_16', label: 'Oitavas' },
  { phase: 'QUARTER_FINAL', label: 'Quartas' },
  { phase: 'SEMI_FINAL', label: 'Semifinal' },
  { phase: 'FINAL', label: 'Final' },
] as const;

const FINISHED_STATUSES = new Set(['FT', 'AET', 'PEN', 'FINISHED']);
const COLUMN_WIDTH = 220;
const COLUMN_GAP = 72;
const ROW_HEIGHT = 53;

type BracketRound = {
  phase: string;
  label: string;
  matches: BracketMatchContract[];
};

type PositionedMatch = {
  match: BracketMatchContract;
  roundIndex: number;
  rowStart: number;
  rowSpan: number;
  centerY: number;
};

function slotNumber(slot: string): number {
  const value = Number(slot.replace(/\D/g, ''));
  return Number.isFinite(value) ? value : Number.MAX_SAFE_INTEGER;
}

function sortBySlot(left: BracketMatchContract, right: BracketMatchContract): number {
  return slotNumber(left.slot) - slotNumber(right.slot) || left.slot.localeCompare(right.slot);
}

function buildMatchLookup(matches: BracketMatchContract[]): Map<string, BracketMatchContract> {
  return new Map(matches.map((match) => [match.slot, match]));
}

function feederToSlot(feederKey: string | null): string | null {
  if (!feederKey?.startsWith('W')) {
    return null;
  }
  return `M${feederKey.slice(1)}`;
}

function collectLeafSlots(
  slot: string,
  lookup: Map<string, BracketMatchContract>,
  visited = new Set<string>()
): string[] {
  if (visited.has(slot)) {
    return [];
  }
  visited.add(slot);

  const match = lookup.get(slot);
  if (!match) {
    return [slot];
  }

  const sourceSlots = [match.feederHomeKey, match.feederAwayKey]
    .map(feederToSlot)
    .filter((sourceSlot): sourceSlot is string => Boolean(sourceSlot));

  if (sourceSlots.length === 0) {
    return [slot];
  }

  const leaves = sourceSlots.flatMap((sourceSlot) => collectLeafSlots(sourceSlot, lookup, new Set(visited)));
  return leaves.length > 0 ? leaves : [slot];
}

function buildLeafOrder(matches: BracketMatchContract[], lookup: Map<string, BracketMatchContract>): Map<string, number> {
  const final = matches.find((match) => match.phase === 'FINAL') ?? matches.find((match) => match.slot === 'M104');
  const fallbackLeaves = matches
    .filter((match) => match.phase === 'ROUND_OF_32')
    .sort(sortBySlot)
    .map((match) => match.slot);
  const leaves = final ? collectLeafSlots(final.slot, lookup) : fallbackLeaves;
  const orderedLeaves = leaves.length > 0 ? leaves : fallbackLeaves;
  const order = new Map<string, number>();

  orderedLeaves.forEach((slot) => {
    if (!order.has(slot)) {
      order.set(slot, order.size);
    }
  });

  return order;
}

function visualRank(
  match: BracketMatchContract,
  lookup: Map<string, BracketMatchContract>,
  leafOrder: Map<string, number>
): number {
  const ownRank = leafOrder.get(match.slot);
  if (ownRank !== undefined) {
    return ownRank;
  }

  const sourceRanks = collectLeafSlots(match.slot, lookup)
    .map((slot) => leafOrder.get(slot))
    .filter((rank): rank is number => rank !== undefined);

  if (sourceRanks.length === 0) {
    return slotNumber(match.slot);
  }

  return sourceRanks.reduce((total, rank) => total + rank, 0) / sourceRanks.length;
}

function buildRounds(matches: BracketMatchContract[]): BracketRound[] {
  const lookup = buildMatchLookup(matches);
  const leafOrder = buildLeafOrder(matches, lookup);

  return ROUND_CONFIG.map(({ phase, label }) => ({
    phase,
    label,
    matches: matches
      .filter((match) => match.phase === phase)
      .sort((left, right) => {
        const visualDiff = visualRank(left, lookup, leafOrder) - visualRank(right, lookup, leafOrder);
        return visualDiff || sortBySlot(left, right);
      }),
  })).filter((round) => round.matches.length > 0);
}

function buildPositionMap(rounds: BracketRound[], baseRows: number): Map<string, PositionedMatch> {
  const positions = new Map<string, PositionedMatch>();
  rounds.forEach((round, roundIndex) => {
    const rowSpan = baseRows / round.matches.length;
    round.matches.forEach((match, matchIndex) => {
      const rowStart = matchIndex * rowSpan + 1;
      positions.set(match.slot, {
        match,
        roundIndex,
        rowStart,
        rowSpan,
        centerY: (rowStart - 1 + rowSpan / 2) * ROW_HEIGHT,
      });
    });
  });
  return positions;
}

function formatKickoff(startsAt: string | null): string {
  if (!startsAt) {
    return 'A definir';
  }
  const parsed = Date.parse(startsAt);
  if (Number.isNaN(parsed)) {
    return 'A definir';
  }
  return new Intl.DateTimeFormat('pt-BR', {
    day: '2-digit',
    month: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  }).format(parsed);
}

function normalizeLabel(value: string | null): string | null {
  if (!value) {
    return null;
  }
  return value
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .replace(/[^a-zA-Z0-9]/g, '')
    .toLowerCase() || null;
}

function isWinner(match: BracketMatchContract, side: 'home' | 'away'): boolean {
  const homeGoals = match.officialHomeGoals;
  const awayGoals = match.officialAwayGoals;
  if (
    FINISHED_STATUSES.has(match.status)
    && homeGoals !== null
    && awayGoals !== null
    && homeGoals !== awayGoals
  ) {
    return side === 'home' ? homeGoals > awayGoals : awayGoals > homeGoals;
  }

  const winner = normalizeLabel(match.winnerTeam);
  if (winner === null) {
    return false;
  }

  const code = normalizeLabel(side === 'home' ? match.homeCode : match.awayCode);
  const name = normalizeLabel(side === 'home' ? match.homeTeam : match.awayTeam);
  return winner === code || winner === name;
}

function BracketConnectorLayer({
  rounds,
  positions,
  width,
  height,
}: {
  rounds: BracketRound[];
  positions: Map<string, PositionedMatch>;
  width: number;
  height: number;
}) {
  const paths: Array<{ id: string; d: string }> = [];
  const columnStep = COLUMN_WIDTH + COLUMN_GAP;

  rounds.forEach((round) => {
    round.matches.forEach((match) => {
      const target = positions.get(match.slot);
      if (!target || target.roundIndex === 0) {
        return;
      }

      [match.feederHomeKey, match.feederAwayKey].forEach((feederKey) => {
        const sourceSlot = feederToSlot(feederKey);
        const source = sourceSlot ? positions.get(sourceSlot) : null;
        if (!source) {
          return;
        }

        const sourceX = source.roundIndex * columnStep + COLUMN_WIDTH;
        const targetX = target.roundIndex * columnStep;
        const midX = sourceX + (targetX - sourceX) / 2;
        paths.push({
          id: `${source.match.slot}-${match.slot}-${feederKey}`,
          d: `M ${sourceX} ${source.centerY} H ${midX} V ${target.centerY} H ${targetX}`,
        });
      });
    });
  });

  return (
    <svg
      className="bracket-connectors"
      width={width}
      height={height}
      viewBox={`0 0 ${width} ${height}`}
      aria-hidden="true"
    >
      {paths.map((path) => (
        <path key={path.id} d={path.d} />
      ))}
    </svg>
  );
}

function BracketTeamRow({
  match,
  side,
}: {
  match: BracketMatchContract;
  side: 'home' | 'away';
}) {
  const teamName = side === 'home' ? match.homeTeam : match.awayTeam;
  const teamFlag = side === 'home' ? match.homeFlag : match.awayFlag;
  const teamIso2 = side === 'home' ? match.homeIso2 : match.awayIso2;
  const teamCode = side === 'home' ? match.homeCode : match.awayCode;
  const goals = side === 'home' ? match.officialHomeGoals : match.officialAwayGoals;
  const winner = isWinner(match, side);

  return (
    <div className={`bracket-team-row${winner ? ' winner' : ''}${teamName ? '' : ' empty'}`}>
      <TeamBadge name={teamName ?? 'TBD'} flag={teamFlag} iso2={teamIso2} code={teamCode} compact />
      <div className="bracket-score">{goals ?? ''}</div>
    </div>
  );
}

function BracketMatchCard({ match }: { match: BracketMatchContract }) {
  const isFinished = FINISHED_STATUSES.has(match.status);

  return (
    <article className={`bracket-match-card${isFinished ? ' finished' : ''}`}>
      <header className="bracket-match-header">
        <span>{formatKickoff(match.startsAt)}</span>
        {isFinished ? <span className="bracket-status">FIM</span> : <span>{match.slot}</span>}
      </header>
      <div className="bracket-match-teams">
        <BracketTeamRow match={match} side="home" />
        <BracketTeamRow match={match} side="away" />
      </div>
    </article>
  );
}

function BracketBoard({ matches }: { matches: BracketMatchContract[] }) {
  const rounds = buildRounds(matches);
  if (rounds.length === 0) {
    return (
      <div className="bracket-empty">
        O chaveamento será gerado automaticamente após a fase de grupos.
      </div>
    );
  }

  const baseRows = Math.max(2, (rounds[0]?.matches.length ?? 1) * 2);
  const positions = buildPositionMap(rounds, baseRows);
  const boardWidth = rounds.length * COLUMN_WIDTH + Math.max(0, rounds.length - 1) * COLUMN_GAP;
  const boardHeight = baseRows * ROW_HEIGHT;
  const boardStyle = {
    '--bracket-columns': rounds.length,
    '--bracket-rows': baseRows,
    '--bracket-row-height': `${ROW_HEIGHT}px`,
    '--bracket-column-width': `${COLUMN_WIDTH}px`,
    '--bracket-column-gap': `${COLUMN_GAP}px`,
    width: `${boardWidth}px`,
  } as CSSProperties;
  const canvasStyle = {
    height: `${boardHeight}px`,
  } as CSSProperties;

  return (
    <div className="bracket-wrapper">
      <div className="bracket-board" style={boardStyle}>
        <div className="bracket-round-labels">
          {rounds.map((round) => (
            <div key={round.phase} className="bracket-round-label">
              {round.label}
            </div>
          ))}
        </div>
        <div className="bracket-canvas" style={canvasStyle}>
          <BracketConnectorLayer rounds={rounds} positions={positions} width={boardWidth} height={boardHeight} />
          <div className="bracket-rounds">
            {rounds.map((round) => (
              <section key={round.phase} className="bracket-round-column" aria-label={round.label}>
                {round.matches.map((match) => {
                  const position = positions.get(match.slot);
                  return (
                    <div
                      key={match.slot}
                      className="bracket-match-slot"
                      style={{ gridRow: position ? `${position.rowStart} / span ${position.rowSpan}` : undefined }}
                    >
                      <BracketMatchCard match={match} />
                    </div>
                  );
                })}
              </section>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

export default async function BracketPage() {
  const { data } = await fetchBackendData<MemberBracketContract>('/api/member/bracket');
  const matches = data?.matches ?? [];

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
          <div>
            <div className="card-title">Árvore eliminatória</div>
            <div className="card-subtitle">sequencial · resultados oficiais</div>
          </div>
          <div className="pill orange"><span className="dot" />oficial</div>
        </div>
        <div className="card-body bracket-card-body">
          <BracketBoard matches={matches} />
        </div>
      </div>
    </>
  );
}
