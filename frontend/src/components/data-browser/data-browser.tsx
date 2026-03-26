"use client";

import { useCallback, useEffect, useState } from "react";
import {
  fetchDataTree,
  fetchSessionDetail,
  type UserSummary,
  type SessionDetailResponse,
} from "@/lib/api";
import { Accordion } from "@/components/ui/accordion";
import { Skeleton } from "@/components/ui/skeleton";
import { Button } from "@/components/ui/button";
import { UserAccordion } from "./user-accordion";

interface DataBrowserProps {
  refreshSignal: number;
}

export function DataBrowser({ refreshSignal }: DataBrowserProps) {
  const [users, setUsers] = useState<UserSummary[] | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [sessionDetails, setSessionDetails] = useState<Map<string, SessionDetailResponse>>(
    new Map(),
  );
  const [loadingSessions, setLoadingSessions] = useState<Set<string>>(new Set());

  const loadTree = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchDataTree();
      setUsers(data.users);
    } catch {
      setError("Failed to load scraped data.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadTree();
  }, [loadTree, refreshSignal]);

  const handleSessionToggle = useCallback(
    async (handle: string, sessionId: string) => {
      const key = `${handle}/${sessionId}`;

      // Already loaded — just let the accordion toggle
      if (sessionDetails.has(key)) return;
      // Already loading
      if (loadingSessions.has(key)) return;

      setLoadingSessions((prev) => new Set(prev).add(key));
      try {
        const detail = await fetchSessionDetail(handle, sessionId);
        setSessionDetails((prev) => new Map(prev).set(key, detail));
      } catch {
        setError(`Failed to load session ${sessionId}`);
      } finally {
        setLoadingSessions((prev) => {
          const next = new Set(prev);
          next.delete(key);
          return next;
        });
      }
    },
    [sessionDetails, loadingSessions],
  );

  if (loading) {
    return (
      <div className="space-y-3">
        <h3 className="text-sm font-medium text-muted-foreground">Past Scrapes</h3>
        <div className="space-y-2">
          {Array.from({ length: 3 }).map((_, i) => (
            <Skeleton key={i} className="h-10 rounded-md" />
          ))}
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="space-y-3">
        <h3 className="text-sm font-medium text-muted-foreground">Past Scrapes</h3>
        <div className="rounded-lg border border-destructive/30 bg-destructive/5 px-4 py-3 text-sm text-destructive">
          {error}
        </div>
      </div>
    );
  }

  if (!users || users.length === 0) {
    return (
      <div className="space-y-3">
        <h3 className="text-sm font-medium text-muted-foreground">Past Scrapes</h3>
        <p className="text-sm text-muted-foreground text-center py-6">
          No past scrapes found. Use the form above to scrape your first profile.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-medium text-muted-foreground">Past Scrapes</h3>
        <Button variant="ghost" size="sm" onClick={loadTree} className="text-xs h-7">
          Refresh
        </Button>
      </div>

      <Accordion multiple>
        {users.map((user) => (
          <UserAccordion
            key={user.handle}
            user={user}
            sessionDetails={sessionDetails}
            loadingSessions={loadingSessions}
            onSessionToggle={handleSessionToggle}
          />
        ))}
      </Accordion>
    </div>
  );
}
