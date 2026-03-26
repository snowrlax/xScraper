# reader.py
# ---------------------------------------------------------
# Read back scraped data from per-user, per-session dirs.
# ---------------------------------------------------------

import json
import os
import re
from pathlib import Path

from .config import DATA_DIR
from .storage import get_tweet_stats
from .logger import log


def list_data_tree() -> list[dict]:
    """
    Scan DATA_DIR for user directories and their session subdirs.
    Returns sorted list of user summaries with nested sessions.
    """
    users = []

    if not DATA_DIR.exists():
        return []

    for entry in sorted(DATA_DIR.iterdir()):
        if not entry.is_dir():
            continue

        sessions = []
        for session_dir in sorted(entry.iterdir(), reverse=True):
            if not session_dir.is_dir():
                continue

            tweets_file = session_dir / "tweets.json"
            if not tweets_file.exists():
                continue

            try:
                with open(tweets_file, encoding="utf-8") as f:
                    tweet_count = len(json.load(f))
                file_size = os.path.getsize(tweets_file)
            except (json.JSONDecodeError, OSError):
                log.warning(f"Skipping corrupt session: {session_dir}")
                continue

            scraped_at = _session_id_to_iso(session_dir.name)

            sessions.append({
                "session_id": session_dir.name,
                "scraped_at": scraped_at,
                "tweet_count": tweet_count,
                "file_size_bytes": file_size,
            })

        if sessions:
            users.append({
                "handle": entry.name,
                "session_count": len(sessions),
                "sessions": sessions,
            })

    return users


def load_session(handle: str, session_id: str) -> dict:
    """
    Load full tweet data and stats for a specific session.
    Raises ValueError for invalid input, FileNotFoundError if missing.
    """
    _validate_handle(handle)
    _validate_session_id(session_id)
    session_dir = _safe_resolve(handle, session_id)

    tweets_file = session_dir / "tweets.json"
    users_file = session_dir / "users.json"

    if not tweets_file.exists():
        raise FileNotFoundError(f"Session not found: {handle}/{session_id}")

    with open(tweets_file, encoding="utf-8") as f:
        tweets = json.load(f)

    stats = get_tweet_stats(tweets)

    users_count = 0
    if users_file.exists():
        try:
            with open(users_file, encoding="utf-8") as f:
                users_data = json.load(f)
            users_count = len(users_data)
        except (json.JSONDecodeError, OSError):
            pass

    stats["users_saved"] = users_count

    return {
        "handle": handle,
        "session_id": session_id,
        "scraped_at": _session_id_to_iso(session_id),
        "stats": stats,
        "tweets": tweets,
        "users_count": users_count,
    }


def _validate_handle(handle: str) -> None:
    if not re.fullmatch(r"[a-z0-9_]+", handle):
        raise ValueError(f"Invalid handle: {handle}")


def _validate_session_id(session_id: str) -> None:
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2}(_\d+)?", session_id):
        raise ValueError(f"Invalid session_id: {session_id}")


def _safe_resolve(handle: str, session_id: str) -> Path:
    """Construct and verify path is under DATA_DIR."""
    candidate = (DATA_DIR / handle / session_id).resolve()
    if not str(candidate).startswith(str(DATA_DIR.resolve())):
        raise ValueError("Path traversal detected")
    return candidate


def _session_id_to_iso(session_id: str) -> str:
    """Convert '2026-03-26_10-04-01' to '2026-03-26T10:04:01Z'."""
    base = session_id.split("_")[0]  # date part
    parts = session_id.split("_")
    if len(parts) >= 2:
        time_part = parts[1]
        return f"{base}T{time_part.replace('-', ':')}Z"
    return f"{base}T00:00:00Z"
