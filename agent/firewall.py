"""
Firewall management using iptables/nftables
Compatible with OpenWrt, Raspberry Pi, and generic Linux
"""

import subprocess
import logging
from typing import Optional
import re

log = logging.getLogger("jadslink.firewall")


class TrafficControl:
    """
    Manage bandwidth limiting using tc (Traffic Control).
    Uses HTB (Hierarchical Token Bucket) for egress shaping and
    IFB (Intermediate Functional Block) for ingress shaping.

    Architecture:
    - Egress (upload): HTB on WAN interface
    - Ingress (download): IFB redirect with HTB
    """

    def __init__(self, wan_interface: str = "eth1"):
        """
        Initialize traffic control.

        Args:
            wan_interface: WAN interface name (eth1, wwan0, etc.)
        """
        self.wan_interface = wan_interface
        self.ifb_interface = "ifb0"
        self.root_handle = "1:"
        self.parent_class = "1:1"
        self.default_class = "1:9999"
        self.session_class_offset = 100  # Start assigning 1:100, 1:101, etc.
        self.mac_to_classid = {}  # Map MAC -> classid for cleanup

    def _run(self, cmd: list[str]) -> bool:
        """Execute command and return success status"""
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode != 0:
                log.warning(f"tc command failed: {' '.join(cmd)} - {result.stderr}")
                return False
            return True
        except subprocess.TimeoutExpired:
            log.error(f"tc command timeout: {' '.join(cmd)}")
            return False
        except Exception as e:
            log.error(f"tc command error: {' '.join(cmd)} - {e}")
            return False

    def _run_output(self, cmd: list[str]) -> Optional[str]:
        """Execute command and return stdout"""
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0:
                return result.stdout
            return None
        except Exception:
            return None

    def setup_egress_shaping(self, max_rate_mbps: int = 50) -> bool:
        """
        Setup HTB qdisc on WAN interface for egress (upload) shaping.

        Args:
            max_rate_mbps: Maximum total bandwidth in Mbps

        Returns:
            True if successful
        """
        # Check if qdisc already exists
        output = self._run_output(["tc", "qdisc", "show", "dev", self.wan_interface])
        if output and "htb" in output:
            log.info(f"HTB qdisc already configured on {self.wan_interface}")
            return True

        # Create root HTB qdisc
        if not self._run([
            "tc", "qdisc", "add", "dev", self.wan_interface, "root",
            "handle", self.root_handle, "htb", "default", self.default_class
        ]):
            return False

        # Create parent class with max rate
        if not self._run([
            "tc", "class", "add", "dev", self.wan_interface,
            "parent", f"{self.root_handle}", "classid", self.parent_class,
            "htb", f"rate={max_rate_mbps}mbit"
        ]):
            return False

        # Create default class (no limit)
        if not self._run([
            "tc", "class", "add", "dev", self.wan_interface,
            "parent", self.parent_class, "classid", f"1:{self.default_class.split(':')[1]}",
            "htb", f"rate={max_rate_mbps}mbit"
        ]):
            return False

        log.info(f"Egress shaping setup on {self.wan_interface} ({max_rate_mbps}Mbps)")
        return True

    def setup_ingress_shaping(self) -> bool:
        """
        Setup IFB interface and ingress redirect for ingress (download) shaping.

        Returns:
            True if successful
        """
        # Check if IFB already exists
        output = self._run_output(["ip", "link", "show", self.ifb_interface])
        if output:
            log.info(f"IFB interface {self.ifb_interface} already configured")
        else:
            # Load IFB kernel module
            subprocess.run(["modprobe", "ifb"], capture_output=True)

            # Create IFB interface
            if not self._run(["ip", "link", "add", self.ifb_interface, "type", "ifb"]):
                log.warning("Failed to create IFB interface")
                return False

            # Enable IFB interface
            if not self._run(["ip", "link", "set", self.ifb_interface, "up"]):
                log.warning("Failed to enable IFB interface")
                return False

        # Add ingress qdisc to WAN interface (if not exists)
        output = self._run_output(["tc", "qdisc", "show", "dev", self.wan_interface, "ingress"])
        if not output or "ingress" not in output:
            self._run(["tc", "qdisc", "add", "dev", self.wan_interface, "ingress"])

        # Add mirred filter to redirect ingress to IFB
        self._run([
            "tc", "filter", "add", "dev", self.wan_interface,
            "parent", "ffff:", "protocol", "ip",
            "u32", "match", "u32", "0", "0",
            "flowid", "1:1",
            "action", "mirred", "egress", "redirect", "dev", self.ifb_interface
        ])

        # Setup HTB on IFB (similar to egress)
        self._run([
            "tc", "qdisc", "add", "dev", self.ifb_interface, "root",
            "handle", self.root_handle, "htb", "default", self.default_class
        ])

        self._run([
            "tc", "class", "add", "dev", self.ifb_interface,
            "parent", f"{self.root_handle}", "classid", self.parent_class,
            "htb", "rate", "1gbit"  # No limit on ingress parent
        ])

        self._run([
            "tc", "class", "add", "dev", self.ifb_interface,
            "parent", self.parent_class, "classid", f"1:{self.default_class.split(':')[1]}",
            "htb", "rate", "1gbit"
        ])

        log.info("Ingress shaping setup via IFB interface")
        return True

    def add_session_limit(self, mac: str, download_mbps: int, upload_mbps: int) -> bool:
        """
        Add bandwidth limit for a MAC address.

        Args:
            mac: MAC address (aa:bb:cc:dd:ee:ff)
            download_mbps: Download limit in Mbps (0 = unlimited)
            upload_mbps: Upload limit in Mbps (0 = unlimited)

        Returns:
            True if successful
        """
        if mac in self.mac_to_classid:
            log.warning(f"MAC {mac} already has bandwidth limit, removing old rule")
            self.remove_session_limit(mac)

        # Allocate next classid
        classid = self.session_class_offset + len(self.mac_to_classid)
        full_classid = f"1:{classid}"

        # Egress (upload) limit
        if upload_mbps > 0:
            # Create class for upload
            if not self._run([
                "tc", "class", "add", "dev", self.wan_interface,
                "parent", self.parent_class, "classid", full_classid,
                "htb", f"rate={upload_mbps}mbit"
            ]):
                log.error(f"Failed to create upload class for {mac}")
                return False

            # Add u32 filter by source MAC
            mac_hex = self._mac_to_u32_match(mac)
            if not self._run([
                "tc", "filter", "add", "dev", self.wan_interface,
                "parent", f"{self.root_handle}", "protocol", "ip",
                "u32", mac_hex, "flowid", full_classid
            ]):
                log.error(f"Failed to add upload filter for {mac}")
                return False

        # Ingress (download) limit
        if download_mbps > 0:
            # Create class on IFB for download
            if not self._run([
                "tc", "class", "add", "dev", self.ifb_interface,
                "parent", self.parent_class, "classid", full_classid,
                "htb", f"rate={download_mbps}mbit"
            ]):
                log.error(f"Failed to create download class for {mac}")
                return False

            # Add u32 filter for destination MAC (on IFB)
            mac_hex = self._mac_to_u32_match(mac)
            if not self._run([
                "tc", "filter", "add", "dev", self.ifb_interface,
                "parent", f"{self.root_handle}", "protocol", "ip",
                "u32", mac_hex, "flowid", full_classid
            ]):
                log.error(f"Failed to add download filter for {mac}")
                return False

        self.mac_to_classid[mac] = full_classid
        log.info(f"Bandwidth limit set for {mac}: {upload_mbps}Mbps up / {download_mbps}Mbps down")
        return True

    def remove_session_limit(self, mac: str) -> bool:
        """
        Remove bandwidth limit for a MAC address.

        Args:
            mac: MAC address

        Returns:
            True if successful
        """
        if mac not in self.mac_to_classid:
            log.warning(f"No bandwidth limit found for {mac}")
            return True

        classid = self.mac_to_classid[mac]

        # Remove filters
        self._run([
            "tc", "filter", "del", "dev", self.wan_interface,
            "parent", f"{self.root_handle}", "protocol", "ip",
            "prio", "1"  # Simple removal
        ])

        self._run([
            "tc", "filter", "del", "dev", self.ifb_interface,
            "parent", f"{self.root_handle}", "protocol", "ip",
            "prio", "1"
        ])

        # Remove classes
        self._run([
            "tc", "class", "del", "dev", self.wan_interface,
            "classid", classid
        ])

        self._run([
            "tc", "class", "del", "dev", self.ifb_interface,
            "classid", classid
        ])

        del self.mac_to_classid[mac]
        log.info(f"Bandwidth limit removed for {mac}")
        return True

    def _mac_to_u32_match(self, mac: str) -> str:
        """
        Convert MAC address to u32 filter match string.

        Example: aa:bb:cc:dd:ee:ff -> match u32 0xaabbccdd at 6 0xffffffff match u32 0xeeff at 12 0xffff

        Args:
            mac: MAC address in standard format

        Returns:
            u32 filter string
        """
        # Remove colons and convert to hex
        mac_clean = mac.replace(":", "")
        if len(mac_clean) != 12:
            return "match u32 0 0"  # Invalid, return no-match

        try:
            # u32 filters work with 32-bit words
            # Ethernet source MAC is at offset 6 (first 4 bytes) and 10 (last 2 bytes)
            high = int(mac_clean[:8], 16)
            low = int(mac_clean[8:12], 16)

            # Return as u32 filter syntax
            return f"match u32 0x{high:08x} at 6 0xffffffff match u32 0x{low:04x}0000 at 12 0xffff0000"
        except ValueError:
            log.error(f"Invalid MAC address: {mac}")
            return "match u32 0 0"

    def cleanup(self) -> bool:
        """
        Remove all traffic control rules.

        Returns:
            True if successful
        """
        log.info("Cleaning up traffic control rules")

        # Remove root qdisc (cascades to remove classes and filters)
        self._run(["tc", "qdisc", "del", "dev", self.wan_interface, "root"])
        self._run(["tc", "qdisc", "del", "dev", self.wan_interface, "ingress"])
        self._run(["tc", "qdisc", "del", "dev", self.ifb_interface, "root"])

        # Disable IFB interface
        subprocess.run(["ip", "link", "set", self.ifb_interface, "down"], capture_output=True)

        self.mac_to_classid.clear()
        return True


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

    def __init__(self, portal_ip: str = "192.168.1.1", portal_port: int = 8080, wan_interface: str = "eth1"):
        """
        Initialize firewall client

        Args:
            portal_ip: IP address of the portal HTTP server
            portal_port: Port where portal is served
            wan_interface: WAN interface for traffic control (eth1, wwan0, etc.)
        """
        self.portal_ip = portal_ip
        self.portal_port = portal_port
        self.chain_forward = "JADSLINK_FORWARD"
        self.chain_prerouting = "JADSLINK_PREROUTING"
        self.tc = None  # TrafficControl instance (lazy initialized)
        self.wan_interface = wan_interface

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
            # Persist rules to survive reboot
            self.persist_rules()

        return success

    def block_mac(self, mac: str) -> bool:
        """
        Block internet access for a specific MAC address.
        Removes the allow rule and bandwidth limits.

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

        # Remove bandwidth limits if traffic control is initialized
        if self.tc is not None:
            self.tc.remove_session_limit(mac)

        if success:
            log.info(f"Blocked MAC {mac}")
            # Persist rules to survive reboot
            self.persist_rules()

        return success

    def set_bandwidth_limit(
        self,
        mac: str,
        download_kbps: int = 0,
        upload_kbps: int = 0
    ) -> bool:
        """
        Set bandwidth limits for a MAC address using tc (traffic control).

        Uses HTB (Hierarchical Token Bucket) for egress and IFB for ingress.

        Args:
            mac: Device MAC address
            download_kbps: Download limit in kbps (0 = unlimited)
            upload_kbps: Upload limit in kbps (0 = unlimited)

        Returns:
            True if successful
        """
        if download_kbps == 0 and upload_kbps == 0:
            return True  # No limits

        # Lazy initialize traffic control
        if self.tc is None:
            self.tc = TrafficControl(wan_interface=self.wan_interface)

            # Setup shaping on first use
            if not self.tc.setup_egress_shaping(max_rate_mbps=100):
                log.warning("Failed to setup egress shaping, bandwidth limiting disabled")
                return False

            if not self.tc.setup_ingress_shaping():
                log.warning("Failed to setup ingress shaping, download limiting may not work")

        # Convert kbps to mbps
        download_mbps = max(1, download_kbps // 1000) if download_kbps > 0 else 0
        upload_mbps = max(1, upload_kbps // 1000) if upload_kbps > 0 else 0

        # Apply limits
        if not self.tc.add_session_limit(mac, download_mbps, upload_mbps):
            log.error(f"Failed to set bandwidth limit for {mac}")
            return False

        log.info(f"Bandwidth limit set for {mac}: {upload_mbps}Mbps up / {download_mbps}Mbps down")
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

    def _is_openwrt(self) -> bool:
        """
        Detect if running on OpenWrt.

        Returns:
            True if /etc/openwrt_release exists
        """
        import os as os_module
        return os_module.path.exists("/etc/openwrt_release")

    def persist_rules(self) -> bool:
        """
        Export current iptables rules to a file for persistence.
        Creates /var/lib/jadslink/iptables.rules

        Returns:
            True if successful
        """
        import os as os_module

        # Create directory if it doesn't exist
        rules_dir = "/var/lib/jadslink"
        try:
            os_module.makedirs(rules_dir, mode=0o755, exist_ok=True)
        except Exception as e:
            log.error(f"Failed to create rules directory: {e}")
            return False

        rules_file = f"{rules_dir}/iptables.rules"

        try:
            # Export JADSLINK rules from both nat and filter tables
            nat_rules = self._run_output([
                "iptables-save", "-t", "nat"
            ])

            filter_rules = self._run_output([
                "iptables-save", "-t", "filter"
            ])

            # Generate shell script format
            script_content = """#!/bin/sh
# JADSlink firewall rules - Auto-generated
# Source: iptables-save output

# Restore NAT table rules
"""
            if nat_rules:
                # Extract only JADSLINK related rules
                for line in nat_rules.split("\n"):
                    if "JADSLINK" in line or line.startswith("-"):
                        script_content += f"{line}\n"

            script_content += """
# Restore filter table rules
"""
            if filter_rules:
                # Extract only JADSLINK related rules
                for line in filter_rules.split("\n"):
                    if "JADSLINK" in line or line.startswith("-"):
                        script_content += f"{line}\n"

            # Write to file
            with open(rules_file, "w") as f:
                f.write(script_content)

            os_module.chmod(rules_file, 0o644)
            log.info(f"Firewall rules persisted to {rules_file}")
            return True

        except Exception as e:
            log.error(f"Failed to persist rules: {e}")
            return False

    def install_firewall_user(self) -> bool:
        """
        Create /etc/firewall.user script to restore rules on boot.
        Only needed on OpenWrt.

        Returns:
            True if successful
        """
        if not self._is_openwrt():
            log.debug("Not on OpenWrt, skipping /etc/firewall.user creation")
            return True

        import os as os_module

        firewall_user_script = """#!/bin/sh
# JADSlink custom firewall rules - Auto-generated
# This script is executed after the OpenWrt firewall starts

# Create chains
iptables -t nat -N JADSLINK_PREROUTING 2>/dev/null || true
iptables -t filter -N JADSLINK_FORWARD 2>/dev/null || true

# Flush chains (in case they already exist)
iptables -t nat -F JADSLINK_PREROUTING
iptables -t filter -F JADSLINK_FORWARD

# Restore rules from cache (if they exist)
[ -f /var/lib/jadslink/iptables.rules ] && . /var/lib/jadslink/iptables.rules

# Hook into main chains (if not already there)
iptables -t nat -C PREROUTING -j JADSLINK_PREROUTING 2>/dev/null || \\
    iptables -t nat -I PREROUTING 1 -j JADSLINK_PREROUTING

iptables -t filter -C FORWARD -j JADSLINK_FORWARD 2>/dev/null || \\
    iptables -t filter -I FORWARD 1 -j JADSLINK_FORWARD

# Default policy for JADSLINK chains
iptables -t filter -A JADSLINK_FORWARD -m state --state ESTABLISHED,RELATED -j ACCEPT
iptables -t nat -A JADSLINK_PREROUTING -p tcp --dport 80 -j DNAT --to-destination 192.168.1.1:80
"""

        try:
            with open("/etc/firewall.user", "w") as f:
                f.write(firewall_user_script)

            os_module.chmod("/etc/firewall.user", 0o755)
            log.info("Created /etc/firewall.user for rule persistence")
            return True

        except Exception as e:
            log.error(f"Failed to create /etc/firewall.user: {e}")
            return False

    def cleanup(self) -> None:
        """Cleanup firewall rules on shutdown"""
        log.info("Cleaning up firewall")

        # Persist rules before cleanup (so they survive reboot if needed)
        self.persist_rules()

        # Cleanup traffic control
        if self.tc is not None:
            self.tc.cleanup()

        # Remove our chains from main chains
        self._run(["iptables", "-t", "filter", "-D", "FORWARD", "-j", self.chain_forward])
        self._run(["iptables", "-t", "nat", "-D", "PREROUTING", "-j", self.chain_prerouting])

        # Flush and delete our chains
        self._run(["iptables", "-t", "filter", "-F", self.chain_forward])
        self._run(["iptables", "-t", "filter", "-X", self.chain_forward])
        self._run(["iptables", "-t", "nat", "-F", self.chain_prerouting])
        self._run(["iptables", "-t", "nat", "-X", self.chain_prerouting])
