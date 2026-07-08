# JADSLink — Contrato de API para la app Android de operadores

Artefactos generados a partir del contrato **verificado** contra `jadslink-app`
(la app real en `link.jadsstudio.com`), no contra el prototipo del contenedor Docker.

```
mobile-api/
├── openapi.yaml            # Spec OpenAPI 3.0 (importable en Postman/Swagger)
├── kotlin/
│   ├── Models.kt           # data classes (Moshi)
│   ├── JadsLinkApi.kt      # interfaz Retrofit (suspend)
│   └── ApiClient.kt        # OkHttp + interceptor Bearer + helper multipart
└── README.md
```

## Autenticación

1. `login` o `signup` devuelven `{ token, role, account_id }`.
2. Guarda `token` (usa `EncryptedSharedPreferences`/DataStore) y ponlo en `TokenStore`.
3. `AuthInterceptor` lo envía como `Authorization: Bearer <token>` en cada request.
4. El token dura **7 días** y se invalida si cambian la contraseña → un `401`
   dispara `UnauthorizedInterceptor.onUnauthorized` para volver al login.

## Roles (RBAC) — ocultar acciones en la UI

| Rol | Puede |
|-----|-------|
| `owner` | Todo: cuenta, usuarios, facturación, gateways, códigos, tienda |
| `manager` | Gateways, códigos, tienda. **No** facturación/usuarios (403) |
| `viewer` | Solo lectura (403 en cualquier POST/PATCH/DELETE) |

Lee `role` de `me()` y esconde botones que darían 403.

## Límites de plan (mostrar en la UI)

`me().account.usage` trae todo lo necesario: `deviceCount`/`maxDevices`,
`ticketsUsed`/`ticketsPerMonth`, `atLimit`, `totalMonthly`. Al llegar al tope,
`registerDevice` y `generateCodes` responden **403** con `detail` explicativo.
Cuenta `suspended`/`past_due` → 403 en acciones de gestión (`billing`).

## Gotchas verificados

- **Generar códigos**: el campo es `quantity`, **no** `count` (mandar `count` crea 1).
- **Alta de gateway**: `registerDevice` devuelve `api_key` — es para el **router**,
  no para la app. El `device_id` (UUID) lo genera el servidor.
- **Reportar pago**: es `multipart/form-data` (no JSON). Usa `PaymentParts.build(...)`.
  Comprobante opcional: JPG/PNG/WEBP/PDF, máx 4 MB.
- **`reboot`/`ssid`** encolan un comando; el router lo ejecuta en su próximo heartbeat.
- Endpoints públicos (sin token): `login`, `signup`, `exchange/current`, `shop/{id}`.

## Dependencias Gradle (referencia)

```kotlin
implementation("com.squareup.retrofit2:retrofit:2.11.0")
implementation("com.squareup.retrofit2:converter-moshi:2.11.0")
implementation("com.squareup.moshi:moshi-kotlin:1.15.1")
implementation("com.squareup.okhttp3:logging-interceptor:4.12.0")
// (opcional, si usas codegen de Moshi en vez de reflect)
// ksp("com.squareup.moshi:moshi-kotlin-codegen:1.15.1")
```

> Nota: `Models.kt` usa `@JsonClass(generateAdapter = true)`. Para que funcione
> sin KSP, `ApiClient` añade `KotlinJsonAdapterFactory` (reflect). Si prefieres
> codegen, agrega el plugin KSP y el `moshi-kotlin-codegen` y quita el factory.

## Uso rápido

```kotlin
val api = ApiClient.create(
    onUnauthorized = { /* limpiar token, ir a login */ },
    debug = BuildConfig.DEBUG,
)

// Login
val auth = api.login(LoginPayload("operador", "secreto"))
ApiClient.tokenStore.set(auth.token)

// Dashboard
val me = api.me()
val overview = api.overview()
val gateways = api.devices()

// Generar 10 códigos de 1h en un gateway
val res = api.generateCodes(gateways.first().id, CodeCreate(quantity = 10, durationMin = 60))
// res.codes -> ["A3K9P2X7", ...]; res.quota.available -> restante
```

## Probar la spec

```bash
# levantar la app local con datos aislados
cd jadslink-app
DATA_DIR=/tmp/jadslink-test COOKIE_SECURE=false \
  python3 -m uvicorn api.main:app --port 8099
# luego apunta ApiClient.BASE_URL a http://10.0.2.2:8099/ (emulador Android)
```
