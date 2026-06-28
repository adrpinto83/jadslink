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
    "portal_footer":   "Desarrollado por JADS Software",
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
body{font-family:Arial,sans-serif;background:linear-gradient(135deg,#0a0a1a,#0d1b3e,#1a0a2e);min-height:100vh;display:flex;align-items:center;justify-content:center}
.box{background:rgba(255,255,255,0.07);backdrop-filter:blur(12px);border:1px solid rgba(255,255,255,0.12);padding:44px 36px;border-radius:20px;text-align:center;width:90%;max-width:420px;box-shadow:0 20px 60px rgba(0,0,0,0.5)}
.logo{max-width:160px;max-height:80px;margin:0 auto 16px;display:block}
h1{font-size:30px;font-weight:800;letter-spacing:2px;margin-bottom:4px;background:linear-gradient(90deg,@@COLOR1@@,@@COLOR2@@);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text}
.tagline{color:#7a8aaa;font-size:12px;letter-spacing:1px;text-transform:uppercase;margin-bottom:24px}
.prompt{color:#c0cce8;font-size:14px;margin-bottom:14px;font-weight:500}
#errmsg{display:none;color:#fc8181;font-size:13px;margin-bottom:14px;background:rgba(252,129,129,0.10);border:1px solid rgba(252,129,129,0.30);padding:10px 14px;border-radius:8px}
input[name="username"]{width:100%;padding:16px;font-size:24px;letter-spacing:10px;text-align:center;text-transform:uppercase;border:2px solid @@COLOR1@@66;border-radius:12px;background:rgba(0,0,0,0.4);color:#fff;outline:none}
input[name="username"]:focus{border-color:@@COLOR1@@}
input[name="username"]::placeholder{letter-spacing:2px;font-size:14px;text-transform:none;color:#4a5568}
button{width:100%;margin-top:14px;padding:16px;font-size:16px;font-weight:700;letter-spacing:1px;background:linear-gradient(90deg,@@COLOR1@@,@@COLOR2@@);color:#fff;border:none;border-radius:12px;cursor:pointer}
.footer{margin-top:28px;color:#4a5568;font-size:11px;line-height:1.9}
.footer a{color:@@COLOR1@@;text-decoration:none}
</style>
</head>
<body>
<div class="box">
  @@LOGO@@
  <h1>@@TITLE@@</h1>
  <p class="tagline">@@TAGLINE@@</p>
  <p class="prompt">@@PROMPT@@</p>
  <div id="errmsg">C&oacute;digo incorrecto. Por favor verifica e intenta de nuevo.</div>
  <form method="get" action="$authaction">
    <input type="hidden" name="tok" value="$tok">
    <input type="hidden" name="redir" value="$redir">
    <input type="text" name="username"
           placeholder="@@PROMPT@@"
           maxlength="12"
           autocapitalize="characters"
           autocomplete="off"
           autocorrect="off"
           spellcheck="false"
           required>
    <button type="submit">@@BUTTON@@</button>
  </form>
  <div class="footer">@@FOOTER@@</div>
</div>
<script>
try {
  if (sessionStorage.getItem('jads_tried')) {
    document.getElementById('errmsg').style.display = 'block';
  }
  document.querySelector('form').addEventListener('submit', function() {
    var code = document.querySelector('[name="username"]').value.trim();
    if (code.length > 0) sessionStorage.setItem('jads_tried', '1');
  });
} catch(e) {}
</script>
</body>
</html>
"""


def render_splash(cfg: dict, overrides: dict | None = None) -> str:
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
    footer  = _text(pick("portal_footer"),  DEFAULTS["portal_footer"])
    color1  = _color(pick("portal_color1"), DEFAULTS["portal_color1"])
    color2  = _color(pick("portal_color2"), DEFAULTS["portal_color2"])
    logo    = (pick("portal_logo_url") or "").strip()

    logo_html = ""
    if logo and re.match(r"^https?://", logo):
        logo_html = f'<img class="logo" src="{html.escape(logo, quote=True)}" alt="logo">'

    out = TEMPLATE
    out = out.replace("@@TITLE@@", title)
    out = out.replace("@@TAGLINE@@", tagline)
    out = out.replace("@@PROMPT@@", prompt)
    out = out.replace("@@BUTTON@@", button)
    out = out.replace("@@FOOTER@@", footer)
    out = out.replace("@@COLOR1@@", color1)
    out = out.replace("@@COLOR2@@", color2)
    out = out.replace("@@LOGO@@", logo_html)
    return out


@router.get("/splash", response_class=HTMLResponse)
def get_splash(device_id: str, request: Request, db: Session = Depends(get_db)):
    """Página HTML del portal cautivo (pública). El agente la descarga y la
    escribe en /etc/nodogsplash/htdocs/splash.html. El dashboard la usa como
    preview pasando overrides por query string."""
    device = db.query(Device).filter(Device.id == device_id).first()
    cfg = device.config if device else {}

    # Overrides de preview: solo claves portal_*
    overrides = {k: v for k, v in request.query_params.items() if k.startswith("portal_")}
    html_out = render_splash(cfg, overrides)
    return HTMLResponse(content=html_out, headers={"Cache-Control": "no-store"})
