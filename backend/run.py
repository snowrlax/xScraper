"""Run the FastAPI server: python run.py"""

import sys
import typing
from pathlib import Path

# ── Python 3.14 compatibility patch ─────────────────────
if sys.version_info >= (3, 14):
    _original_eval_type = typing._eval_type

    def _patched_eval_type(*args, **kwargs):
        kwargs.pop("prefer_fwd_module", None)
        return _original_eval_type(*args, **kwargs)

    typing._eval_type = _patched_eval_type

import uvicorn
from dotenv import load_dotenv

# Load .env from project root
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

if __name__ == "__main__":
    uvicorn.run("app.api:app", host="0.0.0.0", port=8000, reload=True)
