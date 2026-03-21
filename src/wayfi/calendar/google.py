"""Google Calendar API provider with OAuth2 device flow."""

from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime, timedelta, timezone
from functools import partial
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from wayfi.calendar.icloud import CalendarEvent

logger = logging.getLogger(__name__)

SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]


class GoogleCalendar:
    """Fetch events from Google Calendar using OAuth2."""

    def __init__(
        self,
        credentials_json: str | Path | None = None,
        token_data: dict | None = None,
    ) -> None:
        self._credentials_json = credentials_json
        self._token_data = token_data
        self._creds: Credentials | None = None

    def _get_credentials(self) -> Credentials:
        """Load or refresh OAuth2 credentials."""
        if self._creds and self._creds.valid:
            return self._creds

        if self._token_data:
            self._creds = Credentials.from_authorized_user_info(
                self._token_data, SCOPES
            )

        if self._creds and self._creds.expired and self._creds.refresh_token:
            self._creds.refresh(Request())
            return self._creds

        if not self._creds or not self._creds.valid:
            if not self._credentials_json:
                raise RuntimeError(
                    "Google Calendar not authorized. Run initial setup via web UI."
                )
            flow = InstalledAppFlow.from_client_secrets_file(
                str(self._credentials_json), SCOPES
            )
            self._creds = flow.run_local_server(port=0)

        return self._creds

    def get_token_data(self) -> dict | None:
        """Export current token data for vault storage."""
        if self._creds:
            return json.loads(self._creds.to_json())
        return None

    def _fetch_events_sync(self, lookahead_days: int) -> list[CalendarEvent]:
        """Synchronous Google Calendar API fetch."""
        creds = self._get_credentials()
        service = build("calendar", "v3", credentials=creds)

        now = datetime.now(timezone.utc)
        end = now + timedelta(days=lookahead_days)

        events_result = (
            service.events()
            .list(
                calendarId="primary",
                timeMin=now.isoformat(),
                timeMax=end.isoformat(),
                singleEvents=True,
                orderBy="startTime",
                maxResults=100,
            )
            .execute()
        )

        items = events_result.get("items", [])
        events: list[CalendarEvent] = []

        for item in items:
            parsed = self._parse_event(item)
            if parsed:
                events.append(parsed)

        logger.info("Google Calendar: fetched %d events", len(events))
        return events

    def _parse_event(self, item: dict) -> CalendarEvent | None:
        """Parse a Google Calendar API event into CalendarEvent."""
        try:
            summary = item.get("summary", "")
            location = item.get("location", "")

            start_raw = item.get("start", {})
            end_raw = item.get("end", {})

            start = self._parse_datetime(start_raw)
            end = self._parse_datetime(end_raw)

            if not start or not end:
                return None

            return CalendarEvent(
                summary=summary,
                location=location,
                start=start,
                end=end,
                uid=item.get("id", ""),
                provider="google",
            )
        except Exception as e:
            logger.warning("Failed to parse Google event: %s", e)
            return None

    def _parse_datetime(self, raw: dict) -> datetime | None:
        """Parse Google's dateTime or date field."""
        if "dateTime" in raw:
            dt_str = raw["dateTime"]
            return datetime.fromisoformat(dt_str)
        if "date" in raw:
            return datetime.strptime(raw["date"], "%Y-%m-%d").replace(
                tzinfo=timezone.utc
            )
        return None

    async def fetch_events(self, lookahead_days: int = 7) -> list[CalendarEvent]:
        """Async wrapper for Google Calendar fetch."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, partial(self._fetch_events_sync, lookahead_days)
        )
