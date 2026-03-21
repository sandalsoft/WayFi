"""Status dashboard API routes."""

from __future__ import annotations

import time

from fastapi import APIRouter, Request

router = APIRouter(tags=["status"])


@router.get("/status")
async def get_status(request: Request) -> dict:
    """Get current WayFi connection status."""
    orch = request.app.state.orchestrator

    if not orch:
        return {
            "state": "unknown",
            "message": "Orchestrator not initialized",
        }

    os = orch.os
    uptime = time.time() - os.boot_time if os.boot_time else 0

    return {
        "state": os.state.value,
        "ssid": os.current_ssid,
        "bssid": os.current_bssid,
        "ip_address": os.ip_address,
        "quality_score": os.quality_score,
        "vpn_active": os.vpn_active,
        "portal_solved": os.portal_solved,
        "uptime_seconds": round(uptime),
        "connected_at": os.connected_at,
    }


@router.get("/health")
async def health_check() -> dict:
    return {"status": "ok", "service": "wayfi"}
