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

    def report_activations(self, activations: List[Dict[str, str]]) -> bool:
        """Report offline activations to server"""
        if not activations:
            return True

        try:
            url = f"{self.base_url}/api/v1/agent/sessions/report"
            response = requests.post(
                url, json=activations, headers=self.headers, timeout=self.timeout
            )
            if response.status_code == 200:
                result = response.json()
                processed = result.get("processed", 0)
                failed = result.get("failed", 0)
                log.info(f"Reported {processed} activations (failed: {failed})")
                return processed > 0
            else:
                log.warning(f"Report failed: {response.status_code}")
                return False
        except requests.RequestException as e:
            log.warning(f"Report connection error: {e}")
            return False

    def flush_pending_reports(self) -> bool:
        """Send all queued offline activations"""
        pending = self.cache.get_pending_reports()
        if not pending:
            return True

        log.info(f"Flushing {len(pending)} pending reports")

        # Convert to proper format for API
        activations = [
            {
                "code": p["code"],
                "device_mac": p["device_mac"],
                "activated_at": p["activated_at"],
            }
            for p in pending
        ]

        if self.report_activations(activations):
            # Clear successfully reported
            codes = [p["code"] for p in pending]
            self.cache.clear_reported(codes)
            return True

        return False
