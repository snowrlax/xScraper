# logger.py
# ─────────────────────────────────────────────────────────────
# Sets up a logger that writes to both:
#   - stdout (so tmux / nohup shows live output)
#   - scraper.log (so you can check history after the fact)
#
# Every other module imports `log` from here instead of print().
# ─────────────────────────────────────────────────────────────

import logging
import sys
from pathlib import Path

LOG_FILE = "scraper.log"

def _setup() -> logging.Logger:
    logger = logging.getLogger("scraper")
    logger.setLevel(logging.DEBUG)

    fmt = logging.Formatter(
        fmt="%(asctime)s  %(levelname)-7s  %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # File handler — append mode so history is preserved across runs
    fh = logging.FileHandler(LOG_FILE, encoding="utf-8")
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(fmt)

    # Stdout handler
    sh = logging.StreamHandler(sys.stdout)
    sh.setLevel(logging.INFO)
    sh.setFormatter(fmt)

    logger.addHandler(fh)
    logger.addHandler(sh)
    return logger

log = _setup()
