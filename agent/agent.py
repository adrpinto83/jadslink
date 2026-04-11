import schedule, time, logging
from config import AgentConfig
from cache import TicketCache
from mikrotik import MikroTikClient
from sync import ServerSync
from session_manager import SessionManager

log = logging.getLogger("jadslink.agent")

class JADSLinkAgent:
    def __init__(self):
        self.cfg     = AgentConfig()     # lee .env del nodo
        self.cache   = TicketCache()     # SQLite local tickets.db
        self.mt      = MikroTikClient(   # RouterOS API
                           self.cfg.ROUTER_IP,
                           self.cfg.ROUTER_USER,
                           self.cfg.ROUTER_PASS)
        self.sync    = ServerSync(self.cfg)
        self.sessions= SessionManager(self.cache, self.mt)

    def run(self):
        log.info(f"JADSlink Agent iniciado | Nodo: {self.cfg.NODE_ID}")
        schedule.every(30).seconds.do(self._heartbeat)
        schedule.every(5).minutes.do(self._sync_tickets)
        schedule.every(60).seconds.do(self.sessions.expire_overdue)
        while True:
            schedule.run_pending()
            time.sleep(1)

    def activate(self, code: str, mac: str) -> dict:
        """
        Punto de entrada principal — llamado por script MikroTik.
        Funciona con o sin internet (modo offline usando cache local).
        """
        ticket = self.cache.get_ticket(code)

        if not ticket:
            ticket = self.sync.fetch_ticket(code)   # intenta servidor
            if ticket:
                self.cache.store_ticket(ticket)

        if not ticket:
            return {"ok": False, "reason": "ticket_not_found"}

        if ticket["status"] != "pending":
            return {"ok": False, "reason": f"ticket_{ticket['status']}"}

        # Activar en MikroTik Hotspot
        self.mt.add_hotspot_user(
            mac=mac,
            time_limit_minutes=ticket["duration_minutes"],
            rate_down=ticket["bandwidth_down_kbps"],
            rate_up=ticket["bandwidth_up_kbps"]
        )

        self.cache.mark_active(code, mac)
        self.sync.report_activation(code, mac)  # encola si offline

        log.info(f"Ticket {code} activado para {mac}")
        return {"ok": True, "minutes": ticket["duration_minutes"]}

    def _heartbeat(self):
        metrics = {
            "active_sessions" : self.mt.count_active_users(),
            "bytes_total_day" : self.mt.get_bytes_today(),
            "signal_quality"  : self.mt.get_signal_quality(),
        }
        ok = self.sync.post_heartbeat(metrics)
        if not ok:
            log.warning("Servidor no disponible — operando offline")

    def _sync_tickets(self):
        tickets = self.sync.get_pending_tickets()
        if tickets:
            self.cache.bulk_store(tickets)
            log.info(f"{len(tickets)} tickets sincronizados")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s %(name)s %(levelname)s %(message)s")
    JADSLinkAgent().run()
