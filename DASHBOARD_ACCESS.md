# 📊 JADSlink Dashboard - Guía de Acceso

## 🌐 Acceso al Dashboard

**URL**: https://wheat-pigeon-347024.hostingersite.com/dashboard/

---

## 🔐 Credenciales de Prueba

Para acceder al dashboard, usa las siguientes credenciales:

| Campo | Valor |
|-------|-------|
| **Email** | admin@jads.com |
| **Contraseña** | admin123456 |
| **Rol** | Superadmin |

---

## 📋 Pasos para Acceder

### 1. Abre el navegador
Accede a: **https://wheat-pigeon-347024.hostingersite.com/dashboard/**

### 2. Página de Login
Deberías ver una página de login. Ingresa:
- **Email**: `admin@jads.com`
- **Contraseña**: `admin123456`

### 3. Haz clic en "Iniciar Sesión"
El sistema te autenticará y redirigirá al dashboard principal.

---

## 🎯 Funcionalidades del Dashboard

Una vez logueado, tienes acceso a:

### 📊 Panel Principal (Dashboard)
- Resumen de estadísticas
- Nodos conectados
- Sesiones activas
- Ingresos generados

### 🗓️ Planes
- Crear planes de acceso
- Editar duración y precio
- Ver estadísticas de uso
- Activar/desactivar planes

### 🖥️ Nodos
- Listar todos los nodos
- Crear nodos (routers Starlink)
- Configurar parámetros
- Ver mapa de ubicaciones
- Monitorear estado (online/offline)
- Ver métricas en tiempo real

### 🎫 Tickets
- Generar tickets de acceso
- Ver código QR
- Descargar en PDF
- Revocar tickets
- Filtrar por estado (pending, active, expired)

### 📈 Sesiones Activas
- Ver usuarios conectados
- Duración de sesión
- Datos consumidos
- Desconectar usuarios

### 📋 Reportes
- Gráficas de uso
- Ingresos por período
- Nodos más usados
- Horas pico de acceso

### ⚙️ Configuración Tenant
- Logo personalizado
- Color de tema
- SSID de red
- Email de contacto
- Teléfono de contacto

### 🔑 Administración (Superadmin)
- Gestionar operadores (tenants)
- Crear nuevos operadores
- Suspender operadores
- Ver métricas globales
- Mapa global de nodos

---

## 🛠️ Solución de Problemas

### El dashboard no carga
**Problema**: Página en blanco o error 404
**Solución**:
1. Limpia la caché del navegador (Ctrl+Shift+Delete)
2. Actualiza la página (F5 o Ctrl+R)
3. Intenta en una ventana privada/incógnita

### No me permite loguear
**Problema**: "Credenciales inválidas"
**Solución**:
1. Verifica que escribiste correctamente el email y contraseña
2. El email es `admin@jads.com` (con @)
3. La contraseña es `admin123456` (sin espacios)

### Los íconos no carga
**Problema**: Símbolos raros en lugar de íconos
**Solución**:
1. Espera a que cargue completamente (puede tardar unos segundos)
2. Recarga la página (F5)

### API no responde desde dashboard
**Problema**: Error "Network Error" al cargar datos
**Solución**:
1. Verifica que la API está corriendo en Hostinger
2. Ejecuta: `https://wheat-pigeon-347024.hostingersite.com/health`
3. Debería devolver status: "healthy"

---

## 📱 Compatibilidad

El dashboard funciona en:
- ✅ Chrome/Chromium (recomendado)
- ✅ Firefox
- ✅ Safari
- ✅ Edge
- ✅ Navegadores móviles (responsive)

---

## 🔗 Links Útiles

| Recurso | URL |
|---------|-----|
| **Dashboard** | https://wheat-pigeon-347024.hostingersite.com/dashboard/ |
| **API Docs** | https://wheat-pigeon-347024.hostingersite.com/docs |
| **Health Check** | https://wheat-pigeon-347024.hostingersite.com/health |
| **Página Principal** | https://wheat-pigeon-347024.hostingersite.com |

---

## 🎯 Primer Uso: Pasos Recomendados

1. **Loguéate** en el dashboard
2. **Crea un Nodo** (Menú → Nodos → Crear)
   - Dale un nombre descriptivo (ej: "Bus 101")
   - Nota el API Key generado
3. **Crea Planes** (Menú → Planes → Crear)
   - Define duración (30 min, 1 hora, 1 día)
   - Establece precio
4. **Genera Tickets** (Menú → Tickets → Generar)
   - Selecciona plan y nodo
   - Especifica cantidad
   - Descarga/comparte códigos QR
5. **Monitorea Uso** (Menú → Reportes)
   - Revisa gráficas de uso
   - Ve ingresos generados

---

## 🔒 Seguridad

- Los datos se transmiten por **HTTPS** (encriptado)
- Tu token se guarda en **localStorage** del navegador
- Expires automáticamente cada **15 minutos**
- Puedes hacer logout desde el menú superior

---

## 📞 Soporte

Si tienes problemas:
1. Verifica que la API está corriendo: `/health`
2. Revisa los logs: `tail -f /tmp/uvicorn.log` (vía SSH)
3. Limpia caché y cookies del navegador
4. Intenta en modo incógnito

---

**Dashboard v1.0 - Compilado el 2026-04-28**

¡Listo para usar! 🚀
