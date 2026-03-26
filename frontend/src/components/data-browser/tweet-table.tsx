"use client";

import { useState } from "react";
import type { TweetData } from "@/lib/api";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { TweetDetailModal } from "./tweet-detail-modal";

interface TweetTableProps {
  tweets: TweetData[];
}

export function TweetTable({ tweets }: TweetTableProps) {
  const [selectedTweet, setSelectedTweet] = useState<TweetData | null>(null);

  if (tweets.length === 0) {
    return <p className="text-sm text-muted-foreground">No tweets in this session.</p>;
  }

  return (
    <>
      <div className="max-h-96 overflow-y-auto rounded-md border">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead className="w-[100px]">Date</TableHead>
              <TableHead>Text</TableHead>
              <TableHead className="w-[70px] text-right">Likes</TableHead>
              <TableHead className="w-[70px] text-right">RTs</TableHead>
              <TableHead className="w-[80px] text-right">Views</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {tweets.map((tweet) => (
              <TableRow
                key={tweet.tweet_id}
                className="cursor-pointer hover:bg-muted/50"
                onClick={() => setSelectedTweet(tweet)}
              >
                <TableCell className="text-xs text-muted-foreground whitespace-nowrap">
                  {formatShortDate(tweet.created_at)}
                </TableCell>
                <TableCell className="text-sm max-w-xs truncate">
                  {truncate(tweet.text, 100)}
                </TableCell>
                <TableCell className="text-right text-xs tabular-nums">
                  {compact(tweet.likes)}
                </TableCell>
                <TableCell className="text-right text-xs tabular-nums">
                  {compact(tweet.retweets)}
                </TableCell>
                <TableCell className="text-right text-xs tabular-nums">
                  {compact(tweet.views)}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>

      <TweetDetailModal
        tweet={selectedTweet}
        open={selectedTweet !== null}
        onClose={() => setSelectedTweet(null)}
      />
    </>
  );
}

function truncate(text: string, max: number): string {
  if (text.length <= max) return text;
  return text.slice(0, max) + "...";
}

function formatShortDate(iso: string): string {
  try {
    return new Date(iso).toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
    });
  } catch {
    return iso;
  }
}

function compact(n: number): string {
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`;
  if (n >= 1_000) return `${(n / 1_000).toFixed(1)}K`;
  return n.toString();
}
