#!/bin/bash
#
# JADSlink Agent Installer
# Compatible with: OpenWrt 22.03+, Raspberry Pi OS, Ubuntu/Debian
#
# Usage:
#   chmod +x install.sh
#   sudo ./install.sh
#

set -e  # Exit on error

echo "==================================="
echo "  JADSlink Agent Installer"
echo "==================================="
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "ERROR: This script must be run as root (use sudo)"
    exit 1
fi

# Detect OS
if [ -f /etc/openwrt_release ]; then
    OS="openwrt"
    echo "Detected: OpenWrt"
elif [ -f /etc/os-release ]; then
    . /etc/os-release
    OS="$ID"
    echo "Detected: $PRETTY_NAME"
else
    echo "WARNING: Could not detect OS, assuming Debian-based"
    OS="debian"
fi

# Install dependencies
echo ""
echo "[1/6] Installing dependencies..."

if [ "$OS" = "openwrt" ]; then
    opkg update
    opkg install python3 python3-pip iptables-mod-ipopt
elif [ "$OS" = "debian" ] || [ "$OS" = "ubuntu" ] || [ "$OS" = "raspbian" ]; then
    apt-get update
    apt-get install -y python3 python3-pip iptables
else
    echo "WARNING: Unknown OS, skipping package installation"
fi

# Install Python dependencies
echo ""
echo "[2/6] Installing Python packages..."
pip3 install -r requirements.txt

# Create agent directory
INSTALL_DIR="/opt/jadslink"
echo ""
echo "[3/6] Creating installation directory: $INSTALL_DIR"
mkdir -p "$INSTALL_DIR"
cp -r . "$INSTALL_DIR/"
cd "$INSTALL_DIR"

# Create cache directory
mkdir -p "$INSTALL_DIR/.cache"

# Create .env file if it doesn't exist
if [ ! -f "$INSTALL_DIR/.env" ]; then
    echo ""
    echo "[4/6] Creating .env configuration file..."
    cat > "$INSTALL_DIR/.env" << 'EOF'
# JADSlink Agent Configuration
# Copy from backend when creating node

# Node Identity (REQUIRED)
NODE_ID=
API_KEY=

# Server
SERVER_URL=https://api.jadslink.io

# Network
ROUTER_IP=192.168.1.1
PORTAL_PORT=80
PORTAL_HOST=0.0.0.0

# Intervals (seconds)
HEARTBEAT_INTERVAL=30
SYNC_INTERVAL=300
EXPIRE_INTERVAL=60

# Cache
CACHE_DIR=/opt/jadslink/.cache
EOF

    echo ""
    echo "IMPORTANT: Edit /opt/jadslink/.env and set NODE_ID and API_KEY"
    echo "           These values are provided when you create a node in the dashboard."
else
    echo ""
    echo "[4/6] .env file already exists, skipping..."
fi

# Install systemd service
if command -v systemctl &> /dev/null; then
    echo ""
    echo "[5/6] Installing systemd service..."

    cat > /etc/systemd/system/jadslink.service << EOF
[Unit]
Description=JADSlink Agent
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/jadslink
ExecStart=/usr/bin/python3 /opt/jadslink/agent.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

# Environment
Environment="PYTHONUNBUFFERED=1"

[Install]
WantedBy=multi-user.target
EOF

    # Reload systemd
    systemctl daemon-reload

    echo ""
    echo "Systemd service installed: jadslink.service"
    echo "  Start:   sudo systemctl start jadslink"
    echo "  Enable:  sudo systemctl enable jadslink"
    echo "  Status:  sudo systemctl status jadslink"
    echo "  Logs:    sudo journalctl -u jadslink -f"

elif [ "$OS" = "openwrt" ]; then
    echo ""
    echo "[5/6] Installing OpenWrt init script..."

    cat > /etc/init.d/jadslink << 'EOF'
#!/bin/sh /etc/rc.common

START=99
STOP=10

USE_PROCD=1
PROG=/usr/bin/python3
AGENT=/opt/jadslink/agent.py

start_service() {
    procd_open_instance
    procd_set_param command $PROG $AGENT
    procd_set_param respawn
    procd_set_param stdout 1
    procd_set_param stderr 1
    procd_close_instance
}
EOF

    chmod +x /etc/init.d/jadslink

    echo ""
    echo "OpenWrt init script installed: /etc/init.d/jadslink"
    echo "  Start:   /etc/init.d/jadslink start"
    echo "  Enable:  /etc/init.d/jadslink enable"
    echo "  Status:  /etc/init.d/jadslink status"

else
    echo ""
    echo "[5/6] No init system detected, skipping service installation"
    echo "      Run manually: python3 /opt/jadslink/agent.py"
fi

# Setup iptables persistence
echo ""
echo "[6/6] Configuring firewall persistence..."

if [ "$OS" = "openwrt" ]; then
    echo "  OpenWrt manages iptables automatically via /etc/config/firewall"
elif command -v iptables-save &> /dev/null && command -v netfilter-persistent &> /dev/null; then
    apt-get install -y iptables-persistent
    echo "  Installed iptables-persistent for firewall rule persistence"
else
    echo "  WARNING: Install iptables-persistent to save rules across reboots"
    echo "           sudo apt-get install iptables-persistent"
fi

# Final instructions
echo ""
echo "==================================="
echo "  Installation Complete!"
echo "==================================="
echo ""
echo "Next steps:"
echo "  1. Edit /opt/jadslink/.env and set NODE_ID and API_KEY"
echo "  2. Start the service:"
if command -v systemctl &> /dev/null; then
    echo "       sudo systemctl start jadslink"
    echo "       sudo systemctl enable jadslink"
elif [ "$OS" = "openwrt" ]; then
    echo "       /etc/init.d/jadslink start"
    echo "       /etc/init.d/jadslink enable"
else
    echo "       python3 /opt/jadslink/agent.py"
fi
echo ""
echo "  3. Check logs:"
if command -v systemctl &> /dev/null; then
    echo "       sudo journalctl -u jadslink -f"
elif [ "$OS" = "openwrt" ]; then
    echo "       logread -f | grep jadslink"
fi
echo ""
echo "Documentation: https://github.com/adrpinto83/jadslink"
echo ""
