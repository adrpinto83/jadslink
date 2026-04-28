# 🔐 Obtener Credenciales de BD en Hostinger

**Guía rápida para obtener los datos necesarios para configurar JADSlink**

---

## 🎯 Lo que Necesitas

Para desplegar JADSlink en Hostinger, necesitas:

```
DATABASE_URL=mysql+aiomysql://USUARIO:CONTRASEÑA@HOST:PUERTO/BASEDATOS
                             ↑       ↑          ↑    ↑     ↑
                           Usuario Contraseña Host Puerto Base de Datos
```

Estos 5 datos **VIENEN DE HOSTINGER** → Panel de Control

---

## 📋 Paso a Paso (Panel Hostinger)

### 1️⃣ Login a tu Panel

```
URL: https://hostinger.com/account
```

Ingresa tus credenciales de Hostinger.

### 2️⃣ Navegar a Bases de Datos

En el menú lateral izquierdo, busca:

- **"Bases de Datos"** (más común)
- O **"MySQL"**
- O **"Database"**

Haz click.

### 3️⃣ Ver tus Bases de Datos

Deberías ver una lista similar a esto:

```
┌─────────────────────────────────────────────────┐
│ Nombre BD          │ Usuario         │ Host      │
├─────────────────────────────────────────────────┤
│ u938946830_lineair │ u938946830_user │ localhost │
│ u938946830_otro    │ u938946830_otro │ localhost │
│ ...                │                 │           │
└─────────────────────────────────────────────────┘
```

### 4️⃣ Seleccionar o Crear una BD

**Si YA TIENES una BD creada:**
- Click en el nombre de la BD
- Ve al paso 5️⃣

**Si NO TIENES una BD:**
- Click "Crear Nueva Base de Datos"
- Llena los datos:
  - **Nombre BD**: `u938946830_jadslink`
  - **Usuario**: `u938946830_jadslink`
  - **Contraseña**: (generar)
- Click "Crear"

### 5️⃣ Ver Detalles de Conexión

Cuando haces click en una BD, verás:

```
┌──────────────────────────────────────────┐
│ Información de Conexión                  │
├──────────────────────────────────────────┤
│ Nombre de Base de Datos:                 │
│ u938946830_jadslink                      │
│                                          │
│ Nombre de Usuario:                       │
│ u938946830_jadslink                      │
│                                          │
│ Host (Servidor):                         │
│ localhost                                │
│                                          │
│ Puerto:                                  │
│ 3306                                     │
│                                          │
│ Contraseña:                              │
│ [mostrado o oculto]                      │
└──────────────────────────────────────────┘
```

### 6️⃣ Copiar Datos

Anota o copia:

| Campo | Valor | Ej. |
|-------|-------|-----|
| **Host** | `localhost` | `localhost` |
| **Puerto** | Generalmente `3306` | `3306` |
| **Usuario** | De Hostinger | `u938946830_jadslink` |
| **Contraseña** | De Hostinger | `MiContraseña123*` |
| **BD** | De Hostinger | `u938946830_jadslink` |

---

## 🔗 Construir DATABASE_URL

### Fórmula

```
mysql+aiomysql://USUARIO:CONTRASEÑA@HOST:PUERTO/BASEDATOS
```

### Ejemplo Real

**Datos de Hostinger:**
```
Host: localhost
Puerto: 3306
Usuario: u938946830_jadslink
Contraseña: Amore230617*
Base de Datos: u938946830_jadslink
```

**DATABASE_URL resultante:**
```
mysql+aiomysql://u938946830_jadslink:Amore230617*@localhost:3306/u938946830_jadslink
```

### Caracteres Especiales

Si tu contraseña tiene caracteres especiales (`*`, `@`, `#`, `$`, etc.):

**ANTES**: `Amore230617*@#`

**DESPUÉS** (usar URL encoding):
```
Amore230617%2A%40%23
```

**Mapeo:**
- `*` → `%2A`
- `@` → `%40`
- `#` → `%23`
- `&` → `%26`
- `=` → `%3D`

**Ejemplo con caracteres especiales:**
```
mysql+aiomysql://u938946830_jadslink:Amore230617%2A%40%23@localhost:3306/u938946830_jadslink
```

---

## 📝 En el Archivo .env

Una vez que tengas DATABASE_URL:

```bash
# Abrir .env
nano .env

# Buscar esta línea:
DATABASE_URL=mysql+aiomysql://...

# Reemplazarla con tu URL:
DATABASE_URL=mysql+aiomysql://u938946830_jadslink:TuContraseña@localhost:3306/u938946830_jadslink

# Guardar: Ctrl+O → Enter → Ctrl+X
```

---

## ✅ Verificar que Funciona

Una vez configurado el .env, prueba la conexión:

```bash
# Conectar directamente con MySQL
mysql -h localhost -u u938946830_jadslink -p u938946830_jadslink

# Ingresar contraseña cuando pida
# Si funciona, verás el prompt de MySQL:
# mysql>

# Para salir:
# exit
```

Si funciona con `mysql`, también funcionará con JADSlink.

---

## 🆘 Problemas Comunes

### "Access denied for user"
- La contraseña es **incorrecta**
- Verifica en el panel de Hostinger
- Copia exactamente (mayúsculas/minúsculas importan)

### "Unknown MySQL host"
- El HOST es incorrecto
- Generalmente es `localhost`
- A veces puede ser `127.0.0.1`

### "Can't connect to MySQL server"
- El PUERTO es incorrecto
- Generalmente es `3306`
- Rarement es diferente en Hostinger

### "No database selected"
- Falta el nombre de la BD en la URL
- Debe ser: `...@host:puerto/BASEDATOS`

---

## 📋 Checklist

- [ ] Entré al panel de Hostinger
- [ ] Navegué a "Bases de Datos"
- [ ] Vi la lista de mis BDs
- [ ] Anoté los datos:
  - [ ] Host: `____________`
  - [ ] Puerto: `____________`
  - [ ] Usuario: `____________`
  - [ ] Contraseña: `____________`
  - [ ] Base de Datos: `____________`
- [ ] Construí DATABASE_URL: `____________`
- [ ] Lo puse en .env
- [ ] Probé conexión con MySQL: `mysql -h ... -u ... -p`

---

## 🎯 Si todo está listo

Ya puedes:

1. Editar `.env` con DATABASE_URL
2. Ejecutar:
   ```bash
   cd api
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   alembic upgrade head
   ```

---

**Documento**: Obtener Credenciales de BD en Hostinger
**Última actualización**: 2026-04-27
**Status**: ✅ Listo
