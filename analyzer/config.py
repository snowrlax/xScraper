# analyzer/config.py
# ─────────────────────────────────────────────────────────────
# Configuration for the analytics CLI and LLM integration.
# ─────────────────────────────────────────────────────────────

import os
from pathlib import Path

# Load .env file from project root
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / ".env")

# ── LLM Settings ────────────────────────────────────────────

# OpenAI API key - set via environment variable
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")

# Model to use for analysis
# Options: "gpt-4o", "gpt-4o-mini", "gpt-4-turbo"
LLM_MODEL = os.environ.get("LLM_MODEL", "gpt-4o")

# Temperature for generation (higher = more creative)
LLM_TEMPERATURE = 0.7

# Max tokens for responses
LLM_MAX_TOKENS = 2000

# ── Context Settings ────────────────────────────────────────

# Max tweets to include in LLM context
MAX_CONTEXT_TWEETS = 100

# Number of top-engaged tweets to prioritize
TOP_ENGAGED_SAMPLE = 50

# Number of recent tweets to include
RECENT_SAMPLE = 30

# Number of random tweets for diversity
RANDOM_SAMPLE = 20

# ── Voice Cloning Settings ──────────────────────────────────

# Number of example tweets for few-shot voice cloning
VOICE_CLONE_EXAMPLES = 20

# Prioritize high-engagement examples
PRIORITIZE_ENGAGEMENT = True
