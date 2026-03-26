const API_BASE = "http://localhost:8000";

export interface AppConfig {
  manual_mode_available: boolean;
  cookies_present: boolean;
}

export interface ScrapeRequest {
  target_handle: string;
  max_tweets: number;
  headless: boolean;
  scroll_speed: number;
}

export interface ScrapeStats {
  total_tweets: number;
  original_tweets: number;
  replies: number;
  retweets: number;
  quote_tweets: number;
  self_replies_threads: number;
  total_likes: number;
  total_retweets: number;
  total_views: number;
  avg_likes: number;
  avg_retweets: number;
  avg_views: number;
  users_saved: number;
}

export type ScrapeEvent =
  | { type: "progress"; new: number; total: number; elapsed_seconds: number }
  | { type: "rate_limited"; empty_scrolls: number; total: number; elapsed_seconds: number }
  | { type: "auth_failed"; reason: string }
  | { type: "complete"; total: number; stats: ScrapeStats; session_path: string }
  | { type: "error"; message: string };

export async function fetchConfig(): Promise<AppConfig> {
  const res = await fetch(`${API_BASE}/api/config`);
  if (!res.ok) throw new Error("Failed to fetch config");
  return res.json();
}

export async function triggerLogin(): Promise<{ status: string; message: string }> {
  const res = await fetch(`${API_BASE}/api/login`, { method: "POST" });
  if (res.status === 408) {
    return { status: "timeout", message: "Login timed out. Please try again." };
  }
  if (!res.ok) throw new Error("Login request failed");
  return res.json();
}

// ── Data Browser types ───────────────────────────────────

export interface SessionSummary {
  session_id: string;
  scraped_at: string;
  tweet_count: number;
  file_size_bytes: number;
}

export interface UserSummary {
  handle: string;
  session_count: number;
  sessions: SessionSummary[];
}

export interface DataTreeResponse {
  users: UserSummary[];
}

export interface TweetData {
  tweet_id: string;
  created_at: string;
  text: string;
  author_handle: string;
  author_name: string;
  likes: number;
  retweets: number;
  replies: number;
  quotes: number;
  bookmarks: number;
  views: number;
  is_retweet: boolean;
  is_reply: boolean;
  is_quote: boolean;
  is_self_reply: boolean;
  tweet_url: string;
}

export interface SessionDetailResponse {
  handle: string;
  session_id: string;
  scraped_at: string;
  stats: ScrapeStats;
  tweets: TweetData[];
  users_count: number;
}

// ── Data Browser functions ───────────────────────────────

export async function fetchDataTree(): Promise<DataTreeResponse> {
  const res = await fetch(`${API_BASE}/api/data/tree`);
  if (!res.ok) throw new Error("Failed to fetch data tree");
  return res.json();
}

export async function fetchSessionDetail(
  handle: string,
  sessionId: string,
): Promise<SessionDetailResponse> {
  const res = await fetch(`${API_BASE}/api/data/${handle}/sessions/${sessionId}`);
  if (!res.ok) throw new Error("Failed to fetch session detail");
  return res.json();
}

// ── Scrape functions ─────────────────────────────────────

export async function startScrape(
  request: ScrapeRequest,
  onEvent: (event: ScrapeEvent) => void,
  signal?: AbortSignal,
): Promise<void> {
  const res = await fetch(`${API_BASE}/api/scrape`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(request),
    signal,
  });

  if (res.status === 401) {
    onEvent({ type: "auth_failed", reason: "No session cookies. Please log in." });
    return;
  }
  if (res.status === 409) {
    onEvent({ type: "error", message: "A scrape is already running." });
    return;
  }
  if (!res.ok) {
    const detail = await res.json().catch(() => ({ detail: "Request failed" }));
    onEvent({ type: "error", message: detail.detail || "Request failed" });
    return;
  }

  const reader = res.body?.getReader();
  if (!reader) return;

  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split("\n\n");
    buffer = lines.pop() || "";

    for (const line of lines) {
      const trimmed = line.trim();
      if (!trimmed.startsWith("data: ")) continue;
      try {
        const event: ScrapeEvent = JSON.parse(trimmed.slice(6));
        onEvent(event);
      } catch {
        // ignore malformed events
      }
    }
  }
}
