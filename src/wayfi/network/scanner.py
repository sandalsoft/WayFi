"""WiFi scanning via wpa_supplicant/iw with async event-driven interface."""

from __future__ import annotations

import asyncio
import logging
import re
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class SecurityType(Enum):
    OPEN = "open"
    WEP = "wep"
    WPA = "wpa"
    WPA2 = "wpa2"
    WPA3 = "wpa3"
    ENTERPRISE = "enterprise"


@dataclass
class ScanResult:
    bssid: str
    frequency: int
    signal: int  # dBm
    ssid: str
    security: SecurityType
    flags: str = ""

    @property
    def signal_quality(self) -> int:
        """Convert dBm to 0-100 quality percentage."""
        if self.signal >= -50:
            return 100
        if self.signal <= -100:
            return 0
        return 2 * (self.signal + 100)

    @property
    def is_5ghz(self) -> bool:
        return self.frequency > 4900


def _parse_security(flags: str) -> SecurityType:
    """Parse wpa_cli flags string into SecurityType."""
    upper = flags.upper()
    if "WPA3" in upper or "SAE" in upper:
        return SecurityType.WPA3
    if "EAP" in upper or "802.1X" in upper:
        return SecurityType.ENTERPRISE
    if "WPA2" in upper or "RSN" in upper:
        return SecurityType.WPA2
    if "WPA" in upper:
        return SecurityType.WPA
    if "WEP" in upper:
        return SecurityType.WEP
    return SecurityType.OPEN


def parse_scan_results(output: str) -> list[ScanResult]:
    """Parse wpa_cli scan_results output into ScanResult objects.

    Format: bssid / frequency / signal level / flags / ssid
    """
    results = []
    for line in output.strip().splitlines():
        # Skip header line
        if line.startswith("bssid") or not line.strip():
            continue
        parts = line.split("\t")
        if len(parts) < 5:
            continue
        bssid, freq, signal, flags, ssid = (
            parts[0],
            parts[1],
            parts[2],
            parts[3],
            "\t".join(parts[4:]),  # SSID may contain tabs
        )
        try:
            results.append(
                ScanResult(
                    bssid=bssid.strip(),
                    frequency=int(freq),
                    signal=int(signal),
                    ssid=ssid.strip(),
                    security=_parse_security(flags),
                    flags=flags.strip(),
                )
            )
        except (ValueError, IndexError) as e:
            logger.warning("Failed to parse scan line: %s (%s)", line, e)
    return results


class WiFiScanner:
    """Async WiFi scanner wrapping wpa_cli."""

    def __init__(self, interface: str = "wlan0") -> None:
        self.interface = interface
        self._lock = asyncio.Lock()

    async def _run_wpa_cli(self, *args: str) -> str:
        """Run a wpa_cli command and return stdout."""
        cmd = ["wpa_cli", "-i", self.interface] + list(args)
        async with self._lock:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await proc.communicate()
        output = stdout.decode("utf-8", errors="replace")
        if proc.returncode != 0:
            err = stderr.decode("utf-8", errors="replace")
            logger.error("wpa_cli %s failed: %s", args, err)
        return output

    async def scan(self) -> list[ScanResult]:
        """Trigger a scan and return results."""
        trigger = await self._run_wpa_cli("scan")
        if "OK" not in trigger:
            logger.warning("Scan trigger did not return OK: %s", trigger.strip())
        # Wait for scan to complete
        await asyncio.sleep(3)
        output = await self._run_wpa_cli("scan_results")
        results = parse_scan_results(output)
        logger.info("Scan found %d networks on %s", len(results), self.interface)
        return results

    async def get_status(self) -> dict[str, str]:
        """Get current connection status."""
        output = await self._run_wpa_cli("status")
        status = {}
        for line in output.strip().splitlines():
            if "=" in line:
                key, _, value = line.partition("=")
                status[key.strip()] = value.strip()
        return status

    async def list_networks(self) -> str:
        """List configured networks."""
        return await self._run_wpa_cli("list_networks")

    async def monitor_events(self, callback: callable) -> None:
        """Monitor wpa_supplicant events. Calls callback(event_str) for each event.

        Events include CTRL-EVENT-CONNECTED, CTRL-EVENT-DISCONNECTED,
        CTRL-EVENT-SCAN-RESULTS, etc.
        """
        cmd = ["wpa_cli", "-i", self.interface]
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        try:
            while True:
                line = await proc.stdout.readline()
                if not line:
                    break
                decoded = line.decode("utf-8", errors="replace").strip()
                if decoded.startswith("<") or "CTRL-EVENT" in decoded:
                    await callback(decoded)
        except asyncio.CancelledError:
            proc.terminate()
            raise
