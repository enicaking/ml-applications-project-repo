"""Parse Komoot tour pages.

Everything we need lives in the tour HTML — no extra API calls:
  - Structured metadata (distance, waypoints, surfaces, etc.) is embedded
    as JSON in a `kmtBoot.setProps("...")` script tag.
  - The FAQ section is embedded as JSON-LD with @type "FAQPage".
  - The short description is in kmtBoot's `tour_description.text`.

If a future Komoot redesign breaks a field, inspect the HTML, find the
path, and adjust the corresponding `_safe_get(...)` call.
"""
from __future__ import annotations
import json
import logging
import re
from typing import Any, Dict, List, Optional

from bs4 import BeautifulSoup

from .models import FAQ, Trail, Waypoint

logger = logging.getLogger(__name__)

_KMT_BOOT_RE = re.compile(r'kmtBoot\.setProps\("(.+?)"\)\s*;', re.DOTALL)

_SURFACE_PREFIX = "sf#"
_WAYTYPE_PREFIX = "wt#"
_DIFF_TECH_PREFIX = "dh#"
_DIFF_FIT_PREFIX = "d#"


def parse_tour_page(html: str, tour_id: str, url: str) -> Optional[Trail]:
    """Build a Trail from a tour page's HTML.

    Returns None when the page doesn't contain a kmtBoot tour payload —
    this is how we detect "ID exists but page has no tour" even when the
    HTTP response is 200.
    """
    tour = _extract_kmt_boot_tour(html)
    if not tour:
        return None

    trail = Trail(tour_id=tour_id, url=url)
    _populate_from_payload(trail, tour)

    soup = BeautifulSoup(html, "html.parser")

    # FAQs from JSON-LD (FAQPage schema)
    trail.faqs = _extract_faqs_from_jsonld(soup)

    # Fallback for name if the payload was lean
    if not trail.name:
        h1 = soup.find("h1")
        trail.name = h1.get_text(strip=True) if h1 else None

    return trail


def _extract_kmt_boot_tour(html: str) -> Optional[Dict[str, Any]]:
    match = _KMT_BOOT_RE.search(html)
    if not match:
        return None
    raw = match.group(1)
    try:
        unescaped = json.loads(f'"{raw}"')
        payload = json.loads(unescaped)
    except json.JSONDecodeError as e:
        logger.warning("Failed to decode kmtBoot payload: %s", e)
        return None
    return (
        _safe_get(payload, "page", "_embedded", "tour")
        or _safe_get(payload, "tour")
        or None
    )


def _extract_faqs_from_jsonld(soup: BeautifulSoup) -> List[FAQ]:
    """Pull the FAQ Q&A pairs out of <script type="application/ld+json">.

    Komoot embeds a schema.org FAQPage with mainEntity = list of Question
    objects; each Question has an acceptedAnswer with a `text` field.
    """
    faqs: List[FAQ] = []
    for tag in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(tag.string or "")
        except (json.JSONDecodeError, TypeError):
            continue

        # A JSON-LD block may be a list or a single object
        blocks = data if isinstance(data, list) else [data]
        for block in blocks:
            if not isinstance(block, dict):
                continue
            if block.get("@type") != "FAQPage":
                continue
            for q in block.get("mainEntity") or []:
                if not isinstance(q, dict):
                    continue
                question = (q.get("name") or "").strip()
                answer = _safe_get(q, "acceptedAnswer", "text") or ""
                answer = answer.strip()
                if question or answer:
                    faqs.append(FAQ(question=question, answer=answer))
    return faqs


def _safe_get(d: Any, *keys, default=None):
    cur = d
    for k in keys:
        if isinstance(cur, dict) and k in cur:
            cur = cur[k]
        elif isinstance(cur, list) and isinstance(k, int) and 0 <= k < len(cur):
            cur = cur[k]
        else:
            return default
    return cur


def _strip_prefix(value: Any, prefix: str) -> Any:
    if isinstance(value, str) and value.startswith(prefix):
        return value[len(prefix):]
    return value


def _populate_from_payload(trail: Trail, tour: Dict[str, Any]) -> None:
    trail.name = tour.get("name")
    trail.sport = tour.get("sport")
    trail.tour_type = tour.get("type") or tour.get("smart_tour_type")
    trail.share_url = tour.get("share_url")

    ntm = tour.get("name_translation_metadata") or {}
    original_name = ntm.get("original_text")
    if original_name and original_name != trail.name:
        trail.name_original = original_name

    diff = tour.get("difficulty") or {}
    grade = diff.get("grade")
    trail.difficulty = grade.lower() if isinstance(grade, str) else grade
    trail.difficulty_technical = _strip_prefix(diff.get("explanation_technical"), _DIFF_TECH_PREFIX)
    trail.difficulty_fitness = _strip_prefix(diff.get("explanation_fitness"), _DIFF_FIT_PREFIX)

    trail.distance_m = tour.get("distance")
    trail.duration_s = tour.get("duration")
    trail.elevation_up_m = tour.get("elevation_up")
    trail.elevation_down_m = tour.get("elevation_down")
    trail.kcal_active = tour.get("kcal_active")
    trail.kcal_resting = tour.get("kcal_resting")
    trail.constitution = tour.get("constitution")
    trail.roundtrip = tour.get("roundtrip")

    start = tour.get("start_point") or {}
    trail.start_lat = start.get("lat")
    trail.start_lng = start.get("lng")
    trail.start_alt_m = start.get("alt")

    summary_block = tour.get("summary") or {}
    trail.surfaces = _parse_distribution(summary_block.get("surfaces"), _SURFACE_PREFIX)
    trail.way_types = _parse_distribution(summary_block.get("way_types"), _WAYTYPE_PREFIX)

    trail.rating_score = tour.get("rating_score")
    trail.rating_count = tour.get("rating_count")
    trail.visitors = tour.get("visitors")

    trail.created_at = tour.get("date")
    trail.changed_at = tour.get("changed_at")

    creator = _safe_get(tour, "_embedded", "creator") or {}
    trail.author_name = creator.get("display_name") or creator.get("username")
    trail.author_id = creator.get("username")

    _populate_description(trail, tour)
    _populate_waypoints(trail, tour)
    _populate_region(trail, tour)

    custom = tour.get("custom_tags") or []
    trail.tags = [t if isinstance(t, str) else (t.get("name") or "") for t in custom if t]
    trail.tags = [t for t in trail.tags if t]


def _parse_distribution(items: Optional[list], prefix: str) -> Dict[str, float]:
    out: Dict[str, float] = {}
    for item in items or []:
        if not isinstance(item, dict):
            continue
        raw_type = item.get("type") or item.get("name")
        amount = item.get("amount")
        if amount is None:
            amount = item.get("percentage")
        if raw_type is None or amount is None:
            continue
        try:
            out[str(_strip_prefix(raw_type, prefix))] = float(amount)
        except (TypeError, ValueError):
            continue
    return out


def _populate_description(trail: Trail, tour: Dict[str, Any]) -> None:
    """Pull the short description paragraph shown on the tour page."""
    td = _safe_get(tour, "_embedded", "tour_description") or {}

    original_text = td.get("text")
    translated_text = td.get("translated_text")
    original_lang = td.get("text_language")
    translated_lang = td.get("translated_text_language")

    # Prefer English if a translation is available; otherwise keep original.
    if translated_text and translated_lang == "en":
        trail.description = translated_text
        trail.description_language = translated_lang
    else:
        trail.description = td.get("short_description") or original_text
        trail.description_language = original_lang


def _populate_waypoints(trail: Trail, tour: Dict[str, Any]) -> None:
    items = (
        _safe_get(tour, "_embedded", "way_points", "_embedded", "items")
        or _safe_get(tour, "_embedded", "timeline", "_embedded", "items")
        or []
    )

    categories: List[str] = []
    tips: List[str] = []

    for wp in items:
        ref = _safe_get(wp, "_embedded", "reference") or {}
        ref_type = ref.get("type") or ""
        if not ref_type.startswith("highlight"):
            continue

        loc = ref.get("location") or ref.get("mid_point") or {}
        ref_categories = ref.get("categories") or []
        trail.waypoints.append(
            Waypoint(
                name=ref.get("name"),
                lat=loc.get("lat"),
                lng=loc.get("lng"),
                type=ref.get("category") or ref_type,
                categories=list(ref_categories),
                highlight_id=ref.get("id"),
            )
        )
        categories.extend(ref_categories)

        tip_items = _safe_get(ref, "_embedded", "tips", "_embedded", "items") or []
        for tip in tip_items:
            if tip.get("translated_text") and tip.get("translated_text_language") == "en":
                text = tip["translated_text"]
            else:
                text = tip.get("text") or tip.get("translated_text")
            if text:
                tips.append(text)

    if categories:
        trail.categories = sorted(set(categories))
    if tips:
        trail.tips = tips


def _populate_region(trail: Trail, tour: Dict[str, Any]) -> None:
    elements = _safe_get(
        tour, "_embedded", "root_activity", "_embedded", "tour",
        "_embedded", "elements", "_embedded", "items",
    ) or []

    guides = [
        e for e in elements
        if isinstance(e, dict) and e.get("type") == "GUIDE" and e.get("region_name")
    ]
    if not guides:
        return

    def _extent_area(elem: Dict[str, Any]) -> float:
        ext = elem.get("extent") or []
        if len(ext) < 2:
            return float("inf")
        try:
            dlat = abs(ext[0]["lat"] - ext[1]["lat"])
            dlng = abs(ext[0]["lng"] - ext[1]["lng"])
            return dlat * dlng
        except (KeyError, TypeError):
            return float("inf")

    same_sport = [g for g in guides if g.get("sport") == trail.sport]
    candidates = same_sport or guides
    guide = min(candidates, key=_extent_area)

    trail.region = guide.get("region_name")
    trail.region_id = guide.get("region_id")
    if guide.get("intro_plain"):
        trail.region_intro = guide["intro_plain"]

    faq_val = guide.get("faq")
    if isinstance(faq_val, list) and faq_val:
        trail.region_faq = "\n\n".join(
            f"Q: {qa.get('question','')}\nA: {qa.get('answer','')}"
            for qa in faq_val if isinstance(qa, dict)
        )
    elif isinstance(faq_val, str) and faq_val.strip():
        trail.region_faq = faq_val