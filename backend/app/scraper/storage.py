# storage.py
# ---------------------------------------------------------
# Persist tweets (JSON + CSV) and users (JSON).
# Merges with existing data on each run.
# ---------------------------------------------------------

import json
import csv
from pathlib import Path
from datetime import datetime, timezone

from . import config


def save(tweets: list[dict], users: dict[str, dict] | None = None) -> dict:
    """
    Merge with existing data and write all output formats.
    Returns stats dict for the API response.
    """
    merged_tweets = _merge_tweets_with_existing(tweets)
    _write_json(merged_tweets, config.OUTPUT_JSON)
    _write_csv(merged_tweets)

    user_count = 0
    if users:
        merged_users = _merge_users_with_existing(users)
        _write_json(merged_users, config.OUTPUT_USERS)
        user_count = len(merged_users)

    stats = get_tweet_stats(merged_tweets)
    stats["users_saved"] = user_count
    return stats


def save_users(users: dict[str, dict]) -> None:
    merged = _merge_users_with_existing(users)
    _write_json(merged, config.OUTPUT_USERS)


def _merge_tweets_with_existing(new_tweets: list[dict]) -> list[dict]:
    existing: dict[str, dict] = {}

    if Path(config.OUTPUT_JSON).exists():
        try:
            with open(config.OUTPUT_JSON, encoding="utf-8") as f:
                for t in json.load(f):
                    existing[t["tweet_id"]] = t
        except (json.JSONDecodeError, KeyError):
            pass

    for t in new_tweets:
        existing[t["tweet_id"]] = t

    return sorted(existing.values(), key=lambda t: t["tweet_id"], reverse=True)


def _merge_users_with_existing(new_users: dict[str, dict]) -> dict[str, dict]:
    existing: dict[str, dict] = {}

    if Path(config.OUTPUT_USERS).exists():
        try:
            with open(config.OUTPUT_USERS, encoding="utf-8") as f:
                existing = json.load(f)
        except json.JSONDecodeError:
            pass

    now = datetime.now(timezone.utc).isoformat()

    for user_id, user_data in new_users.items():
        if user_id in existing:
            user_data["first_seen"] = existing[user_id].get("first_seen", now)
        else:
            user_data["first_seen"] = user_data.get("first_seen", now)

        user_data["last_updated"] = now
        existing[user_id] = user_data

    return existing


def _write_json(data, filepath: str) -> None:
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _write_csv(tweets: list[dict]) -> None:
    if not tweets:
        return

    fieldnames = [
        "tweet_id", "created_at", "scraped_at", "author_handle",
        "author_name", "author_verified", "text", "likes", "retweets",
        "replies", "quotes", "bookmarks", "views", "lang", "source",
        "is_retweet", "is_reply", "is_quote", "is_self_reply", "is_pinned",
        "conversation_id", "in_reply_to_tweet_id", "in_reply_to_handle",
        "tweet_url",
    ]

    with open(config.OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(tweets)


def plain_text_for_analyzer(tweets: list[dict]) -> str:
    own_tweets = [t for t in tweets if not t.get("is_retweet")]
    return "\n\n".join(t["text"] for t in own_tweets if t.get("text"))


def get_tweet_stats(tweets: list[dict]) -> dict:
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
