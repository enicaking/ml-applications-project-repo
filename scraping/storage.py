"""Persist scraped trails as processed JSON in data/raw/."""
from __future__ import annotations
import json
import logging
from pathlib import Path

from . import config
from .models import Trail

logger = logging.getLogger(__name__)


def save_trail(trail: Trail) -> Path:
    """Write trail.to_dict() to data/raw/{tour_id}.json."""
    config.RAW_DIR.mkdir(parents=True, exist_ok=True)
    path = config.RAW_DIR / f"{trail.tour_id}.json"
    path.write_text(
        json.dumps(trail.to_dict(), ensure_ascii=False, indent=2, default=str),
        encoding="utf-8",
    )
    return path
