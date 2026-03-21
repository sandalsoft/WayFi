# WayFi

AI-powered travel router that handles captive portal logins so you don't have to.

## What This Does

WayFi is a portable Raspberry Pi 5 device that automatically connects to public WiFi, solves captive portal login pages (hotels, airports, coffee shops), and rebroadcasts the authenticated connection as a private, VPN-protected network for all your devices. It uses a 3-tier solving engine: pattern matching for known portals, a local LLM for unknown ones, and a cloud API fallback when the local model can't figure it out.

It also syncs with your calendar to anticipate which networks you'll need and pre-loads credentials before you arrive.

## How It Works

```
┌─────────────┐    ┌──────────────┐    ┌──────────────┐
│  Public WiFi │───▶│   WayFi Pi   │───▶│ Your Devices │
│  (upstream)  │    │  NAT + VPN   │    │ (private AP) │
└─────────────┘    └──────────────┘    └──────────────┘
```

Two WiFi adapters: one connects upstream to the public network, the other broadcasts your private SSID. All traffic routes through WireGuard or OpenVPN.

**Portal solving chain:**

1. **Heuristic patterns** (~50ms) — YAML pattern files for known vendors (Hilton, Marriott, Boingo, Starbucks, etc.)
2. **Local LLM** (8-15s) — Llama 3.1 8B running on the Pi via llama.cpp, parses unknown portal HTML and generates form submissions
3. **Cloud API** (fallback) — Claude or OpenAI API via phone hotspot when the local model fails

**Calendar integration** pulls upcoming hotel stays from iCloud, Google, or Outlook and pre-caches credentials + network profiles.

## Hardware

| Component | Spec |
|-----------|------|
| Board | Raspberry Pi 5 (16GB RAM) |
| Storage | 128GB microSD |
| Upstream WiFi | MT7921 USB adapter |
| AP WiFi | RTL8812BU USB adapter |
| Power | USB-C PD |
| Case | Argon ONE V3 |

**Alternative:** GL-MT3000 Beryl AX travel router running OpenWrt (no local LLM, cloud API only).

## Tech Stack

- **Language:** Python 3.11 (asyncio throughout)
- **Portal solving:** requests + BeautifulSoup4, Playwright for JS-heavy portals
- **LLM:** llama.cpp with GBNF grammar-constrained JSON output
- **Web dashboard:** FastAPI + Jinja2 on `192.168.8.1`
- **Credentials:** AES-256-GCM + Argon2id key derivation in SQLite
- **Notifications:** Twilio bidirectional SMS (connection alerts + room number prompts)
- **VPN:** WireGuard / OpenVPN with per-network policies
- **WiFi:** hostapd + dnsmasq (AP), wpa_supplicant + iw (client)
- **Process management:** systemd
- **Testing:** pytest + pytest-asyncio + mock portal HTTP server

## Project Structure

```
wayfi/
├── config/                     YAML defaults, network profiles
├── src/wayfi/
│   ├── orchestrator.py         Main state machine (9 states)
│   ├── portal/                 Detection, heuristics, LLM solver, cloud fallback
│   │   └── patterns/           Per-vendor YAML patterns (11 vendors)
│   ├── calendar/               iCloud, Google, Outlook sync + location matching
│   ├── vault/                  Encrypted credential store
│   ├── network/                WiFi scan, connect, speed test, AP management
│   ├── notify/                 Twilio SMS service
│   ├── vpn/                    WireGuard/OpenVPN policy engine
│   └── webui/                  FastAPI dashboard
├── scripts/
│   ├── provision.sh            One-command RPi setup
│   └── systemd/                Service unit files
├── tests/
│   ├── mock_portal/            Mock captive portal server + HTML fixtures
│   └── test_*.py               Unit + integration tests
└── models/                     GGUF model files (gitignored)
```

## Getting Started

### Prerequisites

- Raspberry Pi 5 with Raspberry Pi OS Lite (Bookworm 64-bit)
- Two USB WiFi adapters (MT7921 + RTL8812BU or equivalent)
- Python 3.11+

### Install

```bash
git clone https://github.com/your-username/WayFi.git
cd WayFi
bash scripts/provision.sh
```

The provisioning script handles system dependencies, Python packages, hostapd/dnsmasq config, systemd services, and llama.cpp compilation.

### Configuration

Edit `config/wayfi.yaml` for WiFi SSID/password, VPN settings, Twilio credentials, and calendar provider setup. Credential management happens through the web dashboard at `192.168.8.1` or via the encrypted vault CLI.

## Performance Targets

| Metric | Target |
|--------|--------|
| Boot to connected (known network) | < 45s |
| Boot to connected (LLM solve) | < 75s |
| Heuristic portal solve | < 50ms |
| LLM portal solve | 8-15s |
| Auto-solve success rate | 80%+ heuristic, 95%+ with LLM |

## Development

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run tests with mock portal server
pytest tests/ -v

# Type check
mypy src/wayfi/

# Start the orchestrator locally (without WiFi hardware)
python -m wayfi.orchestrator --dry-run
```

## Status

Work in progress. Phase 1 (project scaffolding) is complete. See `plan.md` for the full implementation roadmap.
