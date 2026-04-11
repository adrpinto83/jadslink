"""Session manager — handle ticket activation and expiration"""

from datetime import datetime, timezone, timedelta
from cache import TicketCache
from mikrotik import MikroTikClient
import logging

log = logging.getLogger("jadslink.session_manager")


class SessionManager:
    """Manage active sessions and ticket expiration"""

    def __init__(self, cache: TicketCache, mikrotik: MikroTikClient):
        """Initialize session manager"""
        self.cache = cache
        self.mikrotik = mikrotik

    def activate(self, code: str, device_mac: str) -> dict:
        """
        Activate a ticket locally (with or without internet)

        Returns:
            {ok: bool, reason: str, minutes: int}
        """
        # Try to get ticket from cache
        ticket = self.cache.get_ticket(code)

        if not ticket:
            return {"ok": False, "reason": "ticket_not_found"}

        if ticket["status"] != "pending":
            return {"ok": False, "reason": f"ticket_{ticket['status']}"}

        # Add to hotspot
        success = self.mikrotik.add_hotspot_user(
            mac=device_mac,
            time_limit_minutes=ticket["duration_minutes"],
            rate_down=ticket["bandwidth_down_kbps"],
            rate_up=ticket["bandwidth_up_kbps"],
        )

        if not success:
            return {"ok": False, "reason": "hotspot_error"}

        # Mark ticket as active locally
        self.cache.mark_active(code, device_mac)

        log.info(f"Activated ticket {code} for {device_mac}")
        return {
            "ok": True,
            "minutes": ticket["duration_minutes"],
        }

    def expire_overdue(self) -> int:
        """
        Expire sessions that have passed their duration

        Returns:
            Count of expired sessions
        """
        sessions = self.cache.get_active_sessions()
        now = datetime.now(timezone.utc)
        expired_count = 0

        for session in sessions:
            code = session["code"]
            ticket = self.cache.get_ticket(code)

            if not ticket or not ticket.get("activated_at"):
                continue

            # Parse activation time
            try:
                activated = datetime.fromisoformat(ticket["activated_at"])
                duration_seconds = ticket["duration_minutes"] * 60
                expires_at = activated + timedelta(seconds=duration_seconds) # Corrected calculation

                if now >= expires_at:
                    # Disconnect from hotspot
                    self.mikrotik.remove_hotspot_user(session["device_mac"])
                    self.cache.mark_expired(code) # Mark as expired in cache
                    log.info(f"Expired session for {code}")
                    expired_count += 1
            except Exception as e:
                log.error(f"Error expiring session {code}: {e}")

        return expired_count
