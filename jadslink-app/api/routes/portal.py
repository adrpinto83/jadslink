"""Portal cautivo: renderiza el splash.html de NoDogSplash con el branding
del operador. La nube es la única fuente de verdad; el agente del router solo
descarga el HTML ya renderizado (ver hotspot-agent.sh -> update_portal).

El HTML resultante conserva las variables literales de NoDogSplash
($authaction, $tok, $redir) para que NDS las sustituya al servir la página.
"""
import re, html
from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Device

router = APIRouter(prefix="/api/devices/{device_id}/portal", tags=["portal"])

DEFAULTS = {
    "portal_title":    "JADSLink",
    "portal_tagline":  "Internet • Acceso WiFi",
    "portal_prompt":   "Ingresa tu código de acceso",
    "portal_button":   "CONECTAR",
    "portal_color1":   "#4f8ef7",
    "portal_color2":   "#a259f7",
    "portal_footer":   "",
    "portal_logo_url": "",
}

_HEX = re.compile(r"^#[0-9A-Fa-f]{3,8}$")


def _color(val: str, default: str) -> str:
    val = (val or "").strip()
    return val if _HEX.match(val) else default


def _text(val: str, default: str) -> str:
    val = (val if val is not None else default)
    return html.escape(str(val), quote=True)


TEMPLATE = """<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta http-equiv="Cache-Control" content="no-cache, no-store, must-revalidate">
<meta http-equiv="Pragma" content="no-cache">
<meta http-equiv="Expires" content="0">
<title>@@TITLE@@ - Acceso WiFi</title>
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:Arial,sans-serif;background:linear-gradient(135deg,#060d1f 0%,#0d1b3e 50%,#130a2e 100%);min-height:100vh;display:flex;flex-direction:column;align-items:center;justify-content:center;padding:20px}
.box{background:rgba(255,255,255,0.06);backdrop-filter:blur(16px);-webkit-backdrop-filter:blur(16px);border:1px solid rgba(255,255,255,0.10);padding:40px 32px 32px;border-radius:24px;text-align:center;width:100%;max-width:400px;box-shadow:0 24px 64px rgba(0,0,0,0.6)}
.logo{max-width:150px;max-height:72px;margin:0 auto 18px;display:block;border-radius:8px}
.wifi-icon{margin:0 auto 18px;display:block;width:54px;height:46px}
h1{font-size:28px;font-weight:800;letter-spacing:2px;margin-bottom:6px;background:linear-gradient(90deg,@@COLOR1@@,@@COLOR2@@);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text}
.tagline{color:#6b7da0;font-size:11px;letter-spacing:2px;text-transform:uppercase;margin-bottom:28px}
.prompt{color:#a8b8d8;font-size:14px;margin-bottom:12px;font-weight:500}
#errmsg{display:none;color:#fc8181;font-size:13px;margin-bottom:14px;background:rgba(252,129,129,0.08);border:1px solid rgba(252,129,129,0.25);padding:10px 14px;border-radius:10px}
input[name="username"]{width:100%;padding:15px 12px;font-size:26px;letter-spacing:10px;text-align:center;text-transform:uppercase;border:2px solid rgba(@@COLOR1_RGB@@,0.35);border-radius:14px;background:rgba(0,0,0,0.35);color:#fff;outline:none;transition:border-color .2s}
input[name="username"]:focus{border-color:@@COLOR1@@;box-shadow:0 0 0 3px rgba(@@COLOR1_RGB@@,0.15)}
input[name="username"]::placeholder{letter-spacing:3px;font-size:13px;text-transform:none;color:#3a4a68}
button{width:100%;margin-top:14px;padding:15px;font-size:15px;font-weight:700;letter-spacing:1.5px;background:linear-gradient(90deg,@@COLOR1@@,@@COLOR2@@);color:#fff;border:none;border-radius:14px;cursor:pointer;transition:opacity .2s,transform .1s}
button:hover{opacity:.9}
button:active{transform:scale(.98)}
.op-footer{margin-top:22px;color:#3d4f6e;font-size:11px;line-height:1.8}
.op-footer a{color:#5a7aaa;text-decoration:none}
.divider{width:48px;height:1px;background:rgba(255,255,255,0.08);margin:20px auto 18px}
.powered{display:flex;align-items:center;justify-content:center;gap:8px;text-decoration:none}
.powered-label{font-size:10px;color:#3a4a68;letter-spacing:1.5px;text-transform:uppercase}
.powered-brand{display:flex;align-items:center;gap:5px}
.jads-logo-mini{width:18px;height:15px;flex-shrink:0}
.powered-name{font-size:12px;font-weight:700;letter-spacing:.5px;background:linear-gradient(90deg,@@COLOR1@@,@@COLOR2@@);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text}
.powered:hover .powered-name{opacity:.8}
.ad-chip{display:inline-block;margin-top:10px;padding:5px 12px;border:1px solid rgba(@@COLOR1_RGB@@,0.25);border-radius:20px;font-size:10px;color:#5a7aaa;letter-spacing:.5px;text-decoration:none;transition:border-color .2s,color .2s}
.ad-chip:hover{border-color:@@COLOR1@@;color:@@COLOR1@@}
.hidden{display:none}
.support-link{display:flex;align-items:center;justify-content:center;gap:8px;width:100%;margin-top:12px;padding:12px;font-size:13px;font-weight:600;letter-spacing:.3px;background:rgba(37,211,102,0.12);color:#25d366;border:1px solid rgba(37,211,102,0.35);border-radius:14px;text-decoration:none;transition:background .2s}
.support-link:hover{background:rgba(37,211,102,0.2)}
.support-link svg{width:18px;height:18px;flex-shrink:0}
</style>
</head>
<body>
<div class="box">
  @@LOGO@@
  <svg class="wifi-icon @@LOGO_HIDE@@" viewBox="0 0 54 46" fill="none" xmlns="http://www.w3.org/2000/svg">
    <path d="M2 10C9.74 3.6 19.44 0 27 0s17.26 3.6 25 10" stroke="@@COLOR1@@" stroke-width="3.5" stroke-linecap="round" opacity=".25"/>
    <path d="M7 18C13.6 11.6 20.6 9 27 9s13.4 2.6 20 9" stroke="@@COLOR1@@" stroke-width="3.5" stroke-linecap="round" opacity=".5"/>
    <path d="M13.5 26C18 21.2 22.4 19 27 19s9 2.2 13.5 7" stroke="@@COLOR1@@" stroke-width="3.5" stroke-linecap="round" opacity=".8"/>
    <circle cx="27" cy="38" r="5" fill="@@COLOR1@@"/>
  </svg>
  <h1>@@TITLE@@</h1>
  <p class="tagline">@@TAGLINE@@</p>
  <p class="prompt">@@PROMPT@@</p>
  <div id="errmsg">C&oacute;digo incorrecto. Por favor verifica e intenta de nuevo.</div>
  <form method="get" action="$authaction">
    <input type="hidden" name="tok" value="$tok">
    <input type="hidden" name="redir" value="$redir">
    <input type="text" name="username" id="code-input"
           placeholder="XXXXXXXX"
           maxlength="12"
           autocapitalize="characters"
           autocomplete="off"
           autocorrect="off"
           spellcheck="false"
           required>
    <button type="submit">@@BUTTON@@</button>
  </form>
  <a class="support-link" href="https://wa.me/584124767466?text=Hola%2C%20necesito%20ayuda%20con%20mi%20acceso%20WiFi" target="_blank" rel="noopener">
    <svg viewBox="0 0 24 24" fill="currentColor"><path d="M12.04 2c-5.52 0-10 4.48-10 10 0 1.76.46 3.48 1.34 5L2 22l5.14-1.35c1.46.8 3.1 1.22 4.9 1.22 5.52 0 10-4.48 10-10s-4.48-10-10-10zm0 18.15c-1.56 0-3.1-.42-4.44-1.2l-.32-.19-3.05.8.81-2.97-.21-.31A8.14 8.14 0 013.85 12c0-4.5 3.67-8.15 8.19-8.15 4.5 0 8.15 3.65 8.15 8.15s-3.65 8.15-8.15 8.15zm4.47-6.1c-.24-.12-1.45-.72-1.68-.8-.22-.08-.39-.12-.55.12-.16.24-.63.8-.78.96-.14.16-.28.18-.53.06-.24-.12-1.02-.38-1.95-1.2-.72-.64-1.2-1.44-1.35-1.68-.14-.24-.02-.37.11-.5.11-.11.24-.28.36-.42.12-.14.16-.24.24-.4.08-.16.04-.3-.02-.42-.06-.12-.55-1.32-.75-1.8-.2-.48-.4-.42-.55-.42-.14 0-.3-.02-.46-.02-.16 0-.42.06-.64.3-.22.24-.84.82-.84 2s.86 2.32.98 2.48c.12.16 1.7 2.6 4.12 3.64.58.25 1.03.4 1.38.51.58.18 1.11.16 1.53.1.47-.07 1.45-.59 1.65-1.16.2-.57.2-1.06.14-1.16-.06-.1-.22-.16-.46-.28z"/></svg>
    Soporte por WhatsApp
  </a>
  @@OP_FOOTER@@
  <div class="divider"></div>
  <a class="powered" href="https://jadsstudio.com" target="_blank" rel="noopener">
    <span class="powered-label">Desarrollado por</span>
    <span class="powered-brand">
      <svg class="jads-logo-mini" viewBox="0 0 26 22" fill="none" xmlns="http://www.w3.org/2000/svg">
        <path d="M1 5C4.87 1.8 9.72 0 13 0s8.13 1.8 12 5" stroke="@@COLOR1@@" stroke-width="2" stroke-linecap="round" opacity=".4"/>
        <path d="M3.5 8.5C6.8 5.8 9.8 4.5 13 4.5s6.2 1.3 9.5 4" stroke="@@COLOR1@@" stroke-width="2" stroke-linecap="round" opacity=".7"/>
        <path d="M6.5 12C8.9 10 10.9 9 13 9s4.1 1 6.5 3" stroke="@@COLOR1@@" stroke-width="2" stroke-linecap="round"/>
        <circle cx="13" cy="18" r="2.5" fill="@@COLOR1@@"/>
      </svg>
      <span class="powered-name">JADS Studio</span>
    </span>
  </a>
  @@BUY_CHIP@@
  <a class="ad-chip" href="https://jadsstudio.com" target="_blank" rel="noopener">Plataforma WiFi para tu negocio &rarr;</a>
</div>
<script>
try {
  if (sessionStorage.getItem('jads_tried')) {
    document.getElementById('errmsg').style.display = 'block';
  }
  document.querySelector('form').addEventListener('submit', function(e) {
    if (e.target.tagName === 'FORM') {
      var code = document.querySelector('[name="username"]').value.trim();
      if (code.length > 0) sessionStorage.setItem('jads_tried', '1');
    }
  });
} catch(e) {}
</script>
</body>
</html>
"""


def _hex_to_rgb(hex_color: str) -> str:
    """Convert #rrggbb to 'r,g,b' for use in rgba()."""
    h = hex_color.lstrip("#")
    if len(h) == 3:
        h = h[0]*2 + h[1]*2 + h[2]*2
    try:
        r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
        return f"{r},{g},{b}"
    except Exception:
        return "79,142,247"


def render_splash(cfg: dict, overrides: dict | None = None, buy_url: str = "") -> str:
    """Renderiza el splash a partir de la config del device, con overrides
    opcionales (usados para el preview en vivo del dashboard)."""
    cfg = cfg or {}
    overrides = overrides or {}

    def pick(key):
        if key in overrides and overrides[key] not in (None, ""):
            return overrides[key]
        if cfg.get(key) not in (None, ""):
            return cfg[key]
        return DEFAULTS[key]

    title   = _text(pick("portal_title"),   DEFAULTS["portal_title"])
    tagline = _text(pick("portal_tagline"), DEFAULTS["portal_tagline"])
    prompt  = _text(pick("portal_prompt"),  DEFAULTS["portal_prompt"])
    button  = _text(pick("portal_button"),  DEFAULTS["portal_button"])
    footer  = pick("portal_footer") or ""
    color1  = _color(pick("portal_color1"), DEFAULTS["portal_color1"])
    color2  = _color(pick("portal_color2"), DEFAULTS["portal_color2"])
    logo    = (pick("portal_logo_url") or "").strip()

    logo_html = ""
    logo_hide = ""
    if logo and re.match(r"^https?://", logo):
        logo_html = f'<img class="logo" src="{html.escape(logo, quote=True)}" alt="logo">'
        logo_hide = "hidden"

    op_footer_html = ""
    if footer:
        op_footer_html = f'<div class="op-footer">{html.escape(str(footer))}</div>'

    buy_chip = ""
    if buy_url:
        buy_chip = (f'<a class="ad-chip" href="{html.escape(buy_url, quote=True)}" '
                    f'target="_blank" rel="noopener">&#128179; &iquest;No tienes c&oacute;digo? '
                    f'C&oacute;mpralo aqu&iacute; (usa tus datos m&oacute;viles) &rarr;</a>')

    out = TEMPLATE
    out = out.replace("@@BUY_CHIP@@", buy_chip)
    out = out.replace("@@TITLE@@", title)
    out = out.replace("@@TAGLINE@@", tagline)
    out = out.replace("@@PROMPT@@", prompt)
    out = out.replace("@@BUTTON@@", button)
    out = out.replace("@@OP_FOOTER@@", op_footer_html)
    out = out.replace("@@COLOR1_RGB@@", _hex_to_rgb(color1))
    out = out.replace("@@COLOR1@@", color1)
    out = out.replace("@@COLOR2@@", color2)
    out = out.replace("@@LOGO@@", logo_html)
    out = out.replace("@@LOGO_HIDE@@", logo_hide)
    return out


@router.get("/splash", response_class=HTMLResponse)
def get_splash(device_id: str, request: Request, db: Session = Depends(get_db)):
    """Página HTML del portal cautivo (pública). El agente la descarga y la
    escribe en /etc/nodogsplash/htdocs/splash.html. El dashboard la usa como
    preview pasando overrides por query string."""
    import os
    device = db.query(Device).filter(Device.id == device_id).first()
    cfg = device.config if device else {}

    # Link de compra online: aparece solo si el operador tiene la tienda lista
    # (productos activos + datos de cobro). El comprador la abre con datos móviles.
    buy_url = ""
    if device:
        from .shop import shop_enabled
        if shop_enabled(device, db):
            public_url = os.getenv("PUBLIC_URL", "https://link.jadsstudio.com")
            buy_url = f"{public_url}/buy/{device.id}"

    # Overrides de preview: solo claves portal_*
    overrides = {k: v for k, v in request.query_params.items() if k.startswith("portal_")}
    html_out = render_splash(cfg, overrides, buy_url=buy_url)
    return HTMLResponse(content=html_out, headers={"Cache-Control": "no-store"})
