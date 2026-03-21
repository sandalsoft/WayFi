"""VPN per-network policy engine supporting WireGuard and OpenVPN."""

from __future__ import annotations

import asyncio
import enum
import logging
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)


class VPNType(enum.Enum):
    WIREGUARD = "wireguard"
    OPENVPN = "openvpn"
    NONE = "none"


class VPNPolicy(enum.Enum):
    ALWAYS = "always"
    NEVER = "never"
    ASK = "ask"  # prompt via SMS


@dataclass
class VPNProfile:
    name: str
    vpn_type: VPNType
    config_path: Path
    policy: VPNPolicy = VPNPolicy.ALWAYS


@dataclass
class VPNStatus:
    active: bool
    vpn_type: VPNType = VPNType.NONE
    interface: str = ""
    profile_name: str = ""
    error: str = ""


class VPNManager:
    """Manage VPN connections with per-network policies."""

    def __init__(
        self,
        wireguard_dir: Path = Path("/etc/wireguard"),
        openvpn_dir: Path = Path("/etc/openvpn/client"),
        default_policy: str = "always",
        network_policies: dict[str, str] | None = None,
    ) -> None:
        self.wireguard_dir = wireguard_dir
        self.openvpn_dir = openvpn_dir
        self.default_policy = VPNPolicy(default_policy)
        self.network_policies = network_policies or {}
        self._status = VPNStatus(active=False)

    @property
    def is_active(self) -> bool:
        return self._status.active

    def get_status(self) -> VPNStatus:
        return self._status

    def get_policy(self, ssid: str) -> VPNPolicy:
        """Get VPN policy for a specific network SSID."""
        policy_str = self.network_policies.get(ssid)
        if policy_str:
            return VPNPolicy(policy_str)
        return self.default_policy

    def list_profiles(self) -> list[VPNProfile]:
        """List available VPN profiles from config directories."""
        profiles = []

        # WireGuard configs
        if self.wireguard_dir.exists():
            for conf in self.wireguard_dir.glob("*.conf"):
                profiles.append(VPNProfile(
                    name=conf.stem,
                    vpn_type=VPNType.WIREGUARD,
                    config_path=conf,
                ))

        # OpenVPN configs
        if self.openvpn_dir.exists():
            for conf in self.openvpn_dir.glob("*.conf"):
                profiles.append(VPNProfile(
                    name=conf.stem,
                    vpn_type=VPNType.OPENVPN,
                    config_path=conf,
                ))
            for conf in self.openvpn_dir.glob("*.ovpn"):
                profiles.append(VPNProfile(
                    name=conf.stem,
                    vpn_type=VPNType.OPENVPN,
                    config_path=conf,
                ))

        return profiles

    async def activate_vpn(self, ssid: str = "", profile_name: str = "") -> VPNStatus:
        """Activate VPN based on network policy and available profiles."""
        policy = self.get_policy(ssid) if ssid else self.default_policy

        if policy == VPNPolicy.NEVER:
            logger.info("VPN policy is NEVER for %s, skipping", ssid)
            return self._status

        if policy == VPNPolicy.ASK:
            logger.info("VPN policy is ASK for %s — requires SMS confirmation", ssid)
            return self._status

        profiles = self.list_profiles()
        if not profiles:
            logger.warning("No VPN profiles found")
            self._status = VPNStatus(active=False, error="No VPN profiles configured")
            return self._status

        # Use specified profile or first available
        profile = profiles[0]
        if profile_name:
            matching = [p for p in profiles if p.name == profile_name]
            if matching:
                profile = matching[0]

        if profile.vpn_type == VPNType.WIREGUARD:
            return await self._activate_wireguard(profile)
        return await self._activate_openvpn(profile)

    async def _activate_wireguard(self, profile: VPNProfile) -> VPNStatus:
        """Activate WireGuard VPN."""
        logger.info("Activating WireGuard: %s", profile.name)
        proc = await asyncio.create_subprocess_exec(
            "wg-quick", "up", profile.name,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()

        if proc.returncode == 0:
            self._status = VPNStatus(
                active=True,
                vpn_type=VPNType.WIREGUARD,
                interface=profile.name,
                profile_name=profile.name,
            )
            logger.info("WireGuard %s activated", profile.name)
        else:
            err = stderr.decode("utf-8", errors="replace").strip()
            self._status = VPNStatus(
                active=False,
                vpn_type=VPNType.WIREGUARD,
                error=err,
            )
            logger.error("WireGuard activation failed: %s", err)

        return self._status

    async def _activate_openvpn(self, profile: VPNProfile) -> VPNStatus:
        """Activate OpenVPN."""
        logger.info("Activating OpenVPN: %s", profile.name)
        proc = await asyncio.create_subprocess_exec(
            "openvpn", "--config", str(profile.config_path), "--daemon",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()

        if proc.returncode == 0:
            self._status = VPNStatus(
                active=True,
                vpn_type=VPNType.OPENVPN,
                interface="tun0",
                profile_name=profile.name,
            )
            logger.info("OpenVPN %s activated", profile.name)
        else:
            err = stderr.decode("utf-8", errors="replace").strip()
            self._status = VPNStatus(
                active=False,
                vpn_type=VPNType.OPENVPN,
                error=err,
            )
            logger.error("OpenVPN activation failed: %s", err)

        return self._status

    async def deactivate_vpn(self) -> None:
        """Deactivate current VPN connection."""
        if not self._status.active:
            return

        if self._status.vpn_type == VPNType.WIREGUARD:
            await asyncio.create_subprocess_exec(
                "wg-quick", "down", self._status.profile_name,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
        elif self._status.vpn_type == VPNType.OPENVPN:
            await asyncio.create_subprocess_exec(
                "killall", "openvpn",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

        logger.info("VPN deactivated: %s", self._status.profile_name)
        self._status = VPNStatus(active=False)
