# interceptor.py
# ─────────────────────────────────────────────────────────────
# Big picture:
#   X's frontend is a React app. When it loads a timeline it
#   makes authenticated GraphQL-style requests to its own backend:
#
#     GET https://x.com/i/api/graphql/<hash>/UserTweets?variables=...
#
#   The response is JSON containing every tweet, like count,
#   retweet count, timestamp, etc. — exactly what we want.
#
#   Playwright lets us register a listener on page.on("response")
#   that fires for EVERY network response the browser receives.
#   We filter for the URLs we care about, read the JSON body,
#   and extract the tweet objects.
#
#   This approach is:
#     - More reliable than CSS selectors (HTML changes constantly)
#     - Faster (we get data before the DOM even renders it)
#     - Cleaner (structured JSON vs scraping text nodes)
# ─────────────────────────────────────────────────────────────

import asyncio
from typing import Callable
from playwright.async_api import Page, Response

import config


def attach_interceptor(page: Page, on_tweets: Callable[[list[dict]], None]) -> None:
    async def handle_response(response: Response) -> None:
        url = response.url
        if not _is_tweet_endpoint(url):
            return
        try:
            data = await response.json()
        except Exception:
            return
        tweets = _extract_tweets(data)
        if tweets:
            on_tweets(tweets)

    page.on("response", handle_response)


def _is_tweet_endpoint(url: str) -> bool:
    return any(pattern in url for pattern in config.XHR_INTERCEPT_PATTERNS)


def _extract_tweets(data: dict) -> list[dict]:
    found = []
    _walk(data, found)
    return found


def _walk(node, found: list) -> None:
    if isinstance(node, dict):
        if "tweet_results" in node:
            tweet = _parse_tweet_node(node["tweet_results"].get("result", {}))
            if tweet:
                found.append(tweet)
        else:
            for value in node.values():
                _walk(value, found)
    elif isinstance(node, list):
        for item in node:
            _walk(item, found)


def _parse_tweet_node(result: dict) -> dict:
    if not result or result.get("__typename") not in ("Tweet", "TweetWithVisibilityResults"):
        return None

    if result.get("__typename") == "TweetWithVisibilityResults":
        result = result.get("tweet", {})

    legacy = result.get("legacy", {})
    core = result.get("core", {})
    user = core.get("user_results", {}).get("result", {}).get("legacy", {}) or {}

    if not legacy:
        return None

    handle = user.get("screen_name") or "unknown"

    return {
        "tweet_id":    legacy.get("id_str"),
        "text":        legacy.get("full_text", ""),
        "created_at":  legacy.get("created_at"),
        "likes":       legacy.get("favorite_count", 0),
        "retweets":    legacy.get("retweet_count", 0),
        "replies":     legacy.get("reply_count", 0),
        "views":       result.get("views", {}).get("count", 0),
        "is_retweet":  legacy.get("full_text", "").startswith("RT @"),
        "is_reply":    legacy.get("in_reply_to_status_id_str") is not None,
        "lang":        legacy.get("lang"),
        "user_handle": handle,
        "user_name":   user.get("name", ""),
        "tweet_url":   f"https://x.com/{handle}/status/{legacy.get('id_str')}",
    }
