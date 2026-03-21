"""Portal form submission via requests and Playwright fallback."""

from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import re
from dataclasses import dataclass, field
from urllib.parse import urljoin

import aiohttp
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


@dataclass
class SubmitResult:
    success: bool
    method: str  # "heuristic", "llm", "cloud", "playwright"
    status_code: int = 0
    redirect_url: str = ""
    error: str = ""


@dataclass
class SubmitRequest:
    portal_url: str
    action_url: str
    method: str  # GET or POST
    fields: dict[str, str]
    checkboxes: list[str] = field(default_factory=list)
    cookies: dict[str, str] = field(default_factory=dict)


def fingerprint_portal(html: str) -> str:
    """Generate a stable fingerprint for a portal page based on form structure.

    Hashes sorted field names + action URL pattern. This fingerprint stays
    stable across sessions (unlike tokens/nonces in the full HTML).
    """
    soup = BeautifulSoup(html, "html.parser")
    form = soup.find("form")
    if not form:
        return hashlib.sha256(b"no-form").hexdigest()[:16]

    field_names = sorted(
        inp.get("name", "")
        for inp in form.find_all(["input", "select", "textarea"])
        if inp.get("name")
    )
    action = form.get("action", "")
    # Strip session-specific tokens from action URL
    action_clean = re.sub(r"[?&][\w]+=[\w%-]+", "", action)

    fingerprint_data = json.dumps({"fields": field_names, "action": action_clean})
    return hashlib.sha256(fingerprint_data.encode()).hexdigest()[:16]


def extract_form_details(html: str, base_url: str) -> dict | None:
    """Extract form action URL, method, hidden fields, and checkboxes from HTML."""
    soup = BeautifulSoup(html, "html.parser")
    form = soup.find("form")
    if not form:
        return None

    action = form.get("action", "")
    if action and not action.startswith("http"):
        action = urljoin(base_url, action)

    method = form.get("method", "POST").upper()

    # Collect hidden fields (tokens, session IDs)
    hidden_fields = {}
    for inp in form.find_all("input", {"type": "hidden"}):
        name = inp.get("name")
        if name:
            hidden_fields[name] = inp.get("value", "")

    # Collect checkbox names
    checkboxes = []
    for inp in form.find_all("input", {"type": "checkbox"}):
        name = inp.get("name")
        if name:
            checkboxes.append(name)

    return {
        "action": action or base_url,
        "method": method,
        "hidden_fields": hidden_fields,
        "checkboxes": checkboxes,
    }


class PortalSubmitter:
    """Submit portal forms via HTTP requests, with Playwright as fallback."""

    def __init__(self, verify_url: str = "http://connectivitycheck.gstatic.com/generate_204") -> None:
        self.verify_url = verify_url
        self._strategy_cache: dict[str, dict] = {}

    async def submit(self, request: SubmitRequest, portal_html: str = "") -> SubmitResult:
        """Submit a portal form and verify connectivity afterward."""
        # Merge hidden fields from HTML into the request
        form_details = None
        if portal_html:
            form_details = extract_form_details(portal_html, request.portal_url)

        result = await self._submit_http(request, form_details)

        if result.success:
            # Verify we actually have internet
            verified = await self._verify_connectivity()
            if not verified:
                result.success = False
                result.error = "Form submitted but connectivity check failed"

        if result.success and portal_html:
            # Cache the successful strategy
            fp = fingerprint_portal(portal_html)
            self._strategy_cache[fp] = {
                "action_url": request.action_url,
                "method": request.method,
                "fields": list(request.fields.keys()),
                "checkboxes": request.checkboxes,
            }

        return result

    async def _submit_http(
        self, request: SubmitRequest, form_details: dict | None
    ) -> SubmitResult:
        """Submit form via aiohttp."""
        fields = dict(request.fields)

        # Add hidden fields from HTML
        if form_details:
            fields.update(form_details["hidden_fields"])

        # Set checkboxes to "on"
        for cb in request.checkboxes:
            fields[cb] = "on"

        action_url = request.action_url
        if not action_url and form_details:
            action_url = form_details["action"]
        if not action_url:
            action_url = request.portal_url

        timeout = aiohttp.ClientTimeout(total=10)
        jar = aiohttp.CookieJar()

        try:
            async with aiohttp.ClientSession(
                timeout=timeout, cookie_jar=jar
            ) as session:
                # First fetch portal to get cookies
                if request.portal_url:
                    await session.get(request.portal_url, ssl=False)

                if request.method == "GET":
                    async with session.get(
                        action_url, params=fields, ssl=False
                    ) as resp:
                        status = resp.status
                        redirect = str(resp.url)
                else:
                    async with session.post(
                        action_url, data=fields, ssl=False, allow_redirects=True
                    ) as resp:
                        status = resp.status
                        redirect = str(resp.url)

                return SubmitResult(
                    success=status in (200, 301, 302, 303, 307, 308),
                    method="http",
                    status_code=status,
                    redirect_url=redirect,
                )

        except Exception as e:
            logger.warning("HTTP submit failed: %s", e)
            return SubmitResult(
                success=False, method="http", error=str(e)
            )

    async def submit_with_playwright(self, request: SubmitRequest) -> SubmitResult:
        """Fallback: use Playwright headless browser for JS-heavy portals."""
        try:
            from playwright.async_api import async_playwright
        except ImportError:
            return SubmitResult(
                success=False, method="playwright",
                error="Playwright not installed",
            )

        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                context = await browser.new_context()
                page = await context.new_page()

                await page.goto(request.portal_url, wait_until="networkidle", timeout=15000)

                # Fill form fields
                for name, value in request.fields.items():
                    try:
                        await page.fill(f'[name="{name}"]', value, timeout=3000)
                    except Exception:
                        # Try by ID or placeholder
                        try:
                            await page.fill(f"#{name}", value, timeout=2000)
                        except Exception:
                            logger.warning("Could not fill field: %s", name)

                # Check checkboxes
                for cb in request.checkboxes:
                    try:
                        await page.check(f'[name="{cb}"]', timeout=2000)
                    except Exception:
                        logger.warning("Could not check: %s", cb)

                # Click submit
                submit = page.locator('button[type="submit"], input[type="submit"]').first
                await submit.click(timeout=5000)
                await page.wait_for_load_state("networkidle", timeout=10000)

                await browser.close()

                # Verify connectivity
                verified = await self._verify_connectivity()
                return SubmitResult(
                    success=verified,
                    method="playwright",
                )

        except Exception as e:
            logger.error("Playwright submit failed: %s", e)
            return SubmitResult(
                success=False, method="playwright", error=str(e)
            )

    async def _verify_connectivity(self) -> bool:
        """Check if we have internet access after form submission."""
        timeout = aiohttp.ClientTimeout(total=5)
        try:
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(
                    self.verify_url, allow_redirects=False, ssl=False
                ) as resp:
                    return resp.status == 204
        except Exception:
            return False

    def get_cached_strategy(self, portal_html: str) -> dict | None:
        """Look up a previously successful strategy by portal fingerprint."""
        fp = fingerprint_portal(portal_html)
        return self._strategy_cache.get(fp)
