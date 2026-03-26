# logger.py
# ---------------------------------------------------------
# Dual output logger: stdout + scraper.log
# ---------------------------------------------------------

import logging
import sys
from pathlib import Path

from . import config

LOG_FILE = str(config.DATA_DIR / "scraper.log")


def _setup() -> logging.Logger:
    logger = logging.getLogger("scraper")
    if logger.handlers:
        return logger

    logger.setLevel(logging.DEBUG)

    fmt = logging.Formatter(
        fmt="%(asctime)s  %(levelname)-7s  %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    fh = logging.FileHandler(LOG_FILE, encoding="utf-8")
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(fmt)

    sh = logging.StreamHandler(sys.stdout)
    sh.setLevel(logging.INFO)
    sh.setFormatter(fmt)

    logger.addHandler(fh)
    logger.addHandler(sh)
    return logger


log = _setup()
