# data_loader.py
# ─────────────────────────────────────────────────────────────
# Load and parse tweets.json with datetime conversion and
# data preparation for analytics.
# ─────────────────────────────────────────────────────────────

import json
from pathlib import Path
from datetime import datetime
from typing import Optional

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
import config


def load_tweets(filepath: Optional[str] = None) -> list[dict]:
    """
    Load tweets from JSON file and parse datetime fields.

    Args:
        filepath: Path to tweets.json, defaults to config.OUTPUT_JSON

    Returns:
        List of tweet dicts with parsed datetime fields
    """
    filepath = filepath or config.OUTPUT_JSON

    if not Path(filepath).exists():
        return []

    with open(filepath, "r", encoding="utf-8") as f:
        tweets = json.load(f)

    # Parse datetime fields
    for tweet in tweets:
        tweet["created_at_dt"] = parse_twitter_datetime(tweet.get("created_at"))
        tweet["scraped_at_dt"] = parse_iso_datetime(tweet.get("scraped_at"))

        # Parse nested tweets if present
        if tweet.get("quoted_tweet"):
            tweet["quoted_tweet"]["created_at_dt"] = parse_twitter_datetime(
                tweet["quoted_tweet"].get("created_at")
            )
        if tweet.get("retweeted_tweet"):
            tweet["retweeted_tweet"]["created_at_dt"] = parse_twitter_datetime(
                tweet["retweeted_tweet"].get("created_at")
            )

    return tweets


def parse_twitter_datetime(dt_str: Optional[str]) -> Optional[datetime]:
    """
    Parse Twitter's datetime format: "Mon Mar 16 17:24:09 +0000 2026"

    Args:
        dt_str: Twitter datetime string

    Returns:
        datetime object or None if parsing fails
    """
    if not dt_str:
        return None

    try:
        # Twitter format: "Wed Oct 10 20:19:24 +0000 2018"
        return datetime.strptime(dt_str, "%a %b %d %H:%M:%S %z %Y")
    except ValueError:
        return None


def parse_iso_datetime(dt_str: Optional[str]) -> Optional[datetime]:
    """
    Parse ISO format datetime: "2026-03-16T18:41:28.043764+00:00"

    Args:
        dt_str: ISO datetime string

    Returns:
        datetime object or None if parsing fails
    """
    if not dt_str:
        return None

    try:
        return datetime.fromisoformat(dt_str)
    except ValueError:
        return None


def load_users(filepath: Optional[str] = None) -> dict[str, dict]:
    """
    Load users from JSON file.

    Args:
        filepath: Path to users.json, defaults to config.OUTPUT_USERS

    Returns:
        Dict of user_id -> user profile
    """
    filepath = filepath or config.OUTPUT_USERS

    if not Path(filepath).exists():
        return {}

    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


def get_original_tweets(tweets: list[dict]) -> list[dict]:
    """
    Filter to original tweets only (no retweets).

    Args:
        tweets: List of all tweets

    Returns:
        List of original tweets
    """
    return [t for t in tweets if not t.get("is_retweet")]


def get_own_content(tweets: list[dict]) -> list[dict]:
    """
    Filter to user's own content (no retweets, includes replies).

    Args:
        tweets: List of all tweets

    Returns:
        List of user's own tweets
    """
    return [t for t in tweets if not t.get("is_retweet")]


def get_top_tweets_by_engagement(tweets: list[dict], n: int = 10) -> list[dict]:
    """
    Get top N tweets sorted by likes.

    Args:
        tweets: List of tweets
        n: Number of top tweets to return

    Returns:
        Top N tweets by likes
    """
    original = get_original_tweets(tweets)
    return sorted(original, key=lambda t: t.get("likes", 0), reverse=True)[:n]


def get_recent_tweets(tweets: list[dict], n: int = 10) -> list[dict]:
    """
    Get N most recent tweets.

    Args:
        tweets: List of tweets
        n: Number of recent tweets to return

    Returns:
        N most recent tweets
    """
    with_dates = [t for t in tweets if t.get("created_at_dt")]
    return sorted(with_dates, key=lambda t: t["created_at_dt"], reverse=True)[:n]


def get_author_info(tweets: list[dict]) -> Optional[dict]:
    """
    Extract author info from first available tweet.

    Args:
        tweets: List of tweets

    Returns:
        Dict with author_handle, author_name, author_verified
    """
    if not tweets:
        return None

    t = tweets[0]
    return {
        "author_handle": t.get("author_handle"),
        "author_name": t.get("author_name"),
        "author_verified": t.get("author_verified"),
        "author_id": t.get("author_id"),
    }
