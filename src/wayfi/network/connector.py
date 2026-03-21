"""WiFi connection management via wpa_supplicant."""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ConnectionResult:
    success: bool
    ssid: str
    bssid: str = ""
    ip_address: str = ""
    error: str = ""


class WiFiConnector:
    """Async WiFi connection manager wrapping wpa_cli."""

    def __init__(self, interface: str = "wlan0", dhcp_timeout: int = 5) -> None:
        self.interface = interface
        self.dhcp_timeout = dhcp_timeout
        self._lock = asyncio.Lock()
        self._connected_event = asyncio.Event()

    async def _run_wpa_cli(self, *args: str) -> str:
        cmd = ["wpa_cli", "-i", self.interface] + list(args)
        async with self._lock:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await proc.communicate()
        return stdout.decode("utf-8", errors="replace")

    async def _run_cmd(self, *args: str, timeout: int = 10) -> tuple[str, str, int]:
        proc = await asyncio.create_subprocess_exec(
            *args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        try:
            stdout, stderr = await asyncio.wait_for(
                proc.communicate(), timeout=timeout
            )
        except asyncio.TimeoutError:
            proc.kill()
            return "", "timeout", -1
        return (
            stdout.decode("utf-8", errors="replace"),
            stderr.decode("utf-8", errors="replace"),
            proc.returncode,
        )

    async def connect_to_network(
        self, ssid: str, password: str | None = None, bssid: str | None = None
    ) -> ConnectionResult:
        """Connect to a WiFi network by SSID, optionally with password and BSSID."""
        logger.info("Connecting to %s on %s", ssid, self.interface)

        # Add network
        output = await self._run_wpa_cli("add_network")
        network_id = output.strip().splitlines()[-1].strip()

        try:
            int(network_id)
        except ValueError:
            return ConnectionResult(
                success=False, ssid=ssid, error=f"Failed to add network: {output}"
            )

        # Set SSID
        await self._run_wpa_cli("set_network", network_id, "ssid", f'"{ssid}"')

        if password:
            await self._run_wpa_cli("set_network", network_id, "psk", f'"{password}"')
        else:
            await self._run_wpa_cli("set_network", network_id, "key_mgmt", "NONE")

        if bssid:
            await self._run_wpa_cli("set_network", network_id, "bssid", bssid)

        # Enable and select
        await self._run_wpa_cli("select_network", network_id)

        # Wait for DHCP
        ip = await self._wait_for_dhcp()
        if not ip:
            await self._run_wpa_cli("remove_network", network_id)
            return ConnectionResult(
                success=False, ssid=ssid, error="DHCP timeout"
            )

        status = await self.get_current_network()
        return ConnectionResult(
            success=True,
            ssid=ssid,
            bssid=status.get("bssid", ""),
            ip_address=ip,
        )

    async def _wait_for_dhcp(self) -> str | None:
        """Wait for DHCP lease. Returns IP or None on timeout."""
        for _ in range(self.dhcp_timeout * 2):
            stdout, _, _ = await self._run_cmd("ip", "addr", "show", self.interface)
            for line in stdout.splitlines():
                line = line.strip()
                if line.startswith("inet ") and "127.0.0.1" not in line:
                    ip = line.split()[1].split("/")[0]
                    logger.info("Got DHCP lease: %s", ip)
                    return ip
            await asyncio.sleep(0.5)
        logger.warning("DHCP timeout on %s", self.interface)
        return None

    async def disconnect(self) -> None:
        """Disconnect from current network."""
        await self._run_wpa_cli("disconnect")
        logger.info("Disconnected from %s", self.interface)

    async def get_current_network(self) -> dict[str, str]:
        """Get current connection info via wpa_cli status."""
        output = await self._run_wpa_cli("status")
        status = {}
        for line in output.strip().splitlines():
            if "=" in line:
                key, _, value = line.partition("=")
                status[key.strip()] = value.strip()
        return status

    async def is_connected(self) -> bool:
        """Check if currently connected to any network."""
        status = await self.get_current_network()
        return status.get("wpa_state") == "COMPLETED"

    async def remove_all_networks(self) -> None:
        """Remove all configured networks."""
        await self._run_wpa_cli("remove_network", "all")
        await self._run_wpa_cli("save_config")
