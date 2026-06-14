"""Main orchestrator for the EHR-Sync-Pipeline consumer side.

Starts all Kafka consumer threads, the FastAPI/GraphQL API server, and
coordinates graceful shutdown when SIGTERM or SIGINT is received.
"""

from __future__ import annotations

import signal
import threading
from types import FrameType

from src.api.app import start_api
from src.consumers.lab_consumer import LabConsumer
from src.consumers.medication_consumer import MedicationConsumer
from src.consumers.patient_consumer import PatientConsumer
from src.observability.logging import get_logger, setup_logging
from src.processor.transform import (
    transform_lab_result,
    transform_medication,
    transform_patient,
)
from src.writer.db_pool import close_pool
from src.writer.db_writer import upsert_lab_result, upsert_medication, upsert_patient


def main() -> None:
    """Bootstrap consumers, API server, and block until shutdown."""
    setup_logging()
    log = get_logger("orchestrator")
    log.info("pipeline.starting")

    shutdown_event = threading.Event()

    # ------------------------------------------------------------------
    # Signal handlers — set the shutdown event on SIGTERM / SIGINT
    # ------------------------------------------------------------------
    def handle_signal(signum: int, frame: FrameType | None) -> None:
        """Set the shutdown event when a termination signal arrives."""
        log.info("shutdown.signal_received", signal=signum)
        shutdown_event.set()

    signal.signal(signal.SIGTERM, handle_signal)
    signal.signal(signal.SIGINT, handle_signal)

    # ------------------------------------------------------------------
    # Consumer threads
    # ------------------------------------------------------------------
    consumers: list[tuple[str, type, object, object]] = [
        ("patients", PatientConsumer, transform_patient, upsert_patient),
        ("labs", LabConsumer, transform_lab_result, upsert_lab_result),
        ("medications", MedicationConsumer, transform_medication, upsert_medication),
    ]

    threads: list[threading.Thread] = []
    for name, consumer_cls, transform_fn, write_fn in consumers:
        consumer = consumer_cls(shutdown_event)
        t = threading.Thread(
            target=consumer.run,
            args=(transform_fn, write_fn),
            name=f"consumer-{name}",
            daemon=True,
        )
        t.start()
        threads.append(t)
        log.info("consumer.thread_started", stream=name)

    # ------------------------------------------------------------------
    # API server thread
    # ------------------------------------------------------------------
    api_thread = threading.Thread(target=start_api, name="api-server", daemon=True)
    api_thread.start()
    log.info("api.thread_started")

    # ------------------------------------------------------------------
    # Block until shutdown is requested
    # ------------------------------------------------------------------
    try:
        shutdown_event.wait()
    except KeyboardInterrupt:
        log.info("shutdown.keyboard_interrupt")
        shutdown_event.set()

    # ------------------------------------------------------------------
    # Graceful shutdown
    # ------------------------------------------------------------------
    log.info("shutdown.waiting_for_consumers")
    for t in threads:
        t.join(timeout=10)

    close_pool()
    log.info("pipeline.stopped")


if __name__ == "__main__":
    main()
