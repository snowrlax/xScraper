"use client";

import { useCallback, useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { ScrapeForm } from "@/components/scrape-form";
import { ProgressFeed } from "@/components/progress-feed";
import { ResultsSummary } from "@/components/results-summary";
import { DataBrowser } from "@/components/data-browser/data-browser";
import {
  fetchConfig,
  triggerLogin,
  startScrape,
  type AppConfig,
  type ScrapeEvent,
  type ScrapeStats,
} from "@/lib/api";

type AppState = "idle" | "scraping" | "login_required" | "logging_in";

export default function Home() {
  const [config, setConfig] = useState<AppConfig | null>(null);
  const [state, setState] = useState<AppState>("idle");
  const [events, setEvents] = useState<ScrapeEvent[]>([]);
  const [stats, setStats] = useState<ScrapeStats | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [sessionPath, setSessionPath] = useState<string | null>(null);
  const [refreshSignal, setRefreshSignal] = useState(0);

  useEffect(() => {
    fetchConfig()
      .then(setConfig)
      .catch(() => setError("Cannot connect to backend. Is the server running?"));
  }, []);

  const handleLogin = useCallback(async () => {
    setState("logging_in");
    setError(null);
    try {
      const result = await triggerLogin();
      if (result.status === "timeout") {
        setError(result.message);
        setState("idle");
        return;
      }
      const updated = await fetchConfig();
      setConfig(updated);
      setState("idle");
    } catch {
      setError("Login failed. Please try again.");
      setState("idle");
    }
  }, []);

  const handleScrape = useCallback(
    async (request: { target_handle: string; max_tweets: number; headless: boolean; scroll_speed: number }) => {
      setState("scraping");
      setEvents([]);
      setStats(null);
      setError(null);
      setSessionPath(null);

      await startScrape(request, (event) => {
        setEvents((prev) => [...prev, event]);

        if (event.type === "complete") {
          setStats(event.stats);
          setSessionPath(event.session_path);
          setRefreshSignal((prev) => prev + 1);
          setState("idle");
        } else if (event.type === "auth_failed") {
          setState("login_required");
        } else if (event.type === "error") {
          setError(event.message);
          setState("idle");
        }
      });

      setState((prev) => (prev === "scraping" ? "idle" : prev));
    },
    [],
  );

  return (
    <main className="flex-1 flex items-start justify-center px-4 py-12">
      <div className="w-full max-w-2xl space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold tracking-tight">xScraper</h1>
            <p className="text-sm text-muted-foreground mt-1">
              Scrape and analyze X/Twitter profiles
            </p>
          </div>
          <div className="flex items-center gap-2">
            {config?.cookies_present ? (
              <Badge variant="outline" className="text-green-600 border-green-600/30">
                Session Active
              </Badge>
            ) : (
              <Badge variant="outline" className="text-yellow-600 border-yellow-600/30">
                No Session
              </Badge>
            )}
            <Button variant="ghost" size="sm" onClick={handleLogin} disabled={state === "logging_in"}>
              {state === "logging_in" ? "Logging in..." : "Re-login"}
            </Button>
          </div>
        </div>

        {/* Error */}
        {error && (
          <div className="rounded-lg border border-destructive/30 bg-destructive/5 px-4 py-3 text-sm text-destructive">
            {error}
          </div>
        )}

        {/* Login required */}
        {state === "login_required" && (
          <div className="rounded-lg border border-yellow-600/30 bg-yellow-600/5 px-4 py-3 text-sm">
            <p className="font-medium text-yellow-600">Login Required</p>
            <p className="text-muted-foreground mt-1">
              Session cookies are missing or expired. A browser window will open for you to log in.
            </p>
            <Button size="sm" className="mt-3" onClick={handleLogin}>
              Log in to X
            </Button>
          </div>
        )}

        {/* Form */}
        {config && (
          <ScrapeForm
            manualModeAvailable={config.manual_mode_available}
            isDisabled={state === "scraping" || state === "logging_in"}
            onSubmit={handleScrape}
          />
        )}

        {/* Progress */}
        <ProgressFeed events={events} />

        {/* Results */}
        {stats && <ResultsSummary stats={stats} sessionPath={sessionPath} />}

        {/* Data Browser */}
        <DataBrowser refreshSignal={refreshSignal} />
      </div>
    </main>
  );
}
