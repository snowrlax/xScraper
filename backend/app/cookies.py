# cookies.py
# ---------------------------------------------------------
# Cookie management: check status, trigger login flow.
# Called by the FastAPI endpoints.
# ---------------------------------------------------------

import json
from pathlib import Path

from playwright.async_api import async_playwright

from .scraper import config
from .scraper.logger import log
from .playwright_compat import run_playwright_async


def cookies_exist() -> bool:
    """Check if session_cookies.json exists and is non-empty."""
    path = Path(config.COOKIES_FILE)
    if not path.exists():
        return False
    try:
        with open(path) as f:
            cookies = json.load(f)
        return len(cookies) > 0
    except (json.JSONDecodeError, OSError):
        return False


async def _login_flow_impl() -> dict:
    """Actual login flow — runs inside ProactorEventLoop thread."""
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(
            headless=False,
            args=["--disable-blink-features=AutomationControlled"],
        )
        context = await browser.new_context()
        page = await context.new_page()

        log.info("Opening X login page for manual login...")
        await page.goto("https://x.com/login")

        try:
            await page.wait_for_url("**/home", timeout=120_000)
        except Exception:
            await browser.close()
            return {"status": "timeout", "message": "Login not completed within 2 minutes."}

        cookies = await context.cookies()
        with open(config.COOKIES_FILE, "w") as f:
            json.dump(cookies, f, indent=2)

        await browser.close()
        log.info(f"Login successful — saved {len(cookies)} cookies.")
        return {"status": "ok", "cookies_count": len(cookies)}


async def run_login_flow() -> dict:
    """Run the login flow in a Playwright-compatible event loop."""
    return await run_playwright_async(_login_flow_impl())
