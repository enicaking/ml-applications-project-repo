"""Command-line entry point.

Usage:
    python -m scraping.cli e1287103067      # one ID
    python -m scraping.cli list.txt         # file with one ID per line
"""
from __future__ import annotations
import argparse
import logging
from pathlib import Path
from typing import Iterator

from . import config
from .client import KomootClient
from .scrapers import TourScraper
from .storage import save_trail
from .utils import setup_logging

logger = logging.getLogger(__name__)


def iter_ids(target: str) -> Iterator[str]:
    """Yield tour IDs from either a single-ID argument or a text file."""
    p = Path(target)
    if p.is_file():
        for line in p.read_text(encoding="utf-8").splitlines():
            tid = line.strip()
            if tid and not tid.startswith("#"):
                yield tid
    else:
        yield target


def main():
    parser = argparse.ArgumentParser(description="Komoot scraper")
    parser.add_argument("target", help="Tour ID (e.g. e1287103067) or path to a .txt list")
    args = parser.parse_args()

    setup_logging()
    ids = list(iter_ids(args.target))
    if not ids:
        print("No IDs to scrape.")
        return

    done, failed = 0, 0
    with KomootClient() as client:
        scraper = TourScraper(client=client)
        for i, tid in enumerate(ids, 1):
            logger.info("[%d/%d] %s", i, len(ids), tid)
            trail = scraper.scrape(tid)
            if trail is None:
                failed += 1
                continue
            save_trail(trail)
            done += 1

    print(f"Done. Saved {done} trails to {config.RAW_DIR}. Failed: {failed}.")


if __name__ == "__main__":
    main()
