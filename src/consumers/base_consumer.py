"""Abstract base consumer with manual commits, retry, and dead-letter queue."""

from __future__ import annotations

import abc
import json
import threading
import time
from datetime import datetime, timezone
from typing import Any, Callable, Type

import structlog
from kafka import KafkaConsumer, KafkaProducer
from kafka.errors import KafkaError
from pydantic import BaseModel, ValidationError

from src.config.settings import settings

logger = structlog.get_logger(__name__)


class BaseConsumer(abc.ABC):
    """Abstract Kafka consumer with manual offset commits, retry, and DLQ."""

    def __init__(self, shutdown_event: threading.Event) -> None:
        """Initialise consumer with a shutdown event for graceful termination."""
        self._shutdown_event = shutdown_event
        self._consumer = KafkaConsumer(
            self.topic,
            bootstrap_servers=settings.kafka_bootstrap_servers,
            group_id=self.group_id,
            enable_auto_commit=False,
            auto_offset_reset="earliest",
            value_deserializer=lambda m: json.loads(m.decode("utf-8")),
            api_version=(0, 10, 1),
        )
        self._dlq_producer: KafkaProducer | None = None
        self._log = logger.bind(
            topic=self.topic,
            group_id=self.group_id,
        )
        self._log.info("consumer.initialised")

    # ------------------------------------------------------------------
    # Abstract properties — subclasses MUST implement
    # ------------------------------------------------------------------

    @property
    @abc.abstractmethod
    def topic(self) -> str:
        """Kafka topic this consumer subscribes to."""

    @property
    @abc.abstractmethod
    def group_id(self) -> str:
        """Consumer group identifier."""

    @property
    @abc.abstractmethod
    def model_class(self) -> Type[BaseModel]:
        """Pydantic model used to validate incoming messages."""

    # ------------------------------------------------------------------
    # DLQ producer (created lazily on first failure)
    # ------------------------------------------------------------------

    def _get_dlq_producer(self) -> KafkaProducer:
        """Return a lazily-initialised DLQ producer."""
        if self._dlq_producer is None:
            self._dlq_producer = KafkaProducer(
                bootstrap_servers=settings.kafka_bootstrap_servers,
                value_serializer=lambda v: json.dumps(v).encode("utf-8"),
                api_version=(0, 10, 1),
            )
            self._log.info("dlq_producer.initialised")
        return self._dlq_producer

    def _send_to_dlq(
        self,
        raw_value: dict[str, Any],
        error: Exception,
        attempts: int,
    ) -> None:
        """Produce a failed message to the dead-letter queue topic."""
        dlq_message: dict[str, Any] = {
            "original_message": raw_value,
            "error": str(error),
            "error_type": type(error).__name__,
            "attempts": attempts,
            "original_topic": self.topic,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        try:
            producer = self._get_dlq_producer()
            producer.send(settings.kafka_dlq_topic, value=dlq_message)
            producer.flush()
            self._log.warning(
                "message.sent_to_dlq",
                error=str(error),
                attempts=attempts,
            )
        except KafkaError as exc:
            self._log.error(
                "dlq.send_failed",
                error=str(exc),
                original_error=str(error),
            )

    # ------------------------------------------------------------------
    # Core processing loop
    # ------------------------------------------------------------------

    def _process_message(
        self,
        raw_value: dict[str, Any],
        transform_fn: Callable[[BaseModel], dict[str, Any]],
        write_fn: Callable[[dict[str, Any]], None],
    ) -> None:
        """Validate, transform, and write a single message with retries."""
        max_retries: int = settings.kafka_max_retries
        last_error: Exception | None = None

        for attempt in range(1, max_retries + 1):
            try:
                validated = self.model_class(**raw_value)
                transformed = transform_fn(validated)
                write_fn(transformed)
                return  # success
            except ValidationError as exc:
                last_error = exc
                self._log.warning(
                    "message.validation_failed",
                    attempt=attempt,
                    error=str(exc),
                )
            except KafkaError as exc:
                last_error = exc
                self._log.warning(
                    "message.kafka_error",
                    attempt=attempt,
                    error=str(exc),
                )
            except Exception as exc:  # noqa: BLE001 — catch DB / transform errors
                last_error = exc
                self._log.warning(
                    "message.processing_failed",
                    attempt=attempt,
                    error=str(exc),
                    error_type=type(exc).__name__,
                )

            if attempt < max_retries:
                backoff = 2 ** (attempt - 1)  # 1s, 2s, 4s
                self._log.info(
                    "message.retry_backoff",
                    attempt=attempt,
                    backoff_seconds=backoff,
                )
                time.sleep(backoff)

        # All retries exhausted — send to DLQ
        assert last_error is not None
        self._send_to_dlq(raw_value, last_error, max_retries)

    def run(
        self,
        transform_fn: Callable[[BaseModel], dict[str, Any]],
        write_fn: Callable[[dict[str, Any]], None],
    ) -> None:
        """Poll messages and process them until shutdown is signalled."""
        self._log.info("consumer.run.started")
        try:
            while not self._shutdown_event.is_set():
                records = self._consumer.poll(timeout_ms=1000)
                if not records:
                    continue

                for topic_partition, messages in records.items():
                    for message in messages:
                        if self._shutdown_event.is_set():
                            self._log.info("consumer.shutdown_requested_mid_batch")
                            return

                        self._log.debug(
                            "message.received",
                            partition=topic_partition.partition,
                            offset=message.offset,
                        )

                        self._process_message(
                            message.value,
                            transform_fn,
                            write_fn,
                        )

                        # Commit offset after successful processing (or DLQ)
                        try:
                            self._consumer.commit()
                        except KafkaError as exc:
                            self._log.error(
                                "offset.commit_failed",
                                error=str(exc),
                            )
        except KafkaError as exc:
            self._log.error("consumer.kafka_error", error=str(exc))
            raise
        finally:
            self.close()

    # ------------------------------------------------------------------
    # Graceful shutdown
    # ------------------------------------------------------------------

    def close(self) -> None:
        """Commit final offsets and close consumer and DLQ producer."""
        self._log.info("consumer.closing")
        try:
            self._consumer.commit()
        except KafkaError as exc:
            self._log.error("consumer.final_commit_failed", error=str(exc))
        finally:
            self._consumer.close()
            if self._dlq_producer is not None:
                self._dlq_producer.close()
            self._log.info("consumer.closed")
