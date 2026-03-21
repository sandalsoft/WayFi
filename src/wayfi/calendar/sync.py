"""Calendar sync daemon — aggregates events from all providers."""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field

from wayfi.calendar.icloud import CalendarEvent, ICloudCalendar
from wayfi.calendar.google import GoogleCalendar
from wayfi.calendar.outlook import OutlookCalendar
from wayfi.calendar.location import LocationMatch, LocationMatcher

logger = logging.getLogger(__name__)


@dataclass
class SyncState:
    events: list[CalendarEvent] = field(default_factory=list)
    matches: list[LocationMatch] = field(default_factory=list)
    last_sync: float = 0.0


class CalendarSync:
    """Aggregates calendar events from all configured providers,
    deduplicates, and runs location matching for network prediction."""

    def __init__(
        self,
        providers: list[ICloudCalendar | GoogleCalendar | OutlookCalendar] | None = None,
        sync_interval: int = 1800,
        lookahead_days: int = 7,
    ) -> None:
        self.providers = providers or []
        self.sync_interval = sync_interval
        self.lookahead_days = lookahead_days
        self.matcher = LocationMatcher()
        self.state = SyncState()
        self._running = False
        self._task: asyncio.Task | None = None

    async def sync_once(self) -> SyncState:
        """Run a single sync cycle across all providers."""
        all_events: list[CalendarEvent] = []

        # Fetch from all providers in parallel
        tasks = [
            provider.fetch_events(self.lookahead_days)
            for provider in self.providers
        ]

        if not tasks:
            logger.info("No calendar providers configured")
            return self.state

        results = await asyncio.gather(*tasks, return_exceptions=True)

        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error("Calendar provider %d failed: %s", i, result)
                continue
            all_events.extend(result)

        # Deduplicate by (summary, start time)
        seen = set()
        unique_events = []
        for event in all_events:
            key = (event.summary, event.start.isoformat())
            if key not in seen:
                seen.add(key)
                unique_events.append(event)

        # Run location matching
        matches = []
        for event in unique_events:
            match = self.matcher.match_event(event)
            if match:
                matches.append(match)

        import time
        self.state = SyncState(
            events=unique_events,
            matches=matches,
            last_sync=time.time(),
        )

        logger.info(
            "Calendar sync: %d events, %d hotel matches from %d providers",
            len(unique_events),
            len(matches),
            len(self.providers),
        )
        return self.state

    async def start(self) -> None:
        """Start the background sync loop."""
        if self._running:
            return
        self._running = True
        self._task = asyncio.create_task(self._sync_loop())
        logger.info("Calendar sync daemon started (interval: %ds)", self.sync_interval)

    async def stop(self) -> None:
        """Stop the background sync loop."""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("Calendar sync daemon stopped")

    async def _sync_loop(self) -> None:
        """Background sync loop."""
        while self._running:
            try:
                await self.sync_once()
            except Exception as e:
                logger.error("Calendar sync error: %s", e)
            await asyncio.sleep(self.sync_interval)

    def get_current_matches(self) -> list[LocationMatch]:
        """Get hotel matches from the most recent sync."""
        return self.state.matches

    def get_ssid_hints(self) -> list[str]:
        """Get SSID patterns to prioritize from calendar matches."""
        hints = []
        for match in self.state.matches:
            hints.extend(match.ssid_patterns)
        return hints
