export type ApiMethod = "GET" | "POST" | "PATCH" | "PUT";

export type ApiErrorShape = {
  status: number;
  code: string;
  message: string;
  details?: unknown;
};

export type SessionAccessStatus = "PENDING" | "APPROVED" | "REJECTED" | "BLOCKED";

export type SessionUserPayload = {
  id: string;
  email: string;
  name?: string | null;
  accessStatus: SessionAccessStatus;
  isAdmin?: boolean;
};

export type SessionWindowPayload = {
  predictionCloseAt?: string | null;
  exploreReleaseAt?: string | null;
};

export type SessionPayload = {
  authenticated: boolean;
  user: SessionUserPayload | null;
  competition?: SessionWindowPayload | null;
  now?: string | null;
};

export class ApiClientError extends Error {
  readonly status: number;
  readonly code: string;
  readonly details?: unknown;

  constructor(error: ApiErrorShape) {
    super(error.message);
    this.name = "ApiClientError";
    this.status = error.status;
    this.code = error.code;
    this.details = error.details;
  }
}

type RequestOptions = {
  body?: unknown;
  headers?: HeadersInit;
  signal?: AbortSignal;
};

const apiBaseUrl =
  process.env.NEXT_PUBLIC_API_BASE_URL?.replace(/\/$/, "") ||
  process.env.API_BASE_URL?.replace(/\/$/, "") ||
  "http://localhost:8000";

function buildUrl(path: string): string {
  if (/^https?:\/\//i.test(path)) {
    return path;
  }

  const normalizedPath = path.startsWith("/") ? path : `/${path}`;
  return `${apiBaseUrl}${normalizedPath}`;
}

function isJsonResponse(contentType: string | null): boolean {
  return contentType?.toLowerCase().includes("application/json") ?? false;
}

function inferErrorMessage(payload: unknown, fallback: string): string {
  if (!payload || typeof payload !== "object") {
    return fallback;
  }

  const candidate = payload as Record<string, unknown>;

  if (typeof candidate.message === "string" && candidate.message.trim()) {
    return candidate.message;
  }

  if (typeof candidate.detail === "string" && candidate.detail.trim()) {
    return candidate.detail;
  }

  if (typeof candidate.error === "string" && candidate.error.trim()) {
    return candidate.error;
  }

  return fallback;
}

function inferErrorCode(status: number, payload: unknown): string {
  if (payload && typeof payload === "object") {
    const candidate = payload as Record<string, unknown>;

    if (typeof candidate.code === "string" && candidate.code.trim()) {
      return candidate.code;
    }
  }

  if (status === 401) {
    return "UNAUTHORIZED";
  }

  if (status === 403) {
    return "FORBIDDEN";
  }

  if (status === 404) {
    return "NOT_FOUND";
  }

  return "API_ERROR";
}

async function parseResponseBody<T>(response: Response): Promise<T | null> {
  if (response.status === 204) {
    return null;
  }

  const contentType = response.headers.get("content-type");

  if (isJsonResponse(contentType)) {
    return (await response.json()) as T;
  }

  const text = await response.text();

  if (!text) {
    return null;
  }

  return text as T;
}

async function request<T>(
  method: ApiMethod,
  path: string,
  options: RequestOptions = {}
): Promise<T> {
  const headers = new Headers(options.headers);
  headers.set("accept", "application/json");

  const hasBody = options.body !== undefined;

  if (hasBody) {
    headers.set("content-type", "application/json");
  }

  const response = await fetch(buildUrl(path), {
    method,
    credentials: "include",
    headers,
    body: hasBody ? JSON.stringify(options.body) : undefined,
    signal: options.signal,
    cache: "no-store"
  });

  const payload = await parseResponseBody<T | Record<string, unknown> | string>(response);

  if (!response.ok) {
    const errorPayload =
      payload && typeof payload === "object" && !Array.isArray(payload) ? payload : undefined;

    throw new ApiClientError({
      status: response.status,
      code: inferErrorCode(response.status, errorPayload),
      message: inferErrorMessage(errorPayload, response.statusText || "Request failed"),
      details: payload
    });
  }

  return payload as T;
}

export function getJson<T>(path: string, options: Omit<RequestOptions, "body"> = {}) {
  return request<T>("GET", path, options);
}

export function postJson<T>(
  path: string,
  body?: unknown,
  options: Omit<RequestOptions, "body"> = {}
) {
  return request<T>("POST", path, { ...options, body });
}

export function patchJson<T>(
  path: string,
  body?: unknown,
  options: Omit<RequestOptions, "body"> = {}
) {
  return request<T>("PATCH", path, { ...options, body });
}

export function putJson<T>(
  path: string,
  body?: unknown,
  options: Omit<RequestOptions, "body"> = {}
) {
  return request<T>("PUT", path, { ...options, body });
}

export function getSession(cookieHeader?: string, signal?: AbortSignal) {
  const headers: HeadersInit = cookieHeader ? { cookie: cookieHeader } : {};
  return getJson<SessionPayload>("/api/auth/session", { signal, headers });
}

export function getServerJson<T>(path: string, cookieHeader?: string, signal?: AbortSignal) {
  const headers: HeadersInit = cookieHeader ? { cookie: cookieHeader } : {};
  return getJson<T>(path, { signal, headers });
}
