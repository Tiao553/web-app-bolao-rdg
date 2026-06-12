import type { SessionPayload } from './api-client';

export type SessionContract = SessionPayload;

export type MemberCompetitionWindowContract = {
  predictionCloseAt: string;
  exploreReleaseAt: string;
  predictionLocked: boolean;
  exploreReleased: boolean;
};

export type PhaseMatchContract = {
  id: string;
  homeTeam: string;
  awayTeam: string;
  homeCode: string | null;
  homeIso2: string | null;
  homeFlag: string;
  awayCode: string | null;
  awayIso2: string | null;
  awayFlag: string;
  groupName: string | null;
  startsAt: string;
  involvesBrazil: boolean;
  status: string;
  officialHomeGoals: number | null;
  officialAwayGoals: number | null;
  predictedHomeGoals: number | null;
  predictedAwayGoals: number | null;
  pointsAwarded: number | null;
};

export type PhaseRoundContract = {
  key: string;
  label: string;
  phase: string;
  stageRound: number | null;
  locked: boolean;
  exploreOpen: boolean;
  lockTime: string | null;
  matches: PhaseMatchContract[];
};

export type PhaseScreenContract = {
  rounds: PhaseRoundContract[];
};

export type GroupStandingEntryContract = {
  teamCode: string;
  teamName: string;
  teamIso2: string | null;
  teamFlag: string;
  played: number;
  won: number;
  drawn: number;
  lost: number;
  goalsFor: number;
  goalsAgainst: number;
  goalDiff: number;
  points: number;
};

export type GroupStandingContract = {
  group: string;
  entries: GroupStandingEntryContract[];
};

export type StandingsContract = {
  groups: GroupStandingContract[];
};

export type NextMatchContract = {
  id: string;
  homeTeam: string;
  homeCode: string | null;
  homeIso2: string | null;
  homeFlag: string;
  awayTeam: string;
  awayCode: string | null;
  awayIso2: string | null;
  awayFlag: string;
  startsAt: string;
  involvesBrazil: boolean;
};

export type MemberDashboardContract = {
  user: {
    id: string;
    email: string;
    name: string;
    accessStatus: string;
    isAdmin: boolean;
  };
  competition: MemberCompetitionWindowContract;
  nextLockAt: string | null;
  rankingPosition: number | null;
  totalPoints: number;
  savedMatchPredictions: number;
  savedBonusPredictions: number;
  nextMatches: NextMatchContract[];
};

export type MatchPredictionContract = {
  id: string;
  matchId: string;
  homeGoals: number;
  awayGoals: number;
  pointsAwarded: number | null;
  lockedAt: string | null;
};

export type CompetitionPredictionContract = {
  id: string;
  predictionType: 'CHAMPION' | 'TOP_SCORER';
  selectionKey: string;
  selectionLabel: string;
  pointsAwarded: number | null;
  lockedAt: string | null;
};

export type MemberPredictionsContract = {
  competition: MemberCompetitionWindowContract;
  matchPredictions: MatchPredictionContract[];
  competitionPredictions: CompetitionPredictionContract[];
};

export type RankingRowContract = {
  rank: number;
  userId: string;
  fullName: string;
  totalPoints: number;
  matchPoints: number;
  bonusPoints: number;
};

export type RankingContract = {
  rows: RankingRowContract[];
  currentUserRank: number | null;
};

export type ExploreMatchPredictionContract = {
  userId: string;
  userName: string;
  matchId: string;
  phase: string;
  stageRound: number | null;
  groupName: string | null;
  startsAt: string | null;
  status: string;
  homeTeam: string;
  homeCode: string | null;
  homeIso2: string | null;
  homeFlag: string;
  awayTeam: string;
  awayCode: string | null;
  awayIso2: string | null;
  awayFlag: string;
  homeGoals: number;
  awayGoals: number;
  pointsAwarded: number | null;
};

export type ExploreCompetitionPredictionContract = {
  userId: string;
  userName: string;
  predictionType: 'CHAMPION' | 'TOP_SCORER';
  selectionKey: string;
  selectionLabel: string;
  selectionTeamCode: string | null;
  selectionTeamName: string | null;
  selectionTeamIso2: string | null;
  selectionTeamFlag: string | null;
  pointsAwarded: number | null;
};

export type ExploreContract = {
  exploreReleased: boolean;
  matchPredictions: ExploreMatchPredictionContract[];
  competitionPredictions: ExploreCompetitionPredictionContract[];
};

export type AdminUserContract = {
  id: string;
  email: string;
  full_name: string;
  access_status: 'PENDING' | 'APPROVED' | 'REJECTED' | 'BLOCKED';
  is_admin: boolean;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  last_login_at: string | null;
};

export type AdminCompetitionWindowContract = {
  id: string;
  name: string;
  prediction_close_at: string;
  explore_release_at: string;
  is_active: boolean;
};

export type AdminPhaseConfigContract = {
  id: string;
  phaseKey: string;
  label: string;
  phase: string | null;
  stageRound: number | null;
  sortOrder: number;
  firstMatchStartsAt: string | null;
  lockAt: string;
  exploreAt: string;
  forceLocked: boolean;
  isActive: boolean;
};

export type AdminSyncRunContract = {
  provider: string;
  status: string;
  operation: string;
  message: string;
  recalculation: {
    matchesProcessed?: number;
    predictionsUpdated?: number;
    rankingEntries?: number;
  } | null;
};

export type MemberResultMatchContract = {
  matchId: string;
  phase: string;
  slot: string | null;
  groupName: string | null;
  status: string;
  startsAt: string | null;
  homeTeam: string;
  homeCode: string | null;
  homeIso2: string | null;
  homeFlag: string;
  awayTeam: string;
  awayCode: string | null;
  awayIso2: string | null;
  awayFlag: string;
  officialHomeGoals: number | null;
  officialAwayGoals: number | null;
  predictedHomeGoals: number | null;
  predictedAwayGoals: number | null;
  pointsAwarded: number | null;
  involvesBrazil: boolean;
};

export type MemberResultsContract = {
  summary: {
    totalPoints: number;
    exactHits: number;
    correctOutcomes: number;
    brazilBonusHits: number;
    championPoints: number;
    topScorerPoints: number;
  };
  matches: MemberResultMatchContract[];
};

export type BracketMatchContract = {
  matchId: string | null;
  phase: string;
  slot: string;
  startsAt: string | null;
  homeTeam: string | null;
  homeCode: string | null;
  homeIso2: string | null;
  homeFlag: string | null;
  awayTeam: string | null;
  awayCode: string | null;
  awayIso2: string | null;
  awayFlag: string | null;
  winnerTeam: string | null;
  feederHomeKey: string | null;
  feederAwayKey: string | null;
  hasManualOverride: boolean;
};

export type MemberBracketContract = {
  championPrediction: string | null;
  thirdPlaceSlots: Array<{
    slot: string;
    assignedGroup: string | null;
    assignedTeam: string | null;
  }>;
  matches: BracketMatchContract[];
};

export type AdminDashboardContract = {
  users: {
    total: number;
    approved: number;
    pending: number;
    rejected: number;
    blocked: number;
  };
  matches: {
    total: number;
    scheduled: number;
    finished: number;
    overridden: number;
  };
  latestSyncs: Array<{
    id: string;
    provider: string;
    status: string;
    operation: string;
    resultCode: string | null;
    message: string;
    createdAt: string;
  }>;
  predictionCloseAt: string;
  exploreReleaseAt: string;
};

export type AdminIntegrationContract = {
  primaryProvider: string;
  fallbackProvider: string;
  activeProvider: string;
  apiConfigured: boolean;
  dailyRunLimit: number;
  allowedTerminalStatuses: string[];
  autoSyncEnabled: boolean;
  autoSyncIntervalMinutes: number;
  autoSyncIntervalOptions: number[];
  schedulerMode: string;
  cronTokenConfigured: boolean;
  lastAutoSyncAt: string | null;
  nextAutoSyncAt: string | null;
  autoSyncStatus: string;
  lastSyncs: Array<{
    id: string;
    provider: string;
    status: string;
    operation: string;
    resultCode: string | null;
    message: string;
    createdAt: string;
  }>;
};

export type AdminMatchRowContract = {
  id: string;
  phase: string;
  groupName: string | null;
  bracketSlot: string | null;
  status: string;
  startsAt: string | null;
  venue: string | null;
  homeTeam: string;
  homeCode: string | null;
  homeIso2: string | null;
  homeFlag: string;
  awayTeam: string;
  awayCode: string | null;
  awayIso2: string | null;
  awayFlag: string;
  officialHomeGoals: number | null;
  officialAwayGoals: number | null;
  winnerTeam: string | null;
  hasManualOverride: boolean;
  externalProvider: string | null;
  externalId: string | null;
  goalScorers: { name: string; team: string | null; goals: number }[];
};

export type AdminMatchesContract = {
  summary: {
    total: number;
    scheduled: number;
    finished: number;
    overridden: number;
  };
  matches: AdminMatchRowContract[];
};

export type AdminPlayersContract = {
  topScorerPoints: number;
  leaders: Array<{
    selectionKey: string;
    selectionLabel: string;
    teamCode: string | null;
    teamName: string | null;
    teamIso2: string | null;
    teamFlag: string | null;
    predictionCount: number;
    pointsAwardedTotal: number;
    goals: number;
    assists: number;
  }>;
};

export type AvailableTeamContract = {
  code: string;
  name: string;
  flag: string;
  iso2?: string | null;
  group: string;
  confederation: string;
};

export type AvailableTeamsContract = {
  teams: AvailableTeamContract[];
};

export type AvailablePlayerContract = {
  id: string;
  name: string;
  teamCode: string;
  position: string;
  shirtNumber: number;
  club: string;
  nationality: string;
};

export type AvailablePlayersContract = {
  players: AvailablePlayerContract[];
};

export type AdminSettingsContract = {
  competitionWindow: AdminCompetitionWindowContract;
  phaseConfigs: AdminPhaseConfigContract[];
  forceLockedPhases: number;
  scoring: {
    exact_points: number;
    result_points: number;
    brazil_multiplier: number;
    champion_points: number;
    top_scorer_points: number;
  };
  sync: {
    post_match_offset_minutes: number;
    allowed_terminal_statuses: string[];
    max_runs_per_day: number;
  };
};
