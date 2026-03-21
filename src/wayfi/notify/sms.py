"""Bidirectional Twilio SMS notification service."""

from __future__ import annotations

import asyncio
import logging
import re
from dataclasses import dataclass
from functools import partial

from twilio.rest import Client as TwilioClient

logger = logging.getLogger(__name__)


@dataclass
class SMSConfig:
    account_sid: str
    auth_token: str
    from_number: str
    to_number: str


@dataclass
class RoomNumberReply:
    room_number: str
    nights: int


def parse_room_reply(body: str) -> RoomNumberReply | None:
    """Parse inbound SMS for room number and optional stay duration.

    Accepts formats like:
    - "1412"
    - "1412, 3 nights"
    - "room 1412 3n"
    - "1412 for 2 nights"
    """
    body = body.strip().lower()

    # Extract room number (sequence of digits, possibly with letters like 12A)
    room_match = re.search(r"(?:room\s*)?(\d{1,5}[a-z]?)", body)
    if not room_match:
        return None
    room = room_match.group(1).upper()

    # Extract nights
    nights = 1
    nights_match = re.search(r"(\d+)\s*(?:nights?|n\b)", body)
    if nights_match:
        nights = int(nights_match.group(1))

    return RoomNumberReply(room_number=room, nights=max(1, nights))


class TwilioNotifier:
    """Twilio SMS service for connection notifications and room number collection."""

    def __init__(self, config: SMSConfig) -> None:
        self.config = config
        self._client = TwilioClient(config.account_sid, config.auth_token)
        self._room_callback: callable | None = None

    def _send_sync(self, body: str) -> str:
        """Send SMS synchronously (called in executor)."""
        msg = self._client.messages.create(
            body=body,
            from_=self.config.from_number,
            to=self.config.to_number,
        )
        return msg.sid

    async def _send(self, body: str) -> str:
        """Send SMS asynchronously."""
        loop = asyncio.get_event_loop()
        sid = await loop.run_in_executor(None, partial(self._send_sync, body))
        logger.info("SMS sent (SID: %s): %s", sid, body[:80])
        return sid

    async def send_connection_success(
        self, ssid: str, quality_score: float, vpn_active: bool
    ) -> str:
        vpn_status = "VPN active" if vpn_active else "No VPN"
        body = (
            f"WayFi connected to {ssid}\n"
            f"Quality: {quality_score:.1f}/10 | {vpn_status}"
        )
        return await self._send(body)

    async def send_portal_failure(self, ssid: str, reason: str) -> str:
        body = (
            f"WayFi could not solve portal for {ssid}\n"
            f"Reason: {reason}\n"
            f"You may need to log in manually."
        )
        return await self._send(body)

    async def send_connection_lost(self, ssid: str) -> str:
        body = f"WayFi lost connection to {ssid}. Reconnecting..."
        return await self._send(body)

    async def send_reconnection(self, ssid: str, quality_score: float) -> str:
        body = (
            f"WayFi reconnected to {ssid}\n"
            f"Quality: {quality_score:.1f}/10"
        )
        return await self._send(body)

    async def send_quality_alert(
        self, ssid: str, old_score: float, new_score: float
    ) -> str:
        body = (
            f"WayFi network quality dropped on {ssid}\n"
            f"Score: {old_score:.1f} -> {new_score:.1f}/10"
        )
        return await self._send(body)

    async def send_room_number_request(self, hotel_name: str) -> str:
        body = (
            f"WayFi needs your room number for {hotel_name}.\n"
            f"Reply with: ROOM_NUMBER, NIGHTS\n"
            f"Example: 1412, 3 nights"
        )
        return await self._send(body)

    def set_room_callback(self, callback: callable) -> None:
        """Set callback for when room number is received via inbound SMS."""
        self._room_callback = callback

    async def handle_inbound(self, from_number: str, body: str) -> str:
        """Process inbound SMS webhook. Returns TwiML response body."""
        logger.info("Inbound SMS from %s: %s", from_number, body)

        if from_number != self.config.to_number:
            logger.warning("Ignoring SMS from unknown number: %s", from_number)
            return "Ignored"

        parsed = parse_room_reply(body)
        if parsed and self._room_callback:
            await self._room_callback(parsed)
            return f"Room {parsed.room_number} saved for {parsed.nights} night(s)."

        return "Could not parse room number. Reply with: ROOM_NUMBER, NIGHTS"
