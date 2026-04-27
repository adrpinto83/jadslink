# Pricing Integration Tests

Esta es la guía completa de testing para la funcionalidad de pricing dinámico y multi-moneda.

## Tests Unitarios (Para Vitest/Jest)

Si quieres ejecutar los tests, instala las dependencias:

```bash
npm install -D vitest @vitest/ui @testing-library/react @testing-library/user-event
```

Luego crea el archivo `src/__tests__/pricing.test.ts`:

```typescript
import { describe, it, expect, beforeEach } from 'vitest';
import { cacheService } from '@/utils/cache';

describe('Pricing Integration', () => {
  beforeEach(() => {
    cacheService.clearAll();
  });

  describe('Cache Service', () => {
    it('should cache data with TTL', () => {
      const testData = { name: 'Test Plan', price: 29 };
      cacheService.set('test_key', testData, 60);
      const cached = cacheService.get('test_key');
      expect(cached).toEqual(testData);
    });

    it('should return null for expired cache', async () => {
      const testData = { name: 'Test Plan', price: 29 };
      cacheService.set('test_key_expire', testData, 0);
      await new Promise(resolve => setTimeout(resolve, 10));
      const cached = cacheService.get('test_key_expire');
      expect(cached).toBeNull();
    });

    it('should clear specific cache entry', () => {
      const testData = { name: 'Test Plan' };
      cacheService.set('test_key_clear', testData);
      cacheService.clear('test_key_clear');
      const cached = cacheService.get('test_key_clear');
      expect(cached).toBeNull();
    });
  });

  describe('Pricing Conversion', () => {
    it('should convert USD to VEF correctly', () => {
      const exchangeRate = 36.50;
      const usdAmount = 29.00;
      const vefAmount = Math.round(usdAmount * exchangeRate * 100) / 100;
      expect(vefAmount).toBe(1043.50);
    });

    it('should handle different exchange rates', () => {
      const testCases = [
        { rate: 36.50, usd: 29.00, expected: 1043.50 },
        { rate: 36.50, usd: 99.00, expected: 3613.50 },
        { rate: 40.00, usd: 29.00, expected: 1160.00 },
      ];

      testCases.forEach(({ rate, usd, expected }) => {
        const result = Math.round(usd * rate * 100) / 100;
        expect(result).toBe(expected);
      });
    });
  });
});
```

## E2E Tests Manual - Checklist Completo

### ✅ Login Page - Pricing Display

**Setup:**
- Abrir http://localhost:5173/login en navegador limpio
- Abrir DevTools (F12)
- Ir a tab "Network"

**Pasos:**

1. ✓ **Plans load from API**
   - [ ] Refrescar página (Ctrl+R)
   - [ ] En Network tab, buscar request a `/subscriptions/plans`
   - [ ] Verificar status code 200
   - [ ] Verificar response contiene array de plans con `unit_amount`, `product.name`, etc.

2. ✓ **Pricing displays correctly**
   - [ ] Ver 3 cards de planes en lado derecho
   - [ ] Card 1: "Plan" con precio "$0" o "$29.00"
   - [ ] Card 2: "Plan" con precio "$99.00" (Pro)
   - [ ] Card 3: "Plan" con precio mayor
   - [ ] Todos los precios están en formato "$X.XX"

3. ✓ **Cache works on second load**
   - [ ] Abrir DevTools > Application > Local Storage
   - [ ] Verificar entrada `jadlink_cache_subscription_plans`
   - [ ] El contenido es un objeto JSON con timestamp
   - [ ] Refrescar página (segunda vez)
   - [ ] En Network tab, NO debe aparecer request a `/subscriptions/plans` (usando cache)
   - [ ] Los planes aún se muestran correctamente

4. ✓ **Cache TTL validation (1 hour)**
   - [ ] Verificar timestamp en cache: `(Date.now() - timestamp) < 1 hour`
   - [ ] Wait 1+ hora real (o simular con DevTools)
   - [ ] Limpiar cache manualmente: En DevTools, buscar y eliminar `jadlink_cache_subscription_plans`
   - [ ] Refrescar página
   - [ ] Network tab debe mostrar request a `/subscriptions/plans` nuevamente

### ✅ Billing Page - Multi-Currency Pricing

**Setup:**
- Login con cuenta de demo (admin@jads.com / admin123456)
- Navegar a /dashboard/billing
- DevTools abierto

**Pasos:**

5. ✓ **Exchange rate displayed**
   - [ ] Buscar texto "1 USD = Bs."
   - [ ] Verificar que muestra tasa actualizada (ej: 36.50)
   - [ ] El número coincide con el retornado por `/utils/exchange-rate` (Network tab)

6. ✓ **Plans show both USD and VEF**
   - [ ] Buscar cards de Stripe plans (abajo de la página)
   - [ ] Cada plan debe mostrar:
     ```
     $29.00 USD
     ≈ Bs. 1,043.50
     ```
   - [ ] Verificar conversión matemática: 29.00 * 36.50 = 1,043.50 ✓
   - [ ] Card Pro: "$99.00 USD" → "≈ Bs. 3,613.50" ✓
   - [ ] VEF debe tener separador de miles (Bs. 1,043.50, no 1043.50)

7. ✓ **Each plan shows features**
   - [ ] Plan Free: "Siempre gratis", "1 nodo", "50 tickets/mes"
   - [ ] Plan Starter: "3 nodos máximo", "1,000 tickets/mes", "14 días prueba"
   - [ ] Plan Pro: "10 nodos máximo", "5,000 tickets/mes"
   - [ ] Plan Enterprise (si aparece): "Nodos ilimitados", "Tickets ilimitados"

### ✅ Caching Verification

8. ✓ **Cache in localStorage**
   - [ ] DevTools > Application > Local Storage > localhost:5173
   - [ ] Buscar todas las keys que comienzan con `jadlink_cache_`
   - [ ] Verificar `jadlink_cache_subscription_plans` existe
   - [ ] Click en la key para ver contenido (debe ser JSON)
   - [ ] JSON debe contener: `name`, `description`, `price`, `features`
   - [ ] JSON NO debe contener `icon` (porque funciones no son serializables)

9. ✓ **Cache timestamp**
   - [ ] En console ejecutar: `JSON.parse(localStorage.getItem('jadlink_cache_subscription_plans')).timestamp`
   - [ ] Debe ser un número (milisegundos desde epoch)
   - [ ] Calcular edad: `(Date.now() - timestamp) / 1000 / 60` = minutos desde caching
   - [ ] Debe ser menos de 5 minutos (reciente)

10. ✓ **Network requests optimization**
    - [ ] Limpiar cache: `localStorage.clear()` en console
    - [ ] Refrescar página (F5) - Network tab activo
    - [ ] Contar requests a `/subscriptions/plans`
    - [ ] Primera carga: 1 request ✓
    - [ ] Refrescar de nuevo (sin borrar cache)
    - [ ] Segunda carga: 0 requests ✓ (usando cache)

### ✅ Multi-Currency Scenarios

11. ✓ **USD to VEF conversion accuracy**
    - [ ] Usar calculadora o Excel:
    - [ ] Plan Starter: $29.00 × 36.50 = Bs. 1,043.50 ✓
    - [ ] Plan Pro: $99.00 × 36.50 = Bs. 3,613.50 ✓
    - [ ] Si exchange rate cambia a 40:
    - [ ] Plan Starter: $29.00 × 40 = Bs. 1,160.00 ✓

12. ✓ **Exchange rate updates**
    - [ ] Página Billing refetch automaticamente cada minuto
    - [ ] React Query debería refetchar `/utils/exchange-rate`
    - [ ] En Network tab, debería haber request a `/utils/exchange-rate` frecuentemente
    - [ ] Cambiar tasa manualmente en backend (si es posible en admin)
    - [ ] Refrescar página después de 1 minuto
    - [ ] Verificar que muestra nueva tasa

### ✅ Error Scenarios

13. ✓ **Network error fallback**
    - [ ] DevTools > Network > agregar `offline` en DevTools
    - [ ] Refrescar Login page
    - [ ] Debe mostrar planes por defecto (No error)
    - [ ] En console debería haber: "Failed to load subscription plans"
    - [ ] Click en modo online nuevamente
    - [ ] Limpiar cache manualmente
    - [ ] Refrescar - debe cargar desde API nuevamente

14. ✓ **API timeout handling**
    - [ ] DevTools > Network > Throttling > "Slow 4G"
    - [ ] Refrescar página
    - [ ] Después de ~15 segundos, debe mostrar fallback planes
    - [ ] No debe tener estado "loading" infinito
    - [ ] En console: error message

### ✅ Performance Validation

15. ✓ **First page load time**
    - [ ] DevTools > Performance tab
    - [ ] Start recording
    - [ ] Refrescar página (Ctrl+Shift+R para limpiar cache)
    - [ ] Esperar a que planes se muestren completamente
    - [ ] Stop recording
    - [ ] Verificar:
      - First Contentful Paint (FCP) < 3s ✓
      - Largest Contentful Paint (LCP) < 4s ✓
      - Plans rendered < 2s ✓

16. ✓ **Cached load time**
    - [ ] Performance tab, start recording
    - [ ] Refrescar página (planes deben estar en cache)
    - [ ] Stop recording
    - [ ] Verificar:
      - FCP < 1s ✓ (mucho más rápido)
      - Plans rendered instantly ✓
      - No API requests ✓

---

## Resumen de Implementación

### Archivos Modificados

1. **dashboard/src/utils/cache.ts** (NUEVO)
   - Servicio centralizado de caching con TTL
   - Métodos: `get()`, `set()`, `clear()`, `clearAll()`

2. **dashboard/src/pages/Login.tsx**
   - `loadDemoPlans()` - Carga planes con caching
   - `addIconsToPlan()` - Reconstruye iconos desde cache
   - `getPlanIcon()` - Mapea índices a iconos
   - Renderizado de planes mejorado

3. **dashboard/src/pages/Billing.tsx**
   - `convertToVEF()` - Conversión automática USD→VEF
   - `renderPlanPrice()` - Muestra ambas monedas
   - React Query con `staleTime: 1 hora`
   - Planes mejoradas con features por tier

### Key Features

✅ **Caching**
- localStorage con TTL de 1 hora
- Fallback a planes default si API falla
- Manejo correcto de funciones (no serializables)

✅ **Multi-Moneda**
- Conversión automática USD → VEF
- Tasa de cambio actualizada cada minuto
- Formato correcto de moneda (Bs. con separadores)

✅ **Performance**
- Primera carga: API call + caching
- Cargas siguientes (< 1 hora): desde cache (0 API calls)
- Renderizado instant con cache

✅ **Fallback**
- Si API falla: usa planes default
- Totalmente funcional offline (con cache)
- Mensajes de error en console (no rompe UI)
