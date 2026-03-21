"""Settings management API routes."""

from __future__ import annotations

from pathlib import Path

import yaml
from fastapi import APIRouter, Request
from pydantic import BaseModel

router = APIRouter(tags=["settings"])

CONFIG_PATH = Path("config/wayfi.yaml")


class SettingsUpdate(BaseModel):
    section: str
    values: dict


@router.get("/settings")
async def get_settings() -> dict:
    """Get current configuration."""
    if CONFIG_PATH.exists():
        config = yaml.safe_load(CONFIG_PATH.read_text()) or {}
    else:
        config = {}
    return {"settings": config}


@router.post("/settings")
async def update_settings(body: SettingsUpdate) -> dict:
    """Update a configuration section."""
    if CONFIG_PATH.exists():
        config = yaml.safe_load(CONFIG_PATH.read_text()) or {}
    else:
        config = {}

    config[body.section] = {**config.get(body.section, {}), **body.values}

    CONFIG_PATH.write_text(yaml.dump(config, default_flow_style=False))
    return {"status": "updated", "section": body.section}
