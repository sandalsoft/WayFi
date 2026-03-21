"""Location extraction and network matching from calendar events."""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field

from wayfi.calendar.icloud import CalendarEvent

logger = logging.getLogger(__name__)

# Known hotel chains mapped to SSID patterns and portal heuristic patterns
HOTEL_CHAIN_DB: list[dict] = [
    {
        "chain": "hilton",
        "keywords": ["hilton", "doubletree", "hampton inn", "embassy suites",
                      "waldorf", "conrad", "curio", "garden inn"],
        "ssid_patterns": ["hhonors", "hilton", "hampton"],
        "portal_pattern": "hilton",
    },
    {
        "chain": "marriott",
        "keywords": ["marriott", "sheraton", "westin", "w hotel", "courtyard",
                      "fairfield", "residence inn", "springhill", "ritz-carlton",
                      "st. regis", "aloft", "element"],
        "ssid_patterns": ["marriott", "bonvoy", "sheraton", "westin"],
        "portal_pattern": "marriott",
    },
    {
        "chain": "ihg",
        "keywords": ["holiday inn", "intercontinental", "crowne plaza",
                      "staybridge", "candlewood", "kimpton", "even hotels",
                      "ihg", "indigo"],
        "ssid_patterns": ["ihg", "holiday", "intercontinental"],
        "portal_pattern": "ihg",
    },
    {
        "chain": "hyatt",
        "keywords": ["hyatt", "park hyatt", "andaz", "grand hyatt",
                      "hyatt regency", "hyatt place", "hyatt house"],
        "ssid_patterns": ["hyatt"],
        "portal_pattern": "generic",
    },
    {
        "chain": "airbnb",
        "keywords": ["airbnb", "vrbo", "vacation rental"],
        "ssid_patterns": [],
        "portal_pattern": None,
    },
]


@dataclass
class LocationMatch:
    event: CalendarEvent
    chain: str | None = None
    ssid_patterns: list[str] = field(default_factory=list)
    portal_pattern: str | None = None
    city: str = ""
    venue_name: str = ""
    check_in: str = ""
    check_out: str = ""
    nights: int = 1


class LocationMatcher:
    """Extract venue and location info from calendar events,
    match against known hotel chain database for network prediction."""

    def __init__(self, custom_chains: list[dict] | None = None) -> None:
        self.chains = HOTEL_CHAIN_DB + (custom_chains or [])

    def match_event(self, event: CalendarEvent) -> LocationMatch | None:
        """Match a calendar event against known hotel chains.

        Returns LocationMatch if the event looks like a hotel stay, None otherwise.
        """
        # Only consider multi-day events or events with hotel-like locations
        location = event.location.lower()
        summary = event.summary.lower()
        combined = f"{summary} {location}"

        # Try to match a hotel chain
        chain_match = self._match_chain(combined)

        # Extract venue details
        venue = self._extract_venue(event.location)
        city = self._extract_city(event.location)

        # Multi-day events are strong hotel signals
        is_hotel = chain_match is not None or (
            event.is_multiday and any(
                kw in combined for kw in ["hotel", "inn", "resort", "suites", "lodge"]
            )
        )

        if not is_hotel:
            return None

        nights = event.duration_days

        match = LocationMatch(
            event=event,
            chain=chain_match["chain"] if chain_match else None,
            ssid_patterns=chain_match["ssid_patterns"] if chain_match else [],
            portal_pattern=chain_match["portal_pattern"] if chain_match else None,
            city=city,
            venue_name=venue,
            check_in=event.start.strftime("%Y-%m-%d"),
            check_out=event.end.strftime("%Y-%m-%d"),
            nights=nights,
        )
        logger.info(
            "Calendar match: %s at %s (%s, %d nights)",
            match.chain or "unknown hotel",
            match.venue_name,
            match.city,
            match.nights,
        )
        return match

    def _match_chain(self, text: str) -> dict | None:
        """Match text against known hotel chain keywords."""
        for chain in self.chains:
            for keyword in chain["keywords"]:
                if keyword in text:
                    return chain
        return None

    def _extract_venue(self, location: str) -> str:
        """Extract venue name from location string."""
        if not location:
            return ""
        # Take the first part before comma or dash
        parts = re.split(r"[,\-–]", location)
        return parts[0].strip()

    def _extract_city(self, location: str) -> str:
        """Extract city from location string (usually after first comma)."""
        if not location:
            return ""
        parts = location.split(",")
        if len(parts) >= 2:
            return parts[1].strip()
        return ""
