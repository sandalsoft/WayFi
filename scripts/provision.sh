#!/usr/bin/env bash
# WayFi Raspberry Pi 5 provisioning script
# Run on a fresh Raspberry Pi OS Lite (Bookworm 64-bit) installation
# Usage: sudo bash scripts/provision.sh

set -euo pipefail

WAYFI_DIR="/opt/wayfi"
MODEL_DIR="${WAYFI_DIR}/models"
MODEL_URL="https://huggingface.co/TheBloke/Llama-2-7B-Chat-GGUF/resolve/main/llama-2-7b-chat.Q4_K_M.gguf"
LLAMA_CPP_REPO="https://github.com/ggerganov/llama.cpp.git"

echo "========================================="
echo "  WayFi Provisioning Script"
echo "========================================="

# Check root
if [[ $EUID -ne 0 ]]; then
    echo "This script must be run as root (sudo)"
    exit 1
fi

# Check architecture
ARCH=$(uname -m)
if [[ "$ARCH" != "aarch64" ]]; then
    echo "Warning: Expected aarch64 (Raspberry Pi), got $ARCH"
    echo "Continuing anyway..."
fi

echo ""
echo "[1/9] Updating system packages..."
apt-get update -qq
apt-get upgrade -y -qq

echo ""
echo "[2/9] Installing system dependencies..."
apt-get install -y -qq \
    hostapd \
    dnsmasq \
    wpasupplicant \
    wireguard \
    openvpn \
    python3 \
    python3-pip \
    python3-venv \
    cmake \
    build-essential \
    git \
    iptables \
    iw \
    wireless-tools \
    curl

echo ""
echo "[3/9] Setting up WayFi directory..."
mkdir -p "${WAYFI_DIR}"
mkdir -p "${MODEL_DIR}"
mkdir -p /var/lib/wayfi
mkdir -p /var/log/wayfi

# Copy project files
if [[ -d "$(dirname "$0")/../src" ]]; then
    cp -r "$(dirname "$0")/.." "${WAYFI_DIR}/"
fi

echo ""
echo "[4/9] Installing Python package..."
cd "${WAYFI_DIR}"
pip3 install --break-system-packages -e ".[dev]" 2>/dev/null || pip3 install -e ".[dev]"

# Install Playwright browsers (ARM64)
echo ""
echo "[5/9] Installing Playwright (ARM64 Chromium)..."
python3 -m playwright install chromium 2>/dev/null || echo "Playwright install skipped (may need manual setup on ARM64)"

echo ""
echo "[6/9] Building llama.cpp..."
if [[ ! -f /usr/local/bin/llama-server ]]; then
    TMPDIR=$(mktemp -d)
    git clone --depth 1 "${LLAMA_CPP_REPO}" "${TMPDIR}/llama.cpp"
    cd "${TMPDIR}/llama.cpp"
    mkdir build && cd build
    cmake .. -DGGML_NEON=ON -DCMAKE_BUILD_TYPE=Release
    cmake --build . --config Release -j$(nproc)
    cp bin/llama-server /usr/local/bin/
    cd "${WAYFI_DIR}"
    rm -rf "${TMPDIR}"
    echo "llama.cpp built and installed"
else
    echo "llama-server already installed, skipping"
fi

echo ""
echo "[7/9] Configuring system..."

# Enable IP forwarding
echo "net.ipv4.ip_forward=1" > /etc/sysctl.d/99-wayfi.conf
sysctl -p /etc/sysctl.d/99-wayfi.conf

# CPU governor: performance
echo "performance" | tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor 2>/dev/null || true

# Mask unnecessary services
systemctl mask bluetooth.service 2>/dev/null || true
systemctl mask hciuart.service 2>/dev/null || true

# tmpfs for transient data
if ! grep -q "wayfi-tmp" /etc/fstab; then
    echo "tmpfs /tmp tmpfs defaults,noatime,nosuid,size=256m 0 0  # wayfi-tmp" >> /etc/fstab
fi

# Stop default hostapd/dnsmasq (we manage our own)
systemctl stop hostapd 2>/dev/null || true
systemctl stop dnsmasq 2>/dev/null || true
systemctl disable hostapd 2>/dev/null || true
systemctl disable dnsmasq 2>/dev/null || true

echo ""
echo "[8/9] Installing systemd service units..."
cp "${WAYFI_DIR}/scripts/systemd/"*.service /etc/systemd/system/
systemctl daemon-reload

# Enable services
systemctl enable wayfi-hostapd.service
systemctl enable wayfi-dnsmasq.service
systemctl enable wayfi-llm.service
systemctl enable wayfi-orchestrator.service
systemctl enable wayfi-webui.service
systemctl enable wayfi-calendar.service
systemctl enable wayfi-notifier.service

echo ""
echo "[9/9] Setting up git hooks..."
if [[ -f "${WAYFI_DIR}/scripts/setup-gitleaks-hook.sh" ]]; then
    bash "${WAYFI_DIR}/scripts/setup-gitleaks-hook.sh" 2>/dev/null || true
fi

echo ""
echo "========================================="
echo "  Provisioning complete!"
echo "========================================="
echo ""
echo "Next steps:"
echo "  1. Download a GGUF model to ${MODEL_DIR}/"
echo "  2. Configure WiFi interfaces in config/wayfi.yaml"
echo "  3. Set up credentials via the web UI at 192.168.8.1"
echo "  4. Start services: sudo systemctl start wayfi-orchestrator"
echo ""
echo "Or reboot to start everything automatically."
