"""Multi-metric network speed and quality testing."""

from __future__ import annotations

import asyncio
import logging
import statistics
import time
from dataclasses import dataclass

import aiohttp

logger = logging.getLogger(__name__)


@dataclass
class SpeedResult:
    download_mbps: float
    upload_mbps: float
    latency_ms: float
    jitter_ms: float
    dns_ms: float
    timestamp: float = 0.0

    def __post_init__(self) -> None:
        if self.timestamp == 0.0:
            self.timestamp = time.time()


class SpeedTester:
    """Network quality testing with multi-metric probes."""

    def __init__(
        self,
        download_url: str = "https://speed.cloudflare.com/__down?bytes=10000000",
        upload_url: str = "https://speed.cloudflare.com/__up",
        ping_targets: list[str] | None = None,
        ping_samples: int = 10,
        dns_domains: list[str] | None = None,
    ) -> None:
        self.download_url = download_url
        self.upload_url = upload_url
        self.ping_targets = ping_targets or ["1.1.1.1", "8.8.8.8"]
        self.ping_samples = ping_samples
        self.dns_domains = dns_domains or [
            "google.com", "cloudflare.com", "amazon.com", "github.com", "apple.com"
        ]

    async def run(self) -> SpeedResult:
        """Run all speed tests in parallel and return combined results."""
        download_task = asyncio.create_task(self._test_download())
        upload_task = asyncio.create_task(self._test_upload())
        ping_task = asyncio.create_task(self._test_ping())
        dns_task = asyncio.create_task(self._test_dns())

        download_mbps = await download_task
        upload_mbps = await upload_task
        latency_ms, jitter_ms = await ping_task
        dns_ms = await dns_task

        result = SpeedResult(
            download_mbps=download_mbps,
            upload_mbps=upload_mbps,
            latency_ms=latency_ms,
            jitter_ms=jitter_ms,
            dns_ms=dns_ms,
        )
        logger.info(
            "Speed test: %.1f Mbps down, %.1f Mbps up, %.0fms latency, "
            "%.1fms jitter, %.0fms DNS",
            result.download_mbps,
            result.upload_mbps,
            result.latency_ms,
            result.jitter_ms,
            result.dns_ms,
        )
        return result

    async def _test_download(self) -> float:
        """Download test via HTTP GET. Returns Mbps."""
        timeout = aiohttp.ClientTimeout(total=15)
        try:
            async with aiohttp.ClientSession(timeout=timeout) as session:
                start = time.monotonic()
                async with session.get(self.download_url) as resp:
                    data = await resp.read()
                elapsed = time.monotonic() - start
                bits = len(data) * 8
                return (bits / elapsed) / 1_000_000
        except Exception as e:
            logger.warning("Download test failed: %s", e)
            return 0.0

    async def _test_upload(self) -> float:
        """Upload test via HTTP POST. Returns Mbps."""
        payload = b"0" * 1_000_000  # 1MB
        timeout = aiohttp.ClientTimeout(total=15)
        try:
            async with aiohttp.ClientSession(timeout=timeout) as session:
                start = time.monotonic()
                async with session.post(self.upload_url, data=payload) as resp:
                    await resp.read()
                elapsed = time.monotonic() - start
                bits = len(payload) * 8
                return (bits / elapsed) / 1_000_000
        except Exception as e:
            logger.warning("Upload test failed: %s", e)
            return 0.0

    async def _test_ping(self) -> tuple[float, float]:
        """ICMP ping test. Returns (avg_latency_ms, jitter_ms)."""
        all_times: list[float] = []
        for target in self.ping_targets:
            times = await self._ping_host(target, self.ping_samples)
            all_times.extend(times)

        if not all_times:
            return 999.0, 999.0

        avg = statistics.mean(all_times)
        jitter = statistics.stdev(all_times) if len(all_times) > 1 else 0.0
        return avg, jitter

    async def _ping_host(self, host: str, count: int) -> list[float]:
        """Ping a single host N times. Returns list of RTT in ms."""
        times: list[float] = []
        try:
            proc = await asyncio.create_subprocess_exec(
                "ping", "-c", str(count), "-W", "2", host,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=count * 3)
            output = stdout.decode("utf-8", errors="replace")
            for line in output.splitlines():
                if "time=" in line:
                    # Extract time=XX.X ms
                    parts = line.split("time=")
                    if len(parts) > 1:
                        ms_str = parts[1].split()[0]
                        times.append(float(ms_str))
        except (asyncio.TimeoutError, Exception) as e:
            logger.warning("Ping to %s failed: %s", host, e)
        return times

    async def _test_dns(self) -> float:
        """DNS resolution timing. Returns average resolution time in ms."""
        import socket

        loop = asyncio.get_event_loop()
        times: list[float] = []

        for domain in self.dns_domains:
            try:
                start = time.monotonic()
                await asyncio.wait_for(
                    loop.getaddrinfo(domain, 80), timeout=5
                )
                elapsed = (time.monotonic() - start) * 1000
                times.append(elapsed)
            except Exception as e:
                logger.warning("DNS resolve %s failed: %s", domain, e)

        if not times:
            return 999.0
        return statistics.mean(times)
