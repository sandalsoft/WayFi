"""Mock captive portal HTTP server for testing."""

from __future__ import annotations

import asyncio
from pathlib import Path

from aiohttp import web

PORTALS_DIR = Path(__file__).parent / "portals"

# Track which portals have been "solved"
_solved_sessions: set[str] = set()


async def connectivity_check(request: web.Request) -> web.Response:
    """Simulate connectivity check endpoint.

    Returns 302 redirect to portal if not solved, 204 if solved.
    """
    client = request.remote or "unknown"
    portal_type = request.app.get("portal_type", "generic")

    if client in _solved_sessions:
        return web.Response(status=204)

    portal_url = f"http://{request.host}/portal/{portal_type}"
    raise web.HTTPFound(location=portal_url)


async def serve_portal(request: web.Request) -> web.Response:
    """Serve a portal HTML page by type."""
    portal_type = request.match_info.get("portal_type", "generic")
    html_file = PORTALS_DIR / f"{portal_type}.html"

    if not html_file.exists():
        return web.Response(status=404, text=f"Portal '{portal_type}' not found")

    html = html_file.read_text()
    return web.Response(text=html, content_type="text/html")


async def handle_login(request: web.Request) -> web.Response:
    """Handle portal form submission.

    Marks the client as solved if the submission includes required fields.
    """
    client = request.remote or "unknown"
    data = await request.post()

    # For testing, any POST with at least one field counts as a solve
    if len(data) > 0:
        _solved_sessions.add(client)
        return web.Response(
            status=200,
            text="<html><body><h1>Connected!</h1></body></html>",
            content_type="text/html",
        )

    return web.Response(status=400, text="Missing required fields")


async def reset(request: web.Request) -> web.Response:
    """Reset all solved sessions (for test cleanup)."""
    _solved_sessions.clear()
    return web.Response(text="reset")


def create_app(portal_type: str = "generic") -> web.Application:
    """Create the mock portal web application."""
    app = web.Application()
    app["portal_type"] = portal_type

    app.router.add_get("/generate_204", connectivity_check)
    app.router.add_get("/portal/{portal_type}", serve_portal)
    app.router.add_post("/login", handle_login)
    app.router.add_post("/portal/{portal_type}/login", handle_login)
    app.router.add_get("/reset", reset)

    return app


async def start_server(
    port: int = 8888, portal_type: str = "generic"
) -> tuple[web.AppRunner, str]:
    """Start the mock portal server. Returns (runner, base_url)."""
    app = create_app(portal_type)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "127.0.0.1", port)
    await site.start()
    return runner, f"http://127.0.0.1:{port}"


if __name__ == "__main__":
    app = create_app()
    web.run_app(app, host="127.0.0.1", port=8888)
