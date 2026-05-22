type TeamBadgeProps = {
  name: string | null | undefined;
  flag?: string | null;
  iso2?: string | null;
  code?: string | null;
  align?: 'left' | 'right' | 'center';
  compact?: boolean;
};

export function TeamBadge({ name, flag, iso2, code, align = 'left', compact = false }: TeamBadgeProps) {
  const displayName = name && name !== 'TBD' ? name : 'TBD';

  const flagContent = (() => {
    if (displayName === 'TBD') {
      return <span className="team-badge-flag" aria-hidden="true">🏳</span>;
    }
    const normalizedIso2 = iso2?.trim().toUpperCase();
    if (normalizedIso2) {
      // Support both 2-char (BR) and regional (GB-SCT, GB-ENG) codes
      const isSimple = normalizedIso2.length === 2 && /^[A-Z]{2}$/.test(normalizedIso2);
      const isRegional = /^[A-Z]{2}-[A-Z]{2,3}$/.test(normalizedIso2);
      if (isSimple || isRegional) {
        const slug = normalizedIso2.toLowerCase();
        return (
          <img
            src={`https://flagcdn.com/24x18/${slug}.png`}
            srcSet={`https://flagcdn.com/48x36/${slug}.png 2x`}
            width={compact ? 18 : 22}
            height={compact ? 14 : 17}
            alt={displayName}
            className="team-badge-img"
            loading="lazy"
          />
        );
      }
    }
    return <span className="team-badge-flag" aria-hidden="true">{flag || '🏳'}</span>;
  })();

  return (
    <span className={`team-badge ${align}${compact ? ' compact' : ''}`} title={code ? `${displayName} (${code})` : displayName}>
      {flagContent}
      <span className="team-badge-name">{displayName}</span>
    </span>
  );
}
