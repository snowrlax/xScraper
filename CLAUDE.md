# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

xScraper is a Python-based Twitter/X scraper using Playwright for browser automation. It intercepts GraphQL API responses (not DOM scraping) to collect tweet data while avoiding detection through stealth techniques and human-like scrolling patterns.

## Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Run scraper (default: headless mode)
python main.py

# Monitor progress in separate terminal
python monitor.py

# Generate cookies locally (run once, then upload to server)
python get_cookies.py

# First-time setup: set HEADLESS=False in config.py, run main.py, log in manually
```

## Architecture

```
main.py           → Async orchestrator (entry point)
    ↓
browser.py        → Chromium launch with stealth patches, cookie management
    ↓
scroller.py       → Profile navigation, infinite scroll loop
    ↓
interceptor.py    → XHR response interception, GraphQL tweet extraction
    ↓
storage.py        → JSON/CSV persistence with deduplication
    ↓
logger.py         → Dual logging (stdout + scraper.log)

Utilities:
get_cookies.py    → Generate session cookies (run locally, upload to server)
monitor.py        → Real-time progress dashboard
```

**Data flow**: Browser launches → Navigate to profile → Scroll triggers XHR → Intercept GraphQL responses → Extract tweets → Merge with existing data → Save JSON/CSV

## Key Patterns

- **XHR Interception over DOM scraping**: Intercepts `graphql/.../UserTweets` responses for structured JSON data
- **Callback-based collection**: `interceptor.attach_interceptor(page, callback)` fires as tweets arrive during scrolling
- **Session persistence**: Cookies saved to `session_cookies.json` for reuse across runs
- **Data accumulation**: `storage.py` merges new tweets with existing `tweets.json` (deduplicates by tweet_id)
- **Termination**: Stops at `MAX_TWEETS` or after 5 consecutive empty scrolls

## Server Deployment Workflow

1. **Local**: Run `python get_cookies.py` → log in manually → `session_cookies.json` created
2. **Upload**: `scp session_cookies.json user@server:/path/to/project/`
3. **Server**: Install with `playwright install chromium --with-deps` (the `--with-deps` flag installs system libs like `libglib2.0`, `libnss3` required on Linux)
4. **Run**: `python main.py` (headless, no display needed)

**Note**: The `--disable-gpu` flag in `browser.py` is essential for VPS/cloud servers without GPU support.

## Configuration (config.py)

All settings centralized in `config.py`:
- `DEBUG_MODE` - Enable verbose logging of raw GraphQL responses and tweet node structures
- `TARGET_HANDLE` - Profile to scrape (no @)
- `MAX_TWEETS` - Collection limit
- `HEADLESS` - True for headless, False for visible browser
- `SCROLL_DELAY_MIN/MAX` - Human-like randomization
- `XHR_INTERCEPT_PATTERNS` - GraphQL endpoints to capture

## Anti-Detection

- Chromium flag: `--disable-blink-features=AutomationControlled`
- playwright-stealth patches (navigator, WebGL, canvas fingerprinting)
- Real Chrome user-agent, randomized scroll delays

## Tweet Data Schema

```json
{
  "tweet_id": "string",
  "conversation_id": "string",
  "text": "string",
  "full_text": "string|null",
  "created_at": "string",
  "scraped_at": "string",
  "lang": "string",
  "source": "string",
  "author_id": "string",
  "author_handle": "string",
  "author_name": "string",
  "author_verified": "boolean",
  "likes": "number",
  "retweets": "number",
  "replies": "number",
  "quotes": "number",
  "bookmarks": "number",
  "views": "number",
  "is_retweet": "boolean",
  "is_reply": "boolean",
  "is_quote": "boolean",
  "is_self_reply": "boolean",
  "is_pinned": "boolean",
  "hashtags": ["string"],
  "mentions": ["string"],
  "urls": [{"display": "string", "expanded": "string"}],
  "media": [{"type": "string", "url": "string"}],
  "quoted_tweet": "object|null",
  "retweeted_tweet": "object|null",
  "tweet_url": "string"
}
```

## Output Files

- `tweets.json` - Full structured tweet data
- `tweets.csv` - Spreadsheet-friendly format
- `users.json` - Deduplicated user profiles collected during scraping
- `session_cookies.json` - Browser session (auto-saved)
- `scraper.log` - Persistent log file (includes debug output when `DEBUG_MODE=True`)

## Analytics Tool

The `analyzer/` package provides visualization and AI-powered tweet analysis.

### Dashboard (Streamlit)

```bash
# Start the analytics dashboard
streamlit run analyzer/dashboard.py
```

Visualizations:
- Engagement over time (likes/retweets/views with rolling averages)
- Posting time heatmap (hour vs day-of-week)
- Top performing content table
- Content type breakdown (original/replies/quotes/retweets)
- Hashtag and mention frequency charts

### Interactive CLI

```bash
# Set OpenAI API key first
export OPENAI_API_KEY="your-key"

# Start interactive chat
python -m analyzer.cli chat

# One-shot commands
python -m analyzer.cli style       # Analyze writing patterns
python -m analyzer.cli hooks       # Extract top-performing hooks
python -m analyzer.cli engagement  # What drives engagement
python -m analyzer.cli profile     # Generate user profile
python -m analyzer.cli generate "topic"  # Generate tweets in user's voice
python -m analyzer.cli check       # Verify API key is configured
```

### Analyzer Architecture

```
analyzer/
    dashboard.py          # Streamlit app
    data_loader.py        # Load/parse tweets.json
    metrics.py            # Engagement calculations
    charts.py             # Plotly chart builders
    config.py             # LLM settings

    cli/
        main.py           # CLI entry point
        chat.py           # Interactive chat loop
        llm_client.py     # OpenAI API wrapper
        context_builder.py # Build LLM context from tweets
        prompts.py        # System prompts for analysis
```
