const ACCESS_TOKEN_KEY = "sajilo_access_token";
const REFRESH_TOKEN_KEY = "sajilo_refresh_token";
const AUTH_COOKIE_NAME = "sajilo_authed";

export function getAccessToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(ACCESS_TOKEN_KEY);
}

export function getRefreshToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(REFRESH_TOKEN_KEY);
}

// Non-httpOnly flag cookie, readable only by middleware, used purely for
// routing decisions (redirect to /login before a protected page renders).
// It carries no token material and grants no access on its own — the
// backend still verifies the real JWT on every request.
function setAuthCookie() {
  // 7 days matches REFRESH_TOKEN_EXPIRE_DAYS on the backend.
  document.cookie = `${AUTH_COOKIE_NAME}=1; path=/; max-age=${60 * 60 * 24 * 7}; samesite=lax`;
}

function clearAuthCookie() {
  document.cookie = `${AUTH_COOKIE_NAME}=; path=/; max-age=0`;
}

export function setTokens(accessToken: string, refreshToken: string) {
  localStorage.setItem(ACCESS_TOKEN_KEY, accessToken);
  localStorage.setItem(REFRESH_TOKEN_KEY, refreshToken);
  setAuthCookie();
}

export function clearTokens() {
  localStorage.removeItem(ACCESS_TOKEN_KEY);
  localStorage.removeItem(REFRESH_TOKEN_KEY);
  clearAuthCookie();
}

const SESSION_MESSAGE_KEY = "sajilo_session_message";

/** Reads and clears the one-shot "why were you logged out" message, if any. */
export function consumeSessionMessage(): string | null {
  if (typeof window === "undefined") return null;
  const msg = sessionStorage.getItem(SESSION_MESSAGE_KEY);
  if (msg) sessionStorage.removeItem(SESSION_MESSAGE_KEY);
  return msg;
}

/** Properly ends the session: revokes the refresh token server-side (so
 * it can't be replayed later) and clears local state either way. */
export async function logout(): Promise<void> {
  const refreshToken = getRefreshToken();
  clearTokens();
  if (!refreshToken) return;
  try {
    await fetch("/api/v1/auth/logout", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refresh_token: refreshToken }),
    });
  } catch {
    // best-effort — client-side tokens are already cleared regardless
  }
}

export function isAuthenticated(): boolean {
  return getAccessToken() !== null;
}

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

async function refreshAccessToken(): Promise<string | null> {
  const refreshToken = getRefreshToken();
  if (!refreshToken) return null;

  const res = await fetch("/api/v1/auth/refresh", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ refresh_token: refreshToken }),
  });

  if (!res.ok) {
    // Surface *why* on the next login screen — e.g. "Session expired due
    // to inactivity" vs. a generic failure — instead of silently bouncing.
    let message = "Your session has expired. Please log in again.";
    try {
      const body = await res.json();
      if (body?.detail) message = body.detail;
    } catch {
      // not JSON
    }
    if (typeof window !== "undefined") {
      sessionStorage.setItem(SESSION_MESSAGE_KEY, message);
    }
    clearTokens();
    return null;
  }

  const data = (await res.json()) as { access_token: string; refresh_token: string };
  setTokens(data.access_token, data.refresh_token);
  return data.access_token;
}

interface ApiFetchOptions extends RequestInit {
  auth?: boolean;
}

export async function apiFetch<T>(path: string, options: ApiFetchOptions = {}): Promise<T> {
  const { auth = true, headers, ...rest } = options;

  const doFetch = (token: string | null) =>
    fetch(`/api${path}`, {
      ...rest,
      headers: {
        "Content-Type": "application/json",
        ...(headers || {}),
        ...(auth && token ? { Authorization: `Bearer ${token}` } : {}),
      },
    });

  let res = await doFetch(auth ? getAccessToken() : null);

  if (auth && res.status === 401) {
    const newToken = await refreshAccessToken();
    if (newToken) {
      res = await doFetch(newToken);
    }
  }

  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      if (body?.detail) detail = body.detail;
    } catch {
      // response wasn't JSON
    }
    throw new ApiError(res.status, detail);
  }

  if (res.status === 204) {
    return undefined as T;
  }
  return (await res.json()) as T;
}