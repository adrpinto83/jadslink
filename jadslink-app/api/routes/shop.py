"""Venta online de códigos de acceso.

Flujo (pagos locales VE, sin pasarela):
  comprador abre /buy/{device_id} (QR o link del splash)
    → elige producto (duración/precio definidos por el operador)
    → paga por pago móvil/zelle/usdt según los datos de cobro del operador
    → reporta la referencia → se crea un CodeOrder (pending) con token público
  operador aprueba desde el panel (pestaña Ventas)
    → se genera el código, se encola al router (add_codes) y el comprador
      lo ve en su página de estado (polling con el token).
"""
import os, secrets, html
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from ..database import get_db
from ..models import Account, Device, CodeProduct, CodeOrder, Command, Code, User
from .auth import require_user, require_manage
from .codes import gen_code
from ..scope import is_superadmin
from .. import billing, ratelimit

router = APIRouter(tags=["shop"])

METHODS = {"pago_movil", "transferencia", "zelle", "usdt", "efectivo"}
CODE_EXPIRES_HOURS = 720  # el código comprado vale 30 días para activarse


# ── Helpers ───────────────────────────────────────────────────────────────────

def _device_or_404(device_id: str, db: Session) -> Device:
    d = db.query(Device).filter(Device.id == device_id).first()
    if not d or not d.account_id:
        raise HTTPException(status_code=404, detail="Dispositivo no encontrado")
    return d


def _account_of(device: Device, db: Session) -> Account:
    return db.query(Account).filter(Account.id == device.account_id).first()


def _active_products(account_id: str, db: Session):
    return (db.query(CodeProduct)
            .filter(CodeProduct.account_id == account_id, CodeProduct.is_active == True)
            .order_by(CodeProduct.sort_order.asc(), CodeProduct.duration_min.asc())
            .all())


def _configured_methods(account: Account) -> dict:
    pm = account.payment_methods or {}
    return {k: v for k, v in pm.items() if k in METHODS and str(v).strip()}


def shop_enabled(device: Device, db: Session) -> bool:
    """La tienda existe si la cuenta está operativa, tiene productos y datos de cobro."""
    acc = _account_of(device, db)
    if not acc or billing.account_blocked(acc):
        return False
    return bool(_active_products(acc.id, db)) and bool(_configured_methods(acc))


def _product_dict(p: CodeProduct) -> dict:
    return {
        "id": p.id, "name": p.name, "duration_min": p.duration_min,
        "price_usd": p.price_usd, "price_ves": p.price_ves,
        "bandwidth_dn": p.bandwidth_dn, "bandwidth_up": p.bandwidth_up,
        "is_active": p.is_active, "sort_order": p.sort_order,
    }


def _order_public_dict(o: CodeOrder) -> dict:
    return {
        "token": o.token, "status": o.status,
        "product_name": o.product_name, "duration_min": o.duration_min,
        "price_usd": o.price_usd, "method": o.method, "reference": o.reference,
        "code": o.code if o.status == "approved" else "",
        "review_note": o.review_note if o.status == "rejected" else "",
        "created_at": o.created_at.isoformat() if o.created_at else None,
    }


def _order_admin_dict(o: CodeOrder, device_name: str = "") -> dict:
    d = _order_public_dict(o)
    d.update({
        "id": o.id, "device_id": o.device_id, "device_name": device_name,
        "buyer_name": o.buyer_name, "buyer_phone": o.buyer_phone,
        "code": o.code, "review_note": o.review_note,
        "reviewed_at": o.reviewed_at.isoformat() if o.reviewed_at else None,
    })
    return d


# ═══ API pública (comprador, sin auth) ════════════════════════════════════════

@router.get("/api/shop/{device_id}")
def shop_info(device_id: str, request: Request, db: Session = Depends(get_db)):
    ratelimit.check(f"shop:info:{ratelimit.client_ip(request)}", limit=30, window_sec=60)
    device = _device_or_404(device_id, db)
    acc = _account_of(device, db)
    if not acc:
        raise HTTPException(status_code=404, detail="Dispositivo no encontrado")
    cfg = device.config or {}
    enabled = shop_enabled(device, db)
    return {
        "enabled": enabled,
        "device_name": device.name,
        "operator_name": acc.name,
        "branding": {
            "title":  cfg.get("portal_title") or "JADSLink",
            "color1": cfg.get("portal_color1") or "#4f8ef7",
            "color2": cfg.get("portal_color2") or "#a259f7",
            "logo":   cfg.get("portal_logo_url") or "",
        },
        "products": [_product_dict(p) for p in _active_products(acc.id, db)] if enabled else [],
        "payment_methods": _configured_methods(acc) if enabled else {},
        "contact_phone": acc.contact_phone or "",
    }


class OrderCreate(BaseModel):
    product_id: int
    method: str
    reference: str = ""
    buyer_name: str = ""
    buyer_phone: str = ""


@router.post("/api/shop/{device_id}/orders")
def create_order(device_id: str, payload: OrderCreate, request: Request, db: Session = Depends(get_db)):
    ip = ratelimit.client_ip(request)
    ratelimit.check(f"shop:order:{ip}", limit=6, window_sec=3600)

    device = _device_or_404(device_id, db)
    acc = _account_of(device, db)
    if not acc or billing.account_blocked(acc):
        raise HTTPException(status_code=403, detail="Tienda no disponible")

    product = db.query(CodeProduct).filter(
        CodeProduct.id == payload.product_id,
        CodeProduct.account_id == acc.id,
        CodeProduct.is_active == True,
    ).first()
    if not product:
        raise HTTPException(status_code=400, detail="Producto no válido")

    method = payload.method.strip()
    if method not in _configured_methods(acc):
        raise HTTPException(status_code=400, detail="Método de pago no disponible")

    reference = payload.reference.strip()[:80]
    if method != "efectivo" and len(reference) < 4:
        raise HTTPException(status_code=400, detail="Indica el número de referencia del pago")

    order = CodeOrder(
        token=secrets.token_urlsafe(16),
        account_id=acc.id,
        device_id=device.id,
        product_id=product.id,
        product_name=product.name,
        duration_min=product.duration_min,
        price_usd=product.price_usd,
        bandwidth_dn=product.bandwidth_dn,
        bandwidth_up=product.bandwidth_up,
        buyer_name=payload.buyer_name.strip()[:60],
        buyer_phone=payload.buyer_phone.strip()[:30],
        method=method,
        reference=reference,
        buyer_ip=ip,
    )
    db.add(order)
    db.commit()
    return {"token": order.token, "status": order.status}


@router.get("/api/shop/orders/{token}")
def order_status(token: str, request: Request, db: Session = Depends(get_db)):
    ratelimit.check(f"shop:status:{ratelimit.client_ip(request)}", limit=30, window_sec=60)
    o = db.query(CodeOrder).filter(CodeOrder.token == token).first()
    if not o:
        raise HTTPException(status_code=404, detail="Pedido no encontrado")
    return _order_public_dict(o)


# ═══ API del operador (panel) ═════════════════════════════════════════════════

class ProductCreate(BaseModel):
    name: str
    duration_min: int = 60
    price_usd: float = 0.0
    price_ves: float = 0.0
    bandwidth_dn: int = 0
    bandwidth_up: int = 0
    sort_order: int = 0
    account_id: Optional[str] = None   # solo superadmin


class ProductUpdate(BaseModel):
    name: Optional[str] = None
    duration_min: Optional[int] = None
    price_usd: Optional[float] = None
    price_ves: Optional[float] = None
    bandwidth_dn: Optional[int] = None
    bandwidth_up: Optional[int] = None
    is_active: Optional[bool] = None
    sort_order: Optional[int] = None


class RejectPayload(BaseModel):
    note: str = ""


def _resolve_account(user: User, payload_account_id: Optional[str], db: Session) -> str:
    if is_superadmin(user):
        if not payload_account_id:
            raise HTTPException(status_code=400, detail="account_id requerido para superadmin")
        return payload_account_id
    return user.account_id


@router.get("/api/products")
def list_products(account_id: Optional[str] = None, db: Session = Depends(get_db), user: User = Depends(require_user)):
    q = db.query(CodeProduct)
    if is_superadmin(user):
        if account_id:
            q = q.filter(CodeProduct.account_id == account_id)
    else:
        q = q.filter(CodeProduct.account_id == user.account_id)
    return [_product_dict(p) | {"account_id": p.account_id}
            for p in q.order_by(CodeProduct.sort_order.asc(), CodeProduct.duration_min.asc()).all()]


@router.post("/api/products")
def create_product(payload: ProductCreate, db: Session = Depends(get_db), user: User = Depends(require_manage)):
    name = payload.name.strip()
    if not name:
        raise HTTPException(status_code=400, detail="Nombre requerido")
    if payload.duration_min <= 0 or payload.price_usd < 0:
        raise HTTPException(status_code=400, detail="Duración o precio inválido")
    p = CodeProduct(
        account_id=_resolve_account(user, payload.account_id, db),
        name=name, duration_min=payload.duration_min,
        price_usd=payload.price_usd, price_ves=payload.price_ves,
        bandwidth_dn=payload.bandwidth_dn, bandwidth_up=payload.bandwidth_up,
        sort_order=payload.sort_order,
    )
    db.add(p)
    db.commit()
    return _product_dict(p)


def _owned_product(product_id: int, user: User, db: Session) -> CodeProduct:
    p = db.query(CodeProduct).filter(CodeProduct.id == product_id).first()
    if not p or (not is_superadmin(user) and p.account_id != user.account_id):
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    return p


@router.patch("/api/products/{product_id}")
def update_product(product_id: int, payload: ProductUpdate, db: Session = Depends(get_db), user: User = Depends(require_manage)):
    p = _owned_product(product_id, user, db)
    for field in ("name", "duration_min", "price_usd", "price_ves",
                  "bandwidth_dn", "bandwidth_up", "is_active", "sort_order"):
        val = getattr(payload, field)
        if val is not None:
            setattr(p, field, val)
    db.commit()
    return _product_dict(p)


@router.delete("/api/products/{product_id}")
def delete_product(product_id: int, db: Session = Depends(get_db), user: User = Depends(require_manage)):
    p = _owned_product(product_id, user, db)
    p.is_active = False   # soft: los pedidos históricos conservan el snapshot
    db.commit()
    return {"ok": True}


@router.get("/api/orders")
def list_orders(status: Optional[str] = None, db: Session = Depends(get_db), user: User = Depends(require_user)):
    q = db.query(CodeOrder, Device.name).join(Device, CodeOrder.device_id == Device.id)
    if not is_superadmin(user):
        q = q.filter(CodeOrder.account_id == user.account_id)
    if status:
        q = q.filter(CodeOrder.status == status)
    rows = q.order_by(CodeOrder.created_at.desc()).limit(500).all()
    return [_order_admin_dict(o, name) for o, name in rows]


def _owned_order(order_id: int, user: User, db: Session) -> CodeOrder:
    o = db.query(CodeOrder).filter(CodeOrder.id == order_id).first()
    if not o or (not is_superadmin(user) and o.account_id != user.account_id):
        raise HTTPException(status_code=404, detail="Pedido no encontrado")
    return o


@router.post("/api/orders/{order_id}/approve")
def approve_order(order_id: int, db: Session = Depends(get_db), user: User = Depends(require_manage)):
    o = _owned_order(order_id, user, db)
    if o.status != "pending":
        raise HTTPException(status_code=400, detail="El pedido ya fue procesado")
    acc = db.query(Account).filter(Account.id == o.account_id).first()
    if acc and billing.account_blocked(acc):
        raise HTTPException(status_code=403, detail="Cuenta suspendida")

    # Generar y entregar el código (mismo camino que la generación manual)
    code = gen_code()
    expires_at = datetime.utcnow() + timedelta(hours=CODE_EXPIRES_HOURS)
    db.add(Code(
        device_id=o.device_id, code=code,
        duration_min=o.duration_min, max_uses=1,
        bandwidth_dn=o.bandwidth_dn, bandwidth_up=o.bandwidth_up,
        expires_at=expires_at, note=f"venta online #{o.id}",
    ))
    db.add(Command(
        device_id=o.device_id, action="add_codes",
        payload={
            "codes": [code], "duration_min": o.duration_min, "max_uses": 1,
            "bandwidth_dn": o.bandwidth_dn, "bandwidth_up": o.bandwidth_up,
            "expires_at": int(expires_at.timestamp()),
        },
    ))
    o.status = "approved"
    o.code = code
    o.reviewed_by, o.reviewed_at = user.id, datetime.utcnow()
    db.commit()
    return {"ok": True, "code": code}


@router.post("/api/orders/{order_id}/reject")
def reject_order(order_id: int, payload: RejectPayload, db: Session = Depends(get_db), user: User = Depends(require_manage)):
    o = _owned_order(order_id, user, db)
    if o.status != "pending":
        raise HTTPException(status_code=400, detail="El pedido ya fue procesado")
    o.status = "rejected"
    o.review_note = payload.note.strip()[:200]
    o.reviewed_by, o.reviewed_at = user.id, datetime.utcnow()
    db.commit()
    return {"ok": True}


# ═══ Página pública de compra ═════════════════════════════════════════════════

BUY_TEMPLATE = """<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Comprar acceso WiFi</title>
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:-apple-system,'Segoe UI',Arial,sans-serif;background:linear-gradient(135deg,#060d1f 0%,#0d1b3e 50%,#130a2e 100%);min-height:100vh;color:#fff;padding:16px;display:flex;justify-content:center}
.wrap{width:100%;max-width:430px}
.card{background:rgba(255,255,255,.06);backdrop-filter:blur(14px);border:1px solid rgba(255,255,255,.1);border-radius:20px;padding:24px 20px;margin-bottom:14px}
h1{font-size:22px;font-weight:800;letter-spacing:1px;background:linear-gradient(90deg,@@C1@@,@@C2@@);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;text-align:center}
.sub{color:#7a8aaa;font-size:12px;text-align:center;margin:4px 0 4px}
.step-label{font-size:11px;letter-spacing:1.5px;text-transform:uppercase;color:#5a7aaa;margin:14px 0 10px}
.prod{display:flex;justify-content:space-between;align-items:center;border:2px solid rgba(255,255,255,.1);border-radius:14px;padding:14px;margin-bottom:10px;cursor:pointer;transition:border-color .15s}
.prod.sel{border-color:@@C1@@;background:rgba(255,255,255,.05)}
.prod-name{font-weight:700;font-size:15px}
.prod-dur{color:#7a8aaa;font-size:12px;margin-top:2px}
.prod-price{font-weight:800;font-size:17px;color:@@C1@@;text-align:right}
.prod-ves{display:block;font-size:11px;color:#7a8aaa;font-weight:500}
.pm{border:2px solid rgba(255,255,255,.1);border-radius:12px;padding:12px;margin-bottom:8px;cursor:pointer}
.pm.sel{border-color:@@C1@@}
.pm-name{font-weight:700;font-size:14px;text-transform:capitalize}
.pm-detail{display:none;color:#a8b8d8;font-size:13px;margin-top:8px;white-space:pre-wrap;background:rgba(0,0,0,.25);border-radius:8px;padding:10px}
.pm.sel .pm-detail{display:block}
input,select{width:100%;padding:12px;border-radius:10px;border:1px solid rgba(255,255,255,.15);background:rgba(0,0,0,.3);color:#fff;font-size:15px;margin-bottom:10px;outline:none}
input:focus{border-color:@@C1@@}
button.main{width:100%;padding:15px;border:none;border-radius:12px;background:linear-gradient(90deg,@@C1@@,@@C2@@);color:#fff;font-size:15px;font-weight:700;letter-spacing:1px;cursor:pointer;margin-top:6px}
button.main:disabled{opacity:.5}
.err{display:none;color:#fc8181;font-size:13px;background:rgba(252,129,129,.08);border:1px solid rgba(252,129,129,.25);padding:10px;border-radius:10px;margin-bottom:10px}
.status-icon{font-size:44px;text-align:center;margin:10px 0}
.status-title{text-align:center;font-size:18px;font-weight:700;margin-bottom:6px}
.status-sub{text-align:center;color:#a8b8d8;font-size:13px;line-height:1.6}
.code-box{margin:18px auto;text-align:center}
.code-val{font-size:30px;font-weight:800;letter-spacing:6px;background:rgba(0,0,0,.35);border:2px dashed @@C1@@;border-radius:14px;padding:16px 10px;margin:10px 0}
.qr{width:130px;height:130px;border-radius:10px;margin:8px auto;display:block}
.link-btn{display:block;text-align:center;color:#5a7aaa;font-size:13px;margin-top:14px;background:none;border:none;cursor:pointer;width:100%;text-decoration:underline}
.hidden{display:none}
.foot{text-align:center;color:#3d4f6e;font-size:11px;margin-top:6px}
.foot a{color:#5a7aaa;text-decoration:none}
.spin{display:inline-block;width:14px;height:14px;border:2px solid rgba(255,255,255,.3);border-top-color:#fff;border-radius:50%;animation:sp 1s linear infinite;vertical-align:-2px;margin-right:6px}
@keyframes sp{to{transform:rotate(360deg)}}
</style>
</head>
<body>
<div class="wrap">
  <div class="card">
    <h1>@@TITLE@@</h1>
    <p class="sub">@@DEVICE@@ · Compra tu código de acceso WiFi</p>
  </div>

  <div class="card" id="shop-closed" style="display:none">
    <div class="status-icon">🚫</div>
    <div class="status-title">Tienda no disponible</div>
    <p class="status-sub">Este punto de venta no está activo en este momento.</p>
  </div>

  <div class="card hidden" id="step-buy">
    <div class="err" id="buy-err"></div>
    <div class="step-label">1 · Elige tu plan</div>
    <div id="products"></div>
    <div class="step-label">2 · Paga y reporta</div>
    <div id="methods"></div>
    <input id="reference" placeholder="Nº de referencia del pago" maxlength="80">
    <input id="buyer-phone" placeholder="Tu teléfono (opcional)" maxlength="30">
    <button class="main" id="submit-btn">Reportar pago y pedir mi código</button>
  </div>

  <div class="card hidden" id="step-status">
    <div id="st-pending">
      <div class="status-icon">⏳</div>
      <div class="status-title">Verificando tu pago…</div>
      <p class="status-sub">El operador está confirmando tu pago.<br>Esta página se actualiza sola — no la cierres.<br><span class="spin"></span><span id="poll-info">consultando…</span></p>
    </div>
    <div id="st-approved" class="hidden">
      <div class="status-icon">✅</div>
      <div class="status-title">¡Pago confirmado!</div>
      <div class="code-box">
        <p class="status-sub">Tu código de acceso (<span id="ok-dur"></span>):</p>
        <div class="code-val" id="ok-code"></div>
        <img class="qr" id="ok-qr" alt="QR">
        <p class="status-sub">Conéctate al WiFi <strong>@@DEVICE@@</strong> e ingresa este código en el portal.</p>
      </div>
    </div>
    <div id="st-rejected" class="hidden">
      <div class="status-icon">❌</div>
      <div class="status-title">Pago rechazado</div>
      <p class="status-sub" id="rej-note"></p>
    </div>
    <button class="link-btn" id="new-order-btn">Hacer otra compra</button>
  </div>

  <p class="foot">Desarrollado por <a href="https://jadsstudio.com" target="_blank" rel="noopener">JADS Studio</a> · JADSLink</p>
</div>

<script>
var DEVICE_ID = "@@DEVICE_ID@@";
var API = "";
var LSKEY = "jads_order_" + DEVICE_ID;
var shop = null, selProduct = null, selMethod = null, pollTimer = null;

function $(id){ return document.getElementById(id); }
function esc(s){ var d=document.createElement('div'); d.textContent=s==null?'':String(s); return d.innerHTML; }

function fmtDur(m){
  if (m >= 1440 && m % 1440 === 0) { var d=m/1440; return d + (d>1?' días':' día'); }
  if (m >= 60 && m % 60 === 0) { var h=m/60; return h + (h>1?' horas':' hora'); }
  return m + ' min';
}

var PM_LABEL = {pago_movil:'Pago Móvil', transferencia:'Transferencia', zelle:'Zelle', usdt:'USDT', efectivo:'Efectivo'};

function renderShop(){
  $('products').innerHTML = shop.products.map(function(p){
    return '<div class="prod" data-id="'+p.id+'" onclick="pickProduct('+p.id+')">'
      + '<div><div class="prod-name">'+esc(p.name)+'</div><div class="prod-dur">'+fmtDur(p.duration_min)+' de acceso</div></div>'
      + '<div class="prod-price">$'+p.price_usd.toFixed(2)
      + (p.price_ves>0 ? '<span class="prod-ves">Bs. '+p.price_ves.toFixed(2)+'</span>' : '')
      + '</div></div>';
  }).join('');
  $('methods').innerHTML = Object.keys(shop.payment_methods).map(function(m){
    return '<div class="pm" data-m="'+m+'" onclick="pickMethod(\\''+m+'\\')">'
      + '<div class="pm-name">'+ (PM_LABEL[m]||m) +'</div>'
      + '<div class="pm-detail">'+esc(shop.payment_methods[m])+'</div></div>';
  }).join('');
}

function pickProduct(id){
  selProduct = id;
  document.querySelectorAll('.prod').forEach(function(el){
    el.classList.toggle('sel', el.getAttribute('data-id') == String(id));
  });
}
function pickMethod(m){
  selMethod = m;
  document.querySelectorAll('.pm').forEach(function(el){
    el.classList.toggle('sel', el.getAttribute('data-m') === m);
  });
}

function showErr(msg){ var e=$('buy-err'); e.textContent=msg; e.style.display='block'; }

$('submit-btn').addEventListener('click', function(){
  $('buy-err').style.display='none';
  if (!selProduct) return showErr('Elige un plan primero');
  if (!selMethod)  return showErr('Elige el método de pago');
  var ref = $('reference').value.trim();
  if (selMethod !== 'efectivo' && ref.length < 4) return showErr('Indica el número de referencia de tu pago');
  var btn = $('submit-btn'); btn.disabled = true; btn.textContent = 'Enviando…';
  fetch(API + '/api/shop/' + DEVICE_ID + '/orders', {
    method:'POST', headers:{'Content-Type':'application/json'},
    body: JSON.stringify({product_id:selProduct, method:selMethod, reference:ref, buyer_phone:$('buyer-phone').value.trim()})
  }).then(function(r){ return r.json().then(function(d){ return {ok:r.ok, d:d}; }); })
    .then(function(res){
      if (!res.ok) { showErr(res.d.detail || 'No se pudo crear el pedido'); btn.disabled=false; btn.textContent='Reportar pago y pedir mi código'; return; }
      localStorage.setItem(LSKEY, res.d.token);
      showStatus(res.d.token);
    })
    .catch(function(){ showErr('Error de red, intenta de nuevo'); btn.disabled=false; btn.textContent='Reportar pago y pedir mi código'; });
});

function showStatus(token){
  $('step-buy').classList.add('hidden');
  $('step-status').classList.remove('hidden');
  poll(token);
  pollTimer = setInterval(function(){ poll(token); }, 8000);
}

function poll(token){
  fetch(API + '/api/shop/orders/' + encodeURIComponent(token))
    .then(function(r){ if(!r.ok) throw 0; return r.json(); })
    .then(function(o){
      $('poll-info').textContent = 'pedido: ' + o.product_name + ' · $' + o.price_usd.toFixed(2);
      if (o.status === 'approved') {
        clearInterval(pollTimer);
        $('st-pending').classList.add('hidden');
        $('st-approved').classList.remove('hidden');
        $('ok-code').textContent = o.code;
        $('ok-dur').textContent = fmtDur(o.duration_min);
        $('ok-qr').src = 'https://api.qrserver.com/v1/create-qr-code/?size=130x130&data=' + encodeURIComponent(o.code) + '&bgcolor=0d1b3e&color=ffffff&margin=4';
      } else if (o.status === 'rejected') {
        clearInterval(pollTimer);
        $('st-pending').classList.add('hidden');
        $('st-rejected').classList.remove('hidden');
        $('rej-note').textContent = o.review_note || 'Contacta al operador para más información.';
        localStorage.removeItem(LSKEY);
      }
    })
    .catch(function(){ /* reintenta en el próximo poll */ });
}

$('new-order-btn').addEventListener('click', function(){
  localStorage.removeItem(LSKEY);
  clearInterval(pollTimer);
  $('step-status').classList.add('hidden');
  $('st-pending').classList.remove('hidden');
  $('st-approved').classList.add('hidden');
  $('st-rejected').classList.add('hidden');
  $('step-buy').classList.remove('hidden');
});

fetch(API + '/api/shop/' + DEVICE_ID)
  .then(function(r){ if(!r.ok) throw 0; return r.json(); })
  .then(function(s){
    shop = s;
    if (!s.enabled) { $('shop-closed').style.display='block'; return; }
    renderShop();
    var saved = localStorage.getItem(LSKEY);
    if (saved) { showStatus(saved); } else { $('step-buy').classList.remove('hidden'); }
  })
  .catch(function(){ $('shop-closed').style.display='block'; });
</script>
</body>
</html>
"""


@router.get("/buy/{device_id}", response_class=HTMLResponse)
def buy_page(device_id: str, request: Request, db: Session = Depends(get_db)):
    """Página pública de compra (mobile-first, con el branding del operador)."""
    ratelimit.check(f"shop:page:{ratelimit.client_ip(request)}", limit=30, window_sec=60)
    device = _device_or_404(device_id, db)
    cfg = device.config or {}

    import re as _re
    def _color(v, default):
        v = (v or "").strip()
        return v if _re.match(r"^#[0-9A-Fa-f]{3,8}$", v) else default

    out = BUY_TEMPLATE
    out = out.replace("@@DEVICE_ID@@", html.escape(device.id, quote=True))
    out = out.replace("@@TITLE@@", html.escape(cfg.get("portal_title") or "JADSLink"))
    out = out.replace("@@DEVICE@@", html.escape(device.name))
    out = out.replace("@@C1@@", _color(cfg.get("portal_color1"), "#4f8ef7"))
    out = out.replace("@@C2@@", _color(cfg.get("portal_color2"), "#a259f7"))
    return HTMLResponse(content=out, headers={"Cache-Control": "no-store"})
