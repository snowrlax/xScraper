# storage.py
# ─────────────────────────────────────────────────────────────
# Big picture:
#   Two responsibilities:
#     1. Persist tweets to JSON (full data) and CSV (human-readable)
#     2. Merge with any previously saved run so re-running the
#        scraper accumulates data rather than overwriting it.
#
#   We always write both formats:
#     - tweets.json  → feed directly into the style analyzer
#     - tweets.csv   → open in Excel / Google Sheets
# ─────────────────────────────────────────────────────────────

import json
import csv
from pathlib import Path

import config


def save(tweets: list[dict]) -> None:
    """
    Merge with any existing data and write both output formats.
    """
    merged = _merge_with_existing(tweets)

    _write_json(merged)
    _write_csv(merged)

    print(f"[storage] Saved {len(merged)} tweets → {config.OUTPUT_JSON}, {config.OUTPUT_CSV}")


def _merge_with_existing(new_tweets: list[dict]) -> list[dict]:
    """
    Load any previously saved tweets and merge, deduplicating by tweet_id.
    This means you can run the scraper multiple times (e.g. on different
    days) and it will accumulate without creating duplicates.
    """
    existing: dict[str, dict] = {}

    if Path(config.OUTPUT_JSON).exists():
        with open(config.OUTPUT_JSON) as f:
            for t in json.load(f):
                existing[t["tweet_id"]] = t

    for t in new_tweets:
        existing[t["tweet_id"]] = t   # new data overwrites stale entries

    # Return sorted newest-first
    return sorted(existing.values(), key=lambda t: t["tweet_id"], reverse=True)


def _write_json(tweets: list[dict]) -> None:
    with open(config.OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(tweets, f, ensure_ascii=False, indent=2)


def _write_csv(tweets: list[dict]) -> None:
    if not tweets:
        return

    fieldnames = [
        "tweet_id", "created_at", "text", "likes",
        "retweets", "replies", "views",
        "is_retweet", "is_reply", "lang",
        "tweet_url", "user_handle",
    ]

    with open(config.OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(tweets)


def plain_text_for_analyzer(tweets: list[dict]) -> str:
    """
    Return just the tweet text as a newline-separated string —
    ready to paste into the style analyzer tool.
    Filters out retweets since those aren't the user's own writing.
    """
    own_tweets = [t for t in tweets if not t.get("is_retweet")]
    return "\n\n".join(t["text"] for t in own_tweets if t.get("text"))
