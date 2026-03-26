# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

xScraper is a full-stack Twitter/X scraper with a React frontend and Python/FastAPI backend. The scraper uses Playwright for browser automation, intercepting GraphQL API responses (not DOM scraping) to collect tweet data while avoiding detection through stealth techniques and human-like scrolling patterns.

## Commands

```bash
# ── Backend ──────────────────────────────────────────────
cd backend
pip install -r requirements.txt
playwright install chromium --with-deps
python run.py                        # starts FastAPI on :8000

# ── Frontend ─────────────────────────────────────────────
cd frontend
npm install
npm run dev                          # starts Next.js on :3000

# ── Production ───────────────────────────────────────────
docker-compose up --build
```

## Architecture

```
xScraper/
├── backend/
│   ├── run.py                   ← uvicorn entry point
│   ├── app/
│   │   ├── api.py               ← FastAPI app + SSE endpoints
│   │   ├── cookies.py           ← Login flow, cookie management
│   │   └── scraper/
│   │       ├── config.py        ← Infrastructure defaults + ScrapeParams dataclass
│   │       ├── browser.py       ← Stealth Chromium launch
│   │       ├── scroller.py      ← Infinite scroll loop with progress callbacks
│   │       ├── interceptor.py   ← GraphQL XHR interception + UserCollector
│   │       ├── storage.py       ← JSON/CSV persistence with dedup
│   │       └── logger.py        ← Dual logging (stdout + file)
│   └── data/                    ← Output files (gitignored)
├── frontend/
│   ├── src/app/
│   │   ├── page.tsx             ← Landing page (scrape form + results)
│   │   └── analyze/page.tsx     ← Phase 2 placeholder
│   ├── src/components/
│   │   ├── scrape-form.tsx      ← Handle input, tweet count, headless/manual
│   │   ├── progress-feed.tsx    ← SSE progress display
│   │   └── results-summary.tsx  ← Stats cards
│   └── src/lib/api.ts           ← FastAPI client + SSE reader
├── .env                         ← ENABLE_MANUAL_MODE, DEBUG_MODE
└── docker-compose.yml
```

### Data Flow

```
React UI → POST /api/scrape (SSE) → FastAPI
  → Playwright browser launches
    → Navigate to X profile
      → Scroll triggers GraphQL XHR
        → interceptor.py extracts tweets
          → SSE events stream to frontend
            → storage.py saves to data/
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/health` | Liveness check |
| GET | `/api/config` | Returns `{manual_mode_available, cookies_present}` |
| POST | `/api/login` | Triggers Playwright login window |
| POST | `/api/scrape` | SSE stream — accepts `{target_handle, max_tweets, headless}` |

### SSE Event Types

- `progress` — `{new, total, elapsed_seconds}`
- `rate_limited` — `{empty_scrolls, total, elapsed_seconds}`
- `auth_failed` — `{reason}`
- `complete` — `{total, stats}`
- `error` — `{message}`

## Key Patterns

- **Per-request config**: User-controllable settings (`target_handle`, `max_tweets`, `headless`) passed via `ScrapeParams` dataclass; infrastructure settings stay in `config.py`
- **SSE streaming**: Long-running scrape streams progress events to frontend via `StreamingResponse`
- **Single scrape lock**: Only one scrape at a time (`asyncio.Lock`)
- **Auth failure detection**: Checks for login redirect after navigation + validates first GraphQL response
- **UserCollector**: Per-run instance (not module global) for safe concurrent runs in the future
- **Manual mode gating**: `ENABLE_MANUAL_MODE` env var controls both backend enforcement and frontend visibility

## Configuration

### Environment Variables (.env)

- `ENABLE_MANUAL_MODE` — Show "Manual" browser option (local dev only)
- `DEBUG_MODE` — Log raw GraphQL responses to scraper.log

### Infrastructure Defaults (config.py)

- `SCROLL_DELAY_MIN/MAX` — Human-like randomization (1.5–3.5s)
- `USER_AGENT` — Real Chrome user-agent string
- `XHR_INTERCEPT_PATTERNS` — GraphQL endpoints to capture
- `PAGE_LOAD_TIMEOUT` — 60s page load timeout

## Anti-Detection

- Chromium flag: `--disable-blink-features=AutomationControlled`
- playwright-stealth patches (navigator, WebGL, canvas fingerprinting)
- Real Chrome user-agent, randomized scroll delays (600–900px, 1.5–3.5s)

## Output Files (backend/data/)

- `tweets.json` — Full structured tweet data
- `tweets.csv` — Spreadsheet-friendly format
- `users.json` — Deduplicated user profiles
- `session_cookies.json` — Browser session (auto-saved)
- `scraper.log` — Persistent log file

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
