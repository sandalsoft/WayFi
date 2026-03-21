"""Main orchestrator state machine — the WayFi control loop."""

from __future__ import annotations

import asyncio
import enum
import logging
import time
from dataclasses import dataclass, field
from pathlib import Path

import yaml

from wayfi.calendar.sync import CalendarSync
from wayfi.network.ap import APConfig, APManager
from wayfi.network.connector import ConnectionResult, WiFiConnector
from wayfi.network.scanner import ScanResult, WiFiScanner
from wayfi.network.scorer import NetworkCandidate, NetworkScorer, NetworkSelector, QualityScore
from wayfi.network.speedtest import SpeedTester
from wayfi.notify.sms import RoomNumberReply, SMSConfig, TwilioNotifier
from wayfi.portal.cloud_solver import CloudConfig, CloudSolver
from wayfi.portal.detector import PortalDetector, PortalResult
from wayfi.portal.heuristic import HeuristicEngine
from wayfi.portal.llm_solver import LLMSolver
from wayfi.portal.submitter import PortalSubmitter, SubmitRequest
from wayfi.vault.vault import Vault
from wayfi.vpn.manager import VPNManager

logger = logging.getLogger(__name__)


class State(enum.Enum):
    BOOT = "boot"
    SCAN = "scan"
    SELECT = "select"
    CONNECT = "connect"
    DETECT_PORTAL = "detect_portal"
    SOLVE_PORTAL = "solve_portal"
    VERIFY = "verify"
    POST_AUTH = "post_auth"
    MONITOR = "monitor"


@dataclass
class OrchestratorState:
    state: State = State.BOOT
    current_ssid: str = ""
    current_bssid: str = ""
    ip_address: str = ""
    quality_score: float = 0.0
    vpn_active: bool = False
    boot_time: float = 0.0
    connected_at: float = 0.0
    portal_solved: bool = False
    retries: int = 0
    scan_results: list[ScanResult] = field(default_factory=list)
    candidates: list[NetworkCandidate] = field(default_factory=list)
    candidate_index: int = 0


class Orchestrator:
    """9-state control loop wiring all WayFi modules.

    BOOT -> SCAN -> SELECT -> CONNECT -> DETECT_PORTAL -> SOLVE_PORTAL ->
    VERIFY -> POST_AUTH -> MONITOR (loops back to SCAN on disconnect)
    """

    def __init__(self, config_path: Path = Path("config/wayfi.yaml")) -> None:
        self.config = self._load_config(config_path)
        self.os = OrchestratorState()

        # Module instances (initialized in boot)
        self.vault: Vault | None = None
        self.scanner: WiFiScanner | None = None
        self.connector: WiFiConnector | None = None
        self.detector: PortalDetector | None = None
        self.heuristic: HeuristicEngine | None = None
        self.llm_solver: LLMSolver | None = None
        self.cloud_solver: CloudSolver | None = None
        self.submitter: PortalSubmitter | None = None
        self.speedtester: SpeedTester | None = None
        self.scorer: NetworkScorer | None = None
        self.selector: NetworkSelector | None = None
        self.notifier: TwilioNotifier | None = None
        self.vpn: VPNManager | None = None
        self.calendar: CalendarSync | None = None
        self.ap: APManager | None = None

        self._running = False
        self._room_number_event = asyncio.Event()
        self._room_number_reply: RoomNumberReply | None = None

    def _load_config(self, path: Path) -> dict:
        if path.exists():
            return yaml.safe_load(path.read_text()) or {}
        logger.warning("Config not found at %s, using defaults", path)
        return {}

    async def boot(self) -> None:
        """BOOT state: initialize all modules, load patterns, start AP."""
        self.os.state = State.BOOT
        self.os.boot_time = time.time()
        logger.info("BOOT: initializing WayFi")

        net_cfg = self.config.get("network", {})
        portal_cfg = self.config.get("portal", {})
        ap_cfg = self.config.get("ap", {})
        llm_cfg = self.config.get("llm", {})
        speed_cfg = self.config.get("speedtest", {})

        # Core modules
        upstream_iface = self.config.get("upstream", {}).get("interface", "wlan0")
        self.scanner = WiFiScanner(interface=upstream_iface)
        self.connector = WiFiConnector(
            interface=upstream_iface,
            dhcp_timeout=net_cfg.get("dhcp_timeout", 5),
        )
        self.detector = PortalDetector(
            probe_url=portal_cfg.get("probe_url", "http://connectivitycheck.gstatic.com/generate_204"),
            timeout=portal_cfg.get("probe_timeout", 2.0),
        )

        # Portal solving
        self.heuristic = HeuristicEngine()
        self.heuristic.load_patterns()
        self.llm_solver = LLMSolver(
            endpoint=llm_cfg.get("endpoint", "http://localhost:8080"),
            model=llm_cfg.get("model", "llama-3.1-8b"),
            timeout=llm_cfg.get("timeout", 30),
        )
        self.cloud_solver = CloudSolver()
        self.submitter = PortalSubmitter()

        # Quality
        self.speedtester = SpeedTester(
            download_url=speed_cfg.get("download_url", "https://speed.cloudflare.com/__down?bytes=10000000"),
            ping_targets=speed_cfg.get("ping_targets", ["1.1.1.1", "8.8.8.8"]),
        )
        self.scorer = NetworkScorer()
        self.selector = NetworkSelector()

        # VPN
        self.vpn = VPNManager()

        # AP
        self.ap = APManager(config=APConfig(
            ssid=ap_cfg.get("ssid", "WayFi-Travel"),
            password=ap_cfg.get("password", "changeme"),
            channel=ap_cfg.get("channel", 6),
            interface=ap_cfg.get("interface", "wlan1"),
            upstream_interface=upstream_iface,
        ))

        # Calendar (start sync in background)
        self.calendar = CalendarSync(
            sync_interval=self.config.get("calendar", {}).get("sync_interval", 1800),
            lookahead_days=self.config.get("calendar", {}).get("lookahead_days", 7),
        )

        boot_elapsed = time.time() - self.os.boot_time
        logger.info("BOOT complete in %.1fs", boot_elapsed)

    async def run(self) -> None:
        """Main orchestrator loop."""
        self._running = True
        await self.boot()

        while self._running:
            try:
                await self._step()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Orchestrator error in state %s: %s", self.os.state.value, e)
                await asyncio.sleep(5)

    async def stop(self) -> None:
        self._running = False
        if self.calendar:
            await self.calendar.stop()

    async def _step(self) -> None:
        """Execute one state transition."""
        state = self.os.state

        if state == State.BOOT:
            self.os.state = State.SCAN

        elif state == State.SCAN:
            await self._scan()

        elif state == State.SELECT:
            await self._select()

        elif state == State.CONNECT:
            await self._connect()

        elif state == State.DETECT_PORTAL:
            await self._detect_portal()

        elif state == State.SOLVE_PORTAL:
            await self._solve_portal()

        elif state == State.VERIFY:
            await self._verify()

        elif state == State.POST_AUTH:
            await self._post_auth()

        elif state == State.MONITOR:
            await self._monitor()

    async def _scan(self) -> None:
        logger.info("SCAN: scanning for networks")
        self.os.scan_results = await self.scanner.scan()
        if not self.os.scan_results:
            logger.warning("No networks found, retrying in 5s")
            await asyncio.sleep(5)
            return
        self.os.state = State.SELECT

    async def _select(self) -> None:
        logger.info("SELECT: ranking %d networks", len(self.os.scan_results))
        # Update selector with calendar hints
        if self.calendar:
            self.selector = NetworkSelector(
                calendar_ssid_hints=self.calendar.get_ssid_hints(),
            )
        self.os.candidates = self.selector.rank(self.os.scan_results)
        if not self.os.candidates:
            logger.warning("No viable candidates, rescanning")
            self.os.state = State.SCAN
            await asyncio.sleep(3)
            return
        self.os.candidate_index = 0
        self.os.state = State.CONNECT

    async def _connect(self) -> None:
        if self.os.candidate_index >= len(self.os.candidates):
            logger.warning("Exhausted all candidates, rescanning")
            self.os.state = State.SCAN
            await asyncio.sleep(5)
            return

        candidate = self.os.candidates[self.os.candidate_index]
        ssid = candidate.scan_result.ssid
        logger.info("CONNECT: trying %s (score=%.0f)", ssid, candidate.selection_score)

        result = await self.connector.connect_to_network(
            ssid=ssid, bssid=candidate.scan_result.bssid
        )

        if not result.success:
            logger.warning("Failed to connect to %s: %s", ssid, result.error)
            self.os.candidate_index += 1
            return

        self.os.current_ssid = ssid
        self.os.current_bssid = result.bssid
        self.os.ip_address = result.ip_address
        self.os.connected_at = time.time()
        self.os.state = State.DETECT_PORTAL

    async def _detect_portal(self) -> None:
        logger.info("DETECT_PORTAL: probing connectivity")
        result = await self.detector.detect()

        if not result.is_captive:
            logger.info("No captive portal detected — connected directly")
            self.os.portal_solved = True
            self.os.state = State.POST_AUTH
            return

        logger.info("Captive portal detected: %s", result.redirect_url or "injected")
        self.os.portal_solved = False
        self.os.state = State.SOLVE_PORTAL
        # Stash portal info for solve step
        self._portal_result = result

    async def _solve_portal(self) -> None:
        portal = self._portal_result
        logger.info("SOLVE_PORTAL: attempting to solve portal")

        # Get vault values for field interpolation
        vault_values = self._get_vault_values()

        # Run heuristic and LLM in parallel (first wins)
        heuristic_task = asyncio.create_task(
            self._try_heuristic(portal, vault_values)
        )
        llm_task = asyncio.create_task(
            self._try_llm(portal)
        )

        done, pending = await asyncio.wait(
            [heuristic_task, llm_task],
            return_when=asyncio.FIRST_COMPLETED,
            timeout=35,
        )

        success = False
        for task in done:
            result = task.result()
            if result:
                success = True
                break

        # Cancel remaining tasks
        for task in pending:
            task.cancel()

        if not success:
            # Try cloud fallback
            logger.info("Local solvers failed, trying cloud API")
            success = await self._try_cloud(portal, vault_values)

        if success:
            self.os.portal_solved = True
            self.os.state = State.VERIFY
        else:
            logger.warning("All portal solvers failed")
            if self.notifier:
                await self.notifier.send_portal_failure(
                    self.os.current_ssid, "All solvers failed"
                )
            # Try next network
            self.os.candidate_index += 1
            self.os.state = State.CONNECT

    async def _try_heuristic(self, portal: PortalResult, vault_values: dict) -> bool:
        match = self.heuristic.match(
            portal.portal_html, portal.redirect_url, vault_values
        )
        if not match:
            return False

        # Check if we need room number
        fields = match.strategy.fields
        needs_room = any("{vault.room_number}" in v for v in fields.values())
        if needs_room and not vault_values.get("room_number"):
            room = await self._request_room_number(match.strategy.vendor)
            if room:
                vault_values["room_number"] = room

        # Re-interpolate with room number
        match = self.heuristic.match(
            portal.portal_html, portal.redirect_url, vault_values
        )
        if not match:
            return False

        request = SubmitRequest(
            portal_url=portal.redirect_url,
            action_url=match.strategy.action_url_pattern,
            method=match.strategy.method,
            fields=match.strategy.fields,
            checkboxes=match.strategy.checkboxes,
        )
        result = await self.submitter.submit(request, portal.portal_html)
        return result.success

    async def _try_llm(self, portal: PortalResult) -> bool:
        solve_result = await self.llm_solver.solve(
            portal.portal_html, portal.redirect_url
        )
        if not solve_result.success or not solve_result.fields:
            return False

        request = SubmitRequest(
            portal_url=portal.redirect_url,
            action_url=solve_result.action_url,
            method=solve_result.method,
            fields=solve_result.fields,
            checkboxes=solve_result.checkboxes or [],
        )
        result = await self.submitter.submit(request, portal.portal_html)
        return result.success

    async def _try_cloud(self, portal: PortalResult, vault_values: dict) -> bool:
        solve_result = await self.cloud_solver.solve(
            portal.portal_html, portal.redirect_url
        )
        if not solve_result.success or not solve_result.fields:
            return False

        request = SubmitRequest(
            portal_url=portal.redirect_url,
            action_url=solve_result.action_url,
            method=solve_result.method,
            fields=solve_result.fields,
            checkboxes=solve_result.checkboxes or [],
        )
        result = await self.submitter.submit(request, portal.portal_html)
        return result.success

    async def _request_room_number(self, hotel_name: str) -> str | None:
        """Request room number via SMS and wait for reply."""
        if not self.notifier:
            return None

        self._room_number_event.clear()
        await self.notifier.send_room_number_request(hotel_name)

        # Wait up to 5 minutes with 2-minute reminder
        try:
            await asyncio.wait_for(self._room_number_event.wait(), timeout=120)
        except asyncio.TimeoutError:
            await self.notifier.send_room_number_request(hotel_name)
            try:
                await asyncio.wait_for(self._room_number_event.wait(), timeout=180)
            except asyncio.TimeoutError:
                return None

        if self._room_number_reply:
            room = self._room_number_reply.room_number
            if self.vault and self.vault.is_unlocked():
                self.vault.set_room_number(room, self._room_number_reply.nights)
            return room
        return None

    async def _on_room_reply(self, reply: RoomNumberReply) -> None:
        """Callback from SMS notifier when room number is received."""
        self._room_number_reply = reply
        self._room_number_event.set()

    async def _verify(self) -> None:
        logger.info("VERIFY: checking connectivity after portal solve")
        for attempt in range(3):
            connected = await self.detector.verify_connectivity()
            if connected:
                logger.info("VERIFY: connectivity confirmed")
                self.os.state = State.POST_AUTH
                return
            logger.warning("VERIFY: attempt %d failed", attempt + 1)
            await asyncio.sleep(2)

        logger.warning("VERIFY: failed after 3 attempts, trying next network")
        self.os.candidate_index += 1
        self.os.state = State.CONNECT

    async def _post_auth(self) -> None:
        logger.info("POST_AUTH: running speedtest + VPN activation")

        # Run speedtest and VPN in parallel
        speed_task = asyncio.create_task(self.speedtester.run())
        vpn_task = asyncio.create_task(self._activate_vpn())

        speed_result = await speed_task
        await vpn_task

        quality = self.scorer.score(speed_result)
        self.os.quality_score = quality.overall
        self.os.vpn_active = self.vpn.is_active if self.vpn else False

        # Send SMS notification
        if self.notifier:
            await self.notifier.send_connection_success(
                self.os.current_ssid, quality.overall, self.os.vpn_active
            )

        elapsed = time.time() - self.os.boot_time
        logger.info(
            "POST_AUTH complete: %s, quality=%.1f/10, VPN=%s (%.1fs from boot)",
            self.os.current_ssid,
            quality.overall,
            self.os.vpn_active,
            elapsed,
        )
        self.os.state = State.MONITOR

    async def _activate_vpn(self) -> None:
        if not self.vpn:
            return
        try:
            await self.vpn.activate_vpn(self.os.current_ssid)
        except Exception as e:
            logger.warning("VPN activation failed: %s", e)

    async def _monitor(self) -> None:
        interval = self.config.get("network", {}).get("scan_interval", 15)
        await asyncio.sleep(interval)

        connected = await self.detector.verify_connectivity()
        if connected:
            return

        logger.warning("MONITOR: connectivity lost on %s", self.os.current_ssid)
        if self.notifier:
            await self.notifier.send_connection_lost(self.os.current_ssid)

        self.os.retries += 1
        max_retries = self.config.get("network", {}).get("max_retries", 3)
        if self.os.retries <= max_retries:
            self.os.state = State.DETECT_PORTAL
        else:
            self.os.retries = 0
            self.os.state = State.SCAN

    def _get_vault_values(self) -> dict[str, str]:
        """Extract credential values from vault for portal field interpolation."""
        if not self.vault or not self.vault.is_unlocked():
            return {}
        values = {}
        for cred in self.vault.get_all():
            values[cred.name] = cred.value
        # Also check room number
        room = self.vault.get_room_number()
        if room:
            values["room_number"] = room
        return values
