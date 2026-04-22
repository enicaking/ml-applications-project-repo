"""Configuration constants for the Komoot scraper."""
from pathlib import Path

# URLs
SMART_TOUR_URL_TEMPLATE = "https://www.komoot.com/smarttour/{tour_id}"
TOUR_URL_TEMPLATE = "https://www.komoot.com/tour/{tour_id}"

# Request behaviour
DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

REQUEST_TIMEOUT = 20
MIN_DELAY_SECONDS = 1.5
MAX_DELAY_SECONDS = 3.5
MAX_RETRIES = 3
BACKOFF_FACTOR = 2.0

# Paths
PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"

RAW_DIR.mkdir(parents=True, exist_ok=True)