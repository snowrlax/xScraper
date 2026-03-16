# storage.py
# ─────────────────────────────────────────────────────────────
# Big picture:
#   Three responsibilities:
#     1. Persist tweets to JSON (full data) and CSV (human-readable)
#     2. Persist users to JSON (deduplicated profiles)
#     3. Merge with any previously saved run so re-running the
#        scraper accumulates data rather than overwriting it.
#
#   We always write these formats:
#     - tweets.json  → full enriched tweet data
#     - tweets.csv   → core fields for spreadsheets
#     - users.json   → deduplicated user profiles
# ─────────────────────────────────────────────────────────────

import json
import csv
from pathlib import Path
from datetime import datetime, timezone

import config


def save(tweets: list[dict], users: dict[str, dict] = None) -> None:
    """
    Merge with any existing data and write all output formats.

    Args:
        tweets: List of tweet objects
        users: Dict of user_id -> user profile (optional)
    """
    merged_tweets = _merge_tweets_with_existing(tweets)
    _write_json(merged_tweets, config.OUTPUT_JSON)
    _write_csv(merged_tweets)

    if users:
        merged_users = _merge_users_with_existing(users)
        _write_json(merged_users, config.OUTPUT_USERS)
        print(f"[storage] Saved {len(merged_users)} users → {config.OUTPUT_USERS}")

    print(f"[storage] Saved {len(merged_tweets)} tweets → {config.OUTPUT_JSON}, {config.OUTPUT_CSV}")


def save_users(users: dict[str, dict]) -> None:
    """
    Save users separately (can be called independently).
    """
    merged = _merge_users_with_existing(users)
    _write_json(merged, config.OUTPUT_USERS)
    print(f"[storage] Saved {len(merged)} users → {config.OUTPUT_USERS}")


def _merge_tweets_with_existing(new_tweets: list[dict]) -> list[dict]:
    """
    Load any previously saved tweets and merge, deduplicating by tweet_id.
    This means you can run the scraper multiple times (e.g. on different
    days) and it will accumulate without creating duplicates.
    """
    existing: dict[str, dict] = {}

    if Path(config.OUTPUT_JSON).exists():
        try:
            with open(config.OUTPUT_JSON) as f:
                for t in json.load(f):
                    existing[t["tweet_id"]] = t
        except (json.JSONDecodeError, KeyError):
            pass  # Start fresh if file is corrupted

    for t in new_tweets:
        existing[t["tweet_id"]] = t  # new data overwrites stale entries

    # Return sorted newest-first
    return sorted(existing.values(), key=lambda t: t["tweet_id"], reverse=True)


def _merge_users_with_existing(new_users: dict[str, dict]) -> dict[str, dict]:
    """
    Load any previously saved users and merge, preserving first_seen.
    """
    existing: dict[str, dict] = {}

    if Path(config.OUTPUT_USERS).exists():
        try:
            with open(config.OUTPUT_USERS) as f:
                existing = json.load(f)
        except json.JSONDecodeError:
            pass  # Start fresh if file is corrupted

    now = datetime.now(timezone.utc).isoformat()

    for user_id, user_data in new_users.items():
        if user_id in existing:
            # Preserve first_seen from existing record
            user_data["first_seen"] = existing[user_id].get("first_seen", now)
        else:
            user_data["first_seen"] = user_data.get("first_seen", now)

        user_data["last_updated"] = now
        existing[user_id] = user_data

    return existing


def _write_json(data, filepath: str) -> None:
    """Write data to JSON file."""
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _write_csv(tweets: list[dict]) -> None:
    """
    Write core tweet fields to CSV for spreadsheet analysis.
    Complex fields (arrays, nested objects) are excluded.
    """
    if not tweets:
        return

    # Core fields suitable for CSV (flat, simple values)
    fieldnames = [
        "tweet_id",
        "created_at",
        "scraped_at",
        "author_handle",
        "author_name",
        "author_verified",
        "text",
        "likes",
        "retweets",
        "replies",
        "quotes",
        "bookmarks",
        "views",
        "lang",
        "source",
        "is_retweet",
        "is_reply",
        "is_quote",
        "is_self_reply",
        "is_pinned",
        "conversation_id",
        "in_reply_to_tweet_id",
        "in_reply_to_handle",
        "tweet_url",
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


def get_tweet_stats(tweets: list[dict]) -> dict:
    """
    Calculate summary statistics for scraped tweets.
    """
    if not tweets:
        return {}

    total = len(tweets)
    original = sum(1 for t in tweets if not t.get("is_retweet") and not t.get("is_reply"))
    replies = sum(1 for t in tweets if t.get("is_reply"))
    retweets = sum(1 for t in tweets if t.get("is_retweet"))
    quotes = sum(1 for t in tweets if t.get("is_quote"))
    threads = sum(1 for t in tweets if t.get("is_self_reply"))

    total_likes = sum(t.get("likes", 0) for t in tweets)
    total_retweets = sum(t.get("retweets", 0) for t in tweets)
    total_views = sum(t.get("views", 0) for t in tweets)

    return {
        "total_tweets": total,
        "original_tweets": original,
        "replies": replies,
        "retweets": retweets,
        "quote_tweets": quotes,
        "self_replies_threads": threads,
        "total_likes": total_likes,
        "total_retweets": total_retweets,
        "total_views": total_views,
        "avg_likes": round(total_likes / total, 1) if total else 0,
        "avg_retweets": round(total_retweets / total, 1) if total else 0,
        "avg_views": round(total_views / total, 1) if total else 0,
    }
