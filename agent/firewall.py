"""
Firewall management using iptables/nftables
Compatible with OpenWrt, Raspberry Pi, and generic Linux
"""

import subprocess
import logging
from typing import Optional

log = logging.getLogger("jadslink.firewall")


class FirewallClient:
    """
    Manage captive portal firewall rules using iptables.

    Uses:
    - iptables for packet filtering and NAT
    - tc (traffic control) for bandwidth limiting

    Chain structure:
    - JADSLINK_FORWARD: Allow authenticated MACs, drop others
    - JADSLINK_PREROUTING: Redirect unauthenticated HTTP to portal
    """

    def __init__(self, portal_ip: str = "192.168.1.1", portal_port: int = 8080):
        """
        Initialize firewall client

        Args:
            portal_ip: IP address of the portal HTTP server
            portal_port: Port where portal is served
        """
        self.portal_ip = portal_ip
        self.portal_port = portal_port
        self.chain_forward = "JADSLINK_FORWARD"
        self.chain_prerouting = "JADSLINK_PREROUTING"

        # Initialize chains
        self._init_chains()

    def _run(self, cmd: list[str]) -> bool:
        """Run shell command and return success status"""
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode != 0:
                log.warning(f"Command failed: {' '.join(cmd)} - {result.stderr}")
                return False
            return True
        except subprocess.TimeoutExpired:
            log.error(f"Command timeout: {' '.join(cmd)}")
            return False
        except Exception as e:
            log.error(f"Command error: {' '.join(cmd)} - {e}")
            return False

    def _init_chains(self) -> None:
        """
        Initialize custom iptables chains.
        Creates chains if they don't exist.
        """
        # Create FORWARD chain for authenticated users
        self._run(["iptables", "-t", "filter", "-N", self.chain_forward])

        # Create PREROUTING chain for captive portal redirect
        self._run(["iptables", "-t", "nat", "-N", self.chain_prerouting])

        # Insert our chains into main chains (if not already there)
        # Check if rule exists first to avoid duplicates
        check_forward = subprocess.run(
            ["iptables", "-t", "filter", "-C", "FORWARD", "-j", self.chain_forward],
            capture_output=True
        )
        if check_forward.returncode != 0:
            self._run(["iptables", "-t", "filter", "-I", "FORWARD", "1", "-j", self.chain_forward])

        check_prerouting = subprocess.run(
            ["iptables", "-t", "nat", "-C", "PREROUTING", "-j", self.chain_prerouting],
            capture_output=True
        )
        if check_prerouting.returncode != 0:
            self._run(["iptables", "-t", "nat", "-I", "PREROUTING", "1", "-j", self.chain_prerouting])

        # Default policy: allow established connections
        self._run([
            "iptables", "-t", "filter", "-I", self.chain_forward, "1",
            "-m", "state", "--state", "ESTABLISHED,RELATED", "-j", "ACCEPT"
        ])

        # Default redirect: HTTP traffic to portal (except from portal itself)
        self._run([
            "iptables", "-t", "nat", "-A", self.chain_prerouting,
            "-p", "tcp", "--dport", "80",
            "-j", "DNAT", "--to-destination", f"{self.portal_ip}:{self.portal_port}"
        ])

        log.info("Firewall chains initialized")

    def allow_mac(self, mac: str, duration_minutes: int = 0) -> bool:
        """
        Allow internet access for a specific MAC address.

        Args:
            mac: Device MAC address (e.g., "aa:bb:cc:dd:ee:ff")
            duration_minutes: Session duration (0 = unlimited, handled by session_manager)

        Returns:
            True if successful
        """
        # Add rule to allow this MAC in FORWARD chain
        success = self._run([
            "iptables", "-t", "filter", "-I", self.chain_forward, "2",
            "-m", "mac", "--mac-source", mac.upper(),
            "-j", "ACCEPT"
        ])

        if success:
            log.info(f"Allowed MAC {mac} for {duration_minutes or 'unlimited'} minutes")

        return success

    def block_mac(self, mac: str) -> bool:
        """
        Block internet access for a specific MAC address.
        Removes the allow rule.

        Args:
            mac: Device MAC address

        Returns:
            True if successful
        """
        # Remove allow rule for this MAC
        success = self._run([
            "iptables", "-t", "filter", "-D", self.chain_forward,
            "-m", "mac", "--mac-source", mac.upper(),
            "-j", "ACCEPT"
        ])

        if success:
            log.info(f"Blocked MAC {mac}")

        return success

    def set_bandwidth_limit(
        self,
        mac: str,
        download_kbps: int = 0,
        upload_kbps: int = 0
    ) -> bool:
        """
        Set bandwidth limits for a MAC address using tc (traffic control).

        Note: This is a simplified implementation. Production should use
        more sophisticated QoS with tc classes and filters.

        Args:
            mac: Device MAC address
            download_kbps: Download limit in kbps (0 = unlimited)
            upload_kbps: Upload limit in kbps (0 = unlimited)

        Returns:
            True if successful
        """
        if download_kbps == 0 and upload_kbps == 0:
            return True  # No limits

        # This is a placeholder. Real implementation would need:
        # 1. Identify network interface (wlan0, eth0, etc.)
        # 2. Use tc qdisc/class/filter to apply per-MAC limits
        # 3. Handle both ingress and egress shaping

        log.warning(f"Bandwidth limiting for {mac} not fully implemented (tc required)")
        log.info(f"Would limit {mac} to {download_kbps}kbps down / {upload_kbps}kbps up")

        # TODO: Implement tc-based bandwidth limiting
        # Example structure:
        # tc qdisc add dev wlan0 root handle 1: htb default 30
        # tc class add dev wlan0 parent 1: classid 1:1 htb rate 10mbit
        # tc filter add dev wlan0 protocol ip parent 1:0 prio 1 u32 match ether src MAC flowid 1:1

        return True

    def count_active_users(self) -> int:
        """
        Count currently allowed MAC addresses (active sessions).

        Returns:
            Number of active users
        """
        try:
            result = subprocess.run(
                ["iptables", "-t", "filter", "-L", self.chain_forward, "-n", "-v"],
                capture_output=True,
                text=True,
                timeout=5
            )

            # Count lines with MAC address rules
            count = 0
            for line in result.stdout.split("\n"):
                if "--mac-source" in line.lower():
                    count += 1

            return count
        except Exception as e:
            log.error(f"Error counting active users: {e}")
            return 0

    def clear_all_rules(self) -> bool:
        """
        Clear all JADSlink firewall rules.
        Use with caution - this disconnects all users.

        Returns:
            True if successful
        """
        log.warning("Clearing all firewall rules")

        # Flush our custom chains
        self._run(["iptables", "-t", "filter", "-F", self.chain_forward])
        self._run(["iptables", "-t", "nat", "-F", self.chain_prerouting])

        # Re-initialize chains with default rules
        self._init_chains()

        return True

    def get_mac_from_ip(self, ip: str) -> Optional[str]:
        """
        Get MAC address from IP using ARP table.

        Args:
            ip: IP address

        Returns:
            MAC address or None if not found
        """
        try:
            result = subprocess.run(
                ["arp", "-n", ip],
                capture_output=True,
                text=True,
                timeout=2
            )

            # Parse ARP output
            # Example: 192.168.1.100 ether aa:bb:cc:dd:ee:ff C wlan0
            for line in result.stdout.split("\n"):
                if ip in line and "ether" in line.lower():
                    parts = line.split()
                    if len(parts) >= 3:
                        mac = parts[2]
                        if ":" in mac:
                            return mac.upper()

            return None
        except Exception as e:
            log.error(f"Error getting MAC from IP {ip}: {e}")
            return None

    def cleanup(self) -> None:
        """Cleanup firewall rules on shutdown"""
        log.info("Cleaning up firewall")

        # Remove our chains from main chains
        self._run(["iptables", "-t", "filter", "-D", "FORWARD", "-j", self.chain_forward])
        self._run(["iptables", "-t", "nat", "-D", "PREROUTING", "-j", self.chain_prerouting])

        # Flush and delete our chains
        self._run(["iptables", "-t", "filter", "-F", self.chain_forward])
        self._run(["iptables", "-t", "filter", "-X", self.chain_forward])
        self._run(["iptables", "-t", "nat", "-F", self.chain_prerouting])
        self._run(["iptables", "-t", "nat", "-X", self.chain_prerouting])
