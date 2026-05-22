type TeamBadgeProps = {
  name: string | null | undefined;
  flag?: string | null;
  code?: string | null;
  align?: 'left' | 'right' | 'center';
  compact?: boolean;
};

export function TeamBadge({ name, flag, code, align = 'left', compact = false }: TeamBadgeProps) {
  const displayName = name && name !== 'TBD' ? name : 'TBD';
  const displayFlag = displayName === 'TBD' ? '🏳' : flag || '🏳';

  return (
    <span className={`team-badge ${align}${compact ? ' compact' : ''}`} title={code ? `${displayName} (${code})` : displayName}>
      <span className="team-badge-flag" aria-hidden="true">{displayFlag}</span>
      <span className="team-badge-name">{displayName}</span>
    </span>
  );
}
