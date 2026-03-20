#!/usr/bin/env bash
set -euo pipefail

# Setup script for recommended Claude Code plugins
# Run: bash scripts/setup-plugins.sh

BOLD='\033[1m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
NC='\033[0m'

info()  { echo -e "${BOLD}[INFO]${NC} $*"; }
ok()    { echo -e "${GREEN}[OK]${NC} $*"; }
warn()  { echo -e "${YELLOW}[WARN]${NC} $*"; }
fail()  { echo -e "${RED}[FAIL]${NC} $*"; }

echo ""
echo -e "${BOLD}=== Claude Code Plugin Setup ===${NC}"
echo ""

# --- Destructive Command Guard (dcg) ---
echo -e "${BOLD}1. Destructive Command Guard (dcg)${NC}"
echo "   Blocks dangerous commands before execution"
echo "   https://github.com/Dicklesworthstone/destructive_command_guard"
echo ""

if command -v dcg &>/dev/null; then
    ok "dcg is already installed: $(dcg --version 2>/dev/null || echo 'version unknown')"
else
    info "Installing dcg..."
    if curl -fsSL "https://raw.githubusercontent.com/Dicklesworthstone/destructive_command_guard/master/install.sh?$(date +%s)" | bash -s -- --easy-mode; then
        ok "dcg installed successfully"
    else
        fail "dcg installation failed — install manually:"
        echo "   curl -fsSL https://raw.githubusercontent.com/Dicklesworthstone/destructive_command_guard/master/install.sh | bash -s -- --easy-mode"
    fi
fi

echo ""

# --- Claude-Mem ---
echo -e "${BOLD}2. Claude-Mem${NC}"
echo "   Persistent memory across Claude Code sessions"
echo "   https://github.com/thedotmack/claude-mem"
echo ""

if [ -d "$HOME/.claude-mem" ]; then
    ok "claude-mem appears to be installed (~/.claude-mem exists)"
else
    info "Claude-Mem requires installation from within a Claude Code session."
    info "Run these commands inside Claude Code:"
    echo ""
    echo "   /plugin marketplace add thedotmack/claude-mem"
    echo "   /plugin install claude-mem"
    echo ""
    warn "Cannot auto-install claude-mem outside of Claude Code"
fi

echo ""

# --- Summary ---
echo -e "${BOLD}=== Setup Summary ===${NC}"
echo ""

if command -v dcg &>/dev/null; then
    ok "dcg: installed"
    dcg status 2>/dev/null || true
else
    warn "dcg: not found in PATH (may need shell restart)"
fi

if [ -d "$HOME/.claude-mem" ]; then
    ok "claude-mem: installed"
else
    warn "claude-mem: install from within Claude Code session"
fi

# --- Gitleaks Pre-commit Hook ---
echo -e "${BOLD}3. Gitleaks Secret Scanning${NC}"
echo "   Pre-commit hook to block secrets from being committed"
echo "   https://github.com/gitleaks/gitleaks"
echo ""

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [ -f "$SCRIPT_DIR/setup-gitleaks-hook.sh" ]; then
    bash "$SCRIPT_DIR/setup-gitleaks-hook.sh"
else
    warn "setup-gitleaks-hook.sh not found — run it separately:"
    echo "   bash scripts/setup-gitleaks-hook.sh"
fi

echo ""
info "See docs/plugins.md for configuration details"
echo ""
