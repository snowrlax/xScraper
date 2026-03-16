# browser.py  (server-safe version)
# ─────────────────────────────────────────────────────────────
# On a headless server there is no display, so we never attempt
# an interactive login here. Cookies must exist before running.
# Use get_cookies.py on your local machine to generate them.
#
# Big picture:
#   1. Launch Chromium with realistic flags
#   2. Apply playwright-stealth patches (hides webdriver signals)
#   3. Set a real user-agent and viewport
#   4. Load saved cookies if they exist (so we stay logged in)
#   5. If no cookies exist → open visibly so you can log in manually
# ─────────────────────────────────────────────────────────────

import json
import os
import asyncio
from pathlib import Path
from playwright.async_api import async_playwright, Page, BrowserContext
from playwright_stealth import Stealth

import config


async def create_stealth_page() -> tuple[object, BrowserContext, Page]:
    """
    Launch a stealth-patched browser and return
    (playwright, context, page) so the caller can close them cleanly.
    """
    pw = await async_playwright().start()

    # launch_args mimic a real Chrome install.
    # --disable-blink-features=AutomationControlled is the single
    # most important flag — it removes the automation banner and
    # clears the navigator.webdriver property at the C++ level,
    # before JavaScript even runs.
    launch_args = [
        "--disable-blink-features=AutomationControlled",
        "--no-sandbox",
        "--disable-dev-shm-usage",
        "--disable-infobars",
        f"--window-size={config.BROWSER_WIDTH},{config.BROWSER_HEIGHT}",
    ]

    browser = await pw.chromium.launch(
        headless=config.HEADLESS,
        args=launch_args,
    )

    # A "context" is like a fresh browser profile — its own cookies,
    # localStorage, and cache. We always create one per run so state
    # doesn't bleed between scraping sessions.
    context = await browser.new_context(
        viewport={"width": config.BROWSER_WIDTH, "height": config.BROWSER_HEIGHT},
        user_agent=config.USER_AGENT,
        # Telling the site we accept English reduces the chance of
        # being served a CAPTCHA or a "confirm your location" dialog.
        locale="en-US",
        timezone_id="America/New_York",
    )

    page = await context.new_page()

    # playwright-stealth runs a bundle of JS patches BEFORE any page
    # script executes. It spoofs things like:
    #   - navigator.plugins  (real Chrome has 3 plugins; headless has 0)
    #   - navigator.languages
    #   - window.chrome object presence
    #   - WebGL renderer string  (headless leaks "SwiftShader")
    #   - Canvas fingerprint noise
    await Stealth().apply_stealth_async(page)

    # Load cookies if we have a saved session
    if Path(config.COOKIES_FILE).exists():
        await _load_cookies(context)
        print("[browser] Loaded saved session cookies.")
    else:
        print("[browser] No saved cookies found.")
        print("[browser] Set HEADLESS=False in config.py, log in manually,")
        print("[browser] then re-run — cookies will be saved automatically.")
        await _interactive_login(context, page)

    return pw, context, page


async def save_cookies(context: BrowserContext) -> None:
    """Persist the current session cookies to disk."""
    cookies = await context.cookies()
    with open(config.COOKIES_FILE, "w") as f:
        json.dump(cookies, f, indent=2)
    print(f"[browser] Session saved to {config.COOKIES_FILE}")


async def _load_cookies(context: BrowserContext) -> None:
    with open(config.COOKIES_FILE) as f:
        cookies = json.load(f)
    await context.add_cookies(cookies)


async def _interactive_login(context: BrowserContext, page: Page) -> None:
    """
    Opens X login page and waits for you to log in manually.
    Once the home feed is detected, cookies are saved automatically.
    This only runs ONCE — after that, cookies handle everything.
    """
    # Force visible for the login flow regardless of config.HEADLESS
    # (can't log in if you can't see the browser)
    print("[browser] Opening X login page — please log in manually in the browser.")
    await page.goto("https://x.com/login", wait_until="networkidle")

    # Poll until we see the home feed URL — that means login succeeded
    print("[browser] Waiting for you to complete login...")
    for _ in range(120):   # wait up to 2 minutes
        await asyncio.sleep(1)
        if "home" in page.url or "/feed" in page.url:
            break
    else:
        raise TimeoutError("Login not detected after 2 minutes.")

    await save_cookies(context)
    print("[browser] Login successful — cookies saved for future runs.")
