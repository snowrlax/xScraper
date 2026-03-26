"use client";

import type { TweetData } from "@/lib/api";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogClose,
} from "@/components/ui/dialog";

interface TweetDetailModalProps {
  tweet: TweetData | null;
  open: boolean;
  onClose: () => void;
}

export function TweetDetailModal({ tweet, open, onClose }: TweetDetailModalProps) {
  if (!tweet) return null;

  const fields = [
    { label: "Author", value: `@${tweet.author_handle} (${tweet.author_name})` },
    { label: "Date", value: formatDate(tweet.created_at) },
    { label: "Likes", value: tweet.likes.toLocaleString() },
    { label: "Retweets", value: tweet.retweets.toLocaleString() },
    { label: "Replies", value: tweet.replies.toLocaleString() },
    { label: "Quotes", value: tweet.quotes.toLocaleString() },
    { label: "Bookmarks", value: tweet.bookmarks.toLocaleString() },
    { label: "Views", value: tweet.views.toLocaleString() },
  ];

  const flags = [
    tweet.is_retweet && "Retweet",
    tweet.is_reply && "Reply",
    tweet.is_quote && "Quote",
    tweet.is_self_reply && "Thread",
  ].filter(Boolean);

  return (
    <Dialog open={open} onOpenChange={(o) => { if (!o) onClose(); }}>
      <DialogContent className="max-w-lg max-h-[80vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="text-sm font-medium">Tweet Detail</DialogTitle>
          <DialogDescription className="sr-only">Full tweet information</DialogDescription>
        </DialogHeader>

        <div className="space-y-4 text-sm">
          <p className="whitespace-pre-wrap leading-relaxed">{tweet.text}</p>

          {flags.length > 0 && (
            <div className="flex gap-2">
              {flags.map((f) => (
                <span key={f as string} className="px-2 py-0.5 rounded bg-muted text-xs text-muted-foreground">
                  {f}
                </span>
              ))}
            </div>
          )}

          <div className="grid grid-cols-2 gap-2">
            {fields.map((f) => (
              <div key={f.label}>
                <span className="text-muted-foreground">{f.label}: </span>
                <span className="font-medium">{f.value}</span>
              </div>
            ))}
          </div>

          {tweet.tweet_url && (
            <a
              href={tweet.tweet_url}
              target="_blank"
              rel="noopener noreferrer"
              className="text-xs text-blue-500 hover:underline"
            >
              View on X
            </a>
          )}
        </div>

        <DialogClose className="mt-2 text-sm text-muted-foreground hover:text-foreground">
          Close
        </DialogClose>
      </DialogContent>
    </Dialog>
  );
}

function formatDate(iso: string): string {
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
