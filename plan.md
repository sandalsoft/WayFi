# Implementation Plan: WayFi — AI-Powered Autonomous Travel Router

## Summary

WayFi is a portable, Raspberry Pi 5-based travel router that automatically connects to public WiFi networks, solves captive portal logins using a 3-tier engine (heuristic patterns → local LLM → cloud API fallback), and rebroadcasts the authenticated connection as a private, VPN-protected SSID. It integrates with calendar providers for location-aware network prediction, sends bidirectional SMS notifications via Twilio, and provides a FastAPI web dashboard for configuration. The system is optimized for extreme speed — boot-to-connected in under 45 seconds for known networks.

## Technical Stack

- **Language:** Python 3.11 (all services), C++ (llama.cpp)
- **Web Framework:** FastAPI + Uvicorn
- **LLM Runtime:** llama.cpp with OpenAI-compatible API (localhost:8080)
- **Portal Solving:** requests + BeautifulSoup4 + Playwright (ARM64 headless fallback)
- **Calendar:** caldav, google-api-python-client, msal
- **Credential Store:** SQLite + PyCryptodome (AES-256-GCM) + argon2-cffi
- **Notifications:** Twilio SDK (bidirectional SMS)
- **VPN:** WireGuard (wg-quick) + OpenVPN
- **WiFi:** hostapd + dnsmasq (AP), wpa_supplicant + iw (client)
- **Async:** asyncio throughout all services
- **Config:** YAML (static), SQLite (dynamic)
- **Testing:** pytest + pytest-asyncio + mock portal HTTP server

## Repository Structure

```
wayfi/
├── config/                          # YAML defaults, network profiles
│   ├── wayfi.yaml                   # Main configuration
│   └── network-profiles/            # Per-network saved configs
├── src/wayfi/
│   ├── __init__.py
│   ├── orchestrator.py              # Main state machine control loop
│   ├── portal/
│   │   ├── __init__.py
│   │   ├── detector.py              # Captive portal detection (HTTP probe)
│   │   ├── heuristic.py             # Pattern-matching engine
│   │   ├── llm_solver.py            # Local LLM solver (llama.cpp client)
│   │   ├── cloud_solver.py          # Cloud API fallback (Claude/OpenAI)
│   │   ├── submitter.py             # Form submission (requests + Playwright)
│   │   └── patterns/                # YAML pattern files per vendor
│   │       ├── nomadix.yaml
│   │       ├── antlabs.yaml
│   │       ├── aruba.yaml
│   │       ├── cisco.yaml
│   │       ├── ruckus.yaml
│   │       ├── hilton.yaml
│   │       ├── marriott.yaml
│   │       ├── ihg.yaml
│   │       ├── boingo.yaml
│   │       ├── starbucks.yaml
│   │       └── generic.yaml
│   ├── calendar/
│   │   ├── __init__.py
│   │   ├── sync.py                  # Calendar sync daemon
│   │   ├── icloud.py                # iCloud CalDAV provider
│   │   ├── google.py                # Google Calendar API provider
│   │   ├── outlook.py               # Microsoft Graph provider
│   │   └── location.py              # Location extraction + network matching
│   ├── vault/
│   │   ├── __init__.py
│   │   └── vault.py                 # AES-256-GCM encrypted SQLite store
│   ├── network/
│   │   ├── __init__.py
│   │   ├── scanner.py               # WiFi scanning via wpa_supplicant/iw
│   │   ├── connector.py             # Network connection management
│   │   ├── scorer.py                # Network selection scoring
│   │   └── speedtest.py             # Multi-metric speed/quality testing
│   ├── notify/
│   │   ├── __init__.py
│   │   └── sms.py                   # Bidirectional Twilio SMS service
│   ├── vpn/
│   │   ├── __init__.py
│   │   └── manager.py               # WireGuard/OpenVPN per-network policy
│   └── webui/
│       ├── __init__.py
│       ├── app.py                   # FastAPI application
│       ├── routers/                 # API route modules
│       │   ├── status.py
│       │   ├── vault.py
│       │   ├── networks.py
│       │   ├── patterns.py
│       │   ├── calendar.py
│       │   ├── settings.py
│       │   └── logs.py
│       ├── static/                  # Frontend assets
│       └── templates/               # Jinja2 HTML templates
├── scripts/
│   ├── provision.sh                 # One-command RPi setup
│   ├── systemd/                     # Unit files for all services
│   │   ├── wayfi-orchestrator.service
│   │   ├── wayfi-llm.service
│   │   ├── wayfi-calendar.service
│   │   ├── wayfi-notifier.service
│   │   ├── wayfi-webui.service
│   │   ├── wayfi-hostapd.service
│   │   └── wayfi-dnsmasq.service
│   └── ralph/
├── tests/
│   ├── conftest.py
│   ├── test_vault.py
│   ├── test_portal_detector.py
│   ├── test_heuristic.py
│   ├── test_llm_solver.py
│   ├── test_scanner.py
│   ├── test_speedtest.py
│   ├── test_sms.py
│   ├── test_calendar.py
│   ├── test_vpn.py
│   ├── test_orchestrator.py
│   ├── test_webui.py
│   └── mock_portal/                 # Mock captive portal HTTP server
│       ├── server.py
│       └── portals/                 # Sample portal HTML fixtures
├── models/                          # GGUF files (gitignored)
├── pyproject.toml
└── .gitignore
```

---

## Carmeck Architectural Review

### Overview

The PRD describes a well-scoped embedded systems project with clear module boundaries. The 3-tier portal solving architecture (heuristic → local LLM → cloud API) is sound and provides graceful degradation. The dual-WiFi-adapter NAT topology is the correct approach for transparent upstream bridging. Calendar-driven network prediction is a genuine differentiator.

### Strengths

1. **Clean separation of concerns.** Each service (vault, portal solver, calendar, notifier, speedtest, VPN) is independently testable and deployable. The orchestrator composes them without tight coupling.

2. **Graceful degradation chain.** Heuristic (50ms) → LLM (8-15s) → Cloud API → manual fallback. Each tier has clear latency bounds and failure modes. The parallel heuristic+LLM execution with first-result-wins is an excellent optimization.

3. **Correct network topology.** Two physical interfaces with NAT masquerade is the only reliable way to bridge captive-portal-authenticated upstream to multiple downstream clients. Single-radio solutions (GL.iNet cloud mode) make the right tradeoff for portability.

4. **Security-first credential handling.** AES-256-GCM + Argon2id is current best practice. Passphrase-derived keys with tmpfs caching avoids persisting decrypted material to SD card.

### Risks & Mitigations (Codex-Level)

| ID | Risk | Severity | Mitigation |
|:---|:-----|:---------|:-----------|
| R1 | **Playwright on ARM64 is fragile.** Chromium ARM64 builds have historically been unstable on RPi. Memory pressure with LLM resident + headless browser could OOM. | High | Playwright is heavyweight fallback only. Cap browser pool to 1 instance. Use cgroups to reserve LLM memory. Track portal fingerprints that need JS — if <5%, acceptable. Consider pyppeteer as lighter alternative. |
| R2 | **Portal HTML sanitization for LLM input.** Stripping scripts/styles may remove critical form context (JS-generated fields, dynamic action URLs). | Medium | Preserve `<form>`, `<input>`, `<select>`, `<button>`, `<label>`, `<a>` tags and all attributes. Strip `<script>`, `<style>`, `<img>`, `<svg>`, comments. Keep `<noscript>` content as it often contains the non-JS fallback form. |
| R3 | **wpa_supplicant race conditions.** Automated scan→select→connect cycles can race with manual network changes or driver state. | Medium | Use wpa_cli's event-driven interface (CTRL-EVENT-CONNECTED, CTRL-EVENT-DISCONNECTED) rather than polling. Wrap all wpa_cli interactions in an async lock. |
| R4 | **Calendar OAuth token refresh in headless environment.** Google and Microsoft OAuth tokens expire. Device code flow requires initial user interaction. | Medium | Store refresh tokens in vault. Implement token refresh in background sync loop. Alert via SMS if refresh fails. Initial setup via web UI wizard. |
| R5 | **Room number SMS prompt UX.** User may not respond quickly. Portal may timeout waiting. | Low | Fire SMS immediately on room-number-needed. Set 5-minute wait with 2-minute reminder. If no reply, skip this network and try alternatives. Cache aggressively once received. |
| R6 | **SD card wear from SQLite writes.** Frequent portal cache and log writes degrade microSD cards. | Low | Use WAL mode for SQLite. Put transient DBs on tmpfs. Batch log writes. Consider moving vault DB to tmpfs with periodic flush to SD. |

### Architectural Decisions & Reference Points (RP)

**RP-1: Async-first, not thread-first.** All Python services use asyncio. This is correct for I/O-bound network operations. The LLM client call to localhost:8080 should use aiohttp, not blocking requests. Speedtest probes, VPN activation, and SMS dispatch all benefit from asyncio.gather parallelism.

**RP-2: Portal fingerprinting for solve caching.** Hash the portal's form structure (field names, action URL pattern, vendor signals) — not the full HTML (which changes per session with tokens/nonces). Cache the solve *strategy* (which heuristic pattern or LLM-generated field mapping worked), not the exact POST payload.

**RP-3: Configuration layering.** `config/wayfi.yaml` provides defaults. SQLite stores user-modified settings (vault, network profiles, VPN policies). Web UI writes to SQLite. Systemd unit files reference the YAML. This avoids the common pitfall of config split across too many sources.

**RP-4: LLM prompt design.** The prompt to llama.cpp must be tightly constrained: provide cleaned HTML, request JSON output with strict schema, include 2-3 few-shot examples of common portal types. Use grammar-constrained generation (llama.cpp's GBNF grammar support) to force valid JSON output — eliminates hallucination of invalid field mappings.

**RP-5: Testing strategy.** Mock portal server is critical. Create HTML fixtures for each vendor pattern. Integration tests run the full heuristic→LLM→submit chain against mock portals. Unit tests cover vault crypto, network scoring, calendar parsing independently. No tests should require real WiFi hardware — mock wpa_cli and iw at the subprocess level.

### Default Planning Notes

- **Phase 1 modules have zero interdependencies** — all 6 can be built by parallel subagents
- **Phase 2 depends on Phase 1** — portal patterns need vault (for credentials) and detector (for HTML); calendar needs vault (for OAuth tokens); LLM solver needs detector output
- **Phase 3 is pure integration** — orchestrator wires everything; web UI exposes it
- Steps are sized for single-agent execution (~30-90 min each)
- Each step produces testable output with clear "done" criteria

---

## Phases

### Phase 1: Project Setup & Scaffolding
- [x] Step 1.1: Initialize Python project with `pyproject.toml`, directory structure, and `.gitignore`
- [x] Step 1.2: Create `config/wayfi.yaml` with all default configuration values

### Phase 2: Foundation Modules (Parallelizable — No Interdependencies)
- [ ] Step 2.1: Build encrypted vault module (`src/wayfi/vault/vault.py`) — AES-256-GCM + Argon2id + SQLite CRUD
- [ ] Step 2.2: Build WiFi scanner and connection manager (`src/wayfi/network/scanner.py`, `connector.py`) — wpa_supplicant/iw wrapper with async event interface
- [ ] Step 2.3: Build captive portal detector (`src/wayfi/portal/detector.py`) — HTTP probe engine with 2s timeout
- [ ] Step 2.4: Build Twilio bidirectional SMS service (`src/wayfi/notify/sms.py`) — outbound notifications + inbound webhook for room number replies
- [ ] Step 2.5: Build speed test and network quality scorer (`src/wayfi/network/speedtest.py`, `scorer.py`) — multi-metric composite scoring (1-10)
- [ ] Step 2.6: Build hostapd/dnsmasq AP configuration generator (`src/wayfi/network/ap.py`) — config generation + process management

### Phase 3: Intelligence Layer (Sequential — Depends on Phase 2)
- [ ] Step 3.1: Build heuristic portal pattern engine (`src/wayfi/portal/heuristic.py`) — YAML pattern loader, regex compilation at boot, pattern matching
- [ ] Step 3.2: Create initial portal pattern library (11 vendor YAML files in `src/wayfi/portal/patterns/`)
- [ ] Step 3.3: Build portal form submitter (`src/wayfi/portal/submitter.py`) — requests-based with CookieJar session, redirect following, Playwright heavyweight fallback
- [ ] Step 3.4: Build LLM solver integration (`src/wayfi/portal/llm_solver.py`) — llama.cpp OpenAI-compatible API client + prompt templates + GBNF grammar for JSON output
- [ ] Step 3.5: Build cloud API fallback solver (`src/wayfi/portal/cloud_solver.py`) — Claude/OpenAI API with hotspot detection and routing
- [ ] Step 3.6: Build calendar sync daemon — iCloud CalDAV provider (`src/wayfi/calendar/icloud.py`)
- [ ] Step 3.7: Build calendar sync daemon — Google Calendar API provider (`src/wayfi/calendar/google.py`)
- [ ] Step 3.8: Build calendar sync daemon — Microsoft Outlook Graph provider (`src/wayfi/calendar/outlook.py`)
- [ ] Step 3.9: Build calendar sync coordinator and location extraction (`src/wayfi/calendar/sync.py`, `location.py`) — venue matching, stay duration extraction, network prediction
- [ ] Step 3.10: Build network selection scoring with calendar intelligence (`src/wayfi/network/scorer.py` update) — integrate calendar location matches into scoring weights

### Phase 4: Integration & Orchestration
- [ ] Step 4.1: Build orchestrator state machine (`src/wayfi/orchestrator.py`) — full 9-state control loop wiring all Phase 2+3 modules with asyncio
- [ ] Step 4.2: Build VPN per-network policy engine (`src/wayfi/vpn/manager.py`) — WireGuard/OpenVPN activation with always/never/ask policies
- [ ] Step 4.3: Build FastAPI web UI — app skeleton, status dashboard, and vault management routes (`src/wayfi/webui/app.py`, `routers/status.py`, `routers/vault.py`)
- [ ] Step 4.4: Build FastAPI web UI — network profiles, portal patterns, and calendar config routes (`routers/networks.py`, `routers/patterns.py`, `routers/calendar.py`)
- [ ] Step 4.5: Build FastAPI web UI — settings, logs, and frontend templates (`routers/settings.py`, `routers/logs.py`, `templates/`, `static/`)

### Phase 5: Deployment & Testing
- [ ] Step 5.1: Create systemd unit files for all services with dependency ordering and watchdog config (`scripts/systemd/`)
- [ ] Step 5.2: Create RPi provisioning script (`scripts/provision.sh`) — one-command setup from fresh Raspberry Pi OS Lite
- [ ] Step 5.3: Build mock portal test server (`tests/mock_portal/server.py`) with HTML fixtures for all 11 vendor patterns
- [ ] Step 5.4: Write unit tests for vault, portal detector, heuristic engine, scanner, speedtest, SMS, and calendar modules
- [ ] Step 5.5: Write integration tests — full orchestrator flow against mock portal server (heuristic path + LLM path)
- [ ] Step 5.6: Final validation — lint, type check, test suite green, verify all modules import cleanly, smoke test orchestrator startup sequence
