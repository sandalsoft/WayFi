"""Tests for heuristic portal pattern matching."""

from __future__ import annotations

import time
from pathlib import Path

import pytest

from wayfi.portal.heuristic import HeuristicEngine


class TestHeuristicEngine:
    @pytest.fixture
    def engine(self, portal_patterns_dir):
        e = HeuristicEngine(patterns_dir=portal_patterns_dir)
        count = e.load_patterns()
        assert count >= 11
        return e

    def test_load_patterns(self, engine):
        assert len(engine._patterns) >= 11

    def test_match_hilton(self, engine, mock_portals_dir):
        html = (mock_portals_dir / "hilton.html").read_text()
        match = engine.match(html, "https://hiltonguestinternet.com/portal")
        assert match is not None
        assert match.vendor == "Hilton"

    def test_match_nomadix(self, engine, mock_portals_dir):
        html = (mock_portals_dir / "nomadix.html").read_text()
        match = engine.match(html, "https://gateway.hotel/cgi-bin/login")
        assert match is not None
        assert match.vendor == "Nomadix"

    def test_match_starbucks(self, engine, mock_portals_dir):
        html = (mock_portals_dir / "starbucks.html").read_text()
        match = engine.match(html, "https://starbucks.com/portal")
        assert match is not None
        assert match.vendor == "Starbucks"

    def test_match_marriott(self, engine, mock_portals_dir):
        html = (mock_portals_dir / "marriott.html").read_text()
        match = engine.match(html, "https://marriottwifi.com/login")
        assert match is not None
        assert match.vendor == "Marriott"

    def test_match_aruba(self, engine, mock_portals_dir):
        html = (mock_portals_dir / "aruba.html").read_text()
        match = engine.match(html, "https://clearpass.aruba.com/guest/")
        assert match is not None
        assert match.vendor == "Aruba Networks"

    def test_no_match_for_random_html(self, engine):
        html = "<html><body><p>Hello world</p></body></html>"
        match = engine.match(html, "https://example.com")
        assert match is None

    def test_vault_interpolation(self, engine, mock_portals_dir):
        html = (mock_portals_dir / "hilton.html").read_text()
        vault_values = {
            "last_name": "Smith",
            "room_number": "1412",
            "loyalty_hilton": "H12345",
        }
        match = engine.match(html, "https://hilton.com/portal", vault_values)
        assert match is not None
        assert match.strategy.fields.get("lastName") == "Smith"
        assert match.strategy.fields.get("roomNumber") == "1412"

    def test_performance_sub_50ms(self, engine, mock_portals_dir):
        html = (mock_portals_dir / "hilton.html").read_text()
        start = time.monotonic()
        for _ in range(100):
            engine.match(html, "https://hilton.com/portal")
        elapsed = (time.monotonic() - start) * 1000  # total ms for 100 runs
        per_match = elapsed / 100
        assert per_match < 50, f"Match took {per_match:.1f}ms, should be <50ms"
