"""Persist a discovered ID list to data/."""
from __future__ import annotations
import logging
from pathlib import Path
from typing import Iterable

from . import config

logger = logging.getLogger(__name__)


def save_ids(ids: Iterable[str], name: str = "list") -> Path:
    """Write IDs to data/{name}.txt, one per line.

    `name` is sanitized to a safe filename; pass something like
    "list_madrid_hike" for clarity when crawling multiple regions.
    """
    safe_name = _slugify(name) or "list"
    path = config.DATA_DIR / f"{safe_name}.txt"
    ids = list(ids)
    path.write_text("\n".join(ids) + ("\n" if ids else ""), encoding="utf-8")
    return path


def _slugify(name: str) -> str:
    out = []
    for ch in name.strip().lower():
        if ch.isalnum():
            out.append(ch)
        elif ch in " -_":
            out.append("_")
    # collapse consecutive underscores
    slug = "".join(out)
    while "__" in slug:
        slug = slug.replace("__", "_")
    return slug.strip("_")
