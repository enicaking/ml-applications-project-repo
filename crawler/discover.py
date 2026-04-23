"""Discover tour IDs near a location using Komoot's `/discover_tours/` endpoint.

Problem: the endpoint returns at most ~12 items for any given (lat, lng, sport)
regardless of the `page` or `limit` params — it's a top-K nearest-relevant
lookup, not a paginated feed. Its `totalPages` field is misleading (it reports
the theoretical count in the radius, not what it'll hand back).

Solution: sample a spatial GRID of probe points across the target area. Each
probe yields up to 12 tours local to it; dedupe across points. With a 10 km
grid spacing over a 30 km radius that's ~29 probes and up to ~348 potential
tour IDs, heavily overlapping near the center and thinning out at the edges.

Early stop: if `patience` consecutive probes return zero new IDs we assume the
area is drained and bail out.
"""
from __future__ import annotations
import logging
import math
from typing import Iterator, List, Optional, Tuple

from scraping import KomootClient

from . import config

logger = logging.getLogger(__name__)


def discover_tour_ids(
    lat: float,
    lng: float,
    sport: str = "hike",
    *,
    max_distance_m: int = config.DEFAULT_MAX_DISTANCE_M,
    client: Optional[KomootClient] = None,
    limit: Optional[int] = None,
    grid_spacing_m: int = config.DEFAULT_GRID_SPACING_M,
    patience: int = 5,
) -> List[str]:
    """Walk a grid of probe points, collect tour IDs, dedupe.

    Parameters
    ----------
    lat, lng
        Center of the search area.
    sport
        hike / mtb / racebike / jogging / touringbicycle / ...
    max_distance_m
        Total search radius around (lat, lng) in metres. Probe points are
        laid out inside a circle of this radius; each probe queries the API
        with a local radius = grid_spacing_m so tiles partition the area.
    grid_spacing_m
        Distance between adjacent probe points. Smaller = more API calls but
        denser coverage. Default 10 km gives ~29 probes for a 30 km radius.
    limit
        Stop after collecting this many unique IDs. None = no cap.
    patience
        Stop early if this many consecutive probes return zero new IDs.
    """
    owns_client = client is None
    client = client or KomootClient()

    ids: List[str] = []
    seen: set[str] = set()
    stale_streak = 0

    try:
        probes = list(_grid_points(lat, lng, max_distance_m, grid_spacing_m))
        logger.info(
            "Crawling %d grid probe points (spacing=%dm, radius=%dm)",
            len(probes), grid_spacing_m, max_distance_m,
        )

        for i, (plat, plng) in enumerate(probes):
            new_this_probe = 0
            for tour_id in _query_point(client, plat, plng, sport, grid_spacing_m):
                if tour_id in seen:
                    continue
                seen.add(tour_id)
                ids.append(tour_id)
                new_this_probe += 1
                if limit is not None and len(ids) >= limit:
                    logger.info("Reached limit=%d, stopping", limit)
                    return ids

            logger.info(
                "Probe %d/%d at (%.4f, %.4f): +%d new IDs (total: %d)",
                i + 1, len(probes), plat, plng, new_this_probe, len(ids),
            )

            if new_this_probe == 0:
                stale_streak += 1
                if stale_streak >= patience:
                    logger.info(
                        "Stopping early: %d consecutive probes yielded nothing new",
                        stale_streak,
                    )
                    return ids
            else:
                stale_streak = 0
    finally:
        if owns_client:
            client.close()

    return ids


def _query_point(
    client: KomootClient,
    lat: float,
    lng: float,
    sport: str,
    radius_m: int,
) -> Iterator[str]:
    """Hit /discover_tours/ for one (lat, lng). Yields tour IDs."""
    params = {
        "lat": lat,
        "lng": lng,
        "sport": sport,
        "max_distance": radius_m,
        "searchType": "within_radius",
        "format": "simple",
    }
    try:
        response = client.get(config.DISCOVER_TOURS_URL, params=params)
        payload = response.json()
    except Exception:
        logger.exception("Discover request failed at (%.4f, %.4f)", lat, lng)
        return

    items = (payload.get("_embedded") or {}).get("items") or []
    for item in items:
        if isinstance(item, dict) and item.get("id") is not None:
            yield str(item["id"])


# Latitude degrees to metres: always ~111_320 m per degree.
# Longitude scales with cos(latitude).
_METRES_PER_DEGREE_LAT = 111_320.0


def _grid_points(
    center_lat: float,
    center_lng: float,
    radius_m: int,
    spacing_m: int,
) -> Iterator[Tuple[float, float]]:
    """Yield (lat, lng) points on a square grid, filtered to a circle,
    ordered by distance from the center (so early-stop kicks in sensibly)."""
    metres_per_degree_lng = _METRES_PER_DEGREE_LAT * math.cos(math.radians(center_lat))
    metres_per_degree_lng = max(metres_per_degree_lng, 1.0)  # pole guard

    steps = int(math.ceil(radius_m / spacing_m))

    points: List[Tuple[float, float, float]] = []
    for i in range(-steps, steps + 1):
        for j in range(-steps, steps + 1):
            dx_m = j * spacing_m
            dy_m = i * spacing_m
            dist_m = math.hypot(dx_m, dy_m)
            if dist_m > radius_m:
                continue
            dlat = dy_m / _METRES_PER_DEGREE_LAT
            dlng = dx_m / metres_per_degree_lng
            points.append((dist_m, center_lat + dlat, center_lng + dlng))

    points.sort(key=lambda t: t[0])
    for _, plat, plng in points:
        yield plat, plng