# JADSlink Agent - Field Node Software

Python agent that runs on field hardware (OpenWrt routers, Raspberry Pi) to manage captive portal and internet access control.

## Features

- **Captive Portal**: Ultralight HTTP server (< 40KB) for ticket activation
- **Firewall Management**: iptables-based session control
- **Offline Operation**: SQLite cache for activations without internet
- **Auto-Sync**: Periodic synchronization with backend
- **Low Resource**: < 20MB RAM, < 5% CPU on idle

## Supported Hardware

- **GL.iNet GL-MT3000** (OpenWrt 22.03+)
- **Raspberry Pi** (3B+, 4, Zero 2W) with Raspberry Pi OS
- **Generic Linux** (Ubuntu, Debian) with iptables

## Installation

### Quick Install

```bash
# Download agent files to target device
git clone https://github.com/adrpinto83/jadslink.git
cd jadslink/agent

# Run installer
sudo ./install.sh
```

### Manual Installation

```bash
# Install dependencies
pip3 install -r requirements.txt

# Copy config template
cp .env.example .env

# Edit config with your NODE_ID and API_KEY
nano .env

# Run agent
python3 agent.py
```

## Configuration

All configuration is in `.env` file:

```bash
# Node credentials (from dashboard)
NODE_ID=your-node-uuid
API_KEY=your-api-key

# Server URL
SERVER_URL=https://api.jadslink.io

# Network
ROUTER_IP=192.168.1.1       # Gateway IP
PORTAL_PORT=80              # HTTP port
PORTAL_HOST=0.0.0.0         # Bind all interfaces

# Intervals (seconds)
HEARTBEAT_INTERVAL=30       # Heartbeat frequency
SYNC_INTERVAL=300           # Ticket sync frequency
EXPIRE_INTERVAL=60          # Session expiration check
```

## Architecture

```
┌─────────────────────────────────────────┐
│           JADSlink Agent                │
│                                         │
│  ┌───────────┐      ┌──────────────┐  │
│  │ Portal    │      │  Firewall    │  │
│  │ HTTP:80   │◄────►│  (iptables)  │  │
│  └───────────┘      └──────────────┘  │
│        │                    │          │
│        ↓                    ↓          │
│  ┌───────────────────────────────┐    │
│  │     Session Manager           │    │
│  │  - Activate tickets           │    │
│  │  - Expire sessions            │    │
│  │  - Offline cache (SQLite)     │    │
│  └───────────────────────────────┘    │
│                │                       │
│                ↓                       │
│  ┌───────────────────────────────┐    │
│  │     Server Sync               │    │
│  │  - Heartbeat every 30s        │    │
│  │  - Sync tickets every 5min    │    │
│  │  - Report activations         │    │
│  └───────────────────────────────┘    │
│                │                       │
└────────────────┼───────────────────────┘
                 │ HTTPS
                 ↓
        JADSlink API Server
```

## Components

### agent.py
Main entry point. Coordinates all components and runs scheduled tasks.

### firewall.py
Manages iptables rules for:
- Allowing authenticated MAC addresses
- Blocking unauthenticated traffic
- Redirecting HTTP to captive portal
- (Optional) Bandwidth limiting with tc

### portal.py
Minimal HTTP server serving captive portal HTML and handling ticket activation.

### session_manager.py
Handles ticket activation and session expiration logic.

### sync.py
HTTP client for communicating with backend API.

### cache.py
SQLite-based local cache for offline operation.

### config.py
Configuration management from .env file.

## Usage

### Systemd (Linux)

```bash
# Start service
sudo systemctl start jadslink

# Enable auto-start on boot
sudo systemctl enable jadslink

# Check status
sudo systemctl status jadslink

# View logs
sudo journalctl -u jadslink -f
```

### OpenWrt

```bash
# Start service
/etc/init.d/jadslink start

# Enable auto-start
/etc/init.d/jadslink enable

# Check logs
logread -f | grep jadslink
```

### Manual Run

```bash
python3 agent.py
```

## Firewall Rules

The agent creates custom iptables chains:

- `JADSLINK_FORWARD` (filter table): Allow authenticated MACs
- `JADSLINK_PREROUTING` (nat table): Redirect HTTP to portal

To view rules:

```bash
# View filter rules
sudo iptables -t filter -L JADSLINK_FORWARD -n -v

# View NAT rules
sudo iptables -t nat -L JADSLINK_PREROUTING -n -v

# Count active sessions
sudo iptables -t filter -L JADSLINK_FORWARD -n -v | grep -c "mac-source"
```

## Offline Operation

The agent can activate tickets even without internet connection:

1. Tickets are synced from server every 5 minutes
2. Cached locally in SQLite database (`.cache/tickets.db`)
3. Activations are queued and synced when connection is restored

## Troubleshooting

### Agent won't start

```bash
# Check logs
sudo journalctl -u jadslink -n 50

# Verify configuration
cat /opt/jadslink/.env

# Test manually
cd /opt/jadslink
python3 agent.py
```

### Portal not accessible

```bash
# Check if port 80 is in use
sudo netstat -tulpn | grep :80

# Test portal locally
curl http://localhost:80

# Check firewall rules
sudo iptables -t nat -L JADSLINK_PREROUTING -n -v
```

### Sessions not expiring

```bash
# Check scheduler is running
sudo journalctl -u jadslink | grep "expire"

# Manually trigger expiration
python3 -c "from session_manager import *; from cache import *; from firewall import *; \
  sm = SessionManager(TicketCache(), FirewallClient()); print(sm.expire_overdue())"
```

### No internet after activation

```bash
# Check firewall allows MAC
sudo iptables -t filter -L JADSLINK_FORWARD -n -v

# Check routing
ip route show

# Check DNS
cat /etc/resolv.conf
```

## Performance

Expected resource usage:

- **RAM**: 15-25 MB
- **CPU (idle)**: < 5%
- **CPU (activation)**: 10-15% spike
- **Disk**: < 10 MB (including cache)
- **Network**: ~1 KB/s average (heartbeat + sync)

## Security

- All API communication uses HTTPS
- API key authentication for all server requests
- No passwords stored locally
- iptables rules isolated in custom chains
- SQLite database file permissions: 600 (root only)

## Development

### Run tests

```bash
# No tests yet - coming in FASE 6
```

### Debug mode

```bash
# Run with debug logging
python3 agent.py --log-level DEBUG
```

## Support

- GitHub Issues: https://github.com/adrpinto83/jadslink/issues
- Documentation: See `/docs` folder
- Contact: JADS Studio — Venezuela

## License

Proprietary - JADS Studio
