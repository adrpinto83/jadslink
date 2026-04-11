"""Server synchronization — HTTP REST communication with JADSlink API"""

import requests
from typing import Dict, List, Optional, Any
from datetime import datetime
from cache import TicketCache
import logging

log = logging.getLogger("jadslink.sync")


class ServerSync:
    """Handle all HTTP communication with server"""

    def __init__(self, config, cache: TicketCache):
        """Initialize sync handler"""
        self.config = config
        self.cache = cache
        self.timeout = 5  # seconds
        self.base_url = config.SERVER_URL.rstrip("/")
        self.headers = {
            "X-Node-Key": config.API_KEY,
            "Content-Type": "application/json",
        }

    def post_heartbeat(self, metrics: Dict[str, Any]) -> bool:
        """Send node heartbeat with metrics"""
        try:
            url = f"{self.base_url}/api/v1/agent/heartbeat"
            payload = {
                "node_id": str(self.config.NODE_ID),
                "metrics": {
                    "active_sessions": metrics.get("active_sessions", 0),
                    "bytes_total_day": metrics.get("bytes_total_day", 0),
                    "signal_quality": metrics.get("signal_quality"),
                    "cpu_percent": metrics.get("cpu_percent"),
                    "ram_percent": metrics.get("ram_percent"),
                },
            }
            response = requests.post(
                url, json=payload, headers=self.headers, timeout=self.timeout
            )
            if response.status_code == 200:
                log.debug("Heartbeat sent successfully")
                return True
            else:
                log.warning(f"Heartbeat failed: {response.status_code}")
                return False
        except requests.RequestException as e:
            log.warning(f"Heartbeat connection error: {e}")
            return False

    def get_pending_tickets(self) -> Optional[List[Dict[str, Any]]]:
        """Fetch pending and active tickets from server"""
        try:
            url = f"{self.base_url}/api/v1/agent/tickets/sync"
            params = {"node_id": str(self.config.NODE_ID)}
            response = requests.get(
                url, params=params, headers=self.headers, timeout=self.timeout
            )
            if response.status_code == 200:
                tickets = response.json()
                log.info(f"Synced {len(tickets)} tickets from server")
                return tickets
            else:
                log.warning(f"Ticket sync failed: {response.status_code}")
                return None
        except requests.RequestException as e:
            log.warning(f"Ticket sync connection error: {e}")
            return None

    def fetch_ticket(self, code: str) -> Optional[Dict[str, Any]]:
        """Fetch a single ticket from the server by code."""
        try:
            url = f"{self.base_url}/api/v1/agent/tickets/sync"
            params = {"node_id": str(self.config.NODE_ID), "code": code}
            response = requests.get(
                url, params=params, headers=self.headers, timeout=self.timeout
            )
            if response.status_code == 200:
                ticket_data = response.json()
                if ticket_data:
                    log.info(f"Fetched ticket {code} from server")
                    return ticket_data[0] if isinstance(ticket_data, list) and ticket_data else None
                else:
                    log.info(f"Ticket {code} not found on server")
                    return None
            elif response.status_code == 404:
                log.info(f"Ticket {code} not found on server")
                return None
            else:
                log.warning(f"Fetching ticket {code} failed: {response.status_code}")
                return None
        except requests.RequestException as e:
            log.warning(f"Ticket {code} fetch connection error: {e}")
            return None

    def report_activation(self, code: str, device_mac: str) -> bool:
        """Report a single activation to server, or queue if offline."""
        activation = {"code": code, "device_mac": device_mac, "activated_at": datetime.utcnow().isoformat()}
        if self._try_report_single_activation(activation):
            return True
        else:
            # If reporting fails, queue it for later
            log.warning(f"Failed to report activation for {code}, queuing for later.")
            return self.cache.add_pending_report(code, device_mac, activation["activated_at"])

    def _try_report_single_activation(self, activation: Dict[str, str]) -> bool:
        """Helper to attempt reporting a single activation directly."""
        try:
            url = f"{self.base_url}/api/v1/agent/sessions/report"
            response = requests.post(
                url, json=[activation], headers=self.headers, timeout=self.timeout
            )
            if response.status_code == 200:
                log.debug(f"Activation for {activation["code"]} reported successfully.")
                return True
            else:
                log.warning(f"Failed to report activation {activation["code"]}: {response.status_code}")
                return False
        except requests.RequestException as e:
            log.warning(f"Connection error while reporting activation {activation["code"]}: {e}")
            return False

    def flush_pending_reports(self) -> bool:
        """Send all queued offline activations"""
        pending = self.cache.get_pending_reports()
        if not pending:
            return True

        log.info(f"Flushing {len(pending)} pending reports")

        reported_codes = []
        for activation_data in pending:
            # Construct activation dict directly from activation_data (which is already a dict)
            if self._try_report_single_activation(activation_data):
                reported_codes.append(activation_data["code"])
        
        if reported_codes:
            self.cache.clear_reported(reported_codes)
            log.info(f"Cleared {len(reported_codes)} successfully reported activations.")
            return True
        return False
