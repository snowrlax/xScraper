# config.py
# ─────────────────────────────────────────────────────────────
# All tunable settings live here. You never need to touch the
# other modules just to change a target account or delay.
# ─────────────────────────────────────────────────────────────

# ── Debug ────────────────────────────────────────────────────
DEBUG_MODE    = True                # Set to False to disable verbose logging

# ── Target ────────────────────────────────────────────────────
TARGET_HANDLE = "marclou"          # without the @
MAX_TWEETS    = 5                   # stop after collecting this many (set to 5 for debugging)

# ── Browser ───────────────────────────────────────────────────
HEADLESS      = False                # False = you can watch the browser
BROWSER_WIDTH  = 1280
BROWSER_HEIGHT = 900

# A real Chrome user-agent. X checks this header and rejects
# outdated or obviously-fake strings.
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/123.0.0.0 Safari/537.36"
)

# ── Timing (seconds) ─────────────────────────────────────────
# Humans don't scroll at perfectly even intervals.
# We randomise between MIN and MAX to avoid bot-pattern detection.
SCROLL_DELAY_MIN = 1.5
SCROLL_DELAY_MAX = 3.5
PAGE_LOAD_TIMEOUT = 60_000          # ms — how long to wait for page load

# ── Paths ─────────────────────────────────────────────────────
COOKIES_FILE  = "session_cookies.json"   # saved after first login
OUTPUT_JSON   = "tweets.json"
OUTPUT_CSV    = "tweets.csv"
OUTPUT_USERS  = "users.json"             # deduplicated user profiles

# ── X internal API patterns ───────────────────────────────────
# When X loads a timeline it fires XHR requests to these URL
# fragments. We watch for these to intercept the raw JSON.
XHR_INTERCEPT_PATTERNS = [
    "UserTweets",           # main timeline feed
    "UserTweetsAndReplies", # if you want replies too
    "TweetDetail",          # individual tweet expansions
]
