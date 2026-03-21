"""FastAPI web UI application."""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from wayfi.webui.routers import calendar, networks, patterns, status, vault

STATIC_DIR = Path(__file__).parent / "static"
TEMPLATE_DIR = Path(__file__).parent / "templates"


def create_app(
    orchestrator=None,
    vault_instance=None,
) -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(title="WayFi", version="0.1.0")

    # CORS for local network access
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Static files
    if STATIC_DIR.exists():
        app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

    # Templates
    templates = Jinja2Templates(directory=str(TEMPLATE_DIR))

    # Store shared state
    app.state.orchestrator = orchestrator
    app.state.vault = vault_instance
    app.state.templates = templates

    # Register routers
    app.include_router(status.router, prefix="/api")
    app.include_router(vault.router, prefix="/api")
    app.include_router(networks.router, prefix="/api")
    app.include_router(patterns.router, prefix="/api")
    app.include_router(calendar.router, prefix="/api")

    return app
