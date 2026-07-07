/* JADSLink Cloud Manager */
const API = "";
let token = localStorage.getItem("hcm_token") || "";
let username = localStorage.getItem("hcm_user") || "";
let userRole = localStorage.getItem("hcm_role") || "";
let devices = [];
let currentDevice = null;
let pollInterval = null;
let myAccount = null;   // cuenta del usuario (null si superadmin)

// ── Tema (Claro/Oscuro) ───────────────────────────────────────────────────────

const theme = {
  current: localStorage.getItem("hcm_theme") || "dark",

  init() {
    this.apply(this.current);
    document.querySelectorAll(".js-theme-toggle").forEach(btn => {
      btn.addEventListener("click", () => this.toggle());
    });
    this.updateIcon();
  },

  apply(themeName) {
    this.current = themeName;
    document.documentElement.setAttribute("data-theme", themeName);
    localStorage.setItem("hcm_theme", themeName);
    this.updateIcon();
  },

  toggle() {
    this.apply(this.current === "dark" ? "light" : "dark");
  },

  updateIcon() {
    const title = this.current === "dark" ? "Cambiar a tema claro" : "Cambiar a tema oscuro";
    document.querySelectorAll(".js-theme-toggle").forEach(btn => {
      const icon = btn.querySelector("i");
      if (icon) icon.className = this.current === "dark" ? "fa-solid fa-moon" : "fa-solid fa-sun";
      btn.title = title;
    });
  }
};

// Aplicar tema al cargar
theme.init();

// ── Utilidades ────────────────────────────────────────────────────────────────

async function api(method, path, body) {
  const opts = {
    method,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
  };
  if (body) opts.body = JSON.stringify(body);
  const r = await fetch(API + path, opts);
  if (r.status === 401) { logout(); return null; }
  return r.ok ? r.json() : null;
}

// Abre en una pestaña nueva un recurso que requiere Authorization (el token
// nunca viaja en la URL: las query strings quedan en logs de proxys).
function openAuthed(path) {
  const w = window.open("", "_blank");
  fetch(API + path, { headers: token ? { Authorization: `Bearer ${token}` } : {} })
    .then(r => { if (!r.ok) throw new Error(r.status); return r.blob(); })
    .then(b => { w.location = URL.createObjectURL(b); })
    .catch(() => { if (w) w.close(); alert("No se pudo abrir el documento"); });
}

function fmt_bytes(b) {
  if (!b) return "0 B";
  if (b < 1024) return `${b} B`;
  if (b < 1048576) return `${(b/1024).toFixed(1)} KB`;
  return `${(b/1048576).toFixed(1)} MB`;
}

function fmt_uptime(s) {
  const h = Math.floor(s / 3600), m = Math.floor((s % 3600) / 60);
  return `${h}h ${m}m`;
}

function time_ago(iso) {
  if (!iso) return "—";
  const diff = (Date.now() - new Date(iso + "Z")) / 1000;
  if (diff < 60) return `hace ${Math.round(diff)}s`;
  if (diff < 3600) return `hace ${Math.round(diff/60)}m`;
  if (diff < 86400) return `hace ${Math.round(diff/3600)}h`;
  return `hace ${Math.round(diff/86400)}d`;
}

function fmt_dt(iso) {
  if (!iso) return "—";
  const d = new Date(iso + "Z");
  return d.toLocaleDateString("es") + " " + d.toLocaleTimeString("es", {hour:"2-digit",minute:"2-digit"});
}

function copyText(text, btn) {
  navigator.clipboard.writeText(text).then(() => {
    const orig = btn.innerHTML;
    btn.innerHTML = '<i class="fa-solid fa-check"></i>';
    setTimeout(() => btn.innerHTML = orig, 1500);
  });
}

// ── Auth ──────────────────────────────────────────────────────────────────────

document.getElementById("login-form").addEventListener("submit", async e => {
  e.preventDefault();
  const r = await fetch("/api/auth/login", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      username: document.getElementById("login-user").value,
      password: document.getElementById("login-pass").value,
    }),
  });
  if (r.ok) {
    const d = await r.json();
    token = d.token; username = d.username; userRole = d.role || "";
    localStorage.setItem("hcm_token", token);
    localStorage.setItem("hcm_user", username);
    localStorage.setItem("hcm_role", userRole);
    showDashboard();
  } else {
    // Mostrar el motivo real: 429 = rate limit (esperar), 401 = credenciales
    const d = await r.json().catch(() => ({}));
    document.getElementById("login-error").textContent =
      d.detail || "Usuario o contraseña incorrectos";
    document.getElementById("login-error").classList.remove("hidden");
  }
});

function showSignup() {
  document.getElementById("landing-screen").classList.remove("active");
  document.getElementById("login-screen").classList.add("active");
  document.getElementById("login-form").classList.add("hidden");
  document.getElementById("toggle-signup").classList.add("hidden");
  document.getElementById("signup-form").classList.remove("hidden");
  document.getElementById("toggle-login").classList.remove("hidden");
  document.getElementById("login-subtitle").textContent = "Crea tu cuenta de operador";
}
function showLogin() {
  document.getElementById("landing-screen").classList.remove("active");
  document.getElementById("login-screen").classList.add("active");
  document.getElementById("signup-form").classList.add("hidden");
  document.getElementById("toggle-login").classList.add("hidden");
  document.getElementById("login-form").classList.remove("hidden");
  document.getElementById("toggle-signup").classList.remove("hidden");
  document.getElementById("login-subtitle").textContent = "Panel de administración";
}

document.getElementById("signup-form").addEventListener("submit", async e => {
  e.preventDefault();
  const err = document.getElementById("signup-error");
  err.classList.add("hidden");
  const resp = await fetch("/api/signup", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      company_name: document.getElementById("su-company").value,
      username: document.getElementById("su-user").value,
      password: document.getElementById("su-pass").value,
      email: document.getElementById("su-email").value,
      contact_phone: document.getElementById("su-phone").value,
    }),
  });
  if (resp.ok) {
    const d = await resp.json();
    token = d.token; username = d.username; userRole = d.role || "";
    localStorage.setItem("hcm_token", token);
    localStorage.setItem("hcm_user", username);
    localStorage.setItem("hcm_role", userRole);
    showDashboard();
  } else {
    const e2 = await resp.json().catch(() => ({}));
    err.textContent = e2.detail || "No se pudo crear la cuenta";
    err.classList.remove("hidden");
  }
});

function logout() {
  token = ""; username = ""; userRole = "";
  localStorage.removeItem("hcm_token");
  localStorage.removeItem("hcm_user");
  localStorage.removeItem("hcm_role");
  clearInterval(pollInterval);
  document.getElementById("dashboard-screen").classList.remove("active");
  document.getElementById("login-screen").classList.add("active");
}

document.getElementById("logout-btn").addEventListener("click", logout);

// ── Dashboard ─────────────────────────────────────────────────────────────────

function showDashboard() {
  document.getElementById("login-screen").classList.remove("active");
  document.getElementById("dashboard-screen").classList.add("active");
  // Mostrar la sección Cuentas solo al superadmin
  document.getElementById("nav-accounts").style.display =
    userRole === "superadmin" ? "" : "none";
  loadMe();
  loadDevices();
  pollInterval = setInterval(loadDevices, 30000);
}

async function loadMe() {
  const me = await api("GET", "/api/auth/me");
  const roleLabel = { superadmin: "Superadmin", owner: "Dueño", manager: "Gestor", viewer: "Lector" };
  let label = username;
  if (me) {
    const rl = roleLabel[me.role] || me.role;
    label = me.account ? `${username} · ${me.account.name}` : `${username} · ${rl}`;
    if (me.role === "superadmin") label = `${username} · Superadmin`;
  }
  document.getElementById("nav-user").textContent = label;
  myAccount = me && me.account ? me.account : null;
  renderUsageBanner(me);
  applyRoleUI();
}

// Muestra/oculta acciones según el rol del usuario (RBAC en la UI; el backend es el guardián real).
function applyRoleUI() {
  const isViewer = userRole === "viewer";
  const isOwnerOrSuper = userRole === "owner" || userRole === "superadmin";
  const show = (id, on) => { const el = document.getElementById(id); if (el) el.style.display = on ? "" : "none"; };
  // viewer = solo lectura: no registra routers ni genera códigos
  show("btn-register-gateway", !isViewer);
  show("btn-open-codes", !isViewer);
  // solo el owner (o superadmin) reporta pagos
  show("payment-form", isOwnerOrSuper);
}

function renderUsageBanner(me) {
  const el = document.getElementById("usage-banner");
  if (!me || !me.account || !me.account.usage) { el.classList.add("hidden"); return; }
  const u = me.account.usage;
  const q = me.account.quota || {};
  const suspended = me.account.status === "suspended" || me.account.status === "canceled";
  const maxTxt = u.max_devices == null ? "∞" : u.max_devices;
  const pct = u.max_devices == null ? Math.min(100, (u.device_count / Math.max(u.included_devices,1)) * 100)
                                    : (u.device_count / u.max_devices) * 100;
  const extraTxt = u.extra_devices > 0
    ? `<span class="u-item"><strong>+${u.extra_devices}</strong> extra ($${u.extra_cost}/mes)</span>` : "";

  // Cuota de tickets
  let ticketsTxt = "";
  if (q.unlimited) {
    ticketsTxt = `<span class="u-item"><i class="fa-solid fa-ticket"></i> Tickets <strong>ilimitados</strong></span>`;
  } else {
    const ticketsAvail = q.available || 0;
    const ticketsUsed = q.used || 0;
    const ticketsLimit = q.limit || 0;
    const ticketsPct = ticketsLimit > 0 ? Math.min(100, (ticketsUsed / ticketsLimit) * 100) : 0;
    const lowTickets = ticketsAvail < 20 && ticketsLimit > 0;
    const bonusTxt = q.bonus > 0 ? `<span style="color:var(--accent2)">+${q.bonus} bonus</span>` : "";
    ticketsTxt = `
      <span class="u-item ${lowTickets ? 'u-low' : ''}"><i class="fa-solid fa-ticket"></i> Tickets: <strong>${ticketsAvail}</strong> disponibles ${bonusTxt}</span>
      <span class="u-item-sm">(${ticketsUsed}/${ticketsLimit} usados este mes)</span>`;
  }

  el.classList.toggle("u-warn", suspended || u.at_limit);
  el.classList.remove("hidden");
  el.innerHTML = `
    <span class="u-plan"><i class="fa-solid fa-gem"></i> ${u.plan_name || u.plan}${suspended ? " — SUSPENDIDA" : ""}</span>
    <span class="u-item"><strong>${u.device_count}</strong> / ${maxTxt} routers</span>
    <div class="u-bar"><span style="width:${Math.min(100,pct)}%"></span></div>
    <span class="u-item">${u.included_devices} incluidos</span>
    ${extraTxt}
    ${ticketsTxt}
    <span class="u-item">Total <strong>$${u.total_monthly}/mes</strong></span>`;
}

// ── Navigation ────────────────────────────────────────────────────────────────

document.querySelectorAll(".nav-item").forEach(el => {
  el.addEventListener("click", () => {
    document.querySelectorAll(".nav-item").forEach(i => i.classList.remove("active"));
    document.querySelectorAll(".tab").forEach(t => t.classList.remove("active"));
    el.classList.add("active");
    document.getElementById(`tab-${el.dataset.tab}`).classList.add("active");
    if (el.dataset.tab === "clients")  loadClients();
    if (el.dataset.tab === "logs")     loadLogs();
    if (el.dataset.tab === "codes")    loadCodes();
    if (el.dataset.tab === "reports")  loadReports();
    if (el.dataset.tab === "config")   loadConfig();
    if (el.dataset.tab === "portal")   loadPortal();
    if (el.dataset.tab === "settings") loadSettings();
    if (el.dataset.tab === "accounts") loadAccounts();
    if (el.dataset.tab === "payments") loadPayments();
    if (el.dataset.tab === "sales")    loadSales();
  });
});

// ── Venta online de códigos ─────────────────────────────────────────────────────

let salesAccountId = null;   // cuenta cuya tienda se está configurando
let PRODUCTS_CACHE = [];
let editingProductId = null; // producto en edición inline dentro de la tabla de Ventas

function loadSales() {
  const isViewer = userRole === "viewer";
  document.getElementById("sales-operator").style.display = isViewer ? "none" : "";
  loadOrders();
  if (isViewer) return;
  if (userRole === "superadmin") {
    setupSalesAccountPicker();   // el superadmin elige qué cuenta configurar
  } else {
    salesAccountId = myAccount ? myAccount.id : null;
    refreshSalesConfig();
  }
}

async function setupSalesAccountPicker() {
  document.getElementById("sales-account-picker").style.display = "";
  const sel = document.getElementById("sales-account-select");
  const accs = await api("GET", "/api/accounts") || [];
  sel.innerHTML = accs.map(a => `<option value="${a.id}">${a.name} (${a.plan})</option>`).join("");
  if (!salesAccountId || !accs.some(a => a.id === salesAccountId)) {
    salesAccountId = accs.length ? accs[0].id : null;
  }
  sel.value = salesAccountId || "";
  sel.onchange = () => { salesAccountId = sel.value; refreshSalesConfig(); };
  refreshSalesConfig();
}

function refreshSalesConfig() {
  if (!salesAccountId) return;
  loadProducts();
  loadPayMethods();
  renderSalesLink();
}

async function loadOrders() {
  const orders = await api("GET", "/api/orders") || [];
  const canManage = userRole !== "viewer";
  const pending = orders.filter(o => o.status === "pending");
  document.getElementById("orders-pending").innerHTML = pending.map(o => `
    <tr>
      <td style="color:var(--muted)">${fmt_dt(o.created_at)}</td>
      <td>${o.device_name}</td>
      <td><strong>${o.product_name}</strong></td>
      <td>$${o.price_usd.toFixed(2)}</td>
      <td>${METHOD_LABEL[o.method] || o.method}</td>
      <td>${o.reference || "—"}</td>
      <td>${o.buyer_phone || "—"}</td>
      <td style="white-space:nowrap">${canManage ? `
        <button class="btn-sm" style="background:var(--accent2)" onclick="approveOrder(${o.id})">Aprobar</button>
        <button class="btn-sm" onclick="rejectOrder(${o.id})">Rechazar</button>` : ""}
      </td>
    </tr>`).join("") || '<tr><td colspan="8" style="text-align:center;color:var(--muted);padding:24px">No hay pedidos pendientes</td></tr>';

  const hist = orders.filter(o => o.status !== "pending").slice(0, 50);
  document.getElementById("orders-history").innerHTML = hist.map(o => `
    <tr>
      <td style="color:var(--muted)">${fmt_dt(o.created_at)}</td>
      <td>${o.device_name}</td>
      <td>${o.product_name}</td>
      <td>$${o.price_usd.toFixed(2)}</td>
      <td>${METHOD_LABEL[o.method] || o.method}</td>
      <td>${o.reference || "—"}</td>
      <td><code>${o.code || "—"}</code></td>
      <td>${PAY_STATUS[o.status] || o.status}</td>
    </tr>`).join("") || '<tr><td colspan="8" style="text-align:center;color:var(--muted);padding:24px">Sin ventas todavía</td></tr>';
}

async function approveOrder(id) {
  if (!confirm("¿Confirmas que recibiste este pago? Se generará y entregará el código.")) return;
  if (await api("POST", `/api/orders/${id}/approve`)) loadOrders();
}

async function rejectOrder(id) {
  const note = prompt("Motivo del rechazo (lo verá el comprador):", "No se encontró el pago");
  if (note === null) return;
  if (await api("POST", `/api/orders/${id}/reject`, { note })) loadOrders();
}

async function loadProducts() {
  const q = userRole === "superadmin" ? `?account_id=${encodeURIComponent(salesAccountId)}` : "";
  PRODUCTS_CACHE = await api("GET", "/api/products" + q) || [];
  renderProducts();
}

function currentBsRate() {
  return (typeof currencySystem !== "undefined" && currencySystem.exchangeRate) || null;
}

function renderProducts() {
  const rate = currentBsRate();
  document.getElementById("products-table").innerHTML = PRODUCTS_CACHE.map(p => {
    if (p.id === editingProductId) {
      return `
    <tr>
      <td><input type="text" id="edit-name-${p.id}" value="${p.name}" style="width:100%"></td>
      <td><input type="number" id="edit-dur-${p.id}" min="1" value="${p.duration_min}" style="width:80px"></td>
      <td><input type="number" id="edit-usd-${p.id}" step="0.01" min="0" value="${p.price_usd}" style="width:90px"></td>
      <td>
        <input type="number" id="edit-ves-${p.id}" step="0.01" min="0" value="${p.price_ves || 0}" style="width:100px">
        ${rate ? `<button type="button" class="btn-sm" title="Calcular con la tasa actual (1 USD = ${rate.toFixed(2)} Bs)" onclick="applyRateToEdit(${p.id})"><i class="fa-solid fa-rotate"></i></button>` : ""}
      </td>
      <td>${p.is_active ? '<span class="badge badge-green">activo</span>' : '<span class="badge badge-gray">inactivo</span>'}</td>
      <td style="white-space:nowrap">
        <button class="btn-sm" style="background:var(--accent2)" onclick="saveProduct(${p.id})">Guardar</button>
        <button class="btn-sm" onclick="cancelEditProduct()">Cancelar</button>
      </td>
    </tr>`;
    }
    return `
    <tr style="${p.is_active ? "" : "opacity:.45"}">
      <td><strong>${p.name}</strong></td>
      <td>${p.duration_min} min</td>
      <td>$${p.price_usd.toFixed(2)}</td>
      <td>${p.price_ves > 0 ? "Bs. " + p.price_ves.toFixed(2) : (rate ? `<span style="color:var(--muted)">≈ Bs. ${(p.price_usd * rate).toFixed(2)}</span>` : "—")}</td>
      <td>${p.is_active ? '<span class="badge badge-green">activo</span>' : '<span class="badge badge-gray">inactivo</span>'}</td>
      <td style="white-space:nowrap">
        <button class="btn-sm" onclick="editProduct(${p.id})">Editar</button>
        <button class="btn-sm" onclick="toggleProduct(${p.id}, ${!p.is_active})">${p.is_active ? "Desactivar" : "Activar"}</button>
      </td>
    </tr>`;
  }).join("") || '<tr><td colspan="6" style="text-align:center;color:var(--muted);padding:24px">Crea tu primer producto para activar la tienda</td></tr>';
}

function editProduct(id) {
  editingProductId = id;
  renderProducts();
}

function cancelEditProduct() {
  editingProductId = null;
  renderProducts();
}

function applyRateToEdit(id) {
  const rate = currentBsRate();
  const usd = parseFloat(document.getElementById(`edit-usd-${id}`).value) || 0;
  if (rate) document.getElementById(`edit-ves-${id}`).value = (usd * rate).toFixed(2);
}

async function saveProduct(id) {
  const name = document.getElementById(`edit-name-${id}`).value.trim();
  const duration_min = parseInt(document.getElementById(`edit-dur-${id}`).value, 10);
  const price_usd = parseFloat(document.getElementById(`edit-usd-${id}`).value);
  const price_ves = parseFloat(document.getElementById(`edit-ves-${id}`).value) || 0;
  if (!name || !duration_min || duration_min <= 0 || isNaN(price_usd) || price_usd < 0) {
    return alert("Revisa los datos: nombre, duración y precio USD son requeridos");
  }
  const r = await api("PATCH", `/api/products/${id}`, { name, duration_min, price_usd, price_ves });
  if (r) { editingProductId = null; loadProducts(); }
}

document.getElementById("product-form").addEventListener("submit", async e => {
  e.preventDefault();
  const r = await api("POST", "/api/products", {
    name: document.getElementById("prod-name").value,
    duration_min: parseInt(document.getElementById("prod-dur").value, 10),
    price_usd: parseFloat(document.getElementById("prod-usd").value),
    price_ves: parseFloat(document.getElementById("prod-ves").value) || 0,
    account_id: salesAccountId,   // requerido para superadmin; ignorado para operador
  });
  if (r) { document.getElementById("product-form").reset(); document.getElementById("prod-dur").value = 60; loadProducts(); }
});

function applyRateToNewProduct() {
  const rate = currentBsRate();
  const usd = parseFloat(document.getElementById("prod-usd").value) || 0;
  if (rate) document.getElementById("prod-ves").value = (usd * rate).toFixed(2);
}

async function toggleProduct(id, active) {
  if (await api("PATCH", `/api/products/${id}`, { is_active: active })) loadProducts();
}

const PM_KEYS = ["pago_movil", "transferencia", "zelle", "usdt", "efectivo"];

async function loadPayMethods() {
  if (!salesAccountId) return;
  const acc = await api("GET", `/api/accounts/${salesAccountId}`);
  const pm = (acc && acc.payment_methods) || {};
  PM_KEYS.forEach(k => { const el = document.getElementById("pm-" + k); if (el) el.value = pm[k] || ""; });
  // datos de cobro: los edita el owner de la cuenta o el superadmin
  const canEdit = userRole === "owner" || userRole === "superadmin";
  PM_KEYS.forEach(k => { const el = document.getElementById("pm-" + k); if (el) el.disabled = !canEdit; });
  document.querySelector("#paymethods-form .form-actions").style.display = canEdit ? "" : "none";
}

document.getElementById("paymethods-form").addEventListener("submit", async e => {
  e.preventDefault();
  const pm = {};
  PM_KEYS.forEach(k => { const v = document.getElementById("pm-" + k).value.trim(); if (v) pm[k] = v; });
  const msg = document.getElementById("pm-msg");
  const r = await api("PATCH", `/api/accounts/${salesAccountId}`, { payment_methods: pm });
  msg.textContent = r ? "✓ Datos de cobro guardados" : "✗ No se pudo guardar";
  msg.className = r ? "success" : "error";
  msg.classList.remove("hidden");
  setTimeout(() => msg.classList.add("hidden"), 3000);
});

function renderSalesLink() {
  const sel = document.getElementById("sales-device-select");
  const mine = devices.filter(d => userRole !== "superadmin" || d.account_id === salesAccountId);
  sel.innerHTML = mine.map(d => `<option value="${d.id}">${d.name}</option>`).join("")
    || '<option value="">(esta cuenta no tiene routers)</option>';
  updateSalesLink();
}

function updateSalesLink() {
  const devId = document.getElementById("sales-device-select").value;
  if (!devId) return;
  const url = `${window.location.origin}/buy/${devId}`;
  document.getElementById("sales-link").textContent = url;
  document.getElementById("sales-qr").src =
    `https://api.qrserver.com/v1/create-qr-code/?size=110x110&data=${encodeURIComponent(url)}&margin=4`;
}

document.getElementById("sales-device-select").addEventListener("change", updateSalesLink);

function copySalesLink(btn) {
  copyText(document.getElementById("sales-link").textContent, btn);
}

// ── Pagos y facturación ─────────────────────────────────────────────────────────

const METHOD_LABEL = { pago_movil:"Pago móvil", transferencia:"Transferencia", zelle:"Zelle", usdt:"USDT", efectivo:"Efectivo" };
const PAY_STATUS = {
  pending:  '<span class="badge badge-gray">pendiente</span>',
  approved: '<span class="badge badge-green">aprobado</span>',
  rejected: '<span class="badge badge-red">rechazado</span>',
};

function loadPayments() {
  const isSuper = userRole === "superadmin";
  document.getElementById("pay-admin").style.display = isSuper ? "" : "none";
  document.getElementById("pay-operator").style.display = isSuper ? "none" : "";
  if (isSuper) loadPendingPayments();
  else loadMyPayments();
}

async function loadPendingPayments() {
  const rows = await api("GET", "/api/payments?status=pending") || [];
  document.getElementById("pay-pending").innerHTML = rows.map(p => `
    <tr>
      <td style="color:var(--muted)">${fmt_dt(p.created_at)}</td>
      <td><strong>${p.account_name}</strong></td>
      <td>$${p.amount_usd}</td>
      <td>${METHOD_LABEL[p.method] || p.method}</td>
      <td>${p.reference || "—"}</td>
      <td>${p.has_proof ? `<a href="#" onclick="openAuthed('/api/payments/${p.id}/proof');return false">ver</a>` : "—"}</td>
      <td style="white-space:nowrap">
        <button class="btn-sm" style="background:var(--accent2)" onclick="approvePayment(${p.id})">Aprobar</button>
        <button class="btn-sm" onclick="rejectPayment(${p.id})">Rechazar</button>
      </td>
    </tr>`).join("") || '<tr><td colspan="7" style="text-align:center;color:var(--muted);padding:24px">No hay pagos pendientes</td></tr>';
}

async function approvePayment(id) {
  if (await api("POST", `/api/payments/${id}/approve`)) loadPendingPayments();
}
async function rejectPayment(id) {
  const note = prompt("Motivo del rechazo (opcional):") ?? "";
  if (await api("POST", `/api/payments/${id}/reject`, { note })) loadPendingPayments();
}

async function loadMyPayments() {
  if (!PLANS.length) PLANS = await api("GET", "/api/plans") || [];
  renderBillingSummary();
  if (!myAccount) return;
  const rows = await api("GET", `/api/accounts/${myAccount.id}/payments`) || [];
  document.getElementById("pay-history").innerHTML = rows.map(p => `
    <tr>
      <td style="color:var(--muted)">${fmt_dt(p.created_at)}</td>
      <td>$${p.amount_usd}</td>
      <td>${METHOD_LABEL[p.method] || p.method}</td>
      <td>${p.reference || "—"}</td>
      <td>${PAY_STATUS[p.status] || p.status}${p.status==="rejected" && p.review_note ? `<br><span style="color:var(--muted);font-size:11px">${p.review_note}</span>` : ""}</td>
    </tr>`).join("") || '<tr><td colspan="5" style="text-align:center;color:var(--muted);padding:24px">Sin pagos aún</td></tr>';
}

function renderBillingSummary() {
  const el = document.getElementById("billing-summary");
  if (!myAccount) { el.classList.add("hidden"); return; }
  const b = myAccount.billing || {};
  const u = myAccount.usage || {};
  const suspended = myAccount.status === "suspended" || myAccount.status === "canceled";
  let venc = "sin vencimiento";
  if (b.billing_cycle_end) {
    const d = b.days_left;
    venc = d >= 0 ? `vence en ${d} día${d===1?"":"s"}` : `vencido hace ${-d} día${-d===1?"":"s"}`;
  }
  const planSel = (PLANS.length && userRole === "owner") ? `
    <span class="u-item">Plan:
      <select onchange="updateMyPlan(this.value)">
        ${PLANS.map(p => `<option value="${p.key}" ${p.key===u.plan?"selected":""}>${p.name} ($${p.base_price_usd})</option>`).join("")}
      </select>
    </span>` : "";
  el.classList.toggle("u-warn", suspended || b.expired);
  el.classList.remove("hidden");
  el.innerHTML = `
    <span class="u-plan"><i class="fa-solid fa-file-invoice-dollar"></i> ${u.plan_name || u.plan || ""} · $${u.total_monthly ?? 0}/mes</span>
    ${planSel}
    <span class="u-item">Estado: <strong>${myAccount.status}</strong></span>
    <span class="u-item">${venc}</span>`;
}

async function updateMyPlan(plan) {
  if (!myAccount) return;
  const r = await api("PATCH", `/api/accounts/${myAccount.id}`, { plan });
  if (r) { await loadMe(); loadMyPayments(); }
}

document.getElementById("payment-form").addEventListener("submit", async e => {
  e.preventDefault();
  if (!myAccount) return;
  const fd = new FormData();
  fd.append("amount_usd", document.getElementById("pay-amount").value);
  fd.append("method", document.getElementById("pay-method").value);
  fd.append("reference", document.getElementById("pay-ref").value);
  fd.append("note", document.getElementById("pay-note").value);
  const proof = document.getElementById("pay-proof").files[0];
  if (proof) fd.append("proof", proof);

  const msg = document.getElementById("pay-msg");
  const resp = await fetch(`/api/accounts/${myAccount.id}/payments`, {
    method: "POST", headers: { Authorization: `Bearer ${token}` }, body: fd,
  });
  if (resp.ok) {
    msg.textContent = "✓ Pago reportado. Queda pendiente de aprobación.";
    msg.className = "success"; msg.classList.remove("hidden");
    document.getElementById("payment-form").reset();
    loadMyPayments();
  } else if (resp.status === 401) {
    logout();
  } else {
    const err = await resp.json().catch(() => ({}));
    msg.textContent = "✗ " + (err.detail || "No se pudo reportar el pago");
    msg.className = "error"; msg.classList.remove("hidden");
  }
});

// ── Cuentas (superadmin) ────────────────────────────────────────────────────────

let PLANS = [];
const STATUSES = ["active", "trial", "past_due", "suspended", "canceled"];

async function loadRevenue() {
  const r = await api("GET", "/api/admin/revenue");
  if (!r) return;
  const bs = r.by_status || {};
  const cards = [
    { icon:"fa-sack-dollar", color:"#3ecf8e", bg:"#1a3d2e", val:`$${r.mrr}`, lbl:"MRR estimado" },
    { icon:"fa-building",    color:"#4f8ef7", bg:"#1a2d4a", val:r.accounts_total, lbl:`Cuentas (${bs.active||0} activas)` },
    { icon:"fa-router",      color:"#a78bfa", bg:"#2d1a3d", val:r.devices_total, lbl:"Routers totales" },
    { icon:"fa-hourglass-half", color:"#e5a53c", bg:"#3d331a", val:r.pending_payments, lbl:"Pagos por revisar" },
  ];
  document.getElementById("revenue-stats").innerHTML = cards.map(c => `
    <div class="ov-card">
      <div class="ov-icon" style="background:${c.bg}"><i class="fa-solid ${c.icon}" style="color:${c.color}"></i></div>
      <div><div class="ov-val">${c.val}</div><div class="ov-lbl">${c.lbl}</div></div>
    </div>`).join("");
}

async function loadAccounts() {
  loadRevenue();
  if (!PLANS.length) PLANS = await api("GET", "/api/plans") || [];
  const showDeleted = document.getElementById("show-deleted-accounts")?.checked || false;
  const accounts = await api("GET", `/api/accounts?include_deleted=${showDeleted}`) || [];
  const planOpts = (sel) => PLANS.map(p =>
    `<option value="${p.key}" ${p.key===sel?"selected":""}>${p.name}</option>`).join("");
  const statusOpts = (sel) => STATUSES.map(s =>
    `<option value="${s}" ${s===sel?"selected":""}>${s}</option>`).join("");

  document.getElementById("accounts-table").innerHTML = accounts.map(a => {
    const u = a.usage || {};
    const q = a.quota || {};
    const maxTxt = u.max_devices == null ? "∞" : u.max_devices;
    const isDeleted = a.deleted_at != null;
    const ticketsTxt = q.unlimited
      ? '<span class="badge badge-green">ilimitados</span>'
      : `<strong>${q.available ?? 0}</strong> disp.${q.bonus > 0 ? ` <span style="color:var(--accent2)">+${q.bonus}</span>` : ""}<br><span style="color:var(--muted);font-size:11px">${q.used ?? 0}/${q.limit ?? 0} usados</span>`;

    const actionBtns = isDeleted
      ? `<button class="btn-sm" style="background:var(--accent2)" onclick="restoreAccount('${a.id}')"><i class="fa-solid fa-rotate-left"></i></button>`
      : a.has_superadmin
      ? `<span style="color:var(--muted);font-size:11px;font-style:italic">Cuenta del sistema</span>`
      : `<button class="btn-sm" onclick="grantTickets('${a.id}','${a.name}')" title="Otorgar tickets"><i class="fa-solid fa-gift"></i></button>
         <button class="btn-sm btn-del" onclick="deleteAccount('${a.id}','${a.name}')" title="Eliminar"><i class="fa-solid fa-trash"></i></button>`;
    return `
    <tr style="${isDeleted ? 'opacity:0.5;background:#2d1a1a' : ''}">
      <td>
        <strong>${a.name}</strong>${isDeleted ? ' <span class="badge badge-red">Eliminada</span>' : ''}
        <br><span style="color:var(--muted);font-size:11px">${a.slug}</span>
      </td>
      <td><select onchange="updateAccount('${a.id}','plan',this.value)" ${isDeleted ? 'disabled' : ''}>${planOpts(a.plan)}</select></td>
      <td><select onchange="updateAccount('${a.id}','status',this.value)" ${isDeleted ? 'disabled' : ''}>${statusOpts(a.status)}</select></td>
      <td>${a.device_count} / ${maxTxt}<br><span style="color:var(--muted);font-size:11px">$${u.total_monthly ?? 0}/mes</span></td>
      <td>${ticketsTxt}</td>
      <td style="color:var(--muted)">${a.created_at ? fmt_dt(a.created_at) : "—"}</td>
      <td style="white-space:nowrap">${actionBtns}</td>
    </tr>`;
  }).join("") || '<tr><td colspan="7" style="text-align:center;color:var(--muted);padding:24px">Sin cuentas aún</td></tr>';
}

async function deleteAccount(id, name) {
  if (!confirm(`¿Eliminar la cuenta "${name}"? Los usuarios no podrán acceder, pero los datos se preservan.`)) return;
  const r = await api("DELETE", `/api/accounts/${id}`);
  if (r && r.ok) {
    alert(r.message || "Cuenta eliminada");
    loadAccounts();
  }
}

async function restoreAccount(id) {
  if (!confirm("¿Restaurar esta cuenta?")) return;
  const r = await api("POST", `/api/accounts/${id}/restore`);
  if (r && r.ok) {
    alert(r.message || "Cuenta restaurada");
    loadAccounts();
  }
}

async function grantTickets(id, name) {
  const qty = prompt(`¿Cuántos tickets bonus otorgar a "${name}"?`, "100");
  if (qty === null) return;
  const qtyNum = parseInt(qty, 10);
  if (isNaN(qtyNum) || qtyNum <= 0) return alert("Cantidad inválida");
  const note = prompt("Nota (opcional):", "") || "";
  const r = await api("POST", `/api/accounts/${id}/tickets/grant`, { quantity: qtyNum, note });
  if (r && r.ok) {
    alert(r.message || "Tickets otorgados");
    loadAccounts();
  }
}

async function updateAccount(id, field, value) {
  const r = await api("PATCH", `/api/accounts/${id}`, { [field]: value });
  if (r) {
    // Mostrar confirmación visual
    const msg = document.createElement('div');
    msg.textContent = `✓ ${field === 'plan' ? 'Plan' : 'Estado'} actualizado`;
    msg.style.cssText = 'position:fixed;top:20px;right:20px;background:var(--accent2);color:white;padding:12px 20px;border-radius:8px;z-index:9999;font-weight:600;box-shadow:0 4px 12px rgba(0,0,0,0.3)';
    document.body.appendChild(msg);
    setTimeout(() => msg.remove(), 2000);
    loadAccounts();
  }
}

document.getElementById("account-form").addEventListener("submit", async e => {
  e.preventDefault();
  const msg = document.getElementById("acc-msg");
  const r = await api("POST", "/api/accounts", {
    name: document.getElementById("acc-name").value,
    plan: document.getElementById("acc-plan").value,
    owner_username: document.getElementById("acc-user").value,
    owner_password: document.getElementById("acc-pass").value,
    owner_email: document.getElementById("acc-email").value,
    contact_phone: document.getElementById("acc-phone").value,
  });
  if (r) {
    msg.textContent = `✓ Cuenta "${r.name}" creada`;
    msg.className = "success"; msg.classList.remove("hidden");
    document.getElementById("account-form").reset();
    loadAccounts();
    setTimeout(() => { closeModal("modal-account"); msg.classList.add("hidden"); }, 1500);
  } else {
    msg.textContent = "✗ Error: el usuario ya existe o datos inválidos";
    msg.className = "error"; msg.classList.remove("hidden");
  }
});

// ── Dispositivos + Overview ───────────────────────────────────────────────────

async function loadDevices() {
  devices = await api("GET", "/api/devices") || [];
  renderDevices();
  populateDeviceSelects();
  loadOverview();
}

async function loadOverview() {
  const ov = await api("GET", "/api/devices/overview");
  if (!ov) return;

  document.getElementById("ov-devices").textContent = ov.devices_total;
  document.getElementById("ov-online").textContent = `${ov.devices_online} online`;
  document.getElementById("ov-online").className = `badge ${ov.devices_online > 0 ? "badge-green" : "badge-gray"}`;
  document.getElementById("ov-clients").textContent = ov.active_clients;
  document.getElementById("ov-codes").textContent = ov.active_codes;

  // Tabla estado de gateways
  document.getElementById("gateways-body").innerHTML = devices.map(d => `
    <tr onclick="selectDevice('${d.id}')" style="cursor:pointer">
      <td><span class="status ${d.online ? 'status-online' : 'status-offline'}"></span> <strong>${d.name}</strong></td>
      <td>${d.location || "—"}</td>
      <td>${d.active_clients ?? "—"}</td>
      <td>${time_ago(d.last_seen)}</td>
      <td><span class="badge ${d.online ? 'badge-green' : 'badge-gray'}">${d.online ? "Online" : "Offline"}</span></td>
      <td>
        <button class="btn-secondary btn-sm" onclick="event.stopPropagation();rebootDev('${d.id}')"><i class="fa-solid fa-rotate-right"></i></button>
        <button class="btn-sm btn-del" onclick="event.stopPropagation();deleteDevice('${d.id}','${d.name}')"><i class="fa-solid fa-trash"></i></button>
      </td>
    </tr>
  `).join("") || '<tr><td colspan="6" style="text-align:center;color:var(--muted)">Sin gateways registrados</td></tr>';

  // Conexiones recientes
  document.getElementById("recent-body").innerHTML = (ov.recent_connections || []).map(c => `
    <tr>
      <td>${c.device_name}</td>
      <td><code>${c.mac}</code></td>
      <td>${c.ip}</td>
      <td>${c.code_used || "—"}</td>
      <td>${fmt_dt(c.connected_at)}</td>
      <td><span class="badge ${c.active ? 'badge-green' : 'badge-gray'}">${c.active ? "Activo" : "Desconectado"}</span></td>
    </tr>
  `).join("") || '<tr><td colspan="6" style="text-align:center;color:var(--muted)">Sin conexiones recientes</td></tr>';
}

function renderDevices() {
  const grid = document.getElementById("devices-grid");
  if (!grid) return;
  grid.innerHTML = devices.map(d => `
    <div class="device-card" onclick="selectDevice('${d.id}')">
      <div class="device-name">
        <span class="status ${d.online ? 'status-online' : 'status-offline'}"></span>
        ${d.name}
      </div>
      <div class="device-meta">${d.location || "Sin ubicación"} · ${d.model}</div>
      <div class="device-meta">Visto: ${time_ago(d.last_seen)} · FW: ${d.firmware || "—"}</div>
      <div class="device-actions">
        <button class="btn-secondary btn-sm" onclick="event.stopPropagation();rebootDev('${d.id}')">Reiniciar</button>
        <button class="btn-sm btn-del" onclick="event.stopPropagation();deleteDevice('${d.id}','${d.name}')">Eliminar</button>
      </div>
    </div>
  `).join("") || '<p style="color:var(--muted)">No hay gateways. Registra uno con el botón +</p>';
}

function selectDevice(id) {
  currentDevice = id;
  document.querySelectorAll(".nav-item").forEach(i => i.classList.remove("active"));
  document.querySelectorAll(".tab").forEach(t => t.classList.remove("active"));
  document.querySelector('[data-tab="reports"]').classList.add("active");
  document.getElementById("tab-reports").classList.add("active");
  populateDeviceSelects();
  loadReports();
}

function populateDeviceSelects() {
  const opts = devices.map(d => `<option value="${d.id}">${d.name}</option>`).join("");
  const autoId = devices.length === 1 ? devices[0].id : null;
  if (autoId && !currentDevice) currentDevice = autoId;
  ["clients","logs","codes","reports","config","portal"].forEach(tab => {
    const sel = document.getElementById(`${tab}-device-select`);
    if (!sel) return;
    const cur = sel.value;
    sel.innerHTML = '<option value="">Selecciona gateway</option>' + opts;
    if (cur) sel.value = cur;
    else if (currentDevice) sel.value = currentDevice;
    else if (autoId) sel.value = autoId;
  });
  if (autoId) { loadConfig(); loadPortal(); }
}

async function rebootDev(id) {
  if (!confirm("¿Reiniciar el gateway?")) return;
  await api("POST", `/api/devices/${id}/reboot`);
  alert("Comando de reinicio enviado");
}

async function deleteDevice(id, name) {
  if (!confirm(`¿Eliminar el gateway "${name}"? Esta acción no se puede deshacer.`)) return;
  await api("DELETE", `/api/devices/${id}`);
  loadDevices();
}

// ── Registrar dispositivo ─────────────────────────────────────────────────────

function showRegisterModal() {
  document.getElementById("register-result").classList.add("hidden");
  document.getElementById("register-form").classList.remove("hidden");
  document.getElementById("modal-register").classList.remove("hidden");
}

document.getElementById("register-form").addEventListener("submit", async e => {
  e.preventDefault();
  const fd = new FormData(e.target);
  const resp = await fetch("/api/devices/register", {
    method: "POST",
    headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
    body: JSON.stringify(Object.fromEntries(fd)),
  });
  if (resp.ok) {
    const r = await resp.json();
    const ob = await api("GET", `/api/devices/${r.device_id}/onboarding`);
    if (ob) {
      document.getElementById("register-creds").textContent = ob.agent_conf;
      document.getElementById("onboarding-steps").innerHTML =
        ob.steps.map(s => `<li><strong>${s.title.replace(/^\d+\.\s*/, "")}</strong><br><span style="color:var(--muted)">${s.detail}</span></li>`).join("");
    } else {
      document.getElementById("register-creds").textContent =
        `DEVICE_ID="${r.device_id}"\nAPI_KEY="${r.api_key}"`;
    }
    document.getElementById("register-form").classList.add("hidden");
    document.getElementById("register-result").classList.remove("hidden");
    loadDevices();
    loadMe();  // refrescar indicador de uso
  } else if (resp.status === 401) {
    logout();
  } else {
    const err = await resp.json().catch(() => ({}));
    alert(err.detail || "No se pudo registrar el gateway");
  }
});

function closeModal(id) { document.getElementById(id).classList.add("hidden"); }

// ── Clientes ──────────────────────────────────────────────────────────────────

document.getElementById("clients-device-select").addEventListener("change", loadClients);
document.getElementById("clients-all").addEventListener("change", loadClients);

async function loadClients() {
  const devId = document.getElementById("clients-device-select").value;
  if (!devId) return;
  const all = document.getElementById("clients-all").checked;
  const data = await api("GET", `/api/devices/${devId}/clients?active_only=${!all}`) || [];
  document.getElementById("clients-body").innerHTML = data.map(c => `
    <tr>
      <td><code>${c.mac}</code></td>
      <td>${c.ip}</td>
      <td>${c.hostname || "—"}</td>
      <td>${fmt_bytes(c.bytes_in)}</td>
      <td>${fmt_bytes(c.bytes_out)}</td>
      <td>${c.code_used || "—"}</td>
      <td>${fmt_dt(c.connected_at)}</td>
      <td><span class="badge ${c.active ? 'badge-green' : 'badge-gray'}">${c.active ? "Conectado" : "Desconectado"}</span></td>
      <td>${c.active ? `<button class="btn-sm" onclick="kickClient('${devId}','${c.mac}')">Expulsar</button>` : ""}</td>
    </tr>
  `).join("") || '<tr><td colspan="9" style="text-align:center;color:var(--muted)">Sin clientes</td></tr>';
}

async function kickClient(devId, mac) {
  if (!confirm(`¿Expulsar ${mac}?`)) return;
  await api("POST", `/api/devices/${devId}/kick/${mac}`);
  setTimeout(loadClients, 500);
}

// ── Logs ──────────────────────────────────────────────────────────────────────

document.getElementById("logs-device-select").addEventListener("change", loadLogs);
document.getElementById("logs-days").addEventListener("change", loadLogs);

let logsData = [];

async function loadLogs() {
  const devId = document.getElementById("logs-device-select").value;
  if (!devId) return;
  const days = document.getElementById("logs-days").value;
  logsData = await api("GET", `/api/devices/${devId}/logs?days=${days}&limit=500`) || [];
  document.getElementById("logs-body").innerHTML = logsData.map(c => `
    <tr>
      <td><code>${c.mac}</code></td>
      <td>${c.ip}</td>
      <td>${c.hostname || "—"}</td>
      <td>${c.code_used || "—"}</td>
      <td>${fmt_dt(c.connected_at)}</td>
      <td>${c.disconnected_at ? fmt_dt(c.disconnected_at) : "—"}</td>
      <td>${fmt_bytes(c.bytes_in)}</td>
      <td>${fmt_bytes(c.bytes_out)}</td>
      <td><span class="badge ${c.active ? 'badge-green' : 'badge-gray'}">${c.active ? "Activo" : "Desconectado"}</span></td>
    </tr>
  `).join("") || '<tr><td colspan="9" style="text-align:center;color:var(--muted)">Sin registros</td></tr>';
}

function exportLogs() {
  if (!logsData.length) return alert("No hay datos para exportar");
  const csv = ["MAC,IP,Hostname,Código,Entrada,Salida,Bytes↓,Bytes↑,Estado",
    ...logsData.map(c =>
      `${c.mac},${c.ip},${c.hostname||""},${c.code_used||""},${c.connected_at},${c.disconnected_at||""},${c.bytes_in},${c.bytes_out},${c.active?"Activo":"Desconectado"}`)
  ].join("\n");
  const a = document.createElement("a");
  a.href = "data:text/csv;charset=utf-8," + encodeURIComponent(csv);
  a.download = "logs.csv";
  a.click();
}

// ── Códigos ───────────────────────────────────────────────────────────────────

document.getElementById("codes-device-select").addEventListener("change", loadCodes);

async function loadCodes() {
  const devId = document.getElementById("codes-device-select").value;
  if (!devId) return;
  const data = await api("GET", `/api/devices/${devId}/codes`) || [];
  document.getElementById("codes-body").innerHTML = data.map(c => `
    <tr>
      <td><code>${c.code}</code></td>
      <td>${c.duration_min}m</td>
      <td>${c.uses}/${c.max_uses}</td>
      <td>${c.bandwidth_dn || "∞"}/${c.bandwidth_up || "∞"} kbps</td>
      <td>${c.expires_at ? new Date(c.expires_at+"Z").toLocaleDateString("es") : "Nunca"}</td>
      <td>${c.note || "—"}</td>
      <td><span class="badge ${c.active ? 'badge-green' : 'badge-gray'}">${c.active ? "Activo" : "Inactivo"}</span></td>
      <td>${c.active ? `<button class="btn-sm" onclick="revokeCode('${devId}',${c.id})">Revocar</button>` : ""}</td>
    </tr>
  `).join("") || '<tr><td colspan="8" style="text-align:center;color:var(--muted)">Sin códigos</td></tr>';
}

// ── Generación de tickets ─────────────────────────────────────────────────────

const TICKET_TYPES = {
  bus:     { name: "Bus",          bw_dn: 2048, bw_up: 1024 },
  evento:  { name: "Evento",       bw_dn: 3072, bw_up: 1536 },
  playa:   { name: "Playa",        bw_dn: 2048, bw_up: 1024 },
  express: { name: "Express",      bw_dn: 0,    bw_up: 0    },
  custom:  { name: "Personalizado",bw_dn: 0,    bw_up: 0    },
};

let ticketType = "bus";
let ticketDurMin = 60;

document.querySelectorAll("#type-chips .chip").forEach(btn => {
  btn.addEventListener("click", () => {
    document.querySelectorAll("#type-chips .chip").forEach(b => b.classList.remove("active"));
    btn.classList.add("active");
    ticketType = btn.dataset.type;
    document.getElementById("adv-bw").style.display = ticketType === "custom" ? "block" : "none";
    const noteEl = document.getElementById("tickets-note");
    const names = Object.values(TICKET_TYPES).map(t => t.name);
    if (!noteEl.value || names.includes(noteEl.value))
      noteEl.value = TICKET_TYPES[ticketType].name;
  });
});

document.querySelectorAll("#dur-chips .chip").forEach(btn => {
  btn.addEventListener("click", () => {
    document.querySelectorAll("#dur-chips .chip").forEach(b => b.classList.remove("active"));
    btn.classList.add("active");
    const min = parseInt(btn.dataset.min);
    document.getElementById("dur-custom-wrap").style.display = min === 0 ? "block" : "none";
    ticketDurMin = min;
  });
});

function showCodesModal() {
  if (!document.getElementById("codes-device-select").value)
    return alert("Selecciona un gateway primero");
  document.querySelectorAll("#type-chips .chip").forEach(b => b.classList.toggle("active", b.dataset.type === "bus"));
  document.querySelectorAll("#dur-chips .chip").forEach(b => b.classList.toggle("active", b.dataset.min === "60"));
  ticketType = "bus"; ticketDurMin = 60;
  document.getElementById("adv-bw").style.display = "none";
  document.getElementById("dur-custom-wrap").style.display = "none";
  document.getElementById("tickets-note").value = "Bus";
  document.getElementById("tickets-qty").value = "10";
  document.getElementById("gen-codes-result").classList.add("hidden");
  document.getElementById("modal-codes").classList.remove("hidden");
}

document.getElementById("btn-gen-codes").addEventListener("click", async () => {
  const devId = document.getElementById("codes-device-select").value;
  if (!devId) return;

  let durMin = ticketDurMin;
  if (durMin === 0) {
    const h = parseFloat(document.getElementById("dur-custom-val").value);
    if (!h || h <= 0) return alert("Ingresa una duración válida");
    durMin = Math.round(h * 60);
  }

  const type = TICKET_TYPES[ticketType];
  const isCustom = ticketType === "custom";
  const payload = {
    quantity:     parseInt(document.getElementById("tickets-qty").value) || 10,
    duration_min: durMin,
    max_uses:     isCustom ? (parseInt(document.getElementById("adv-max-uses").value) || 1) : 1,
    bandwidth_dn: isCustom ? (parseInt(document.getElementById("adv-bw-dn").value) || 0) : type.bw_dn,
    bandwidth_up: isCustom ? (parseInt(document.getElementById("adv-bw-up").value) || 0) : type.bw_up,
    note:         document.getElementById("tickets-note").value || type.name,
  };
  if (isCustom) {
    const exp = document.getElementById("adv-expires").value;
    const pre = document.getElementById("adv-prefix").value;
    if (exp) payload.expires_hours = parseInt(exp);
    if (pre) payload.prefix = pre;
  }

  const btn = document.getElementById("btn-gen-codes");
  btn.disabled = true; btn.textContent = "Generando…";

  const resp = await fetch(`/api/devices/${devId}/codes`, {
    method: "POST",
    headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
    body: JSON.stringify(payload),
  });

  btn.disabled = false; btn.innerHTML = '<i class="fa-solid fa-ticket"></i> Generar';
  const msg = document.getElementById("gen-codes-result");

  if (resp.ok) {
    const r = await resp.json();
    let quotaMsg = "";
    if (r.quota && !r.quota.unlimited) {
      const avail = r.quota.available || 0;
      if (avail < 20) {
        quotaMsg = ` — Quedan ${avail} tickets`;
      }
    }
    msg.textContent = `✓ ${r.created} tickets generados${quotaMsg}`;
    msg.className = "success"; msg.classList.remove("hidden");
    loadCodes();
    loadMe(); // refrescar indicador de cuota
    setTimeout(() => { closeModal("modal-codes"); msg.classList.add("hidden"); }, 2500);
  } else if (resp.status === 401) {
    logout();
  } else {
    const err = await resp.json().catch(() => ({}));
    msg.textContent = "✗ " + (err.detail || "Error al generar");
    msg.className = "error"; msg.classList.remove("hidden");
  }
});

async function revokeCode(devId, codeId) {
  if (!confirm("¿Revocar este código?")) return;
  await api("DELETE", `/api/devices/${devId}/codes/${codeId}`);
  loadCodes();
}

function exportCodes() {
  const devId = document.getElementById("codes-device-select").value;
  if (!devId) return;
  api("GET", `/api/devices/${devId}/codes`).then(data => {
    if (!data) return;
    const csv = ["Código,Duración,Usos,BW_dn,BW_up,Vence,Nota",
      ...data.map(c => `${c.code},${c.duration_min},${c.max_uses},${c.bandwidth_dn},${c.bandwidth_up},${c.expires_at||""},${c.note}`)
    ].join("\n");
    const a = document.createElement("a");
    a.href = "data:text/csv;charset=utf-8," + encodeURIComponent(csv);
    a.download = "codigos.csv";
    a.click();
  });
}

function printVouchers() {
  const devId = document.getElementById("codes-device-select").value;
  if (!devId) return alert("Selecciona un gateway primero");
  openAuthed(`/api/devices/${devId}/codes/vouchers`);
}

// ── Reportes / Monitor ────────────────────────────────────────────────────────

document.getElementById("reports-device-select").addEventListener("change", loadReports);
document.getElementById("reports-days").addEventListener("change", loadReports);

async function loadReports() {
  const devId = document.getElementById("reports-device-select").value;
  if (!devId) return;
  loadUsageSummary(devId);

  const data = await api("GET", `/api/devices/${devId}/reports?limit=48`) || [];
  if (!data.length) return;

  const latest = data[0];
  document.getElementById("stats-row").innerHTML = `
    <div class="stat-card"><div class="val">${latest.clients_count}</div><div class="lbl">Clientes</div></div>
    <div class="stat-card"><div class="val">${fmt_bytes(latest.bytes_in)}</div><div class="lbl">Tráfico ↓</div></div>
    <div class="stat-card"><div class="val">${fmt_bytes(latest.bytes_out)}</div><div class="lbl">Tráfico ↑</div></div>
    <div class="stat-card"><div class="val">${latest.cpu_load.toFixed(1)}%</div><div class="lbl">CPU</div></div>
    <div class="stat-card"><div class="val">${latest.mem_free_mb.toFixed(0)} MB</div><div class="lbl">RAM libre</div></div>
    <div class="stat-card"><div class="val">${fmt_uptime(latest.uptime_sec)}</div><div class="lbl">Uptime</div></div>
  `;

  const rev = [...data].reverse();
  drawLineChart("traffic-chart", rev.map(r => r.bytes_in / 1024),
    rev.map(r => r.timestamp.slice(11,16)), "Tráfico ↓ (KB)", "#4f8ef7");
  drawLineChart("clients-chart", rev.map(r => r.clients_count),
    rev.map(r => r.timestamp.slice(11,16)), "Clientes", "#3ecf8e");
}

async function loadUsageSummary(devId) {
  const days = document.getElementById("reports-days").value || 30;
  const d = await api("GET", `/api/devices/${devId}/usage-summary?days=${days}`);
  if (!d) return;

  document.getElementById("us-used").textContent    = d.codes.used;
  document.getElementById("us-active").textContent  = d.codes.active;
  document.getElementById("us-clients").textContent = d.clients.total;
  const totalBytes = (d.clients.bytes_in || 0) + (d.clients.bytes_out || 0);
  document.getElementById("us-data").textContent    = fmt_bytes(totalBytes);

  renderBarChart("daily-chart", d.daily);
}

function renderBarChart(containerId, daily) {
  const wrap = document.getElementById(containerId);
  if (!wrap || !daily?.length) return;
  const max = Math.max(...daily.map(d => d.connections), 1);
  wrap.innerHTML = daily.map(d => `
    <div class="bar-col">
      <div class="bar-fill" style="height:${Math.round(d.connections / max * 100)}%"></div>
      <div class="bar-val">${d.connections || ""}</div>
      <div class="bar-lbl">${d.date}</div>
    </div>
  `).join("");
}

function drawLineChart(canvasId, values, labels, label, color) {
  const canvas = document.getElementById(canvasId);
  const ctx = canvas.getContext("2d");
  const W = canvas.offsetWidth; const H = canvas.offsetHeight || 80;
  canvas.width = W; canvas.height = H;
  ctx.clearRect(0, 0, W, H);
  if (!values.length) return;
  const max = Math.max(...values) || 1;
  const step = W / (values.length - 1 || 1);
  ctx.strokeStyle = color; ctx.lineWidth = 2; ctx.beginPath();
  values.forEach((v, i) => {
    const x = i * step, y = H - (v / max) * (H - 20) - 10;
    i === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y);
  });
  ctx.stroke();
  ctx.fillStyle = color + "22"; ctx.lineTo(W, H); ctx.lineTo(0, H); ctx.fill();
  ctx.fillStyle = color; ctx.font = "12px sans-serif";
  ctx.fillText(`${label}: ${values[values.length-1]?.toFixed(1)}`, 8, 16);
}

// ── Configuración del dispositivo ─────────────────────────────────────────────

document.getElementById("config-device-select").addEventListener("change", loadConfig);

async function loadConfig() {
  const devId = document.getElementById("config-device-select").value;
  if (!devId) return;
  const d = devices.find(x => x.id === devId);
  if (!d?.config) return;
  const form = document.getElementById("config-form");
  Object.entries(d.config).forEach(([k, v]) => {
    const el = form.querySelector(`[name="${k}"]`);
    if (el) el.value = v;
  });
  const ssidInput = document.getElementById("ssid-input");
  if (ssidInput && d.config["wlan.essid"]) ssidInput.value = d.config["wlan.essid"];
}

document.getElementById("config-form").addEventListener("submit", async e => {
  e.preventDefault();
  const devId = document.getElementById("config-device-select").value;
  if (!devId) return alert("Selecciona un gateway");
  const fd = new FormData(e.target);
  const config = {};
  fd.forEach((v, k) => { if (v && k !== "device") config[k] = v; });
  const r = await api("PUT", `/api/devices/${devId}/config`, { config });
  const msg = document.getElementById("config-msg");
  msg.textContent = r ? "✓ Configuración enviada al gateway" : "✗ Error al enviar";
  msg.className = r ? "success" : "error";
  msg.classList.remove("hidden");
  setTimeout(() => msg.classList.add("hidden"), 3000);
});

async function rebootDevice() {
  const devId = document.getElementById("config-device-select").value;
  if (!devId) return alert("Selecciona un gateway");
  if (!confirm("¿Reiniciar el gateway?")) return;
  await api("POST", `/api/devices/${devId}/reboot`);
  alert("Comando de reinicio enviado");
}

document.getElementById("ssid-form").addEventListener("submit", async e => {
  e.preventDefault();
  const devId = document.getElementById("config-device-select").value;
  if (!devId) return alert("Selecciona un gateway");
  const ssid = document.getElementById("ssid-input").value.trim();
  if (!ssid) return alert("Ingresa un SSID");
  const msg = document.getElementById("ssid-msg");
  const r = await api("POST", `/api/devices/${devId}/ssid`, { ssid });
  msg.textContent = r ? `✓ SSID enviado al router — se aplicará en ≤30 seg` : "✗ Error al enviar comando";
  msg.className = r ? "success" : "error";
  msg.classList.remove("hidden");
  setTimeout(() => msg.classList.add("hidden"), 4000);
  if (r) {
    const d = devices.find(x => x.id === devId);
    if (d) d.config = { ...(d.config || {}), "wlan.essid": ssid };
  }
});

// ── Portal cautivo (branding) ─────────────────────────────────────────────────

const PORTAL_FIELDS = ["portal_logo_url","portal_title","portal_tagline","portal_prompt",
                       "portal_button","portal_color1","portal_color2","portal_footer"];
const PORTAL_DEFAULTS = {
  portal_title: "JADSLink", portal_tagline: "Internet • Acceso WiFi",
  portal_prompt: "Ingresa tu código de acceso", portal_button: "CONECTAR",
  portal_color1: "#4f8ef7", portal_color2: "#a259f7",
  portal_footer: "Desarrollado por JADS Software", portal_logo_url: "",
};

document.getElementById("portal-device-select").addEventListener("change", loadPortal);

function loadPortal() {
  const devId = document.getElementById("portal-device-select").value;
  document.getElementById("portal-msg").classList.add("hidden");
  if (!devId) return;
  const d = devices.find(x => x.id === devId);
  const cfg = d?.config || {};
  const form = document.getElementById("portal-form");
  PORTAL_FIELDS.forEach(k => {
    const el = form.querySelector(`[name="${k}"]`);
    if (!el) return;
    el.value = (cfg[k] !== undefined && cfg[k] !== "") ? cfg[k] : (PORTAL_DEFAULTS[k] || "");
  });
  refreshPortalPreview();
}

function refreshPortalPreview() {
  const devId = document.getElementById("portal-device-select").value;
  if (!devId) return;
  const form = document.getElementById("portal-form");
  const params = new URLSearchParams();
  PORTAL_FIELDS.forEach(k => {
    const v = form.querySelector(`[name="${k}"]`)?.value || "";
    if (v) params.set(k, v);
  });
  params.set("_t", Date.now());  // cache-bust
  document.getElementById("portal-iframe").src =
    `/api/devices/${devId}/portal/splash?${params.toString()}`;
}

// Preview en vivo mientras se edita
document.getElementById("portal-form").addEventListener("input", () => {
  clearTimeout(window._portalDebounce);
  window._portalDebounce = setTimeout(refreshPortalPreview, 350);
});

document.getElementById("portal-form").addEventListener("submit", async e => {
  e.preventDefault();
  const devId = document.getElementById("portal-device-select").value;
  if (!devId) return alert("Selecciona un gateway");
  const form = e.target;
  const config = {};
  PORTAL_FIELDS.forEach(k => { config[k] = form.querySelector(`[name="${k}"]`)?.value || ""; });
  const r = await api("PUT", `/api/devices/${devId}/config`, { config });
  const msg = document.getElementById("portal-msg");
  if (r) {
    msg.textContent = "✓ Guardado. El router aplicará el nuevo portal en el próximo heartbeat (~30s).";
    msg.className = "success";
    // refrescar config local
    const d = devices.find(x => x.id === devId);
    if (d) d.config = { ...(d.config||{}), ...config };
  } else {
    msg.textContent = "✗ Error al guardar";
    msg.className = "error";
  }
  msg.classList.remove("hidden");
  refreshPortalPreview();
  setTimeout(() => msg.classList.add("hidden"), 5000);
});

// ── Ajustes de cuenta ─────────────────────────────────────────────────────────

async function loadSettings() {
  // Formulario cambio de contraseña
  document.getElementById("pwd-form").reset();
  document.getElementById("pwd-msg").classList.add("hidden");

  // Cargar ajustes de alertas
  const s = await api("GET", "/api/settings");
  if (s) {
    document.getElementById("alert-enabled").checked = s.alert_enabled === "true";
    document.getElementById("alert-email").value     = s.alert_email || "";
    document.getElementById("alert-threshold").value = s.alert_threshold_min || "5";
  }

  // Mostrar credenciales de cada gateway
  const list = document.getElementById("api-keys-list");
  if (!devices.length) {
    list.innerHTML = '<p style="color:var(--muted)">No hay gateways registrados.</p>';
    return;
  }
  list.innerHTML = devices.map(d => `
    <div class="apikey-row">
      <div class="apikey-name">
        <span class="status ${d.online ? 'status-online' : 'status-offline'}"></span>
        <strong>${d.name}</strong>
        <span style="color:var(--muted);font-size:12px">${d.location || ""}</span>
      </div>
      <div class="apikey-field">
        <span class="apikey-label">DEVICE_ID</span>
        <code class="apikey-val">${d.id}</code>
        <button class="copy-btn" onclick="copyText('${d.id}', this)"><i class="fa-regular fa-copy"></i></button>
      </div>
      <div class="apikey-field">
        <span class="apikey-label">API_KEY</span>
        <code class="apikey-val apikey-secret" id="key-${d.id}">${d.api_key ? d.api_key.slice(0,8) + "••••••••••••••••••••••••" : "—"}</code>
        <button class="copy-btn" onclick="copyText('${d.api_key||""}', this)"><i class="fa-regular fa-copy"></i></button>
        <button class="copy-btn" onclick="toggleKey('${d.id}','${d.api_key||""}')"><i class="fa-regular fa-eye"></i></button>
      </div>
    </div>
  `).join("");
}

function toggleKey(id, val) {
  const el = document.getElementById(`key-${id}`);
  if (el.dataset.visible === "1") {
    el.textContent = val.slice(0,8) + "••••••••••••••••••••••••";
    el.dataset.visible = "0";
  } else {
    el.textContent = val;
    el.dataset.visible = "1";
  }
}

document.getElementById("pwd-form").addEventListener("submit", async e => {
  e.preventDefault();
  const cur = document.getElementById("pwd-current").value;
  const nw  = document.getElementById("pwd-new").value;
  const cfm = document.getElementById("pwd-confirm").value;
  const msg = document.getElementById("pwd-msg");

  if (nw !== cfm) {
    msg.textContent = "Las contraseñas nuevas no coinciden";
    msg.className = "error"; msg.classList.remove("hidden");
    return;
  }

  const r = await api("PUT", "/api/auth/password", {
    current_password: cur,
    new_password: nw,
  });

  if (r?.ok) {
    msg.textContent = "✓ Contraseña actualizada. Inicia sesión de nuevo.";
    msg.className = "success"; msg.classList.remove("hidden");
    setTimeout(logout, 2000);
  } else {
    msg.textContent = "✗ Contraseña actual incorrecta";
    msg.className = "error"; msg.classList.remove("hidden");
  }
});

document.getElementById("alert-form").addEventListener("submit", async e => {
  e.preventDefault();
  const msg = document.getElementById("alert-msg");
  const r = await api("POST", "/api/settings", {
    alert_enabled:       document.getElementById("alert-enabled").checked ? "true" : "false",
    alert_email:         document.getElementById("alert-email").value.trim(),
    alert_threshold_min: document.getElementById("alert-threshold").value,
  });
  msg.textContent = r?.ok ? "✓ Ajustes de alertas guardados" : "✗ Error al guardar";
  msg.className   = r?.ok ? "success" : "error";
  msg.classList.remove("hidden");
  setTimeout(() => msg.classList.add("hidden"), 3000);
});

// ── Init ──────────────────────────────────────────────────────────────────────

if (token) {
  showDashboard();
} else {
  document.getElementById("landing-screen").classList.add("active");
}
// ── Gestión de cuentas mejorada ───────────────────────────────────────────────

async function deleteAccount(id, name) {
  showConfirmModal(
    '¿Eliminar cuenta?',
    `¿Estás seguro de eliminar la cuenta "<strong>${name}</strong>"?<br><br>
    <span style="color:var(--muted);font-size:13px">
    Los usuarios no podrán acceder, pero los datos se preservan para auditoría.
    </span>`,
    async () => {
      const r = await api('DELETE', `/api/accounts/${id}`);
      if (r && r.ok) {
        showToast('✓ Cuenta eliminada correctamente', 'success');
        loadAccounts();
      }
    }
  );
}

async function restoreAccount(id, name) {
  showConfirmModal(
    '¿Restaurar cuenta?',
    `¿Restaurar la cuenta "<strong>${name}</strong>"?<br><br>
    <span style="color:var(--muted);font-size:13px">
    Los usuarios podrán volver a iniciar sesión y usar sus servicios.
    </span>`,
    async () => {
      const r = await api('POST', `/api/accounts/${id}/restore`);
      if (r && r.ok) {
        showToast('✓ Cuenta restaurada correctamente', 'success');
        loadAccounts();
      }
    }
  );
}

let grantTicketsAccountId = null;
let grantTicketsAccountName = null;

function grantTickets(id, name) {
  grantTicketsAccountId = id;
  grantTicketsAccountName = name;
  document.getElementById('grant-account-name').textContent = name;
  document.getElementById('grant-qty').value = '100';
  document.getElementById('grant-note').value = '';
  document.getElementById('modal-grant-tickets').classList.remove('hidden');
}

async function submitGrantTickets() {
  const qty = parseInt(document.getElementById('grant-qty').value, 10);
  const note = document.getElementById('grant-note').value.trim();

  if (isNaN(qty) || qty <= 0) {
    showToast('✗ Cantidad inválida', 'error');
    return;
  }

  const r = await api('POST', `/api/accounts/${grantTicketsAccountId}/tickets/grant`, {
    quantity: qty,
    note: note
  });

  if (r && r.ok) {
    showToast(`✓ ${qty} tickets otorgados a ${grantTicketsAccountName}`, 'success');
    closeModal('modal-grant-tickets');
    loadAccounts();
  }
}

async function updateAccount(id, field, value) {
  showConfirmModal(
    'Confirmar cambio',
    `¿Cambiar el ${field === 'plan' ? 'plan' : 'estado'} de esta cuenta?<br><br>
    <span style="color:var(--muted);font-size:13px">
    Nuevo valor: <strong>${value}</strong>
    </span>`,
    async () => {
      const r = await api('PATCH', `/api/accounts/${id}`, { [field]: value });
      if (r) {
        showToast(`✓ ${field === 'plan' ? 'Plan' : 'Estado'} actualizado`, 'success');
        loadAccounts();
      }
    },
    () => {
      // Si cancela, recargar para restaurar el valor anterior del select
      loadAccounts();
    }
  );
}

// ── Modales y toasts ──────────────────────────────────────────────────────────

function showToast(message, type = 'success') {
  const toast = document.createElement('div');
  toast.className = `toast toast-${type}`;
  toast.textContent = message;
  toast.style.cssText = `
    position: fixed;
    top: 20px;
    right: 20px;
    background: ${type === 'success' ? 'var(--accent2)' : 'var(--danger)'};
    color: white;
    padding: 14px 24px;
    border-radius: 8px;
    z-index: 10000;
    font-weight: 600;
    box-shadow: 0 4px 16px rgba(0,0,0,0.3);
    animation: slideIn 0.3s ease;
  `;
  document.body.appendChild(toast);
  setTimeout(() => {
    toast.style.animation = 'slideOut 0.3s ease';
    setTimeout(() => toast.remove(), 300);
  }, 3000);
}

let confirmCallback = null;
let cancelCallback = null;

function showConfirmModal(title, message, onConfirm, onCancel) {
  confirmCallback = onConfirm;
  cancelCallback = onCancel;
  document.getElementById('confirm-title').textContent = title;
  document.getElementById('confirm-message').innerHTML = message;
  document.getElementById('modal-confirm').classList.remove('hidden');
}

async function confirmAction() {
  closeModal('modal-confirm');
  if (confirmCallback) await confirmCallback();
  confirmCallback = null;
  cancelCallback = null;
}

function cancelAction() {
  closeModal('modal-confirm');
  if (cancelCallback) cancelCallback();
  confirmCallback = null;
  cancelCallback = null;
}
// ── Hero Carousel con Contenido Dinámico ─────────────────────────────────────

const heroSlider = {
  currentSlide: 0,
  slides: [],
  dots: [],
  interval: null,

  // Contenido dinámico para cada slide
  content: [
    {
      title: "WiFi Premium en Buses Interurbanos",
      subtitle: "Ofrece conectividad de alta velocidad en rutas de larga distancia. Tus pasajeros navegan, trabajan y se entretienen mientras viajan. Cobra por hora o por viaje."
    },
    {
      title: "Conectividad para Eventos Masivos",
      subtitle: "Despliega puntos de acceso temporales en conciertos, festivales y ferias. Miles de usuarios conectados simultáneamente. Sistema de pago automático por tiempo de uso."
    },
    {
      title: "Internet en Camping y Zonas Remotas",
      subtitle: "Lleva WiFi profesional a campamentos, cabañas y sitios alejados. Tus huéspedes disfrutan de conectividad satelital donde antes era imposible. Monetiza cada sesión."
    },
    {
      title: "WiFi en Playas y Destinos Turísticos",
      subtitle: "Instala puntos de acceso en costas, ríos y montañas. Los turistas pagan por conectarse mientras disfrutan de la naturaleza. Sin cables, sin complicaciones."
    }
  ],

  init() {
    this.slides = document.querySelectorAll('.hero-slide');
    this.dots = document.querySelectorAll('.slider-dot');

    if (this.slides.length === 0) return;

    // Iniciar autoplay
    this.startAutoplay();

    // Pausar en hover
    const heroSection = document.querySelector('.landing-hero');
    if (heroSection) {
      heroSection.addEventListener('mouseenter', () => this.stopAutoplay());
      heroSection.addEventListener('mouseleave', () => this.startAutoplay());
    }
  },

  goToSlide(index) {
    // Remover active de slide y dot actuales
    this.slides[this.currentSlide].classList.remove('active');
    this.dots[this.currentSlide].classList.remove('active');

    // Actualizar índice
    this.currentSlide = index;

    // Agregar active a nuevos slide y dot
    this.slides[this.currentSlide].classList.add('active');
    this.dots[this.currentSlide].classList.add('active');

    // Actualizar contenido dinámico
    this.updateContent();
  },

  nextSlide() {
    const next = (this.currentSlide + 1) % this.slides.length;
    this.goToSlide(next);
  },

  updateContent() {
    const titleEl = document.getElementById('hero-title');
    const subtitleEl = document.getElementById('hero-subtitle');
    const content = this.content[this.currentSlide];

    if (titleEl && subtitleEl && content) {
      // Fade out
      titleEl.style.opacity = '0';
      subtitleEl.style.opacity = '0';

      setTimeout(() => {
        // Cambiar texto
        titleEl.textContent = content.title;
        subtitleEl.textContent = content.subtitle;

        // Fade in
        titleEl.style.transition = 'opacity 0.6s ease';
        subtitleEl.style.transition = 'opacity 0.6s ease';
        titleEl.style.opacity = '1';
        subtitleEl.style.opacity = '1';
      }, 300);
    }
  },

  startAutoplay() {
    this.stopAutoplay(); // Limpiar interval anterior
    this.interval = setInterval(() => this.nextSlide(), 6000); // Cambiar cada 6 segundos
  },

  stopAutoplay() {
    if (this.interval) {
      clearInterval(this.interval);
      this.interval = null;
    }
  }
};

// Inicializar carousel cuando se muestra el landing
const originalShowSignup = showSignup;
const originalShowLogin = showLogin;

// Override para inicializar el carousel cuando se vuelve al landing
window.addEventListener('load', () => {
  // Solo inicializar si estamos en el landing (sin token)
  if (!token) {
    setTimeout(() => heroSlider.init(), 100);
  }
});
