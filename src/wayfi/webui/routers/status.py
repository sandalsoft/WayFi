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


async def _system_status() -> dict:
    """Read network state directly from the system (no orchestrator)."""
    ssid = ""
    ip_address = ""
    ap_active = False

    # Check upstream WiFi (wlan0)
    try:
        proc = await asyncio.create_subprocess_exec(
            "iw", "dev", "wlan0", "link",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, _ = await proc.communicate()
        output = stdout.decode("utf-8", errors="replace")
        for line in output.splitlines():
            line = line.strip()
            if line.startswith("SSID:"):
                ssid = line.split(":", 1)[1].strip()
    except Exception:
        pass

    # Get IP
    try:
        proc = await asyncio.create_subprocess_exec(
            "ip", "-4", "-br", "addr", "show", "wlan0",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, _ = await proc.communicate()
        parts = stdout.decode().split()
        for p in parts:
            if "/" in p and p[0].isdigit():
                ip_address = p.split("/")[0]
                break
    except Exception:
        pass

    # Check AP
    try:
        proc = await asyncio.create_subprocess_exec(
            "systemctl", "is-active", "wayfi-hostapd",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, _ = await proc.communicate()
        ap_active = stdout.decode().strip() == "active"
    except Exception:
        pass

    clients = await _get_ap_clients()

    if ssid:
        state = "MONITOR"
    elif ip_address:
        state = "CONNECT"
    else:
        state = "SCAN"

    return {
        "state": state,
        "ssid": ssid,
        "ip_address": ip_address,
        "ap_active": ap_active,
        "ap_clients": len(clients),
        "quality_score": 0,
        "vpn_active": False,
        "portal_solved": bool(ssid),
        "uptime_seconds": 0,
        "connected_at": 0,
    }


@router.get("/status")
async def get_status(request: Request) -> dict:
    """Get current WayFi connection status."""
    orch = request.app.state.orchestrator

    if not orch:
        # No orchestrator — read system state directly
        return await _system_status()

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
