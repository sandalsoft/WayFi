"""Integration tests for the orchestrator state machine."""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from wayfi.network.scanner import ScanResult, SecurityType
from wayfi.network.scorer import NetworkCandidate
from wayfi.network.speedtest import SpeedResult
from wayfi.orchestrator import Orchestrator, State
from wayfi.portal.detector import PortalResult
from wayfi.portal.heuristic import HeuristicMatch, SolveStrategy
from wayfi.portal.submitter import SubmitResult


@pytest.fixture
def orchestrator(tmp_dir):
    """Orchestrator with mocked dependencies."""
    config_path = tmp_dir / "wayfi.yaml"
    config_path.write_text("network:\n  scan_interval: 1\n  dhcp_timeout: 1\n")
    orch = Orchestrator.__new__(Orchestrator)
    orch.config = {"network": {"scan_interval": 1, "dhcp_timeout": 1, "max_retries": 3}}
    orch.os = Orchestrator.__new__(Orchestrator).__class__.__mro__[0]
    # Re-init properly
    from wayfi.orchestrator import OrchestratorState
    orch.os = OrchestratorState()
    orch._running = True
    orch._room_number_event = asyncio.Event()
    orch._room_number_reply = None

    # Mock all modules
    orch.scanner = AsyncMock()
    orch.connector = AsyncMock()
    orch.detector = AsyncMock()
    orch.heuristic = MagicMock()
    orch.llm_solver = AsyncMock()
    orch.cloud_solver = AsyncMock()
    orch.submitter = AsyncMock()
    orch.speedtester = AsyncMock()
    orch.scorer = MagicMock()
    orch.selector = MagicMock()
    orch.notifier = AsyncMock()
    orch.vpn = AsyncMock()
    orch.vpn.is_active = False
    orch.calendar = None
    orch.ap = AsyncMock()
    orch.vault = None

    return orch


def _make_scan_result(ssid="TestWiFi", signal=-50):
    return ScanResult(
        bssid="aa:bb:cc:dd:ee:ff",
        frequency=2437,
        signal=signal,
        ssid=ssid,
        security=SecurityType.OPEN,
    )


class TestStateTransitions:
    async def test_boot_to_scan(self, orchestrator):
        orchestrator.os.state = State.BOOT
        await orchestrator._step()
        assert orchestrator.os.state == State.SCAN

    async def test_scan_finds_networks(self, orchestrator):
        orchestrator.os.state = State.SCAN
        orchestrator.scanner.scan.return_value = [_make_scan_result()]
        await orchestrator._step()
        assert orchestrator.os.state == State.SELECT

    async def test_scan_no_networks_retries(self, orchestrator):
        orchestrator.os.state = State.SCAN
        orchestrator.scanner.scan.return_value = []
        await orchestrator._step()
        assert orchestrator.os.state == State.SCAN

    async def test_select_ranks_and_moves_to_connect(self, orchestrator):
        orchestrator.os.state = State.SELECT
        scan = _make_scan_result()
        orchestrator.os.scan_results = [scan]
        orchestrator.selector.rank.return_value = [
            NetworkCandidate(scan_result=scan, selection_score=100)
        ]
        await orchestrator._step()
        assert orchestrator.os.state == State.CONNECT

    async def test_connect_success_goes_to_detect(self, orchestrator):
        orchestrator.os.state = State.CONNECT
        scan = _make_scan_result()
        orchestrator.os.candidates = [NetworkCandidate(scan_result=scan)]
        orchestrator.os.candidate_index = 0
        from wayfi.network.connector import ConnectionResult
        orchestrator.connector.connect_to_network.return_value = ConnectionResult(
            success=True, ssid="TestWiFi", bssid="aa:bb:cc:dd:ee:ff", ip_address="192.168.1.100"
        )
        await orchestrator._step()
        assert orchestrator.os.state == State.DETECT_PORTAL
        assert orchestrator.os.current_ssid == "TestWiFi"

    async def test_detect_no_portal_goes_to_post_auth(self, orchestrator):
        orchestrator.os.state = State.DETECT_PORTAL
        orchestrator.detector.detect.return_value = PortalResult(is_captive=False)
        await orchestrator._step()
        assert orchestrator.os.state == State.POST_AUTH

    async def test_detect_portal_goes_to_solve(self, orchestrator):
        orchestrator.os.state = State.DETECT_PORTAL
        orchestrator.detector.detect.return_value = PortalResult(
            is_captive=True, redirect_url="http://portal.example.com", portal_html="<form></form>"
        )
        await orchestrator._step()
        assert orchestrator.os.state == State.SOLVE_PORTAL


class TestPostAuth:
    async def test_post_auth_runs_speedtest_and_notifies(self, orchestrator):
        orchestrator.os.state = State.POST_AUTH
        orchestrator.os.boot_time = 1000.0
        orchestrator.os.current_ssid = "TestWiFi"

        orchestrator.speedtester.run.return_value = SpeedResult(
            download_mbps=50, upload_mbps=10, latency_ms=20, jitter_ms=5, dns_ms=15
        )
        from wayfi.network.scorer import QualityScore
        orchestrator.scorer.score.return_value = QualityScore(
            overall=8.0, download_score=8, upload_score=7,
            latency_score=8, jitter_score=7, dns_score=8,
        )
        orchestrator.vpn.activate_vpn = AsyncMock()
        orchestrator.vpn.is_active = True

        await orchestrator._step()

        assert orchestrator.os.state == State.MONITOR
        assert orchestrator.os.quality_score == 8.0
        orchestrator.notifier.send_connection_success.assert_called_once()


class TestVerify:
    async def test_verify_success(self, orchestrator):
        orchestrator.os.state = State.VERIFY
        orchestrator.detector.verify_connectivity.return_value = True
        await orchestrator._step()
        assert orchestrator.os.state == State.POST_AUTH

    async def test_verify_failure_tries_next_network(self, orchestrator):
        orchestrator.os.state = State.VERIFY
        orchestrator.detector.verify_connectivity.return_value = False
        orchestrator.os.candidate_index = 0
        await orchestrator._step()
        assert orchestrator.os.state == State.CONNECT
        assert orchestrator.os.candidate_index == 1
