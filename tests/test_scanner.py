"""Tests for WiFi scanner output parsing."""

from __future__ import annotations

from wayfi.network.scanner import ScanResult, SecurityType, parse_scan_results


SAMPLE_SCAN_OUTPUT = """bssid / frequency / signal level / flags / ssid
aa:bb:cc:dd:ee:01\t2437\t-45\t[WPA2-PSK-CCMP][ESS]\tHilton_WiFi
aa:bb:cc:dd:ee:02\t5180\t-62\t[ESS]\tStarbucks_Free
aa:bb:cc:dd:ee:03\t2462\t-78\t[WPA-PSK-TKIP][WPA2-PSK-CCMP][ESS]\tAirport_Lounge
aa:bb:cc:dd:ee:04\t5240\t-55\t[WPA3-SAE][ESS]\tSecure_5G
aa:bb:cc:dd:ee:05\t2412\t-90\t[WEP][ESS]\tOld_Network
"""


class TestScanResultParsing:
    def test_parse_basic_output(self):
        results = parse_scan_results(SAMPLE_SCAN_OUTPUT)
        assert len(results) == 5

    def test_parse_ssid(self):
        results = parse_scan_results(SAMPLE_SCAN_OUTPUT)
        ssids = [r.ssid for r in results]
        assert "Hilton_WiFi" in ssids
        assert "Starbucks_Free" in ssids

    def test_parse_signal(self):
        results = parse_scan_results(SAMPLE_SCAN_OUTPUT)
        hilton = next(r for r in results if r.ssid == "Hilton_WiFi")
        assert hilton.signal == -45

    def test_parse_frequency(self):
        results = parse_scan_results(SAMPLE_SCAN_OUTPUT)
        starbucks = next(r for r in results if r.ssid == "Starbucks_Free")
        assert starbucks.frequency == 5180
        assert starbucks.is_5ghz is True

    def test_parse_security_wpa2(self):
        results = parse_scan_results(SAMPLE_SCAN_OUTPUT)
        hilton = next(r for r in results if r.ssid == "Hilton_WiFi")
        assert hilton.security == SecurityType.WPA2

    def test_parse_security_open(self):
        results = parse_scan_results(SAMPLE_SCAN_OUTPUT)
        starbucks = next(r for r in results if r.ssid == "Starbucks_Free")
        assert starbucks.security == SecurityType.OPEN

    def test_parse_security_wpa3(self):
        results = parse_scan_results(SAMPLE_SCAN_OUTPUT)
        secure = next(r for r in results if r.ssid == "Secure_5G")
        assert secure.security == SecurityType.WPA3

    def test_parse_security_wep(self):
        results = parse_scan_results(SAMPLE_SCAN_OUTPUT)
        old = next(r for r in results if r.ssid == "Old_Network")
        assert old.security == SecurityType.WEP

    def test_signal_quality(self):
        results = parse_scan_results(SAMPLE_SCAN_OUTPUT)
        hilton = next(r for r in results if r.ssid == "Hilton_WiFi")
        # -45 dBm should be high quality (close to 100)
        assert hilton.signal_quality >= 90
        weak = next(r for r in results if r.ssid == "Old_Network")
        # -90 dBm should be low quality
        assert weak.signal_quality <= 20

    def test_empty_output(self):
        results = parse_scan_results("")
        assert results == []

    def test_header_only(self):
        results = parse_scan_results("bssid / frequency / signal level / flags / ssid\n")
        assert results == []
