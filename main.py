# main.py
# ─────────────────────────────────────────────────────────────
# The only file you run.
#   python main.py
#
# Wires everything together:
#   browser.py  →  scroller.py  →  storage.py
#
# All async because Playwright is async-native. asyncio.run()
# is the bridge between synchronous Python entry point and the
# async world inside.
# ─────────────────────────────────────────────────────────────

import asyncio

from browser import create_stealth_page, save_cookies
from scroller import scrape_profile
from storage import save, plain_text_for_analyzer
from logger import log
import config


async def run() -> None:
    log.info("=" * 50)
    log.info(f"Run started — target: @{config.TARGET_HANDLE}, max: {config.MAX_TWEETS}")

    pw, context, page = await create_stealth_page()

    try:
        tweets = await scrape_profile(page)

        if not tweets:
            log.warning("No tweets collected. Check cookies or target handle.")
            return

        save(tweets)
        log.info(f"Run complete — {len(tweets)} tweets saved.")

        preview = plain_text_for_analyzer(tweets)
        log.info(f"Style analyzer text ready ({len(preview)} chars)")

    except Exception as e:
        log.error(f"Run failed: {e}", exc_info=True)

    finally:
        await save_cookies(context)
        await context.close()
        await pw.stop()
        log.info("Browser closed cleanly.")


if __name__ == "__main__":
    asyncio.run(run())
