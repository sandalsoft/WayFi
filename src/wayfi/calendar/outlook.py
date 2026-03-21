"""Microsoft Outlook calendar provider via MSAL and Graph API."""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta, timezone
from functools import partial

import aiohttp
import msal

from wayfi.calendar.icloud import CalendarEvent

logger = logging.getLogger(__name__)

GRAPH_ENDPOINT = "https://graph.microsoft.com/v1.0"
SCOPES = ["Calendars.Read"]


class OutlookCalendar:
    """Fetch events from Microsoft Outlook via Graph API with device code flow."""

    def __init__(
        self,
        client_id: str,
        tenant_id: str = "common",
        refresh_token: str | None = None,
    ) -> None:
        self.client_id = client_id
        self.tenant_id = tenant_id
        self._refresh_token = refresh_token
        self._access_token: str | None = None
        self._app = msal.PublicClientApplication(
            client_id,
            authority=f"https://login.microsoftonline.com/{tenant_id}",
        )

    def initiate_device_flow(self) -> dict:
        """Start device code flow for initial authorization.

        Returns flow dict with 'user_code' and 'verification_uri' for the user.
        """
        flow = self._app.initiate_device_flow(scopes=SCOPES)
        if "user_code" not in flow:
            raise RuntimeError(f"Device flow initiation failed: {flow}")
        return flow

    def complete_device_flow(self, flow: dict) -> str:
        """Complete device code flow after user authorizes. Returns refresh token."""
        result = self._app.acquire_token_by_device_flow(flow)
        if "access_token" not in result:
            raise RuntimeError(f"Device flow auth failed: {result.get('error_description', 'Unknown error')}")
        self._access_token = result["access_token"]
        self._refresh_token = result.get("refresh_token", "")
        return self._refresh_token

    def _get_access_token(self) -> str:
        """Get a valid access token, refreshing if needed."""
        if self._access_token:
            return self._access_token

        if not self._refresh_token:
            raise RuntimeError("Outlook not authorized. Run device flow setup.")

        accounts = self._app.get_accounts()
        if accounts:
            result = self._app.acquire_token_silent(SCOPES, account=accounts[0])
            if result and "access_token" in result:
                self._access_token = result["access_token"]
                return self._access_token

        # Use refresh token directly
        result = self._app.acquire_token_by_refresh_token(
            self._refresh_token, scopes=SCOPES
        )
        if "access_token" not in result:
            raise RuntimeError("Token refresh failed. Re-authorize via device flow.")
        self._access_token = result["access_token"]
        self._refresh_token = result.get("refresh_token", self._refresh_token)
        return self._access_token

    async def fetch_events(self, lookahead_days: int = 7) -> list[CalendarEvent]:
        """Fetch events from Outlook calendar view."""
        token = await asyncio.get_event_loop().run_in_executor(
            None, self._get_access_token
        )

        now = datetime.now(timezone.utc)
        end = now + timedelta(days=lookahead_days)

        url = (
            f"{GRAPH_ENDPOINT}/me/calendarview"
            f"?startdatetime={now.isoformat()}"
            f"&enddatetime={end.isoformat()}"
            f"&$top=100"
            f"&$orderby=start/dateTime"
        )

        headers = {
            "Authorization": f"Bearer {token}",
            "Prefer": 'outlook.timezone="UTC"',
        }

        timeout = aiohttp.ClientTimeout(total=15)
        try:
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(url, headers=headers) as resp:
                    if resp.status != 200:
                        text = await resp.text()
                        logger.error("Graph API error %d: %s", resp.status, text[:200])
                        return []
                    data = await resp.json()
        except Exception as e:
            logger.error("Outlook API call failed: %s", e)
            return []

        events: list[CalendarEvent] = []
        for item in data.get("value", []):
            parsed = self._parse_event(item)
            if parsed:
                events.append(parsed)

        logger.info("Outlook: fetched %d events", len(events))
        return events

    def _parse_event(self, item: dict) -> CalendarEvent | None:
        """Parse a Graph API event into CalendarEvent."""
        try:
            summary = item.get("subject", "")
            location_data = item.get("location", {})
            location = location_data.get("displayName", "")

            start_raw = item.get("start", {}).get("dateTime", "")
            end_raw = item.get("end", {}).get("dateTime", "")

            start = datetime.fromisoformat(start_raw.rstrip("Z")).replace(
                tzinfo=timezone.utc
            )
            end = datetime.fromisoformat(end_raw.rstrip("Z")).replace(
                tzinfo=timezone.utc
            )

            return CalendarEvent(
                summary=summary,
                location=location,
                start=start,
                end=end,
                uid=item.get("id", ""),
                provider="outlook",
            )
        except Exception as e:
            logger.warning("Failed to parse Outlook event: %s", e)
            return None

    @property
    def refresh_token(self) -> str | None:
        return self._refresh_token
