"""Network profile management API routes."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

router = APIRouter(tags=["networks"])


class NetworkProfileRequest(BaseModel):
    ssid: str
    password: str = ""
    vpn_policy: str = "always"  # always, never, ask
    notes: str = ""


# In-memory store (backed by config in production)
_network_profiles: dict[str, dict] = {}


@router.get("/networks")
async def list_networks(request: Request) -> dict:
    """List saved network profiles."""
    return {"networks": list(_network_profiles.values())}


@router.get("/networks/scan")
async def scan_networks(request: Request) -> dict:
    """Trigger a WiFi scan and return results."""
    orch = request.app.state.orchestrator
    if not orch or not orch.scanner:
        raise HTTPException(status_code=503, detail="Scanner not available")
    results = await orch.scanner.scan()
    return {
        "networks": [
            {
                "ssid": r.ssid,
                "bssid": r.bssid,
                "signal": r.signal,
                "signal_quality": r.signal_quality,
                "security": r.security.value,
                "frequency": r.frequency,
                "is_5ghz": r.is_5ghz,
                "saved": r.ssid in _network_profiles,
            }
            for r in results
        ]
    }


@router.post("/networks")
async def save_network(body: NetworkProfileRequest) -> dict:
    """Save or update a network profile."""
    _network_profiles[body.ssid] = {
        "ssid": body.ssid,
        "password": body.password,
        "vpn_policy": body.vpn_policy,
        "notes": body.notes,
    }
    return {"status": "saved", "ssid": body.ssid}


@router.delete("/networks/{ssid}")
async def delete_network(ssid: str) -> dict:
    """Delete a saved network profile."""
    if ssid not in _network_profiles:
        raise HTTPException(status_code=404, detail="Network not found")
    del _network_profiles[ssid]
    return {"status": "deleted", "ssid": ssid}
