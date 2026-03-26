# storage.py
# ---------------------------------------------------------
# Persist tweets (JSON + CSV) and users (JSON) to a
# per-user, per-session directory.
# ---------------------------------------------------------

import json
import csv
from datetime import datetime, timezone

from .config import SessionPaths


def save(
    tweets: list[dict],
    users: dict[str, dict] | None,
    session_paths: SessionPaths,
) -> dict:
    """
    Write all output files to the session directory.
    Returns stats dict for the API response.
    """
    sorted_tweets = sorted(tweets, key=lambda t: t["tweet_id"], reverse=True)
    _write_json(sorted_tweets, session_paths.json_file)
    _write_csv(sorted_tweets, session_paths.csv_file)

    user_count = 0
    if users:
        now = datetime.now(timezone.utc).isoformat()
        stamped_users = {
            uid: {**udata, "first_seen": now, "last_updated": now}
            for uid, udata in users.items()
        }
        _write_json(stamped_users, session_paths.users_file)
        user_count = len(stamped_users)

    stats = get_tweet_stats(sorted_tweets)
    stats["users_saved"] = user_count
    return stats


def _write_json(data, filepath) -> None:
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _write_csv(tweets: list[dict], filepath) -> None:
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

    with open(filepath, "w", newline="", encoding="utf-8") as f:
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
