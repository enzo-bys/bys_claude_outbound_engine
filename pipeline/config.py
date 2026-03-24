"""Configuration and API keys for the outbound pipeline — BuildYourSales.tech"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env.local from project root
PROJECT_ROOT = Path(__file__).parent.parent
load_dotenv(PROJECT_ROOT / ".env.local")


# API Keys
SCRAPINGDOG_API_KEY: str = os.environ.get("SCRAPINGDOG_API_KEY", "")
RAPIDAPI_KEY: str = os.environ.get("RAPIDAPI_KEY", "")
ANTHROPIC_API_KEY: str = os.environ.get("ANTHROPIC_API_KEY", "")
LEMLIST_API_KEY: str = os.environ.get("LEMLIST_API_KEY", "")

# API URLs
SCRAPINGDOG_BASE_URL = "https://api.scrapingdog.com"
RAPIDAPI_BASE_URL = "https://professional-network-data.p.rapidapi.com"
LEMLIST_BASE_URL = "https://api.lemlist.com/api"

# Claude model
CLAUDE_MODEL = "claude-sonnet-4-6"

# Concurrency limits
ENRICH_CONCURRENCY = 10      # Google SERP parallel calls (5 credits each)
LINKEDIN_CONCURRENCY = 10    # RapidAPI LinkedIn parallel calls
LINKEDIN_DELAY = 0.0         # No delay needed for RapidAPI parallel
WRITE_CONCURRENCY = 10       # Claude API parallel calls
INJECT_BATCH_SIZE = 15       # Lemlist leads per batch
INJECT_BATCH_PAUSE = 2.0     # Seconds between batches

# Retry config
MAX_RETRIES = 3
RETRY_BACKOFF_BASE = 2.0     # Exponential backoff: 2s, 4s, 8s

# Logging
LOG_PREFIX = "[Pipeline]"
