# Interview Answers — WayFi

_Derived directly from PRD v1.5 (March 20, 2026). Interview step skipped per user request._

## What are you building?

WayFi — an AI-powered autonomous travel router. A portable device that automatically connects to public WiFi networks, solves captive portal login pages (hotel, airport, coffee shop), and rebroadcasts the connection as a private, VPN-protected SSID for all user devices. It uses calendar integration to anticipate network needs, sends SMS notifications via Twilio, and runs a local LLM for portal solving when heuristics fail.

## Who is the target user?

Frequent travelers (business travelers, digital nomads) who connect to public WiFi dozens of times per year and are tired of repetitive captive portal logins across multiple devices.

## What is the core problem?

Repetitive credential entry into diverse captive portal UIs at every venue, on every device, on every trip. No quality signal for networks. No automatic VPN protection. Multi-device authentication hassle.

## What is the technical stack?

- **Language:** Python 3.11 (all services except llama.cpp)
- **Web Framework:** FastAPI + Uvicorn (admin dashboard)
- **LLM Runtime:** llama.cpp (C++, ARM NEON) — Llama-3.1-8B-Instruct Q4_K_M
- **LLM Fallback:** Claude API / OpenAI API via iPhone hotspot
- **Portal Solving:** requests + BeautifulSoup + Playwright (headless browser fallback)
- **Calendar:** caldav (iCloud), google-api-python-client (Google), msal (Outlook)
- **Credential Store:** SQLite + PyCryptodome (AES-256-GCM) + Argon2id
- **Notifications:** Twilio Python SDK (bidirectional SMS)
- **Speed Test:** Custom multi-metric probes (Cloudflare)
- **VPN:** WireGuard (wg-quick) + OpenVPN
- **WiFi AP:** hostapd + dnsmasq
- **WiFi Client:** wpa_supplicant + iw
- **Process Management:** systemd
- **Config:** YAML + SQLite

## What is the hardware platform?

**Primary:** Raspberry Pi 5 (16GB) with BCM2712 SoC, 128GB microSD, two USB WiFi adapters (MT7921 for upstream, RTL8812BU for downstream AP), USB-C PD power, Argon ONE V3 case.

**Alternative (Cloud Mode):** GL-MT3000 Beryl AX travel router running OpenWrt. No local LLM — uses cloud API via iPhone hotspot for non-heuristic portal solving.

## What are the key modules?

1. **wayfi-orchestrator** — Main control loop and state machine (BOOT→SCAN→SELECT→CONNECT→DETECT_PORTAL→SOLVE_PORTAL→VERIFY→POST_AUTH→MONITOR)
2. **wayfi-portal-solver** — 3-layer solve: heuristic patterns → local LLM → cloud API fallback
3. **wayfi-llm** — llama.cpp inference server on localhost:8080
4. **wayfi-calendar** — Multi-provider calendar sync (iCloud, Google, Outlook)
5. **wayfi-notifier** — Bidirectional Twilio SMS (outbound alerts + inbound room number webhook)
6. **wayfi-speedtest** — Network quality scoring (1-10 composite)
7. **wayfi-vpn** — Per-network VPN policy engine (WireGuard/OpenVPN)
8. **wayfi-vault** — AES-256-GCM encrypted credential store with Argon2id KDF
9. **wayfi-webui** — FastAPI admin dashboard on 192.168.8.1

## What are the performance targets?

- Boot-to-connected: <45s (heuristic), <75s (LLM solve)
- Portal heuristic solve: <50ms
- Portal LLM solve: 8-15s (30s timeout)
- SMS delivery: <10s after connection
- POST_AUTH phase: <8s total
- Connectivity monitoring: every 15s (aggressive) or 60s (battery-saver)
- Portal auto-solve rate: ≥80% heuristic, ≥95% heuristic+LLM

## What are the key architectural decisions?

- Dual WiFi adapter topology: wlan0 (upstream STA) + wlan1 (downstream AP) with iptables NAT
- 3-tier portal solving: heuristic → local LLM → cloud API
- Calendar-driven network prediction and credential pre-loading
- Room number caching tied to stay duration (calendar or SMS-derived)
- Parallel async operations (asyncio) throughout
- LLM pre-loaded at boot, kept resident in RAM
- Stripped OS (no GUI, no Bluetooth, tmpfs for transient data)

## What are the risks?

- JS-heavy portals needing Playwright (High)
- LLM hallucinated form fields (Medium — validate against actual HTML DOM)
- Portal vendor updates breaking heuristics (Medium — LLM fallback covers)
- iPhone hotspot unavailability (Medium — heuristics handle 80%+)
- RPi thermal throttling (Low — active cooling)
- AP isolation (Medium — separate interface topology)
- 802.1X enterprise portals (Low — out of scope v1)

## Repository structure?

```
wayfi/
  config/                    — YAML configuration files, default network profiles
  src/wayfi/                 — Python package root
    orchestrator.py          — main control loop and state machine
    portal/                  — portal detection, heuristic engine, LLM solver
      patterns/              — YAML pattern files per vendor
    calendar/                — multi-provider calendar sync
    vault/                   — encrypted credential store
    network/                 — WiFi scanning, connection management, speed testing
    notify/                  — Twilio SMS integration
    vpn/                     — WireGuard/OpenVPN management
    webui/                   — FastAPI admin dashboard
  scripts/                   — setup scripts, systemd unit files, RPi provisioning
  tests/                     — unit + integration tests with mock portals
  models/                    — GGUF model files (gitignored)
```

## Deployment model?

Systemd-managed services on Raspberry Pi OS Lite (Bookworm 64-bit, headless). One-command RPi provisioning script from fresh OS. Alternative: OpenWrt packages for GL.iNet travel routers.
