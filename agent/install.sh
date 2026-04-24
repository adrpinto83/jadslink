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

# Detect OS and package manager
detect_os_and_pm() {
    if [ -f /etc/openwrt_release ]; then
        OS="openwrt"
        PM="opkg"
        echo "Detected: OpenWrt"
    elif command -v apt-get >/dev/null 2>&1; then
        OS="debian"
        PM="apt"
        . /etc/os-release
        echo "Detected: $PRETTY_NAME"
    elif command -v yum >/dev/null 2>&1; then
        OS="rhel"
        PM="yum"
        echo "Detected: RHEL-based"
    elif command -v apk >/dev/null 2>&1; then
        OS="alpine"
        PM="apk"
        echo "Detected: Alpine Linux"
    else
        echo "WARNING: Could not detect OS, assuming Debian-based"
        OS="debian"
        PM="apt"
    fi
}

detect_os_and_pm

# Check if .ipk package is available (OpenWrt only)
install_openwrt_package() {
    echo ""
    echo "[1/6] Checking for JADSlink Agent package..."

    # Look for .ipk in current directory
    ipk_file=$(find . -maxdepth 2 -name "jadslink-agent*.ipk" 2>/dev/null | head -1)

    if [ -z "$ipk_file" ]; then
        return 1  # No .ipk found
    fi

    echo "Found JADSlink Agent package: $ipk_file"
    echo ""
    echo "Installing via opkg (native OpenWrt package)..."

    # Update package list
    opkg update

    # Install dependencies
    opkg install python3 python3-requests python3-schedule \
        tc kmod-ifb kmod-sched-core kmod-sched-htb \
        iptables-mod-conntrack-extra

    # Install the .ipk
    if opkg install "$ipk_file"; then
        echo ""
        echo "Package installed successfully!"
        echo ""
        echo "Next steps:"
        echo "1. Configure the agent:"
        echo "   uci set jadslink.agent.node_id='YOUR_NODE_ID'"
        echo "   uci set jadslink.agent.api_key='YOUR_API_KEY'"
        echo "   uci commit jadslink"
        echo ""
        echo "2. Start the service:"
        echo "   /etc/init.d/jadslink start"
        echo "   /etc/init.d/jadslink enable"
        echo ""
        echo "3. Check logs:"
        echo "   logread -f | grep jadslink"
        echo ""
        return 0
    else
        echo "WARNING: Package installation failed, falling back to manual install"
        return 1
    fi
}

# Try OpenWrt package installation first
if [ "$OS" = "openwrt" ]; then
    if install_openwrt_package; then
        exit 0
    fi
fi

# Fallback to manual installation for non-OpenWrt or if .ipk not found
echo ""
echo "[1/6] Installing dependencies..."

if [ "$OS" = "openwrt" ]; then
    echo "Using manual installation (no .ipk package found)"
    opkg update
    opkg install python3 python3-pip iptables-mod-ipopt
elif [ "$PM" = "apt" ]; then
    apt-get update
    apt-get install -y python3 python3-pip iptables
elif [ "$PM" = "yum" ]; then
    yum install -y python3 python3-pip iptables
elif [ "$PM" = "apk" ]; then
    apk add --no-cache python3 py3-pip iptables
else
    echo "WARNING: Unknown package manager, skipping dependency installation"
fi

# Install Python dependencies
echo ""
echo "[2/6] Installing Python packages..."

if [ -f "requirements.txt" ]; then
    if [ "$PM" = "apt" ]; then
        pip3 install -r requirements.txt
    elif [ "$PM" = "opkg" ]; then
        # OpenWrt pip3 may not be available, install manually
        python3 -m pip install -r requirements.txt || {
            echo "WARNING: pip install failed, installing packages manually"
            python3 -m ensurepip --default-pip 2>/dev/null || true
            python3 -m pip install -r requirements.txt
        }
    else
        pip3 install -r requirements.txt
    fi
else
    echo "WARNING: requirements.txt not found, skipping pip install"
fi

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

# Network (auto-detected if not set)
ROUTER_IP=
LAN_INTERFACE=
WAN_INTERFACE=
PORTAL_PORT=80
PORTAL_HOST=0.0.0.0

# Intervals (seconds)
HEARTBEAT_INTERVAL=30
SYNC_INTERVAL=300
EXPIRE_INTERVAL=60

# Cache
CACHE_DIR=/opt/jadslink/.cache

# Max Bandwidth (Mbps)
MAX_BANDWIDTH_MBPS=100
EOF

    echo ""
    echo "IMPORTANT: Edit $INSTALL_DIR/.env and set NODE_ID and API_KEY"
    echo "           These values are provided when you create a node in the dashboard."
    echo ""
    echo "           Network interfaces are auto-detected, but you can override them if needed."
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
