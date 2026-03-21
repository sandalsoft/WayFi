"""Network quality scoring with configurable weights and calendar intelligence."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

from wayfi.network.scanner import ScanResult, SecurityType
from wayfi.network.speedtest import SpeedResult

logger = logging.getLogger(__name__)

# Scoring bonuses for network selection
CALENDAR_MATCH_BONUS = 50
KNOWN_NETWORK_BONUS = 30
SIGNAL_WEIGHT = 1.0


@dataclass
class ScoreWeights:
    download: float = 0.4
    upload: float = 0.2
    latency: float = 0.2
    jitter: float = 0.1
    dns: float = 0.1


@dataclass
class QualityScore:
    overall: float  # 1-10 composite
    download_score: float
    upload_score: float
    latency_score: float
    jitter_score: float
    dns_score: float

    @property
    def grade(self) -> str:
        if self.overall >= 8:
            return "excellent"
        if self.overall >= 6:
            return "good"
        if self.overall >= 4:
            return "fair"
        if self.overall >= 2:
            return "poor"
        return "unusable"


def _scale(value: float, min_val: float, max_val: float) -> float:
    """Scale a value to 1-10 range. Higher = better."""
    if value <= min_val:
        return 1.0
    if value >= max_val:
        return 10.0
    return 1.0 + 9.0 * (value - min_val) / (max_val - min_val)


def _scale_inverse(value: float, best: float, worst: float) -> float:
    """Scale where lower value = better score (latency, jitter, DNS)."""
    if value <= best:
        return 10.0
    if value >= worst:
        return 1.0
    return 10.0 - 9.0 * (value - best) / (worst - best)


class NetworkScorer:
    """Compute composite network quality scores from speed test results."""

    def __init__(self, weights: ScoreWeights | None = None) -> None:
        self.weights = weights or ScoreWeights()

    def score(self, result: SpeedResult) -> QualityScore:
        """Score a speed test result on a 1-10 scale."""
        dl = _scale(result.download_mbps, 0.5, 100.0)
        ul = _scale(result.upload_mbps, 0.1, 50.0)
        lat = _scale_inverse(result.latency_ms, 10.0, 500.0)
        jit = _scale_inverse(result.jitter_ms, 1.0, 100.0)
        dns = _scale_inverse(result.dns_ms, 5.0, 500.0)

        overall = (
            dl * self.weights.download
            + ul * self.weights.upload
            + lat * self.weights.latency
            + jit * self.weights.jitter
            + dns * self.weights.dns
        )
        # Clamp to 1-10
        overall = max(1.0, min(10.0, overall))

        qs = QualityScore(
            overall=round(overall, 1),
            download_score=round(dl, 1),
            upload_score=round(ul, 1),
            latency_score=round(lat, 1),
            jitter_score=round(jit, 1),
            dns_score=round(dns, 1),
        )
        logger.info("Network score: %.1f/10 (%s)", qs.overall, qs.grade)
        return qs


@dataclass
class NetworkCandidate:
    scan_result: ScanResult
    selection_score: float = 0.0
    calendar_match: bool = False
    known_network: bool = False


class NetworkSelector:
    """Select the best network from scan results using signal strength,
    calendar intelligence, and known network bonuses."""

    def __init__(
        self,
        known_ssids: set[str] | None = None,
        calendar_ssid_hints: list[str] | None = None,
    ) -> None:
        self.known_ssids = known_ssids or set()
        self.calendar_hints = [h.lower() for h in (calendar_ssid_hints or [])]

    def rank(self, scan_results: list[ScanResult]) -> list[NetworkCandidate]:
        """Rank scan results by composite score. Higher = better."""
        candidates = []
        for result in scan_results:
            if not result.ssid:
                continue  # Skip hidden networks

            candidate = NetworkCandidate(scan_result=result)
            score = 0.0

            # Signal strength (0-100 mapped to 0-100 points)
            score += result.signal_quality * SIGNAL_WEIGHT

            # Calendar location match
            ssid_lower = result.ssid.lower()
            if any(hint in ssid_lower for hint in self.calendar_hints):
                score += CALENDAR_MATCH_BONUS
                candidate.calendar_match = True

            # Known network bonus
            if result.ssid in self.known_ssids:
                score += KNOWN_NETWORK_BONUS
                candidate.known_network = True

            # Prefer open networks (easier portal solve) over encrypted ones
            # for travel router use case
            if result.security == SecurityType.OPEN:
                score += 10

            # Prefer 5GHz for speed
            if result.is_5ghz:
                score += 5

            candidate.selection_score = score
            candidates.append(candidate)

        candidates.sort(key=lambda c: c.selection_score, reverse=True)

        if candidates:
            best = candidates[0]
            logger.info(
                "Best network: %s (score=%.0f, signal=%d%%, calendar=%s, known=%s)",
                best.scan_result.ssid,
                best.selection_score,
                best.scan_result.signal_quality,
                best.calendar_match,
                best.known_network,
            )

        return candidates
