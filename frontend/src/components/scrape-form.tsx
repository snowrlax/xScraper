"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

const TWEET_COUNT_OPTIONS = [
  { value: "50", label: "50 tweets" },
  { value: "100", label: "100 tweets" },
  { value: "500", label: "500 tweets" },
  { value: "1000", label: "1000 tweets" },
];

interface ScrapeFormProps {
  manualModeAvailable: boolean;
  isDisabled: boolean;
  onSubmit: (config: {
    target_handle: string;
    max_tweets: number;
    headless: boolean;
  }) => void;
}

export function ScrapeForm({
  manualModeAvailable,
  isDisabled,
  onSubmit,
}: ScrapeFormProps) {
  const [handle, setHandle] = useState("");
  const [maxTweets, setMaxTweets] = useState("100");
  const [mode, setMode] = useState<"headless" | "manual">("headless");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const cleanHandle = handle.replace(/^@/, "").trim();
    if (!cleanHandle) return;
    onSubmit({
      target_handle: cleanHandle,
      max_tweets: parseInt(maxTweets, 10),
      headless: mode === "headless",
    });
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div className="flex flex-col sm:flex-row gap-3">
        <div className="flex-1">
          <Input
            placeholder="@username"
            value={handle}
            onChange={(e) => setHandle(e.target.value)}
            disabled={isDisabled}
            className="h-10"
          />
        </div>

        <Select value={maxTweets} onValueChange={(v) => { if (v) setMaxTweets(v); }} disabled={isDisabled}>
          <SelectTrigger className="w-[160px] h-10">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            {TWEET_COUNT_OPTIONS.map((opt) => (
              <SelectItem key={opt.value} value={opt.value}>
                {opt.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>

        {manualModeAvailable && (
          <div className="flex items-center gap-3 rounded-lg border border-border px-3 h-10">
            <label className="flex items-center gap-1.5 cursor-pointer text-sm">
              <input
                type="radio"
                name="mode"
                value="headless"
                checked={mode === "headless"}
                onChange={() => setMode("headless")}
                disabled={isDisabled}
                className="accent-primary"
              />
              Headless
            </label>
            <label className="flex items-center gap-1.5 cursor-pointer text-sm">
              <input
                type="radio"
                name="mode"
                value="manual"
                checked={mode === "manual"}
                onChange={() => setMode("manual")}
                disabled={isDisabled}
                className="accent-primary"
              />
              Manual
            </label>
          </div>
        )}
      </div>

      <Button type="submit" disabled={isDisabled || !handle.trim()} size="lg" className="w-full">
        {isDisabled ? "Scraping..." : "Start Scraping"}
      </Button>
    </form>
  );
}
