"""Calendar configuration and status API routes."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

router = APIRouter(tags=["calendar"])


class CalendarSourceRequest(BaseModel):
    provider: str  # icloud, google, outlook
    name: str
    # Provider-specific config stored in vault


@router.get("/calendars")
async def list_calendars(request: Request) -> dict:
    """List configured calendar sources and upcoming matches."""
    orch = request.app.state.orchestrator
    if not orch or not orch.calendar:
        return {"sources": [], "matches": [], "events": []}

    state = orch.calendar.state
    return {
        "sources": [
            {"provider": type(p).__name__.lower(), "index": i}
            for i, p in enumerate(orch.calendar.providers)
        ],
        "events": [
            {
                "summary": e.summary,
                "location": e.location,
                "start": e.start.isoformat(),
                "end": e.end.isoformat(),
                "provider": e.provider,
            }
            for e in state.events
        ],
        "matches": [
            {
                "venue": m.venue_name,
                "chain": m.chain,
                "city": m.city,
                "check_in": m.check_in,
                "check_out": m.check_out,
                "nights": m.nights,
                "ssid_patterns": m.ssid_patterns,
                "portal_pattern": m.portal_pattern,
            }
            for m in state.matches
        ],
        "last_sync": state.last_sync,
    }


@router.post("/calendars/sync")
async def trigger_sync(request: Request) -> dict:
    """Trigger an immediate calendar sync."""
    orch = request.app.state.orchestrator
    if not orch or not orch.calendar:
        raise HTTPException(status_code=503, detail="Calendar not configured")
    state = await orch.calendar.sync_once()
    return {
        "status": "synced",
        "events": len(state.events),
        "matches": len(state.matches),
    }
