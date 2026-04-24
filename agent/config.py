"""Agent configuration — reads from .env file in the agent directory"""

import os
import subprocess
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Dict

log = logging.getLogger("jadslink.config")


class NetworkDetector:
    """
    Auto-detect network interfaces and IP addresses.
    Compatible with OpenWrt, Raspberry Pi, and generic Linux.
    """

    @staticmethod
    def _run_cmd(cmd: list[str]) -> Optional[str]:
        """Execute command and return stdout"""
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=2,
            )
            if result.returncode == 0:
                return result.stdout.strip()
            return None
        except Exception:
            return None

    @staticmethod
    def get_wan_interface() -> Optional[str]:
        """
        Detect WAN interface by checking default route.
        Works on OpenWrt and Linux.

        Returns:
            Interface name (e.g., "eth1", "wwan0") or None
        """
        # Method 1: Get default route interface
        output = NetworkDetector._run_cmd(["ip", "route", "get", "1.1.1.1"])
        if output:
            # Parse: "1.1.1.1 via 192.168.1.1 dev eth1 src 192.168.1.2"
            parts = output.split()
            if "dev" in parts:
                idx = parts.index("dev")
                if idx + 1 < len(parts):
                    return parts[idx + 1]

        # Method 2: Check main route table
        output = NetworkDetector._run_cmd(["ip", "route"])
        if output:
            for line in output.split("\n"):
                if line.startswith("default"):
                    parts = line.split()
                    if "dev" in parts:
                        idx = parts.index("dev")
                        if idx + 1 < len(parts):
                            return parts[idx + 1]

        # Fallback: common interface names
        for iface in ["eth1", "wwan0", "ppp0", "wan"]:
            output = NetworkDetector._run_cmd(["ip", "link", "show", iface])
            if output:
                return iface

        return None

    @staticmethod
    def get_lan_interface() -> Optional[str]:
        """
        Detect LAN interface.
        On OpenWrt, usually br-lan (bridge). On Linux, usually wlan0 or eth0.

        Returns:
            Interface name or None
        """
        # Check for OpenWrt bridge
        output = NetworkDetector._run_cmd(["ip", "link", "show", "br-lan"])
        if output:
            return "br-lan"

        # Check for common interface names
        for iface in ["wlan0", "eth0", "wlan1"]:
            output = NetworkDetector._run_cmd(["ip", "link", "show", iface])
            if output and "UP" in output:
                return iface

        return None

    @staticmethod
    def get_interface_ip(iface: str) -> Optional[str]:
        """
        Get IPv4 address of interface.

        Args:
            iface: Interface name

        Returns:
            IP address or None
        """
        output = NetworkDetector._run_cmd(["ip", "-4", "addr", "show", iface])
        if output:
            # Parse: "inet 192.168.1.1/24 brd 192.168.1.255"
            for line in output.split("\n"):
                if "inet " in line:
                    parts = line.split()
                    if len(parts) >= 2:
                        ip_with_mask = parts[1]
                        return ip_with_mask.split("/")[0]
        return None

    @staticmethod
    def detect_all() -> Dict[str, Optional[str]]:
        """
        Auto-detect all network parameters.

        Returns:
            {
                'wan_interface': str or None,
                'wan_ip': str or None,
                'lan_interface': str or None,
                'lan_ip': str or None,
                'router_ip': str or None  # Same as lan_ip
            }
        """
        wan_iface = NetworkDetector.get_wan_interface()
        wan_ip = NetworkDetector.get_interface_ip(wan_iface) if wan_iface else None

        lan_iface = NetworkDetector.get_lan_interface()
        lan_ip = NetworkDetector.get_interface_ip(lan_iface) if lan_iface else None

        result = {
            'wan_interface': wan_iface or "eth1",
            'wan_ip': wan_ip,
            'lan_interface': lan_iface or "br-lan",
            'lan_ip': lan_ip or "192.168.1.1",
            'router_ip': lan_ip or "192.168.1.1",  # Alias for lan_ip
        }

        # Log detection
        log.info(
            f"Network auto-detected: LAN={result['lan_interface']} ({result['router_ip']}), "
            f"WAN={result['wan_interface']} ({result['wan_ip'] or 'auto'})"
        )

        return result


@dataclass
class AgentConfig:
    """Configuration for JADSlink field agent"""

    # Node identity
    NODE_ID: str = os.getenv("NODE_ID", "")
    API_KEY: str = os.getenv("API_KEY", "")

    # Server communication
    SERVER_URL: str = os.getenv("SERVER_URL", "http://localhost:8000")
    HEARTBEAT_INTERVAL: int = int(os.getenv("HEARTBEAT_INTERVAL", "30"))
    SYNC_INTERVAL: int = int(os.getenv("SYNC_INTERVAL", "300"))  # 5 minutes
    EXPIRE_INTERVAL: int = int(os.getenv("EXPIRE_INTERVAL", "60"))

    # Network configuration (auto-detected if not set)
    ROUTER_IP: str = os.getenv("ROUTER_IP", "")  # Gateway IP
    LAN_INTERFACE: str = os.getenv("LAN_INTERFACE", "")  # LAN interface name
    WAN_INTERFACE: str = os.getenv("WAN_INTERFACE", "")  # WAN interface name
    PORTAL_PORT: int = int(os.getenv("PORTAL_PORT", "80"))  # HTTP port
    PORTAL_HOST: str = os.getenv("PORTAL_HOST", "0.0.0.0")  # Bind all interfaces
    MAX_BANDWIDTH_MBPS: int = int(os.getenv("MAX_BANDWIDTH_MBPS", "100"))  # Max total bandwidth

    # Cache
    CACHE_DIR: Path = Path(os.getenv("CACHE_DIR", ".cache"))

    def __post_init__(self):
        """Validate configuration and auto-detect network parameters"""
        if not self.NODE_ID:
            raise ValueError("NODE_ID must be set in .env or environment")
        if not self.API_KEY:
            raise ValueError("API_KEY must be set in .env or environment")

        # Auto-detect network parameters if not explicitly set
        network_info = NetworkDetector.detect_all()

        if not self.ROUTER_IP:
            self.ROUTER_IP = network_info['router_ip']

        if not self.LAN_INTERFACE:
            self.LAN_INTERFACE = network_info['lan_interface']

        if not self.WAN_INTERFACE:
            self.WAN_INTERFACE = network_info['wan_interface']

        # Create cache directory if it doesn't exist
        self.CACHE_DIR.mkdir(parents=True, exist_ok=True)

    @property
    def cache_db_path(self) -> Path:
        """Path to local SQLite cache database"""
        return self.CACHE_DIR / "tickets.db"
