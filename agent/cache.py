"""Local SQLite cache for offline operation"""

import sqlite3
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime
import logging

log = logging.getLogger("jadslink.cache")


class TicketCache:
    """SQLite-based ticket cache for offline operation"""

    def __init__(self, db_path: Path):
        """Initialize cache database"""
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """Create tables if they don't exist"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS tickets (
                    code TEXT PRIMARY KEY,
                    status TEXT NOT NULL,
                    duration_minutes INTEGER NOT NULL,
                    plan_id TEXT NOT NULL,
                    node_id TEXT NOT NULL,
                    bandwidth_down_kbps INTEGER DEFAULT 0,
                    bandwidth_up_kbps INTEGER DEFAULT 0,
                    created_at TEXT NOT NULL,
                    activated_at TEXT,
                    device_mac TEXT
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS pending_reports (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    code TEXT NOT NULL,
                    device_mac TEXT NOT NULL,
                    activated_at TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )
            conn.commit()

    def get_ticket(self, code: str) -> Optional[Dict[str, Any]]:
        """Get ticket from cache"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("SELECT * FROM tickets WHERE code = ?", (code,))
            row = cursor.fetchone()
            if row:
                return dict(row)
        return None

    def store_ticket(self, ticket: Dict[str, Any]) -> bool:
        """Store single ticket in cache"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO tickets
                    (code, status, duration_minutes, plan_id, node_id,
                     bandwidth_down_kbps, bandwidth_up_kbps, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        ticket["code"],
                        ticket.get("status", "pending"),
                        ticket.get("duration_minutes", 0),
                        ticket.get("plan_id", ""),
                        ticket.get("node_id", ""),
                        ticket.get("bandwidth_down_kbps", 0),
                        ticket.get("bandwidth_up_kbps", 0),
                        datetime.utcnow().isoformat(),
                    ),
                )
                conn.commit()
            return True
        except Exception as e:
            log.error(f"Error storing ticket: {e}")
            return False

    def bulk_store(self, tickets: List[Dict[str, Any]]) -> int:
        """Store multiple tickets — returns count stored"""
        count = 0
        for ticket in tickets:
            if self.store_ticket(ticket):
                count += 1
        return count

    def mark_active(self, code: str, device_mac: str) -> bool:
        """Mark ticket as activated locally"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    """
                    UPDATE tickets
                    SET status = 'active', activated_at = ?, device_mac = ?
                    WHERE code = ?
                    """,
                    (datetime.utcnow().isoformat(), device_mac, code),
                )
                conn.commit()
            return True
        except Exception as e:
            log.error(f"Error marking ticket active: {e}")
            return False

    def get_pending_reports(self) -> List[Dict[str, str]]:
        """Get all pending activation reports"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("SELECT code, device_mac, activated_at FROM pending_reports")
            return [dict(row) for row in cursor.fetchall()]

    def add_pending_report(self, code: str, device_mac: str, activated_at: str) -> bool:
        """Queue activation report for when connection is restored"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    """
                    INSERT INTO pending_reports (code, device_mac, activated_at, created_at)
                    VALUES (?, ?, ?, ?)
                    """,
                    (code, device_mac, activated_at, datetime.utcnow().isoformat()),
                )
                conn.commit()
            return True
        except Exception as e:
            log.error(f"Error adding pending report: {e}")
            return False

    def clear_reported(self, codes: List[str]) -> bool:
        """Remove successfully reported activations"""
        if not codes:
            return True
        try:
            with sqlite3.connect(self.db_path) as conn:
                placeholders = ",".join("?" * len(codes))
                conn.execute(f"DELETE FROM pending_reports WHERE code IN ({placeholders})", codes)
                conn.commit()
            return True
        except Exception as e:
            log.error(f"Error clearing reported: {e}")
            return False

    def get_active_sessions(self) -> List[Dict[str, Any]]:
        """Get all active sessions (activated tickets)"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                "SELECT code, device_mac, activated_at FROM tickets WHERE status = 'active'"
            )
            return [dict(row) for row in cursor.fetchall()]
