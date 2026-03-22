"""3-tier portal solving chain test: heuristic -> LLM -> cloud fallback."""
import asyncio
import json
import sys
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
import urllib.request
import urllib.error

# Mock Hilton portal HTML
HILTON_PORTAL_HTML = """<!DOCTYPE html>
<html>
<head><title>Hilton Guest Internet</title></head>
<body>
<h1>Welcome to Hilton</h1>
<p>Please log in with your Hilton Honors credentials</p>
<form action="/login" method="POST">
  <input type="text" name="lastName" placeholder="Last Name">
  <input type="text" name="roomNumber" placeholder="Room Number">
  <input type="text" name="loyaltyNumber" placeholder="Hilton Honors #">
  <label><input type="checkbox" name="acceptTerms"> I accept the terms</label>
  <button type="submit">Connect</button>
</form>
</body>
</html>"""

# Unknown portal for LLM fallback test
UNKNOWN_PORTAL_HTML = """<!DOCTYPE html>
<html>
<head><title>Guest WiFi - Boutique Hotel</title></head>
<body>
<h2>Welcome to The Grand Boutique</h2>
<form action="/guest-auth" method="POST">
  <input type="email" name="guest_email" placeholder="Email Address" required>
  <input type="text" name="guest_name" placeholder="Full Name" required>
  <input type="text" name="room" placeholder="Room #" required>
  <label><input type="checkbox" name="tos" value="1"> I agree to terms of service</label>
  <button type="submit">Get Online</button>
</form>
</body>
</html>"""


class MockPortalHandler(BaseHTTPRequestHandler):
    portal_html = HILTON_PORTAL_HTML

    def do_GET(self):
        if self.path in ("/generate_204", "/hotspot-detect.html"):
            self.send_response(302)
            self.send_header("Location", "http://127.0.0.1:18888/portal")
            self.end_headers()
        elif self.path == "/portal":
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(self.portal_html.encode())
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.end_headers()
        self.wfile.write(b"<html><body>Connected!</body></html>")

    def log_message(self, *args):
        pass


def start_mock_server(port, html=HILTON_PORTAL_HTML):
    MockPortalHandler.portal_html = html
    server = HTTPServer(("127.0.0.1", port), MockPortalHandler)
    t = threading.Thread(target=server.serve_forever, daemon=True)
    t.start()
    return server


def test_portal_detection():
    print("\n" + "=" * 60)
    print("PORTAL DETECTION: Mock captive portal redirect")
    print("=" * 60)

    server = start_mock_server(18888)
    try:
        req = urllib.request.Request("http://127.0.0.1:18888/generate_204")
        handler = urllib.request.HTTPHandler()
        opener = urllib.request.build_opener(handler)
        # Don't follow redirects
        class NoRedirect(urllib.request.HTTPRedirectHandler):
            def redirect_request(self, req, fp, code, msg, headers, newurl):
                raise urllib.error.HTTPError(newurl, code, msg, headers, fp)
        opener = urllib.request.build_opener(NoRedirect)
        try:
            resp = opener.open(req)
            print(f"  Response: {resp.status} (no redirect)")
            print("  [FAIL] Expected redirect")
            return False
        except urllib.error.HTTPError as e:
            if e.code in (301, 302):
                print(f"  {e.code} redirect detected -> portal page")
                # Fetch the portal page directly
                resp = urllib.request.urlopen("http://127.0.0.1:18888/portal")
                html = resp.read().decode()
                if "Hilton" in html:
                    print("  [PASS] Captive portal detected, Hilton HTML received")
                    return True
                print("  [FAIL] Unexpected HTML content")
                return False
            print(f"  [FAIL] Unexpected HTTP error: {e.code}")
            return False
    finally:
        server.shutdown()


def test_tier1_heuristic():
    print("\n" + "=" * 60)
    print("TIER 1: Heuristic Pattern Matching")
    print("=" * 60)

    from wayfi.portal.heuristic import HeuristicEngine

    engine = HeuristicEngine()
    count = engine.load_patterns()
    print(f"  Loaded {count} patterns")

    vault_values = {
        "last_name": "Nelson",
        "room_number": "134",
        "loyalty_hilton": "",
        "email_throwaway": "feiefi@26.com",
    }

    match = engine.match(
        portal_html=HILTON_PORTAL_HTML,
        portal_url="http://hiltonguestinternet.com/portal",
        vault_values=vault_values,
    )

    if not match:
        print("  [FAIL] No heuristic match found")
        return False

    print(f"  MATCH: {match.pattern_name} ({match.vendor})")
    print(f"  Confidence: {match.confidence:.0%}")
    print(f"  Match time: {match.match_time_ms:.1f}ms")
    print(f"  Strategy:")
    print(f"    Action: {match.strategy.method} {match.strategy.action_url_pattern}")
    print(f"    Fields: {json.dumps(match.strategy.fields, indent=6)}")
    print(f"    Checkboxes: {match.strategy.checkboxes}")

    ok = True
    if match.strategy.fields.get("lastName") == "Nelson":
        print("  [PASS] Vault interpolation: last_name -> Nelson")
    else:
        print(f"  [FAIL] Expected lastName=Nelson, got {match.strategy.fields.get('lastName')}")
        ok = False

    if match.strategy.fields.get("roomNumber") == "134":
        print("  [PASS] Vault interpolation: room_number -> 134")
    else:
        print(f"  [FAIL] Expected roomNumber=134, got {match.strategy.fields.get('roomNumber')}")
        ok = False

    return ok


def test_tier1_no_match():
    print("\n" + "=" * 60)
    print("TIER 1b: Heuristic - Unknown Portal (should NOT match)")
    print("=" * 60)

    from wayfi.portal.heuristic import HeuristicEngine
    engine = HeuristicEngine()
    engine.load_patterns()

    match = engine.match(
        portal_html=UNKNOWN_PORTAL_HTML,
        portal_url="http://192.168.1.1/guest-auth",
        vault_values={},
    )

    if match is None:
        print("  [PASS] No heuristic match for unknown portal")
        return True
    elif match.pattern_name == "generic":
        print(f"  [PASS] Only generic catch-all matched (confidence={match.confidence:.0%}) - expected behavior")
        return True
    else:
        print(f"  [WARN] Unexpected specific match: {match.pattern_name} (confidence={match.confidence:.0%})")
        return False


def test_tier2_llm():
    print("\n" + "=" * 60)
    print("TIER 2: Local LLM Portal Solving (Qwen2.5-3B)")
    print("=" * 60)

    from wayfi.portal.llm_solver import LLMSolver

    solver = LLMSolver(
        endpoint="http://127.0.0.1:8081",
        model="qwen2.5-3b-instruct",
    )

    print("  Sending unknown portal HTML to local LLM...")
    print("  (This may take 15-30s on RPi 5)")

    start = time.monotonic()
    try:
        loop = asyncio.new_event_loop()
        result = loop.run_until_complete(
            solver.solve(UNKNOWN_PORTAL_HTML, "http://192.168.1.1/guest-auth")
        )
        elapsed = time.monotonic() - start

        print(f"  Response time: {elapsed:.1f}s")
        if result and result.success:
            print(f"  LLM result:")
            print(f"    action_url: {result.action_url}")
            print(f"    method: {result.method}")
            print(f"    fields: {result.fields}")
            print(f"    checkboxes: {result.checkboxes}")
            print("  [PASS] LLM returned a solve strategy")
            return True
        elif result and not result.success:
            print(f"  [FAIL] LLM returned error: {result.error}")
            return False
        else:
            print("  [FAIL] LLM returned no result")
            return False
    except Exception as e:
        elapsed = time.monotonic() - start
        print(f"  [FAIL] LLM error after {elapsed:.1f}s: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    results = {}

    print("\n" + "#" * 60)
    print("#  WayFi 3-Tier Portal Solving Chain Test")
    print("#" * 60)

    results["detection"] = test_portal_detection()
    results["tier1_match"] = test_tier1_heuristic()
    results["tier1_nomatch"] = test_tier1_no_match()
    results["tier2_llm"] = test_tier2_llm()

    print("\n" + "=" * 60)
    print("RESULTS SUMMARY")
    print("=" * 60)
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    for name, ok in results.items():
        status = "PASS" if ok else "FAIL"
        print(f"  [{status}] {name}")
    print(f"\n  {passed}/{total} tests passed")

    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
