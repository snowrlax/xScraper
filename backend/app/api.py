# api.py
# ---------------------------------------------------------
# FastAPI app with SSE streaming for scrape progress.
#
# Endpoints:
#   GET  /api/config   → manual_mode, cookie_status
#   POST /api/login    → trigger Playwright login window
#   POST /api/scrape   → SSE stream of scrape progress
#   GET  /api/health   → liveness check
# ---------------------------------------------------------

# ── Python 3.14 compatibility patch ───────────────────
# Must run BEFORE importing pydantic/fastapi.
import sys
import typing

if sys.version_info >= (3, 14):
    _original_eval_type = typing._eval_type

    def _patched_eval_type(*args, **kwargs):
        kwargs.pop("prefer_fwd_module", None)
        return _original_eval_type(*args, **kwargs)

    typing._eval_type = _patched_eval_type
# ─────────────────────────────────────────────────────────

import asyncio
import json
import queue
import threading
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from .cookies import cookies_exist, run_login_flow
from .scraper.browser import create_stealth_page, save_cookies
from .scraper.config import ScrapeParams, SessionPaths, ENABLE_MANUAL_MODE, DATA_DIR, create_session_paths
from .scraper.scroller import scrape_profile, AuthFailedError
from .scraper.storage import save
from .scraper.reader import list_data_tree, load_session
from .scraper.logger import log
from .playwright_compat import run_playwright_with_events

# ── State ────────────────────────────────────────────────
_scrape_lock = threading.Lock()


@asynccontextmanager
async def lifespan(app: FastAPI):
    log.info("xScraper API starting up")
    yield
    log.info("xScraper API shutting down")


app = FastAPI(title="xScraper API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Request / Response models ────────────────────────────

class ScrapeRequest(BaseModel):
    target_handle: str = Field(..., min_length=1, max_length=50)
    max_tweets: int = Field(default=100, ge=10, le=1000)
    headless: bool = True
    scroll_speed: float = Field(default=1.0, ge=0.5, le=2.0)


class ConfigResponse(BaseModel):
    manual_mode_available: bool
    cookies_present: bool


class LoginResponse(BaseModel):
    status: str
    message: str = ""
    cookies_count: int = 0


class SessionSummary(BaseModel):
    session_id: str
    scraped_at: str
    tweet_count: int
    file_size_bytes: int


class UserSummary(BaseModel):
    handle: str
    session_count: int
    sessions: list[SessionSummary]


class DataTreeResponse(BaseModel):
    users: list[UserSummary]


class SessionDetailResponse(BaseModel):
    handle: str
    session_id: str
    scraped_at: str
    stats: dict
    tweets: list[dict]
    users_count: int


# ── Endpoints ────────────────────────────────────────────

@app.get("/api/health")
async def health():
    return {"status": "ok"}


@app.get("/api/config", response_model=ConfigResponse)
async def get_config():
    return ConfigResponse(
        manual_mode_available=ENABLE_MANUAL_MODE,
        cookies_present=cookies_exist(),
    )


@app.get("/api/data/tree", response_model=DataTreeResponse)
async def get_data_tree():
    """List all scraped users and their sessions."""
    users = list_data_tree()
    return DataTreeResponse(users=users)


@app.get("/api/data/{handle}/sessions/{session_id}", response_model=SessionDetailResponse)
async def get_session_detail(handle: str, session_id: str):
    """Get full tweet data and stats for a specific session."""
    try:
        result = load_session(handle, session_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return SessionDetailResponse(**result)


@app.post("/api/login", response_model=LoginResponse)
async def login():
    """Trigger Playwright login window for manual X authentication."""
    result = await run_login_flow()
    if result["status"] == "timeout":
        raise HTTPException(status_code=408, detail=result["message"])
    return LoginResponse(
        status="ok",
        message="Login successful",
        cookies_count=result.get("cookies_count", 0),
    )


@app.post("/api/scrape")
async def scrape(request: ScrapeRequest):
    """
    Start a scraping job. Returns an SSE stream of progress events.
    """
    if not request.headless and not ENABLE_MANUAL_MODE:
        raise HTTPException(
            status_code=400,
            detail="Manual (non-headless) mode is not available in this environment.",
        )

    if _scrape_lock.locked():
        raise HTTPException(
            status_code=409,
            detail="A scrape is already in progress. Please wait.",
        )

    if not cookies_exist():
        raise HTTPException(
            status_code=401,
            detail="No session cookies found. Please log in first.",
        )

    params = ScrapeParams(
        target_handle=request.target_handle.lstrip("@"),
        max_tweets=request.max_tweets,
        headless=request.headless,
        scroll_speed=request.scroll_speed,
    )

    # Build the coroutine factory for the Playwright thread
    async def scrape_coro(on_event):
        """Runs entirely inside the ProactorEventLoop thread."""
        with _scrape_lock:
            session_paths = create_session_paths(params.target_handle)
            pw, context, page = await create_stealth_page(params)
            try:
                tweets, users = await scrape_profile(
                    page, params, on_progress=on_event
                )
                stats = save(tweets, users, session_paths)
                on_event({
                    "type": "complete",
                    "total": stats.get("total_tweets", 0),
                    "stats": stats,
                    "session_path": str(session_paths.session_dir.relative_to(DATA_DIR)),
                })
            except AuthFailedError as e:
                on_event({"type": "auth_failed", "reason": str(e)})
            except Exception as e:
                log.error(f"Scrape failed: {e}", exc_info=True)
                on_event({"type": "error", "message": str(e)})
            finally:
                await save_cookies(context)
                await context.close()
                await pw.stop()

    # Thread-safe queue bridges Playwright thread → SSE generator
    event_queue: queue.Queue[dict] = queue.Queue()

    # Launch Playwright in a dedicated ProactorEventLoop thread
    run_playwright_with_events(scrape_coro, event_queue)

    async def event_stream():
        """Yield SSE events from the queue until done."""
        loop = asyncio.get_event_loop()
        while True:
            # Non-blocking poll so we don't block uvicorn's loop
            event = await loop.run_in_executor(None, event_queue.get)
            if event.get("type") == "_done":
                break
            yield f"data: {json.dumps(event)}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
