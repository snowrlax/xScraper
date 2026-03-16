# get_cookies.py
# ─────────────────────────────────────────────────────────────
# Run this ONCE on your local machine (not the server).
# It opens a visible browser, you log in manually to X,
# and it saves session_cookies.json which you then scp to the server.
#
# Usage (local machine only):
#   python get_cookies.py
#   scp session_cookies.json user@yourserver:/path/to/project/
# ─────────────────────────────────────────────────────────────

import asyncio
import json
from playwright.async_api import async_playwright


async def get_cookies():
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(
            headless=False,      # must be visible so you can log in
            args=["--disable-blink-features=AutomationControlled"]
        )
        context = await browser.new_context()
        page = await context.new_page()

        print("Opening X login page...")
        await page.goto("https://x.com/login")

        print("Please log in manually in the browser window.")
        print("Waiting for home feed...")

        # Wait until the URL contains 'home' — login is complete
        await page.wait_for_url("**/home", timeout=120_000)

        cookies = await context.cookies()
        with open("session_cookies.json", "w") as f:
            json.dump(cookies, f, indent=2)

        print(f"Done. Saved {len(cookies)} cookies to session_cookies.json")
        print()
        print("Now upload to your server:")
        print("  scp -i ..\pranavs-gcp-key.pem session_cookies.json pranav@104.197.92.63:~/x-scraper")

        await browser.close()


asyncio.run(get_cookies())
