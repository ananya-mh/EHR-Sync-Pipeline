"""Connection pool singleton for PostgreSQL using psycopg3.

Provides a module-level ConnectionPool that is lazily initialized on first
access via get_pool(). All database access in the application should go
through this pool rather than creating standalone connections.
"""

import threading

import psycopg_pool
import structlog

from src.config.settings import settings

logger = structlog.get_logger(__name__)

_pool: psycopg_pool.ConnectionPool | None = None
_lock = threading.Lock()


def _build_conninfo() -> str:
    """Build a psycopg3 connection string from settings."""
    return (
        f"host={settings.db_host} "
        f"port={settings.db_port} "
        f"dbname={settings.db_name} "
        f"user={settings.db_user} "
        f"password={settings.db_password}"
    )


def get_pool() -> psycopg_pool.ConnectionPool:
    """Return the module-level connection pool, creating it on first call."""
    global _pool
    if _pool is None:
        with _lock:
            # Double-checked locking to avoid race conditions.
            if _pool is None:
                conninfo = _build_conninfo()
                _pool = psycopg_pool.ConnectionPool(
                    conninfo=conninfo,
                    min_size=settings.db_pool_min_size,
                    max_size=settings.db_pool_max_size,
                    max_idle=settings.db_pool_max_idle,
                )
                logger.info(
                    "connection_pool_initialized",
                    host=settings.db_host,
                    port=settings.db_port,
                    dbname=settings.db_name,
                    min_size=settings.db_pool_min_size,
                    max_size=settings.db_pool_max_size,
                )
    return _pool


def close_pool() -> None:
    """Close the connection pool for graceful shutdown."""
    global _pool
    if _pool is not None:
        _pool.close()
        logger.info("connection_pool_closed")
        _pool = None
