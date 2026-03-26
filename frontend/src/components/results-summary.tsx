"use client";

import type { ScrapeStats } from "@/lib/api";
import { Card, CardContent } from "@/components/ui/card";

interface ResultsSummaryProps {
  stats: ScrapeStats;
  sessionPath?: string | null;
}

export function ResultsSummary({ stats, sessionPath }: ResultsSummaryProps) {
  const items = [
    { label: "Total Tweets", value: stats.total_tweets },
    { label: "Original", value: stats.original_tweets },
    { label: "Replies", value: stats.replies },
    { label: "Retweets", value: stats.retweets },
    { label: "Quotes", value: stats.quote_tweets },
    { label: "Threads", value: stats.self_replies_threads },
    { label: "Total Likes", value: stats.total_likes.toLocaleString() },
    { label: "Total Views", value: stats.total_views.toLocaleString() },
    { label: "Avg Likes", value: stats.avg_likes },
    { label: "Avg Views", value: stats.avg_views.toLocaleString() },
    { label: "Users Found", value: stats.users_saved },
  ];

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-medium text-muted-foreground">Results</h3>
        {sessionPath && (
          <span className="text-xs text-muted-foreground">
            Saved to: {sessionPath}
          </span>
        )}
      </div>
      <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-3">
        {items.map((item) => (
          <Card key={item.label} className="bg-muted/30">
            <CardContent className="p-3">
              <div className="text-xs text-muted-foreground">{item.label}</div>
              <div className="text-lg font-semibold mt-0.5">{item.value}</div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
