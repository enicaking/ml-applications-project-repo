"""Geocoding via Komoot's public Photon service.

Photon is an open-source geocoder Komoot runs at photon.komoot.io. Free for
reasonable use; rate-limited by the server. Docs: github.com/komoot/photon
"""
from __future__ import annotations
import logging
from dataclasses import dataclass
from typing import List, Optional

from scraping import KomootClient

from . import config

logger = logging.getLogger(__name__)


@dataclass
class GeoHit:
    name: str
    lat: float
    lng: float
    country: Optional[str] = None
    osm_type: Optional[str] = None   # 'city', 'village', 'suburb', ...


def geocode(
    query: str,
    client: Optional[KomootClient] = None,
    limit: int = 5,
    lang: str = "en",
) -> List[GeoHit]:
    """Resolve a place name to candidate coordinates.

    Returns an empty list if the geocoder has no idea. Callers should fail
    loudly if the result is empty — we do NOT guess.
    """
    owns_client = client is None
    client = client or KomootClient()
    try:
        response = client.get(
            config.PHOTON_API_URL,
            params={"q": query, "limit": limit, "lang": lang},
        )
    except Exception:
        logger.exception("Photon request failed for %r", query)
        if owns_client:
            client.close()
        return []

    try:
        data = response.json()
    except ValueError:
        logger.warning("Photon returned non-JSON for %r", query)
        if owns_client:
            client.close()
        return []
    finally:
        if owns_client:
            client.close()

    hits: List[GeoHit] = []
    for feat in data.get("features") or []:
        props = feat.get("properties") or {}
        geom = feat.get("geometry") or {}
        coords = geom.get("coordinates") or [None, None]
        if coords[0] is None or coords[1] is None:
            continue
        hits.append(GeoHit(
            name=(
                props.get("name")
                or props.get("city")
                or props.get("state")
                or query
            ),
            lat=float(coords[1]),
            lng=float(coords[0]),
            country=props.get("country"),
            osm_type=props.get("osm_value"),
        ))
    return hits
