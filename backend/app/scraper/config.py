# config.py
# ---------------------------------------------------------
# Infrastructure defaults that do NOT change per request.
# User-controllable settings (target_handle, max_tweets,
# headless) come from ScrapeParams at request time.
# ---------------------------------------------------------

from dataclasses import dataclass
from pathlib import Path
import os

# ── Directories ──────────────────────────────────────────
DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

# ── Debug ────────────────────────────────────────────────
DEBUG_MODE = os.getenv("DEBUG_MODE", "false").lower() == "true"

# ── Browser defaults ────────────────────────────────────
BROWSER_WIDTH = 1280
BROWSER_HEIGHT = 900

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/123.0.0.0 Safari/537.36"
)

# ── Timing (seconds) ────────────────────────────────────
SCROLL_DELAY_MIN = 1.5
SCROLL_DELAY_MAX = 3.5
PAGE_LOAD_TIMEOUT = 60_000  # ms

# ── Paths ────────────────────────────────────────────────
COOKIES_FILE = str(DATA_DIR / "session_cookies.json")
OUTPUT_JSON = str(DATA_DIR / "tweets.json")
OUTPUT_CSV = str(DATA_DIR / "tweets.csv")
OUTPUT_USERS = str(DATA_DIR / "users.json")

# ── X internal API patterns ─────────────────────────────
XHR_INTERCEPT_PATTERNS = [
    "UserTweets",
    "UserTweetsAndReplies",
    "TweetDetail",
]

# ── Environment flags ────────────────────────────────────
ENABLE_MANUAL_MODE = os.getenv("ENABLE_MANUAL_MODE", "false").lower() == "true"


@dataclass(frozen=True)
class ScrapeParams:
    """Per-request scraping parameters sent from the frontend."""
    target_handle: str
    max_tweets: int = 100
    headless: bool = True
