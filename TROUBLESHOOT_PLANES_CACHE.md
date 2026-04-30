# 🧹 SOLUCIÓN: Planes Incorrectos en Login/Billing

**Problema**: Ves planes viejos como "Starter" y "Pro" en lugar de los 4 planes correctos.

---

## ✅ LOS PLANES CORRECTOS SON:

```
1. Gratuito:  $0/mes    | 50 tickets      | 1 nodo       | Email (48h)
2. Básico:    $29/mes   | 200 tickets     | 1 nodo       | Email (24h)
3. Estándar:  $79/mes   | 1000 tickets    | 3 nodos  ⭐  | Chat+Email
4. Pro:       $199/mes  | Ilimitado       | Ilimitado    | 24/7
```

---

## 🔍 ¿QUÉ ESTÁ PASANDO?

Tu **navegador está cacheando datos viejos**. El backend está correcto (devuelve 4 planes), pero el frontend muestra datos antiguos.

### Posibles causas:
1. ❌ Cache HTTP del navegador (más común)
2. ❌ LocalStorage de la app
3. ❌ Service Worker cacheando datos
4. ❌ Cache de React Query

---

## 🧹 SOLUCIONES (Elige una)

### **OPCIÓN 1: Limpiar Caché Completo (RECOMENDADO)**

#### Chrome, Edge, Brave, Opera:
```
1. Presiona: Ctrl+Shift+Del (Windows) o Cmd+Shift+Del (Mac)
2. Selecciona: "Todo el tiempo" en el dropdown
3. Marca:
   ☑️ Cookies y otros datos de sitios
   ☑️ Archivos en caché
   ☑️ Imágenes y archivos en caché (si está disponible)
4. Haz click en "Borrar datos"
5. Recarga la página: Ctrl+F5 (Windows) o Cmd+Shift+R (Mac)
```

#### Firefox:
```
1. Presiona: Ctrl+Shift+Del (Windows) o Cmd+Shift+Del (Mac)
2. Selecciona: "Todo" en el dropdown
3. Marca:
   ☑️ Cookies
   ☑️ Caché
4. Haz click en "Limpiar ahora"
5. Recarga: Ctrl+F5 o Cmd+Shift+R
```

#### Safari (Mac):
```
1. Menú → Develop → Empty Web Storage (si no ves Develop, habilítalo en Preferencias)
2. Menú → Safari → Borrar historial → "Todo el historial"
3. Recarga: Cmd+Shift+R
```

---

### **OPCIÓN 2: Modo Incógnito/Privado (RÁPIDO)**

Abre una **nueva ventana privada**:
- **Chrome/Edge**: Ctrl+Shift+N (Windows) o Cmd+Shift+N (Mac)
- **Firefox**: Ctrl+Shift+P (Windows) o Cmd+Shift+P (Mac)
- **Safari**: Cmd+Shift+N (Mac)

Luego ve a: `https://wheat-pigeon-347024.hostingersite.com/login`

**Deberías ver los 4 planes correctos**.

---

### **OPCIÓN 3: Hard Refresh**

Presiona:
- **Windows/Linux**: Ctrl+Shift+R o Ctrl+F5
- **Mac**: Cmd+Shift+R o Cmd+Option+R

Esto fuerza al navegador a descargar archivos nuevos en lugar de usar el caché.

---

## 🔧 VERIFICACIÓN TÉCNICA

Si aún ves planes incorrectos, abre la **consola del navegador** (F12) y ejecuta:

```javascript
// Limpiar localStorage
localStorage.clear();

// Limpiar sessionStorage
sessionStorage.clear();

// Desactivar service workers
navigator.serviceWorker.getRegistrations().then(registrations => {
  registrations.forEach(r => r.unregister());
});

// Recargar
location.reload();
```

---

## 📊 CÓMO VERIFICAR QUE LOS PLANES SON CORRECTOS

### En el navegador (F12 → Network):
1. Abre DevTools: F12
2. Ir a "Network"
3. Recarga la página
4. Busca: `saas-plans`
5. Haz click y verifica que la respuesta contiene 4 planes:
   - `"tier":"free"`
   - `"tier":"basic"`
   - `"tier":"standard"`
   - `"tier":"pro"`

### Desde terminal:
```bash
curl -s https://wheat-pigeon-347024.hostingersite.com/api/v1/saas-plans | jq '.[] | {tier, name, price: .monthly_price}'
```

**Output esperado**:
```json
{
  "tier": "free",
  "name": "Gratuito",
  "price": "0.00"
}
{
  "tier": "basic",
  "name": "Básico",
  "price": "29.00"
}
{
  "tier": "standard",
  "name": "Estándar",
  "price": "79.00"
}
{
  "tier": "pro",
  "name": "Pro",
  "price": "199.00"
}
```

---

## 📝 DÓNDE VER LOS PLANES CORRECTOS

✅ **En la app después de limpiar caché**:
- Login: Grid de 4 columnas
- Billing: Grid de 4 tarjetas
- AdminSubscriptions: Select con 4 opciones

✅ **En el endpoint directo**:
```
https://wheat-pigeon-347024.hostingersite.com/api/v1/saas-plans
```
(Abre en el navegador para ver JSON con 4 planes)

✅ **En Hostinger directamente**:
```bash
ssh -p 65002 u938946830@217.65.147.159
curl http://localhost:8000/api/v1/saas-plans | python3 -m json.tool
```

---

## 🚨 SI NADA FUNCIONA

### Paso 1: Reinicia el navegador completo
- Cierra TODAS las tabs/ventanas del sitio
- Cierra el navegador completamente
- Abre de nuevo
- Ve a `https://wheat-pigeon-347024.hostingersite.com/login`

### Paso 2: Intenta otro navegador
- Chrome vs Firefox vs Edge
- Esto ayuda a aislar si es un problema del navegador

### Paso 3: Verifica el backend
```bash
ssh -p 65002 u938946830@217.65.147.159
ps aux | grep uvicorn  # Verificar API corriendo
curl http://localhost:8000/api/v1/saas-plans | head -100  # Ver respuesta
```

---

## ✨ DESPUÉS DE LIMPIAR CACHÉ

Deberías ver:

### ✅ LOGIN PAGE
```
┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐
│ GRATUITO    │ │ BÁSICO      │ │ ESTÁNDAR ⭐ │ │ PRO         │
│ $0/mes      │ │ $29/mes     │ │ $79/mes     │ │ $199/mes    │
│             │ │             │ │             │ │             │
│ 50 tickets  │ │ 200 tickets │ │1000 tickets │ │ Ilimitado   │
│ 1 nodo      │ │ 1 nodo      │ │ 3 nodos     │ │ Ilimitado   │
└─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘
```

### ✅ BILLING PAGE
Mismos 4 planes con features detalladas

### ✅ ADMIN SUBSCRIPTIONS
Select desplegable con 4 opciones:
- Gratuito
- Básico
- Estándar
- Pro

---

## 📞 CONTACTO

Si persiste el problema después de todos estos pasos, reporta:
1. Tu navegador (Chrome, Firefox, etc.) y versión
2. Tu sistema operativo (Windows 10/11, Mac, Linux)
3. Screenshot de lo que ves
4. Output de `curl https://wheat-pigeon-347024.hostingersite.com/api/v1/saas-plans | head -50`

---

_Última actualización: 2026-04-30_
_Planes verificados correctos en el endpoint ✅_
