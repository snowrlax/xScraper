# scroller.py
# ---------------------------------------------------------
# Infinite scroll loop with SSE-compatible progress callback.
# Accepts ScrapeParams; uses auth failure detection.
# ---------------------------------------------------------

import asyncio
import random
import time
from typing import Callable

from playwright.async_api import Page

from . import config
from .config import ScrapeParams
from .interceptor import attach_interceptor, UserCollector
from .logger import log


class AuthFailedError(Exception):
    """Raised when the scraper detects expired/missing auth."""
    pass


async def scrape_profile(
    page: Page,
    params: ScrapeParams,
    on_progress: Callable[[dict], None] | None = None,
) -> tuple[list[dict], dict[str, dict]]:
    """
    Navigate to the target profile and scroll until max_tweets
    or end of timeline.

    Args:
        page: Playwright page
        params: Per-request scraping parameters
        on_progress: Optional callback for SSE progress events

    Returns:
        (tweets_list, users_dict)
    """
    collected: dict[str, dict] = {}
    new_in_last_batch = [0]
    user_collector = UserCollector()
    start_time = time.time()

    def _emit(event: dict) -> None:
        if on_progress:
            on_progress(event)

    def on_tweets(tweets: list[dict]) -> None:
        before = len(collected)
        for t in tweets:
            tid = t.get("tweet_id")
            if tid and tid not in collected:
                collected[tid] = t
        new_count = len(collected) - before
        new_in_last_batch[0] = new_count
        elapsed = round(time.time() - start_time, 1)
        log.info(f"+{new_count} tweets  |  total: {len(collected)}")
        _emit({
            "type": "progress",
            "new": new_count,
            "total": len(collected),
            "elapsed_seconds": elapsed,
        })

    # Wire up interceptor BEFORE navigating
    attach_interceptor(page, on_tweets, user_collector)

    url = f"https://x.com/{params.target_handle}"
    log.info(f"Navigating to {url}")
    _emit({"type": "progress", "new": 0, "total": 0, "elapsed_seconds": 0})

    await page.goto(url, wait_until="load", timeout=config.PAGE_LOAD_TIMEOUT)

    # ── Auth failure detection ──────────────────────────
    # Check 1: URL redirect to login page
    await asyncio.sleep(2)
    current_url = page.url
    if "/login" in current_url or "/i/flow/login" in current_url:
        _emit({"type": "auth_failed", "reason": "Redirected to login page"})
        raise AuthFailedError("Redirected to login page — cookies expired or missing.")

    # ── Scroll loop ─────────────────────────────────────
    no_new_streak = 0
    new_in_last_batch[0] = 0  # Clear stale count from initial page load

    while len(collected) < params.max_tweets:
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")

        delay = random.uniform(config.SCROLL_DELAY_MIN, config.SCROLL_DELAY_MAX) * params.scroll_speed
        await asyncio.sleep(delay)

        try:
            await page.wait_for_response(
                lambda r: any(p in r.url for p in config.XHR_INTERCEPT_PATTERNS),
                timeout=8_000,
            )
        except Exception:
            pass

        if new_in_last_batch[0] == 0:
            no_new_streak += 1
            _emit({
                "type": "rate_limited",
                "empty_scrolls": no_new_streak,
                "total": len(collected),
                "elapsed_seconds": round(time.time() - start_time, 1),
            })
            log.info(f"No new tweets for {no_new_streak} scroll(s).")
        else:
            no_new_streak = 0

        if no_new_streak >= 5:
            log.info("Reached end of timeline or rate limit. Stopping.")
            break

        new_in_last_batch[0] = 0

    elapsed = round(time.time() - start_time, 1)
    log.info(f"Done. Collected {len(collected)} unique tweets in {elapsed}s.")

    tweets = sorted(collected.values(), key=lambda t: t["tweet_id"], reverse=True)
    return tweets, user_collector.get_all()
