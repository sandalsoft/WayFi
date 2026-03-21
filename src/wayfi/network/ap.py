"""Access Point management via hostapd and dnsmasq."""

from __future__ import annotations

import asyncio
import logging
import textwrap
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class APConfig:
    ssid: str = "WayFi-Travel"
    password: str = "changeme"
    channel: int = 6
    interface: str = "wlan1"
    upstream_interface: str = "wlan0"
    subnet: str = "192.168.8.0/24"
    gateway: str = "192.168.8.1"
    dhcp_start: str = "192.168.8.10"
    dhcp_end: str = "192.168.8.250"
    hw_mode: str = "a"
    country_code: str = "US"


class APManager:
    """Manages hostapd, dnsmasq, and iptables NAT for the access point."""

    def __init__(
        self,
        config: APConfig | None = None,
        hostapd_conf: Path = Path("/etc/hostapd/hostapd.conf"),
        dnsmasq_conf: Path = Path("/etc/dnsmasq.d/wayfi.conf"),
    ) -> None:
        self.config = config or APConfig()
        self.hostapd_conf = hostapd_conf
        self.dnsmasq_conf = dnsmasq_conf

    def generate_hostapd_conf(self) -> str:
        """Generate hostapd configuration for WPA2-PSK 802.11ac AP."""
        c = self.config
        return textwrap.dedent(f"""\
            # WayFi hostapd configuration
            interface={c.interface}
            driver=nl80211
            ssid={c.ssid}
            hw_mode={c.hw_mode}
            channel={c.channel}
            country_code={c.country_code}
            ieee80211n=1
            ieee80211ac=1
            wmm_enabled=1

            # WPA2-PSK
            auth_algs=1
            wpa=2
            wpa_passphrase={c.password}
            wpa_key_mgmt=WPA-PSK
            rsn_pairwise=CCMP

            # Performance
            ht_capab=[HT40+][SHORT-GI-20][SHORT-GI-40]
            vht_oper_chwidth=1
            max_num_sta=32
        """)

    def generate_dnsmasq_conf(self) -> str:
        """Generate dnsmasq configuration for DHCP and DNS forwarding."""
        c = self.config
        return textwrap.dedent(f"""\
            # WayFi dnsmasq configuration
            interface={c.interface}
            bind-interfaces
            dhcp-range={c.dhcp_start},{c.dhcp_end},255.255.255.0,24h
            dhcp-option=option:router,{c.gateway}
            dhcp-option=option:dns-server,{c.gateway}

            # DNS forwarding
            server=1.1.1.1
            server=8.8.8.8

            # Performance
            cache-size=1000
            no-resolv
            bogus-priv
            domain-needed
        """)

    async def generate_configs(self) -> None:
        """Write hostapd and dnsmasq config files."""
        self.hostapd_conf.parent.mkdir(parents=True, exist_ok=True)
        self.dnsmasq_conf.parent.mkdir(parents=True, exist_ok=True)

        self.hostapd_conf.write_text(self.generate_hostapd_conf())
        self.dnsmasq_conf.write_text(self.generate_dnsmasq_conf())
        logger.info("Generated AP configs: %s, %s", self.hostapd_conf, self.dnsmasq_conf)

    async def _run(self, *args: str, check: bool = True) -> tuple[str, int]:
        proc = await asyncio.create_subprocess_exec(
            *args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()
        output = stdout.decode() + stderr.decode()
        if check and proc.returncode != 0:
            logger.error("Command failed: %s -> %s", args, output.strip())
        return output, proc.returncode

    async def setup_interface(self) -> None:
        """Configure the AP interface with a static IP."""
        c = self.config
        await self._run("ip", "addr", "flush", "dev", c.interface)
        await self._run(
            "ip", "addr", "add", f"{c.gateway}/24", "dev", c.interface
        )
        await self._run("ip", "link", "set", c.interface, "up")
        logger.info("AP interface %s configured with %s", c.interface, c.gateway)

    async def setup_nat(self) -> None:
        """Configure iptables NAT masquerade from AP to upstream."""
        c = self.config
        # Enable IP forwarding
        await self._run("sysctl", "-w", "net.ipv4.ip_forward=1")
        # NAT masquerade
        await self._run(
            "iptables", "-t", "nat", "-A", "POSTROUTING",
            "-o", c.upstream_interface, "-j", "MASQUERADE",
        )
        await self._run(
            "iptables", "-A", "FORWARD",
            "-i", c.interface, "-o", c.upstream_interface,
            "-j", "ACCEPT",
        )
        await self._run(
            "iptables", "-A", "FORWARD",
            "-i", c.upstream_interface, "-o", c.interface,
            "-m", "state", "--state", "RELATED,ESTABLISHED",
            "-j", "ACCEPT",
        )
        logger.info("NAT configured: %s -> %s", c.interface, c.upstream_interface)

    async def start_ap(self) -> None:
        """Start the access point (hostapd + dnsmasq + NAT)."""
        await self.generate_configs()
        await self.setup_interface()
        await self.setup_nat()
        await self._run("systemctl", "start", "hostapd")
        await self._run("systemctl", "start", "dnsmasq")
        logger.info("Access point started: SSID=%s", self.config.ssid)

    async def stop_ap(self) -> None:
        """Stop the access point."""
        await self._run("systemctl", "stop", "hostapd", check=False)
        await self._run("systemctl", "stop", "dnsmasq", check=False)
        logger.info("Access point stopped")

    async def restart_ap(self) -> None:
        """Restart the access point."""
        await self.stop_ap()
        await asyncio.sleep(1)
        await self.start_ap()

    async def get_connected_clients(self) -> list[str]:
        """List MAC addresses of connected clients."""
        output, _ = await self._run(
            "iw", "dev", self.config.interface, "station", "dump",
            check=False,
        )
        clients = []
        for line in output.splitlines():
            if line.startswith("Station"):
                mac = line.split()[1]
                clients.append(mac)
        return clients
