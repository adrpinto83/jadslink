"""Rate limiting en memoria (ventana deslizante) — sin Redis, "liviano primero".

Suficiente para un proceso uvicorn único. Si algún día corren varios workers,
cada worker limita por separado (el límite efectivo se multiplica; aceptable).
"""
import time
import threading
from collections import defaultdict, deque

from fastapi import HTTPException, Request

_hits: dict[str, deque] = defaultdict(deque)
_lock = threading.Lock()
_MAX_KEYS = 10_000


def client_ip(request: Request) -> str:
    """IP real del cliente, respetando el proxy (PHP proxy de Hostinger)."""
    fwd = request.headers.get("x-forwarded-for", "")
    if fwd:
        return fwd.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def check(key: str, limit: int, window_sec: int) -> None:
    """Lanza 429 si `key` superó `limit` eventos en los últimos `window_sec`."""
    now = time.monotonic()
    with _lock:
        q = _hits[key]
        while q and q[0] <= now - window_sec:
            q.popleft()
        if len(q) >= limit:
            raise HTTPException(status_code=429, detail="Demasiados intentos. Espera un momento e intenta de nuevo.")
        if len(_hits) > _MAX_KEYS:  # evitar crecimiento sin límite
            _hits.clear()
            q = _hits[key]
        q.append(now)


def record(key: str) -> None:
    """Registra un evento sin verificar (para contar solo fallos)."""
    now = time.monotonic()
    with _lock:
        _hits[key].append(now)


def over_limit(key: str, limit: int, window_sec: int) -> bool:
    """True si `key` ya superó el límite (sin registrar un evento nuevo)."""
    now = time.monotonic()
    with _lock:
        q = _hits[key]
        while q and q[0] <= now - window_sec:
            q.popleft()
        return len(q) >= limit


def reset() -> None:
    """Limpia todos los contadores (tests)."""
    with _lock:
        _hits.clear()
