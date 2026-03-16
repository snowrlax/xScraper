# scroller.py
# ─────────────────────────────────────────────────────────────
# Big picture:
#   X's timeline uses "virtual scrolling" — it only renders the
#   tweets currently in the viewport and loads more as you scroll.
#   There is no pagination, no "next page" URL, no page number.
#
#   The only trigger for new data is: scroll down → browser fires
#   a new XHR to UserTweets → new tweets render.
#
#   This module owns that loop:
#     1. Navigate to the profile
#     2. Scroll in increments that look human
#     3. After each scroll, wait for network to settle
#        (meaning: the new XHR has come back)
#     4. Check if we've hit MAX_TWEETS or stopped getting new ones
#     5. Exit cleanly
#
#   The interceptor runs in parallel (via Playwright's event system)
#   and feeds tweets into a shared set as they arrive.
# ─────────────────────────────────────────────────────────────

import asyncio
import random
from playwright.async_api import Page

import config
from interceptor import attach_interceptor


async def scrape_profile(page: Page) -> list[dict]:
    """
    Navigate to the target profile and scroll until we hit MAX_TWEETS
    or the page stops yielding new content.

    Returns a deduplicated list of tweet dicts sorted newest-first.
    """
    collected: dict[str, dict] = {}   # tweet_id → tweet dict (auto-dedupes)
    new_in_last_batch = [0]           # mutable so the closure can write to it

    def on_tweets(tweets: list[dict]) -> None:
        """Callback — called by interceptor every time a batch arrives."""
        before = len(collected)
        for t in tweets:
            tid = t.get("tweet_id")
            if tid and tid not in collected:
                collected[tid] = t
        new_in_last_batch[0] = len(collected) - before
        print(f"[scroller] +{new_in_last_batch[0]} tweets  |  total: {len(collected)}")

    # Wire up the XHR interceptor BEFORE navigating so we don't miss
    # the first batch that fires on initial page load.
    attach_interceptor(page, on_tweets)

    url = f"https://x.com/{config.TARGET_HANDLE}"
    print(f"[scroller] Navigating to {url}")
    await page.goto(url, wait_until="load", timeout=config.PAGE_LOAD_TIMEOUT)

    # Give the initial XHR time to fire and return

    # ── Scroll loop ───────────────────────────────────────────
    no_new_streak = 0   # how many consecutive scrolls yielded nothing new

    while len(collected) < config.MAX_TWEETS:
        # Scroll down by a randomised amount — between 600px and 900px.
        # A fixed 800px every time is a bot fingerprint.
        scroll_px = random.randint(600, 900)
        await page.evaluate(f"window.scrollBy(0, {scroll_px})")

        # Random human-like pause between scrolls
        delay = random.uniform(config.SCROLL_DELAY_MIN, config.SCROLL_DELAY_MAX)
        await asyncio.sleep(delay)

        # Wait for the network to settle — this means the new XHR
        # request has completed and the interceptor has fired.
        try:
            await page.wait_for_load_state("networkidle", timeout=8_000)
        except Exception:
            # networkidle timeout is fine — X sometimes keeps a background
            # websocket open. We just continue.
            pass

        # Check if we're stuck (end of timeline or rate limited)
        if new_in_last_batch[0] == 0:
            no_new_streak += 1
            print(f"[scroller] No new tweets for {no_new_streak} scroll(s).")
        else:
            no_new_streak = 0

        # After 5 consecutive empty scrolls, assume we've reached
        # the end of the timeline.
        if no_new_streak >= 5:
            print("[scroller] Reached end of timeline or rate limit. Stopping.")
            break

        # Reset batch counter for next iteration
        new_in_last_batch[0] = 0

    print(f"[scroller] Done. Collected {len(collected)} unique tweets.")

    # Sort newest-first by tweet_id (Twitter IDs are time-ordered)
    return sorted(collected.values(), key=lambda t: t["tweet_id"], reverse=True)
