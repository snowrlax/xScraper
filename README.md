# 🐦 xScraper

**A stealthy Twitter/X scraper powered by Playwright**

Intercepts GraphQL API responses instead of DOM scraping for reliable, structured tweet data with anti-detection built in.

---

## ✨ Features

- 🔒 **Stealth mode** — bypasses automation detection
- 📡 **API interception** — captures structured JSON, not fragile DOM elements
- 🔄 **Auto-deduplication** — merges new tweets with existing data
- 📊 **Dual export** — JSON + CSV output
- 🖥️ **Server-ready** — headless mode with cookie-based auth
- 📈 **Live monitoring** — real-time progress dashboard

---

## 🚀 Quick Start (Local)

```bash
# 1. Install dependencies
pip install playwright playwright-stealth
playwright install chromium

# 2. Configure target
# Edit config.py → set TARGET_HANDLE to the profile you want

# 3. First run (logs in & saves cookies)
# Set HEADLESS=False in config.py
python main.py
# Log in manually when browser opens → cookies auto-saved

# 4. Run scraper (headless)
# Set HEADLESS=True in config.py
python main.py
```

---

## 🖥️ Server Deployment

**Step 1: Generate cookies locally**
```bash
python get_cookies.py
# Browser opens → log in to X → window closes
# session_cookies.json is created
```

**Step 2: Upload to server**
```bash
scp session_cookies.json user@yourserver:/path/to/project/
```

**Step 3: Install on server**
```bash
pip install playwright playwright-stealth
playwright install chromium --with-deps   # --with-deps is required on Linux
```

**Step 4: Run**
```bash
python main.py   # fully headless, no display needed
```

> 💡 The `--with-deps` flag installs system libraries (`libglib2.0`, `libnss3`, etc.) that Chromium needs on Linux servers.

---

## 📈 Monitoring

Run in a separate terminal while scraping:

```bash
python monitor.py
```

Shows:
- ✅ Scraper status (running/stopped)
- 📊 Progress bar toward `MAX_TWEETS`
- 📁 Output file sizes
- 📝 Live log tail

---

## ⚙️ Configuration

All settings in `config.py`:

| Setting | Description |
|---------|-------------|
| `TARGET_HANDLE` | Profile to scrape (without @) |
| `MAX_TWEETS` | Stop after collecting this many |
| `HEADLESS` | `True` for invisible, `False` for visible browser |
| `SCROLL_DELAY_MIN/MAX` | Random delay range between scrolls |

---

## 📦 Output

| File | Description |
|------|-------------|
| `tweets.json` | Full structured data |
| `tweets.csv` | Spreadsheet-friendly format |
| `session_cookies.json` | Reusable browser session |
| `scraper.log` | Persistent log file |

**Tweet schema:**
```json
{
  "tweet_id": "1234567890",
  "text": "Tweet content...",
  "created_at": "2024-01-15T10:30:00Z",
  "likes": 42,
  "retweets": 5,
  "replies": 3,
  "views": "1.2K",
  "is_retweet": false,
  "is_reply": false,
  "user_handle": "username",
  "tweet_url": "https://x.com/username/status/1234567890"
}
```

---

## 🛡️ Anti-Detection

- Disables `AutomationControlled` Blink feature
- Applies playwright-stealth patches (navigator, WebGL, canvas)
- Uses real Chrome user-agent
- Randomized scroll delays for human-like behavior
- `--disable-gpu` flag for server compatibility

---

## 📁 Project Structure

```
main.py           → Entry point & orchestration
browser.py        → Browser launch with stealth config
scroller.py       → Infinite scroll logic
interceptor.py    → GraphQL response capture
storage.py        → JSON/CSV persistence
logger.py         → Dual logging (stdout + file)
config.py         → All configuration settings
get_cookies.py    → Cookie generator (local use)
monitor.py        → Progress dashboard
```

---

## 📝 License

MIT
