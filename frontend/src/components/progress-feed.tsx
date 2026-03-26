"use client";

import { useEffect, useRef } from "react";
import type { ScrapeEvent } from "@/lib/api";

interface ProgressFeedProps {
  events: ScrapeEvent[];
}

export function ProgressFeed({ events }: ProgressFeedProps) {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [events.length]);

  if (events.length === 0) return null;

  return (
    <div className="rounded-lg border border-border bg-muted/30 p-4">
      <h3 className="text-sm font-medium text-muted-foreground mb-3">Progress</h3>
      <div className="max-h-48 overflow-y-auto space-y-1 font-mono text-xs">
        {events.map((event, i) => (
          <div key={i} className={getEventClass(event)}>
            {formatEvent(event)}
          </div>
        ))}
        <div ref={bottomRef} />
      </div>
    </div>
  );
}

function getEventClass(event: ScrapeEvent): string {
  switch (event.type) {
    case "progress":
      return "text-foreground";
    case "rate_limited":
      return "text-yellow-600 dark:text-yellow-400";
    case "auth_failed":
    case "error":
      return "text-destructive font-medium";
    case "complete":
      return "text-green-600 dark:text-green-400 font-medium";
    default:
      return "text-muted-foreground";
  }
}

function formatEvent(event: ScrapeEvent): string {
  switch (event.type) {
    case "progress":
      return `+${event.new} tweets | total: ${event.total} | ${event.elapsed_seconds}s`;
    case "rate_limited":
      return `No new tweets (${event.empty_scrolls}/5 empty scrolls) | total: ${event.total}`;
    case "auth_failed":
      return `Auth failed: ${event.reason}`;
    case "complete":
      return `Done! ${event.total} tweets scraped.`;
    case "error":
      return `Error: ${event.message}`;
    default:
      return JSON.stringify(event);
  }
}
