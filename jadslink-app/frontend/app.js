/* Hotspot Cloud Manager - Frontend */
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
    headers: { "Content-Type": "application/json", ...(token ? { Authorization: `Bearer ${token}` } : {}) },
  };
  if (body) opts.body = JSON.stringify(body);
  const r = await fetch(API + path, opts);
  if (r.status === 401) { logout(); return null; }
  return r.ok ? r.json() : null;
}

function fmt_bytes(b) {
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
  return `hace ${Math.round(diff/3600)}h`;
}

// ── Auth ──────────────────────────────────────────────────────────────────────

document.getElementById("login-form").addEventListener("submit", async e => {
  e.preventDefault();
  const r = await fetch("/api/auth/login", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username: document.getElementById("login-user").value, password: document.getElementById("login-pass").value }),
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
    if (el.dataset.tab === "codes")    loadCodes();
    if (el.dataset.tab === "reports")  loadReports();
    if (el.dataset.tab === "config")   loadConfig();
  });
});

// ── Dispositivos ──────────────────────────────────────────────────────────────

async function loadDevices() {
  devices = await api("GET", "/api/devices") || [];
  renderDevices();
  populateDeviceSelects();
}

function renderDevices() {
  const grid = document.getElementById("devices-grid");
  grid.innerHTML = devices.map(d => `
    <div class="device-card" onclick="selectDevice('${d.id}')">
      <div class="device-name">
        <span class="status ${d.online ? 'status-online' : 'status-offline'}"></span>
        ${d.name}
      </div>
      <div class="device-meta">${d.location || "Sin ubicación"} · ${d.model}</div>
      <div class="device-meta">Visto: ${time_ago(d.last_seen)} · FW: ${d.firmware || "—"}</div>
      <div class="device-actions">
        <button class="btn-secondary btn-sm" onclick="event.stopPropagation(); rebootDev('${d.id}')">Reiniciar</button>
        <button class="btn-sm" style="background:var(--accent)" onclick="event.stopPropagation(); showApiKey('${d.id}')">API Key</button>
      </div>
    </div>
  `).join("") || '<p style="color:var(--muted)">No hay dispositivos. Registra uno con el botón +</p>';
}

function selectDevice(id) {
  currentDevice = id;
  document.querySelectorAll(".nav-item").forEach(i => i.classList.remove("active"));
  document.querySelectorAll(".tab").forEach(t => t.classList.remove("active"));
  document.querySelector('[data-tab="reports"]').classList.add("active");
  document.getElementById("tab-reports").classList.add("active");
  loadReports();
}

function populateDeviceSelects() {
  const opts = devices.map(d => `<option value="${d.id}">${d.name}</option>`).join("");
  ["clients","codes","reports","config"].forEach(tab => {
    const sel = document.getElementById(`${tab}-device-select`);
    const cur = sel.value;
    sel.innerHTML = '<option value="">Selecciona dispositivo</option>' + opts;
    if (cur) sel.value = cur;
    if (!cur && currentDevice) sel.value = currentDevice;
  });
}

async function rebootDev(id) {
  if (!confirm("¿Reiniciar el dispositivo?")) return;
  await api("POST", `/api/devices/${id}/reboot`);
  alert("Comando de reinicio enviado");
}

function showApiKey(id) {
  const d = devices.find(x => x.id === id);
  if (d) alert(`Device ID: ${d.id}\nAPI Key: ${d.api_key || "(ver en registro)"}`);
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
      `Device ID : ${r.device_id}\nAPI Key   : ${r.api_key}\n\nGuarda esto en el agente OpenWrt.`;
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
  const tbody = document.getElementById("clients-body");
  tbody.innerHTML = data.map(c => `
    <tr>
      <td><code>${c.mac}</code></td>
      <td>${c.ip}</td>
      <td>${c.hostname || "—"}</td>
      <td>${fmt_bytes(c.bytes_in)}</td>
      <td>${fmt_bytes(c.bytes_out)}</td>
      <td>${c.code_used || "—"}</td>
      <td>${time_ago(c.connected_at)}</td>
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
      <td>${c.expires_at ? new Date(c.expires_at+"Z").toLocaleDateString() : "Nunca"}</td>
      <td>${c.note || "—"}</td>
      <td><span class="badge ${c.active ? 'badge-green' : 'badge-gray'}">${c.active ? "Activo" : "Inactivo"}</span></td>
      <td>${c.active ? `<button class="btn-sm" onclick="revokeCode('${devId}',${c.id})">Revocar</button>` : ""}</td>
    </tr>
  `).join("") || '<tr><td colspan="8" style="text-align:center;color:var(--muted)">Sin códigos</td></tr>';
}

function showCodesModal() {
  if (!document.getElementById("codes-device-select").value)
    return alert("Selecciona un dispositivo primero");
  document.getElementById("modal-codes").classList.remove("hidden");
}

document.getElementById("gen-codes-form").addEventListener("submit", async e => {
  e.preventDefault();
  const devId = document.getElementById("codes-device-select").value;
  const fd = new FormData(e.target);
  const payload = Object.fromEntries(fd);
  ["quantity","duration_min","max_uses","bandwidth_dn","bandwidth_up"].forEach(k => {
    if (payload[k]) payload[k] = parseInt(payload[k]);
  });
  if (payload.expires_hours) payload.expires_hours = parseInt(payload.expires_hours);
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

// ── Reportes ──────────────────────────────────────────────────────────────────

document.getElementById("reports-device-select").addEventListener("change", loadReports);

let trafficChart = null, clientsChart = null;

async function loadReports() {
  const devId = document.getElementById("reports-device-select").value;
  if (!devId) return;
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

  // Gráficas simples con Canvas
  drawLineChart("traffic-chart", data.reverse().map(r => r.bytes_in / 1024),
    data.map(r => r.timestamp.slice(11,16)), "Tráfico ↓ (KB)", "#4f8ef7");
  drawLineChart("clients-chart", data.map(r => r.clients_count),
    data.map(r => r.timestamp.slice(11,16)), "Clientes", "#3ecf8e");
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

// ── Configuración ─────────────────────────────────────────────────────────────

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
  if (!devId) return alert("Selecciona un dispositivo");
  const fd = new FormData(e.target);
  const config = {};
  fd.forEach((v, k) => { if (v && k !== "device") config[k] = v; });
  const r = await api("PUT", `/api/devices/${devId}/config`, { config });
  const msg = document.getElementById("config-msg");
  msg.textContent = r ? "✓ Configuración enviada al dispositivo" : "✗ Error al enviar";
  msg.className = r ? "success" : "error";
  msg.classList.remove("hidden");
  setTimeout(() => msg.classList.add("hidden"), 3000);
});

async function rebootDevice() {
  const devId = document.getElementById("config-device-select").value;
  if (!devId) return alert("Selecciona un dispositivo");
  if (!confirm("¿Reiniciar el dispositivo?")) return;
  await api("POST", `/api/devices/${devId}/reboot`);
  alert("Comando de reinicio enviado");
}

// ── Init ──────────────────────────────────────────────────────────────────────

if (token) showDashboard();
