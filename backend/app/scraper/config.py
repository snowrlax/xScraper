# config.py
# ---------------------------------------------------------
# Infrastructure defaults that do NOT change per request.
# User-controllable settings (target_handle, max_tweets,
# headless) come from ScrapeParams at request time.
# ---------------------------------------------------------

import re
from dataclasses import dataclass
from datetime import datetime, timezone
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
    scroll_speed: float = 1.0


@dataclass(frozen=True)
class SessionPaths:
    """Paths for a single scrape session's output files."""
    session_dir: Path
    json_file: Path
    csv_file: Path
    users_file: Path


def create_session_paths(target_handle: str) -> SessionPaths:
    """Create a timestamped session directory for a scrape target."""
    sanitized = re.sub(r"[^a-zA-Z0-9_]", "", target_handle).lower()
    if not sanitized:
        raise ValueError("Invalid target handle")

    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d_%H-%M-%S")
    session_dir = DATA_DIR / sanitized / timestamp

    # Collision guard (unlikely due to _scrape_lock serialization)
    suffix = 1
    candidate = session_dir
    while candidate.exists():
        candidate = session_dir.parent / f"{timestamp}_{suffix}"
        suffix += 1
    session_dir = candidate

    session_dir.mkdir(parents=True, exist_ok=True)

    return SessionPaths(
        session_dir=session_dir,
        json_file=session_dir / "tweets.json",
        csv_file=session_dir / "tweets.csv",
        users_file=session_dir / "users.json",
    )
