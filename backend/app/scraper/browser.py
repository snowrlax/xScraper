# browser.py
# ---------------------------------------------------------
# Stealth browser launch. Accepts ScrapeParams for headless
# setting; infrastructure config stays in config.py.
# ---------------------------------------------------------

import json
from pathlib import Path

from playwright.async_api import async_playwright, Page, BrowserContext
from playwright_stealth import Stealth

from . import config
from .config import ScrapeParams
from .logger import log


async def create_stealth_page(
    params: ScrapeParams,
) -> tuple[object, BrowserContext, Page]:
    """
    Launch a stealth-patched browser.
    Returns (playwright, context, page).
    """
    pw = await async_playwright().start()

    launch_args = [
        "--disable-blink-features=AutomationControlled",
        "--no-sandbox",
        "--disable-dev-shm-usage",
        "--disable-infobars",
        f"--window-size={config.BROWSER_WIDTH},{config.BROWSER_HEIGHT}",
    ]

    browser = await pw.chromium.launch(
        headless=params.headless,
        args=launch_args,
    )

    context = await browser.new_context(
        viewport={"width": config.BROWSER_WIDTH, "height": config.BROWSER_HEIGHT},
        user_agent=config.USER_AGENT,
        locale="en-US",
        timezone_id="America/New_York",
    )

    page = await context.new_page()
    await Stealth().apply_stealth_async(page)

    # Load saved cookies
    if Path(config.COOKIES_FILE).exists():
        await _load_cookies(context)
        log.info("Loaded saved session cookies.")
    else:
        log.warning("No saved cookies found — scrape will likely fail auth.")

    return pw, context, page


async def save_cookies(context: BrowserContext) -> None:
    """Persist the current session cookies to disk."""
    cookies = await context.cookies()
    with open(config.COOKIES_FILE, "w") as f:
        json.dump(cookies, f, indent=2)
    log.info(f"Session saved to {config.COOKIES_FILE}")


async def _load_cookies(context: BrowserContext) -> None:
    with open(config.COOKIES_FILE) as f:
        cookies = json.load(f)
    await context.add_cookies(cookies)
