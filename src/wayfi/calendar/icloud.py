"""iCloud CalDAV calendar provider."""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from functools import partial

import caldav

logger = logging.getLogger(__name__)

ICLOUD_CALDAV_URL = "https://caldav.icloud.com"


@dataclass
class CalendarEvent:
    summary: str
    location: str
    start: datetime
    end: datetime
    uid: str = ""
    provider: str = "icloud"

    @property
    def duration_days(self) -> int:
        delta = self.end - self.start
        return max(1, delta.days)

    @property
    def is_multiday(self) -> bool:
        return self.duration_days > 1


class ICloudCalendar:
    """Fetch events from iCloud CalDAV using app-specific password."""

    def __init__(self, username: str, app_password: str) -> None:
        self.username = username
        self.app_password = app_password
        self._client: caldav.DAVClient | None = None

    def _connect(self) -> caldav.DAVClient:
        if self._client is None:
            self._client = caldav.DAVClient(
                url=ICLOUD_CALDAV_URL,
                username=self.username,
                password=self.app_password,
            )
        return self._client

    def _fetch_events_sync(self, lookahead_days: int) -> list[CalendarEvent]:
        """Synchronous CalDAV fetch — run in executor."""
        client = self._connect()
        principal = client.principal()
        calendars = principal.calendars()

        now = datetime.now(timezone.utc)
        end = now + timedelta(days=lookahead_days)
        events: list[CalendarEvent] = []

        for cal in calendars:
            try:
                results = cal.date_search(start=now, end=end, expand=True)
                for event_obj in results:
                    parsed = self._parse_vevent(event_obj)
                    if parsed:
                        events.append(parsed)
            except Exception as e:
                logger.warning("Error fetching calendar %s: %s", cal.name, e)

        logger.info("iCloud: fetched %d events from %d calendars", len(events), len(calendars))
        return events

    def _parse_vevent(self, event_obj: caldav.Event) -> CalendarEvent | None:
        """Parse a caldav Event into our CalendarEvent dataclass."""
        try:
            vevent = event_obj.vobject_instance.vevent

            summary = str(getattr(vevent, "summary", None) or "")
            location = str(getattr(vevent, "location", None) or "")

            dtstart = vevent.dtstart.value
            dtend = getattr(vevent, "dtend", None)

            # Normalize to datetime with timezone
            if hasattr(dtstart, "hour"):
                start = dtstart if dtstart.tzinfo else dtstart.replace(tzinfo=timezone.utc)
            else:
                # Date-only events (all-day)
                start = datetime.combine(dtstart, datetime.min.time(), tzinfo=timezone.utc)

            if dtend:
                dtend_val = dtend.value
                if hasattr(dtend_val, "hour"):
                    end = dtend_val if dtend_val.tzinfo else dtend_val.replace(tzinfo=timezone.utc)
                else:
                    end = datetime.combine(dtend_val, datetime.min.time(), tzinfo=timezone.utc)
            else:
                end = start + timedelta(hours=1)

            uid = str(getattr(vevent, "uid", None) or "")

            return CalendarEvent(
                summary=summary,
                location=location,
                start=start,
                end=end,
                uid=uid,
                provider="icloud",
            )
        except Exception as e:
            logger.warning("Failed to parse iCloud event: %s", e)
            return None

    async def fetch_events(self, lookahead_days: int = 7) -> list[CalendarEvent]:
        """Async wrapper — runs CalDAV in executor to avoid blocking."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, partial(self._fetch_events_sync, lookahead_days)
        )
