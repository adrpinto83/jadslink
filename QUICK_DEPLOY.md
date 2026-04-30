# ⚡ QUICK DEPLOYMENT - Planes SaaS en Hostinger

**EJECUTA ESTO EN TU SERVIDOR HOSTINGER (VÍA SSH)**

```bash
# 1. SSH al servidor
ssh usuario@tu-servidor.com

# 2. Ir al proyecto
cd /home/adrpinto/jadslink

# 3. Actualizar código
git pull origin main

# 4. Ejecutar deployment
./deploy-saas-plans.sh
```

**¡Eso es todo!** El script hará todo lo demás automáticamente.

---

## ✅ Durante la ejecución verás:

```
✅ Verificaciones iniciales
✅ Crear backup de seguridad
✅ Actualizar código desde Git
✅ Ejecutar migración Alembic
✅ Insertar 4 planes SaaS
✅ Verificar planes en BD
✅ Verificar endpoint API
✅ Reiniciar API
✅ Verificación final
```

---

## 🎯 Después, verifica:

### Terminal (rápido):
```bash
# Verificar planes en BD
mysql -u usuario -p basedatos -e "SELECT tier, name, monthly_price FROM pricing_plans;"

# Probar endpoint
curl http://localhost:8000/api/v1/saas-plans | jq '.[] | {tier, name}'
```

### Navegador:
- Login: `https://tu-dominio.com/login` (ver 4 planes)
- Billing: `https://tu-dominio.com/dashboard/billing` (dinámico)
- Admin: `https://tu-dominio.com/dashboard/admin/subscriptions` (opción "standard")

---

## ⚠️ Si algo falla:

1. **Leer output del script** → dice exactamente qué falló
2. **Ver troubleshooting** en `DEPLOY_HOSTINGER_SAAS_PLANS.md`
3. **Restore desde backup** si es necesario

---

## 📊 Los 4 Planes:

| Plan | Precio | Tickets | Nodos | Soporte |
|------|--------|---------|-------|---------|
| Gratuito | $0/mes | 50 | 1 | Email 48h |
| Básico | $29/mes | 200 | 1 | Email 24h |
| **Estándar** | **$79/mes** | **1,000** | **3** | **Chat 12h** |
| Pro | $199/mes | ∞ | ∞ | 24/7 Teléfono |

---

**¡Listo!** Ahora ejecuta el script en tu servidor 🚀
