"use client";

import type { SessionSummary, SessionDetailResponse } from "@/lib/api";
import {
  Accordion,
  AccordionItem,
  AccordionTrigger,
  AccordionContent,
} from "@/components/ui/accordion";
import { SessionDetail } from "./session-detail";

interface SessionListProps {
  handle: string;
  sessions: SessionSummary[];
  sessionDetails: Map<string, SessionDetailResponse>;
  loadingSessions: Set<string>;
  onSessionToggle: (handle: string, sessionId: string) => void;
}

export function SessionList({
  handle,
  sessions,
  sessionDetails,
  loadingSessions,
  onSessionToggle,
}: SessionListProps) {
  return (
    <Accordion
      multiple
      className="pl-4 border-l border-border/50"
      onValueChange={(openValues: string[]) => {
        for (const sessionId of openValues) {
          onSessionToggle(handle, sessionId);
        }
      }}
    >
      {sessions.map((session) => {
        const key = `${handle}/${session.session_id}`;
        const detail = sessionDetails.get(key) ?? null;
        const loading = loadingSessions.has(key);

        return (
          <AccordionItem key={session.session_id} value={session.session_id}>
            <AccordionTrigger className="text-sm py-2 hover:no-underline">
              <div className="flex items-center gap-3 text-left">
                <span className="font-mono text-xs text-muted-foreground">
                  {formatSessionDate(session.scraped_at)}
                </span>
                <span className="text-xs text-muted-foreground">
                  {session.tweet_count} tweets
                </span>
                <span className="text-[11px] text-muted-foreground/60">
                  ({formatBytes(session.file_size_bytes)})
                </span>
              </div>
            </AccordionTrigger>
            <AccordionContent>
              <SessionDetail detail={detail} loading={loading} />
            </AccordionContent>
          </AccordionItem>
        );
      })}
    </Accordion>
  );
}

function formatSessionDate(iso: string): string {
  try {
    return new Date(iso).toLocaleString("en-US", {
      month: "short",
      day: "numeric",
      year: "numeric",
      hour: "numeric",
      minute: "2-digit",
    });
  } catch {
    return iso;
  }
}

function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}
