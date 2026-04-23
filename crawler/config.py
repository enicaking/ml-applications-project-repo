"""Configuration constants for the Komoot crawler."""
from pathlib import Path

# URLs
DISCOVER_TOURS_URL = "https://www.komoot.com/api/v007/discover_tours/"

PHOTON_API_URL = "https://photon.komoot.io/api/"

# Defaults
DEFAULT_MAX_DISTANCE_M = 30_000      # 30 km total search radius
DEFAULT_GRID_SPACING_M = 10_000      # 10 km between probe points

# Paths
PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"

DATA_DIR.mkdir(parents=True, exist_ok=True)