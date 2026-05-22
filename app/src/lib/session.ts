import { cookies } from 'next/headers';

import {
  getServerJson,
  type SessionAccessStatus,
  type SessionPayload,
  type SessionUserPayload,
  type SessionWindowPayload
} from "./api-client";

export type AccessStatus = SessionAccessStatus;

export type AppSessionUser = SessionUserPayload;

export type SessionWindows = {
  predictionCloseAt: string | null;
  exploreReleaseAt: string | null;
};

export type AppSession = {
  authenticated: boolean;
  user: AppSessionUser | null;
  accessStatus: AccessStatus | null;
  isAdmin: boolean;
  competition: SessionWindows;
  now: string | null;
};

export type SessionViewState =
  | "anonymous"
  | "pending"
  | "approved"
  | "rejected"
  | "blocked";

export type FetchResult<T> = {
  data: T | null;
  error: string | null;
};

function normalizeWindows(competition?: SessionWindowPayload | null): SessionWindows {
  return {
    predictionCloseAt: competition?.predictionCloseAt ?? null,
    exploreReleaseAt: competition?.exploreReleaseAt ?? null
  };
}

export function normalizeSession(payload: SessionPayload | null): AppSession {
  const user = payload?.user ?? null;
  const accessStatus = user?.accessStatus ?? null;

  return {
    authenticated: payload?.authenticated ?? Boolean(user),
    user,
    accessStatus,
    isAdmin: Boolean(user?.isAdmin),
    competition: normalizeWindows(payload?.competition),
    now: payload?.now ?? null
  };
}

export async function fetchAppSession(): Promise<AppSession> {
  const cookieHeader = await getServerCookieHeader();
  try {
    const payload = await getServerJson<SessionPayload>('/api/auth/session', cookieHeader);
    return normalizeSession(payload);
  } catch {
    return normalizeSession(null);
  }
}

export async function getServerCookieHeader(): Promise<string> {
  try {
    const cookieStore = await cookies();
    return cookieStore.getAll().map((c) => `${c.name}=${c.value}`).join('; ');
  } catch {
    return '';
  }
}

export async function fetchBackendData<T>(path: string): Promise<FetchResult<T>> {
  try {
    const cookieHeader = await getServerCookieHeader();
    const data = await getServerJson<T>(path, cookieHeader);
    return { data, error: null };
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Não foi possível carregar os dados.';
    return { data: null, error: message };
  }
}

export function getSessionViewState(session: AppSession): SessionViewState {
  if (!session.authenticated || !session.user) {
    return "anonymous";
  }

  if (session.accessStatus === "APPROVED") {
    return "approved";
  }

  if (session.accessStatus === "REJECTED") {
    return "rejected";
  }

  if (session.accessStatus === "BLOCKED") {
    return "blocked";
  }

  return "pending";
}

export function isApprovedSession(session: AppSession): boolean {
  return getSessionViewState(session) === "approved";
}

export function isPendingSession(session: AppSession): boolean {
  return getSessionViewState(session) === "pending";
}

export function isRejectedSession(session: AppSession): boolean {
  return getSessionViewState(session) === "rejected";
}

export function isBlockedSession(session: AppSession): boolean {
  return getSessionViewState(session) === "blocked";
}

export function isAdminSession(session: AppSession): boolean {
  return session.isAdmin;
}

function parseInstant(value: string | null | undefined): number | null {
  if (!value) {
    return null;
  }

  const parsed = Date.parse(value);
  return Number.isNaN(parsed) ? null : parsed;
}

export function isReleasedAt(
  releaseAt: string | null | undefined,
  now: string | null | undefined
): boolean {
  const releaseTime = parseInstant(releaseAt);

  if (releaseTime === null) {
    return true;
  }

  const currentTime = parseInstant(now);

  if (currentTime === null) {
    return false;
  }

  return currentTime >= releaseTime;
}

export function isLockedAt(
  closeAt: string | null | undefined,
  now: string | null | undefined
): boolean {
  const closeTime = parseInstant(closeAt);

  if (closeTime === null) {
    return false;
  }

  const currentTime = parseInstant(now);

  if (currentTime === null) {
    return false;
  }

  return currentTime >= closeTime;
}

export function isExploreReleased(session: AppSession): boolean {
  return isReleasedAt(session.competition.exploreReleaseAt, session.now);
}

export function isPredictionLocked(session: AppSession): boolean {
  return isLockedAt(session.competition.predictionCloseAt, session.now);
}

export function canAccessExplore(session: AppSession): boolean {
  return isApprovedSession(session) && isExploreReleased(session);
}

export function resolveHomePath(session: AppSession): string {
  if (!session.authenticated || !session.user) {
    return '/login';
  }

  if (session.isAdmin) {
    return '/admin/dashboard';
  }

  if (session.accessStatus === 'APPROVED') {
    return '/dashboard';
  }

  return '/waiting';
}
