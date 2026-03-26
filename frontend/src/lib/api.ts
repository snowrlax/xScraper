const API_BASE = "http://localhost:8000";

export interface AppConfig {
  manual_mode_available: boolean;
  cookies_present: boolean;
}

export interface ScrapeRequest {
  target_handle: string;
  max_tweets: number;
  headless: boolean;
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
  | { type: "complete"; total: number; stats: ScrapeStats }
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
