#!/usr/bin/env python3
"""
JADSlink Field Agent — runs on GL.iNet or Raspberry Pi in field

Responsibilities:
- Maintain connection to central server
- Cache tickets for offline activation
- Manage hotspot sessions
- Report metrics and activations
"""

import schedule
import time
import logging
from pathlib import Path
from config import AgentConfig
from cache import TicketCache
from sync import ServerSync
from mikrotik import MikroTikClient
from session_manager import SessionManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)
log = logging.getLogger("jadslink.agent")


class JADSLinkAgent:
    """Main agent class"""

    def __init__(self):
        """Initialize agent with configuration"""
        try:
            self.config = AgentConfig()
            log.info(f"Agent initialized for node {self.config.NODE_ID}")
        except ValueError as e:
            log.error(f"Configuration error: {e}")
            raise

        # Initialize components
        self.cache = TicketCache(self.config.cache_db_path)
        self.sync = ServerSync(self.config, self.cache)
        self.mikrotik = MikroTikClient(
            self.config.ROUTER_IP,
            self.config.ROUTER_USER,
            self.config.ROUTER_PASS,
            self.config.ROUTER_PORT,
        )
        self.sessions = SessionManager(self.cache, self.mikrotik)

    def run(self):
        """Main event loop with scheduled tasks"""
        log.info(f"🚀 JADSlink Agent started | Node: {self.config.NODE_ID}")
        log.info(f"   Server: {self.config.SERVER_URL}")
        log.info(f"   Router: {self.config.ROUTER_IP}")

        # Schedule tasks
        schedule.every(self.config.HEARTBEAT_INTERVAL).seconds.do(self._heartbeat)
        schedule.every(self.config.SYNC_INTERVAL).seconds.do(self._sync_tickets)
        schedule.every(self.config.EXPIRE_INTERVAL).seconds.do(self._expire_sessions)

        # Main loop
        try:
            while True:
                schedule.run_pending()
                time.sleep(1)
        except KeyboardInterrupt:
            log.info("Agent shutting down...")
            self.mikrotik.disconnect()

    def activate(self, code: str, device_mac: str) -> dict:
        """
        Activate a ticket (entry point for external systems)

        Called by scripts like MikroTik hotspot redirect script.
        Works offline if needed.
        """
        return self.sessions.activate(code, device_mac)

    def _heartbeat(self):
        """Send heartbeat with metrics every 30 seconds"""
        try:
            metrics = {
                "active_sessions": self.mikrotik.count_active_users(),
                "bytes_total_day": self.mikrotik.get_bytes_today(),
                "signal_quality": self.mikrotik.get_signal_quality(),
            }

            ok = self.sync.post_heartbeat(metrics)
            if not ok:
                log.warning("Heartbeat failed — server unavailable (operating offline)")
        except Exception as e:
            log.error(f"Heartbeat error: {e}")

    def _sync_tickets(self):
        """Sync pending tickets from server every 5 minutes"""
        try:
            tickets = self.sync.get_pending_tickets()
            if tickets:
                count = self.cache.bulk_store(tickets)
                log.info(f"Synced {count} tickets from server")

            # Also try to flush any pending reports
            self.sync.flush_pending_reports()
        except Exception as e:
            log.error(f"Sync error: {e}")

    def _expire_sessions(self):
        """Expire overdue sessions every 60 seconds"""
        try:
            count = self.sessions.expire_overdue()
            if count > 0:
                log.info(f"Expired {count} session(s)")
        except Exception as e:
            log.error(f"Expiration error: {e}")


def main():
    """Entry point"""
    agent = JADSLinkAgent()
    agent.run()


if __name__ == "__main__":
    main()
