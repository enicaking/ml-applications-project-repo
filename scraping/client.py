"""HTTP client with rate limiting and retries."""
from __future__ import annotations
import logging
import random
import time
from typing import Optional

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from . import config

logger = logging.getLogger(__name__)


class KomootClient:
    """Thin wrapper around requests.Session with polite defaults."""

    def __init__(
        self,
        headers: Optional[dict] = None,
        min_delay: float = config.MIN_DELAY_SECONDS,
        max_delay: float = config.MAX_DELAY_SECONDS,
        timeout: float = config.REQUEST_TIMEOUT,
    ):
        self.session = requests.Session()
        self.session.headers.update(headers or config.DEFAULT_HEADERS)
        self.min_delay = min_delay
        self.max_delay = max_delay
        self.timeout = timeout

        retry = Retry(
            total=config.MAX_RETRIES,
            backoff_factor=config.BACKOFF_FACTOR,
            status_forcelist=(429, 500, 502, 503, 504),
            allowed_methods=("GET",),
            respect_retry_after_header=True,
        )
        adapter = HTTPAdapter(max_retries=retry)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

        self._last_request_at: float = 0.0

    def _throttle(self) -> None:
        elapsed = time.time() - self._last_request_at
        wait = random.uniform(self.min_delay, self.max_delay) - elapsed
        if wait > 0:
            time.sleep(wait)

    def get(self, url: str, **kwargs) -> requests.Response:
        self._throttle()
        logger.debug("GET %s", url)
        response = self.session.get(url, timeout=self.timeout, **kwargs)
        self._last_request_at = time.time()
        response.raise_for_status()
        return response

    def close(self) -> None:
        self.session.close()

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()
