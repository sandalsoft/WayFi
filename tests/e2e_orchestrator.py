"""End-to-end orchestrator state machine test.

Simulates: portal detection -> heuristic solve -> form submission -> verify connectivity.
Uses a mock server that acts as both the captive portal and the connectivity check endpoint.
"""
import asyncio
import json
import logging
import sys
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("e2e-test")

MOCK_PORT = 18889
MOCK_BASE = f"http://127.0.0.1:{MOCK_PORT}"

# Track what the portal receives
submitted_data = {}
portal_solved = False


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


class MockPortalServer(BaseHTTPRequestHandler):
    """Simulates a captive portal + connectivity check endpoint.

    Before solve: /generate_204 returns 302 -> /portal
    After solve:  /generate_204 returns 204 (connectivity restored)
    """

    def do_GET(self):
        global portal_solved
        if self.path == "/generate_204":
            if portal_solved:
                # Internet is working
                self.send_response(204)
                self.end_headers()
            else:
                # Redirect to captive portal
                self.send_response(302)
                self.send_header("Location", f"{MOCK_BASE}/portal")
                self.end_headers()
        elif self.path == "/portal":
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(HILTON_PORTAL_HTML.encode())
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        global portal_solved, submitted_data
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length).decode()

        # Parse form data
        from urllib.parse import parse_qs
        submitted_data = {k: v[0] for k, v in parse_qs(body).items()}
        logger.info("Portal received form submission: %s", submitted_data)

        # Mark portal as solved
        portal_solved = True

        # Return success redirect
        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.end_headers()
        self.wfile.write(b"<html><body>Welcome! You are now connected.</body></html>")

    def log_message(self, *args):
        pass


def start_mock_server():
    server = HTTPServer(("127.0.0.1", MOCK_PORT), MockPortalServer)
    t = threading.Thread(target=server.serve_forever, daemon=True)
    t.start()
    return server


async def test_orchestrator_flow():
    """Test the orchestrator from DETECT_PORTAL through VERIFY."""
    from wayfi.portal.detector import PortalDetector
    from wayfi.portal.heuristic import HeuristicEngine
    from wayfi.portal.submitter import PortalSubmitter, SubmitRequest
    from wayfi.vault.vault import Vault
    from pathlib import Path
    import tempfile

    results = {}

    # --- Step 1: Portal Detection ---
    print("\n" + "=" * 60)
    print("STEP 1: Portal Detection")
    print("=" * 60)

    detector = PortalDetector(
        probe_url=f"{MOCK_BASE}/generate_204",
        fallbacks=[],
        timeout=5.0,
    )

    result = await detector.detect()
    print(f"  is_captive: {result.is_captive}")
    print(f"  redirect_url: {result.redirect_url}")
    print(f"  status_code: {result.status_code}")
    print(f"  portal_html length: {len(result.portal_html)} chars")

    if result.is_captive and "Hilton" in result.portal_html:
        print("  [PASS] Captive portal detected with Hilton HTML")
        results["detection"] = True
    else:
        print("  [FAIL] Portal not detected correctly")
        results["detection"] = False
        return results

    # --- Step 2: Heuristic Matching ---
    print("\n" + "=" * 60)
    print("STEP 2: Heuristic Pattern Matching + Vault Interpolation")
    print("=" * 60)

    engine = HeuristicEngine()
    count = engine.load_patterns()
    print(f"  Loaded {count} patterns")

    # Use real vault with test credentials
    with tempfile.TemporaryDirectory() as tmpdir:
        vault_path = Path(tmpdir) / "test_vault.db"
        vault = Vault(db_path=vault_path)
        vault.initialize("testpass123")
        vault.unlock("testpass123")
        vault.set_credential("last_name", "Nelson")
        vault.set_credential("room_number", "134")
        vault.set_credential("email_throwaway", "test@example.com")

        # Get vault values like the orchestrator does
        vault_values = {}
        for cred in vault.get_all():
            vault_values[cred.name] = cred.value

        match = engine.match(
            portal_html=result.portal_html,
            portal_url=result.redirect_url,
            vault_values=vault_values,
        )

        if not match:
            print("  [FAIL] No heuristic match")
            results["heuristic"] = False
            return results

        print(f"  MATCH: {match.pattern_name} ({match.vendor})")
        print(f"  Confidence: {match.confidence:.0%}")
        print(f"  Strategy: {match.strategy.method} {match.strategy.action_url_pattern}")
        print(f"  Fields: {match.strategy.fields}")

        if match.strategy.fields.get("lastName") == "Nelson" and match.strategy.fields.get("roomNumber") == "134":
            print("  [PASS] Heuristic matched + vault values interpolated")
            results["heuristic"] = True
        else:
            print("  [FAIL] Vault interpolation incorrect")
            results["heuristic"] = False
            return results

        # --- Step 3: Form Submission ---
        print("\n" + "=" * 60)
        print("STEP 3: Portal Form Submission")
        print("=" * 60)

        submitter = PortalSubmitter(verify_url=f"{MOCK_BASE}/generate_204")

        # Build action URL (resolve relative to portal URL)
        from urllib.parse import urljoin
        action_url = urljoin(result.redirect_url, match.strategy.action_url_pattern)
        print(f"  Action URL: {action_url}")

        request = SubmitRequest(
            portal_url=result.redirect_url,
            action_url=action_url,
            method=match.strategy.method,
            fields=match.strategy.fields,
            checkboxes=match.strategy.checkboxes,
        )

        submit_result = await submitter.submit(request, result.portal_html)
        print(f"  Submit success: {submit_result.success}")
        print(f"  Status code: {submit_result.status_code}")
        print(f"  Server received: {submitted_data}")

        if submit_result.success:
            print("  [PASS] Form submitted and connectivity verified")
            results["submission"] = True
        else:
            print(f"  [FAIL] Submission failed: {submit_result.error}")
            results["submission"] = False

        # --- Step 4: Post-Solve Verification ---
        print("\n" + "=" * 60)
        print("STEP 4: Post-Solve Connectivity Verification")
        print("=" * 60)

        connected = await detector.verify_connectivity()
        print(f"  Connectivity: {connected}")

        if connected:
            print("  [PASS] Internet access confirmed after portal solve")
            results["verify"] = True
        else:
            print("  [FAIL] No connectivity after solve")
            results["verify"] = False

        # --- Step 5: Verify submitted data ---
        print("\n" + "=" * 60)
        print("STEP 5: Validate Submitted Credentials")
        print("=" * 60)

        checks = {
            "lastName": "Nelson",
            "roomNumber": "134",
            "acceptTerms": "on",
        }
        all_ok = True
        for field_name, expected in checks.items():
            actual = submitted_data.get(field_name, "")
            if actual == expected:
                print(f"  [PASS] {field_name} = {actual}")
            else:
                print(f"  [FAIL] {field_name}: expected '{expected}', got '{actual}'")
                all_ok = False
        results["credentials"] = all_ok

    return results


def main():
    global portal_solved, submitted_data
    portal_solved = False
    submitted_data = {}

    print("\n" + "#" * 60)
    print("#  WayFi Orchestrator End-to-End Test")
    print("#  Detection -> Heuristic -> Submit -> Verify")
    print("#" * 60)

    server = start_mock_server()
    time.sleep(0.2)  # let server bind

    try:
        loop = asyncio.new_event_loop()
        results = loop.run_until_complete(test_orchestrator_flow())
    finally:
        server.shutdown()

    print("\n" + "=" * 60)
    print("RESULTS SUMMARY")
    print("=" * 60)
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    for name, ok in results.items():
        status = "PASS" if ok else "FAIL"
        print(f"  [{status}] {name}")
    print(f"\n  {passed}/{total} steps passed")

    if passed == total:
        print("\n  The full portal-solving state machine works end-to-end.")
        print("  Detection -> Pattern Match -> Vault Interpolation -> Form Submit -> Verify")
    else:
        print("\n  Some steps failed. Review output above.")

    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
