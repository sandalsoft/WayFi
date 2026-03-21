"""Tests for captive portal detection."""

from __future__ import annotations

import pytest

from wayfi.portal.detector import PortalDetector


@pytest.fixture
async def mock_portal_server():
    """Start a mock server that simulates a captive portal."""
    from tests.mock_portal.server import start_server
    runner, base_url = await start_server(port=18888, portal_type="generic")
    yield base_url
    await runner.cleanup()


@pytest.fixture
async def mock_open_server():
    """Start a mock server that returns 204 (no portal)."""
    from aiohttp import web

    async def handle(request):
        return web.Response(status=204)

    app = web.Application()
    app.router.add_get("/generate_204", handle)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "127.0.0.1", 18889)
    await site.start()
    yield "http://127.0.0.1:18889"
    await runner.cleanup()


class TestPortalDetection:
    async def test_detect_portal_via_redirect(self, mock_portal_server):
        detector = PortalDetector(
            probe_url=f"{mock_portal_server}/generate_204",
            timeout=5.0,
        )
        result = await detector.detect()
        assert result.is_captive is True
        assert result.status_code == 302

    async def test_detect_no_portal(self, mock_open_server):
        detector = PortalDetector(
            probe_url=f"{mock_open_server}/generate_204",
            timeout=5.0,
        )
        result = await detector.detect()
        assert result.is_captive is False

    async def test_verify_connectivity(self, mock_open_server):
        detector = PortalDetector(
            probe_url=f"{mock_open_server}/generate_204",
            timeout=5.0,
        )
        assert await detector.verify_connectivity() is True

    async def test_timeout_handling(self):
        detector = PortalDetector(
            probe_url="http://192.0.2.1/generate_204",  # non-routable
            fallbacks=[],
            timeout=0.5,
        )
        result = await detector.detect()
        assert result.error == "timeout"
