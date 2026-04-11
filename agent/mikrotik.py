from typing import Optional
import logging

# Import the actual routeros_api library
from routeros_api import RouterOsApiPool, RouterOsQueryError

log = logging.getLogger("jadslink.mikrotik")


class MikroTikClient:
    """Wrapper for RouterOS hotspot and interface management"""

    def __init__(self, ip: str, user: str, password: str):
        """
        Initialize MikroTik connection

        Args:
            ip: RouterOS API IP address
            user: RouterOS API username
            password: RouterOS API password
        """
        self.ip = ip
        self.user = user
        self.password = password
        self._api = None  # Will hold the RouterOsApiPool connection

        log.info(f"MikroTik client initialized for {ip}")

    def _connect_if_needed(self):
        """Connects to RouterOS API if not already connected."""
        if not self._api or not self._api.connected:
            try:
                # Use default port 8728, or 8729 for SSL
                self._api = RouterOsApiPool(self.ip, username=self.user, password=self.password, plaintext_login=True)
                self._api.connect()
                log.info(f"Successfully connected to MikroTik at {self.ip}")
            except Exception as e:
                log.error(f"MikroTik connection failed at {self.ip}: {e}")
                self._api = None # Ensure _api is None on failure
                raise ConnectionError(f"Failed to connect to MikroTik: {e}")

    def disconnect(self):
        """Close RouterOS connection"""
        if self._api and self._api.connected:
            try:
                self._api.disconnect()
                log.info("Disconnected from RouterOS")
            except Exception as e:
                log.error(f"Error disconnecting from MikroTik: {e}")
        self._api = None

    def add_hotspot_user(
        self,
        mac: str,
        time_limit_minutes: int,
        rate_down: int = 0,
        rate_up: int = 0,
    ) -> bool:
        """
        Add user to hotspot with time and bandwidth limits

        Args:
            mac: Device MAC address
            time_limit_minutes: Duration in minutes (0 = unlimited)
            rate_down: Download rate limit in kbps (0 = unlimited)
            rate_up: Upload rate limit in kbps (0 = unlimited)

        Returns:
            True if successful
        """
        try:
            self._connect_if_needed()
            hotspot_user_api = self._api.get_path('/ip/hotspot/user')
            hotspot_profile_api = self._api.get_path('/ip/hotspot/user/profile')

            # Create a profile if needed (or use a default one)
            # For simplicity, we assume a default profile exists or we create a basic one
            # A more robust solution might check for specific profiles or create them dynamically.
            profile_name = f"profile-{rate_down}-{rate_up}-{time_limit_minutes}"
            existing_profiles = hotspot_profile_api.get(name=profile_name)

            if not existing_profiles:
                limit_rx_tx = "" # no limits
                if rate_down > 0 and rate_up > 0:
                    limit_rx_tx = f"{rate_up}k/{rate_down}k"
                elif rate_down > 0:
                    limit_rx_tx = f"0k/{rate_down}k"
                elif rate_up > 0:
                    limit_rx_tx = f"{rate_up}k/0k"

                hotspot_profile_api.add(
                    name=profile_name,
                    'rate-limit': limit_rx_tx, # Format: upload/download
                    # Other profile settings like shared-users, idle-timeout, keepalive-timeout can be added here
                )
                log.info(f"Created MikroTik hotspot profile: {profile_name} with limits {limit_rx_tx}")

            # Add the user
            hotspot_user_api.add(
                name=mac,
                password="", # MAC based login, password not strictly needed
                'mac-address': mac,
                profile=profile_name,
                'limit-uptime': f"{time_limit_minutes}m" if time_limit_minutes > 0 else "",
                comment=f"JADSlink Ticket - {mac}",
            )
            log.debug(f"Added hotspot user {mac} ({time_limit_minutes}min, profile: {profile_name})")
            return True
        except ConnectionError:
            log.error("Not connected to MikroTik for add_hotspot_user.")
            return False
        except RouterOsQueryError as e:
            log.error(f"RouterOS query error adding hotspot user {mac}: {e}")
            return False
        except Exception as e:
            log.error(f"Unexpected error adding hotspot user {mac}: {e}")
            return False

    def remove_hotspot_user(self, mac: str) -> bool:
        """Remove user from hotspot (disconnect session)"""
        try:
            self._connect_if_needed()
            hotspot_user_api = self._api.get_path('/ip/hotspot/user')
            hotspot_active_api = self._api.get_path('/ip/hotspot/active')

            # First, find and remove the user entry
            users = hotspot_user_api.get(**{'mac-address': mac})
            for user in users:
                hotspot_user_api.remove(id=user['.id'])
                log.debug(f"Removed hotspot user entry for MAC {mac}")

            # Then, remove any active sessions for that MAC
            active_sessions = hotspot_active_api.get(**{'mac-address': mac})
            for session in active_sessions:
                hotspot_active_api.remove(id=session['.id'])
                log.debug(f"Removed active hotspot session for MAC {mac}")
            return True
        except ConnectionError:
            log.error("Not connected to MikroTik for remove_hotspot_user.")
            return False
        except RouterOsQueryError as e:
            log.error(f"RouterOS query error removing hotspot user {mac}: {e}")
            return False
        except Exception as e:
            log.error(f"Unexpected error removing hotspot user {mac}: {e}")
            return False

    def count_active_users(self) -> int:
        """Get count of active hotspot sessions"""
        try:
            self._connect_if_needed()
            active_sessions = self._api.get_path('/ip/hotspot/active').get()
            return len(active_sessions)
        except ConnectionError:
            log.error("Not connected to MikroTik for count_active_users.")
            return 0
        except RouterOsQueryError as e:
            log.error(f"RouterOS query error counting active users: {e}")
            return 0
        except Exception as e:
            log.error(f"Unexpected error counting active users: {e}")
            return 0

    def get_bytes_today(self) -> int:
        """Get total bytes transferred today (sum of all interfaces) in KB"""
        try:
            self._connect_if_needed()
            # This is a simplification. A real implementation might need to track specific interfaces
            # or use RouterOS accounting features. For now, we'll sum all interface stats.
            interfaces = self._api.get_path('/interface').get()
            total_bytes = 0
            for iface in interfaces:
                # stat format can vary, need to check if .stat.rx-byte and .stat.tx-byte exist
                if '.stat.rx-byte' in iface and '.stat.tx-byte' in iface:
                    total_bytes += int(iface['.stat.rx-byte']) + int(iface['.stat.tx-byte'])
            return total_bytes // 1024 # Convert bytes to KB
        except ConnectionError:
            log.error("Not connected to MikroTik for get_bytes_today.")
            return 0
        except RouterOsQueryError as e:
            log.error(f"RouterOS query error getting bytes today: {e}")
            return 0
        except Exception as e:
            log.error(f"Unexpected error getting bytes today: {e}")
            return 0

    def get_signal_quality(self) -> Optional[int]:
        """
        Get LTE/4G signal quality (if available).
        This is highly dependent on the RouterOS device and its LTE modem.
        It tries to find an LTE interface and get 'rsrp' or 'rssi' value.

        Returns:
            Signal strength 0-100, or None if not available/applicable.
        """
        try:
            self._connect_if_needed()
            lte_interfaces = self._api.get_path('/interface/lte').get()
            if lte_interfaces:
                # Assuming the first LTE interface for simplicity
                lte_status = self._api.get_path('/interface/lte/info').get(interface=lte_interfaces[0]['name'])
                if lte_status:
                    # RSRP (Reference Signal Received Power) is a common metric, usually in dBm
                    # Convert dBm to a 0-100 scale (e.g., -120 dBm = 0%, -60 dBm = 100%)
                    if 'rsrp' in lte_status[0]:
                        rsrp_dbm = int(lte_status[0]['rsrp'].replace("dBm", ""))
                        # Map -120dBm to 0 and -60dBm to 100
                        quality = min(100, max(0, int((rsrp_dbm + 120) * (100 / 60))))
                        return quality
                    elif 'rssi' in lte_status[0]: # RSSI can also be used as a fallback
                        rssi_dbm = int(lte_status[0]['rssi'].replace("dBm", ""))
                        # Map -100dBm to 0 and -50dBm to 100
                        quality = min(100, max(0, int((rssi_dbm + 100) * (100 / 50))))
                        return quality
            return None
        except ConnectionError:
            log.error("Not connected to MikroTik for get_signal_quality.")
            return None
        except RouterOsQueryError as e:
            log.error(f"RouterOS query error getting signal quality: {e}")
            return None
        except Exception as e:
            log.error(f"Unexpected error getting signal quality: {e}")
            return None
