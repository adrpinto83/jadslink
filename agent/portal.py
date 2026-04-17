"""
Captive Portal HTTP Server
Ultralight HTTP server (< 40KB) using Python stdlib
Serves portal HTML and handles ticket activation
"""

import logging
import socket
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs
from typing import Callable, Dict, Any
import json

log = logging.getLogger("jadslink.portal")


class PortalHandler(BaseHTTPRequestHandler):
    """
    Minimalist HTTP handler for captive portal.
    Serves HTML and handles activation requests.
    """

    # Will be set by PortalServer
    activate_callback: Callable = None
    portal_html: str = ""

    def log_message(self, format, *args):
        """Override to use custom logger"""
        log.debug(f"{self.address_string()} - {format % args}")

    def do_GET(self):
        """Handle GET requests"""
        parsed_path = urlparse(self.path)

        # Serve portal HTML
        if parsed_path.path in ["/", "/portal", "/index.html"]:
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
            self.end_headers()
            self.wfile.write(self.portal_html.encode("utf-8"))

        # Health check
        elif parsed_path.path == "/health":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"status": "ok"}).encode())

        # 404 for anything else
        else:
            self.send_error(404, "Not Found")

    def do_POST(self):
        """Handle POST requests (ticket activation)"""
        parsed_path = urlparse(self.path)

        if parsed_path.path == "/activate":
            # Read form data
            content_length = int(self.headers.get("Content-Length", 0))
            post_data = self.rfile.read(content_length).decode("utf-8")

            # Parse form data
            params = parse_qs(post_data)
            code = params.get("code", [""])[0].strip().upper()

            if not code:
                self.send_error(400, "Missing ticket code")
                return

            # Get client MAC address
            client_ip = self.client_address[0]
            mac = self._get_mac_from_ip(client_ip)

            if not mac:
                self.send_error(500, "Could not determine device MAC address")
                return

            # Call activation callback
            if self.activate_callback:
                result = self.activate_callback(code, mac)

                if result.get("ok"):
                    # Success - return HTML response
                    self.send_response(200)
                    self.send_header("Content-Type", "text/html; charset=utf-8")
                    self.end_headers()

                    success_html = f"""
                    <!DOCTYPE html>
                    <html>
                    <head>
                        <meta charset="utf-8">
                        <meta name="viewport" content="width=device-width, initial-scale=1">
                        <title>Activación Exitosa</title>
                        <style>
                            body {{ font-family: sans-serif; text-align: center; padding: 50px; }}
                            .success {{ color: #10b981; font-size: 24px; }}
                        </style>
                    </head>
                    <body>
                        <div class="success">✓ Ticket Activado</div>
                        <p>Duración: {result.get('minutes', 0)} minutos</p>
                        <p>Ya puedes navegar por internet.</p>
                    </body>
                    </html>
                    """
                    self.wfile.write(success_html.encode("utf-8"))
                else:
                    # Error - show reason
                    reason = result.get("reason", "unknown_error")
                    self.send_response(400)
                    self.send_header("Content-Type", "text/html; charset=utf-8")
                    self.end_headers()

                    error_html = f"""
                    <!DOCTYPE html>
                    <html>
                    <head>
                        <meta charset="utf-8">
                        <meta name="viewport" content="width=device-width, initial-scale=1">
                        <title>Error de Activación</title>
                        <style>
                            body {{ font-family: sans-serif; text-align: center; padding: 50px; }}
                            .error {{ color: #ef4444; font-size: 20px; }}
                        </style>
                    </head>
                    <body>
                        <div class="error">✗ Error al Activar</div>
                        <p>Razón: {reason}</p>
                        <a href="/">← Volver</a>
                    </body>
                    </html>
                    """
                    self.wfile.write(error_html.encode("utf-8"))
            else:
                self.send_error(500, "Activation handler not configured")

        else:
            self.send_error(404, "Not Found")

    def _get_mac_from_ip(self, ip: str) -> str | None:
        """
        Get MAC address from IP using ARP.
        Fallback for FirewallClient.get_mac_from_ip()
        """
        try:
            import subprocess
            result = subprocess.run(
                ["arp", "-n", ip],
                capture_output=True,
                text=True,
                timeout=2
            )

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


class PortalServer:
    """
    Lightweight captive portal HTTP server.
    Uses Python stdlib http.server for minimal footprint.
    """

    def __init__(
        self,
        host: str = "0.0.0.0",
        port: int = 8080,
        portal_html: str = "",
        activate_callback: Callable = None
    ):
        """
        Initialize portal server

        Args:
            host: Bind address (0.0.0.0 = all interfaces)
            port: HTTP port (usually 80 or 8080)
            portal_html: HTML content to serve
            activate_callback: Function to call when ticket is activated
        """
        self.host = host
        self.port = port
        self.portal_html = portal_html
        self.activate_callback = activate_callback
        self.server: HTTPServer | None = None

        # Set class variables for handler
        PortalHandler.portal_html = self.portal_html
        PortalHandler.activate_callback = self.activate_callback

    def start(self):
        """Start the HTTP server (blocking)"""
        try:
            self.server = HTTPServer((self.host, self.port), PortalHandler)
            log.info(f"Portal server listening on {self.host}:{self.port}")
            self.server.serve_forever()
        except KeyboardInterrupt:
            log.info("Portal server interrupted")
            self.stop()
        except Exception as e:
            log.error(f"Portal server error: {e}")
            raise

    def stop(self):
        """Stop the HTTP server"""
        if self.server:
            log.info("Stopping portal server")
            self.server.shutdown()
            self.server.server_close()


def get_default_portal_html() -> str:
    """
    Return minimal fallback HTML if backend is unreachable.
    Real HTML should be fetched from /api/v1/portal/
    """
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <title>Portal JADSlink</title>
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body {
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                display: flex;
                align-items: center;
                justify-content: center;
                padding: 20px;
            }
            .container {
                background: white;
                padding: 40px;
                border-radius: 16px;
                box-shadow: 0 20px 60px rgba(0,0,0,0.3);
                max-width: 400px;
                width: 100%;
                text-align: center;
            }
            h1 { color: #1a202c; margin-bottom: 10px; font-size: 28px; }
            p { color: #718096; margin-bottom: 30px; }
            input {
                width: 100%;
                padding: 12px;
                border: 2px solid #e2e8f0;
                border-radius: 8px;
                font-size: 16px;
                margin-bottom: 15px;
                text-transform: uppercase;
            }
            button {
                width: 100%;
                padding: 12px;
                background: #667eea;
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 16px;
                font-weight: 600;
                cursor: pointer;
            }
            button:hover { background: #5568d3; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🌐 JADSlink</h1>
            <p>Ingresa tu código de ticket</p>
            <form method="POST" action="/activate">
                <input type="text" name="code" placeholder="Código" maxlength="8" required autofocus>
                <button type="submit">Activar</button>
            </form>
        </div>
    </body>
    </html>
    """


# Example usage
if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(name)s %(levelname)s %(message)s"
    )

    def example_activate(code: str, mac: str) -> Dict[str, Any]:
        """Example activation callback"""
        log.info(f"Activating code={code} for mac={mac}")
        # In real usage, this would call agent.activate()
        return {"ok": True, "minutes": 30}

    # Create and start server
    server = PortalServer(
        host="0.0.0.0",
        port=8080,
        portal_html=get_default_portal_html(),
        activate_callback=example_activate
    )

    log.info("Starting example portal server")
    server.start()
