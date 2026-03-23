"""Status dashboard API routes."""

from __future__ import annotations

import asyncio
import re
import time
from pathlib import Path

from fastapi import APIRouter, Request

router = APIRouter(tags=["status"])


async def _get_ap_clients(interface: str = "wlan1") -> list[dict]:
    """Get connected AP clients from iw station dump and DHCP leases."""
    clients = {}

    # Get station info (MAC, signal, tx/rx bytes)
    try:
        proc = await asyncio.create_subprocess_exec(
            "iw", "dev", interface, "station", "dump",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, _ = await proc.communicate()
        output = stdout.decode("utf-8", errors="replace")

        current_mac = None
        for line in output.splitlines():
            line = line.strip()
            m = re.match(r"Station\s+([0-9a-f:]{17})", line, re.IGNORECASE)
            if m:
                current_mac = m.group(1).lower()
                clients[current_mac] = {"mac": current_mac}
                continue
            if current_mac and ":" in line:
                key, _, val = line.partition(":")
                val = val.strip()
                key = key.strip()
                if key == "signal":
                    clients[current_mac]["signal_dbm"] = val.split()[0]
                elif key == "rx bytes":
                    clients[current_mac]["rx_bytes"] = int(val)
                elif key == "tx bytes":
                    clients[current_mac]["tx_bytes"] = int(val)
                elif key == "connected time":
                    clients[current_mac]["connected_secs"] = int(val.split()[0])
    except Exception:
        pass

    # Enrich with DHCP lease info (IP + hostname)
    lease_file = Path("/var/lib/misc/dnsmasq.leases")
    if lease_file.exists():
        try:
            for line in lease_file.read_text().splitlines():
                parts = line.split()
                if len(parts) >= 4:
                    mac = parts[1].lower()
                    ip = parts[2]
                    hostname = parts[3] if parts[3] != "*" else ""
                    if mac in clients:
                        clients[mac]["ip"] = ip
                        clients[mac]["hostname"] = hostname
                    else:
                        clients[mac] = {
                            "mac": mac, "ip": ip, "hostname": hostname,
                        }
        except Exception:
            pass

    return list(clients.values())


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


@router.get("/clients")
async def get_clients() -> dict:
    """Get connected AP clients."""
    clients = await _get_ap_clients()
    return {"clients": clients, "count": len(clients)}


@router.get("/health")
async def health_check() -> dict:
    return {"status": "ok", "service": "wayfi"}
