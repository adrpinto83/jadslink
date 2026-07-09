# Tema Claro/Oscuro - JADSlink

## Implementación

✅ Tema claro/oscuro funcional en el frontend de producción (Hostinger).

## Características

- **Toggle en navbar**: Botón con icono de sol/luna
- **Persistencia**: Se guarda en `localStorage` como `hcm_theme`
- **Temas disponibles**: 
  - `dark` (por defecto) - Tema oscuro profesional
  - `light` - Tema claro con buen contraste

## Paleta de Colores

### Tema Oscuro
```css
--bg: #0f1117
--surface: #1a1d27
--surface2: #222536
--accent: #4f8ef7
--accent2: #3ecf8e
--danger: #e55353
--text: #e2e8f0
--muted: #8892a4
--border: #2d3348
```

### Tema Claro
```css
--bg: #f5f7fa
--surface: #ffffff
--surface2: #f0f2f5
--accent: #4f8ef7
--accent2: #10b981
--danger: #ef4444
--text: #1a202c
--muted: #64748b
--border: #e2e8f0
```

## Uso en Código

El tema se aplica mediante el atributo `data-theme` en el elemento raíz:

```html
<html data-theme="light">
  <!-- Tema claro -->
</html>

<html data-theme="dark">
  <!-- Tema oscuro -->
</html>
```

## API JavaScript

```javascript
// Cambiar tema
theme.apply("light");
theme.apply("dark");

// Toggle entre temas
theme.toggle();

// Obtener tema actual
console.log(theme.current); // "light" o "dark"
```

## Archivos Modificados

- `frontend/static/css/app.css` - Variables CSS para ambos temas
- `frontend/static/js/app.js` - Lógica del toggle y persistencia
- `frontend/index.html` - Botón de toggle en navbar

---
Implementado: 2026-07-05
