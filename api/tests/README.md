# JADSlink Tests

Tests unitarios e integración para JADSlink API usando pytest.

## Ejecutar Tests

### En Docker (Recomendado)

```bash
# Instalar dependencias de test en el contenedor
docker compose exec api pip install pytest pytest-asyncio aiosqlite

# Ejecutar todos los tests
docker compose exec api pytest tests/ -v

# Ejecutar tests específicos
docker compose exec api pytest tests/test_ticket_service.py -v
docker compose exec api pytest tests/test_session_service.py -v
docker compose exec api pytest tests/test_rate_limit.py -v
```

### Localmente

```bash
cd api
pip install -r requirements.txt
pytest tests/ -v
```

## Estructura de Tests

```
tests/
├── conftest.py                  # Fixtures compartidas (db_session, setup_data)
├── test_ticket_service.py       # Tests para generación de tickets
├── test_session_service.py      # Tests para activación y expiración de sesiones
└── test_rate_limit.py           # Tests para rate limiting
```

## Fixtures Disponibles

### `db_session`
Base de datos SQLite en memoria para testing aislado.

```python
@pytest.mark.asyncio
async def test_example(db_session: AsyncSession):
    # Tu test aquí
    pass
```

### `setup_data`
Datos de prueba pre-cargados: tenant, node, plan, ticket.

```python
@pytest.mark.asyncio
async def test_example(db_session: AsyncSession, setup_data):
    ticket = setup_data["ticket"]
    node = setup_data["node"]
    # Tu test aquí
    pass
```

## Cobertura de Tests

### ticket_service.py
- ✓ Generación de códigos únicos (10,000 códigos sin colisiones)
- ✓ Formato de código (8 caracteres alfanuméricos uppercase)
- ✓ Códigos diferentes con mismo secreto (randomness)
- ✓ Códigos diferentes con secretos diferentes
- ✓ Generación de QR base64
- ✓ QR con datos vacíos

### session_service.py
- ✓ Activación exitosa de sesión
- ✓ Prevención de doble activación
- ✓ Expiración de sesiones vencidas
- ✓ No expirar sesiones activas
- ✓ Almacenamiento de IP del usuario

### rate_limit.py
- ✓ Permitir requests bajo el límite
- ✓ Bloquear requests sobre el límite (HTTP 429)
- ✓ Configurar expiración en primera request
- ✓ Continuar sin Redis si no está disponible
- ✓ Continuar en caso de error de Redis
- ✓ Límites separados por endpoint
- ✓ Factory de dependency funcional

## Añadir Nuevos Tests

1. Crear archivo `test_*.py` en `tests/`
2. Importar fixtures desde `conftest.py`
3. Marcar funciones async con `@pytest.mark.asyncio`
4. Usar `db_session` fixture para operaciones de base de datos

Ejemplo:

```python
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

@pytest.mark.asyncio
async def test_my_feature(db_session: AsyncSession, setup_data):
    # Arrange
    ticket = setup_data["ticket"]

    # Act
    result = await my_service.do_something(ticket)

    # Assert
    assert result is not None
```
