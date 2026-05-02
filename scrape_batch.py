"""
Run from the project root (ML-APPLICATIONS-PROJECT.../) to scrape trails.

Usage:
    python scrape_batch.py --per-sport 500
"""

import argparse
import logging
import sys
from pathlib import Path

# fix: add project root to path so Python finds the 'scraping' folder
ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from scraping import KomootClient, TourScraper
from scraping.storage import save_trail
from scraping.utils import setup_logging

SPORT_FILES = [
    "data/spain_hike.txt",
    "data/spain_jogging.txt",
    "data/spain_mtb.txt",
    "data/spain_mtb_easy.txt",
    "data/spain_racebike.txt",
    "data/spain_touringbicycle.txt",
]

RAW_DIR = ROOT / "data" / "raw"


def load_ids(filepath: Path) -> list[str]:
    return [
        line.strip()
        for line in filepath.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.startswith("#")
    ]


def already_scraped(tour_id: str) -> bool:
    return (RAW_DIR / f"{tour_id}.json").exists()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--per-sport", type=int, default=500,
                        help="Max new trails to scrape per sport (default: 500)")
    args = parser.parse_args()

    setup_logging()
    log = logging.getLogger(__name__)
    RAW_DIR.mkdir(parents=True, exist_ok=True)

    total_done = 0
    total_failed = 0

    with KomootClient() as client:
        scraper = TourScraper(client=client)

        for filename in SPORT_FILES:
            filepath = ROOT / filename
            if not filepath.exists():
                # also try without 'data/' prefix in case txt files are in root
                filepath = ROOT / Path(filename).name
            if not filepath.exists():
                log.warning("File not found: %s", filename)
                continue

            ids = load_ids(filepath)
            todo = [tid for tid in ids if not already_scraped(tid)][:args.per_sport]

            log.info("=== %s: %d to scrape ===", Path(filename).name, len(todo))
            done, failed = 0, 0

            for i, tid in enumerate(todo, 1):
                log.info("[%s] %d/%d — %s", Path(filename).name, i, len(todo), tid)
                trail = scraper.scrape(tid)
                if trail is None or not trail.description:
                    failed += 1
                    continue
                save_trail(trail)
                done += 1

            log.info("Done: %d saved, %d skipped/failed", done, failed)
            total_done += done
            total_failed += failed

    print(f"\nTotal saved: {total_done} | Skipped/failed: {total_failed}")
    print(f"JSONs in: {RAW_DIR}")


if __name__ == "__main__":
    main()
