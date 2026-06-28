/* JADSLink Cloud Manager */
const API = "";
let token = localStorage.getItem("hcm_token") || "";
let username = localStorage.getItem("hcm_user") || "";
let devices = [];
let currentDevice = null;
let pollInterval = null;

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
    token = d.token; username = d.username;
    localStorage.setItem("hcm_token", token);
    localStorage.setItem("hcm_user", username);
    showDashboard();
  } else {
    document.getElementById("login-error").textContent = "Usuario o contraseña incorrectos";
    document.getElementById("login-error").classList.remove("hidden");
  }
});

function logout() {
  token = ""; username = "";
  localStorage.removeItem("hcm_token");
  localStorage.removeItem("hcm_user");
  clearInterval(pollInterval);
  document.getElementById("dashboard-screen").classList.remove("active");
  document.getElementById("login-screen").classList.add("active");
}

document.getElementById("logout-btn").addEventListener("click", logout);

// ── Dashboard ─────────────────────────────────────────────────────────────────

function showDashboard() {
  document.getElementById("login-screen").classList.remove("active");
  document.getElementById("dashboard-screen").classList.add("active");
  document.getElementById("nav-user").textContent = username;
  loadDevices();
  pollInterval = setInterval(loadDevices, 30000);
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
  });
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
  ["clients","logs","codes","reports","config","portal"].forEach(tab => {
    const sel = document.getElementById(`${tab}-device-select`);
    if (!sel) return;
    const cur = sel.value;
    sel.innerHTML = '<option value="">Selecciona gateway</option>' + opts;
    if (cur) sel.value = cur;
    if (!cur && currentDevice) sel.value = currentDevice;
  });
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
  const r = await api("POST", "/api/devices/register", Object.fromEntries(fd));
  if (r) {
    document.getElementById("register-creds").textContent =
      `Device ID : ${r.device_id}\nAPI Key   : ${r.api_key}\n\nAgrega esto en /etc/hotspot/agent.conf del router.`;
    document.getElementById("register-form").classList.add("hidden");
    document.getElementById("register-result").classList.remove("hidden");
    loadDevices();
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

function showCodesModal() {
  if (!document.getElementById("codes-device-select").value)
    return alert("Selecciona un gateway primero");
  document.getElementById("modal-codes").classList.remove("hidden");
}

document.getElementById("gen-codes-form").addEventListener("submit", async e => {
  e.preventDefault();
  const devId = document.getElementById("codes-device-select").value;
  const fd = new FormData(e.target);
  const payload = Object.fromEntries(fd);
  // Quitar campos vacíos: enviar "" rompe la validación de enteros del backend.
  for (const k of Object.keys(payload)) {
    if (payload[k] === "") delete payload[k];
  }
  ["quantity","duration_min","max_uses","bandwidth_dn","bandwidth_up","expires_hours"].forEach(k => {
    if (payload[k] !== undefined) payload[k] = parseInt(payload[k]);
  });
  const r = await api("POST", `/api/devices/${devId}/codes`, payload);
  if (r) { closeModal("modal-codes"); loadCodes(); alert(`${r.created} códigos generados`); }
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
  window.open(`/api/devices/${devId}/codes/vouchers?token=${encodeURIComponent(token)}`, "_blank");
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

if (token) showDashboard();
