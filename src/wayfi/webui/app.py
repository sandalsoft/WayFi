"""FastAPI web UI application."""

from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from wayfi.webui.routers import calendar, logs, networks, patterns, settings, status, vault

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
    app.include_router(settings.router, prefix="/api")
    app.include_router(logs.router, prefix="/api")

    # Set up log buffer for streaming
    logs.setup_log_buffer()

    # HTML page routes
    @app.get("/")
    async def dashboard(request: Request):
        return templates.TemplateResponse("dashboard.html", {"request": request})

    @app.get("/vault")
    async def vault_page(request: Request):
        return templates.TemplateResponse("vault.html", {"request": request})

    @app.get("/networks")
    async def networks_page(request: Request):
        return templates.TemplateResponse("networks.html", {"request": request})

    @app.get("/patterns")
    async def patterns_page(request: Request):
        return templates.TemplateResponse("patterns.html", {"request": request})

    @app.get("/settings")
    async def settings_page(request: Request):
        return templates.TemplateResponse("settings.html", {"request": request})

    @app.get("/logs")
    async def logs_page(request: Request):
        return templates.TemplateResponse("logs.html", {"request": request})

    return app
