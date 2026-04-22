"""Data models for scraped trails."""
from __future__ import annotations
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


@dataclass
class Waypoint:
    name: Optional[str] = None
    lat: Optional[float] = None
    lng: Optional[float] = None
    type: Optional[str] = None
    categories: List[str] = field(default_factory=list)
    highlight_id: Optional[int] = None


@dataclass
class FAQ:
    question: str
    answer: str


@dataclass
class Trail:
    # Identification
    tour_id: str
    url: str
    source: str = "komoot"
    share_url: Optional[str] = None

    # Core metadata
    name: Optional[str] = None
    name_original: Optional[str] = None
    sport: Optional[str] = None
    tour_type: Optional[str] = None

    # Difficulty
    difficulty: Optional[str] = None
    difficulty_technical: Optional[str] = None
    difficulty_fitness: Optional[str] = None
    constitution: Optional[int] = None

    # Numerical
    distance_m: Optional[float] = None
    duration_s: Optional[int] = None
    elevation_up_m: Optional[float] = None
    elevation_down_m: Optional[float] = None
    avg_speed_kmh: Optional[float] = None
    kcal_active: Optional[int] = None
    kcal_resting: Optional[int] = None
    roundtrip: Optional[bool] = None

    # Location
    start_lat: Optional[float] = None
    start_lng: Optional[float] = None
    start_alt_m: Optional[float] = None
    region: Optional[str] = None
    region_id: Optional[int] = None
    country: Optional[str] = None

    # Text
    description: Optional[str] = None
    description_language: Optional[str] = None
    region_intro: Optional[str] = None
    region_faq: Optional[str] = None
    tips: List[str] = field(default_factory=list)
    faqs: List[FAQ] = field(default_factory=list)

    # Extras
    surfaces: Dict[str, float] = field(default_factory=dict)
    way_types: Dict[str, float] = field(default_factory=dict)
    waypoints: List[Waypoint] = field(default_factory=list)
    categories: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)

    # Engagement
    rating_score: Optional[float] = None
    rating_count: Optional[int] = None
    visitors: Optional[int] = None

    # Author
    author_name: Optional[str] = None
    author_id: Optional[str] = None

    # Timestamps
    created_at: Optional[str] = None
    changed_at: Optional[str] = None
    scraped_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)