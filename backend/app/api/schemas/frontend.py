from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ResultsSummaryDto(BaseModel):
    model_config = ConfigDict(extra="forbid")

    totalPoints: int
    exactHits: int
    correctOutcomes: int
    brazilBonusHits: int
    championPoints: int
    topScorerPoints: int


class MemberResultMatchDto(BaseModel):
    model_config = ConfigDict(extra="forbid")

    matchId: UUID
    phase: str
    slot: str | None
    groupName: str | None
    status: str
    startsAt: datetime | None
    homeTeam: str
    homeCode: str | None
    homeIso2: str | None
    homeFlag: str
    awayTeam: str
    awayCode: str | None
    awayIso2: str | None
    awayFlag: str
    officialHomeGoals: int | None
    officialAwayGoals: int | None
    predictedHomeGoals: int | None
    predictedAwayGoals: int | None
    pointsAwarded: int | None
    involvesBrazil: bool


class MemberResultsScreenDto(BaseModel):
    model_config = ConfigDict(extra="forbid")

    summary: ResultsSummaryDto
    matches: list[MemberResultMatchDto]


class BracketMatchDto(BaseModel):
    model_config = ConfigDict(extra="forbid")

    matchId: UUID | None
    phase: str
    slot: str
    status: str
    startsAt: datetime | None
    homeTeam: str | None
    homeCode: str | None
    homeIso2: str | None
    homeFlag: str | None
    awayTeam: str | None
    awayCode: str | None
    awayIso2: str | None
    awayFlag: str | None
    officialHomeGoals: int | None
    officialAwayGoals: int | None
    winnerTeam: str | None
    feederHomeKey: str | None
    feederAwayKey: str | None
    hasManualOverride: bool


class BracketThirdPlaceSlotDto(BaseModel):
    model_config = ConfigDict(extra="forbid")

    slot: str
    assignedGroup: str | None
    assignedTeam: str | None


class MemberBracketScreenDto(BaseModel):
    model_config = ConfigDict(extra="forbid")

    championPrediction: str | None
    thirdPlaceSlots: list[BracketThirdPlaceSlotDto]
    matches: list[BracketMatchDto]


class AdminUserCountsDto(BaseModel):
    model_config = ConfigDict(extra="forbid")

    total: int
    approved: int
    pending: int
    rejected: int
    blocked: int


class SyncLogDto(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID
    provider: str
    status: str
    operation: str
    resultCode: str | None
    message: str
    createdAt: datetime


class MatchStatusCountsDto(BaseModel):
    model_config = ConfigDict(extra="forbid")

    total: int
    scheduled: int
    finished: int
    overridden: int


class AdminDashboardScreenDto(BaseModel):
    model_config = ConfigDict(extra="forbid")

    users: AdminUserCountsDto
    matches: MatchStatusCountsDto
    latestSyncs: list[SyncLogDto]
    predictionCloseAt: datetime
    exploreReleaseAt: datetime


class AdminIntegrationScreenDto(BaseModel):
    model_config = ConfigDict(extra="forbid")

    primaryProvider: str
    fallbackProvider: str
    activeProvider: str
    apiConfigured: bool
    dailyRunLimit: int
    allowedTerminalStatuses: list[str]
    autoSyncEnabled: bool
    autoSyncIntervalMinutes: int
    autoSyncIntervalOptions: list[int]
    schedulerMode: str
    cronTokenConfigured: bool
    lastAutoSyncAt: datetime | None
    nextAutoSyncAt: datetime | None
    autoSyncStatus: str
    lastSyncs: list[SyncLogDto]


class AdminMatchRowDto(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID
    phase: str
    groupName: str | None
    bracketSlot: str | None
    status: str
    startsAt: datetime | None
    venue: str | None
    homeTeam: str
    homeCode: str | None
    homeIso2: str | None
    homeFlag: str
    awayTeam: str
    awayCode: str | None
    awayIso2: str | None
    awayFlag: str
    officialHomeGoals: int | None
    officialAwayGoals: int | None
    winnerTeam: str | None
    hasManualOverride: bool
    externalProvider: str | None
    externalId: str | None
    goalScorers: list[dict[str, Any]] = Field(default_factory=list)


class AdminMatchesScreenDto(BaseModel):
    model_config = ConfigDict(extra="forbid")

    summary: MatchStatusCountsDto
    matches: list[AdminMatchRowDto]


class AdminPlayerRowDto(BaseModel):
    model_config = ConfigDict(extra="forbid")

    selectionKey: str
    selectionLabel: str
    teamCode: str | None
    teamName: str | None
    teamIso2: str | None
    teamFlag: str | None
    predictionCount: int
    pointsAwardedTotal: int
    goals: int = 0
    assists: int = 0


class AdminPlayersScreenDto(BaseModel):
    model_config = ConfigDict(extra="forbid")

    topScorerPoints: int
    leaders: list[AdminPlayerRowDto]


class AdminPhaseConfigDto(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    phaseKey: str
    label: str
    phase: str | None
    stageRound: int | None
    sortOrder: int
    firstMatchStartsAt: datetime | None
    lockAt: datetime
    exploreAt: datetime
    forceLocked: bool
    isActive: bool


class AdminSettingsScreenDto(BaseModel):
    model_config = ConfigDict(extra="forbid")

    competitionWindow: dict[str, Any]
    phaseConfigs: list[AdminPhaseConfigDto] = Field(default_factory=list)
    forceLockedPhases: int = 0
    scoring: dict[str, int]
    sync: dict[str, Any]
