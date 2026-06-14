"""Health check endpoints for liveness and readiness probes.

Provides /healthz (liveness) and /readyz (readiness) routes intended for
container orchestrators such as Kubernetes.
"""

from __future__ import annotations

from typing import Any

import structlog
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from kafka import KafkaConsumer
from kafka.errors import KafkaError
from psycopg import OperationalError

from src.config.settings import settings
from src.writer.db_pool import get_pool

logger = structlog.get_logger(__name__)

router = APIRouter(tags=["health"])


@router.get("/healthz")
def liveness() -> dict[str, str]:
    """Return 200 if the process is alive."""
    return {"status": "ok"}


@router.get("/readyz")
def readiness() -> JSONResponse:
    """Return 200 only when both the DB pool and Kafka broker are reachable."""
    checks: dict[str, Any] = {}

    # -- Database check --
    try:
        pool = get_pool()
        with pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
                cur.fetchone()
        checks["database"] = "ok"
    except OperationalError as exc:
        logger.warning("readiness.db_check_failed", error=str(exc))
        checks["database"] = f"error: {exc}"
    except Exception as exc:  # noqa: BLE001 — pool may raise RuntimeError
        logger.warning("readiness.db_check_failed", error=str(exc))
        checks["database"] = f"error: {exc}"

    # -- Kafka check --
    consumer: KafkaConsumer | None = None
    try:
        consumer = KafkaConsumer(
            bootstrap_servers=settings.kafka_bootstrap_servers,
            consumer_timeout_ms=5000,
            api_version=(0, 10, 1),
        )
        topics = consumer.topics()
        checks["kafka"] = "ok"
        logger.debug("readiness.kafka_topics", count=len(topics))
    except KafkaError as exc:
        logger.warning("readiness.kafka_check_failed", error=str(exc))
        checks["kafka"] = f"error: {exc}"
    except Exception as exc:  # noqa: BLE001 — connection / timeout errors
        logger.warning("readiness.kafka_check_failed", error=str(exc))
        checks["kafka"] = f"error: {exc}"
    finally:
        if consumer is not None:
            try:
                consumer.close()
            except KafkaError:
                pass

    # -- Aggregate result --
    all_ok = all(v == "ok" for v in checks.values())
    status_code = 200 if all_ok else 503
    body = {
        "status": "ready" if all_ok else "degraded",
        "checks": checks,
    }

    return JSONResponse(content=body, status_code=status_code)
