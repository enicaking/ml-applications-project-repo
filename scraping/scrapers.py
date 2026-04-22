"""Scraping orchestration."""
from __future__ import annotations
import logging
from typing import Optional

import requests

from . import config
from .client import KomootClient
from .models import Trail
from .parsers import parse_tour_page

logger = logging.getLogger(__name__)


def tour_url(tour_id: str) -> str:
    """Build the correct URL for a tour ID.

    Editorial ("smart") tours carry an 'e' prefix (e.g. e1287103067) and
    live under /smarttour/. Community tours use plain numeric IDs under
    /tour/.
    """
    tour_id = str(tour_id)
    if tour_id.startswith("e"):
        return config.SMART_TOUR_URL_TEMPLATE.format(tour_id=tour_id)
    return config.TOUR_URL_TEMPLATE.format(tour_id=tour_id)


class TourScraper:
    """Scrape a single tour page by ID. One HTTP request per tour."""

    def __init__(self, client: Optional[KomootClient] = None):
        self.client = client or KomootClient()
        self._owns_client = client is None

    def scrape(self, tour_id: str) -> Optional[Trail]:
        url = tour_url(tour_id)
        try:
            response = self.client.get(url)
        except requests.HTTPError as e:
            status = e.response.status_code if e.response is not None else "?"
            logger.warning("HTTP %s for %s", status, tour_id)
            return None
        except Exception:
            logger.exception("Failed to fetch tour %s (%s)", tour_id, url)
            return None

        try:
            return parse_tour_page(response.text, tour_id=tour_id, url=url)
        except Exception:
            logger.exception("Failed to parse tour %s", tour_id)
            return None

    def close(self):
        if self._owns_client:
            self.client.close()

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()