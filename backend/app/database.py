"""
Gestión de conexión a base de datos con connection pooling.
"""
import logging
import psycopg2
from psycopg2.extras import RealDictCursor
from psycopg2.pool import ThreadedConnectionPool
from .config import settings

logger = logging.getLogger(__name__)

# Pool compartido: mínimo 2 conexiones, máximo 10.
# Se inicializa en el primer uso para no fallar en tiempo de importación (tests).
_pool: ThreadedConnectionPool | None = None

def _get_pool() -> ThreadedConnectionPool:
    global _pool
    if _pool is None or _pool.closed:
        _pool = ThreadedConnectionPool(
            minconn=2,
            maxconn=10,
            dsn=settings.DATABASE_URL,
            cursor_factory=RealDictCursor,
        )
        logger.info("Connection pool creado (min=2, max=10)")
    return _pool


def get_db():
    """
    Obtener una conexión del pool. La devuelve automáticamente al terminar el request.

    Yields:
        Connection: Conexión a PostgreSQL con RealDictCursor
    """
    pool = _get_pool()
    conn = pool.getconn()
    try:
        yield conn
    finally:
        pool.putconn(conn)