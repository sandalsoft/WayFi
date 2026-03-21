"""Captive portal detection via HTTP probes."""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field

import aiohttp

logger = logging.getLogger(__name__)

DEFAULT_PROBE_URL = "http://connectivitycheck.gstatic.com/generate_204"
FALLBACK_PROBES = [
    "http://captive.apple.com",
    "http://detectportal.firefox.com",
]


@dataclass
class PortalResult:
    is_captive: bool
    redirect_url: str = ""
    portal_html: str = ""
    probe_url: str = ""
    status_code: int = 0
    error: str = ""


class PortalDetector:
    """Detect captive portals by sending HTTP probes and checking responses.

    A captive portal is detected when:
    - The probe returns a 302/301/307 redirect (most common)
    - The probe returns 200 with body content (some portals intercept and inject HTML)
    - The probe returns 200 but content doesn't match expected empty/known response
    """

    def __init__(
        self,
        probe_url: str = DEFAULT_PROBE_URL,
        fallbacks: list[str] | None = None,
        timeout: float = 2.0,
    ) -> None:
        self.probe_url = probe_url
        self.fallbacks = fallbacks if fallbacks is not None else FALLBACK_PROBES
        self.timeout = timeout

    async def detect(self) -> PortalResult:
        """Run portal detection probes. Returns first definitive result."""
        result = await self._probe(self.probe_url)
        if result.is_captive or result.error == "":
            return result

        # Primary probe failed with error — try fallbacks
        for url in self.fallbacks:
            result = await self._probe(url)
            if result.error == "":
                return result

        return result

    async def _probe(self, url: str) -> PortalResult:
        """Send a single HTTP probe and interpret the response."""
        timeout = aiohttp.ClientTimeout(total=self.timeout)
        try:
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(
                    url, allow_redirects=False, ssl=False
                ) as resp:
                    status = resp.status

                    # 204 No Content = no portal, we have internet
                    if status == 204:
                        return PortalResult(
                            is_captive=False,
                            probe_url=url,
                            status_code=status,
                        )

                    # 301/302/307/308 redirect = portal
                    if status in (301, 302, 307, 308):
                        redirect_url = str(resp.headers.get("Location", ""))
                        # Fetch the portal page
                        portal_html = await self._fetch_portal(session, redirect_url)
                        return PortalResult(
                            is_captive=True,
                            redirect_url=redirect_url,
                            portal_html=portal_html,
                            probe_url=url,
                            status_code=status,
                        )

                    # 200 with body = portal injected content
                    body = await resp.text()
                    if status == 200 and len(body) > 0:
                        # Apple's captive check returns "Success" when connected
                        if url == "http://captive.apple.com" and body.strip() == "Success":
                            return PortalResult(
                                is_captive=False,
                                probe_url=url,
                                status_code=status,
                            )
                        # Firefox returns "success\n"
                        if "detectportal" in url and body.strip() == "success":
                            return PortalResult(
                                is_captive=False,
                                probe_url=url,
                                status_code=status,
                            )
                        # Google's should be empty 204, so 200 with body = portal
                        return PortalResult(
                            is_captive=True,
                            portal_html=body,
                            probe_url=url,
                            status_code=status,
                        )

                    return PortalResult(
                        is_captive=False,
                        probe_url=url,
                        status_code=status,
                    )

        except asyncio.TimeoutError:
            # Timeout often means portal is blocking — treat as portal
            logger.warning("Probe timeout for %s — may indicate portal", url)
            return PortalResult(
                is_captive=False,
                probe_url=url,
                error="timeout",
            )
        except aiohttp.ClientError as e:
            logger.error("Probe error for %s: %s", url, e)
            return PortalResult(
                is_captive=False,
                probe_url=url,
                error=str(e),
            )

    async def _fetch_portal(
        self, session: aiohttp.ClientSession, url: str
    ) -> str:
        """Fetch portal page HTML from redirect URL."""
        if not url:
            return ""
        try:
            async with session.get(url, ssl=False) as resp:
                return await resp.text()
        except Exception as e:
            logger.warning("Failed to fetch portal at %s: %s", url, e)
            return ""

    async def verify_connectivity(self) -> bool:
        """Quick check — are we actually online?"""
        result = await self._probe(self.probe_url)
        return not result.is_captive and result.error == ""
