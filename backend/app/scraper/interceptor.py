# interceptor.py
# ---------------------------------------------------------
# XHR response interception for GraphQL tweet extraction.
# Uses a per-run UserCollector instead of module globals
# so concurrent runs don't share state.
# ---------------------------------------------------------

import json
import re
from datetime import datetime, timezone
from typing import Callable

from playwright.async_api import Page, Response

from . import config
from .logger import log


class UserCollector:
    """Per-scrape user profile collector."""

    def __init__(self) -> None:
        self._users: dict[str, dict] = {}

    def collect(self, user_result: dict) -> None:
        if not user_result:
            return
        user_id = user_result.get("rest_id", "")
        if not user_id:
            return

        user_core = user_result.get("core", {})
        user_legacy = user_result.get("legacy", {})
        now = datetime.now(timezone.utc).isoformat()

        user_data = {
            "user_id": user_id,
            "handle": user_core.get("screen_name", ""),
            "name": user_core.get("name", ""),
            "bio": user_legacy.get("description", ""),
            "followers": user_legacy.get("followers_count", 0),
            "following": user_legacy.get("friends_count", 0),
            "tweet_count": user_legacy.get("statuses_count", 0),
            "verified": user_result.get("is_blue_verified", False),
            "avatar_url": user_result.get("avatar", {}).get("image_url", ""),
            "banner_url": user_legacy.get("profile_banner_url", ""),
            "created_at": user_core.get("created_at", ""),
            "last_updated": now,
        }

        if user_id not in self._users:
            user_data["first_seen"] = now
        else:
            user_data["first_seen"] = self._users[user_id].get("first_seen", now)

        self._users[user_id] = user_data

    def get_all(self) -> dict[str, dict]:
        return dict(self._users)


def attach_interceptor(
    page: Page,
    on_tweets: Callable[[list[dict]], None],
    user_collector: UserCollector,
) -> None:
    """Attach response interceptor to capture tweet data from GraphQL responses."""

    async def handle_response(response: Response) -> None:
        url = response.url
        if not _is_tweet_endpoint(url):
            return
        try:
            data = await response.json()
        except Exception:
            return

        tweets = _extract_tweets(data, user_collector)
        if tweets:
            on_tweets(tweets)

    page.on("response", handle_response)


def _is_tweet_endpoint(url: str) -> bool:
    return any(pattern in url for pattern in config.XHR_INTERCEPT_PATTERNS)


def _extract_tweets(data: dict, user_collector: UserCollector) -> list[dict]:
    """Walk the GraphQL response and extract all tweet objects."""
    if config.DEBUG_MODE:
        raw_json = json.dumps(data, indent=2)
        log.debug(f"[RAW RESPONSE] (truncated):\n{raw_json[:5000]}")

    found: list[dict] = []
    _walk(data, found, user_collector)
    return found


def _walk(
    node,
    found: list,
    user_collector: UserCollector,
    context: dict | None = None,
) -> None:
    if context is None:
        context = {}

    if isinstance(node, dict):
        if node.get("clientEventInfo", {}).get("component") == "pinned_tweets":
            context = {**context, "is_pinned": True}

        if "tweet_results" in node:
            tweet = _parse_tweet_node(
                node["tweet_results"].get("result", {}),
                user_collector,
                context,
            )
            if tweet:
                found.append(tweet)
        else:
            for value in node.values():
                _walk(value, found, user_collector, context)
    elif isinstance(node, list):
        for item in node:
            _walk(item, found, user_collector, context)


def _parse_tweet_node(
    result: dict,
    user_collector: UserCollector,
    context: dict | None = None,
) -> dict | None:
    if context is None:
        context = {}

    if not result:
        return None

    typename = result.get("__typename")
    if typename not in ("Tweet", "TweetWithVisibilityResults"):
        return None

    if typename == "TweetWithVisibilityResults":
        result = result.get("tweet", {})
        if not result:
            return None

    legacy = result.get("legacy", {})
    if not legacy:
        return None

    core = result.get("core", {})
    user_result = core.get("user_results", {}).get("result", {})
    user_core = user_result.get("core", {})

    if config.DEBUG_MODE:
        log.debug(f"[TWEET NODE] __typename: {result.get('__typename')}")
        log.debug(f"[TWEET NODE] All keys: {list(result.keys())}")
        log.debug(f"[TWEET NODE] core: {json.dumps(core, indent=2) if core else 'EMPTY'}")

    author_id = user_result.get("rest_id", "")
    author_handle = user_core.get("screen_name", "") or "unknown"
    author_name = user_core.get("name", "") or ""
    author_verified = user_result.get("is_blue_verified", False)

    user_collector.collect(user_result)

    tweet_id = legacy.get("id_str") or result.get("rest_id", "")
    text = legacy.get("full_text", "")
    full_text = _extract_note_tweet(result)

    likes = legacy.get("favorite_count", 0)
    retweets = legacy.get("retweet_count", 0)
    replies = legacy.get("reply_count", 0)
    quotes = legacy.get("quote_count", 0)
    bookmarks = legacy.get("bookmark_count", 0)
    views = _safe_int(result.get("views", {}).get("count"))

    created_at = legacy.get("created_at", "")
    scraped_at = datetime.now(timezone.utc).isoformat()
    lang = legacy.get("lang", "")
    source = _clean_source(result.get("source", ""))

    conversation_id = legacy.get("conversation_id_str", "")
    in_reply_to_tweet_id = legacy.get("in_reply_to_status_id_str")
    in_reply_to_user_id = legacy.get("in_reply_to_user_id_str")
    in_reply_to_handle = legacy.get("in_reply_to_screen_name")

    entities = _extract_entities(legacy.get("entities", {}))
    quoted_tweet = _extract_linked_tweet(
        result.get("quoted_status_result", {}), user_collector
    )
    retweeted_tweet = _extract_linked_tweet(
        legacy.get("retweeted_status_result", {}), user_collector
    )

    is_retweet = text.startswith("RT @") or retweeted_tweet is not None
    is_reply = in_reply_to_tweet_id is not None
    is_quote = quoted_tweet is not None
    is_self_reply = is_reply and in_reply_to_user_id == author_id
    is_pinned = context.get("is_pinned", False)

    return {
        "tweet_id": tweet_id,
        "conversation_id": conversation_id,
        "in_reply_to_tweet_id": in_reply_to_tweet_id,
        "in_reply_to_user_id": in_reply_to_user_id,
        "in_reply_to_handle": in_reply_to_handle,
        "text": text,
        "full_text": full_text,
        "lang": lang,
        "source": source,
        "author_id": author_id,
        "author_handle": author_handle,
        "author_name": author_name,
        "author_verified": author_verified,
        "likes": likes,
        "retweets": retweets,
        "replies": replies,
        "quotes": quotes,
        "bookmarks": bookmarks,
        "views": views,
        "is_retweet": is_retweet,
        "is_reply": is_reply,
        "is_quote": is_quote,
        "is_self_reply": is_self_reply,
        "is_pinned": is_pinned,
        "created_at": created_at,
        "scraped_at": scraped_at,
        "hashtags": entities["hashtags"],
        "mentions": entities["mentions"],
        "urls": entities["urls"],
        "media": entities["media"],
        "quoted_tweet": quoted_tweet,
        "retweeted_tweet": retweeted_tweet,
        "tweet_url": f"https://x.com/{author_handle}/status/{tweet_id}",
    }


def _extract_note_tweet(result: dict) -> str | None:
    note = result.get("note_tweet", {})
    if not note:
        return None
    return (
        note.get("note_tweet_results", {})
        .get("result", {})
        .get("text", None)
    )


def _extract_entities(entities: dict) -> dict:
    hashtags = [h.get("text", "") for h in entities.get("hashtags", []) if h.get("text")]
    mentions = [m.get("screen_name", "") for m in entities.get("user_mentions", []) if m.get("screen_name")]

    urls = []
    for u in entities.get("urls", []):
        if u.get("expanded_url"):
            urls.append({
                "display": u.get("display_url", ""),
                "expanded": u.get("expanded_url", ""),
            })

    media = []
    for m in entities.get("media", []):
        media_item = {
            "type": m.get("type", ""),
            "url": m.get("media_url_https", "") or m.get("media_url", ""),
        }
        video_info = m.get("video_info", {})
        if video_info:
            media_item["duration_ms"] = video_info.get("duration_millis")
            variants = video_info.get("variants", [])
            video_urls = [v for v in variants if v.get("content_type") == "video/mp4"]
            if video_urls:
                best = max(video_urls, key=lambda x: x.get("bitrate", 0))
                media_item["video_url"] = best.get("url", "")
        media.append(media_item)

    return {
        "hashtags": hashtags,
        "mentions": mentions,
        "urls": urls,
        "media": media,
    }


def _extract_linked_tweet(
    tweet_result: dict, user_collector: UserCollector
) -> dict | None:
    if not tweet_result:
        return None
    result = tweet_result.get("result", {})
    if not result:
        return None
    return _parse_tweet_node(result, user_collector, context={"_nested": True})


def _clean_source(source_html: str) -> str:
    if not source_html:
        return ""
    match = re.search(r">([^<]+)<", source_html)
    return match.group(1) if match else source_html


def _safe_int(value) -> int:
    if value is None:
        return 0
    try:
        return int(value)
    except (ValueError, TypeError):
        return 0
