"""Tests for calendar location matching."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from wayfi.calendar.icloud import CalendarEvent
from wayfi.calendar.location import LocationMatcher


def _make_event(
    summary: str,
    location: str,
    days: int = 1,
    start_offset_days: int = 1,
) -> CalendarEvent:
    now = datetime.now(timezone.utc)
    start = now + timedelta(days=start_offset_days)
    end = start + timedelta(days=days)
    return CalendarEvent(
        summary=summary,
        location=location,
        start=start,
        end=end,
        provider="test",
    )


class TestLocationMatcher:
    @property
    def matcher(self):
        return LocationMatcher()

    def test_match_hilton(self):
        event = _make_event("Business trip", "Hilton Garden Inn, Denver, CO", days=3)
        match = self.matcher.match_event(event)
        assert match is not None
        assert match.chain == "hilton"
        assert match.nights == 3

    def test_match_marriott(self):
        event = _make_event("Conference", "Marriott Marquis, San Francisco, CA", days=2)
        match = self.matcher.match_event(event)
        assert match is not None
        assert match.chain == "marriott"

    def test_match_ihg_holiday_inn(self):
        event = _make_event("Stay", "Holiday Inn Express, Chicago, IL", days=1)
        match = self.matcher.match_event(event)
        assert match is not None
        assert match.chain == "ihg"

    def test_no_match_restaurant(self):
        event = _make_event("Dinner", "The Italian Place, NYC")
        match = self.matcher.match_event(event)
        assert match is None

    def test_extract_city(self):
        event = _make_event("Trip", "Hilton, Denver, CO", days=2)
        match = self.matcher.match_event(event)
        assert match is not None
        assert match.city == "Denver"

    def test_extract_venue(self):
        event = _make_event("Stay", "Hilton Garden Inn - Downtown, Denver, CO", days=2)
        match = self.matcher.match_event(event)
        assert match is not None
        assert "Hilton" in match.venue_name

    def test_ssid_patterns(self):
        event = _make_event("Trip", "Hilton, NYC", days=2)
        match = self.matcher.match_event(event)
        assert match is not None
        assert len(match.ssid_patterns) > 0
        assert any("hilton" in p.lower() for p in match.ssid_patterns)

    def test_multiday_hotel_keyword(self):
        event = _make_event("Vacation", "Grand Hotel, Paris", days=5)
        match = self.matcher.match_event(event)
        assert match is not None
        assert match.nights == 5

    def test_single_day_no_match(self):
        event = _make_event("Meeting", "Some Office, NYC", days=0)
        match = self.matcher.match_event(event)
        assert match is None


class TestCalendarEvent:
    def test_duration_days(self):
        event = _make_event("Stay", "Hotel", days=3)
        assert event.duration_days == 3

    def test_is_multiday(self):
        single = _make_event("Meeting", "Office", days=0)
        multi = _make_event("Trip", "Hotel", days=3)
        assert single.is_multiday is False
        assert multi.is_multiday is True
