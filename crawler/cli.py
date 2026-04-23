"""Command-line entry point for the crawler.

Examples:
    # Crawl around a region by name (geocoded via Photon)
    python -m crawler.cli --region "Boadilla del Monte" --sport hike

    # Pass coordinates directly (skips geocoding)
    python -m crawler.cli --lat 40.405 --lng -3.8783 --sport hike

    # Narrow radius, cap output, custom name
    python -m crawler.cli --region "Madrid" --sport mtb \\
        --max-distance 15000 --limit 200 --output madrid_mtb

    # Denser spatial sampling (more API calls, more coverage)
    python -m crawler.cli --region "Sierra de Guadarrama" \\
        --max-distance 50000 --grid-spacing 5000

    # Just geocode, don't crawl
    python -m crawler.cli --region "Sierra de Guadarrama" --geocode-only
    
    # Example: search the entirety of Spain for hiking tours
    python -m crawler.cli \\
        --lat 40.0 --lng -4.0 \\
        --sport hike \\
        --max-distance 600000 \\
        --grid-spacing 25000 \\
        --patience 50 \\
        --output spain_hike
"""
from __future__ import annotations
import argparse
import logging
import sys

from scraping import KomootClient

from . import config
from .discover import discover_tour_ids
from .geocode import geocode
from .storage import save_ids
from .utils import setup_logging

logger = logging.getLogger(__name__)


def _resolve_location(args, client: KomootClient):
    """Return (lat, lng, label_for_output) or exit if we can't."""
    if args.lat is not None and args.lng is not None:
        label = args.output or f"coords_{args.lat:.3f}_{args.lng:.3f}_{args.sport}"
        return args.lat, args.lng, label

    if not args.region:
        print("error: either --region or both --lat/--lng are required", file=sys.stderr)
        sys.exit(2)

    hits = geocode(args.region, client=client, limit=5)
    if not hits:
        print(f"Geocoder returned no hits for {args.region!r}.", file=sys.stderr)
        sys.exit(1)

    chosen = hits[0]
    logger.info(
        "Geocoded %r -> %r (%s, %s)  lat=%.5f lng=%.5f",
        args.region, chosen.name, chosen.osm_type, chosen.country,
        chosen.lat, chosen.lng,
    )
    if args.geocode_only:
        for i, h in enumerate(hits):
            print(f"[{i}] {h.name!r} ({h.osm_type}, {h.country})  "
                  f"lat={h.lat:.5f} lng={h.lng:.5f}")
        sys.exit(0)

    label = args.output or f"{args.region}_{args.sport}"
    return chosen.lat, chosen.lng, label


def main():
    parser = argparse.ArgumentParser(description="Komoot tour-ID crawler")

    parser.add_argument("--region", help="Place name; geocoded via Photon")
    parser.add_argument("--lat", type=float, help="Latitude (skips geocoding)")
    parser.add_argument("--lng", type=float, help="Longitude (skips geocoding)")
    parser.add_argument(
        "--geocode-only", action="store_true",
        help="Print geocode candidates and exit (no crawling)",
    )

    parser.add_argument(
        "--sport", default="hike",
        help="Sport filter (hike, mtb, racebike, jogging, ...). Default: hike",
    )
    parser.add_argument(
        "--max-distance", type=int, default=config.DEFAULT_MAX_DISTANCE_M,
        help=f"Total search radius in metres. Default: {config.DEFAULT_MAX_DISTANCE_M}",
    )
    parser.add_argument(
        "--grid-spacing", type=int, default=config.DEFAULT_GRID_SPACING_M,
        help=(
            "Distance between probe points in metres. Smaller = more API "
            f"calls, denser coverage. Default: {config.DEFAULT_GRID_SPACING_M}"
        ),
    )
    parser.add_argument(
        "--patience", type=int, default=5,
        help="Stop early after this many consecutive empty probes. Default: 5",
    )
    parser.add_argument(
        "--limit", type=int, default=None,
        help="Stop after this many unique IDs. Default: no cap",
    )
    parser.add_argument(
        "--output", "-o",
        help="Output filename stem. Default: {region}_{sport}",
    )

    args = parser.parse_args()
    setup_logging()

    with KomootClient() as client:
        lat, lng, label = _resolve_location(args, client)

        ids = discover_tour_ids(
            lat=lat, lng=lng,
            sport=args.sport,
            max_distance_m=args.max_distance,
            grid_spacing_m=args.grid_spacing,
            client=client,
            limit=args.limit,
            patience=args.patience,
        )

    path = save_ids(ids, name=label)
    print(f"Saved {len(ids)} tour IDs -> {path}")


if __name__ == "__main__":
    main()