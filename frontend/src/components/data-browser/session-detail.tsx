"use client";

import type { SessionDetailResponse } from "@/lib/api";
import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { TweetTable } from "./tweet-table";

interface SessionDetailProps {
  detail: SessionDetailResponse | null;
  loading: boolean;
}

export function SessionDetail({ detail, loading }: SessionDetailProps) {
  if (loading) {
    return (
      <div className="space-y-3 p-2">
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-2">
          {Array.from({ length: 8 }).map((_, i) => (
            <Skeleton key={i} className="h-14 rounded-md" />
          ))}
        </div>
        <Skeleton className="h-48 rounded-md" />
      </div>
    );
  }

  if (!detail) return null;

  const { stats } = detail;

  const statItems = [
    { label: "Total Tweets", value: stats.total_tweets },
    { label: "Original", value: stats.original_tweets },
    { label: "Replies", value: stats.replies },
    { label: "Retweets", value: stats.retweets },
    { label: "Quotes", value: stats.quote_tweets },
    { label: "Threads", value: stats.self_replies_threads },
    { label: "Total Likes", value: stats.total_likes.toLocaleString() },
    { label: "Avg Likes", value: stats.avg_likes },
    { label: "Total Views", value: stats.total_views.toLocaleString() },
    { label: "Avg Views", value: stats.avg_views.toLocaleString() },
    { label: "Users Found", value: stats.users_saved },
  ];

  return (
    <div className="space-y-4 p-2">
      <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-2">
        {statItems.map((item) => (
          <Card key={item.label} className="bg-muted/30">
            <CardContent className="p-2.5">
              <div className="text-[11px] text-muted-foreground">{item.label}</div>
              <div className="text-base font-semibold mt-0.5">{item.value}</div>
            </CardContent>
          </Card>
        ))}
      </div>

      <TweetTable tweets={detail.tweets} />
    </div>
  );
}
