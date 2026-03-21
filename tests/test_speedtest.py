"""Tests for speed test and network scoring."""

from __future__ import annotations

from wayfi.network.scorer import NetworkScorer, QualityScore, ScoreWeights
from wayfi.network.speedtest import SpeedResult


class TestNetworkScorer:
    def test_excellent_network(self):
        result = SpeedResult(
            download_mbps=80.0,
            upload_mbps=30.0,
            latency_ms=15.0,
            jitter_ms=2.0,
            dns_ms=10.0,
        )
        scorer = NetworkScorer()
        score = scorer.score(result)
        assert score.overall >= 8.0
        assert score.grade == "excellent"

    def test_poor_network(self):
        result = SpeedResult(
            download_mbps=1.0,
            upload_mbps=0.2,
            latency_ms=400.0,
            jitter_ms=80.0,
            dns_ms=300.0,
        )
        scorer = NetworkScorer()
        score = scorer.score(result)
        assert score.overall <= 3.0

    def test_custom_weights(self):
        result = SpeedResult(
            download_mbps=50.0,
            upload_mbps=1.0,
            latency_ms=100.0,
            jitter_ms=50.0,
            dns_ms=200.0,
        )
        # Weight download 100%
        weights = ScoreWeights(download=1.0, upload=0, latency=0, jitter=0, dns=0)
        scorer = NetworkScorer(weights=weights)
        score = scorer.score(result)
        # 50 Mbps download should score well
        assert score.overall >= 5.0

    def test_score_clamped_to_range(self):
        # Impossibly good
        result = SpeedResult(
            download_mbps=1000.0,
            upload_mbps=500.0,
            latency_ms=1.0,
            jitter_ms=0.1,
            dns_ms=1.0,
        )
        scorer = NetworkScorer()
        score = scorer.score(result)
        assert 1.0 <= score.overall <= 10.0

    def test_grade_thresholds(self):
        scorer = NetworkScorer()
        cases = [
            (9.0, "excellent"),
            (7.0, "good"),
            (5.0, "fair"),
            (3.0, "poor"),
            (1.0, "unusable"),
        ]
        for overall, expected_grade in cases:
            qs = QualityScore(
                overall=overall,
                download_score=0, upload_score=0,
                latency_score=0, jitter_score=0, dns_score=0,
            )
            assert qs.grade == expected_grade
