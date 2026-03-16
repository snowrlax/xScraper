# monitor.py
# ─────────────────────────────────────────────────────────────
# Run this in a second SSH terminal while main.py is running.
#   python monitor.py
#
# It refreshes every 3 seconds and shows:
#   - Is the scraper process alive?
#   - How many tweets collected so far?
#   - Last 10 log lines
#   - Data file sizes
#   - Estimated progress toward MAX_TWEETS
# ─────────────────────────────────────────────────────────────

import os
import sys
import time
import json
import subprocess
from pathlib import Path
from datetime import datetime

import config
from logger import LOG_FILE

REFRESH_SECONDS = 3


def clear():
    os.system("clear" if os.name != "nt" else "cls")


def is_process_running() -> tuple[bool, str]:
    """Check if any python process running main.py exists."""
    try:
        result = subprocess.run(
            ["pgrep", "-a", "-f", "main.py"],
            capture_output=True, text=True
        )
        lines = [l for l in result.stdout.strip().splitlines() if "main.py" in l]
        if lines:
            pid = lines[0].split()[0]
            return True, pid
        return False, ""
    except Exception:
        return False, ""


def tweet_count() -> int:
    p = Path(config.OUTPUT_JSON)
    if not p.exists():
        return 0
    try:
        return len(json.loads(p.read_text()))
    except Exception:
        return 0


def file_size(path: str) -> str:
    p = Path(path)
    if not p.exists():
        return "not created yet"
    size = p.stat().st_size
    if size < 1024:
        return f"{size} B"
    elif size < 1024 ** 2:
        return f"{size/1024:.1f} KB"
    else:
        return f"{size/1024**2:.1f} MB"


def last_log_lines(n=12) -> list[str]:
    p = Path(LOG_FILE)
    if not p.exists():
        return ["(no log file yet)"]
    with open(p, encoding="utf-8") as f:
        lines = f.readlines()
    return [l.rstrip() for l in lines[-n:]]


def progress_bar(current: int, total: int, width=36) -> str:
    pct = min(current / total, 1.0) if total else 0
    filled = int(width * pct)
    bar = "█" * filled + "░" * (width - filled)
    return f"[{bar}] {current}/{total}  ({pct*100:.0f}%)"


def run():
    print("Starting monitor... (Ctrl+C to exit)\n")
    time.sleep(1)

    while True:
        clear()
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        alive, pid = is_process_running()
        count = tweet_count()

        status_icon = "● RUNNING" if alive else "○ STOPPED"
        status_color = "\033[32m" if alive else "\033[31m"   # green / red
        reset = "\033[0m"

        print(f"  X Scraper Monitor                        {now}")
        print(f"  {'─'*54}")
        print(f"  Status   {status_color}{status_icon}{reset}"
              + (f"   (pid {pid})" if pid else ""))
        print(f"  Target   @{config.TARGET_HANDLE}")
        print()
        print(f"  Progress")
        print(f"  {progress_bar(count, config.MAX_TWEETS)}")
        print()
        print(f"  Output files")
        print(f"    {config.OUTPUT_JSON:<28} {file_size(config.OUTPUT_JSON)}")
        print(f"    {config.OUTPUT_CSV:<28} {file_size(config.OUTPUT_CSV)}")
        print(f"    {config.COOKIES_FILE:<28} {file_size(config.COOKIES_FILE)}")
        print()
        print(f"  Last log entries")
        print(f"  {'─'*54}")
        for line in last_log_lines():
            print(f"  {line}")
        print(f"  {'─'*54}")
        print(f"\n  Refreshing every {REFRESH_SECONDS}s   Ctrl+C to exit")

        time.sleep(REFRESH_SECONDS)


if __name__ == "__main__":
    try:
        run()
    except KeyboardInterrupt:
        print("\nMonitor stopped.")
