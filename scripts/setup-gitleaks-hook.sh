#!/usr/bin/env bash
set -euo pipefail

# Installs gitleaks CLI and activates the tracked .githooks/ directory.
# Run: bash scripts/setup-gitleaks-hook.sh

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
echo -e "${BOLD}=== Gitleaks Pre-commit Hook Setup ===${NC}"
echo ""

# --- 1. Install gitleaks CLI ---
echo -e "${BOLD}1. Gitleaks CLI${NC}"
echo "   https://github.com/gitleaks/gitleaks"
echo ""

if command -v gitleaks &>/dev/null; then
    ok "gitleaks is already installed: $(gitleaks version 2>/dev/null || echo 'version unknown')"
else
    info "Installing gitleaks..."

    # Try brew first (macOS/Linux), then the official install script
    if command -v brew &>/dev/null; then
        if brew install gitleaks 2>/dev/null; then
            ok "gitleaks installed via Homebrew"
        else
            fail "Homebrew install failed"
        fi
    fi

    # Check again in case brew succeeded
    if ! command -v gitleaks &>/dev/null; then
        if curl -sSfL https://raw.githubusercontent.com/gitleaks/gitleaks/master/scripts/install.sh | bash -s -- -b /usr/local/bin 2>/dev/null; then
            ok "gitleaks installed via install script"
        else
            fail "Automatic installation failed. Install manually:"
            echo "   brew install gitleaks"
            echo "   # or: go install github.com/gitleaks/gitleaks/v8@latest"
            echo "   # or: https://github.com/gitleaks/gitleaks/releases"
        fi
    fi
fi

echo ""

# --- 2. Activate tracked hooks directory ---
echo -e "${BOLD}2. Activate Pre-commit Hook${NC}"
echo ""

REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || echo "")"
if [ -z "$REPO_ROOT" ]; then
    fail "Not inside a git repository. Run this from within a repo."
    exit 1
fi

HOOKS_DIR="$REPO_ROOT/.githooks"
if [ ! -f "$HOOKS_DIR/pre-commit" ]; then
    fail ".githooks/pre-commit not found — is this the right repo?"
    exit 1
fi

CURRENT_HOOKS_PATH="$(git config --local core.hooksPath 2>/dev/null || echo "")"
if [ "$CURRENT_HOOKS_PATH" = ".githooks" ]; then
    ok "core.hooksPath already set to .githooks"
else
    git config --local core.hooksPath .githooks
    ok "core.hooksPath set to .githooks"
fi

echo ""

# --- Summary ---
echo -e "${BOLD}=== Setup Summary ===${NC}"
echo ""

if command -v gitleaks &>/dev/null; then
    ok "gitleaks CLI: installed ($(gitleaks version 2>/dev/null || echo '?'))"
else
    warn "gitleaks CLI: not found — hook will warn but not block"
fi

ACTIVE_PATH="$(git config --local core.hooksPath 2>/dev/null || echo "")"
if [ "$ACTIVE_PATH" = ".githooks" ]; then
    ok "pre-commit hook: active (.githooks/pre-commit)"
else
    warn "pre-commit hook: not configured"
fi

echo ""
info "Secrets will be blocked before commit. To customize, edit .gitleaks.toml"
echo ""
