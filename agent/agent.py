import schedule, time, logging, threading
from config import AgentConfig
from cache import TicketCache
from firewall import FirewallClient
from sync import ServerSync
from session_manager import SessionManager
from portal import PortalServer, get_default_portal_html

log = logging.getLogger("jadslink.agent")

class JADSLinkAgent:
    def __init__(self):
        self.cfg     = AgentConfig()     # lee .env del nodo
        self.cache   = TicketCache()     # SQLite local tickets.db
        self.firewall= FirewallClient(   # iptables firewall
                           portal_ip=self.cfg.ROUTER_IP,
                           portal_port=self.cfg.PORTAL_PORT)
        self.sync    = ServerSync(self.cfg, self.cache)
        self.sessions= SessionManager(self.cache, self.firewall)
        self.portal  = None              # Portal HTTP server
        self.portal_thread = None         # Portal server thread

    def run(self):
        log.info(f"JADSlink Agent iniciado | Nodo: {self.cfg.NODE_ID}")

        # Start portal server in background thread
        self._start_portal()

        # Schedule periodic tasks
        schedule.every(30).seconds.do(self._heartbeat)
        schedule.every(5).minutes.do(self._sync_tickets)
        schedule.every(60).seconds.do(self.sessions.expire_overdue)

        # Main loop
        try:
            while True:
                schedule.run_pending()
                time.sleep(1)
        except KeyboardInterrupt:
            log.info("Agent interrupted, shutting down...")
            self._shutdown()

    def _start_portal(self):
        """Start captive portal HTTP server in background thread"""
        # Try to fetch HTML from backend, fallback to default
        portal_html = self._fetch_portal_html()

        # Create portal server
        self.portal = PortalServer(
            host=self.cfg.PORTAL_HOST,
            port=self.cfg.PORTAL_PORT,
            portal_html=portal_html,
            activate_callback=self.activate
        )

        # Start in daemon thread
        self.portal_thread = threading.Thread(target=self.portal.start, daemon=True)
        self.portal_thread.start()
        log.info(f"Portal server started on {self.cfg.PORTAL_HOST}:{self.cfg.PORTAL_PORT}")

    def _fetch_portal_html(self) -> str:
        """Fetch portal HTML from backend, or use fallback"""
        try:
            import requests
            url = f"{self.cfg.SERVER_URL}/api/v1/portal/"
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                log.info("Fetched portal HTML from backend")
                return response.text
        except Exception as e:
            log.warning(f"Could not fetch portal HTML from backend: {e}")

        log.info("Using default fallback portal HTML")
        return get_default_portal_html()

    def _shutdown(self):
        """Cleanup on shutdown"""
        if self.portal:
            self.portal.stop()
        self.firewall.cleanup()
        log.info("Agent shutdown complete")

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

        # Activar en firewall (iptables)
        success = self.firewall.allow_mac(
            mac=mac,
            duration_minutes=ticket["duration_minutes"]
        )

        if not success:
            return {"ok": False, "reason": "firewall_error"}

        # Aplicar límites de ancho de banda (opcional)
        self.firewall.set_bandwidth_limit(
            mac=mac,
            download_kbps=ticket.get("bandwidth_down_kbps", 0),
            upload_kbps=ticket.get("bandwidth_up_kbps", 0)
        )

        self.cache.mark_active(code, mac)
        self.sync.report_activation(code, mac)  # encola si offline

        log.info(f"Ticket {code} activado para {mac}")
        return {"ok": True, "minutes": ticket["duration_minutes"]}

    def _heartbeat(self):
        metrics = {
            "active_sessions" : self.firewall.count_active_users(),
            "bytes_total_day" : 0,  # TODO: Implement network stats collection
            "signal_quality"  : None,  # Not applicable for generic Linux
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
